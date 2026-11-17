"""Admin document ingestion for document-grounded generation (migration 023).

An administrator supplies TXT, Markdown or a text-based PDF. The file is never
stored: this service extracts and normalizes the text, splits it into bounded,
ordered chunks and persists only the extracted text, page/heading metadata and
SHA-256 checksums. No model is called here, and document text is never logged.

Attached documents stay in ``draft`` until an administrator approves them.
Only ``approved`` documents attached to a CLO may later feed grounded
generation; archived documents are retained for audit but never retrieved.
"""

import base64
import binascii
import hashlib
import io
import logging
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..errors import AppError
from ..models import CourseDocument, CourseLearningOutcome
from ..repositories import DocumentRepository
from ..schemas import (
    DocumentChunkResult,
    DocumentCloResult,
    DocumentDetail,
    DocumentSummary,
)

logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_BASE64_CHARS = 4 * ((MAX_UPLOAD_BYTES + 2) // 3)
MAX_UPLOAD_JSON_BYTES = MAX_BASE64_CHARS + 64 * 1024
MAX_TEXT_CHARS = 1_000_000
MIN_TEXT_CHARS = 20
MAX_PAGES = 500
MAX_CHUNKS = 5_000
CHUNK_TARGET = 1_000
CHUNK_MAX = 1_600
CHUNK_MIN = 200
TEXT_POLICY_VERSION = "untrusted-v1"
ALLOWED_EXTENSIONS = {".txt": "text/plain", ".md": "text/markdown", ".pdf": "application/pdf"}
_HEADING = re.compile(r"^#{1,6}\s+(.+)$")


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def check_content_length(value: str | None) -> None:
    """Reject an oversized upload from its header before JSON parsing."""
    if value is None:
        return
    try:
        length = int(value)
    except ValueError:
        raise AppError(400, "invalid_content_length", "The Content-Length header is invalid")
    if length > MAX_UPLOAD_JSON_BYTES:
        raise AppError(
            413,
            "document_too_large",
            f"Documents are limited to {MAX_UPLOAD_BYTES // (1024 * 1024)} MB",
        )


def _decode_upload(content_base64: str) -> bytes:
    # Bound the encoded form before decoding so an oversized request cannot
    # inflate into a larger in-memory buffer.
    if len(content_base64) > MAX_BASE64_CHARS:
        raise AppError(
            413,
            "document_too_large",
            f"Documents are limited to {MAX_UPLOAD_BYTES // (1024 * 1024)} MB",
        )
    try:
        raw = base64.b64decode(content_base64, validate=True)
    except (binascii.Error, ValueError):
        raise AppError(422, "invalid_upload_encoding", "The upload content must be standard base64")
    if not raw:
        raise AppError(422, "document_empty", "The uploaded file is empty")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise AppError(
            413,
            "document_too_large",
            f"Documents are limited to {MAX_UPLOAD_BYTES // (1024 * 1024)} MB",
        )
    return raw


def _read_text(raw: bytes) -> list[str]:
    try:
        value = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise AppError(422, "invalid_text_encoding", "Text and Markdown uploads must be UTF-8")
    controls = sum(1 for ch in value if ord(ch) < 32 and ch not in "\n\t\r")
    if "\x00" in value or controls > max(8, len(value) // 100):
        raise AppError(422, "invalid_text_encoding", "The uploaded text contains binary data")
    return [value]


def _read_pdf(raw: bytes) -> list[str]:
    from pypdf import PdfReader

    try:
        reader = PdfReader(io.BytesIO(raw), strict=False)
        if reader.is_encrypted:
            raise AppError(422, "pdf_encrypted", "Encrypted PDFs are not accepted")
        if len(reader.pages) > MAX_PAGES:
            raise AppError(413, "document_too_large", f"PDFs are limited to {MAX_PAGES} pages")
        pages = []
        for page in reader.pages:
            try:
                pages.append(page.extract_text() or "")
            except Exception:
                pages.append("")
    except AppError:
        raise
    except Exception:
        raise AppError(422, "invalid_pdf", "The PDF could not be read")
    if not any(page.strip() for page in pages):
        raise AppError(
            422,
            "pdf_text_unavailable",
            "The PDF has no extractable text; scanned PDFs are not supported",
        )
    return pages


def normalize_text(value: str) -> str:
    """NFKC + whitespace normalization; control characters never reach storage."""
    text = unicodedata.normalize("NFKC", value).replace("\r\n", "\n").replace("\r", "\n")
    text = "".join(
        ch for ch in text if ch in "\n\t" or unicodedata.category(ch)[0] != "C"
    )
    text = "\n".join(re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n"))
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _prepare_pages(pages: list[str]) -> tuple[str, list[tuple[int, int, int]]]:
    parts: list[str] = []
    spans: list[tuple[int, int, int]] = []
    cursor = 0
    for number, page in enumerate(pages, 1):
        text = normalize_text(page)
        if not text:
            continue
        if parts:
            cursor += 2  # the "\n\n" page separator
        start = cursor
        parts.append(text)
        cursor += len(text)
        spans.append((number, start, cursor))
    return "\n\n".join(parts), spans


def _page_at(offset: int, spans: list[tuple[int, int, int]]) -> int | None:
    for number, start, end in spans:
        if start <= offset < end:
            return number
    return spans[-1][0] if spans else None


def _paragraphs(text: str):
    position = 0
    for part in text.split("\n\n"):
        if not part:
            continue
        start = text.find(part, position)
        end = start + len(part)
        position = end
        yield start, end, part


def _windows(text: str, start: int, end: int):
    """Split one paragraph at sentence/newline boundaries, never above CHUNK_MAX."""
    while end - start > CHUNK_MAX:
        limit = start + CHUNK_MAX
        cut = max(
            text.rfind("\n", start, limit),
            text.rfind(". ", start, limit),
            text.rfind("? ", start, limit),
            text.rfind("! ", start, limit),
        )
        stop = cut + 1 if cut >= start + CHUNK_MIN else limit
        yield start, stop
        start = stop
    if end > start:
        yield start, end


def chunk_document(text: str, spans: list[tuple[int, int, int]], *, markdown: bool) -> list[dict]:
    """Deterministic, bounded chunks with page ranges and Markdown headings."""
    units: list[tuple[int, int, str | None]] = []
    heading: str | None = None
    for start, end, block in _paragraphs(text):
        if markdown:
            first = block.split("\n", 1)[0].strip()
            match = _HEADING.match(first)
            if match:
                heading = match.group(1).strip()[:300]
        for window_start, window_end in _windows(text, start, end):
            piece = text[window_start:window_end]
            value = piece.strip()
            if not value:
                continue
            lead = len(piece) - len(piece.lstrip())
            units.append((window_start + lead, window_start + lead + len(value), heading))
    units.sort()

    packed: list[dict] = []
    for start, end, unit_heading in units:
        current = packed[-1] if packed else None
        if (
            current is not None
            and current["heading"] == unit_heading
            and end - current["start"] <= CHUNK_MAX
            and current["end"] - current["start"] < CHUNK_TARGET
        ):
            current["end"] = end
        else:
            packed.append({"start": start, "end": end, "heading": unit_heading})
    if (
        len(packed) > 1
        and packed[-1]["end"] - packed[-1]["start"] < CHUNK_MIN
        and packed[-1]["heading"] == packed[-2]["heading"]
        and packed[-1]["end"] - packed[-2]["start"] <= CHUNK_MAX
    ):
        packed[-2]["end"] = packed[-1]["end"]
        packed.pop()

    chunks = []
    for item in packed:
        value = text[item["start"]:item["end"]].strip()
        if not value:
            continue
        chunks.append(
            {
                "ordinal": len(chunks) + 1,
                "page_from": _page_at(item["start"], spans),
                "page_to": _page_at(max(item["start"], item["end"] - 1), spans),
                "heading": item["heading"],
                "text": value,
                "text_hash": _digest(value),
                "char_count": len(value),
            }
        )
    return chunks


def _active_clos(db: Session, clo_ids: list[int]) -> set[int]:
    wanted = sorted(set(clo_ids))
    if not wanted:
        return set()
    found = set(
        db.scalars(
            select(CourseLearningOutcome.clo_id).where(
                CourseLearningOutcome.clo_id.in_(wanted),
                CourseLearningOutcome.status == "active",
            )
        )
    )
    if found != set(wanted):
        raise AppError(404, "clo_not_found", "Attach documents only to active course learning outcomes")
    return found


def _summary(document: CourseDocument, chunk_count: int) -> DocumentSummary:
    return DocumentSummary(
        document_id=document.document_id,
        title=document.title,
        mime_type=document.mime_type,
        original_filename=document.original_filename,
        sha256=document.sha256,
        char_count=document.char_count,
        page_count=document.page_count,
        chunk_count=chunk_count,
        status=document.status,
        text_policy_version=document.text_policy_version,
        uploaded_by=document.uploaded_by,
        uploaded_at=document.uploaded_at,
        approved_at=document.approved_at,
    )


def _detail(document: CourseDocument) -> DocumentDetail:
    chunks = [
        DocumentChunkResult(
            chunk_id=chunk.chunk_id,
            ordinal=chunk.ordinal,
            page_from=chunk.page_from,
            page_to=chunk.page_to,
            heading=chunk.heading,
            text=chunk.text,
            text_hash=chunk.text_hash,
            char_count=chunk.char_count,
        )
        for chunk in sorted(document.chunks, key=lambda item: item.ordinal)
    ]
    clos = sorted(
        (
            DocumentCloResult(
                clo_id=link.clo_id,
                clo_code=link.clo.clo_code,
                title=link.clo.title,
                status=link.status,
            )
            for link in document.clo_links
            if link.status != "rejected"
        ),
        key=lambda item: (item.clo_code, item.clo_id),
    )
    return DocumentDetail(**_summary(document, len(chunks)).model_dump(), chunks=chunks, clos=clos)


def _get(document_id: int, db: Session) -> CourseDocument:
    document = DocumentRepository(db).get(document_id)
    if document is None:
        raise AppError(404, "document_not_found", "Course document not found")
    return document


def ingest(db: Session, payload, admin) -> DocumentDetail:
    raw = _decode_upload(payload.content_base64)
    filename = Path(payload.filename.replace("\\", "/")).name.strip()
    extension = Path(filename).suffix.lower()
    mime_type = ALLOWED_EXTENSIONS.get(extension)
    if not filename or mime_type is None:
        raise AppError(422, "unsupported_document_type", "Upload a .txt, .md or text-based .pdf file")
    title = payload.title.strip()
    if not title:
        raise AppError(422, "document_title_empty", "A document title is required")

    pages = _read_pdf(raw) if extension == ".pdf" else _read_text(raw)
    text, spans = _prepare_pages(pages)
    if len(text) < MIN_TEXT_CHARS:
        raise AppError(422, "document_text_empty", "The document has no usable text")
    if len(text) > MAX_TEXT_CHARS:
        raise AppError(413, "document_too_large", "The extracted document text is too large")
    chunks = chunk_document(text, spans, markdown=extension == ".md")
    if not chunks:
        raise AppError(422, "document_text_empty", "The document has no usable text")
    if len(chunks) > MAX_CHUNKS:
        raise AppError(413, "document_too_large", "The document splits into too many chunks")

    clos = _active_clos(db, payload.clo_ids) if payload.clo_ids else set()
    repo = DocumentRepository(db)
    document = repo.create(
        title=title,
        mime_type=mime_type,
        original_filename=filename,
        sha256=_digest(text),
        char_count=len(text),
        page_count=len(pages) if extension == ".pdf" else 1,
        status="draft",
        uploaded_by=admin.account_id,
        text_policy_version=TEXT_POLICY_VERSION,
    )
    for chunk in chunks:
        repo.add_chunk(document.document_id, **chunk)
    db.flush()
    if clos:
        repo.replace_clos(document, clos, admin)
    db.commit()
    logger.info(
        "document ingested id=%s chunks=%d chars=%d",
        document.document_id,
        len(chunks),
        len(text),
    )
    return _detail(repo.get(document.document_id))


def list_documents(db: Session, status: str | None = None) -> list[DocumentSummary]:
    return [
        _summary(document, int(chunk_count))
        for document, chunk_count in DocumentRepository(db).list(status)
    ]


def get_document(db: Session, document_id: int) -> DocumentDetail:
    return _detail(_get(document_id, db))


def approve_document(db: Session, document_id: int, admin) -> DocumentDetail:
    repo = DocumentRepository(db)
    document = _get(document_id, db)
    if document.status == "archived":
        raise AppError(409, "document_archived", "An archived document cannot be approved")
    if document.status != "approved":
        document.status = "approved"
        document.approved_by = admin.account_id
        document.approved_at = datetime.now(timezone.utc)
        db.commit()
    return _detail(repo.get(document_id))


def archive_document(db: Session, document_id: int) -> DocumentDetail:
    repo = DocumentRepository(db)
    document = _get(document_id, db)
    if document.status != "archived":
        document.status = "archived"
        db.commit()
    return _detail(repo.get(document_id))


def set_document_clos(db: Session, document_id: int, payload, admin) -> DocumentDetail:
    repo = DocumentRepository(db)
    document = _get(document_id, db)
    if document.status == "archived":
        raise AppError(409, "document_archived", "An archived document cannot be attached to a CLO")
    repo.replace_clos(document, _active_clos(db, payload.clo_ids), admin)
    db.commit()
    return _detail(repo.get(document_id))
