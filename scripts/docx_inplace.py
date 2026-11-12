# -*- coding: utf-8 -*-
"""Minimal in-place .docx text editing that preserves the original package.

Only ``word/document.xml`` text nodes are changed. Paragraph/run properties,
styles, numbering, tables, headers, footers, fields and all other parts are
left byte-for-byte identical.

    python scripts/docx_inplace.py <src.docx> <dst.docx> <edits.json>

``edits.json`` is a list of objects:
    {"old": "...", "new": "...", "count": 1}   # count optional, default all
or
    {"paragraph": "exact old paragraph text", "new": "..."}
"""
import json
import shutil
import sys
import zipfile
from pathlib import Path

from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML = "http://www.w3.org/XML/1998/namespace"
NS = {"w": W}


def q(tag):
    return f"{{{W}}}{tag}"


def paragraph_text(p):
    parts = []
    for el in p.iter():
        if el.tag == q("t"):
            parts.append(el.text or "")
        elif el.tag == q("tab"):
            parts.append("\t")
        elif el.tag in (q("br"), q("cr")):
            parts.append("\n")
    return "".join(parts)


def _text_nodes(p):
    """Return [(node, run, text)] for every w:t in document order."""
    out = []
    for run in p.iter(q("r")):
        for node in run.iter(q("t")):
            out.append((node, run, node.text or ""))
    return out


def _has_field(p):
    return any(el.tag in (q("fldChar"), q("instrText")) for el in p.iter())


def _set_text(node, text):
    node.text = text
    if text != text.strip():
        node.set(f"{{{XML}}}space", "preserve")


def replace_in_paragraph(p, old, new):
    """Replace ``old`` in a paragraph, preserving the run that starts the match."""
    if not old:
        return 0
    if _has_field(p):
        # Never edit inside TOC/caption/SEQ field results.
        return 0
    nodes = _text_nodes(p)
    full = "".join(t for _, _, t in nodes)
    start = full.find(old)
    if start < 0:
        return 0

    # Refuse matches that span a tab/break (not representable by w:t).
    if "\t" in old or "\n" in old:
        return 0

    end = start + len(old)
    pos = 0
    replaced = False
    for node, _run, text in nodes:
        nstart, nend = pos, pos + len(text)
        pos = nend
        if nend <= start or nstart >= end:
            continue
        local_start = max(start, nstart) - nstart
        local_end = min(end, nend) - nstart
        if not replaced:
            _set_text(node, text[:local_start] + new + text[local_end:])
            replaced = True
        else:
            _set_text(node, text[:local_start] + text[local_end:])
    return 1 if replaced else 0


def iter_paragraphs(root):
    body = root.find(q("body"))
    if body is None:
        return
    for p in body.iter(q("p")):
        yield p


def apply_edits(root, edits):
    counts = []
    for edit in edits:
        old = edit.get("old")
        if old is None:
            old = edit.get("paragraph")
        new = edit["new"]
        want = edit.get("count")
        if old is None:
            raise ValueError(f"edit has no old/paragraph: {edit}")
        done = 0
        for p in iter_paragraphs(root):
            if want is not None and done >= want:
                break
            if want is None:
                done += replace_in_paragraph(p, old, new)
            elif done < want:
                done += replace_in_paragraph(p, old, new)
        counts.append((old[:80], done, want))
    return counts


def edit_docx(src, dst, edits):
    src, dst = Path(src), Path(dst)
    shutil.copyfile(src, dst)
    with zipfile.ZipFile(src) as zin:
        xml = zin.read("word/document.xml")
    parser = etree.XMLParser(remove_blank_text=False, huge_tree=True)
    root = etree.fromstring(xml, parser)
    counts = apply_edits(root, edits)
    new_xml = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)

    tmp = dst.with_suffix(".tmp")
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                data = new_xml
            zout.writestr(item, data)
    tmp.replace(dst)
    return counts


def main():
    src, dst, edits_path = sys.argv[1:4]
    edits = json.loads(Path(edits_path).read_text(encoding="utf-8"))
    counts = edit_docx(src, dst, edits)
    for old, done, want in counts:
        flag = "OK" if (want is None and done) or done == want else "CHECK"
        print(f"{flag} {done}x (want {want}): {old!r}")


if __name__ == "__main__":
    main()
