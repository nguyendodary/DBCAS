# -*- coding: utf-8 -*-
"""Shared FITAI-derived Word layout for the C1SE.70 DBCAS submission files.

The measured reference values and the resulting DBCAS interpretation are
recorded in docs/agent/freeze-logs/doc-style-spec.md.  Only python-docx and
lxml are used; nothing here touches the application, its validators or the
database.

Mandatory layout:
  * A4, left margin 3.5 cm, top/bottom/right 2 cm
  * body text 13 pt Times New Roman, line spacing 1.5
  * tables 11 pt, code 9 pt, captions 10 pt, header/footer 9 pt (documented
    exceptions, see doc-style-spec.md)
  * FITAI palette: accent #4472C4, dark #201F35, text2 #44546A, table header
    #D9D9D9, rules #BFBFBF, hyperlink #0563C1
"""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "submission" / "final" / "assets"
LOGO = ASSETS / "logo.png"

# --- measured FITAI palette -------------------------------------------------
ACCENT = "4472C4"
DARK = "201F35"
TEXT2 = "44546A"
RULE = "BFBFBF"
TABLE_HEAD = "D9D9D9"
TABLE_ALT = "F3F3F3"
LINK = "0563C1"
BLACK = "000000"

FONT_BODY = "Times New Roman"
FONT_CODE = "Consolas"
BODY_PT = 13
TABLE_PT = 11
CODE_PT = 9
CAPTION_PT = 9
META_PT = 9

PAGE_W, PAGE_H = Cm(21.0), Cm(29.7)
M_LEFT, M_RIGHT = Cm(3.5), Cm(2.0)
M_TOP, M_BOTTOM = Cm(2.0), Cm(2.0)
TEXT_W_CM = 21.0 - 3.5 - 2.0  # 15.5 cm usable width

GROUP = "C1SE.70"
PROJECT = "DBCAS"
PROJECT_TITLE = ("DBCAS – AI-Assisted Database Competency Assessment "
                 "and Skill Gap Analysis")
VERSION = "1.3"
VERSION_TAG = "ver1.3"
DATE_SLASH = "25/11/2026"
DATE_LONG = "November 25th, 2026"
AUTHOR = "Do, Nguyen Quoc"
INSTITUTION = "International School, Duy Tan University"
MENTOR = "MSc Viet, Huynh Duc"
START_DATE = "14/09/2026"
END_DATE = "26/12/2026"

TEAM = [
    ("Thu, Nguyen Ngoc Anh", "29209245799", "01258319907anhthu@gmail.com",
     "Project Manager, Scrum Master, Frontend Developer"),
    ("Nguyen, Nguyen Nhat", "26211227029", "nhnguyen240602@gmail.com",
     "Backend Developer, QA Tester"),
    ("Truong, Nguyen Quang", "29212730635", "quangtruongtt8@gmail.com",
     "Database Developer"),
    ("Do, Nguyen Quoc", "29211156881", "nguyenquocdodary@gmail.com",
     "Backend Developer"),
    ("Han, Nguyen Ngoc", "29204423268", "Hannguyenngoc0506@gmail.com",
     "Frontend Developer, QA Tester"),
]

REVISIONS = [
    ("1.0", "18/09/2026", "Initial release", "C1SE.70 Team"),
    ("1.1", "30/10/2026", "Update", "C1SE.70 Team"),
    ("1.2", "08/11/2026", "Correct project facts and diagrams", "C1SE.70 Team"),
    ("1.3", DATE_SLASH,
     "Align to the measured FITAI layout and re-verify every measured figure",
     AUTHOR),
]


# --- low level helpers ------------------------------------------------------
def _rgb(hex_value: str) -> RGBColor:
    return RGBColor.from_string(hex_value)


def set_run_font(run, *, name=FONT_BODY, size=BODY_PT, color=BLACK,
                 bold=None, italic=None):
    run.font.name = name
    if size is not None:
        run.font.size = Pt(size)
    if color is not None:
        run.font.color.rgb = _rgb(color)
    if bold is not None:
        run.font.bold = bold
    if italic is not None:
        run.font.italic = italic
    rpr = run._element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.insert(0, fonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        fonts.set(qn(attr), name)


def style_font(style, *, name=FONT_BODY, size=BODY_PT, color=BLACK, bold=None,
               italic=None):
    style.font.name = name
    style.font.size = Pt(size)
    style.font.color.rgb = _rgb(color)
    if bold is not None:
        style.font.bold = bold
    if italic is not None:
        style.font.italic = italic
    rpr = style.element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.insert(0, fonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        fonts.set(qn(attr), name)


def add_field(paragraph, instruction: str, placeholder: str = "1",
              *, size=META_PT, color=TEXT2, bold=False):
    run = paragraph.add_run()
    set_run_font(run, size=size, color=color, bold=bold)
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = f" {instruction} "
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = placeholder
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(begin)
    run._r.append(instr)
    run._r.append(separate)
    run._r.append(text)
    run._r.append(end)


def add_toc(paragraph, levels="1-2"):
    add_field(paragraph, f'TOC \\o "{levels}" \\h \\z \\u',
              "Right-click and choose Update Field to build the table of contents.",
              size=BODY_PT, color=BLACK)


def _borders(element, edges=("top", "left", "bottom", "right"), *,
             color=RULE, size="4", space="0", val="single"):
    borders = OxmlElement("w:tcBorders" if element.tag.endswith("tcPr") else "w:pBdr")
    for edge in edges:
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), val)
        el.set(qn("w:sz"), size)
        el.set(qn("w:space"), space)
        el.set(qn("w:color"), color)
        borders.append(el)
    element.append(borders)


def paragraph_bottom_rule(paragraph, *, color=RULE, size="6"):
    ppr = paragraph._p.get_or_add_pPr()
    _borders(ppr, ("bottom",), color=color, size=size, space="2")


def shade(cell, hex_color: str):
    tcpr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcpr.append(shd)


def cell_margins(table, top=60, bottom=60, left=90, right=90):
    tblpr = table._tbl.tblPr
    mar = OxmlElement("w:tblCellMar")
    for edge, value in (("top", top), ("left", left), ("bottom", bottom),
                        ("right", right)):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:w"), str(value))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tblpr.append(mar)


def fixed_layout(table, width_cm=TEXT_W_CM):
    tblpr = table._tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblpr.append(layout)
    tblw = tblpr.find(qn("w:tblW"))
    if tblw is None:
        tblw = OxmlElement("w:tblW")
        tblpr.append(tblw)
    tblw.set(qn("w:w"), str(int(width_cm / 2.54 * 1440)))
    tblw.set(qn("w:type"), "dxa")


def normalise_cells(table):
    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                if paragraph.alignment in (None, WD_ALIGN_PARAGRAPH.JUSTIFY):
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT


def table_borders(table, *, color=RULE, size="4"):
    tblpr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), size)
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        borders.append(el)
    tblpr.append(borders)


def repeat_header(row):
    trpr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    trpr.append(el)


def no_split(row):
    trpr = row._tr.get_or_add_trPr()
    trpr.append(OxmlElement("w:cantSplit"))


def keep_next(paragraph):
    paragraph.paragraph_format.keep_with_next = True


def page_borders(section):
    sectpr = section._sectPr
    existing = sectpr.find(qn("w:pgBorders"))
    if existing is not None:
        sectpr.remove(existing)
    borders = OxmlElement("w:pgBorders")
    borders.set(qn("w:offsetFrom"), "page")
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "12")
        el.set(qn("w:space"), "24")
        el.set(qn("w:color"), BLACK)
        borders.append(el)
    sectpr.insert_element_before(
        borders, "w:lnNumType", "w:pgNumType", "w:cols", "w:formProt",
        "w:vAlign", "w:noEndnote", "w:titlePg", "w:textDirection",
        "w:bidi", "w:rtlGutter", "w:docGrid", "w:printerSettings",
        "w:sectPrChange")


def configure_page(section):
    section.page_width = PAGE_W
    section.page_height = PAGE_H
    section.left_margin = M_LEFT
    section.right_margin = M_RIGHT
    section.top_margin = M_TOP
    section.bottom_margin = M_BOTTOM
    section.header_distance = Cm(1.0)
    section.footer_distance = Cm(1.0)
    section.gutter = Cm(0)


# --- document setup ---------------------------------------------------------
def new_document(spec) -> Document:
    doc = Document()
    configure_page(doc.sections[0])

    styles = doc.styles
    normal = styles["Normal"]
    style_font(normal, size=BODY_PT)
    pf = normal.paragraph_format
    pf.line_spacing = 1.5
    pf.space_before = Pt(0)
    pf.space_after = Pt(6)
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    heading_specs = {
        "Heading 1": (18, "1F3863", 18, 8),
        "Heading 2": (14, TEXT2, 14, 6),
        "Heading 3": (13, BLACK, 10, 4),
        "Heading 4": (13, BLACK, 8, 4),
    }
    for name, (size, color, before, after) in heading_specs.items():
        style = styles[name]
        style_font(style, size=size, color=color, bold=True)
        pf = style.paragraph_format
        pf.space_before = Pt(before)
        pf.space_after = Pt(after)
        pf.line_spacing = 1.5
        pf.keep_with_next = True
        pf.alignment = WD_ALIGN_PARAGRAPH.LEFT

    for name in ("Caption", "Quote", "Intense Quote"):
        try:
            style = styles[name]
        except KeyError:
            continue
        style_font(style, size=CAPTION_PT, color=TEXT2, italic=True)
        style.paragraph_format.line_spacing = 1.0
        style.paragraph_format.space_after = Pt(8)

    # TOC entry styles: Word reuses existing styles when it builds the field.
    from docx.enum.style import WD_STYLE_TYPE
    for name, size, indent in (("TOC 1", 11, 0.0), ("TOC 2", 11, 0.6),
                               ("TOC 3", 11, 1.2)):
        try:
            style = styles[name]
        except KeyError:
            style = styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        style.base_style = styles["Normal"]
        style_font(style, size=size, color=BLACK)
        pf = style.paragraph_format
        pf.line_spacing = 1.0
        pf.space_after = Pt(2)
        pf.left_indent = Cm(indent)
        pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for name, size, color, italic, bold in (
            ("DBCAS Table", TABLE_PT, BLACK, False, False),
            ("DBCAS Code", CODE_PT, BLACK, False, False),
            ("DBCAS Caption", CAPTION_PT, TEXT2, True, False),
            ("DBCAS Cover Title", 26, BLACK, False, True),
            ("DBCAS Cover Label", 13, BLACK, False, False),
            ("DBCAS Cover Team", 11, BLACK, False, False),
            ("DBCAS Cover Signature", 11, BLACK, False, False),
            ("DBCAS Meta", 12, BLACK, False, True),
            ("DBCAS Note", 13, TEXT2, True, False)):
        style = styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        style.base_style = styles["Normal"]
        style_font(style, size=size, color=color, italic=italic, bold=bold)
        pf = style.paragraph_format
        pf.line_spacing = 1.5 if name not in ("DBCAS Table", "DBCAS Code") else 1.0
        pf.space_after = Pt(4 if name != "DBCAS Caption" else 8)
        if name == "DBCAS Caption":
            pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
            pf.space_before = Pt(4)
        if name == "DBCAS Code":
            pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
            pf.left_indent = Cm(0.5)
        if name.startswith("DBCAS Cover"):
            pf.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.core_properties.author = AUTHOR
    doc.core_properties.last_modified_by = AUTHOR
    doc.core_properties.title = spec.title
    doc.core_properties.subject = f"{GROUP} {PROJECT} {VERSION_TAG}"
    doc.core_properties.category = spec.category
    doc.core_properties.comments = (f"{GROUP} {PROJECT} {spec.title} "
                                    f"{VERSION_TAG}; author {AUTHOR}")
    doc.core_properties.keywords = f"{GROUP}; {PROJECT}; {VERSION_TAG}"
    return doc


def _para(doc, text="", *, style=None, size=None, color=None, bold=None,
          italic=None, align=None, space_after=None, space_before=None,
          line=None, keep=False):
    p = doc.add_paragraph(style=style)
    if text:
        run = p.add_run(text)
        set_run_font(run, size=size,
                     color=color if color is not None else BLACK,
                     bold=bold, italic=italic)
    if align is not None:
        p.alignment = align
    if space_after is not None:
        p.paragraph_format.space_after = Pt(space_after)
    if space_before is not None:
        p.paragraph_format.space_before = Pt(space_before)
    if line is not None:
        p.paragraph_format.line_spacing = line
    if keep:
        keep_next(p)
    return p


def _cover(doc, spec):
    section = doc.sections[0]
    section.different_first_page_header_footer = True
    page_borders(section)
    valign = OxmlElement("w:vAlign")
    valign.set(qn("w:val"), "center")
    section._sectPr.insert_element_before(
        valign, "w:noEndnote", "w:titlePg", "w:textDirection", "w:bidi",
        "w:rtlGutter", "w:docGrid", "w:printerSettings", "w:sectPrChange")
    # top spacing
    _para(doc, "", space_after=6)
    if LOGO.exists():
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(4)
        p.add_run().add_picture(str(LOGO), width=Cm(6.4))
    _para(doc, "DUY TAN UNIVERSITY", size=13, color=ACCENT, bold=True,
          align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    _para(doc, "International School", size=13, color=ACCENT, bold=True,
          align=WD_ALIGN_PARAGRAPH.CENTER, space_after=18)
    _para(doc, "Capstone Project 1", size=13, align=WD_ALIGN_PARAGRAPH.CENTER,
          space_after=2)
    _para(doc, f"CMU-SE 450_{GROUP}", size=13,
          align=WD_ALIGN_PARAGRAPH.CENTER, space_after=26)
    _para(doc, spec.title, style="DBCAS Cover Title",
          align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)
    _para(doc, f"Version {VERSION}", size=13,
          align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    _para(doc, f"Date: {DATE_LONG}", size=13,
          align=WD_ALIGN_PARAGRAPH.CENTER, space_after=20)
    _para(doc, PROJECT_TITLE, size=13, bold=True,
          align=WD_ALIGN_PARAGRAPH.CENTER, space_after=18)
    _para(doc, f"Submitted by {GROUP}", style="DBCAS Meta",
          align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)
    for name, sid, _email, _role in TEAM:
        _para(doc, f"{name} - {sid}", style="DBCAS Cover Team",
              align=WD_ALIGN_PARAGRAPH.CENTER, space_after=0)
    _para(doc, "", space_after=24)
    _para(doc, "Review Panel Representative", style="DBCAS Cover Signature",
          align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    _para(doc, "Name                    Signature                    Date",
          style="DBCAS Cover Signature",
          align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)
    _para(doc, f"Capstone Project 1 - Mentor: {MENTOR}",
          style="DBCAS Cover Signature",
          align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    _para(doc, "Signature                                        Date",
          style="DBCAS Cover Signature",
          align=WD_ALIGN_PARAGRAPH.CENTER, space_after=0)


def _info_table(doc, rows, *, widths):
    table = doc.add_table(rows=0, cols=len(widths))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table_borders(table, color=RULE, size="4")
    cell_margins(table)
    fixed_layout(table, sum(widths))
    for row in rows:
        cells = table.add_row().cells
        for index, (cell, value) in enumerate(zip(cells, row)):
            cell.width = Cm(widths[index])
            cell.text = ""
            p = cell.paragraphs[0]
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.space_after = Pt(2)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            run = p.add_run(str(value))
            is_label = (len(widths) == 4 and index % 2 == 0) or (len(widths) == 2 and index == 0)
            set_run_font(run, size=TABLE_PT, bold=is_label)
            if is_label:
                shade(cell, TABLE_HEAD)
    normalise_cells(table)
    return table


def _meta_heading(doc, text):
    p = _para(doc, text, style="DBCAS Meta", space_before=12, space_after=6,
              keep=True)
    return p


def _front_matter(doc, spec):
    section = doc.add_section(WD_SECTION.NEW_PAGE)
    configure_page(section)
    existing = section._sectPr.find(qn("w:pgBorders"))
    if existing is not None:
        section._sectPr.remove(existing)
    _header_footer(section, spec)
    _para(doc, "PROJECT INFORMATION", style="DBCAS Meta",
          space_after=6, keep=True)
    rows = [
        ("Project acronym", PROJECT, "Project code", GROUP),
        ("Project title", PROJECT_TITLE, "Version", VERSION),
        ("Start date", START_DATE, "End date", END_DATE),
        ("Lead institution", INSTITUTION, "Project mentor", MENTOR),
        ("Document", spec.title, "File name", spec.filename),
        ("Group", GROUP, "Date", DATE_SLASH),
    ]
    _info_table(doc, rows, widths=[3.2, 4.8, 3.2, 4.3])
    _para(doc, "", space_after=2)

    _meta_heading(doc, "DOCUMENT INFORMATION")
    rows = [
        ("Document title", spec.title, "Version", VERSION_TAG),
        ("Author", AUTHOR, "Role", "Backend Developer"),
        ("Group", GROUP, "Project", PROJECT),
        ("Date", DATE_SLASH, "Status", "Owner review"),
        ("File name", spec.filename, "Access", "Project and CMU Program"),
        ("URL", "[OWNER TO PROVIDE: public document URL]", "Group", GROUP),
    ]
    _info_table(doc, rows, widths=[3.2, 4.8, 3.2, 4.3])

    doc.add_page_break()
    _meta_heading(doc, "DOCUMENT APPROVALS")
    _para(doc, "Approval status: [OWNER TO PROVIDE: approval decisions and "
               "signature dates]. This document does not assert approval.",
          style="DBCAS Note", space_after=6)
    table = doc.add_table(rows=1, cols=4)
    table.autofit = False
    table_borders(table)
    cell_margins(table)
    headers = ("Name", "Student ID", "Role", "Signature / Date")
    widths = [4.6, 2.9, 5.2, 2.8]
    fixed_layout(table, sum(widths))
    for cell, text, width in zip(table.rows[0].cells, headers, widths):
        cell.width = Cm(width)
        shade(cell, TABLE_HEAD)
        p = cell.paragraphs[0]
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_after = Pt(2)
        set_run_font(p.add_run(text), size=TABLE_PT, bold=True)
    repeat_header(table.rows[0])
    for name, sid, _email, role in TEAM:
        cells = table.add_row().cells
        for cell, value, width in zip(cells, (name, sid, role, ""), widths):
            cell.width = Cm(width)
            p = cell.paragraphs[0]
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.space_after = Pt(2)
            set_run_font(p.add_run(value), size=TABLE_PT)
    cells = table.add_row().cells
    for cell, value, width in zip(cells, (MENTOR, "", "Project mentor", ""),
                                  widths):
        cell.width = Cm(width)
        p = cell.paragraphs[0]
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_after = Pt(2)
        set_run_font(p.add_run(value), size=TABLE_PT)
    normalise_cells(table)

    _meta_heading(doc, "REVISION HISTORY")
    table = doc.add_table(rows=1, cols=4)
    table.autofit = False
    table_borders(table)
    cell_margins(table)
    headers = ("Version", "Date", "Description", "Author")
    widths = [1.8, 2.4, 8.3, 3.0]
    fixed_layout(table, sum(widths))
    for cell, text, width in zip(table.rows[0].cells, headers, widths):
        cell.width = Cm(width)
        shade(cell, TABLE_HEAD)
        p = cell.paragraphs[0]
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_after = Pt(2)
        set_run_font(p.add_run(text), size=TABLE_PT, bold=True)
    repeat_header(table.rows[0])
    for row in REVISIONS:
        cells = table.add_row().cells
        for cell, value, width in zip(cells, row, widths):
            cell.width = Cm(width)
            p = cell.paragraphs[0]
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.space_after = Pt(2)
            set_run_font(p.add_run(value), size=TABLE_PT)
    normalise_cells(table)

    doc.add_page_break()
    _para(doc, "TABLE OF CONTENTS", style="DBCAS Meta",
          space_after=10, keep=True)
    toc = doc.add_paragraph()
    toc.paragraph_format.line_spacing = 1.5
    add_toc(toc)


def _header_footer(section, spec):
    section.header.is_linked_to_previous = False
    section.footer.is_linked_to_previous = False
    header = section.header
    p = header.paragraphs[0]
    p.text = ""
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.tab_stops.clear_all()
    usable = PAGE_W - M_LEFT - M_RIGHT
    from docx.enum.text import WD_TAB_ALIGNMENT
    p.paragraph_format.tab_stops.add_tab_stop(usable, WD_TAB_ALIGNMENT.RIGHT)  # right aligned
    left = p.add_run(f"{GROUP} · {PROJECT}")
    set_run_font(left, size=META_PT, color=TEXT2)
    right = p.add_run(f"\t{spec.header}")
    set_run_font(right, size=META_PT, color=TEXT2, bold=True)
    paragraph_bottom_rule(p, color=RULE, size="6")

    footer = section.footer
    fp = footer.paragraphs[0]
    fp.text = ""
    fp.paragraph_format.line_spacing = 1.0
    fp.paragraph_format.tab_stops.clear_all()
    from docx.enum.text import WD_TAB_ALIGNMENT
    fp.paragraph_format.tab_stops.add_tab_stop(usable, WD_TAB_ALIGNMENT.RIGHT)
    set_run_font(fp.add_run(f"{GROUP} · {PROJECT} · {spec.title}"),
                 size=META_PT, color=TEXT2)
    tab = fp.add_run("\tPage ")
    set_run_font(tab, size=META_PT, color=TEXT2)
    add_field(fp, "PAGE", "1", size=META_PT)
    of = fp.add_run(" of ")
    set_run_font(of, size=META_PT, color=TEXT2)
    add_field(fp, "NUMPAGES", "1", size=META_PT)


# --- block renderers --------------------------------------------------------
class Renderer:
    def __init__(self, doc, spec):
        self.doc = doc
        self.spec = spec
        self.table_no = 0
        self.figure_no = 0
        self.heading_no = 0

    # headings ---------------------------------------------------------
    def heading(self, level, text):
        p = self.doc.add_paragraph(style=f"Heading {level}")
        run = p.add_run(text)
        color = {1: "1F3863", 2: TEXT2, 3: BLACK}.get(level, BLACK)
        size = {1: 18, 2: 14, 3: 13, 4: 13}.get(level, 13)
        set_run_font(run, size=size, color=color, bold=True)
        return p

    def paragraph(self, text, **kwargs):
        return _para(self.doc, text, **kwargs)

    def note(self, text):
        return _para(self.doc, text, style="DBCAS Note")

    def bullets(self, items):
        for item in items:
            p = self.doc.add_paragraph(style="List Bullet")
            p.paragraph_format.line_spacing = 1.5
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.left_indent = Cm(0.75)
            p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            run = p.add_run(item)
            set_run_font(run, size=BODY_PT)

    def numbers(self, items):
        for index, item in enumerate(items, 1):
            p = self.doc.add_paragraph(style="Normal")
            p.paragraph_format.line_spacing = 1.5
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.left_indent = Cm(0.75)
            p.paragraph_format.first_line_indent = Cm(-0.75)
            p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            set_run_font(p.add_run(f"{index}. "), size=BODY_PT, bold=True)
            set_run_font(p.add_run(item), size=BODY_PT)

    def table(self, header, rows, *, caption=None, widths=None,
              first_col_bold=False, font=TABLE_PT, align_center=True,
              compact=False):
        if caption:
            self.table_no += 1
            cap = self.doc.add_paragraph(style="DBCAS Caption")
            set_run_font(cap.add_run(f"Table {self.table_no}. {caption}"),
                         size=CAPTION_PT, color=TEXT2, italic=True)
            keep_next(cap)
        ncols = len(header) if header else len(rows[0])
        table = self.doc.add_table(rows=0, cols=ncols)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        table_borders(table)
        cell_margins(table)
        if widths is None:
            widths = [TEXT_W_CM / ncols] * ncols
        for index, width in enumerate(widths):
            table.columns[index].width = Cm(width)
        scale = TEXT_W_CM / sum(widths)
        widths = [w * scale for w in widths]
        if header:
            cells = table.add_row().cells
            for cell, text, width in zip(cells, header, widths):
                cell.width = Cm(width)
                shade(cell, TABLE_HEAD)
                p = cell.paragraphs[0]
                p.paragraph_format.line_spacing = 1.0
                p.paragraph_format.space_after = Pt(1)
                p.paragraph_format.space_before = Pt(1)
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                set_run_font(p.add_run(str(text)), size=font, bold=True)
            repeat_header(table.rows[0])
        for index, row in enumerate(rows):
            cells = table.add_row().cells
            no_split(table.rows[-1])
            for col, (cell, value) in enumerate(zip(cells, row)):
                cell.width = Cm(widths[col])
                p = cell.paragraphs[0]
                p.paragraph_format.line_spacing = 1.0
                p.paragraph_format.space_after = Pt(1)
                p.paragraph_format.space_before = Pt(1)
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                if align_center and len(str(value)) <= 4:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                set_run_font(p.add_run(str(value)), size=font,
                             bold=(first_col_bold and col == 0))
                if index % 2 == 1:
                    shade(cell, TABLE_ALT)
        fixed_layout(table, sum(widths))
        normalise_cells(table)
        if compact:
            spacer = self.doc.add_paragraph()
            spacer.paragraph_format.space_after = Pt(0)
            spacer.paragraph_format.line_spacing = 1.0
            set_run_font(spacer.add_run(""), size=4)
        else:
            _para(self.doc, "", size=6, space_after=4)
        return table

    def figure(self, path, caption, *, width_cm=None):
        from PIL import Image
        self.figure_no += 1
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(2)
        keep_next(p)
        width = Cm(width_cm) if width_cm else None
        if width is None:
            with Image.open(path) as im:
                px_w, px_h = im.size
            width = Cm(min(TEXT_W_CM, TEXT_W_CM * 0.96))
            if px_w / px_h < 1.2:
                width = Cm(TEXT_W_CM * 0.8)
        p.add_run().add_picture(str(path), width=width)
        cap = self.doc.add_paragraph(style="DBCAS Caption")
        set_run_font(cap.add_run(f"Figure {self.figure_no}. {caption}"),
                     size=CAPTION_PT, color=TEXT2, italic=True)

    def code(self, text, *, caption=None):
        if caption:
            cap = self.doc.add_paragraph(style="DBCAS Caption")
            set_run_font(cap.add_run(caption), size=CAPTION_PT, color=TEXT2,
                         italic=True)
            keep_next(cap)
        for line in text.strip("\n").split("\n"):
            p = self.doc.add_paragraph(style="DBCAS Code")
            p.paragraph_format.space_after = Pt(0)
            set_run_font(p.add_run(line if line else " "), name=FONT_CODE,
                         size=CODE_PT)
        _para(self.doc, "", size=6, space_after=4)

    def callout(self, text):
        p = _para(self.doc, text, style="DBCAS Note",
                  space_before=2, space_after=8)
        p.paragraph_format.left_indent = Cm(0.5)
        paragraph_bottom_rule(p, color=RULE, size="4")

    def reference(self, text):
        p = self.doc.add_paragraph(style="Normal")
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.left_indent = Cm(1.1)
        p.paragraph_format.first_line_indent = Cm(-1.1)
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        set_run_font(p.add_run(text), size=BODY_PT)

    def page_break(self):
        self.doc.add_page_break()


def build_document(spec, blocks, out_path):
    doc = new_document(spec)
    _cover(doc, spec)
    _front_matter(doc, spec)
    doc.add_page_break()
    renderer = Renderer(doc, spec)
    for block in blocks:
        kind = block[0]
        if kind == "h1":
            renderer.heading(1, block[1])
        elif kind == "h2":
            renderer.heading(2, block[1])
        elif kind == "h3":
            renderer.heading(3, block[1])
        elif kind == "h4":
            renderer.heading(4, block[1])
        elif kind == "p":
            renderer.paragraph(block[1])
        elif kind == "note":
            renderer.note(block[1])
        elif kind == "bullets":
            renderer.bullets(block[1])
        elif kind == "numbers":
            renderer.numbers(block[1])
        elif kind == "table":
            options = dict(block[1])
            header = options.pop("header", None)
            rows = options.pop("rows")
            renderer.table(header, rows, **options)
        elif kind == "figure":
            renderer.figure(block[1], block[2], **(block[3] if len(block) > 3 else {}))
        elif kind == "code":
            renderer.code(block[1], **(block[2] if len(block) > 2 else {}))
        elif kind == "callout":
            renderer.callout(block[1])
        elif kind == "ref":
            renderer.reference(block[1])
        elif kind == "pagebreak":
            renderer.page_break()
        else:
            raise ValueError(f"unknown block {kind}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_path))
    return renderer
