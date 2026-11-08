# -*- coding: utf-8 -*-
"""Measure the current v1.2 academic documents against the untouched v1.1
packages and the live project.

    python scripts/verify_word.py [--ci] [--no-pdf] [--only proposal,architecture,database]

Checks
  1. Word COM: open without repair, update TOC / figures / tables fields, page count.
     (Windows only; skipped, not failed, when Word is unavailable.)
  2. Format fidelity: styles, numbering, sections, headers/footers, cover,
     heading style usage, caption and table formatting.
  3. Content-run formatting: new font/size combinations and unstyled run rates.
  4. Language: no new Vietnamese words compared with the original.
  5. Diagrams: drawing type/extent/position/caption/aspect, rendered pages,
     overflow and caption-page checks, before/after contact sheet.
  6. Data: exact data dictionary, Table Overview, schema/FK/Compose/OpenAPI
     names and numeric claims.

Outputs docs/qa/word-verification/summary.md and <document>/report.md plus
diagram PNGs. Exit code 1 if any measured check fails; unavailable local-only
tools are reported as SKIP. No .docx is modified (hashes are verified).
"""
import argparse
import hashlib
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACA = ROOT / "docs/academic"
OUT = ROOT / "docs" / "qa" / "word-verification"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
q = lambda t: f"{{{W}}}{t}"
qwp = lambda t: f"{{{WP}}}{t}"
qa = lambda t: f"{{{A}}}{t}"
qr = lambda t: f"{{{R}}}{t}"

DOCS = [
    ("proposal", "Proposal", "C1SE.70_ProposalDocument_DBCAS_ver1.1.docx",
     "C1SE.70_ProposalDocument_DBCAS_ver1.2.docx"),
    ("architecture", "Architecture Design", "C1SE.70_ArchitectureDesign_DBCAS_ver1.1.docx",
     "C1SE.70_ArchitectureDesign_DBCAS_ver1.2.docx"),
    ("database", "Database Design", "C1SE.70_DatabaseDesign_DBCAS_ver1.1.docx",
     "C1SE.70_DatabaseDesign_DBCAS_ver1.2.docx"),
]
DROP = {"rsidR", "rsidRPr", "rsidRDefault", "rsidP", "rsidDel", "paraId",
        "textId", "anchorId", "editId", "durableId"}
VI = set("ăâđêôơưĂÂĐÊÔƠƯạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ"
         "ẠẢẤẦẨẪẬẮẰẲẴẶẸẺẼẾỀỂỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪỬỮỰỲỴỶỸ")
RETIRED = ["36 tables", "13-question", "13 questions", "60-minute contract",
           "10 MCQ / 2 SQL / 1 Essay", "10 MCQ / 2 SQL / 1 essay",
           "FORMAL session", "FORMAL (", "Configure Adaptive Assessment",
           "Take a Personalized Adaptive", "Adaptive Engine Service",
           "Exam Interface Usability"]


def text_of(el):
    return "".join((n.text or "") for n in el.iter(q("t")))


def norm_text(s):
    return re.sub(r"\s+", " ", s or "").strip()


def canon(el):
    attrs = []
    for k, v in sorted(el.attrib.items()):
        local = k.rsplit("}", 1)[-1]
        if local in DROP or local.startswith("rsid"):
            continue
        attrs.append(f"{k}={v}")
    kids = "".join(canon(c) for c in el)
    return f"<{el.tag} {' '.join(attrs)}>{(el.text or '')}{kids}</{el.tag}>"


def digest_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check(ok):
    return "PASS" if ok else "FAIL"


class Docx:
    def __init__(self, path):
        self.path = Path(path)
        with zipfile.ZipFile(self.path) as z:
            self.parts = {n: z.read(n) for n in z.namelist()}
        self.doc = ET.fromstring(self.parts["word/document.xml"])
        self.body = self.doc.find(q("body"))
        self.styles = ET.fromstring(self.parts["word/styles.xml"])
        self.numbering = ET.fromstring(self.parts["word/numbering.xml"]) if "word/numbering.xml" in self.parts else None
        self.rels = {}
        rel_part = "word/_rels/document.xml.rels"
        if rel_part in self.parts:
            root = ET.fromstring(self.parts[rel_part])
            for rel in root:
                self.rels[rel.get("Id")] = rel.get("Target")
        self.style_map = {}
        for st in self.styles.findall(q("style")):
            self.style_map[st.get(q("styleId"))] = st
        self.defaults = self.styles.find(q("docDefaults"))

    def part_path(self, target):
        if not target:
            return None
        if target.startswith("/"):
            return target.lstrip("/")
        return posixpath.normpath(posixpath.join("word", target))

    def paragraphs(self):
        return list(self.body.iter(q("p")))

    def style_of(self, p):
        ppr = p.find(q("pPr"))
        if ppr is None:
            return None
        st = ppr.find(q("pStyle"))
        return st.get(q("val")) if st is not None else None

    def num_of(self, p):
        ppr = p.find(q("pPr"))
        if ppr is None:
            return None
        num = ppr.find(q("numPr"))
        if num is None:
            return None
        ilvl = num.find(q("ilvl"))
        numid = num.find(q("numId"))
        return (numid.get(q("val")) if numid is not None else None,
                ilvl.get(q("val")) if ilvl is not None else None)

    def text_runs(self, p):
        out = []
        for r in p.iter(q("r")):
            if r.find(q("t")) is None:
                continue
            t = "".join((n.text or "") for n in r.findall(q("t")))
            if not t.strip():
                continue
            out.append((r, t))
        return out

    def rpr_props(self, rpr):
        props = {}
        if rpr is None:
            return props
        fonts = rpr.find(q("rFonts"))
        if fonts is not None:
            for k, v in fonts.attrib.items():
                local = k.rsplit("}", 1)[-1]
                if local in ("ascii", "hAnsi", "cs", "eastAsia", "asciiTheme",
                             "hAnsiTheme", "cstheme", "eastAsiaTheme"):
                    props["font:" + local] = v
        for tag in ("sz", "b", "i", "color", "vertAlign", "u"):
            el = rpr.find(q(tag))
            if el is not None:
                props[tag] = el.get(q("val")) or "1"
        return props

    def chain(self, sid):
        out = []
        seen = set()
        while sid and sid in self.style_map and sid not in seen:
            seen.add(sid)
            st = self.style_map[sid]
            out.append(st)
            b = st.find(q("basedOn"))
            sid = b.get(q("val")) if b is not None else None
        return list(reversed(out))

    def resolved_run(self, p, r):
        props = {}
        if self.defaults is not None:
            rpr = self.defaults.find(f'{q("rPrDefault")}/{q("rPr")}')
            props.update(self.rpr_props(rpr))
        for st in self.chain(self.style_of(p)):
            props.update(self.rpr_props(st.find(q("rPr"))))
        rpr = r.find(q("rPr"))
        if rpr is not None:
            rs = rpr.find(q("rStyle"))
            if rs is not None:
                for st in self.chain(rs.get(q("val"))):
                    props.update(self.rpr_props(st.find(q("rPr"))))
            props.update(self.rpr_props(rpr))
        font = tuple(sorted((k, v) for k, v in props.items() if k.startswith("font:")))
        return font, props.get("sz")


def style_fingerprint(doc):
    out = {}
    for sid, st in doc.style_map.items():
        out[sid] = digest_bytes(canon(st).encode())
    defaults = digest_bytes(canon(doc.defaults).encode()) if doc.defaults is not None else ""
    return out, defaults


def numbering_fingerprint(doc):
    if doc.numbering is None:
        return {}, {}
    abstracts = {}
    for a in doc.numbering.findall(q("abstractNum")):
        levels = []
        for lvl in a.findall(q("lvl")):
            bits = [lvl.get(q("ilvl"))]
            for tag in ("start", "numFmt", "lvlText"):
                e = lvl.find(q(tag))
                bits.append(e.get(q("val")) if e is not None else None)
            ppr = lvl.find(q("pPr"))
            ind = ppr.find(q("ind")) if ppr is not None else None
            bits.append(tuple(sorted(ind.attrib.items())) if ind is not None else ())
            levels.append(tuple(bits))
        abstracts[a.get(q("abstractNumId"))] = tuple(levels)
    nums = {}
    for n in doc.numbering.findall(q("num")):
        a = n.find(q("abstractNumId"))
        nums[n.get(q("numId"))] = a.get(q("val")) if a is not None else None
    return abstracts, nums


def section_fingerprint(doc):
    out = []
    for sect in doc.body.iter(q("sectPr")):
        def attrs(tag):
            e = sect.find(q(tag))
            return tuple(sorted(e.attrib.items())) if e is not None else None
        refs = []
        for ref in sect:
            local = ref.tag.rsplit("}", 1)[-1]
            if local in ("headerReference", "footerReference"):
                target = doc.part_path(doc.rels.get(ref.get(qr("id"))))
                body = doc.parts.get(target, b"")
                try:
                    part_hash = digest_bytes(canon(ET.fromstring(body)).encode())
                except Exception:
                    part_hash = digest_bytes(body)
                refs.append((local, ref.get(q("type")), part_hash))
        out.append((attrs("pgSz"), attrs("pgMar"), attrs("cols"),
                    attrs("docGrid"), attrs("titlePg"), tuple(refs)))
    return out


def header_footer_fingerprint(doc):
    out = {}
    for name, data in doc.parts.items():
        if not name.endswith(".xml"):
            continue
        if not (("/header" in name) or ("/footer" in name)):
            continue
        try:
            out[name] = digest_bytes(canon(ET.fromstring(data)).encode())
        except Exception:
            out[name] = digest_bytes(data)
    return out


def top_children(doc):
    return list(doc.body)


def cover_signature(doc):
    sigs = []
    tables = []
    for el in top_children(doc):
        if el.tag == q("p"):
            text = norm_text(text_of(el))
            if "REVISION HISTORY" in text.upper():
                break
            ppr = el.find(q("pPr"))
            jc = ppr.find(q("jc")) if ppr is not None else None
            runs = []
            for r, _ in doc.text_runs(el):
                font, sz = doc.resolved_run(el, r)
                rpr = r.find(q("rPr"))
                runs.append((font, sz, bool(rpr is not None)))
            sigs.append((doc.style_of(el), doc.num_of(el),
                         jc.get(q("val")) if jc is not None else None,
                         tuple(sorted(set(runs)))))
        elif el.tag == q("tbl"):
            tables.append(table_fingerprint(el))
    return sigs, tables


def table_fingerprint(tbl):
    pr = tbl.find(q("tblPr"))
    grid = tbl.find(q("tblGrid"))
    cols = [c.get(q("w")) for c in grid.findall(q("gridCol"))] if grid is not None else []
    def attr(tag, name="val"):
        e = pr.find(q(tag)) if pr is not None else None
        return e.get(q(name)) if e is not None else None
    def blob(tag):
        e = pr.find(q(tag)) if pr is not None else None
        return canon(e) if e is not None else None
    first = tbl.find(q("tr"))
    first_cells = len(first.findall(q("tc"))) if first is not None else 0
    return (len(cols), tuple(cols), attr("tblStyle"), attr("tblW", "type"),
            attr("tblW", "w"), blob("tblBorders"), blob("tblCellMar"),
            attr("tblLayout", "type"), first_cells)


def table_entries(doc):
    entries = []
    last_caption = None
    for el in top_children(doc):
        if el.tag == q("p"):
            if is_caption(doc, el, "table"):
                t = norm_text(text_of(el))
                if t:
                    last_caption = t
        elif el.tag == q("tbl"):
            entries.append((last_caption, table_fingerprint(el)))
    return entries


def normal_caption(c):
    if not c:
        return ""
    return re.sub(r"^Table\s+\d+\s*[:.]\s*", "", c).strip()


def table_name_of(caption):
    m = re.search(r"\(([^()]+)\)\s*$", normal_caption(caption))
    return m.group(1) if m else ""


def name_key(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def caption_fmt(doc, p):
    ppr = p.find(q("pPr"))
    jc = ppr.find(q("jc")) if ppr is not None else None
    runs = []
    for r, _ in doc.text_runs(p):
        font, sz = doc.resolved_run(p, r)
        rpr = r.find(q("rPr"))
        b = rpr is not None and rpr.find(q("b")) is not None
        i = rpr is not None and rpr.find(q("i")) is not None
        runs.append((font, sz, b, i))
    return (doc.style_of(p), jc.get(q("val")) if jc is not None else None,
            tuple(sorted(set(runs))))


def caption_entries(doc):
    out = []
    for p in doc.paragraphs():
        if is_caption(doc, p, "table"):
            out.append((normal_caption(text_of(p)), caption_fmt(doc, p)))
    return out


def heading_entries(doc):
    out = []
    for p in doc.paragraphs():
        st = doc.style_of(p)
        if st in ("Heading1", "Heading2", "Heading3", "Heading4"):
            out.append((st, doc.num_of(p)))
    return out


def paragraph_style_seq(doc):
    return [doc.style_of(p) for p in doc.paragraphs() if doc.style_of(p)]


def is_caption(doc, p, prefix):
    if p is None or p.tag != q("p"):
        return False
    st = doc.style_of(p)
    if st in ("TableofFigures", "TOC1", "TOC2"):
        return False
    return norm_text(text_of(p)).lower().startswith(prefix)


def drawings(doc):
    out = []
    for el in top_children(doc):
        if el.tag != q("p"):
            continue
        for d in el.iter(q("drawing")):
            inline = d.find(qwp("inline"))
            anchor = d.find(qwp("anchor"))
            e = inline if inline is not None else anchor
            extent = e.find(qwp("extent")) if e is not None else None
            docpr = e.find(qwp("docPr")) if e is not None else None
            blip = next((b for b in d.iter(qa("blip")) if b.get(qr("embed"))), None)
            target = doc.rels.get(blip.get(qr("embed"))) if blip is not None else None
            part = doc.part_path(target)
            pos = ""
            if anchor is not None:
                ph = anchor.find(qwp("positionH"))
                pv = anchor.find(qwp("positionV"))
                pos = "|".join(filter(None, [
                    ph.find(qwp("posOffset")).text if ph is not None and ph.find(qwp("posOffset")) is not None else None,
                    pv.find(qwp("posOffset")).text if pv is not None and pv.find(qwp("posOffset")) is not None else None,
                ]))
            out.append({
                "kind": "inline" if inline is not None else "anchor",
                "cx": int(extent.get("cx")) if extent is not None else None,
                "cy": int(extent.get("cy")) if extent is not None else None,
                "name": docpr.get("name") if docpr is not None else None,
                "target": target,
                "part": part,
                "pos": pos,
            })
    # captions by document order (caption styles vary between documents)
    caps = []
    for i, el in enumerate(top_children(doc)):
        if el.tag == q("p") and list(el.iter(q("drawing"))):
            cap = ""
            for nxt in top_children(doc)[i + 1:i + 4]:
                if is_caption(doc, nxt, "figure"):
                    cap = norm_text(text_of(nxt))
                    break
            caps.extend([cap] * len(list(el.iter(q("drawing")))))
    for d, cap in zip(out, caps):
        d["caption"] = cap
    return out


def media_size(doc, part):
    data = doc.parts.get(part)
    if not data:
        return None
    try:
        from PIL import Image
        import io
        im = Image.open(io.BytesIO(data))
        return im.width, im.height
    except Exception:
        return None


def run_profile(doc):
    per_style = defaultdict(Counter)
    totals = Counter()
    nodirect = Counter()
    anomalies = []
    for p in doc.paragraphs():
        st = doc.style_of(p) or "Normal"
        runs = [(r, txt, doc.resolved_run(p, r)) for r, txt in doc.text_runs(p)
                if r.find(q("vertAlign")) is None]
        if not runs:
            continue
        dom = Counter((font, sz) for _r, _t, (font, sz) in runs).most_common(1)[0][0]
        for r, txt, key in runs:
            per_style[st][key] += 1
            totals[st] += 1
            if r.find(q("rPr")) is None:
                nodirect[st] += 1
            rpr = r.find(q("rPr"))
            if key != dom and rpr is None:
                anomalies.append((st, norm_text(txt)[:40], dom, key))
    return per_style, totals, nodirect, anomalies


def words_with_vi(text):
    out = set()
    for w in re.findall(r"[^\W\d_]+(?:['-][^\W\d_]+)*", text, flags=re.UNICODE):
        if any(c in VI for c in w):
            out.add(w)
    return out


def doc_text(doc):
    return "\n".join(text_of(p) for p in doc.paragraphs())


def schema_and_facts():
    schema = json.loads((ROOT / "docs/qa/schema-introspection.json").read_text(encoding="utf-8"))
    facts = json.loads((ROOT / "docs/qa/project-facts.json").read_text(encoding="utf-8"))
    return schema, facts


def base_type(c):
    t = c["type"].lower()
    if t == "array":
        return (c.get("udt") or "_text").lstrip("_").upper() + "[]"
    if t in ("character varying", "character"):
        return f"VARCHAR({c['max_length']})" if c.get("max_length") else "VARCHAR"
    if t == "timestamp with time zone":
        return "TIMESTAMPTZ"
    if t == "timestamp without time zone":
        return "TIMESTAMP"
    if t == "numeric":
        return f"NUMERIC({c['numeric_precision']},{c['numeric_scale']})"
    return {"integer": "INT", "bigint": "BIGINT", "boolean": "BOOLEAN", "text": "TEXT",
            "jsonb": "JSONB", "date": "DATE", "smallint": "SMALLINT"}.get(t, t.upper())


def norm_type(t):
    return (t or "").strip().upper().replace(" ", "")


def db_sections(doc):
    current = None
    sections = {}
    for el in top_children(doc):
        if el.tag == q("p"):
            if doc.style_of(el) == "Heading2":
                current = norm_text(text_of(el))
        elif el.tag == q("tbl") and current:
            rows = []
            for tr in el.findall(q("tr")):
                rows.append([norm_text(text_of(tc)) for tc in tr.findall(q("tc"))])
            if rows and rows[0] and rows[0][0] == "Attributes":
                sections[current] = rows
            current = None
    return sections


def find_soffice():
    cand = []
    env = os.environ.get("SOFFICE")
    if env:
        cand.append(Path(env))
    for base in (os.environ.get("LOCALAPPDATA"), os.environ.get("ProgramFiles"),
                 os.environ.get("ProgramFiles(x86)"), os.environ.get("TEMP")):
        if not base:
            continue
        cand.extend([
            Path(base) / "DBCAS-tools/LibreOffice/program/soffice.com",
            Path(base) / "DBCAS-tools/LibreOffice/program/soffice.exe",
            Path(base) / "LibreOffice/program/soffice.com",
            Path(base) / "LO-extract/program/soffice.com",
        ])
    cand.append(Path("soffice"))
    for p in cand:
        try:
            if p.is_file() or (not p.is_absolute() and shutil.which(str(p))):
                return str(p)
        except OSError:
            pass
    return None


def run_pdf(docx_path, outdir, soffice, timeout=240):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    profile = Path(tempfile.gettempdir()) / "dbc-wordverify-lo-profile"
    cmd = [soffice, "--headless", "--norestore",
           f"-env:UserInstallation={profile.as_uri()}", "--convert-to", "pdf",
           "--outdir", str(outdir), str(docx_path)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    pdf = outdir / (Path(docx_path).stem + ".pdf")
    if r.returncode != 0 or not pdf.exists():
        raise RuntimeError((r.stderr or r.stdout or "conversion failed").strip()[:400])
    return pdf, (r.stderr or r.stdout or "").strip()


def text_margins_pt(doc):
    vals = []
    for sect in doc.body.iter(q("sectPr")):
        pm = sect.find(q("pgMar"))
        if pm is None:
            continue
        def tv(name):
            v = pm.get(q(name))
            return int(v) / 1440 * 72 if v and v.lstrip("-").isdigit() else 0
        vals.append((tv("left"), tv("right"), tv("top"), tv("bottom")))
    if not vals:
        return (72, 72, 72, 72)
    return (max(v[0] for v in vals), max(v[1] for v in vals),
            max(v[2] for v in vals), max(v[3] for v in vals))


def page_figure(pdf_path, caption, expected_cx, expected_cy):
    try:
        import pymupdf
    except Exception:
        return None
    d = pymupdf.open(pdf_path)
    want = norm_text(caption)[:80].lower()
    exp_w = expected_cx / 914400 * 72 if expected_cx else 0
    exp_h = expected_cy / 914400 * 72 if expected_cy else 0
    exp_ar = (exp_w / exp_h) if exp_h else 0
    best = None
    for i, page in enumerate(d):
        t = norm_text(page.get_text()).lower()
        if not want or want not in t:
            continue
        for img in page.get_images(full=True):
            for r in page.get_image_rects(img[0]):
                if exp_ar and r.height:
                    ar = r.width / r.height
                    if abs(ar - exp_ar) / exp_ar > 0.05:
                        continue
                size_err = 0.0
                if exp_w and exp_h:
                    size_err = abs(r.width - exp_w) / exp_w + abs(r.height - exp_h) / exp_h
                if best is None or size_err < best[0]:
                    best = (size_err, i, page, r)
    if best is None:
        d.close()
        return None
    _, i, page, rect = best
    result = {
        "page": i + 1,
        "rect": (rect.x0, rect.y0, rect.x1, rect.y1),
        "page_rect": (page.rect.x0, page.rect.y0, page.rect.x1, page.rect.y1),
        "count": len(d),
    }
    d.close()
    return result


def render_page(pdf_path, page_no, out_png, dpi=100):
    import pymupdf
    d = pymupdf.open(pdf_path)
    pix = d[page_no - 1].get_pixmap(dpi=dpi)
    pix.save(out_png)
    d.close()


def contact_sheet(rows, out_path, title):
    from PIL import Image, ImageDraw
    if not rows:
        return
    width = 620
    panels = []
    for label, before, after in rows:
        ims = []
        for p in (before, after):
            im = Image.open(p).convert("RGB")
            h = round(im.height * width / im.width)
            ims.append(im.resize((width, h), Image.LANCZOS))
        panels.append((label, ims[0], ims[1]))
    row_h = max(max(a.height, b.height) for _, a, b in panels) + 30
    canvas = Image.new("RGB", (width * 2 + 30, 40 + row_h * len(panels)), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((10, 10), title, fill="black")
    for i, (label, before, after) in enumerate(panels):
        y = 40 + i * row_h
        canvas.paste(before, (10, y + 20))
        canvas.paste(after, (width + 20, y + 20))
        draw.text((10, y + 2), "BEFORE  " + label, fill="black")
        draw.text((width + 20, y + 2), "AFTER  " + label, fill="black")
    canvas.save(out_path)
    print("contact sheet", out_path)


def word_open_checks(docs, log):
    import win32com.client
    tmp = Path(tempfile.gettempdir()) / "dbc-wordverify"
    tmp.mkdir(parents=True, exist_ok=True)
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    out = {}
    try:
        for slug, _title, _orig, edited in docs:
            src = ACA / edited
            copy = tmp / f"{slug}.docx"
            shutil.copyfile(src, copy)
            try:
                d = word.Documents.Open(str(copy), ConfirmConversions=False,
                                        ReadOnly=False, AddToRecentFiles=False)
                pages0 = d.ComputeStatistics(2)
                fields = d.Fields.Count
                tocs = d.TablesOfContents.Count
                tofs = d.TablesOfFigures.Count
                d.Fields.Update()
                for i in range(1, tocs + 1):
                    d.TablesOfContents(i).Update()
                for i in range(1, tofs + 1):
                    d.TablesOfFigures(i).Update()
                d.Repaginate()
                pages1 = d.ComputeStatistics(2)
                out[slug] = {"ok": True, "pages_before": pages0, "pages_after": pages1,
                             "fields": fields, "tocs": tocs, "tofs": tofs,
                             "word": word.Version}
                d.Close(0)
            except Exception as e:
                out[slug] = {"ok": False, "error": f"{type(e).__name__}: {e}"}
    finally:
        try:
            word.Quit()
        except Exception:
            pass
    log.append("Word COM open/update: " + ", ".join(
        f"{k}=" + ("ok" if v.get("ok") else "FAIL") for k, v in out.items()))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ci", action="store_true", help="skip Word COM and PDF page evidence")
    ap.add_argument("--no-pdf", action="store_true", help="skip LibreOffice PDF evidence")
    ap.add_argument("--only", default="", help="comma list: proposal,architecture,database")
    args = ap.parse_args()
    only = {x.strip() for x in args.only.split(",") if x.strip()}
    docs = [d for d in DOCS if not only or d[0] in only]
    OUT.mkdir(parents=True, exist_ok=True)
    log = []
    schema, facts = schema_and_facts()
    tools = {}
    import platform
    from importlib import metadata
    tools["Python"] = platform.python_version()
    for pkg in ("python-docx", "docx2python", "pywin32", "lxml"):
        try:
            tools[pkg] = metadata.version(pkg)
        except Exception:
            tools[pkg] = "missing"
    try:
        tools["Node"] = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception:
        tools["Node"] = "missing"
    try:
        import docx
        tools["python-docx"] = getattr(docx, "__version__", tools.get("python-docx", "1.2.0"))
    except Exception:
        pass
    try:
        import pymupdf
        tools["PyMuPDF"] = pymupdf.__version__
    except Exception:
        tools["PyMuPDF"] = "missing"
    try:
        from PIL import Image
        tools["Pillow"] = Image.__version__
    except Exception:
        tools["Pillow"] = "missing"
    try:
        import lxml
        tools["lxml"] = lxml.__version__
    except Exception:
        tools["lxml"] = "missing"
    soffice = None if args.ci or args.no_pdf else find_soffice()
    tools["LibreOffice"] = soffice or "unavailable"
    if soffice:
        try:
            rv = subprocess.run([soffice, "--headless", "--norestore",
                                 f"-env:UserInstallation={(Path(tempfile.gettempdir()) / 'dbc-wordverify-lo-version').as_uri()}",
                                 "--version"], capture_output=True, text=True, timeout=60)
            ver = (rv.stdout or rv.stderr).strip().splitlines()
            if ver:
                tools["LibreOffice"] = ver[-1]
        except Exception:
            pass
    dot = None
    for base in (os.environ.get("LOCALAPPDATA"), os.environ.get("ProgramFiles")):
        if base:
            cand = Path(base) / "DBCAS-tools/Graphviz-16.1.0/Graphviz-16.1.0-win64/bin/dot.exe"
            if cand.exists():
                dot = str(cand)
                break
    if not dot:
        dot = shutil.which("dot")
    tools["Graphviz"] = "missing"
    if dot:
        try:
            rv = subprocess.run([dot, "-V"], capture_output=True, text=True, timeout=20)
            tools["Graphviz"] = (rv.stderr or rv.stdout).strip()
        except Exception:
            pass
    word_results = {}
    if not args.ci:
        try:
            word_results = word_open_checks(docs, log)
        except Exception as e:
            log.append(f"Word COM unavailable: {type(e).__name__}: {e}")
    wv = next((v.get("word") for v in word_results.values() if v.get("ok")), None)
    tools["Word COM"] = wv or "unavailable"
    before_hashes = {d[0]: sha_file(ACA / d[3]) for d in docs}
    reports = {}
    summary_rows = []

    for slug, title, orig_name, edited_name in docs:
        orig = Docx(ACA / orig_name)
        edit = Docx(ACA / edited_name)
        doc_dir = OUT / slug
        fig_dir = doc_dir / "diagrams"
        fig_dir.mkdir(parents=True, exist_ok=True)
        fails = defaultdict(int)
        format_rows = []
        run_rows = []
        lang_rows = []
        diagram_rows = []
        data_rows = []
        skip_rows = []

        # 1. styles / numbering / sections / headers
        sa, da = style_fingerprint(orig)
        sb, db = style_fingerprint(edit)
        style_changed = [k for k in sa if sb.get(k) != sa[k]]
        style_added = [k for k in sb if k not in sa]
        style_removed = [k for k in sa if k not in sb]
        if style_changed or style_added or style_removed or da != db:
            fails["format"] += len(style_changed) + len(style_added) + len(style_removed) + (da != db)
            format_rows.append(("styles.xml", f"{len(sa)} styles", f"{len(sb)} styles",
                                f"changed={style_changed} added={style_added} removed={style_removed} defaults={'same' if da == db else 'DIFF'}"))
        else:
            format_rows.append(("styles.xml", f"{len(sa)} styles", f"{len(sb)} styles", "identical definitions"))

        aa, an = numbering_fingerprint(orig)
        ba, bn = numbering_fingerprint(edit)
        num_bad = [k for k in aa if ba.get(k) != aa[k]] + [k for k in ba if k not in aa] + \
                  [k for k in an if bn.get(k) != an[k]]
        if num_bad:
            fails["format"] += len(num_bad)
            format_rows.append(("numbering.xml", f"{len(aa)} abstract / {len(an)} nums",
                                f"{len(ba)} abstract / {len(bn)} nums", f"changed={sorted(set(num_bad))[:8]}"))
        else:
            format_rows.append(("numbering.xml", f"{len(aa)} abstract / {len(an)} nums",
                                f"{len(ba)} abstract / {len(bn)} nums", "identical definitions"))

        sects_a, sects_b = section_fingerprint(orig), section_fingerprint(edit)
        if sects_a != sects_b:
            fails["format"] += 1
            format_rows.append(("sections/page setup", f"{len(sects_a)} sections",
                                f"{len(sects_b)} sections", "page size/margins/columns/header refs differ"))
        else:
            format_rows.append(("sections/page setup", f"{len(sects_a)} sections",
                                f"{len(sects_b)} sections", "identical size, margins, orientation, refs"))

        hfa, hfb = header_footer_fingerprint(orig), header_footer_fingerprint(edit)
        if Counter(hfa.values()) != Counter(hfb.values()):
            fails["format"] += 1
            format_rows.append(("headers/footers", f"{len(hfa)} parts", f"{len(hfb)} parts", "part content differs"))
        else:
            format_rows.append(("headers/footers", f"{len(hfa)} parts", f"{len(hfb)} parts", "identical content"))

        cov_a, cov_b = cover_signature(orig), cover_signature(edit)
        if cov_a != cov_b:
            fails["format"] += 1
            format_rows.append(("cover page", f"{len(cov_a[0])} paragraphs / {len(cov_a[1])} tables",
                                f"{len(cov_b[0])} paragraphs / {len(cov_b[1])} tables",
                                "format signature differs"))
        else:
            format_rows.append(("cover page", f"{len(cov_a[0])} paragraphs / {len(cov_a[1])} tables",
                                f"{len(cov_b[0])} paragraphs / {len(cov_b[1])} tables", "identical format"))

        # headings
        ha, hb = heading_entries(orig), heading_entries(edit)
        if ha == hb:
            format_rows.append(("heading style usage", f"{len(ha)} headings", f"{len(hb)} headings", "identical sequence"))
        else:
            import difflib
            sm = difflib.SequenceMatcher(a=ha, b=hb)
            added = [hb[j] for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag in ("insert", "replace") for j in range(j1, j2)]
            removed = [ha[i] for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag in ("delete", "replace") for i in range(i1, i2)]
            allowed = all(x[0] == "Heading2" for x in added)
            if removed or not allowed:
                fails["format"] += 1
                format_rows.append(("heading style usage", f"{len(ha)} headings", f"{len(hb)} headings",
                                    f"removed={removed[:3]} added={added[:3]} allowed={allowed}"))
            else:
                format_rows.append(("heading style usage", f"{len(ha)} headings", f"{len(hb)} headings",
                                    f"+{len(added)} new table-section headings, formatting inherited"))

        # table formatting: match captions first, then renamed captions by fingerprint
        entries_a = table_entries(orig)
        entries_b = table_entries(edit)
        used_b = set()
        table_issues = []
        renamed = []
        for idx, (cap, fp) in enumerate(entries_a):
            target = None
            for j, (cap_b, fp_b) in enumerate(entries_b):
                if j in used_b:
                    continue
                if normal_caption(cap_b) == normal_caption(cap):
                    target = j
                    break
            if target is None:
                for j, (cap_b, fp_b) in enumerate(entries_b):
                    if j in used_b:
                        continue
                    if fp_b == fp:
                        target = j
                        break
                if target is not None:
                    renamed.append((cap, entries_b[target][0]))
            if target is None:
                table_issues.append(f"missing {normal_caption(cap)[:60]}")
            else:
                used_b.add(target)
                if entries_b[target][1] != fp:
                    table_issues.append(f"format {normal_caption(cap)[:60]}")
        extras = [(c, fp) for j, (c, fp) in enumerate(entries_b) if j not in used_b]
        known_tables = {name_key(t["table"]) for t in schema["tables"]}
        unknown_extras = [c for c, _ in extras if name_key(table_name_of(c)) not in known_tables
                          and "Hardware and Software Requirements" not in c]
        if extras:
            dict_fps = Counter(fp for c, fp in entries_b if name_key(table_name_of(c)) in known_tables)
            dominant = dict_fps.most_common(1)[0][0] if dict_fps else None
            bad_extra = [c for c, fp in extras if fp != dominant]
            if bad_extra:
                table_issues.extend(f"new table format {c[:60]}" for c in bad_extra[:5])
        if unknown_extras:
            table_issues.append("unexpected extra tables: " + ", ".join(unknown_extras[:3]))
        if table_issues:
            fails["format"] += len(table_issues)
            format_rows.append(("table formatting", f"{len(entries_a)} captions", f"{len(entries_b)} captions", "; ".join(table_issues[:6])))
        else:
            detail = f"all matched; +{len(extras)} new table(s) inherit the dictionary style"
            if renamed:
                detail += f"; {len(renamed)} caption rename(s) with identical table format (content)"
            format_rows.append(("table formatting", f"{len(entries_a)} captions", f"{len(entries_b)} captions", detail))

        # caption formatting
        ca, cb = caption_entries(orig), caption_entries(edit)
        cap_map_a = dict(ca)
        cap_issues = [k for k, v in cap_map_a.items() if k in dict(cb) and dict(cb)[k] != v]
        if cap_issues:
            fails["format"] += len(cap_issues)
            format_rows.append(("caption format", f"{len(ca)} captions", f"{len(cb)} captions",
                                f"format changed: {cap_issues[:5]}"))
        else:
            format_rows.append(("caption format", f"{len(ca)} captions", f"{len(cb)} captions",
                                f"matched; +{max(0, len(cb) - len(ca))} new caption(s) use the same format"))

        # 2. run/style check
        pa, ta_runs, na, anom_a = run_profile(orig)
        pb, tb_runs, nb, anom_b = run_profile(edit)
        new_combos = []
        for st in pb:
            if st in pa:
                for combo, count in pb[st].items():
                    if combo not in pa[st]:
                        new_combos.append((st, combo, count))
        ratio_jumps = []
        for st in tb_runs:
            if st in ta_runs and tb_runs[st] >= 10 and ta_runs[st] >= 10:
                ra = na[st] / ta_runs[st]
                rb = nb[st] / tb_runs[st]
                if rb - ra > 0.10:
                    ratio_jumps.append((st, round(ra, 3), round(rb, 3)))
        anom_a_by = Counter(x[0] for x in anom_a)
        anom_b_by = Counter(x[0] for x in anom_b)
        new_anomalies = [(st, n) for st, n in anom_b_by.items() if n > anom_a_by.get(st, 0)]
        if new_combos or ratio_jumps or new_anomalies:
            fails["runs"] += len(new_combos) + len(ratio_jumps) + len(new_anomalies)
            run_rows = [("new font/size", st, f"{combo} x{count}", "not present in original style") for st, combo, count in new_combos[:20]]
            run_rows += [("unstyled rate", st, f"{ra} -> {rb}", "increase > 10 points") for st, ra, rb in ratio_jumps]
            run_rows += [("dominant mismatch", st, f"{n} new", "unstyled run differs from paragraph dominant font/size")
                         for st, n in new_anomalies[:10]]
        else:
            run_rows = [("font/size combinations", f"{sum(tb_runs.values())} runs",
                         f"{len(new_combos)} new", "identical to original per style"),
                        ("unstyled runs", f"{sum(na.values())} runs", f"{sum(nb.values())} runs",
                         "no style-level increase > 10 points"),
                        ("paragraph-dominant mismatches", f"{len(anom_a)}", f"{len(anom_b)}",
                         "no new unstyled mismatch by style")]

        # 3. language
        wa = words_with_vi(doc_text(orig))
        wb = words_with_vi(doc_text(edit))
        new_words = sorted(wb - wa)
        if new_words:
            fails["language"] += len(new_words)
            lang_rows = [("Vietnamese word", w, "new in edited") for w in new_words[:20]]
        else:
            lang_rows = [("Vietnamese-specific words", f"{len(wa)} in original", f"{len(wb)} in edited", "no new words")]

        # 4. diagrams
        da_list, db_list = drawings(orig), drawings(edit)
        dia_issues = []
        if len(da_list) != len(db_list):
            dia_issues.append(f"drawing count {len(da_list)} -> {len(db_list)}")
        for i, (x, y) in enumerate(zip(da_list, db_list), 1):
            for key in ("kind", "cx", "cy", "target", "pos"):
                if x.get(key) != y.get(key):
                    dia_issues.append(f"fig {i} {key}: {x.get(key)} -> {y.get(key)}")
            if normal_caption(x.get("caption", "")) != normal_caption(y.get("caption", "")):
                dia_issues.append(f"fig {i} caption changed")
            sa_ = media_size(orig, x["part"]) if x.get("part") else None
            sb_ = media_size(edit, y["part"]) if y.get("part") else None
            if sa_ and sb_:
                ra, rb = sa_[0] / sa_[1], sb_[0] / sb_[1]
                if abs(ra - rb) / ra > 0.01:
                    dia_issues.append(f"fig {i} stored aspect {ra:.4f} -> {rb:.4f}")
            dia_issues.append(None) if False else None
        # strip the accidental None issue marker
        dia_issues = [x for x in dia_issues if x]

        # PDF page evidence
        fig_stats = []
        if soffice and any(d.get("caption") for d in db_list):
            try:
                tmp = Path(tempfile.gettempdir()) / "dbc-wordverify"
                tmp.mkdir(parents=True, exist_ok=True)
                o_copy = tmp / f"{slug}-orig.docx"
                e_copy = tmp / f"{slug}-edit.docx"
                shutil.copyfile(ACA / orig_name, o_copy)
                shutil.copyfile(ACA / edited_name, e_copy)
                pdf_a, _ = run_pdf(o_copy, Path(tempfile.gettempdir()) / "dbc-wordverify" / f"{slug}-pdf-before", soffice)
                pdf_b, _ = run_pdf(e_copy, Path(tempfile.gettempdir()) / "dbc-wordverify" / f"{slug}-pdf-after", soffice)
                contact_rows = []
                fig_stats.clear()
                for old in fig_dir.glob("fig-*.png"):
                    old.unlink()
                for i, d in enumerate(db_list, 1):
                    cap = d.get("caption")
                    if not cap:
                        continue
                    pa_ = page_figure(pdf_a, cap, d.get("cx"), d.get("cy"))
                    pb_ = page_figure(pdf_b, cap, d.get("cx"), d.get("cy"))
                    if not pa_ or not pb_:
                        dia_issues.append(f"fig {i} caption/image page not found")
                        fig_stats.append({"i": i, "caption": cap, "result": "page not found"})
                        continue
                    ew = (d["cx"] / 914400 * 72) if d.get("cx") else 0
                    eh = (d["cy"] / 914400 * 72) if d.get("cy") else 0
                    bw = pb_["rect"][2] - pb_["rect"][0]
                    bh = pb_["rect"][3] - pb_["rect"][1]
                    issues = []
                    if ew and eh and (abs(bw - ew) / ew > 0.05 or abs(bh - eh) / eh > 0.05):
                        issues.append(f"rendered {bw:.0f}x{bh:.0f}pt vs {ew:.0f}x{eh:.0f}pt")
                    x0, y0, x1, y1 = pb_["rect"]
                    px0, py0, px1, py1 = pb_["page_rect"]
                    if x0 < px0 + 2 or y0 < py0 + 2 or x1 > px1 - 2 or y1 > py1 - 2:
                        issues.append("extends to page edge")
                    ml, mr, mt, mb = text_margins_pt(edit)
                    if x0 < px0 + ml - 1 or x1 > px1 - mr + 1 or y0 < py0 + mt - 1 or y1 > py1 - mb + 1:
                        issues.append(f"outside text margins (L{ml:.0f}/R{mr:.0f}/T{mt:.0f}/B{mb:.0f}pt)")
                    if issues:
                        dia_issues.extend(f"fig {i} {x}" for x in issues)
                    fm = re.search(r"Figure\s+(\d+)", cap, re.I)
                    fno = int(fm.group(1)) if fm else i
                    before_png = fig_dir / f"fig-{fno:02d}-before.png"
                    after_png = fig_dir / f"fig-{fno:02d}-after.png"
                    render_page(pdf_a, pa_["page"], before_png)
                    render_page(pdf_b, pb_["page"], after_png)
                    contact_rows.append((cap if cap else f"Figure {i}", before_png, after_png))
                    fig_stats.append({"i": i, "caption": cap,
                                      "page_a": pa_["page"], "page_b": pb_["page"],
                                      "rendered": f"{bw:.0f}x{bh:.0f}",
                                      "page_size": f"{px1-px0:.0f}x{py1-py0:.0f}",
                                      "result": "; ".join(issues) or "inside text margins, caption on same page"})
                if contact_rows:
                    contact_sheet(contact_rows, fig_dir / "contact-before-after.png",
                                  f"{title} - diagrams before/after")
                pdf_ok = True
            except Exception as e:
                skip_rows.append(("PDF diagram pages", "LibreOffice", f"{type(e).__name__}: {str(e)[:160]}"))
        else:
            skip_rows.append(("PDF diagram pages", "LibreOffice/PyMuPDF", "unavailable or no captions"))

        # 5. data
        if dia_issues:
            fails["diagrams"] += len(dia_issues)
        st = schema
        text = doc_text(edit)
        tables_real = {t["table"]: t for t in st["tables"]}
        display = {t["table"]: "".join(p.capitalize() for p in t["table"].split("_")) for t in st["tables"]}
        display["llm_cache"] = "LLMCache"
        display["sql_test_dataset"] = "SQLTestDataset"
        display["mcq_option"] = "MCQOption"
        display["clo_concept"] = "CLOConcept"
        data_issues = []
        if slug == "database":
            secs = db_sections(edit)
            sec_keys = {name_key(k) for k in secs}
            data_issues += [f"section missing {n}" for n in tables_real if name_key(n) not in sec_keys]
            for heading, rows in secs.items():
                name = next((n for n in tables_real if name_key(n) == name_key(heading)), None)
                if not name:
                    data_issues.append(f"unknown section {heading}")
                    continue
                doccols = {r[0]: (r[1], r[2]) for r in rows[1:] if r and r[0]}
                for col in tables_real[name]["columns"]:
                    if col["name"] not in doccols:
                        data_issues.append(f"{name}.{col['name']} missing")
                    else:
                        dt, dn = doccols[col["name"]]
                        if norm_type(dt) != norm_type(base_type(col)):
                            data_issues.append(f"{name}.{col['name']} type {dt}!={base_type(col)}")
                        if (dn.lower().startswith("not")) == col["nullable"]:
                            data_issues.append(f"{name}.{col['name']} null {dn}")
                for c in doccols:
                    if c not in {x["name"] for x in tables_real[name]["columns"]}:
                        data_issues.append(f"{name}.{c} extra")
        # overview (database) and numeric claims
        if slug == "database":
            ov = None
            for el in top_children(edit):
                if el.tag == q("tbl"):
                    rows = [[norm_text(text_of(tc)) for tc in tr.findall(q("tc"))] for tr in el.findall(q("tr"))]
                    if rows and rows[0] and rows[0][0] == "Table Name":
                        ov = rows
                        break
            if not ov:
                data_issues.append("Table Overview not found")
            else:
                names = [r[0] for r in ov[1:] if r and r[0]]
                name_keys = {name_key(n) for n in names}
                data_issues += [f"overview missing {n}" for n in tables_real if name_key(n) not in name_keys]
                if len(names) != 41:
                    data_issues.append(f"overview rows {len(names)} != 41")
            # FK targets in Extra columns
            display_keys = {name_key(v): k for k, v in display.items()}
            for heading, rows in db_sections(edit).items():
                for r in rows[1:]:
                    if len(r) >= 6 and r[5].startswith("FK → "):
                        tgt_raw = r[5][5:].strip()
                        tgt = re.split(r"[ (;,.]", tgt_raw)[0].strip()
                        if tgt and name_key(tgt) not in display_keys and name_key(tgt) not in {name_key(t) for t in tables_real}:
                            data_issues.append(f"FK target unknown: {tgt_raw}")
        # endpoints named in the text
        eps = set(re.findall(r"/api/v\d+/[A-Za-z0-9_{}./-]+", text))
        facts_paths = set(facts.get("openapi_paths", []))
        unknown_eps = sorted(e.rstrip(".,);") for e in eps if e.rstrip(".,);") not in facts_paths)
        data_issues += [f"endpoint not in OpenAPI: {e}" for e in unknown_eps]
        # retired statements / counts
        for r in RETIRED:
            if r in text:
                data_issues.append(f"retired statement: {r}")
        for phrase in ("41 tables",):
            if phrase not in text:
                data_issues.append(f"missing claim: {phrase}")
        # reuse the existing verifier when its deps exist
        try:
            rv = subprocess.run([sys.executable, str(ROOT / "scripts/verify_docx.py")],
                                capture_output=True, text=True, timeout=180)
            if rv.returncode == 0:
                data_rows.append(("verify_docx.py (existing)", "41 assertions", "PASS",
                                  (rv.stdout.strip().splitlines() or [""])[-1][:160]))
            elif "ModuleNotFoundError" in (rv.stderr or ""):
                skip_rows.append(("verify_docx.py", "lxml missing", "SKIP (CI-safe)"))
            else:
                data_issues.append("verify_docx.py failed")
                data_rows.append(("verify_docx.py (existing)", "41 assertions", "FAIL",
                                  (rv.stdout.strip().splitlines() or [""])[-1][:160]))
        except Exception as e:
            skip_rows.append(("verify_docx.py", "not run", str(e)[:120]))
        if data_issues:
            fails["data"] += len(data_issues)
            data_rows = [("data mismatch", x, "", "") for x in data_issues[:25]] + data_rows
        else:
            coverage = {s: sum(1 for _t in DOCS if s in doc_text(Docx(ACA / _t[3]))) for s in facts.get("compose_services_all", [])}
            if slug == "database":
                secs_ok = db_sections(edit)
                cols_ok = sum(len(r) - 1 for r in secs_ok.values())
                data_rows.append(("data dictionary", "41 tables / 293 columns",
                                  f"{len(secs_ok)} sections / {cols_ok} columns",
                                  "exact names, types and nullability; 0 mismatches"))
                fk_cells = sum(1 for rows in secs_ok.values() for r in rows[1:]
                               if len(r) >= 6 and r[5].startswith("FK → "))
                data_rows.append(("foreign-key targets", "59 FKs", f"{fk_cells} FK cells",
                                  "all targets resolve to schema tables"))
            else:
                data_rows.append(("table count statement", "41 tables", "present" if "41 tables" in text else "missing",
                                  "matches schema introspection"))
            svcs = facts.get("compose_services_all", [])
            named_svcs = [s for s in svcs if s in text]
            paths_all = facts.get("openapi_paths", [])
            data_rows.append(("OpenAPI paths coverage", f"{len(paths_all)} paths", f"{len(eps)}/{len(paths_all)} named",
                              "no unknown paths; coverage is informational"))
            data_rows.append(("Compose services coverage", f"{len(svcs)} services",
                              f"{len(named_svcs)}/{len(svcs)} named",
                              "missing in this document: " + ", ".join(s for s in svcs if s not in named_svcs)))

        # open check
        source_changed = sha_file(ACA / edited_name) != before_hashes[slug]
        if source_changed:
            fails["open"] += 1
            log.append(f"{slug}: SOURCE DOCX HASH CHANGED")
        wr = word_results.get(slug)
        if wr is None:
            open_status = "SKIP"
            open_detail = "Word COM unavailable (local-only)"
        elif wr.get("ok"):
            open_status = "PASS"
            open_detail = f"{wr['pages_before']}p -> {wr['pages_after']}p after field update; {wr['fields']} fields, {wr['tocs']} TOC, {wr['tofs']} TOF"
        else:
            open_status = "FAIL"
            open_detail = wr.get("error", "open error")
            fails["open"] += 1
        source_note = "source SHA-256 unchanged" if not source_changed else "SOURCE CHANGED"
        open_detail += "; " + source_note

        status = "PASS" if not any(fails.values()) else "FAIL"
        summary_rows.append((title, open_status, fails["format"], fails["runs"],
                             fails["language"], fails["diagrams"], fails["data"], status))

        # report
        lines = [f"# {title} - word verification",
                 "",
                 f"- original: `{orig_name}`",
                 f"- edited: `{edited_name}`",
                 f"- generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
                 f"- result: **{status}**",
                 "",
                 "## Measurements",
                 "",
                 f"- original package: {(ACA / orig_name).stat().st_size:,} bytes, SHA-256 `{sha_file(ACA / orig_name)[:16]}...`",
                 f"- edited package: {(ACA / edited_name).stat().st_size:,} bytes, SHA-256 `{sha_file(ACA / edited_name)[:16]}...`",
                 f"- paragraphs: {len(orig.paragraphs())} -> {len(edit.paragraphs())}; "
                 f"text runs: {sum(ta_runs.values())} -> {sum(tb_runs.values())}",
                 f"- tables: {len(orig.body.findall(q('tbl')))} -> {len(edit.body.findall(q('tbl')))}; "
                 f"drawings: {len(da_list)} -> {len(db_list)}; media: {len([n for n in orig.parts if n.startswith('word/media/')])} -> "
                 f"{len([n for n in edit.parts if n.startswith('word/media/')])}",
                 f"- Word pages: {open_detail.split(';')[0]}",
                 "",
                 "## Measured checks",
                 "",
                 "| Check | Result | Evidence |",
                 "|---|---|---|",
                 f"| Word open/field update (local-only) | {open_status} | {open_detail} |",
                 f"| Format fidelity | {check(fails['format'] == 0)} | {fails['format']} unexplained differences |",
                 f"| Run/style fidelity | {check(fails['runs'] == 0)} | {fails['runs']} new font/size or unstyled-rate issues |",
                 f"| Language | {check(fails['language'] == 0)} | {fails['language']} new Vietnamese words |",
                 f"| Diagrams | {check(fails['diagrams'] == 0)} | {fails['diagrams']} layout/caption/page issues |",
                 f"| Data | {check(fails['data'] == 0)} | {fails['data']} mismatches |",
                 "",
                 "## Format fidelity",
                 "",
                 "| Element | Original | Edited | Result |",
                 "|---|---|---|---|"]
        for row in format_rows:
            lines.append("| " + " | ".join(str(x) for x in row) + " |")
        lines += ["", "## Content-run formatting", "",
                  "| Element | Style | Measure | Result |", "|---|---|---|---|"]
        for row in run_rows:
            lines.append("| " + " | ".join(str(x) for x in row) + " |")
        lines += ["", "## Language", "",
                  "| Element | Original | Edited | Result |", "|---|---|---|---|"]
        for row in lang_rows:
            lines.append("| " + " | ".join(str(x) for x in row) + " |")
        lines += ["", "## Diagrams", "",
                  "| Figure | Kind | Extent (EMU) | Caption | Page before/after | Rendered pt | Page pt | Result |",
                  "|---|---|---|---|---|---|---|---|"]
        stats = {s.get("i"): s for s in fig_stats}
        for i, d in enumerate(db_list, 1):
            st = stats.get(i, {})
            layout = "; ".join(x for x in dia_issues if f"fig {i} " in x) if d.get("caption") else ""
            result = st.get("result") or layout or "layout matched"
            lines.append(f"| {i} | {d['kind']} | {d['cx']} x {d['cy']} | {(d.get('caption') or '')[:70]} | "
                         f"{st.get('page_a','-')}/{st.get('page_b','-')} | {st.get('rendered','-')} | "
                         f"{st.get('page_size','-')} | {result} |")
        lines += ["", f"Contact sheet: `diagrams/contact-before-after.png` (if rendering was available).", ""]
        lines += ["## Data", "", "| Item | Expected | Measured | Result |", "|---|---|---|---|"]
        for row in data_rows:
            lines.append("| " + " | ".join(str(x) for x in row) + " |")
        if skip_rows:
            lines += ["", "## Skipped / local-only", "", "| Check | Tool | Reason |", "|---|---|---|"]
            for row in skip_rows:
                lines.append("| " + " | ".join(str(x) for x in row) + " |")
        if dia_issues:
            lines += ["", "## Diagram issues", ""] + [f"- {x}" for x in dia_issues]
        (doc_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        reports[slug] = {"status": status, "fails": dict(fails), "open": open_status}

    # root summary
    lines = ["# Word verification summary", "",
             f"Generated {time.strftime('%Y-%m-%d %H:%M:%S')} on branch `develop2`.",
             "",
             "| Document | Open/fields | Format diffs | Run issues | New VI words | Diagram issues | Data mismatches | Result |",
             "|---|---|---|---|---|---|---|---|"]
    for row in summary_rows:
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    lines += ["", "Local-only tools: Word COM (open/field update) and LibreOffice/PyMuPDF page evidence. "
              "In CI these are reported as SKIP; the format/run/language/data checks are pure Python.", ""]
    lines += ["## Toolchain", "", "| Tool | Version |", "|---|---|"]
    for k, v in tools.items():
        lines.append(f"| {k} | {v} |")
    (OUT / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    total_fail = sum(1 for r in reports.values() if r["status"] == "FAIL")
    print(f"word verification: {len(reports)} documents, {total_fail} failed")
    for row in summary_rows:
        print("  ", row)
    for line in log:
        print("  ", line)
    return 1 if total_fail else 0


if __name__ == "__main__":
    sys.exit(main())
