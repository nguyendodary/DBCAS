import docx
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from pathlib import Path

ROOT = Path(r'C:\Users\kudot\Downloads\proposal test\DBCAS')
DOC = ROOT / 'docs/submission/final/C1SE.70_ArchitectureDesign_DBCAS_ver1.3.docx'
ERD = ROOT / 'docs/submission/final/assets/erd'
d = docx.Document(str(DOC))
paras = d.paragraphs
# locate the landscape section heading and its closing sectPr
start = None
for i, p in enumerate(paras):
    if p.text.strip() == '7. Entity Relationship Diagram':
        start = i
        break
if start is None:
    raise SystemExit('heading not found')
end = None
for j in range(start + 1, len(paras)):
    if paras[j]._p.findall('.//' + qn('w:sectPr')):
        end = j
        break
if end is None:
    raise SystemExit('section end not found')
# remove old image/caption paragraphs between heading and sectPr
for p in paras[start + 1:end]:
    p._p.getparent().remove(p._p)
# insert 13 new pages before the sectPr paragraph
end_p = paras[end]
titles = [
    'Figure 7. Entity relationship overview (1/2)',
    'Figure 7. Entity relationship index (2/2)',
    'Figure 8. Entity relationship diagram — Identity and access (1/11)',
    'Figure 8. Entity relationship diagram — Curriculum and concepts (2/11)',
    'Figure 8. Entity relationship diagram — Question bank and generation (3/11)',
    'Figure 8. Entity relationship diagram — Assessment and attempts (4/11)',
    'Figure 8. Entity relationship diagram — Grading, results and competency (5/11)',
    'Figure 8. Entity relationship diagram — Review workflow (6/11)',
    'Figure 8. Entity relationship diagram — AI audit and retention (7/11)',
    'Figure 8. Foreign-key ledger — rows 1–31 of 122 (8/11)',
    'Figure 8. Foreign-key ledger — rows 32–62 of 122 (9/11)',
    'Figure 8. Foreign-key ledger — rows 63–92 of 122 (10/11)',
    'Figure 8. Foreign-key ledger — rows 93–122 of 122 (11/11)',
]
files = ['erd-overview.png', 'erd-index.png'] + [f'erd-module-{i}.png' for i in range(1, 8)] + [f'erd-ledger-{i}.png' for i in range(1, 5)]
for idx, (title, file) in enumerate(zip(titles, files)):
    ip = end_p.insert_paragraph_before('')
    ip.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if idx:
        ip.paragraph_format.page_break_before = True
    ip.add_run().add_picture(str(ERD / file), width=Cm(20.5))
    cp = end_p.insert_paragraph_before(title)
    cp.style = d.styles['Caption']
    cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r in cp.runs:
        r.font.name = 'Times New Roman'
        r.font.size = Pt(11)
        r.italic = True
        r.font.color.rgb = RGBColor(0x44, 0x54, 0x6A)
d.save(str(DOC))
print('inserted 13 ERD pages; images', len(d.inline_shapes), 'sections', len(d.sections))
