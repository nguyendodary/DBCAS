# -*- coding: utf-8 -*-
"""Revise the five submission DOCX in place from their baselines.

The three academic documents are the content-complete Documents/Final-ver1.3
packages; Code Standards and Technical Report use the best existing DBCAS files
(no older baseline exists). The script changes text, tables, figures, headers,
footers, margins and properties without rebuilding the documents.

Usage:
  py scripts/revise_submission_docs.py proposal
  py scripts/revise_submission_docs.py architecture
  py scripts/revise_submission_docs.py database
  py scripts/revise_submission_docs.py codestandards
  py scripts/revise_submission_docs.py technicalreport
  py scripts/revise_submission_docs.py all
"""
from __future__ import annotations

import copy
import datetime as dt
import re
import sys
from pathlib import Path

import docx
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "docs/submission/final"
ASSETS = FINAL / "assets"
FIG = ASSETS / "figures"
ERD = ASSETS / "erd"
DATE_LONG = "November 26th, 2026"
DATE_SHORT = "26/11/2026"
AUTHOR = "Do, Nguyen Quoc"
NAVY = RGBColor(0x1F, 0x38, 0x63)
GREY = RGBColor(0x44, 0x54, 0x6A)

DOCS = {
    "proposal": ("C1SE.70_ProposalDocument_DBCAS_ver1.3.docx", "Proposal Document"),
    "architecture": ("C1SE.70_ArchitectureDesign_DBCAS_ver1.3.docx", "Architecture Design Document"),
    "database": ("C1SE.70_DatabaseDesign_DBCAS_ver1.3.docx", "Database Design Document"),
    "codestandards": ("C1SE.70_CodeStandards_DBCAS_ver1.3.docx", "Code Standards Document"),
    "technicalreport": ("C1SE.70_TechnicalReport_DBCAS_ver1.3.docx", "Technical Report"),
}


# ---------------------------------------------------------------------------
# low-level helpers
# ---------------------------------------------------------------------------
def iter_paragraphs(container):
    for p in container.paragraphs:
        yield p
    for table in container.tables:
        for row in table.rows:
            for cell in row.cells:
                yield from cell.paragraphs


def replace_in_paragraph(p, old, new):
    if old not in p.text:
        return 0
    for run in p.runs:
        if old in run.text:
            run.text = run.text.replace(old, new)
            return 1
    # text split across runs: rebuild the paragraph, keeping the first run format
    full = p.text.replace(old, new)
    first = next((r for r in p.runs if r.text), None)
    for run in p.runs:
        run.text = ""
    if first is not None:
        first.text = full
    else:
        p.add_run(full)
    return 1


def replace_everywhere(doc, old, new):
    count = 0
    for p in iter_paragraphs(doc):
        count += replace_in_paragraph(p, old, new)
    for section in doc.sections:
        for part in (section.header, section.footer):
            for p in part.paragraphs:
                count += replace_in_paragraph(p, old, new)
    return count


def find_para(doc, needle, start=0):
    for i, p in enumerate(doc.paragraphs):
        if i >= start and needle in p.text:
            return p
    return None


def find_table(doc, header_needle):
    for t in doc.tables:
        if not t.rows:
            continue
        head = " | ".join(c.text.strip() for c in t.rows[0].cells)
        if header_needle.lower() in head.lower():
            return t
    return None


def set_cell(cell, text, *, size=9, bold=False, color=None, align=None):
    cell.text = ""
    p = cell.paragraphs[0]
    if align is not None:
        p.alignment = align
    run = p.add_run(str(text))
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.bold = bold
    if color is not None:
        run.font.color.rgb = color
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.0


def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def add_field(paragraph, instr, placeholder="1", *, size=9, italic=True):
    def run_with(child):
        run = paragraph.add_run()
        run.font.size = Pt(size)
        run.font.name = "Times New Roman"
        run.italic = italic
        run._r.append(child)
        return run
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr_el = OxmlElement("w:instrText")
    instr_el.set(qn("xml:space"), "preserve")
    instr_el.text = f" {instr} "
    sep = OxmlElement("w:fldChar")
    sep.set(qn("w:fldCharType"), "separate")
    txt = OxmlElement("w:t")
    txt.text = placeholder
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run_with(begin)
    run_with(instr_el)
    run_with(sep)
    run_with(txt)
    run_with(end)


def border(paragraph, edge="bottom", sz=6, color="44546A"):
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = pPr.find(qn("w:pBdr"))
    if pBdr is None:
        pBdr = OxmlElement("w:pBdr")
        pPr.append(pBdr)
    el = OxmlElement(f"w:{edge}")
    el.set(qn("w:val"), "single")
    el.set(qn("w:sz"), str(sz))
    el.set(qn("w:space"), "1")
    el.set(qn("w:color"), color)
    pBdr.append(el)


def clear_part(part):
    for p in list(part.paragraphs)[1:]:
        p._element.getparent().remove(p._element)
    p = part.paragraphs[0]
    for run in list(p.runs):
        run._r.getparent().remove(run._r)
    return p


def style_run(run, size=9, italic=True, color=GREY):
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.italic = italic
    run.font.color.rgb = color


def set_header_footer(section, doc_title):
    section.header.is_linked_to_previous = False
    section.footer.is_linked_to_previous = False
    width_cm = (section.page_width - section.left_margin - section.right_margin) / 360000
    hp = clear_part(section.header)
    hp.paragraph_format.tab_stops.add_tab_stop(Cm(width_cm), WD_TAB_ALIGNMENT.RIGHT)
    hp.paragraph_format.space_after = Pt(0)
    r = hp.add_run(f"C1SE.70 · DBCAS · {doc_title}")
    style_run(r, 9, True)
    hp.add_run("\t")
    r = hp.add_run("International School Capstone 1 – 2026")
    style_run(r, 9, True)
    border(hp, "bottom")
    fp = clear_part(section.footer)
    fp.paragraph_format.tab_stops.add_tab_stop(Cm(width_cm), WD_TAB_ALIGNMENT.RIGHT)
    fp.paragraph_format.space_after = Pt(0)
    r = fp.add_run(AUTHOR)
    style_run(r, 9, True)
    fp.add_run("\t")
    r = fp.add_run("Page ")
    style_run(r, 9, True)
    add_field(fp, "PAGE", "1", size=9, italic=True)
    r = fp.add_run(" of ")
    style_run(r, 9, True)
    add_field(fp, "NUMPAGES", "1", size=9, italic=True)
    border(fp, "top")


def set_page_start(section, start=1):
    sectPr = section._sectPr
    pgNumType = sectPr.find(qn("w:pgNumType"))
    if pgNumType is None:
        pgNumType = OxmlElement("w:pgNumType")
        sectPr.append(pgNumType)
    pgNumType.set(qn("w:start"), str(start))


def set_margins(section):
    section.left_margin = Cm(3.5)
    section.right_margin = Cm(2.0)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.0)


def set_styles(doc):
    # document defaults: Times New Roman 13 pt, 1.5 line spacing
    styles_el = doc.styles.element
    defaults = styles_el.find(qn("w:docDefaults"))
    if defaults is not None:
        rPr = defaults.find(qn("w:rPrDefault"))
        if rPr is not None:
            rPr = rPr.find(qn("w:rPr"))
            if rPr is not None:
                for tag in ("w:sz", "w:szCs"):
                    el = rPr.find(qn(tag))
                    if el is None:
                        el = OxmlElement(tag)
                        rPr.append(el)
                    el.set(qn("w:val"), "26")
                fonts = rPr.find(qn("w:rFonts"))
                if fonts is None:
                    fonts = OxmlElement("w:rFonts")
                    rPr.insert(0, fonts)
                for attr in ("w:ascii", "w:eastAsia", "w:hAnsi", "w:cs"):
                    fonts.set(qn(attr), "Times New Roman")
        pPr = defaults.find(qn("w:pPrDefault"))
        if pPr is not None:
            pPr = pPr.find(qn("w:pPr"))
            if pPr is not None:
                spacing = pPr.find(qn("w:spacing"))
                if spacing is None:
                    spacing = OxmlElement("w:spacing")
                    pPr.append(spacing)
                spacing.set(qn("w:line"), "360")
                spacing.set(qn("w:lineRule"), "auto")
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(13)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_after = Pt(6)
    for name, size, before, after in (("Heading 1", 18, 12, 6), ("Heading 2", 14, 10, 4), ("Heading 3", 13, 8, 4)):
        try:
            st = doc.styles[name]
        except KeyError:
            continue
        st.font.name = "Times New Roman"
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.color.rgb = NAVY
        st.paragraph_format.space_before = Pt(before)
        st.paragraph_format.space_after = Pt(after)
        st.paragraph_format.keep_with_next = True
    try:
        cap = doc.styles["Caption"]
        cap.font.name = "Times New Roman"
        cap.font.size = Pt(11)
        cap.font.italic = True
        cap.font.color.rgb = GREY
        cap.paragraph_format.space_before = Pt(4)
        cap.paragraph_format.space_after = Pt(8)
    except KeyError:
        pass


def enable_update_fields(doc):
    settings = doc.settings.element
    upd = settings.find(qn("w:updateFields"))
    if upd is None:
        upd = OxmlElement("w:updateFields")
        settings.append(upd)
    upd.set(qn("w:val"), "true")


def update_core(doc, title):
    cp = doc.core_properties
    cp.author = AUTHOR
    cp.last_modified_by = AUTHOR
    cp.title = title
    cp.subject = "C1SE.70 DBCAS ver1.3"
    cp.keywords = "C1SE.70; DBCAS; FITAI; ver1.3"
    cp.category = "Capstone Project 1"
    cp.comments = "In-place revision of the content-complete ver1.3 baseline."
    cp.language = "en-US"
    cp.modified = dt.datetime(2026, 11, 26, 12, 0, 0)
    cp.revision = max(cp.revision or 1, 14)


def apply_common(doc, doc_title):
    for section in doc.sections:
        set_margins(section)
    for i, section in enumerate(doc.sections):
        if i == 0:
            # cover: no running head or page number
            section.header.is_linked_to_previous = False
            section.footer.is_linked_to_previous = False
            clear_part(section.header)
            clear_part(section.footer)
        else:
            set_header_footer(section, doc_title)
    set_page_start(doc.sections[1], 1)
    set_styles(doc)
    update_core(doc, f"{doc_title} — ver1.3")
    enable_update_fields(doc)


# ---------------------------------------------------------------------------
# text/table edits
# ---------------------------------------------------------------------------
def fix_cover_and_revision(doc):
    placeholder = "[OWNER TO PROVIDE: confirmed public URL, or an explicit decision that the demo remains local]"
    for old in ("OWNER UNKNOWN - no public URL verified", "OWNER UNKNOWN – no public URL verified",
                "OWNER UNKNOWN — no public URL verified", "OWNER UNKNOWN — no live URL is verified."):
        replace_everywhere(doc, old, placeholder)
    replace_everywhere(doc, "OWNER UNKNOWN", "[OWNER TO PROVIDE: verify this value]")
    for old, new in (
        ("November 25th, 2026", DATE_LONG),
        ("25/11/2026", DATE_SHORT),
        ("Align to the measured FITAI layout and re-verify every measured figure",
         "Rebuilt in place from the content-complete ver1.3 baseline; facts, figures and counts re-measured against migration 028"),
    ):
        replace_everywhere(doc, old, new)
    t = find_table(doc, "Version | Date | Description")
    if t is None:
        t = find_table(doc, "Version")
    if t is not None:
        for row in t.rows:
            if row.cells and row.cells[0].text.strip() == "1.3":
                set_cell(row.cells[1], DATE_SHORT, size=9)
                if len(row.cells) > 2:
                    set_cell(row.cells[2], "Rebuilt in place from the content-complete ver1.3 baseline; facts, figures and counts re-measured against migration 028", size=9)
                if len(row.cells) > 3:
                    set_cell(row.cells[3], AUTHOR, size=9)
    fixed = fix_missing_caption_numbers(doc)
    if fixed:
        print(f"  restored {fixed} caption numbers")


def fix_missing_caption_numbers(doc):
    """Restore the number in body captions whose SEQ field was stripped.

    The List of Figures/Tables retains the correct numbers, so match by title
    rather than by counting (the body order and the list order are identical,
    but a title match is safer).
    """
    known = {}
    for p in doc.paragraphs:
        if p.style.name.lower() != "table of figures":
            continue
        m = re.match(r"(Figure|Table)\s+(\d+)\.\s*(.+?)(?:\t\d+)?$", p.text.strip())
        if m:
            known[(m.group(1), m.group(3).strip())] = m.group(2)
    fixed = 0
    for p in doc.paragraphs:
        if p.style.name.lower() == "table of figures":
            continue
        m = re.match(r"(Figure|Table)\s+\.\s*(.+)$", p.text.strip())
        if not m:
            continue
        kind, title = m.group(1), m.group(2).strip()
        num = known.get((kind, title))
        if num is None:
            # tolerate a changed suffix after a successful in-place edit
            for (k, t), n in known.items():
                if k == kind and (title.startswith(t[:40]) or t.startswith(title[:40])):
                    num = n
                    break
        if num:
            new = f"{kind} {num}. {title}"
            for run in p.runs:
                run.text = ""
            if p.runs:
                p.runs[0].text = new
            else:
                p.add_run(new)
            fixed += 1
    return fixed


def clean_table54_list_entry(doc):
    new_title = "Table 54. Details about the 41 core ERD tables"
    for p in doc.paragraphs:
        if p.style.name.lower() != "table of figures" or "Table 54" not in p.text:
            continue
        # remove an accidentally appended direct run outside the hyperlink;
        # the original hyperlink and its PAGEREF stay intact, and Word refreshes
        # the list field on render if it is a TOF field.
        for r in list(p._p.findall(qn("w:r"))):
            p._p.remove(r)


def add_owner_appendix(doc, heading="Appendix A. Open owner decisions"):
    doc.add_page_break()
    h = doc.add_heading(heading, level=1)
    h.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p = doc.add_paragraph("The following values are not derivable from the repository. They stay owner-owned and are not asserted anywhere in this document.")
    p.paragraph_format.space_after = Pt(6)
    rows = [
        ("O1", "Team identities", "Confirm every student ID, email address and phone number in Table 1", "Open"),
        ("O2", "Supervisor and faculty", "Confirm the official faculty/department name and whether an industry co-supervisor is required", "Open"),
        ("O3", "Approvals and signatures", "Sign the approval table and supply the approval dates", "Open"),
        ("O4", "Public document URL", "Provide the public URL, or confirm that the demo remains local", "Open"),
        ("O5", "Survey provenance", "Confirm the survey date/method and add one citation per surveyed product", "Open"),
        ("O6", "Effort and velocity", "Confirm per-member effort allocation, story points and sprint attendance", "Open"),
        ("O7", "Sandbox capacity", "Accept two concurrent SQL executions for the demonstration", "Open"),
        ("O8", "Legacy data", "Decide whether the legacy assessment tables are dropped and confirm the retention period", "Open"),
        ("O9", "Appendices", "Decide whether the classical use-case/component appendices are restored", "Open"),
        ("O10", "References", "Verify every URL/DOI and supply any missing source", "Open"),
    ]
    t = doc.add_table(rows=1 + len(rows), cols=4)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    try:
        t.style = doc.styles["Table Grid"]
    except KeyError:
        pass
    widths = [Cm(1.3), Cm(3.2), Cm(8.4), Cm(1.6)]
    for j, text in enumerate(("ID", "Item", "Owner action required", "Status")):
        set_cell(t.rows[0].cells[j], text, size=9, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF))
        shade(t.rows[0].cells[j], "1F3863")
    for i, row in enumerate(rows, 1):
        for j, text in enumerate(row):
            set_cell(t.rows[i].cells[j], text, size=8.5)
            if i % 2 == 0:
                shade(t.rows[i].cells[j], "EAF4FB")
    for row in t.rows:
        for j, cell in enumerate(row.cells):
            cell.width = widths[j]


def add_figure_sources(doc, rows, heading="Appendix B. Figure sources"):
    doc.add_page_break()
    h = doc.add_heading(heading, level=1)
    h.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p = doc.add_paragraph("Every shipped figure is traceable to a repository source. The figure number is the number used in the body and in the List of Figures.")
    p.paragraph_format.space_after = Pt(6)
    t = doc.add_table(rows=1 + len(rows), cols=4)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    try:
        t.style = doc.styles["Table Grid"]
    except KeyError:
        pass
    widths = [Cm(2.0), Cm(4.4), Cm(6.2), Cm(2.0)]
    for j, text in enumerate(("Figure", "Title", "Source of truth", "Verification")):
        set_cell(t.rows[0].cells[j], text, size=9, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF))
        shade(t.rows[0].cells[j], "1F3863")
    for i, row in enumerate(rows, 1):
        for j, text in enumerate(row):
            set_cell(t.rows[i].cells[j], text, size=8.5)
            if i % 2 == 0:
                shade(t.rows[i].cells[j], "EAF4FB")
    for row in t.rows:
        for j, cell in enumerate(row.cells):
            cell.width = widths[j]


def add_row_after(table, index):
    new_tr = copy.deepcopy(table.rows[index]._tr)
    table.rows[index]._tr.addnext(new_tr)
    return table.rows[index + 1]


# ---------------------------------------------------------------------------
# figure replacement
# ---------------------------------------------------------------------------
def replace_picture(paragraph, image_path, width_cm):
    # remove the first drawing run and add a new picture run at the same point
    for run in paragraph.runs:
        if run._r.find(qn("w:drawing")) is not None:
            run._r.getparent().remove(run._r)
            break
    run = paragraph.add_run()
    run.add_picture(str(image_path), width=Cm(width_cm))


def image_paragraphs_between(doc, start_needle, end_needle):
    start = None
    end = len(doc.paragraphs)
    for i, p in enumerate(doc.paragraphs):
        if start is None and start_needle in p.text and p.style.name.lower().startswith("heading"):
            start = i
        elif start is not None and end_needle in p.text:
            end = i
            break
    return [p for p in doc.paragraphs[start:end] if p._element.findall(".//" + qn("w:drawing"))]


def replace_erd_figures(doc, prefix_fig7, prefix_fig8, module_label="module"):
    paras = image_paragraphs_between(doc, "Entity Relationship Diagram", "Details about ERD")
    images = [ERD / "erd-overview.png", ERD / "erd-index.png"] + [ERD / f"erd-module-{i}.png" for i in range(1, 8)] + [ERD / f"erd-ledger-{i}.png" for i in range(1, 5)]
    assert len(paras) == 13, f"expected 13 ERD image paragraphs, found {len(paras)}"
    for p, img in zip(paras, images):
        replace_picture(p, img, 20.5)
    # captions: the next non-empty paragraph after each image
    captions = []
    for p in paras:
        nxt = p._element.getnext()
        while nxt is not None and nxt.tag == qn("w:p"):
            text = "".join(n.text or "" for n in nxt.iter(qn("w:t"))).strip()
            if text:
                captions.append((nxt, text))
                break
            nxt = nxt.getnext()
        else:
            captions.append((None, ""))
    names = ["Identity and access", "Curriculum and concepts", "Question bank and generation",
             "Assessment and attempts", "Grading, results and competency", "Review workflow",
             "AI audit and retention"]
    starts = [1, 32, 63, 93]
    ends = [31, 62, 92, 122]
    wanted = [f"{prefix_fig7} Entity relationship overview (1/2)",
              f"{prefix_fig7} Entity relationship index (2/2)"]
    for i, name in enumerate(names, 1):
        wanted.append(f"{prefix_fig8} Entity relationship diagram — {name} ({i}/11)")
    for i in range(4):
        wanted.append(f"{prefix_fig8} Foreign-key ledger — rows {starts[i]}–{ends[i]} of 122 ({8 + i}/11)")
    for (el, old), new in zip(captions, wanted):
        if el is None:
            continue
        # replace text in the first run, clear the rest
        runs = el.findall(qn("w:r"))
        if runs:
            first = runs[0]
            for r in runs[1:]:
                el.remove(r)
            for t in first.findall(qn("w:t")):
                first.remove(t)
            t = OxmlElement("w:t")
            t.set(qn("xml:space"), "preserve")
            t.text = new
            first.append(t)


def replace_one_figure(doc, caption_needle, image_path, width_cm, new_caption=None):
    p = None
    for candidate in doc.paragraphs:
        if caption_needle in candidate.text and candidate.style.name.lower() != "table of figures":
            p = candidate
            break
    if p is None:
        return False
    # image is the nearest preceding paragraph with a drawing
    prev = p._element.getprevious()
    while prev is not None:
        if prev.tag == qn("w:p") and prev.findall(".//" + qn("w:drawing")):
            from docx.text.paragraph import Paragraph
            para = Paragraph(prev, p._parent)
            replace_picture(para, image_path, width_cm)
            break
        prev = prev.getprevious()
    if new_caption:
        for run in p.runs:
            run.text = ""
        if p.runs:
            p.runs[0].text = new_caption
        else:
            p.add_run(new_caption)
    return True


# ---------------------------------------------------------------------------
# document-specific edits
# ---------------------------------------------------------------------------
def revise_proposal():
    path = FINAL / DOCS["proposal"][0]
    doc = docx.Document(str(path))
    apply_common(doc, "Proposal Document")
    fix_cover_and_revision(doc)

    # supervisor wording
    replace_everywhere(doc, "academic faculty from the Software Engineering Department at the International School",
                       "academic faculty from the CSE Center at the International School")

    # survey citations
    p = find_para(doc, "Our team did not conduct direct student interviews")
    if p:
        p.add_run(" The difficulties recur in the database-education literature and in public practitioner discussions [1], [2], [6], [8].")
    p = find_para(doc, "Websites like LeetCode")
    if p:
        p.add_run(" The exact-output practice-site model is documented by LeetCode's database problem set [14].")
    p = find_para(doc, "Systems like Moodle")
    if p:
        p.add_run(" Outcome-based course design is required by the ACM/IEEE curriculum guidance [3].")
    p = find_para(doc, "General-purpose AI chatbots")
    if p:
        p.add_run(" The opportunities and risks of generative AI in computing education are documented in [6] and [7].")

    # technology stack: nine layers, add AI/ML and testing rows
    replace_everywhere(doc, "organized across seven core system layers", "organized across nine core system layers")
    t = find_table(doc, "System Layer")
    if t is not None:
        ai_row = None
        for i, row in enumerate(t.rows):
            if "AI Service Integration" in row.cells[0].text:
                ai_row = i
        if ai_row is not None:
            new = add_row_after(t, ai_row)
            set_cell(new.cells[0], "AI / ML (applied)", size=8.5, bold=True)
            set_cell(new.cells[1], "No trained model; external LLM API", size=8.5)
            set_cell(new.cells[2], "OpenAI-compatible chat completions via .env", size=8.5)
            set_cell(new.cells[3], "No model is trained, fine-tuned or hosted. The provider is configured through environment variables, prompts and responses are schema-validated, and a deterministic rubric is the fallback when the provider fails.", size=8.5)
            new2 = add_row_after(t, ai_row + 1)
            set_cell(new2.cells[0], "Testing & QA", size=8.5, bold=True)
            set_cell(new2.cells[1], "pytest, Vitest, Playwright, gate scripts", size=8.5)
            set_cell(new2.cells[2], "pytest 9.1.1 / Vitest 4.1.12 / Playwright 1.64", size=8.5)
            set_cell(new2.cells[3], "Backend, frontend and browser suites plus docs, schema, inventory, secret and contrast gates; every result is cited to a saved log.", size=8.5)

    # FR-06 split: remove session configuration from FR-06, add it to FR-07
    t = find_table(doc, "FR ID")
    if t is not None:
        for row in t.rows:
            if row.cells[0].text.strip() == "FR-06":
                set_cell(row.cells[2], "System exposes read-only runtime status (AI evaluator, prompt builder, database and pipeline) and applies the release policy: FIXED Test publishes AI-official V1 at finalize; legacy/practice results use AI grading then administrator review and approval. Administrators do not choose between automatic and reviewed release, and do not create exams.", size=8.5)
            if row.cells[0].text.strip() == "FR-07":
                current = row.cells[2].text.strip()
                set_cell(row.cells[2], current + " The learner also fixes the session configuration before question one: concepts, difficulty bands, an exact question count (1–13 legacy; single-type caps MCQ 50 / SQL 5 / essay 10; mixed total 25 with caps MCQ 20 / SQL 2 / essay 3; default 5) and a source (validated bank or AI).", size=8.5)

    # explicit Mode 1 / Mode 2 source description
    anchor = find_para(doc, "7.2. Functional Requirements")
    if anchor is not None and "Mode 1 draws only" not in anchor.text:
        text = ("Two question-source modes are exposed in the practice setup. Mode 1 draws only from the administrator-reviewed bank. "
                "Mode 2 requests live AI questions for one concept and one starting band; generated items pass the same validation gate, "
                "SQL items still come from the bank, and any provider failure falls back to the bank. The Free demo plan hides Mode 2; "
                "Pro is a UI-only simulation with no payment or backend entitlement.")
        new = anchor.insert_paragraph_before(text)
        new.style = doc.styles["Normal"]
        new.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for run in new.runs:
            run.font.name = "Times New Roman"
            run.font.size = Pt(13)

    # risk register contradiction
    replace_everywhere(doc, "accept SELECT statements only; DML/DDL are assessed through MCQ and essay.",
                       "accept SELECT by default; DML/DDL run only in the opt-in writable demo, inside the disposable container and always rolled back; grading remains read-only.")
    placeholder = "[OWNER TO PROVIDE: confirmed public URL, or an explicit decision that the demo remains local]"
    replace_everywhere(doc, "OWNER UNKNOWN — no live URL is verified.", placeholder)
    replace_everywhere(doc, "OWNER UNKNOWN – no public URL verified", placeholder)
    replace_everywhere(doc, "OWNER UNKNOWN — no public URL verified", placeholder)
    replace_everywhere(doc, "OWNER UNKNOWN", "[OWNER TO PROVIDE: verify this value]")

    # reference [13] author correction
    replace_everywhere(doc, 'S. Ramírez, "FastAPI Documentation', 'FastAPI project and contributors, "FastAPI Documentation')

    # figures: Gantt, context and logical architecture
    replace_one_figure(doc, "Figure 1: Agile Scrum Sprint Roadmap", FIG / "gantt-roadmap.png", 15.5)
    replace_one_figure(doc, "Figure 2: DBCAS System Context Diagram", FIG / "system-context.png", 15.5)
    replace_one_figure(doc, "Figure 3: DBCAS Logical System Architecture Diagram", FIG / "logical-architecture.png", 15.5)

    # appendices
    add_owner_appendix(doc)
    add_figure_sources(doc, [
        ("Figure 1", "Agile delivery roadmap", "Proposal Table 13; docs/academic proposal calendar", "13 dated rows; final submission before defence"),
        ("Figure 2", "DBCAS system context", "docker-compose.local.yml; routers; services/oauth.py; services/mail.py; docs/openapi.json", "106 paths / 118 operations"),
        ("Figure 3", "DBCAS logical architecture", "backend/app/main.py; Dockerfile; docker-compose.local.yml; docs/openapi.json", "7 routers; 67 tables / 561 columns / 122 FKs"),
        ("Figure 4", "Evidence-based competency and gap pipeline", "backend/app/services/{prompt_builder,evaluation_pipeline,result_version}.py", "release paths checked against FR-12"),
    ])
    doc.save(str(path))
    print(f"revised {path.name}")


def revise_architecture():
    path = FINAL / DOCS["architecture"][0]
    doc = docx.Document(str(path))
    apply_common(doc, "Architecture Design Document")
    fix_cover_and_revision(doc)
    replace_everywhere(doc, "all 67 tables are described in Table 54.",
                       "the 41 core tables are described in Table 54; the 26 tables added by migrations 020–028 are described in Appendix A of the Database Design document.")
    replace_everywhere(doc, "Figure  (1/2). Component Diagram", "Figure 4 (1/2). Component Diagram")
    replace_everywhere(doc, "Figure  (2/2). Component Diagram", "Figure 4 (2/2). Component Diagram")
    replace_everywhere(doc, "Table . Details about ERD tables", "Table 54. Details about the 41 core ERD tables")
    replace_erd_figures(doc, "Figure 7.", "Figure 8.")
    replace_everywhere(doc, "Table 54. Details about ERD tables", "Table 54. Details about the 41 core ERD tables")
    clean_table54_list_entry(doc)
    # shared context and logical figures
    replace_one_figure(doc, "Figure 2. System Context Diagram", FIG / "system-context.png", 15.5)
    replace_one_figure(doc, "Figure 3. Container Diagram", FIG / "logical-architecture.png", 15.5)
    # explicit Mode 1 / Mode 2 source description in the practice use case
    for t in doc.tables:
        for row in t.rows:
            if any("Take a Personalized Practice Session" in c.text for c in row.cells):
                cell = row.cells[1] if len(row.cells) > 1 else row.cells[0]
                if "Mode 1" not in cell.text:
                    para = cell.add_paragraph("Two source modes: Mode 1 uses the reviewed bank; Mode 2 uses live AI questions for one concept and one starting band, with SQL and fallback still bank-only; the Free demo hides Mode 2.")
                    for run in para.runs:
                        run.font.name = "Times New Roman"
                        run.font.size = Pt(9)
                break
        else:
            continue
        break
    p = find_para(doc, "All persistent data is stored in a PostgreSQL 17 database")
    if p is not None and "OpenAI-compatible endpoint" not in p.text:
        p.add_run(" The LLM Provider is an OpenAI-compatible endpoint configured through environment variables; no model weights are hosted.")
    add_owner_appendix(doc)
    add_figure_sources(doc, [
        ("Figure 1", "Use case diagram", "docs/diagrams/rebuild/use-case; use-case.svg", "UC01–UC18 reviewed"),
        ("Figure 2", "System context", "docker-compose.local.yml; routers; oauth/mail services", "external services verified in configuration"),
        ("Figure 3", "Container / logical view", "backend/app/main.py; Dockerfile; compose files", "7 routers; 67/561/122/159/28"),
        ("Figure 4", "Component diagram (1/2, 2/2)", "docs/diagrams/rebuild/component", "responsibilities traced to services"),
        ("Figure 5", "Module view", "docs/diagrams/rebuild/module", "72 top-level service modules"),
        ("Figure 6", "Allocation view", "docker-compose.local.yml; qa/real-qa compose", "deployment view"),
        ("Figure 7", "ERD overview and index (1/2, 2/2)", "docs/diagrams/schema-028/schema-introspection.json", "67 tables / 561 columns / 122 FKs"),
        ("Figure 8", "Module ERDs and FK ledgers (1/11–11/11)", "docs/diagrams/schema-028/schema-introspection.json", "122 FKs enumerated; cardinality and delete rules"),
    ])
    doc.save(str(path))
    print(f"revised {path.name}")


def revise_database():
    path = FINAL / DOCS["database"][0]
    doc = docx.Document(str(path))
    apply_common(doc, "Database Design Document")
    fix_cover_and_revision(doc)
    # index breakdown from introspection
    p = find_para(doc, "In PostgreSQL, data is organized into tables")
    if p:
        p.insert_paragraph_before(
            "The 159 indexes comprise 67 primary-key indexes, 50 unique indexes and 42 standalone performance indexes "
            "(67 + 50 + 42 = 159). Unique constraints are counted separately from the indexes that enforce them."
        )
    replace_everywhere(doc, "all 67 tables appear across the 11 pages of Figure 2",
                       "all 67 tables appear across the seven module pages and four relationship ledgers of Figure 2")
    replace_everywhere(doc, "Figure 1 is the conceptual model: the many-to-many relationships",
                       "Figure 1 (1/2–2/2) is the domain overview and table index; Figure 2 (1/11–11/11) is the module ERD and foreign-key ledger set. The many-to-many relationships")
    replace_erd_figures(doc, "Figure 1:", "Figure 2:")
    add_owner_appendix(doc)
    add_figure_sources(doc, [
        ("Figure 1", "ERD overview and index (1/2, 2/2)", "schema-028/schema-introspection.json", "67 tables / 561 columns / 122 FKs / 159 indexes / 28 migrations"),
        ("Figure 2", "Module ERDs (1/7–7/7)", "schema-028/schema-introspection.json", "67 tables mapped once to seven domains; intra-module FK lines"),
        ("Figure 2", "FK ledgers (8/11–11/11)", "schema-028/schema-introspection.json", "122 foreign keys with cardinality and delete/update rules"),
    ])
    doc.save(str(path))
    print(f"revised {path.name}")


def revise_codestandards():
    path = FINAL / DOCS["codestandards"][0]
    doc = docx.Document(str(path))
    apply_common(doc, "Code Standards Document")
    fix_cover_and_revision(doc)
    # insert a legible layering figure after section 4 prose
    p = find_para(doc, "The backend separates HTTP contracts, use cases and queries.")
    if p is not None:
        cap = p.insert_paragraph_before("")
        cap.style = doc.styles["Caption"]
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.add_run("Figure 1. Backend layering and dependency direction").italic = True
        pic = p.insert_paragraph_before("")
        pic.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pic.add_run().add_picture(str(FIG / "backend-layering.png"), width=Cm(15.2))
    add_owner_appendix(doc)
    add_figure_sources(doc, [
        ("Figure 1", "Backend layering and dependency direction", "backend/app/routers; services; repositories.py; docs/diagrams", "dependency direction is a review standard; measured exceptions listed in §4"),
    ])
    doc.save(str(path))
    print(f"revised {path.name}")


def revise_technicalreport():
    path = FINAL / DOCS["technicalreport"][0]
    doc = docx.Document(str(path))
    apply_common(doc, "Technical Report")
    fix_cover_and_revision(doc)
    t = find_table(doc, "Measurement")
    if t is not None:
        for row in t.rows:
            if row.cells[0].text.strip() == "E10":
                set_cell(row.cells[1], "Document set built from baselines and measured sources", size=9)
                set_cell(row.cells[2], "5 documents: 3 revised in place from the content-complete baseline, 2 from their existing baselines; every figure traced to repository sources; XML layout checked", size=9)
                set_cell(row.cells[3], "build_erd_relationships + revise_submission_docs + Word field refresh", size=9)
    replace_everywhere(doc, "every figure in this report was re-measured from the repository.",
                       "the figure in this report was re-measured from the repository.")
    replace_everywhere(doc, 'S. Ramírez and contributors, "FastAPI Documentation',
                       'FastAPI project and contributors, "FastAPI Documentation')
    add_owner_appendix(doc)
    add_figure_sources(doc, [
        ("Figure 1", "AI generation, evaluation and fallback pipeline", "services/{governed_generation,prompt_builder,llm,evaluation_pipeline}.py", "two AI roles, schema/domain gates, deterministic fallback"),
    ])
    doc.save(str(path))
    print(f"revised {path.name}")


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    funcs = {
        "proposal": revise_proposal,
        "architecture": revise_architecture,
        "database": revise_database,
        "codestandards": revise_codestandards,
        "technicalreport": revise_technicalreport,
    }
    if which == "all":
        for fn in funcs.values():
            fn()
    else:
        funcs[which]()


if __name__ == "__main__":
    main()
