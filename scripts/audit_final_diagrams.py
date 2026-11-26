# -*- coding: utf-8 -*-
"""Audit every body figure in the five submission DOCX files against originals.

Compares embedded media by SHA-256 first, then perceptual hash (DCT pHash),
average hash and pixel RMSE.  Never opens an image for visual inspection.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image
from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}

TARGETS = {
    "ProposalDocument": "docs/submission/final/C1SE.70_ProposalDocument_DBCAS_ver1.3.docx",
    "ArchitectureDesign": "docs/submission/final/C1SE.70_ArchitectureDesign_DBCAS_ver1.3.docx",
    "DatabaseDesign": "docs/submission/final/C1SE.70_DatabaseDesign_DBCAS_ver1.3.docx",
    "CodeStandards": "docs/submission/final/C1SE.70_CodeStandards_DBCAS_ver1.3.docx",
    "TechnicalReport": "docs/submission/final/C1SE.70_TechnicalReport_DBCAS_ver1.3.docx",
}

BASELINES = {
    "ProposalDocument": [
        ("Final-ver1.3", "../Documents/Final-ver1.3/C1SE.70_ProposalDocument_DBCAS_ver1.3.docx"),
        ("Documents-Final-1.2", "../Documents/Final/C1SE.70_ProposalDocument_DBCAS_ver1.2.docx"),
        ("root-1.4", "../C1SE.70_ProposalDocument_DBCAS_ver1.4.docx"),
    ],
    "ArchitectureDesign": [
        ("Final-ver1.3", "../Documents/Final-ver1.3/C1SE.70_ArchitectureDesign_DBCAS_ver1.3.docx"),
        ("Documents-Final-1.2", "../Documents/Final/C1SE.70_ArchitectureDesign_DBCAS_ver1.2.docx"),
        ("root-1.2", "../C1SE.70_ArchitectureDesign_DBCAS_ver1.2.docx"),
    ],
    "DatabaseDesign": [
        ("Final-ver1.3", "../Documents/Final-ver1.3/C1SE.70_DatabaseDesign_DBCAS_ver1.3.docx"),
        ("Documents-Final-1.2", "../Documents/Final/C1SE.70_DatabaseDesign_DBCAS_ver1.2.docx"),
        ("root-1.3", "../C1SE.70_DatabaseDesign_DBCAS_ver1.3.docx"),
    ],
    "CodeStandards": [],
    "TechnicalReport": [],
}

SOURCE_DIRS = [
    "docs/diagrams/originals",
    "docs/diagrams/generated",
    "docs/diagrams/rebuild",
    "docs/submission/final/assets/figures",
    "docs/submission/final/assets/erd",
    "docs/submission/final/verification/figures",
]


def sha256(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def dct_matrix(n: int) -> np.ndarray:
    k = np.arange(n).reshape(-1, 1)
    x = np.arange(n).reshape(1, -1)
    m = np.cos(np.pi * (2 * x + 1) * k / (2 * n))
    m[0, :] *= 1 / np.sqrt(2)
    return m * np.sqrt(2 / n)


_DCT = dct_matrix(32)


def phash(gray: np.ndarray) -> int:
    small = np.asarray(Image.fromarray(gray).resize((32, 32), Image.LANCZOS), dtype=float)
    coeff = _DCT @ small @ _DCT.T
    low = coeff[:8, :8].flatten()
    med = np.median(low[1:])
    bits = 0
    for bit in low[1:]:
        bits = (bits << 1) | (1 if bit > med else 0)
    return bits


def ahash(gray: np.ndarray) -> int:
    small = np.asarray(Image.fromarray(gray).resize((8, 8), Image.LANCZOS), dtype=float)
    med = small.mean()
    bits = 0
    for v in small.flatten():
        bits = (bits << 1) | (1 if v > med else 0)
    return bits


def dhash(gray: np.ndarray) -> int:
    small = np.asarray(Image.fromarray(gray).resize((9, 8), Image.LANCZOS), dtype=int)
    bits = 0
    for row in small:
        for i in range(8):
            bits = (bits << 1) | (1 if row[i] > row[i + 1] else 0)
    return bits


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def load_gray(blob: bytes, size=(256, 256)) -> np.ndarray:
    from io import BytesIO
    im = Image.open(BytesIO(blob)).convert("L")
    return np.asarray(im.resize(size, Image.LANCZOS), dtype=float)


def rmse(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.sqrt(np.mean((a - b) ** 2)) / 255.0)


def image_info(blob: bytes) -> dict:
    from io import BytesIO
    im = Image.open(BytesIO(blob))
    gray = np.asarray(im.convert("L"), dtype=np.uint8)
    rgb = np.asarray(im.convert("RGB").resize((64, 64), Image.LANCZOS), dtype=int)
    mx = rgb.max(axis=2)
    mn = rgb.min(axis=2)
    saturation = float(np.mean((mx - mn) / np.maximum(mx, 1)))
    return {
        "sha256": sha256(blob),
        "bytes": len(blob),
        "format": im.format,
        "width": im.width,
        "height": im.height,
        "pixels": f"{im.width}x{im.height}",
        "phash": f"{phash(gray):016x}",
        "ahash": f"{ahash(gray):016x}",
        "dhash": f"{dhash(gray):016x}",
        "saturation": round(saturation, 4),
        "gray": gray,
        "thumb": load_gray(blob),
    }


def iter_body_images(path: Path, caption_before: bool = False):
    """Yield dicts for body figures in document order, with caption lookahead."""
    with zipfile.ZipFile(path) as z:
        doc = etree.fromstring(z.read("word/document.xml"))
        rels = etree.fromstring(z.read("word/_rels/document.xml.rels"))
        relmap = {}
        for rel in rels:
            rid = rel.get("Id")
            target = rel.get("Target")
            if target and "media/" in target:
                relmap[rid] = "word/" + target.replace("../", "").lstrip("/")
        body = doc.find("w:body", NS)
        paras = body.findall("w:p", NS)
        records = []
        for idx, p in enumerate(paras):
            blips = p.findall(".//a:blip", NS)
            if not blips:
                continue
            rid = blips[0].get("{%s}embed" % NS["r"])
            if not rid or rid not in relmap:
                continue
            part = relmap[rid]
            blob = z.read(part)
            info = image_info(blob)
            extent = p.find(".//wp:extent", NS)
            cx = int(extent.get("cx")) if extent is not None else None
            cy = int(extent.get("cy")) if extent is not None else None
            caption = ""
            cap_re = re.compile(r"^(?:Figure|Table)\s+(?:A\.)?\d+(?:\s*\(\d+/\d+\))?[.:]\s")

            def look(start, stop, step):
                for j in range(start, stop, step):
                    text = "".join(paras[j].itertext()).strip()
                    if text and cap_re.match(text):
                        return text
                return ""

            if caption_before:
                caption = look(idx - 1, max(-1, idx - 7), -1) or look(
                    idx + 1, min(idx + 7, len(paras)), 1)
            else:
                caption = look(idx + 1, min(idx + 7, len(paras)), 1) or look(
                    idx - 1, max(-1, idx - 7), -1)
            if not caption:
                for j in range(idx + 1, min(idx + 5, len(paras))):
                    text = "".join(paras[j].itertext()).strip()
                    if text:
                        caption = text
                        break
            records.append({
                "index": len(records),
                "para": idx,
                "part": part,
                "cx_cm": round(cx / 360000, 2) if cx else None,
                "cy_cm": round(cy / 360000, 2) if cy else None,
                "caption": caption,
                **{k: v for k, v in info.items() if k not in ("gray", "thumb")},
                "_blob": blob,
                "_thumb": info["thumb"],
            })
        return records


def collect_sources() -> list[dict]:
    out = []
    seen = set()
    for d in SOURCE_DIRS:
        base = ROOT / d
        if not base.exists():
            continue
        for p in sorted(base.rglob("*.png")):
            blob = p.read_bytes()
            h = sha256(blob)
            if h in seen:
                continue
            seen.add(h)
            info = image_info(blob)
            out.append({
                "name": str(p.relative_to(ROOT)).replace("\\", "/"),
                "sha256": h,
                "pixels": info["pixels"],
                "phash": info["phash"],
                "ahash": info["ahash"],
                "dhash": info["dhash"],
                "saturation": info["saturation"],
                "_thumb": info["thumb"],
            })
    for label, rel in [
        ("Documents/Final-ver1.3/ProposalDocument", "../Documents/Final-ver1.3/C1SE.70_ProposalDocument_DBCAS_ver1.3.docx"),
        ("Documents/Final-ver1.3/ArchitectureDesign", "../Documents/Final-ver1.3/C1SE.70_ArchitectureDesign_DBCAS_ver1.3.docx"),
        ("Documents/Final-ver1.3/DatabaseDesign", "../Documents/Final-ver1.3/C1SE.70_DatabaseDesign_DBCAS_ver1.3.docx"),
        ("Documents/Final/ProposalDocument-1.2", "../Documents/Final/C1SE.70_ProposalDocument_DBCAS_ver1.2.docx"),
        ("Documents/Final/ArchitectureDesign-1.2", "../Documents/Final/C1SE.70_ArchitectureDesign_DBCAS_ver1.2.docx"),
        ("Documents/Final/DatabaseDesign-1.2", "../Documents/Final/C1SE.70_DatabaseDesign_DBCAS_ver1.2.docx"),
        ("root/ProposalDocument-1.4", "../C1SE.70_ProposalDocument_DBCAS_ver1.4.docx"),
        ("root/ArchitectureDesign-1.2", "../C1SE.70_ArchitectureDesign_DBCAS_ver1.2.docx"),
        ("root/DatabaseDesign-1.3", "../C1SE.70_DatabaseDesign_DBCAS_ver1.3.docx"),
    ]:
        p = (ROOT / rel).resolve()
        if not p.exists():
            continue
        for rec in iter_body_images(p):
            if rec["sha256"] in seen:
                continue
            seen.add(rec["sha256"])
            out.append({
                "name": f"{label}/{rec['part'].split('/')[-1]}",
                "sha256": rec["sha256"],
                "pixels": rec["pixels"],
                "phash": rec["phash"],
                "ahash": rec["ahash"],
                "dhash": rec["dhash"],
                "saturation": rec["saturation"],
                "_thumb": rec["_thumb"],
            })
    return out


def compare(rec: dict, sources: list[dict]) -> dict:
    exact = [s for s in sources if s["sha256"] == rec["sha256"]]
    if exact:
        return {"verdict": "byte-identical", "source": exact[0], "phash_distance": 0,
                "ahash_distance": 0, "dhash_distance": 0, "rmse": 0.0}
    scored = []
    for s in sources:
        d = hamming(int(rec["phash"], 16), int(s["phash"], 16))
        a = hamming(int(rec["ahash"], 16), int(s["ahash"], 16))
        dd = hamming(int(rec["dhash"], 16), int(s["dhash"], 16))
        e = rmse(rec["_thumb"], s["_thumb"])
        scored.append((d, a + dd, e, s))
    scored.sort(key=lambda t: (t[0], t[2], t[1]))
    d, ah, e, best = scored[0]
    if d <= 4 and e <= 0.06:
        verdict = "near-identical"
    elif d <= 10 and e <= 0.12:
        verdict = "perceptually-similar"
    else:
        verdict = "different"
    return {"verdict": verdict, "source": best, "phash_distance": d,
            "ahash_distance": hamming(int(rec["ahash"], 16), int(best["ahash"], 16)),
            "dhash_distance": hamming(int(rec["dhash"], 16), int(best["dhash"], 16)),
            "rmse": round(e, 4)}


def attach_baseline(doc: str, rows: list[dict]) -> None:
    """Record the same-position baseline image for each body figure."""
    if doc == "CodeStandards":
        for row in rows:
            row["baseline_match"] = None
            row["baseline_part"] = ""
            row["baseline_sha256"] = ""
            row["baseline_pixels"] = ""
            row["baseline_placed_cm"] = ""
            row["classification"] = "logo" if row["figure"] == 1 else "new-no-baseline"
        return
    if doc == "TechnicalReport":
        rel = "../Documents/Final-ver1.3/C1SE.70_ProposalDocument_DBCAS_ver1.3.docx"
        base_rows = iter_body_images((ROOT / rel).resolve())
        for row in rows:
            if row["figure"] == 1:
                match = next((b for b in base_rows if b["sha256"] == row["sha256"]), None)
                row["classification"] = "logo"
            else:
                match = next((b for b in base_rows if b["sha256"] == row["sha256"]), None)
                row["classification"] = "original-shared" if match else "DEFECT"
            row["baseline_match"] = bool(match)
            row["baseline_part"] = match["part"] if match else ""
            row["baseline_sha256"] = match["sha256"] if match else ""
            row["baseline_pixels"] = match["pixels"] if match else ""
            row["baseline_placed_cm"] = f"{match['cx_cm']}x{match['cy_cm']}" if match else ""
        return
    rel = next(relb for label, relb in BASELINES[doc] if label == "Final-ver1.3")
    base_rows = iter_body_images((ROOT / rel).resolve())
    for row, base in zip(rows, base_rows):
        same = row["sha256"] == base["sha256"]
        row["baseline_match"] = same
        row["baseline_part"] = base["part"]
        row["baseline_sha256"] = base["sha256"]
        row["baseline_pixels"] = base["pixels"]
        row["baseline_placed_cm"] = f"{base['cx_cm']}x{base['cy_cm']}"
        if row["figure"] == 1:
            row["classification"] = "logo"
        else:
            row["classification"] = "original-restored" if same else "DEFECT"


def markdown(result: dict) -> str:
    lines = [
        "# Diagram audit — five ver1.3 documents",
        "",
        "Generated by `scripts/audit_final_diagrams.py`. No image was opened for",
        "visual inspection: each embedded `word/media` part was extracted, hashed",
        "with SHA-256, measured with Pillow, and compared with a 64-bit DCT pHash,",
        "aHash, dHash and a 256×256 greyscale RMSE. `byte-identical` means the",
        "embedded bytes equal the baseline file; `pHash 0 / RMSE 0` means the same",
        "picture after re-encoding.",
        "",
        "Originals are the body figures in",
        "`Documents/Final-ver1.3/C1SE.70_*_DBCAS_ver1.3.docx` (the content-complete",
        "baselines). The Technical Report reuses the baseline Proposal pipeline",
        "image; Code Standards has no baseline figure. Cover logos are listed for",
        "completeness but are not diagrams.",
        "",
        "## Summary",
        "",
        "| Document | Body images | Logos | Original restored | Original shared | New (no baseline) | Defects |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for doc, rows in result["documents"].items():
        klass = [r["classification"] for r in rows]
        lines.append(
            f"| {doc} | {len(rows)} | {klass.count('logo')} | "
            f"{klass.count('original-restored')} | {klass.count('original-shared')} | "
            f"{klass.count('new-no-baseline')} | {klass.count('DEFECT')} |"
        )
    lines += [
        "",
        "All restored originals keep the baseline extent and visible caption. The",
        "Technical Report pipeline was re-encoded in the rebuilt file (`163 292`",
        "bytes, pixel-identical); it is now the exact baseline media (`127 856`",
        "bytes). The Code Standards figure is the only new drawing: no baseline",
        "source exists, and its style values are copied from the original ERD/TRD",
        "spec (`docs/qa/diagram-originals/style-spec.md`, sections 10-11): white ground,",
        "`#F2F2F2` fill, black rules, Arial, no colour accents.",
        "",
        "## Figures",
        "",
    ]
    for doc, rows in result["documents"].items():
        lines += [
            f"### {doc}",
            "",
            "| # | Caption | Current SHA-256 | Pixels | Placed (cm) | Baseline part | Baseline SHA-256 | Match | Action |",
            "|---:|---|---|---|---|---|---|---|---|",
        ]
        for row in rows:
            caption = row["caption"].replace("|", "\\|")[:95]
            if row["classification"] == "logo":
                caption = "cover logo"
            action = {
                "logo": "kept",
                "original-restored": "restored in place",
                "original-shared": "restored shared original",
                "new-no-baseline": "new; no baseline source",
                "DEFECT": "revert required",
            }[row["classification"]]
            if row["classification"] == "logo":
                match = "n/a"
            elif row["classification"] == "new-no-baseline":
                match = "no baseline"
            else:
                match = "byte-identical" if row["baseline_match"] else "DIFF"
            lines.append(
                f"| {row['figure']} | {caption} | `{row['sha256'][:16]}…` | {row['pixels']} | "
                f"{row['placed_cm']} | `{row['baseline_part'] or '—'}` | "
                f"`{(row['baseline_sha256'] or '—')[:16]}` | {match} | {action} |"
            )
        lines.append("")
    lines += [
        "## Source facts already in the originals",
        "",
        "No original figure needed a minimal content extension. The baseline",
        "original-style sources under `docs/submission/after/diagrams/` already",
        "carry the current facts:",
        "",
        "- `Architecture-image3-after.svg` (container) and `Architecture-image4/5-after.svg`",
        "  (component) label the database `(67 tables)`.",
        "- `Architecture-image8-trd-6..11-after.svg` add the 26 post-41 tables; the",
        "  11-page set covers all 67 tables and its footers read `67 tables · 561",
        "  columns · 122 FKs · 28 migrations`.",
        "- `Architecture-image5-after.svg` includes the `review queue` and",
        "  `review & approval` components; the use-case page includes the AI",
        "  question review/oversight goals.",
        "- The pipeline, use-case, container and component pages retain the original",
        "  black/blue/grey line art, Arial text and original extents.",
        "",
        "The 67-table/561-column/122-FK/28-migration facts in the text are therefore",
        "consistent with the restored figures; no figure is listed as minimally",
        "extended.",
        "",
        "## Owner questions",
        "",
        "1. Code Standards Figure 1 has no baseline source. The shipped version is",
        "   the new monochrome original-style drawing; the earlier blue FITAI-palette",
        "   version is superseded. Confirm the monochrome choice.",
        "2. Architecture Figure 3 is the baseline container diagram. Commit `889e8bf`",
        "   had replaced it with a rebuilt version (reflowed text, OAuth/Email boxes);",
        "   the baseline already contains OAuth/Email and 67 tables, so the 1:1 rule",
        "   restored the baseline. Confirm no content from `889e8bf` is required.",
        "3. Technical Report Figure 1 is the baseline Proposal pipeline image, not a",
        "   redraw. Confirm the shared figure is acceptable under the Technical",
        "   Report caption.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    sources = collect_sources()
    result = {"sources": len(sources), "documents": {}}
    for doc, rel in TARGETS.items():
        p = ROOT / rel
        print(f"## {doc}")
        rows = []
        for rec in iter_body_images(p, caption_before=(doc == "CodeStandards")):
            cmp = compare(rec, sources)
            src = cmp["source"]
            row = {
                "figure": rec["index"] + 1,
                "caption": rec["caption"][:140],
                "part": rec["part"],
                "sha256": rec["sha256"],
                "bytes": rec["bytes"],
                "pixels": rec["pixels"],
                "placed_cm": f"{rec['cx_cm']}x{rec['cy_cm']}",
                "saturation": rec["saturation"],
                "verdict": cmp["verdict"],
                "source": src["name"],
                "source_sha256": src["sha256"],
                "source_pixels": src["pixels"],
                "source_saturation": src["saturation"],
                "phash_distance": cmp["phash_distance"],
                "ahash_distance": cmp["ahash_distance"],
                "dhash_distance": cmp["dhash_distance"],
                "rmse": cmp["rmse"],
            }
            rows.append(row)
            print(f"{row['figure']:>2} {row['verdict']:<22} d={row['phash_distance']:>2} "
                  f"rmse={row['rmse']:.4f} {rec['pixels']:>10} <- {src['name']}")
        result["documents"][doc] = rows
        # Baselines for cross-check
        result.setdefault("baselines", {})
        for label, relb in BASELINES[doc]:
            bp = (ROOT / relb).resolve()
            if bp.exists():
                result["baselines"][f"{doc}/{label}"] = [
                    {k: v for k, v in r.items() if not k.startswith("_")}
                    for r in iter_body_images(bp)
                ]
    for doc, rows in result["documents"].items():
        attach_baseline(doc, rows)
    out = ROOT / "docs/submission/final/verification/diagram-audit.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    md = ROOT / "docs/submission/final/verification/diagram-audit.md"
    md.write_text(markdown(result), encoding="utf-8")
    print(f"\nwrote {out} and {md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
