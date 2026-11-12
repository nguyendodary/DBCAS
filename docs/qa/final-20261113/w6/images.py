# -*- coding: utf-8 -*-
"""Map image relationships per package part and inspect dimensions/alpha."""
import io
import json
import zipfile
from pathlib import Path

from PIL import Image
from lxml import etree

ROOT = Path(__file__).resolve().parents[4]
ACA = ROOT / "docs/academic"
FILES = [
    ("proposal", "C1SE.70_ProposalDocument_DBCAS_ver1.2.docx"),
    ("architecture", "C1SE.70_ArchitectureDesign_DBCAS_ver1.2.docx"),
    ("database", "C1SE.70_DatabaseDesign_DBCAS_ver1.2.docx"),
]
OUT = Path(__file__).resolve().parent
R = "http://schemas.openxmlformats.org/package/2006/relationships"


def rels(z, part):
    base = part.rsplit("/", 1)[0]
    name = part.rsplit("/", 1)[1]
    relpart = f"{base}/_rels/{name}.rels"
    if relpart not in z.namelist():
        return {}
    root = etree.fromstring(z.read(relpart))
    return {r.get("Id"): r.get("Target") for r in root.findall(f"{{{R}}}Relationship")}


def main():
    report = {}
    for slug, name in FILES:
        rows = []
        with zipfile.ZipFile(ACA / name) as z:
            parts = [n for n in z.namelist() if n.startswith("word/header") and n.endswith(".xml")]
            parts += [n for n in z.namelist() if n.startswith("word/footer") and n.endswith(".xml")]
            parts += ["word/document.xml"]
            for part in parts:
                if part not in z.namelist():
                    continue
                r = rels(z, part)
                root = etree.fromstring(z.read(part))
                used = sorted({v for k, v in r.items() if k in
                               {e.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")
                                for e in root.iter() if e.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")}
                               or v.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".emf", ".wmf", ".svg"))})
                for target in used:
                    mname = "word/" + target.lstrip("/") if not target.startswith("word/") else target
                    if mname not in z.namelist():
                        rows.append({"part": part, "target": target, "error": "missing"})
                        continue
                    b = z.read(mname)
                    info = {"part": part, "target": mname, "bytes": len(b)}
                    try:
                        im = Image.open(io.BytesIO(b))
                        info.update({"format": im.format, "mode": im.mode, "size": im.size})
                        if im.mode in ("RGBA", "LA"):
                            alpha = im.getchannel("A")
                            info["alpha_range"] = [alpha.getextrema()[0], alpha.getextrema()[1]]
                            info["alpha_zero_pct"] = round(
                                100.0 * sum(1 for p in alpha.getdata() if p == 0) / (im.width * im.height), 2)
                    except Exception as exc:
                        info["image_error"] = str(exc)
                    rows.append(info)
        report[slug] = rows
    (OUT / "images.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    for slug, rows in report.items():
        print(slug)
        for r in rows:
            print(" ", r.get("part"), r.get("target"), r.get("size"), r.get("mode"), r.get("bytes"),
                  r.get("alpha_zero_pct"), r.get("error", ""), r.get("image_error", ""))


if __name__ == "__main__":
    main()
