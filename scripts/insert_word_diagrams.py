# -*- coding: utf-8 -*-
"""Insert the approved rebuild diagrams into the three v1.2 Word packages.

Works on copies under C:/tmp/dbcas_word (no spaces).  Images are replaced at
the package level so anchors, styles, headers/footers and captions stay in
place.  Component (Figure 4) becomes 08a/08b and the TRD (Figure 8 / Figure 2)
becomes five pages; the extra captions use SEQ Figure with \\r so the original
numbering of following figures does not change.

Run:  python scripts/insert_word_diagrams.py
"""
import copy
import json
import os
import shutil
import zipfile
from pathlib import Path

from lxml import etree
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ACA = ROOT / "docs" / "academic"
TMP = Path(r"C:\tmp\dbcas_word")
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC = "http://schemas.openxmlformats.org/drawingml/2006/picture"
WP14 = "http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
q = lambda ns, t: f"{{{ns}}}{t}"

REBUILD = ROOT / "docs" / "diagrams" / "rebuild"
PREVIEW = ROOT / "docs" / "qa" / "rebuild-preview"

DOCS = {
    "proposal": {
        "src": ACA / "C1SE.70_ProposalDocument_DBCAS_ver1.2.docx",
        "out": TMP / "proposal.docx",
        "replace": [
            # (media file, new png, width EMU or None to keep, split spec)
            ("media/image3.png", PREVIEW / "system-context" / "final.png", None),
            ("media/image4.png", REBUILD / "logical" / "logical.png", None),
            ("media/image5.png", REBUILD / "pipeline" / "pipeline.png", None),
        ],
    },
    "architecture": {
        "src": ACA / "C1SE.70_ArchitectureDesign_DBCAS_ver1.2.docx",
        "out": TMP / "architecture.docx",
        "replace": [
            ("media/image2.png", REBUILD / "use-case" / "use-case.png", None),
            ("media/image3.png", PREVIEW / "system-context" / "final.png", None),
            ("media/image4.png", REBUILD / "container" / "container.png", 5580000),
            ("media/image6.png", REBUILD / "module" / "module.png", None),
            ("media/image7.png", REBUILD / "allocation" / "allocation.png", 5431536),
            ("media/image8.png", REBUILD / "erd" / "erd.png", 8712000),
        ],
        "split": [
            {
                "media": "media/image5.png",
                "pages": [REBUILD / "component" / "component-08a.png",
                          REBUILD / "component" / "component-08b.png"],
                "width_emu": 7315200,  # 8.00 in, image + heading + caption on one landscape page
                "number": 4,
                "total": 2,
                "suffix_after_number": True,
                "captions": [
                    "Component Diagram \u2014 controllers, services and repositories: "
                    "Auth, Practice, Curriculum and Question Bank.",
                    "Component Diagram \u2014 Analytics/Competency & Gap, Grading and "
                    "Accounts/Admin & Settings. The Database cylinder is repeated for "
                    "connector context; it is identical to Figure 4 (1/2).",
                ],
            },
            {
                "media": "media/image9.png",
                "pages": [REBUILD / "trd" / "trd-1.png",
                          REBUILD / "trd" / "trd-2.png",
                          REBUILD / "trd" / "trd-3.png",
                          REBUILD / "trd" / "trd-4.png",
                          REBUILD / "trd" / "trd-5.png"],
                "width_emu": 7877175,  # original 8.614 in
                "number": 8,
                "total": 5,
                "suffix_after_number": False,
                "captions": ["Table Relationship Diagram"] * 5,
            },
        ],
    },
    "database": {
        "src": ACA / "C1SE.70_DatabaseDesign_DBCAS_ver1.2.docx",
        "out": TMP / "database.docx",
        "replace": [
            ("media/image3.png", REBUILD / "erd" / "erd.png", None),
        ],
        "split": [
            {
                "media": "media/image4.png",
                "pages": [REBUILD / "trd" / "trd-1.png",
                          REBUILD / "trd" / "trd-2.png",
                          REBUILD / "trd" / "trd-3.png",
                          REBUILD / "trd" / "trd-4.png",
                          REBUILD / "trd" / "trd-5.png"],
                "width_emu": 8649335,  # original 9.458 in
                "number": 2,
                "total": 5,
                "suffix_after_number": False,
                "captions": ["Table Relationship Diagram"] * 5,
            },
        ],
    },
}


def png_size(path):
    with Image.open(path) as im:
        return im.size


def set_extent(inline, cx, cy):
    wp = inline.find(q(WP, "extent"))
    wp.set("cx", str(int(cx)))
    wp.set("cy", str(int(cy)))
    # picture frame
    for ext in inline.iter(q(A, "ext")):
        ext.set("cx", str(int(cx)))
        ext.set("cy", str(int(cy)))


def seq_instr(p):
    """Return ('simple', fld, instr) or ('complex', run, instrText) or None."""
    fld = p.find(q(W, "fldSimple"))
    if fld is not None and "SEQ Figure" in (fld.get(q(W, "instr")) or ""):
        return "simple", fld, None
    for r in p.findall(q(W, "r")):
        it = r.find(q(W, "instrText"))
        if it is not None and "SEQ Figure" in (it.text or ""):
            return "complex", r, it
    return None


def caption_parts(p):
    runs = p.findall(q(W, "r"))
    texts = [(r, r.find(q(W, "t"))) for r in runs if r.find(q(W, "t")) is not None]
    result = None
    sep = None
    for i, r in enumerate(runs):
        fc = r.find(q(W, "fldChar"))
        if fc is not None and fc.get(q(W, "fldCharType")) == "separate":
            sep = i
    if sep is not None:
        for i in range(sep + 1, len(runs)):
            t = runs[i].find(q(W, "t"))
            if t is not None:
                result = (runs[i], t)
                break
    return texts, result


def set_caption(p, number, page, total, body, suffix_after_number, reset):
    kind = seq_instr(p)
    assert kind, "no SEQ Figure field"
    texts, result = caption_parts(p)
    assert len(texts) >= 3
    fig_t = texts[0][1]
    punc_t = texts[-2][1]
    body_t = texts[-1][1]
    fig_t.text = "Figure "
    if suffix_after_number:
        punc_t.text = " (%d/%d). " % (page, total)
        body_t.text = body
    else:
        prefix = "" if (punc_t.text or "").endswith(" ") else " "
        body_t.text = prefix + ("%s (%d/%d)" % (body, page, total))
    instr = " SEQ Figure \\* ARABIC " + ("\\r %d " % number if reset else "")
    if kind[0] == "simple":
        fld = kind[1]
        fld.set(q(W, "instr"), instr)
        ft = fld.find(".//" + q(W, "t"))
        ft.text = str(number)
    else:
        kind[2].text = instr
        assert result is not None
        result[1].text = str(number)


def is_figure_caption(p):
    return seq_instr(p) is not None


def unique_id(root, tag, attr, start=900000):
    used = [int(el.get(q(W, attr))) for el in root.iter(q(W, tag))
            if el.get(q(W, attr)) and el.get(q(W, attr)).isdigit()]
    n = max([start] + used) + 1
    return n, used


def replace_media_bytes(zin, zout, replacements, new_files):
    """Rewrite zip replacing media bytes and adding new_files {name: bytes}."""
    with zipfile.ZipFile(zin) as zi, zipfile.ZipFile(zout, "w", zipfile.ZIP_DEFLATED) as zo:
        for item in zi.infolist():
            data = zi.read(item.filename)
            if item.filename in replacements:
                data = replacements[item.filename]
            zo.writestr(item, data)
        for name, data in new_files.items():
            zo.writestr(name, data)


def process(key, spec):
    src, out = spec["src"], spec["out"]
    with zipfile.ZipFile(src) as z:
        names = set(z.namelist())
        doc = etree.fromstring(z.read("word/document.xml"))
        rels = etree.fromstring(z.read("word/_rels/document.xml.rels"))
        rel_target = {r.get("Id"): r.get("Target") for r in rels}
        rel_id = {v: k for k, v in rel_target.items()}
        media_bytes = {n: z.read(n) for n in names if n.startswith("word/media/")}

    body = doc.find(q(W, "body"))
    paras = body.findall(".//" + q(W, "p"))

    # media replacements for single images
    media_out = {}
    for media, newpng, width in spec.get("replace", []):
        assert ("word/" + media) in media_bytes, (key, media)
        media_out["word/" + media] = Path(newpng).read_bytes()
        w, h = png_size(newpng)
        rid = rel_id[media]
        for p in paras:
            for inline in p.iter(q(WP, "inline")):
                blip = inline.find(".//" + q(A, "blip"))
                if blip is None or blip.get(q(R, "embed")) != rid:
                    continue
                ext = inline.find(q(WP, "extent"))
                cx = width if width else int(ext.get("cx"))
                cy = round(cx * h / w)
                set_extent(inline, cx, cy)
                print("%-12s %-14s %sx%s px -> %.3f x %.3f in"
                      % (key, media, w, h, cx / 914400, cy / 914400))

    # splits
    new_files = {}
    max_rid = max(int(n[3:]) for n in rel_target if n.startswith("rId"))
    for sp in spec.get("split", []):
        media = sp["media"]
        assert ("word/" + media) in media_bytes, (key, media)
        pages = sp["pages"]
        rid = rel_id[media]
        # find image paragraph and its following caption paragraph
        img_p = cap_p = None
        for i, p in enumerate(paras):
            found = False
            for inline in p.iter(q(WP, "inline")):
                blip = inline.find(".//" + q(A, "blip"))
                if blip is not None and blip.get(q(R, "embed")) == rid:
                    found = True
            if found:
                img_p = p
                # next paragraph with a SEQ Figure field (simple or complex)
                j = i + 1
                while j < len(paras):
                    if is_figure_caption(paras[j]):
                        cap_p = paras[j]
                        break
                    j += 1
                break
        assert img_p is not None and cap_p is not None, (key, media)
        parent = img_p.getparent()
        # first page uses the existing paragraph/media
        media_out["word/" + media] = Path(pages[0]).read_bytes()
        w0, h0 = png_size(pages[0])
        cx = sp["width_emu"]
        cy = round(cx * h0 / w0)
        inline = img_p.find(".//" + q(WP, "inline"))
        set_extent(inline, cx, cy)
        # delete any stale break hint
        for lr in img_p.iter(q(W, "lastRenderedPageBreak")):
            lr.getparent().remove(lr)
        # first caption
        suffix_after = sp["suffix_after_number"]
        set_caption(cap_p, sp["number"], 1, sp["total"],
                    sp["captions"][0], suffix_after, reset=False)
        # build extra pages after caption 1
        cursor = cap_p
        bm_id, used = unique_id(doc, "bookmarkStart", "id")
        for page in range(2, len(pages) + 1):
            new_rid = "rId%d" % (max_rid + 1)
            max_rid += 1
            new_media = "media/image%d.png" % (len(media_bytes) + len(new_files) + 1)
            # ensure the name is free
            while new_media in media_bytes:
                new_media = "media/image%d.png" % (int(new_media.split("image")[1].split(".")[0]) + 1)
            new_media_full = "word/" + new_media
            new_files[new_media_full] = Path(pages[page - 1]).read_bytes()
            rel = etree.SubElement(rels, q(REL, "Relationship"))
            rel.set("Id", new_rid)
            rel.set("Type", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image")
            rel.set("Target", new_media)

            ip = copy.deepcopy(img_p)
            ip_pr = ip.find(q(W, "pPr"))
            if ip_pr is not None:
                for kn in ip_pr.findall(q(W, "keepNext")):
                    ip_pr.remove(kn)
                if ip_pr.find(q(W, "pageBreakBefore")) is None:
                    ip_pr.insert(0, etree.Element(q(W, "pageBreakBefore")))
            ip_inline = ip.find(".//" + q(WP, "inline"))
            blip = ip_inline.find(".//" + q(A, "blip"))
            blip.set(q(R, "embed"), new_rid)
            wp_docpr = ip_inline.find(q(WP, "docPr"))
            wp_docpr.set("id", str(900000 + page + sp["number"] * 100))
            wp_docpr.set("name", "figure-%d-page-%d" % (sp["number"], page))
            wp_docpr.set("descr", "figure-%d-page-%d" % (sp["number"], page))
            c_nv = ip_inline.find(".//" + q(PIC, "cNvPr"))
            c_nv.set("id", str(900000 + page + sp["number"] * 100))
            c_nv.set("name", "figure-%d-page-%d" % (sp["number"], page))
            wj, hj = png_size(pages[page - 1])
            set_extent(ip_inline, cx, round(cx * hj / wj))
            for lr in ip.iter(q(W, "lastRenderedPageBreak")):
                lr.getparent().remove(lr)
            cp = copy.deepcopy(cap_p)
            # unique paragraph id
            pid = 0x50000000 + sp["number"] * 1000 + page
            cp.set("{http://schemas.microsoft.com/office/word/2010/wordml}paraId", "%08X" % pid)
            for bs in cp.findall(q(W, "bookmarkStart")):
                bm_id += 1
                bs.set(q(W, "id"), str(bm_id))
                bs.set(q(W, "name"), "_Toc%09d" % bm_id)
            for be in cp.findall(q(W, "bookmarkEnd")):
                be.set(q(W, "id"), str(bm_id))
            set_caption(cp, sp["number"], page, sp["total"],
                        sp["captions"][page - 1], suffix_after, reset=True)
            parent.insert(parent.index(cursor) + 1, ip)
            parent.insert(parent.index(cursor) + 2, cp)
            cursor = cp
            print("%-12s %-14s page %d/%d -> rId %s %s (%.3f x %.3f in)"
                  % (key, media, page, len(pages), new_rid, new_media,
                     cx / 914400, cx * hj / wj / 914400))

    # Word treats drawings with duplicate wp14:anchorId/editId as the same
    # object and may relocate them during field updates.  Give every drawing
    # (originals included) a unique anchor, docPr id and picture id.
    for idx, inline in enumerate(doc.iter(q(WP, "inline")), 1):
        inline.set(q(WP14, "anchorId"), "%08X" % (0xA0000000 + idx))
        inline.set(q(WP14, "editId"), "%08X" % (0xB0000000 + idx))
        docpr = inline.find(q(WP, "docPr"))
        if docpr is not None:
            docpr.set("id", str(100000 + idx))
        for cnv in inline.iter(q(PIC, "cNvPr")):
            cnv.set("id", str(200000 + idx))

    TMP.mkdir(parents=True, exist_ok=True)
    tmpdoc = TMP / (key + ".document.xml")
    tmpdoc.write_bytes(etree.tostring(doc, xml_declaration=True, encoding="UTF-8",
                                      standalone=True))
    tmprels = TMP / (key + ".rels.xml")
    tmprels.write_bytes(etree.tostring(rels, xml_declaration=True, encoding="UTF-8",
                                       standalone=True))

    # rewrite package with modified xml + media
    with zipfile.ZipFile(src) as zi, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zo:
        for item in zi.infolist():
            data = zi.read(item.filename)
            if item.filename == "word/document.xml":
                data = tmpdoc.read_bytes()
            elif item.filename == "word/_rels/document.xml.rels":
                data = tmprels.read_bytes()
            elif item.filename in media_out:
                data = media_out[item.filename]
            zo.writestr(item, data)
        for name, data in new_files.items():
            zo.writestr(name, data)
    size = out.stat().st_size
    with zipfile.ZipFile(out) as z:
        bad = z.testzip()
        media = [n for n in z.namelist() if n.startswith("word/media/")]
    print("%-12s -> %s  %.1f MB  media=%d  ziptest=%s"
          % (key, out.name, size / 1024 / 1024, len(media), bad or "OK"))


def main():
    TMP.mkdir(parents=True, exist_ok=True)
    for key, spec in DOCS.items():
        process(key, spec)
    print("\nPrepared copies in", TMP)


if __name__ == "__main__":
    main()
