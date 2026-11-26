# Exact-name baseline duplicates — 2026-11-26

"""
Owner-designated names:
1. `C1SE.70_ProposalDocument_DBCAS_ver1.4.docx`
2. `C1SE.70_ArchitectureDesign_DBCAS_ver1.2.docx`
3. `C1SE.70_DatabaseDesign_DBCAS_ver1.3.docx`
4. `C1SE.56_CodeStandard_SHFA_ver2.0.docx`
5. `C1SE.56_FitnessAI_FNAI_ver2.0.docx`

Read-only inventory. Identical content is grouped by SHA-256. Pages are the
cached Word `docProps/app.xml` count; cover version is the first `Version X`
string on the cover. No file was modified, copied or deleted.
"""
from __future__ import annotations

import hashlib
import re
import zipfile
from collections import defaultdict
from pathlib import Path

import docx
from docx.oxml.ns import qn

WS = Path(r"C:\Users\kudot\Downloads\proposal test")
NAMES = [
    "C1SE.70_ProposalDocument_DBCAS_ver1.4.docx",
    "C1SE.70_ArchitectureDesign_DBCAS_ver1.2.docx",
    "C1SE.70_DatabaseDesign_DBCAS_ver1.3.docx",
    "C1SE.56_CodeStandard_SHFA_ver2.0.docx",
    "C1SE.56_FitnessAI_FNAI_ver2.0.docx",
]
OUT = WS / "DBCAS/docs/agent/freeze-logs/baseline-duplicates-20261126.md"


def rel(p: Path):
    return str(p.relative_to(WS))


def props(p: Path):
    pages = words = None
    try:
        with zipfile.ZipFile(p) as z:
            if "docProps/app.xml" in z.namelist():
                s = z.read("docProps/app.xml").decode("utf-8", "ignore")
                m = re.search(r"<Pages>(\d+)</Pages>", s)
                pages = int(m.group(1)) if m else None
                m = re.search(r"<Words>(\d+)</Words>", s)
                words = int(m.group(1)) if m else None
    except Exception:
        pass
    return pages, words


def cover_version(p: Path):
    try:
        d = docx.Document(str(p))
    except Exception:
        return ""
    text = "\n".join(x.text for x in d.paragraphs[:80])
    m = re.search(r"Version\s+([0-9]+(?:\.[0-9]+)*)", text)
    return m.group(0) if m else ""


def toc3(p: Path):
    try:
        d = docx.Document(str(p))
    except Exception:
        return []
    out = []
    for para in d.element.body.iter(qn("w:p")):
        pPr = para.find(qn("w:pPr"))
        if pPr is None:
            continue
        ps = pPr.find(qn("w:pStyle"))
        if ps is None:
            continue
        st = (ps.get(qn("w:val")) or "").lower()
        if not re.match(r"toc[1-9]", st):
            continue
        text = "".join(x.text or "" for x in para.iter(qn("w:t"))).strip()
        if text:
            out.append(text)
        if len(out) == 3:
            break
    return out


def main():
    lines = ["# Exact-name baseline duplicates", "",
             "Read-only. Identical content grouped by SHA-256.", ""]
    for name in NAMES:
        paths = sorted(WS.rglob(name), key=lambda p: (p.stat().st_mtime, rel(p)))
        paths = [p for p in paths if p.is_file()]
        groups = defaultdict(list)
        for p in paths:
            try:
                h = hashlib.sha256(p.read_bytes()).hexdigest()
            except Exception:
                h = f"ERR:{p}"
            groups[h].append(p)
        lines += [f"## {name}", "",
                  f"Found **{len(paths)}** copies, **{len(groups)}** distinct contents.", "",
                  "| Hash | Copies | Modified | Pages | Words | Cover version | TOC 1–3 | Representative / all paths |",
                  "|---|---:|---|---:|---:|---|---|---|"]
        for h, ps in sorted(groups.items(), key=lambda kv: (-len(kv[1]), rel(kv[1][0]))):
            rep = ps[0]
            pages, words = props(rep)
            toc = " / ".join(toc3(rep)) or "no TOC"
            allp = "<br>".join(f"`{rel(x)}`" for x in ps)
            lines.append(
                f"| `{h[:16]}` | {len(ps)} | {rep.stat().st_mtime:.0f} | "
                f"{pages if pages is not None else 'n/a'} | {words if words is not None else 'n/a'} | "
                f"{cover_version(rep) or 'n/a'} | {toc[:120]} | {allp[:700]} |")
        lines.append("")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
