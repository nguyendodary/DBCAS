# -*- coding: utf-8 -*-
"""W6 independent checks: language, TOC/TOF consistency, cross-document claims."""
import json
import re
import sys
import zipfile
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[4]
ACA = ROOT / "docs/academic"
FILES = [
    ("Proposal", "C1SE.70_ProposalDocument_DBCAS_ver1.2.docx"),
    ("Architecture Design", "C1SE.70_ArchitectureDesign_DBCAS_ver1.2.docx"),
    ("Database Design", "C1SE.70_DatabaseDesign_DBCAS_ver1.2.docx"),
]
VI = set("ăâđêôơưĂÂĐÊÔƠƯạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ"
         "ẠẢẤẦẨẪẬẮẰẲẴẶẸẺẼẾỀỂỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪỬỮỰỲỴỶỸ")


def text_of(p):
    return "".join(n.text or "" for n in p._p.iter(qn("w:t")))


def norm(t):
    return re.sub(r"\s+", " ", t or "").strip()


def toc_entries(doc):
    toc, lof, lot = [], [], []
    current = None
    for p in doc.paragraphs:
        style = (p.style.name or "").lower()
        t = norm(text_of(p))
        if style.startswith("toc"):
            if t:
                toc.append((style, t))
        elif style == "table of figures":
            if "list of tables" in t.lower():
                current = lot
            elif "list of figures" in t.lower():
                current = lof
            elif t and current is not None:
                current.append(t)
    return toc, lof, lot


def headings(doc):
    return [(p.style.name, norm(text_of(p))) for p in doc.paragraphs
            if (p.style.name or "").startswith("Heading") and norm(text_of(p))]


def captions(doc):
    figs, tables = [], []
    for p in doc.paragraphs:
        t = norm(text_of(p))
        if p.style and p.style.name == "Caption" and t:
            if re.match(r"^Figure\b", t, re.I):
                figs.append(t)
            elif re.match(r"^Table\b", t, re.I):
                tables.append(t)
    return figs, tables


def body_text(doc):
    chunks = [text_of(p) for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                chunks.extend(text_of(p) for p in cell.paragraphs)
    return "\n".join(chunks)


def strip_toc_number(t):
    return re.sub(r"\s*\d+\s*$", "", t).strip()


def main():
    report = {}
    all_text = {}
    for name, fn in FILES:
        doc = Document(str(ACA / fn))
        toc, lof, lot = toc_entries(doc)
        hs = headings(doc)
        figs, tabs = captions(doc)

        # Vietnamese scan: full body + tables + headers/footers
        body = body_text(doc)
        with zipfile.ZipFile(ACA / fn) as z:
            for part in z.namelist():
                if (part.startswith("word/header") or part.startswith("word/footer")) and part.endswith(".xml"):
                    body += "\n" + z.read(part).decode("utf-8", "ignore")
        vi_hits = sorted({ch for ch in body if ch in VI})
        vi_paras = [norm(text_of(p)) for p in doc.paragraphs
                    if any(ch in VI for ch in text_of(p))]

        # TOC coverage: heading text appears in TOC (allow trailing page number)
        toc_wo = [strip_toc_number(t) for _, t in toc]
        missing_toc = []
        for style, h in hs:
            if style == "Heading 1" and h not in toc_wo:
                missing_toc.append(h)
        extra_toc = [t for t in toc_wo if t not in {h for _, h in hs}]

        # TOF/table list coverage
        fig_missing = [f for f in figs if strip_toc_number(f) not in [strip_toc_number(x) for x in lof]]
        tab_missing = [t for t in tabs if strip_toc_number(t) not in [strip_toc_number(x) for x in lot]]
        fig_extra = [x for x in lof if strip_toc_number(x) not in [strip_toc_number(f) for f in figs]]
        tab_extra = [x for x in lot if strip_toc_number(x) not in [strip_toc_number(t) for t in tabs]]

        report[name] = {
            "paragraphs": len(doc.paragraphs), "tables": len(doc.tables),
            "headings": len(hs), "toc_entries": len(toc), "list_of_figures": len(lof),
            "list_of_tables": len(lot), "figure_captions": len(figs),
            "table_captions": len(tabs), "vietnamese_chars": vi_hits,
            "vietnamese_paragraphs": len(vi_paras),
            "missing_toc_headings": missing_toc, "extra_toc_entries": extra_toc,
            "missing_figure_entries": fig_missing, "missing_table_entries": tab_missing,
            "extra_figure_entries": len(fig_extra), "extra_table_entries": len(tab_extra),
        }
        all_text[name] = body
        print(json.dumps({name: report[name]}, ensure_ascii=False, indent=1))

    # cross-document claims
    claims = {
        "DBCAS": ["DBCAS"],
        "Duy Tan University": ["Duy Tan University"],
        "PostgreSQL 17": ["PostgreSQL 17"],
        "FastAPI": ["FastAPI"],
        "Python 3.13": ["Python 3.13"],
        "41 tables": ["41 tables"],
        "Google": ["Google"],
        "GitHub": ["GitHub"],
        "Learner": ["Learner"],
        "Administrator": ["Administrator"],
        "mandatory review/approval": ["administrator review", "review and approval", "review and approve", "approve"],
    }
    cross = {}
    for name, text in all_text.items():
        cross[name] = {k: sum(len(re.findall(re.escape(v), text, re.I)) for v in vals)
                       for k, vals in claims.items()}
    report["_cross_document"] = cross
    (Path(__file__).resolve().parent / "independent-checks.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
