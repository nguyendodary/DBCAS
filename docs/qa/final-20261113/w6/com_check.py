# -*- coding: utf-8 -*-
"""Word COM field/list check on temporary copies; never saves the source."""
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
ACA = ROOT / "docs/academic"
FILES = [
    ("proposal", "C1SE.70_ProposalDocument_DBCAS_ver1.2.docx"),
    ("architecture", "C1SE.70_ArchitectureDesign_DBCAS_ver1.2.docx"),
    ("database", "C1SE.70_DatabaseDesign_DBCAS_ver1.2.docx"),
]
OUT = Path(__file__).resolve().parent


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    import win32com.client
    tmp = Path(tempfile.gettempdir()) / "dbc-w6-com"
    tmp.mkdir(parents=True, exist_ok=True)
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    result = {"word": word.Version, "documents": {}}
    try:
        for slug, name in FILES:
            src = ACA / name
            before = sha(src)
            copy = tmp / f"{slug}.docx"
            shutil.copyfile(src, copy)
            try:
                d = word.Documents.Open(str(copy), ConfirmConversions=False,
                                        ReadOnly=False, AddToRecentFiles=False)
                pages0 = d.ComputeStatistics(2)  # wdStatisticPages
                fields = d.Fields.Count
                toc_count = d.TablesOfContents.Count
                tof_count = d.TablesOfFigures.Count
                opening = {"pages": pages0, "fields": fields,
                           "tocs": toc_count, "tofs": tof_count}
                d.Fields.Update()
                for i in range(1, toc_count + 1):
                    d.TablesOfContents(i).Update()
                tof_rows = []
                for i in range(1, tof_count + 1):
                    tof = d.TablesOfFigures(i)
                    d.TablesOfFigures(i).Update()
                    text = tof.Range.Text
                    paras = [p.strip() for p in text.replace("\r", "\n").split("\n") if p.strip()]
                    tof_rows.append({"caption": getattr(tof, "Caption", ""),
                                     "entries": len(paras),
                                     "first": paras[0] if paras else "",
                                     "last": paras[-1] if paras else ""})
                d.Repaginate()
                pages1 = d.ComputeStatistics(2)
                toc_range = d.TablesOfContents(1).Range.Text
                toc_paras = [p.strip() for p in toc_range.replace("\r", "\n").split("\n") if p.strip()]
                result["documents"][slug] = {
                    "file": name, "sha256_before": before, "sha256_after": sha(src),
                    "opened_without_repair": True, "opening": opening,
                    "pages_after_update": pages1,
                    "toc_entries": len(toc_paras), "toc_first": toc_paras[:2],
                    "toc_last": toc_paras[-2:], "tof": tof_rows,
                }
                d.Close(0)
            except Exception as exc:  # noqa: BLE001
                result["documents"][slug] = {"file": name, "error": f"{type(exc).__name__}: {exc}",
                                             "sha256_before": before, "sha256_after": sha(src)}
    finally:
        try:
            word.Quit()
        except Exception:
            pass
    (OUT / "word-com.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    for slug, row in result["documents"].items():
        print(slug, json.dumps(row, ensure_ascii=False)[:500])


if __name__ == "__main__":
    main()
