# -*- coding: utf-8 -*-
"""Build a .docx from a structured block model, reusing a template's styles.

The template supplies word/styles.xml, numbering.xml, theme, headers/footers,
settings and fontTable so the generated document keeps the official structure,
heading styles, numbering, captions and page furniture. Only word/document.xml,
the image relationships, media and docProps are rebuilt.

Block model (list of dicts):
  {"type": "title"|"subtitle"|"heading"|"para"|"bullet"|"caption"|"pagebreak"|
            "toc"|"toc_figures"|"toc_tables"|"table"|"image",
   ...}
"""
from __future__ import annotations
import hashlib
import html
import json
import shutil
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC = "http://schemas.openxmlformats.org/drawingml/2006/picture"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
PR = "http://schemas.openxmlformats.org/package/2006/relationships"
CP = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC = "http://purl.org/dc/elements/1.1/"
DCTERMS = "http://purl.org/dc/terms/"
EP = "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
EMU_PER_INCH = 914400


def esc(s):
    return html.escape(str(s), quote=True)


def runs(text, bold=False, size=None, color=None):
    rpr = ""
    if bold or size or color:
        rpr = "<w:rPr>" + ("<w:b/>" if bold else "") + \
              (f'<w:sz w:val="{size}"/>' if size else "") + \
              (f'<w:color w:val="{color}"/>' if color else "") + "</w:rPr>"
    parts = str(text).split("\n")
    out = []
    for i, p in enumerate(parts):
        if i:
            out.append("<w:r><w:br/></w:r>")
        out.append(f"<w:r>{rpr}<w:t xml:space=\"preserve\">{esc(p)}</w:t></w:r>")
    return "".join(out)


def p(text, style=None, bold=False, size=None, align=None, spacing=None, keep=False):
    ppr = ""
    if style:
        ppr += f'<w:pStyle w:val="{style}"/>'
    if align:
        ppr += f'<w:jc w:val="{align}"/>'
    if spacing:
        ppr += f'<w:spacing w:before="{spacing}" w:after="{spacing}"/>'
    if keep:
        ppr += "<w:keepNext/>"
    ppr = f"<w:pPr>{ppr}</w:pPr>" if ppr else ""
    return f"<w:p>{ppr}{runs(text, bold=bold, size=size)}</w:p>"


def field(instr):
    return (f'<w:p><w:r><w:fldChar w:fldCharType="begin"/></w:r>'
            f'<w:r><w:instrText xml:space="preserve">{esc(instr)}</w:instrText></w:r>'
            f'<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
            f'<w:r><w:t>[Cập nhật trường này trong Word: F9]</w:t></w:r>'
            f'<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>')


def table(rows, widths=None, header=True):
    ncol = max(len(r) for r in rows)
    widths = widths or [int(9360 / ncol)] * ncol
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    out = ['<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/>'
           '<w:tblW w:w="9360" w:type="dxa"/>'
           '<w:tblBorders>'
           + "".join(f'<w:{s} w:val="single" w:sz="4" w:color="7F8C8D"/>'
                     for s in ("top", "left", "bottom", "right", "insideH", "insideV"))
           + '</w:tblBorders></w:tblPr>'
           f'<w:tblGrid>{grid}</w:tblGrid>']
    for ri, row in enumerate(rows):
        cells = []
        for ci in range(ncol):
            val = row[ci] if ci < len(row) else ""
            shade = '<w:shd w:val="clear" w:fill="DCEAF7"/>' if (header and ri == 0) else ""
            cells.append(
                f'<w:tc><w:tcPr><w:tcW w:w="{widths[ci]}" w:type="dxa"/>{shade}</w:tcPr>'
                + p(val, bold=(header and ri == 0), size="17") + '</w:tc>')
        out.append("<w:tr>" + "".join(cells) + "</w:tr>")
    out.append("</w:tbl>")
    return "".join(out)


def image(rel_id, width_in, height_in, name, description):
    cx, cy = int(width_in * EMU_PER_INCH), int(height_in * EMU_PER_INCH)
    return (
        '<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:drawing>'
        f'<wp:inline distT="0" distB="0" distL="0" distR="0">'
        f'<wp:extent cx="{cx}" cy="{cy}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>'
        f'<wp:docPr id="{rel_id}" name="{esc(name)}" descr="{esc(description)}"/>'
        '<wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
        '<a:graphic><a:graphicData uri="' + PIC + '">'
        '<pic:pic><pic:nvPicPr><pic:cNvPr id="0" name="' + esc(name) + '"/>'
        '<pic:cNvPicPr/></pic:nvPicPr>'
        f'<pic:blipFill><a:blip r:embed="rId{rel_id}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="' + str(cx) + '" cy="' + str(cy) + '"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
        '</a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>')


class Builder:
    def __init__(self, template: Path, out: Path):
        self.template, self.out = template, out
        self.parts = {}
        with zipfile.ZipFile(template) as z:
            for n in z.namelist():
                self.parts[n] = z.read(n)
        self.images = []   # (rel_id, path, bytes)
        self.rels = []
        self.body = []
        self.next_id = 100

    def add_image(self, path: Path, width_in, height_in, name, description):
        rid = self.next_id
        self.next_id += 1
        self.images.append((rid, "image%d.png" % rid, Path(path).read_bytes()))
        self.rels.append((rid, "media/image%d.png" % rid))
        return image(rid, width_in, height_in, name, description)

    def render_block(self, b):
        t = b["type"]
        if t == "title":
            return p(b["text"], style="Title", align="center", spacing="120")
        if t == "subtitle":
            return p(b["text"], style="Subtitle", align="center", spacing="80")
        if t == "heading":
            lvl = b.get("level", 1)
            return p(b["text"], style=f"Heading{lvl}", keep=True)
        if t == "para":
            return p(b["text"], style=b.get("style"), bold=b.get("bold", False),
                     align=b.get("align"), spacing=b.get("spacing"))
        if t == "bullet":
            return p("•  " + b["text"], style="ListParagraph")
        if t == "caption":
            return p(b["text"], style="Caption", align="center", keep=b.get("keep", False))
        if t == "pagebreak":
            return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'
        if t == "toc":
            return field(r'TOC \o "1-3" \h \z \u')
        if t == "toc_figures":
            return field(r'TOC \h \z \c "Hình"')
        if t == "toc_tables":
            return field(r'TOC \h \z \c "Bảng"')
        if t == "table":
            return table(b["rows"], b.get("widths"), b.get("header", True))
        if t == "image":
            return self.add_image(Path(b["path"]), b["width"], b["height"],
                                  b.get("name", "figure"), b.get("description", ""))
        raise ValueError("unknown block type " + t)

    def build(self, blocks, core):
        for b in blocks:
            self.body.append(self.render_block(b))
        # Reuse the template's sectPr verbatim (page size, margins, header/
        # footer references and column settings) so page furniture is preserved.
        import re
        raw_old = self.parts.get("word/document.xml", b"").decode("utf-8")
        m = re.search(r"<w:sectPr\b.*?</w:sectPr>", raw_old, re.S)
        sect = m.group(0) if m else (
            '<w:sectPr><w:pgSz w:w="11907" w:h="16839"/>'
            '<w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134" '
            'w:header="720" w:footer="720" w:gutter="0"/></w:sectPr>')
        doc = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:document xmlns:w="{W}" xmlns:r="{R}" xmlns:wp="{WP}" '
            f'xmlns:a="{A}" xmlns:pic="{PIC}"><w:body>'
            + "".join(self.body) + sect + '</w:body></w:document>')
        self.parts["word/document.xml"] = doc.encode("utf-8")
        # relationships: keep non-image relationships from the template, add ours
        old = self.parts.get("word/_rels/document.xml.rels", b"").decode("utf-8")
        keep = [m for m in __import__("re").findall(r'<Relationship\b[^>]*/>', old)
                if "image" not in m and 'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"' not in m]
        # drop old image rels and any dangling hyperlink targets are harmless
        extra = "".join(f'<Relationship Id="rId{rid}" Type="{R}/image" Target="{tgt}"/>'
                        for rid, tgt in self.rels)
        self.parts["word/_rels/document.xml.rels"] = (
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<Relationships xmlns="{PR}">' + "".join(keep) + extra + '</Relationships>').encode("utf-8")
        # Drop template media so only the regenerated figures are embedded.
        for n in [n for n in self.parts if n.startswith("word/media/")]:
            del self.parts[n]
        for rid, name, data in self.images:
            self.parts["word/media/" + name] = data
        # content types: ensure png default (templates already embed PNGs)
        ct = self.parts["[Content_Types].xml"].decode("utf-8")
        if 'Extension="png"' not in ct:
            ct = ct.replace("</Types>", '<Default Extension="png" ContentType="image/png"/></Types>')
            self.parts["[Content_Types].xml"] = ct.encode("utf-8")
        # core properties
        cxml = self.parts.get("docProps/core.xml", b"").decode("utf-8")
        def set_tag(xml, tag, val, ns):
            import re
            pattern = rf"<{ns}:{tag}[^>]*>.*?</{ns}:{tag}>"
            new = f"<{ns}:{tag}>{esc(val)}</{ns}:{tag}>"
            if re.search(pattern, xml):
                return re.sub(pattern, new, xml, count=1)
            return xml.replace(f"</cp:coreProperties>", new + "</cp:coreProperties>")
        # simpler: rebuild a minimal core.xml
        core_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<cp:coreProperties xmlns:cp="{CP}" xmlns:dc="{DC}" '
            f'xmlns:dcterms="{DCTERMS}" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            f'<dc:title>{esc(core["title"])}</dc:title>'
            f'<dc:creator>{esc(core.get("creator", "DBCAS team"))}</dc:creator>'
            f'<cp:lastModifiedBy>{esc(core.get("creator", "DBCAS team"))}</cp:lastModifiedBy>'
            f'<cp:revision>{esc(core.get("revision", "3"))}</cp:revision>'
            f'<dcterms:created xsi:type="dcterms:W3CDTF">{esc(core["created"])}</dcterms:created>'
            f'<dcterms:modified xsi:type="dcterms:W3CDTF">{esc(core["modified"])}</dcterms:modified>'
            '</cp:coreProperties>')
        self.parts["docProps/core.xml"] = core_xml.encode("utf-8")
        # app.xml: leave template values but fix Pages if possible (Word recalcs)
        self.out.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(self.out, "w", zipfile.ZIP_DEFLATED) as z:
            for n, data in self.parts.items():
                z.writestr(n, data)
        return self.out
