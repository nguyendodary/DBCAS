# -*- coding: utf-8 -*-
"""Extract text, tables and embedded images from .docx files (stdlib only).

    python scripts/extract_docx_inventory.py <file.docx> [...] -o out.json

Used both for the "before" discrepancy inventory and the final programmatic
verification of the edited Word documents.
"""
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
CP = "{http://schemas.openxmlformats.org/package/2006/metadata/core-properties}"
DC = "{http://purl.org/dc/elements/1.1/}"
DCTERMS = "{http://purl.org/dc/terms/}"


def text_of(element):
    parts = []
    for node in element.iter():
        if node.tag == W + "t" and node.text:
            parts.append(node.text)
        elif node.tag == W + "tab":
            parts.append("\t")
        elif node.tag in (W + "br", W + "cr"):
            parts.append("\n")
    return "".join(parts)


def extract(path):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        doc = ET.fromstring(z.read("word/document.xml"))
        styles = {}
        if "word/styles.xml" in names:
            sroot = ET.fromstring(z.read("word/styles.xml"))
            for st in sroot.findall(W + "style"):
                sid = st.get(W + "styleId")
                nm = st.find(W + "name")
                styles[sid] = nm.get(W + "val") if nm is not None else sid
        paragraphs = []
        for p in doc.iter(W + "p"):
            ppr = p.find(W + "pPr")
            sid = None
            if ppr is not None:
                ps = ppr.find(W + "pStyle")
                if ps is not None:
                    sid = ps.get(W + "val")
            t = text_of(p).strip()
            if t:
                paragraphs.append({"style": sid, "style_name": styles.get(sid), "text": t})
        tables = []
        for tbl in doc.iter(W + "tbl"):
            rows = []
            for tr in tbl.findall(W + "tr"):
                rows.append([text_of(tc).strip() for tc in tr.findall(W + "tc")])
            tables.append(rows)
        media = []
        for n in names:
            if n.startswith("word/media/"):
                data = z.read(n)
                media.append({"name": n, "bytes": len(data),
                              "sha256": hashlib.sha256(data).hexdigest()})
        drawing_refs = len(list(doc.iter(W + "drawing"))) + len(list(doc.iter("{urn:schemas-microsoft-com:vml}imagedata")))
        core = {}
        if "docProps/core.xml" in names:
            croot = ET.fromstring(z.read("docProps/core.xml"))
            for tag, key in ((DC + "title", "title"), (DC + "creator", "creator"),
                             (CP + "lastModifiedBy", "last_modified_by"),
                             (DCTERMS + "created", "created"), (DCTERMS + "modified", "modified"),
                             (CP + "revision", "revision")):
                el = croot.find(tag)
                if el is not None and el.text:
                    core[key] = el.text
        app = {}
        if "docProps/app.xml" in names:
            aroot = ET.fromstring(z.read("docProps/app.xml"))
            for tag, key in (("{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}Pages", "pages"),
                             ("{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}Words", "words")):
                el = aroot.find(tag)
                if el is not None and el.text:
                    app[key] = el.text
        # relationship ids for images (used by the editor to replace figures)
        rels = {}
        if "word/_rels/document.xml.rels" in names:
            rroot = ET.fromstring(z.read("word/_rels/document.xml.rels"))
            for rel in rroot:
                if "image" in (rel.get("Type") or ""):
                    rels[rel.get("Id")] = rel.get("Target")
        embed_ids = [b.get(R + "embed") for b in doc.iter(W + "blip") if b.get(R + "embed")]
    return {
        "file": str(path), "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "core": core, "app": app,
        "paragraph_count": len(paragraphs), "table_count": len(tables),
        "image_count": len(media), "drawing_refs": drawing_refs,
        "paragraphs": paragraphs, "tables": tables, "media": media,
        "image_rels": rels, "embed_ids": embed_ids,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("-o", "--output")
    args = ap.parse_args()
    data = [extract(Path(f)) for f in args.files]
    out = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        Path(args.output).write_text(out, encoding="utf-8")
        for d in data:
            print(f"{Path(d['file']).name}: {d['paragraph_count']} paragraphs, "
                  f"{d['table_count']} tables, {d['image_count']} images, "
                  f"{d['drawing_refs']} drawing refs, pages={d['app'].get('pages')}")
    else:
        print(out)


if __name__ == "__main__":
    main()
