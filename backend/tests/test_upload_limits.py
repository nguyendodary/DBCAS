"""The reverse proxy must accept every document upload the API accepts.

The browser sends the file as base64 inside JSON, so the HTTP body is about
4/3 of the binary size plus JSON overhead.  A limit below that silently turns
valid uploads into Nginx 413 responses before the application can report the
document error.
"""
from pathlib import Path
import re

from app.services.document_service import MAX_BASE64_CHARS, MAX_UPLOAD_JSON_BYTES

ROOT = Path(__file__).resolve().parents[2]
NGINX = ROOT / "deploy" / "nginx.conf"


def _nginx_body_limit_bytes() -> int:
    text = NGINX.read_text(encoding="utf-8")
    match = re.search(r"^\s*client_max_body_size\s+(\d+)([kmg]?);", text, re.M)
    assert match, "client_max_body_size is missing from deploy/nginx.conf"
    value = int(match.group(1))
    unit = match.group(2).lower()
    factor = {"": 1, "k": 1024, "m": 1024**2, "g": 1024**3}[unit]
    return value * factor


def test_nginx_accepts_full_document_upload_json():
    limit = _nginx_body_limit_bytes()
    assert limit >= MAX_UPLOAD_JSON_BYTES
    assert MAX_UPLOAD_JSON_BYTES >= MAX_BASE64_CHARS


def test_nginx_limit_is_not_effectively_unbounded():
    # Keep the proxy from becoming an accidental unlimited upload endpoint.
    assert _nginx_body_limit_bytes() <= 64 * 1024**2
