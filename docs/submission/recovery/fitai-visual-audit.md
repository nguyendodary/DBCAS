# FITAI visual design language - independent read-only audit

**Date:** 2026-11-25  
**Workspace:** `C:\Users\kudot\Downloads\proposal test`  
**Scope:** all 14 FITAI DOCX files and their PDF exports under `FITAI - Documents\`.  
**Method:** DOCX parts were copied read-only with System.IO.Compression.ZipFile into `C:\Users\kudot\AppData\Local\Temp\opencode\fitai-audit\<short-name>\`; XML was parsed from those copies. Embedded media were viewed with the `read` tool. The `read` tool cannot decode PDF for this model, so PDFs were rendered page-by-page with LibreOffice Draw (read-only source, output only to temp) and the PNGs viewed with `read`. No source document was modified.  

**Evidence notation.** `proposal/word/styles.xml` means the extracted copy of `1. Proposal Document\C1SE.56_ProposalDocument_SHFA_ver1.2.docx`. Short names: `proposal`, `arch`, `db`, `code`, `plan`, `backlog`, `testplan`, `tech`, `stories`, `ui`, `sprint`, `meeting`, `reflection`, `ai`. Twips to cm: value * 2.54 / 1440. `w:sz` half-points to pt: value / 2. Border `w:sz` eighths of a point: 4 = 0.5 pt, 6 = 0.75 pt, 8 = 1 pt.

---

## 1. Colour palette

### 1.1 Theme matrices (exact XML values)

Every theme contains `clrScheme name="Office"` at `word/theme/theme1.xml:/a:theme/a:themeElements/a:clrScheme`. `dk1`/`lt1` are `sysClr` (`windowText`/`window`); others are `srgbClr`.

| Slot | proposal, arch, plan, backlog, stories, ui, ai (7 files) | db | code | tech, testplan |
|---|---|---|---|---|
| dk1 | `lastClr="000000"` | `000000` | `000000` | `000000` |
| lt1 | `lastClr="FFFFFF"` | `FFFFFF` | `FFFFFF` | `FFFFFF` |
| dk2 | `#44546A` | `#44546A` | `#0E2841` | `#1F497D` |
| lt2 | `#E7E6E6` | `#E7E6E6` | `#E8E8E8` | `#EEECE1` |
| accent1 | `#4472C4` | **`#5B9BD5`** | `#156082` | `#4F81BD` |
| accent2 | `#ED7D31` | `#ED7D31` | `#E97132` | `#C0504D` |
| accent3 | `#A5A5A5` | `#A5A5A5` | `#196B24` | `#9BBB59` |
| accent4 | `#FFC000` | `#FFC000` | `#0F9ED5` | `#8064A2` |
| accent5 | `#5B9BD5` | **`#4472C4`** | `#A02B93` | `#4BACC6` |
| accent6 | `#70AD47` | `#70AD47` | `#4EA72E` | `#F79646` |
| hlink | `#0563C1` | `#0563C1` | `#467886` | `#0000FF` |
| folHlink | `#954F72` | `#954F72` | `#96607D` | `#800080` |

Font scheme: major/minor = Calibri Light/Calibri in proposal, arch, db, plan, backlog, stories, ui; Aptos Display/Aptos in code; Calibri/Cambria in tech/testplan. The Database file swaps accent1 and accent5 relative to Office default (`db/word/theme/theme1.xml:/a:clrScheme/a:accent1/a:srgbClr@val = 5B9BD5`). Code Standard and TechStack/TestPlan use entirely different themes.

### 1.2 Direct colours actually used (frequency in `word/document.xml`)

| File | Direct text/line colours | Shading fills | Border colours |
|---|---|---|---|
| arch | `000000` x1040, `201F35` x2, `4472C4` x4 | `FFFFFF` 41, `E7E6E6` 32, `D9D9D9` 18, `D0CECE` 16, `F3F3F3` 4, `BFBFBF` 1 | `000000` x1410, `8EAADB` x6 |
| db | `000000` x197, `00000A` x30, `4472C4` x2 | `BFBFBF` x113, `D9D9D9` x6 | `000000` x112, `666666` x64 |
| proposal | `000000` x204, `201F35` x2, `4472C4` x2 | `FFFFFF` 61, `D0CECE` 30, `AEAAAA` 6, `BFBFBF` 4 | `000000` x570, `8EAADB` x6 |
| plan | `000000` x64, `00000A` x63 | `FFFFFF` 333, `BFBFBF` 26, `A6A6A6` 25, `D9D9D9` 12 | `000000` x2161, `00000A` x78 |
| code | `auto` x557 | `FFFFFF` 12, `D9D9D9` 5, `BFBFBF` 1 | `000000` x78 |
| tech | `auto` x673, `000000` x295, `695D46` x3, `4F81BD` x4 | `FFFFFF` 93, `D9D9D9` 38, `BFBFBF` 18, `8EAADB` 2 | `000000` x84 |
| testplan | `000000` x1821, `auto` x235, `695D46` x1, `4F81BD` x4 | `FFFFFF` 93, `D9D9D9` 38, `BFBFBF` 18, `A6A6A6` 6 | `000000` x309 |

Evidence: `arch/word/document.xml` cover runs have `w:color w:val="4472C4"` on "International School" (15 pt bold) and `000000` on other cover text; `db/word/document.xml://w:tbl//w:shd[@w:fill="BFBFBF"]` occurs 113 times; `//w:tblBorders/*[@w:color="666666" and @w:sz="4"]` occurs 64 times and `auto` 149 times.

### 1.3 Dominant scheme of Architecture and Database

Both are essentially **achromatic academic documents**: black Times New Roman on white, neutral gray table fills, hairline black borders; the Office theme is present but mostly unused in visible text.

* Architecture: `arch/word/styles.xml:/w:docDefaults/w:rPrDefault/w:rPr/w:sz=26` with Times New Roman; all 1040 direct colour runs are `000000`, only two `201F35` and four `4472C4`. Gray fills `E7E6E6/D9D9D9/D0CECE`. The only coloured style text is `/w:style[@w:styleId="Heading3"]/w:rPr/w:color@w:val=1F3863` (12 pt Calibri). PDF `arch_p10.png` and `arch_p33.png` confirm black text, gray frames, hairline diagrams, blue only as a narrow left rule on the ER page.
* Database: theme accent1 is `5B9BD5` but `db/word/document.xml` never uses it. Visible colour is `000000`/`auto`, `BFBFBF` table heads, `666666` borders and `44546A` only in the 9 pt Caption style (`db/word/styles.xml:/w:style[@w:styleId="Caption"]/w:rPr/w:color@w:val`), which body captions override. PDF `db_p15.png` confirms gray header bars, black hairline grid, black serif text.

---

## 2. Fonts (family / size / weight)

`w:sz` values are half-points. "Effective" includes style inheritance.

| Element | proposal | arch | db | code | plan / backlog | tech / testplan |
|---|---|---|---|---|---|---|
| Normal / body | TNR **12 pt** (`styles.xml:/...Normal/w:rPr/w:sz=24`); docDefaults TNR | TNR **13 pt** effective (`docDefaults...w:sz=26`; Normal has no own size) | TNR **13 pt** (`Normal...w:sz=26`); docDefaults theme minor 11 pt overridden | TNR **13 pt** effective (`docDefaults...sz=26`; Normal only `color=000000`) | TNR **13 pt** (`Normal...sz=26`, `szCs=24`) | defaults Open Sans **11 pt** brown `695D46` (`docDefaults...sz=22`), but direct runs are TNR **13 pt** black (tech 1007, testplan 2052 runs); PDFs `tech_p6.png`, `testpl_p7.png` confirm |
| Title | TNR **14 pt** bold centred (`Title...sz=28`) | TNR **14 pt** bold centred (`sz=28`) | **no Title style** | **36 pt** bold (`sz=72`) | 14 pt bold centred | PT Sans Narrow **24 pt** bold (`sz=48`) in styles; direct cover text still TNR 20/28 pt |
| Heading1 | TNR **13 pt** bold (`sz=26`; `szCs=32`) | TNR **13 pt** bold, no own `sz`, inherits 13 pt | TNR **13 pt** bold (`sz=26`) | TNR **13 pt** bold effective (no explicit `sz`) | 13 pt bold effective (`szCs=32` only) | PT Sans Narrow **18 pt** bold `FF5E0E` (`sz=36`) in style; PDF shows 13 pt TNR bold via direct overrides |
| Heading2 | TNR **13 pt** bold, Arial cs, `position=-1` | TNR **13 pt** bold | TNR **13 pt** bold | 13 pt bold effective | 13 pt bold effective (Arial cs, `position=-1`) | PT Sans Narrow **16 pt** `008575` (`sz=32`) in style |
| Heading3 | **absent** | Calibri **12 pt** `#1F3863` (`sz=24`) | **absent** | **14 pt** bold (`sz=28`) | 13 pt bold (plan) / 12 pt `1F3763` (backlog) | PT Sans Narrow **14 pt** bold (`sz=28`), indent 2160 tw |
| Caption | italic `sz=26` = **13 pt** plus `szCs=18` = 9 pt | italic `szCs=18` only, renders **13 pt**; direct captions: bold "Figure 1." + italic title | style italic `44546A` **9 pt** (`sz=18`), but all 21 body captions override to **13 pt** (`/w:pPr/w:rPr/w:sz=26`) | **absent** | plan/backlog 9 pt italic `44546A` | testplan 9 pt italic `1F497D`; tech absent |
| Table text | inherits 13 pt; 571 direct 13 pt runs | inherits 13 pt; 6 direct 12 pt runs | inherits 13 pt; no direct table `sz` | inherits 13 pt | inherits 13 pt | inherits 13 pt (174/1182 direct 13 pt runs) |
| Header/footer | 13 pt (`szCs=26`) bold italic footer; 13 pt italic bold header | 11-13 pt bold italic | header Calibri 11 pt (`sz=22`) + bold italic 12 pt (`sz=24`); footer `szCs=26` | footer 11 pt (`sz=22`) | 13 pt bold italic | 11 pt brown italic |
| Monospace | none | none | none | **HTML Preformatted**: Courier New **10 pt**, tab stops every 916 tw, single spacing (`code/word/styles.xml:/w:style[@w:styleId="HTMLPreformatted"]/w:rPr`); **unused** | none | none |

**Hierarchy:** the mainstream family deliberately has **no size step** between body and H1/H2 (both 13 pt); distinction is bold plus numbering plus spacing/indent. Only Architecture H3 introduces a smaller 12 pt and a different family/colour. Tech/TestPlan have 18/16/14 pt heading styles, but direct TNR 13 pt runs dominate the rendered body.

---

## 3. Heading hierarchy, numbering and TOC

* **Architecture** (`arch/word/styles.xml`): Title plus Heading1/2/3/4/5/6, each with `w:outlineLvl` 0...5. H1/H2/H3 are `basedOn=Normal`; H3 is Calibri 12 pt `#1F3863`. Direct heading paragraphs carry `w:numPr` with `numId=17`; H1 ilvl 0 (9 paragraphs), H2 ilvl 1 (11). `arch/word/numbering.xml:/w:num[@w:numId="17"]` maps to abstractNum 11: `ilvl0 numFmt=decimal lvlText="%1." indent 440/440`, `ilvl1 decimal "%1.%2." indent 440/80`, `ilvl2 lowerLetter "%3."`. PDF `arch_p6.png` renders "1." and "1.1." exactly.
* **Proposal**: Heading1/2 only, `outlineLvl` 0/1, style-based `numId=1` mapping to abstract 4 (`%1.`, `%1.%2.`, `lowerRoman %3.`). No Heading3 style. Direct paragraphs have no `numPr`.
* **Database**: Heading1/2 only (no Heading3, no Title), both `sz=26` bold with `numId=2` in the style (abstract 1: `%1.`/`%1.%2.`, lowerRoman `%3`), but body paragraphs override with `numId=0`, `7`, `16`, `17`, `18`, `19` or none - numbering is inconsistent across sections (e.g. "2.2. Entity Relationship Diagram" in the TOC vs plain "Introduction" in the body).
* **Code Standard**: Title 36 pt, Heading1/2 body-size bold with `outlineLvl`, Heading3 14 pt; no Caption.
* **TOC field codes** from `word/document.xml://w:instrText`:
  * arch: three `TOC` fields - `TOC \h \u \z \t "Heading 1,1,Heading 2,2,Heading 3,3,"` plus a six-level variant twice. Cached entries are literal `w:hyperlink w:anchor="_heading=..."` paragraphs inside `w:sdt/w:sdtContent`, with `<w:tab/>` and literal page numbers; they are **not** styled with TOC1/TOC2 (0 `pStyle=TOCn` paragraphs although those styles exist). PDF `arch_p6.png` shows the cached entries (pages 9-33).
  * proposal: `TOC \o "1-4" \h \z \u`, plus `TOC \h \z \c "Table"` and `\c "Figure"`, 16 TOC1 + 11 TOC2 cached paragraphs, `SEQ Table` x7, `SEQ Figure` x3.
  * db: `TOC \o "1-2" \h \z \u` plus `\c "Figure"` x2 and `\c "Table"`; 4 TOC1 + 23 TOC2 cached paragraphs; `SEQ Table` x14, `SEQ Figure` x1.
  * code: `TOC \h \u \z \t "Heading 1,1,Heading 2,2,"`, 1 TOC1 + 19 TOC2 cached entries.
  * plan/backlog/stories/ui/testplan/tech use `TOC \o "1-3" \h \z \u` (and table/figure list fields where relevant).
  * `settings.xml` has **no** `w:updateFields` in any of the 14 files; TOCs display cached text until manually updated.
* `w:sectPr/w:titlePg` is true on cover sections (arch, proposal, db, plan, etc.), producing empty first-page headers/footers in several files.

## 4. Paragraph spacing, line spacing, indentation, justification

From `word/styles.xml` and direct `word/document.xml` `w:spacing`, `w:ind`, `w:jc`; line values: 240 = single, 259 about 1.08, 276 = 1.15, 360 = 1.5.

| File | Body line / after / indent / jc | Heading1 | Heading2 |
|---|---|---|---|
| proposal | direct `line=360` on 178 paragraphs; `jc=both` 44, `center` 32; Normal 12 pt, no spacing | `before=240`, no after | `before=360, after=120, line=276`, `ind left=1080 hanging=1`, `textDirection=btLr` |
| arch | direct `line=360` 93, `line=276` 26; `jc=center` 70, `both` 27; `after=200` 29, `after=120` 24 | `before=240`, `ind left=440 hanging=440` | `before=360, after=120, line=276`, `ind left=80 hanging=80` |
| db | Normal: `after=127`, `ind left=10 hanging=10`, `jc=both`; docDefaults `after=160, line=259`; direct `line=360` 98, `after=0` 43 | `after=128`, `ind right=3604` | `after=128`, `ind left=283 right=3604` |
| code | docDefaults `line=360`, `ind firstLine=567`; direct `jc=both` 58, `ind firstLine=0` 64 | `line=259`, `ind hanging=10` | `line=259`, `ind hanging=10` |
| plan | direct `line=360` 73, `jc=both` 30, `center` 19 | `before=240`, `ind left=440` | `before=360, after=120, line=276`, `ind left=80`, `btLr` |
| testplan | docDefaults `line=360`, `ind left=357 firstLine=567`; `jc` rarely set (8 left, 9 center) | `line=312`, `ind left=450` | `before=200`, `ind left=1080 hanging=90` |
| tech | docDefaults `line=360`, `ind left=357 firstLine=567`, brown text | `line=312`, `ind left=450` | `before=200`, `ind left=1080 hanging=90` |

Figure/caption spacing: `arch/word/styles.xml:/w:style[@w:styleId="figure"]` = before 240, after 240, line 360, centred italic; direct caption paragraphs use the same values (`arch/word/document.xml` paragraph containing "Figure 1. Usecase Diagram"). `db` Caption style: after 200, line 240, no `jc` (body captions add `jc=center` directly). Proposal Caption: after 200, centred.

---

## 5. Page geometry (exact twips and cm)

From `word/document.xml://w:sectPr/w:pgSz` and `/w:pgMar`; all `gutter=0`.

| File (DOCX) | Sections | Portrait size | Margins L / R / T / B (twips) | Header / Footer distance |
|---|---|---|---|---|
| arch | 8 (3 landscape) | 11907 x 16840 tw = **21.003 x 29.704 cm** | 1701 / 1134 / 1134 / 1418 tw = **3.00 / 2.00 / 2.00 / 2.50 cm** | 720 / 720 tw = 1.27 cm |
| arch landscape (sections 3, 5, 7) | 3 | 16840 x 11907 tw = **29.704 x 21.003 cm**, `orient=landscape` | 1418 / 1134 / 1701 / 1134 tw = 2.50 / 2.00 / 3.00 / 2.00 cm | 720 / 720 tw; **no header/footer references** |
| proposal | 3 | 11907 x 16840 tw | cover 1701 / 1134 / 1134 / 1418; body sections 2-3: 1620 / 1134 / 906 / 1418 = 2.86 / 2.00 / 1.60 / 2.50 cm | 720 / 720 |
| db | 9 (1 landscape) | cover 11920 x 16860 tw = 21.026 x 29.739 cm, L=1985 (3.50 cm), T/B=1701 (3.00 cm); body 11906 x 16838 tw = 21.001 x 29.700 cm, 1440 tw all round (2.54 cm) | as listed | cover 720/720; body variants 510/454, 680/283, 720/720, 720/613 |
| db landscape (section 8) | 1 | **23811 x 16838 tw = 42.00 x 29.70 cm** (A3 width), `orient=landscape` | 1440 / 1440 / 1440 / 862 tw = 2.54 / 2.54 / 2.54 / 1.52 cm | 720 / 1229 tw |
| code | 5 | cover 11920 x 16860; body 11904 x 16840 tw = 20.997 x 29.704 cm | cover 1985 / 1134 / 1701 / 1701; body 1440 all | cover 720/720; body header **164 tw = 0.29 cm**, footer 720 |
| plan / backlog / stories | 2 each | 11907 x 16840 tw | 1701 / 1134 / 1134 / 1418 tw (3/2/2/2.5 cm) | plan 288/720, backlog 288/720, stories 720/720 |
| ui | 2 | 11907 x 16840 tw | 1699 / 1138 / 1138 / 1411 tw = 2.998 / 2.008 / 2.008 / 2.490 cm | 720 / 720 |
| tech / testplan | 4 each | **12240 x 15840 tw = US Letter 21.59 x 27.94 cm** | 1440 all (2.54 cm) | 720 / 720 |
| sprint | 5 | 16838 x 11906 tw = **29.70 x 21.00 cm landscape**, all sections | 1440 all | variants 720/720, 58/720, 1123/720 |

`arch` is the only required reference with true A4 portrait plus regular landscape A4 inserts; `db` uses a 42 cm-wide landscape page for the schema figure (`db/word/media/image5.png`, 35.03 x 21.85 cm).

## 6. Header and footer conventions

Evidence: `word/header*.xml`, `word/footer*.xml`, `word/document.xml://w:sectPr/w:headerReference|w:footerReference`.

| File | Header text (exact) | Header construction | Footer text / fields |
|---|---|---|---|
| arch | "Architecture Design" | 1-row, 2-cell table, grid cols 4607 + 4607 tw; bold+italic 13 pt black runs; a separate shape with `wp:extent cx=1108075 cy=198120` in the header; **no rule in header** | `footer1.xml` empty (title page); `footer2.xml` SDT with `C1SE.56`, `Page ` and `PAGE` field (cached **35**), `w:pBdr` top/left/right `single sz=4 space=1/4 color=auto` - a **0.5 pt** box rule |
| proposal | "Proposal Document" | same 2-cell table (`gridCols=4607,4607`), second cell "International School Capstone 1 - 2025", bold italic 13 pt | `footer4.xml` `C1SE.56` + `Page` + `PAGE` (cached 6) + 0.5 pt box rule; other footers empty |
| db | "DATABASE DESIGN" + "International School Capstone 1 - 2024" or "- 2025" (13 header parts, mixed years), some repeat the title twice | paragraph with Calibri 11 pt (`sz=22`) and bold italic 12 pt (`sz=24`) runs, rule from a 7356474 x 227330 EMU (20.44 x 0.63 cm) shape | 13 footers: `Page | 2`; `Page 14 of 14` (`PAGE \* MERGEFORMAT`); `Page 2 of 2` (`PAGE;NUMPAGES`); `C1SE.56Page 10/11/21` with 0.5 pt box rule |
| code | "Code Standards v1.0 - PRH", "CODE  STANDARD  International School Capstone 1 - 2025" | rule image 5999988 x 6096 EMU (16.67 x 0.017 cm) | `C1SE.03  Page 10` (**stale project code**) with `PAGE`; other footers include `C1SE.56Page 2` with 0.5 pt rule |
| plan / backlog / stories / ui / tech / testplan / meeting / reflection / ai / sprint | e.g. "Project Plan", "User Story", "TECHNOLOGIES STACK", "TEST PLAN", "MEETING MINUTES", "REFLECTION" | mostly 2-cell or plain italic bold text; sprint `header3.xml` has "Page  of 22" (`PAGE;NUMPAGES`) in the **header** | plain `C1SE.56Page N` + `PAGE` with 0.5 pt box rule; `Page | 2` variants without rule |

* `PAGE` exists in **all 14** DOCX header/footer parts; `NUMPAGES` exists only in `db/word/footer4.xml` and `sprint/word/header3.xml`.
* Stale content: `code/word/footer3.xml` has `C1SE.03`; `db/word/header2,4,5,7,10,11,13.xml` say `2024` while other DB headers say `2025`; `reflection/word/header3.xml` says `DATABASE DESIGN`; `testplan/word/header1.xml` says `Proposal Document` twice. Cached page numbers (arch 35, proposal 6, db 21) are field results, not live values.
* PDF check: `arch_p2.png`, `arch_p10.png`, `db_p9.png`, `tech_p3.png`, `code_p3.png` all show the dark rectangular block at left, bold-italic header text, a thin horizontal rule, and the footer box with `C1SE.56` left / `Page N` right.

---

## 7. Cover pages and front matter

### Family A - stacked text cover (proposal, plan, backlog, stories, ui)

Evidence: `proposal/word/document.xml://w:body/w:p[1..25]`, PDF `proposal_p1.png`.

* Centred stacked text inside a **double-line rectangular frame** (two nested shapes). The logo is a standalone inline picture, not a grouped cover.
* Logo: `proposal/word/media/image1.png` = **454 x 134 px**, displayed `wp:extent cx=1887220 cy=556260` EMU = **5.24 x 1.55 cm**.
* Typography: all Times New Roman. "International School" 14 pt bold `4472C4` (`sz=28`); "Capstone Project 1", "Project Proposal", "FitAI - Smart Health & Fitness Assistant" **20 pt** bold (`sz=40`); version/date/team/signature 13 pt (`sz=26`). No 26 pt title and no 15 pt blue label in this family.
* Signature language: two anchored hairline rules (`cx=4737100 cy=0` and `cx=4694767 cy=4233` EMU = 13.16 cm and 13.04 cm wide) under "Review Panel Representative" and "Capstone Project 1 - Mentor:"; no "Approved by" block on the Proposal cover.
* Front matter: PROJECT INFORMATION (14-row table), DOCUMENT INFORMATION (7-row table), DOCUMENT APPROVALS (5-row signature table), REVISION HISTORY, TOC, List of Tables, List of Figures.

### Family B - grouped framed cover (arch, db, code, testplan, reflection, meeting, ai)

Evidence: `arch/word/document.xml://w:body/w:p[1]` (one `wp:anchor` group "Group 679" plus VML shape `#_x0000_t75` with `style=position:absolute;...width:18111;height:6000...`), `db/word/document.xml` same shape, PDFs `arch_p1.png`, `db_p1.png`, `code_p1.png`, `tech_p1.png`.

* Single-line rectangular frame; all cover text lives inside one grouped drawing (text duplicated in alternate content).
* Group extents: arch `cx=6050280 cy=8846820` = **16.81 x 24.57 cm**, anchor frame `6313170 x 9559290` = **17.54 x 26.55 cm**; db group `5943600 x 8793480` = **16.51 x 24.43 cm**, anchor `6618515 x 9971314` = **18.38 x 27.70 cm**. Nested logo xfrm `1811020 x 600033` EMU = **5.03 x 1.67 cm**; source `image1.png` = **420 x 124 px**.
* Typography: "International School" 15 pt bold `4472C4` (`sz=30`), "Capstone Project 1" **28 pt** bold (`sz=56`), document/project titles **20 pt** bold (`sz=40`), version/date 12 pt bold (`sz=24`), team lines italic 13 pt, "Approved by MSc. Tran Nhat Vinh", two signature blocks with horizontal rules, and "Capstone Project 1 - Menter:" (typo in the source).
* Front matter: Architecture has all seven blocks (project info, doc info, approvals, revision history, TOC, list of tables, list of figures). Database has only document information, revision history, TOC, list of figures, list of tables - **no project information and no approvals table** (`db/word/document.xml://w:body`, first table is DOCUMENT INFORMATION; no PROJECT INFORMATION text).

### Family C - Family B cover with coloured body styles (tech, testplan)

Covers are Family B in geometry/typography (`tech_p1.png`), but `docDefaults` are Open Sans 11 pt brown and heading styles are PT Sans Narrow with orange/teal; direct runs restore TNR 13 pt black in the visible body (`tech_p6.png`, `testpl_p7.png`). Header uses a dark blue rectangle with small brown italic labels.

## 8. Tables

| Property | Measured evidence |
|---|---|
| Header fills | `db`: `BFBFBF` x113 (`db/word/document.xml://w:tbl//w:shd@w:fill`), `D9D9D9` x6. `arch`: `E7E6E6` x32, `D9D9D9` x18, `D0CECE` x16, `F3F3F3` x4, `BFBFBF` x1, `FFFFFF` x41. `proposal`: `D0CECE` x30, `AEAAAA` x6. `testplan`: `D9D9D9` x38, `BFBFBF` x18. `tech`: one table uses `8EAADB` (PDF `tech_p6.png`). |
| Borders | Mostly `single` black `w:sz=4` (0.5 pt) and `w:sz=8` (1 pt): arch 1010 x 1 pt + 340 x 0.5 pt; db 149 x 0.5 pt `auto` + 64 x 0.5 pt `666666`; plan 2155 x 0.5 pt black. `8EAADB` x6 in arch/proposal/stories/ui. |
| Font size / weight | Table runs almost all **inherit 13 pt** (proposal 571 direct `sz=26`; arch only 6 direct `sz=24`; db/plan no direct table size). Header rows bold, body regular. No FITAI 10/11 pt table-text convention in the required files. |
| Alignment | Cell `jc`: arch center 51 / both 15; db center 108 / left 12; proposal center 86 / both 25; testplan center 478 / left 124. |
| Captions | Arch captions are direct-formatted paragraphs (bold "Figure 1." + italic title), centred, 12 pt before/after, 1.5 line, inheriting 13 pt (`arch/word/document.xml` paragraph with bookmark `_heading=h.iqyjyy1psp7`). DB captions use `pStyle=Caption` but override to 13 pt and centre (`db/word/document.xml` paragraph containing `image4.png`). Proposal captions `sz=26` = 13 pt. `SEQ Table`/`SEQ Figure` fields number them; DB lists 20 tables and 2 figures. PDF `db_p15.png` shows `Table 9: Database Design (Goal)` centred bold-italic between the heading and the table. |

---

## 9. Figures and diagrams (images actually viewed)

| Viewed image | Source | Visual description |
|---|---|---|
| `arch/word/media/image1.png` (420 x 124 px) | Architecture cover | University logo: red Duy Tan mark/wordmark, gray "UNIVERSITY", blue "International School" - the only multi-colour brand element on the monochrome cover. |
| `arch/word/media/image3.png` (1035 x 703 px) | Architecture use-case diagram | Black hairline (about 1 px) ellipses and stick figures, thin dashed `<<include>>`/`<<extend>>` links, bold centred title, Times-like serif 12-14 px labels, single rectangular frame. No fills or colour. |
| `arch/word/media/image5.png` (1386 x 804 px) | Architecture context diagram | Same language: rounded rectangles for actors, one central oval system, orthogonal solid/dashed arrows with arrowheads, bordered legend box at bottom (`System`, `Actor`, `Interaction`). |
| `proposal/word/media/image2.png` (1386 x 954 px) | Proposal context diagram | Essentially the same figure as arch image5 (reused asset), confirming cross-document consistency. |
| `proposal/word/media/image4.png` (799 x 449 px) | Proposal Scrum framework | **Exception**: third-party "neon rain / Agile for all" illustration with teal, orange, blue and red icons and coloured people - visually foreign to the house monochrome style. |
| `db/word/media/image4.png` (1875 x 1352 px) | Database ER diagram | Hairline black rectangles/ellipses/diamonds, `(PK)` and cardinality `1`/`n` notation, tiny serif labels, no colour, legend box at lower right. |
| `db/word/media/image5.png` (1846 x 858 px) | Database physical schema | dbdiagram.io export: gray `#DCDCDC`-style header bars, yellow key icons, thin gray orthogonal connectors with crow's-foot ends, small sans-serif column names - a second, tool-generated visual dialect. |

Pixel-frequency check (System.Drawing sampling): arch image3 dominated by `#FFFFFF` and `#000000` with grays `#ECECEC`/`#3F3F3F`; db image5 dominated by `#FFFFFF`, `#DCDCDC`, `#929292`, `#707070`, with a little `#475568` blue-gray.

**PDF comparison.** `pdfpages/arch_p10.png` shows the use-case diagram at about 16.0 x 12.3 cm (`arch/word/document.xml` extent 5768133 x 4426182 EMU) with legend and centred `Figure 1. Usecase Diagram` caption; pixels match `arch/word/media/image3.png`. `pdfpages/arch_p33.png` shows `image11.png` (25.97 x 13.91 cm) on a landscape-width page with a narrow blue left rule and `Figure 7. Entity Relationship Diagram`. `pdfpages/db_p15.png` shows table typography/caption placement matching XML; DB figure pages use the same embedded images. The PDF export introduces no new colour or line weight.

**Consistency verdict:** figure style is *hairline monochrome line art with serif labels and a legend*, but assets come from at least three tools (hand/UML export, dbdiagram.io, third-party coloured Scrum image). No unified icon system; shared traits are thin black strokes, centred placement, numbered captions and white space.

## 10. FITAI design system (measured)

### Global styles (most of the 14-file set)

| Element | Measured value | Exact source |
|---|---|---|
| Body | Times New Roman 13 pt (proposal 12 pt), black/auto | `arch/word/styles.xml:/w:docDefaults/w:rPrDefault/w:rPr/w:sz=26`; `proposal/word/styles.xml:/w:style[@w:styleId="Normal"]/w:rPr/w:sz=24` |
| Page | A4 11906-11920 x 16838-16860 tw; US Letter in tech/testplan | `arch/word/document.xml://w:sectPr/w:pgSz@w:w/@w:h`; `tech/word/document.xml` (12240 x 15840) |
| Colour | Office theme black/white/gray plus `#44546A`, `#4472C4`; visible text black | `arch/word/theme/theme1.xml:/a:clrScheme` |
| Headings | bold, numbering from `w:numPr` plus abstract numbering; H1/H2 mostly = body size | `arch/word/styles.xml:/w:style[@w:styleId="Heading1"]`; `arch/word/numbering.xml:/w:num[@w:numId="17"]` |
| TOC | `w:sdt` plus `TOC \o ... \h \z \u` or `\t "Heading..."`, cached hyperlinks, no `w:updateFields` | `arch/word/document.xml://w:instrText`; `arch/word/settings.xml` |

### Section-specific

| Element | Measured value | Exact source |
|---|---|---|
| Architecture | A4, L 1701 tw, H1/H2 13 pt, H3 12 pt Calibri `#1F3863`, 3 landscape sections, 2-cell header, 0.5 pt footer box rule | `arch/word/document.xml://w:sectPr[3]`; `arch/word/footer2.xml://w:pBdr/w:top@w:sz=4` |
| Database | Cover 11920 x 16860 / L 1985; body A4 1440 margins; 42 cm landscape section; `BFBFBF` table heads; 13 pt caption override; 9 pt Caption style `#44546A` | `db/word/document.xml://w:sectPr[8]`; `db/word/styles.xml:/w:style[@w:styleId="Caption"]` |
| Code Standard | TNR 13 pt, 1.5 line, first-line indent 567 tw, 36 pt Title, Courier New 10 pt `HTMLPreformatted` (unused), stale `C1SE.03` footer | `code/word/styles.xml:/w:docDefaults`; `code/word/footer3.xml` |
| TechStack / TestPlan | Letter, Open Sans 11 pt brown defaults, PT Sans Narrow heading styles, but visible TNR 13 pt black via direct runs | `tech/word/styles.xml:/w:docDefaults`; `tech/word/document.xml://w:rFonts[@w:ascii="Times New Roman"]` |

### Figure and diagram styles

| Property | Measured value | Exact source |
|---|---|---|
| Stroke / fill | about 1 px black hairlines, white fill, occasional gray `#DCDCDC` header bars | viewed `arch/image3.png`, `db/image4.png`, `db/image5.png` |
| Shape language | ellipses, rounded rectangles, orthogonal arrows, stick figures, diamonds, legend box | `arch/word/media/image3.png`, `image5.png`, `db/image4.png` |
| Typography in figures | serif 10-14 px, centred bold figure title, labels on connectors | viewed images above |
| Placement / size | centred inline, 16.00-25.97 cm wide; captions centred below | `arch/word/document.xml://wp:extent` for image3/image5/image11 |
| Numbering | `SEQ Figure \* ARABIC`, "Figure N. Title" (arch) / "Figure N: Title" (db) | `arch/word/document.xml://w:instrText`; `db/word/document.xml://w:instrText` |

### Table styles

| Property | Measured value | Exact source |
|---|---|---|
| Head fill | `E7E6E6` / `D9D9D9` / `D0CECE` (arch, plan, proposal), `BFBFBF` (db) | `arch/word/document.xml://w:shd/@w:fill`; `db/word/document.xml://w:shd[@w:fill="BFBFBF"]` |
| Borders | black `single w:sz=4` (0.5 pt) and `w:sz=8` (1 pt); db also `666666` 0.5 pt | `db/word/document.xml://w:tblBorders/*/@w:sz` |
| Text | inherited 13 pt, header bold, centred or justified | `arch/word/document.xml://w:tbl//w:jc` |
| Caption | centred 13 pt, bold label plus italic title (arch), 13 pt italic (db override) | `arch/word/document.xml` caption paragraph; `db/word/document.xml` Caption paragraph |

---

## 11. Differences vs `DBCAS/docs/agent/freeze-logs/doc-style-spec.md`

Every row cites a spec line and the measured evidence. "Spec" = previous agent, "Measured" = this audit.

| Spec claim | Measured reality | Evidence | Impact |
|---|---|---|---|
| L15: "the Architecture file is the only one with A4 + left 1701 tw (3.00 cm)" | Proposal, plan, backlog, stories and UI also use left 1701 tw; arch is not unique. DB/code/testplan/meeting/reflection use 1985 tw (3.5 cm) on the **cover only**, body 1440 tw | `proposal/word/document.xml://w:sectPr/w:pgMar@w:left=1701`; `db/word/document.xml://w:sectPr[2]/w:pgMar@w:left=1440` | "Mainstream A4 margin" is a family pattern, not architecture-only |
| L16: "Open Sans 11 pt brown (TechStack, TestPlan)" as body font | Defaults are Open Sans 11 pt `695D46`, but visible body/table runs are Times New Roman 13 pt black (tech 1007, testplan 2052 direct runs) | `tech/word/styles.xml:/w:docDefaults`; `testplan/word/document.xml://w:rFonts[@w:ascii="Times New Roman"]`; PDFs `tech_p6.png`, `testpl_p7.png` | Brown Open Sans is a latent style, not the rendered body |
| L18: "CodeStandard H1/H2 are bold with no size at all" | No explicit `w:sz`, but they inherit 13 pt from docDefaults; body-size headings, not sizeless text | `code/word/styles.xml:/w:style[@w:styleId="Heading1"]` plus `/w:docDefaults/w:rPrDefault/w:rPr/w:sz=26` | Effective size should be reported |
| L20: "Caption 9 pt `44546A` in Database and ProjectPlan; 13 pt in Proposal and UserStory (szCs only)" | DB style is 9 pt but **all 21 body captions override to 13 pt**; proposal Caption has both `sz=26` (13 pt) and `szCs=18` (9 pt), not "szCs only" | `db/word/styles.xml:/w:style[@w:styleId="Caption"]/w:rPr/w:sz=18`; `db/word/document.xml://w:p[pStyle=Caption]/w:pPr/w:rPr/w:sz=26` x21; `proposal/word/styles.xml:/w:style[@w:styleId="Caption"]/w:rPr/w:sz=26` | Rendered FITAI captions are 13 pt; generator's 9 pt caption is a deliberate deviation |
| L21: DB `BFBFBF` on 113 heads with 0.5 pt auto borders | Fill/count correct; borders are both `auto` (149) **and** explicit `666666` (64), all 0.5 pt | `db/word/document.xml://w:tblBorders/*[@w:color]`, `sz=4` | Border colour is not exclusively auto |
| L22: one theme palette for all files | DB swaps accent1/accent5; code uses dk2 `0E2841`, accents `156082/E97132/...`; tech/testplan use dk2 `1F497D`, accents `4F81BD/...`, hlink `0000FF` | `db/word/theme/theme1.xml:/a:clrScheme/a:accent1`; `code/word/theme/theme1.xml`; `tech/word/theme/theme1.xml` | "The FITAI theme" is three distinct themes |
| L25: "12 of 14 have a working PAGE field" | All 14 DOCX define a `PAGE` field in header/footer XML; only db and sprint define `NUMPAGES` | `*/word/footer*.xml://w:instrText[contains(.,"PAGE")]`; `db/word/footer4.xml`, `sprint/word/header3.xml` | "Page X of Y" is rare (2 files), not the dominant footer pattern |
| L35-40: Architecture has "style-based TOC, a header built as a two-cell table with a 0.75 pt rule, a working PAGE footer from page two" | Header is a 2-cell table **without** rule; the 0.5 pt (`w:sz=4`) box rule is in the footer; TOC has field codes and cached hyperlink text but no TOC-styled cached paragraphs; three TOC fields present (one 3-level, two 6-level) | `arch/word/header1.xml://w:tbl` (no coloured `pBdr`); `arch/word/footer2.xml://w:pBdr/w:top@w:sz=4`; `arch/word/document.xml://w:sdt` containing `TOC` fields; 0 `pStyle=TOCn` cached paragraphs | Chosen base carries duplicate fields and unstyled cached TOC; cloning would inherit them |
| L44: "Code Standard file has no usable format base ... no monospace style" | A monospace style exists: `HTMLPreformatted`, Courier New 10 pt, tab stops 916 tw, single spacing - defined but unused; Code also has Title 36 pt and Heading3 14 pt | `code/word/styles.xml:/w:style[@w:styleId="HTMLPreformatted"]/w:rPr` | Generator's Consolas 9 pt code style is a new choice, smaller than FITAI's defined 10 pt |
| L58: "left 3.5 cm equals the FITAI Database cover margin" | True **only for DB cover section** (sectPr 1, left 1985 tw); DB body section 2 uses 1440 tw = 2.54 cm | `db/word/document.xml://w:sectPr[1]/w:pgMar@w:left=1985`; `//w:sectPr[2]/w:pgMar@w:left=1440` | 3.5 cm body margin is an owner decision, not a body-style match |
| L59: "Body ... justified ... 1.5x as in CodeStandard/TestPlan" | 1.5x (`line=360`) true for code defaults and much of testplan; justification is not universal (testplan has 8 left / 9 center direct `jc` and first-line indent) | `code/word/styles.xml:/w:docDefaults/w:pPrDefault/w:pPr/w:spacing@w:line=360`; `testplan/word/document.xml://w:pPr/w:jc`; `testplan/word/styles.xml:/w:docDefaults/w:pPrDefault/w:pPr/w:ind@w:left=357` | Universal justified/1.5 body is a house-style choice |
| L61: "Heading 1 18 pt bold `#1F3863` ... FITAI Architecture Heading 3 colour `1F3863`; 18 pt keeps a hierarchy above 13 pt body" | Colour source correct; 18 pt is not a FITAI H1 size (architectural H1 is 13 pt, same as body; Title 14 pt). Explicitly a DBCAS-house adjustment | `arch/word/styles.xml:/w:style[@w:styleId="Heading1"]` (no `w:sz`); same file Heading3 `w:color@w:val=1F3863` and `w:sz=24` | Must be recorded as deviation, not FITAI match |
| L64: "Tables header row 11 pt bold, body 11 pt, 10 pt in dense tables, 9 pt in column dictionary" | No such sizes in measured table bodies: inherited 13 pt dominates; arch 6 runs at 12 pt, proposal 571 at 13 pt, db/plan no direct table size | `arch/word/document.xml://w:tbl//w:rPr/w:sz`; `db/word/document.xml://w:tbl//w:rPr/w:sz` empty | Table size reductions are generator decisions, not FITAI measurements |
| L65: "Code: Consolas 9 pt ... No FITAI monospace style exists" | FITAI defines Courier New 10 pt `HTMLPreformatted` (unused); Consolas appears nowhere in the 14 DOCX font histograms | `code/word/styles.xml:/w:style[@w:styleId="HTMLPreformatted"]/w:rPr`; font histograms of all `word/document.xml` | Both the existence claim and the chosen font/size are inaccurate |
| L66: "Header ... 9 pt `#44546A`, 1 pt rule - FITAI header pattern" | FITAI headers are 11-13 pt bold italic black (tech/testplan 11 pt brown), no 9 pt coloured text; rule is 0.5 pt (`w:sz=4`) and often in the footer | `arch/word/header1.xml://w:rPr` (b/i, `color=000000`); `arch/word/footer2.xml://w:pBdr/w:top@w:sz=4`; `db/word/header11.xml://w:rPr/w:sz=22/24` | Generator header is a new design |
| L67: "Footer ... `Page X of Y` from `PAGE`/`NUMPAGES` fields - FITAI footer pattern" | Only db (`footer4.xml`) and sprint (`header3.xml`) use NUMPAGES; mainstream footer is `C1SE.56` plus plain `Page N` | `*/word/footer*.xml://w:instrText`; `arch/word/footer2.xml` | "X of Y" is an exception, not the pattern |
| L68: "Cover ... blue school labels `#4472C4`, **26 pt title**, version, date, project title, five member lines, signature block" | Measured cover sizes: 15 pt blue label (`sz=30`), **28 pt** "Capstone Project 1" (`sz=56`), **20 pt** document/project titles (`sz=40`), 12 pt version/date, 13 pt member lines. 26 pt appears nowhere on those covers | `arch/word/document.xml://w:body/w:p[1]//w:rPr/w:sz`; `proposal/word/document.xml://w:body/w:p[2..24]//w:sz`; PDFs `arch_p1.png`, `proposal_p1.png` | Generator's 26 pt title is not a FITAI measurement |
| L77 / L82: "Cover labels ... 11-26 pt", "Figure/table captions 9 pt italic" | Cover range 10-28 pt (`sz=20..56`); rendered captions 13 pt, not 9 pt | cover run-size histograms; `arch/word/document.xml` Figure 1 paragraph; `db/word/document.xml` Caption paragraphs | Generator size-exception list does not describe FITAI output |
| L24: "approvals (4 files only); Architecture has all seven blocks" | Architecture confirmed; Database has no project-information or approvals table, only five of seven blocks | `db/word/document.xml://w:body` first 50 block items | Database is not a complete front-matter model |

**Bottom line:** the previous spec's high-level claim that FITAI is a *family* of inconsistent templates is correct, but many values labelled "measured FITAI" are latent style defaults, single-file exceptions or deliberate DBCAS generator choices. The generator's 18 pt H1, 11/10/9 pt tables, 9 pt captions, Consolas 9 pt, 26 pt cover title, 9 pt `#44546A` header and 1 pt rule, and `Page X of Y` footer cannot be justified as copies of the FITAI reference; they should be recorded as explicit DBCAS deviations. Genuinely transferable FITAI traits are: A4-ish page, Times New Roman 13 pt body, black/neutral-gray palette, 2-cell or plain italic running head with hairline rule, numbered captions, `TOC`/`SEQ` fields, monochrome hairline diagrams, and the two framed cover families with the DTU logo at 5.0-5.2 cm width.
