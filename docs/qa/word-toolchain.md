# Word-inspection toolchain (2026-11-08)

Local machine: Windows, branch `develop2`. No application code or `.docx`
content was changed while building this toolchain.

## Installed / detected

| Tool | Purpose | Version | Status |
| --- | --- | --- | --- |
| Python (backend venv) | application + existing helpers | 3.14.5 | already present |
| Python (tools venv) | docx/Word toolchain | 3.14.5 | installed at `tools/.venv` |
| pip (tools venv) | packages | 26.1.1 | installed |
| Node / npm | runner scripts | 24.16.0 / 11.13.0 | already present |
| Microsoft Word (COM) | open check, field/TOC update, page count | 16.0 build 16.0.20527 | already registered |
| LibreOffice | headless DOCX → PDF | 26.2.7.3 | installed as an extracted admin MSI under `%LOCALAPPDATA%\DBCAS-tools\LibreOffice` (workaround, see below) |
| Graphviz `dot` | DOT smoke test / diagram rendering | 16.1.0 | installed as portable ZIP under `%LOCALAPPDATA%\DBCAS-tools\Graphviz-16.1.0` |
| Pandoc | optional text cross-check | — | **not installed** (not required; skipped) |
| Poppler | PDF pages | — | **not installed** (PyMuPDF used instead) |
| MuPDF (via PyMuPDF) | PDF pages/PNG | 1.28.6 engine (PyMuPDF 2.1) | installed in tools venv |
| python-docx | readable DOCX API | 1.2.0 | installed (pinned) |
| docx2python | structured extraction | 3.7.2 | installed (pinned) |
| pywin32 | Word COM | 312 | installed (pinned) |
| lxml | direct OOXML | 6.1.3 | installed (pinned) |
| PyMuPDF | PDF render/measure | 2.1 | installed (pinned) |
| Pillow | page/contact images | 13.0.0 | installed (pinned) |

Pinned requirements: `scripts/requirements-docs.txt`.

### Installation notes / workarounds

- The LibreOffice MSI cannot be installed by the current non-elevated user
  (`msiexec` exits 1603; the log says “user without sufficient administrator
  rights”). An administrative extraction works and runs headless:
  `msiexec /a libreoffice.msi /qn TARGETDIR=%LOCALAPPDATA%\DBCAS-tools\LibreOffice`.
  For a normal machine-wide install the owner may run, elevated:
  `msiexec /i "%TEMP%\libreoffice.msi" /qn /norestore ALLUSERS=1`.
- Graphviz was extracted from the official 16.1.0 64-bit ZIP to avoid an
  elevation prompt. Optional machine install: `winget install Graphviz.Graphviz`.
- The LibreOffice bundled `soffice.exe` does not print `--version` to this
  console; `soffice.com` reports `LibreOffice 26.2.7.3`.
- Word's PDF export is known to hang machine-wide and is **not** used. Word is
  used only to open (a short temp copy), update fields in memory, and read the
  page count without saving.
- docx2python 3.7.2 pulled `pymupdf4llm`, `pymupdf-layout`, `onnxruntime`,
  `numpy` and `networkx` as transitive dependencies; they are not used by the
  verifier.

## Smoke test (end to end)

Source used: `C1SE.70_ProposalDocument_DBCAS_ver1.1.docx` copied to a short
temporary path (`%TEMP%\dbcw\proposal.docx`).

| Step | Result |
| --- | --- |
| python-docx open | 224 paragraphs, 21 tables, 5 inline images, 2 sections |
| docx2python extract | 43 body blocks, 978 paragraphs in tables |
| LibreOffice → PDF | exit 0, 60 pages |
| PyMuPDF page 1 → PNG | `docs/qa/word-verification/smoke-page1.png`, 94,349 bytes |
| Word COM read-only open | Word 16.0, 60 pages, 10,488 words |
| Graphviz trivial DOT → PNG | exit 0, 3,235-byte PNG |

No tool failed. The only unavailable optional tools are Pandoc and Poppler,
which are not needed for this task.

## Commands

```powershell
# recreate the Python toolchain
python -m venv tools\.venv
tools\.venv\Scripts\python -m pip install -r scripts\requirements-docs.txt

# smoke evidence in this file was produced with the same paths the verifier uses
npm run docs:verify-word
```

## Verification entry point

```powershell
npm run docs:verify-word                  # local: Word COM + LibreOffice page evidence
npm run docs:verify-word -- --ci --no-pdf # CI-safe: stdlib OOXML checks only
```

Outputs:

- `docs/qa/word-verification/summary.md` (one-page table)
- `docs/qa/word-verification/<document>/report.md`
- `docs/qa/word-verification/<document>/diagrams/fig-XX-before.png`,
  `fig-XX-after.png` and `contact-before-after.png`

The verifier opens a short temporary copy for Word and never saves it; it also
checks the SHA-256 of each source package before and after the run. The
existing `scripts/verify_docx.py` is invoked as a subprocess and its result is
included in every report; `scripts/check_docs.py` / `diagrams:check` remain
under `npm run docs:check`.
