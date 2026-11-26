# -*- coding: utf-8 -*-
"""Sync Architecture facts/release wording from the content-complete reference.

The baseline keeps its cover, headers, TOC and section geometry. Only text that
is factually obsolete (66 tables, mandatory review, SELECT-only sandbox) is
replaced, plus the 67-table/28-migration counts.
"""
from __future__ import annotations

import copy
import difflib
import re
from pathlib import Path

import docx
from docx.oxml.ns import qn
from docx.shared import Pt

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/submission/final/C1SE.70_ArchitectureDesign_DBCAS_ver1.3.docx"
REF = ROOT.parent / "Documents/Final-ver1.3/C1SE.70_ArchitectureDesign_DBCAS_ver1.3.docx"
TERMS = ["66 tables", "66-table", "mandatory", "every submission", "reviews every",
         "select only", "select-only", "read-only transaction", "mandatory ai-then"]


def paragraph_text(p):
    return p.text.strip()


def set_paragraph_text(p, text):
    if p.text.strip() == text.strip():
        return False
    first = next((r for r in p.runs if r.text), None)
    for r in p.runs:
        r.text = ""
    if first is not None:
        first.text = text
    else:
        p.add_run(text)
    return True


def main():
    base = docx.Document(str(BASE))
    ref = docx.Document(str(REF))
    changed_paras = 0
    changed_cells = 0

    # 1) tables: same structure except revision history (index 3)
    for ti, (bt, rt) in enumerate(zip(base.tables, ref.tables)):
        if ti == 3:
            continue
        if len(bt.rows) != len(rt.rows):
            continue
        for btr, rtr in zip(bt._tbl.tr_lst, rt._tbl.tr_lst):
            for btc, rtc in zip(btr.tc_lst, rtr.tc_lst):
                btext = "".join(t.text or "" for t in btc.iter(qn("w:t"))).strip()
                rtext = "".join(t.text or "" for t in rtc.iter(qn("w:t"))).strip()
                if btext != rtext:
                    btc.getparent().replace(btc, copy.deepcopy(rtc))
                    changed_cells += 1

    # 2) paragraphs: align by text and update only obsolete factual wording
    bp = [p for p in base.paragraphs if p.text.strip()]
    rp = [p for p in ref.paragraphs if p.text.strip()]
    sm = difflib.SequenceMatcher(None, [p.text.strip() for p in bp],
                                 [p.text.strip() for p in rp], autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "replace":
            continue
        for b, r in zip(bp[i1:i2], rp[j1:j2]):
            old = b.text.strip()
            if any(term in old.lower() for term in TERMS):
                if set_paragraph_text(b, r.text.strip()):
                    changed_paras += 1

    # 3) explicit 67-table / 28-migration sentence
    for p in base.paragraphs:
        t = p.text
        if "PostgreSQL 17 database (66 tables)" in t:
            set_paragraph_text(p, t.replace(
                "PostgreSQL 17 database (66 tables)",
                "PostgreSQL 17 database (67 tables, 561 columns, 122 foreign keys, 159 indexes, 28 migrations)"))
            changed_paras += 1

    # 4) Table 54 title and 41-core note
    for p in base.paragraphs:
        if p.text.strip() == "Table . Details about ERD tables":
            set_paragraph_text(p, "Table 54. Details about the 41 core ERD tables")
            changed_paras += 1
        elif p.text.strip() == "The conceptual model in Figure 7 is implemented physically by the core tables shown in Figure 8. The many-to-many relationships (assigned, maps to, tagged with, targets) are realized by the junction tables AccountRole, CLOConcept, QuestionConcept and the legacy AssessmentConcept; all 67 tables are described in Table 54.":
            set_paragraph_text(p, "The conceptual model in Figure 7 is implemented physically by the core tables shown in Figure 8. The many-to-many relationships (assigned, maps to, tagged with, targets) are realized by the junction tables AccountRole, CLOConcept, QuestionConcept and the legacy AssessmentConcept; the 41 core tables are described in Table 54 and the 26 tables added by migrations 020–028 are described in Appendix A of the Database Design document.")
            changed_paras += 1

    # 5) Mode 1/2 and provider sentence
    for p in base.paragraphs:
        if p.text.startswith("All persistent data is stored in a PostgreSQL 17 database"):
            if "OpenAI-compatible endpoint" not in p.text:
                p.add_run(" The LLM Provider is an OpenAI-compatible endpoint configured through environment variables; no model weights are hosted.")
                changed_paras += 1
            break
    for t in base.tables:
        for row in t.rows:
            if any("Take a Personalized Practice Session" in c.text for c in row.cells):
                cell = row.cells[1] if len(row.cells) > 1 else row.cells[0]
                if "Mode 1" not in cell.text:
                    para = cell.add_paragraph("Two source modes: Mode 1 uses the reviewed bank; Mode 2 uses live AI questions for one concept and one starting band, with SQL and fallback still bank-only; the Free demo hides Mode 2.")
                    for run in para.runs:
                        run.font.name = "Times New Roman"
                        run.font.size = Pt(9)
                    changed_cells += 1
                break
        else:
            continue
        break

    base.save(str(BASE))
    print(f"changed paragraphs={changed_paras}, table cells={changed_cells}")


if __name__ == "__main__":
    main()
