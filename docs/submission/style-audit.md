# Style / cover audit

## Proposal

- Styles/theme/settings/numbering C14N equal: `{'word/styles.xml': True, 'word/theme/theme1.xml': True, 'word/settings.xml': True, 'word/numbering.xml': True}`
- Page setup/header/footer identical: `True`
- Cover paragraphs identical: `True`
- Cover tables identical: `True`
- Paragraphs 225 -> 225; tables 21 -> 21
- Images 5 -> 5; changed indices [3, 4]; display sizes equal `True`

## Architecture

- Styles/theme/settings/numbering C14N equal: `{'word/styles.xml': True, 'word/theme/theme1.xml': True, 'word/settings.xml': True, 'word/numbering.xml': True}`
- Page setup/header/footer identical: `True`
- Cover paragraphs identical: `True`
- Cover tables identical: `True`
- Paragraphs 250 -> 271; tables 58 -> 58
- Images 14 -> 21; changed indices [1-13]; display sizes equal `True`

## Database

- Styles/theme/settings/numbering C14N equal: `{'word/styles.xml': True, 'word/theme/theme1.xml': True, 'word/settings.xml': True, 'word/numbering.xml': True}`
- Page setup/header/footer identical: `True`
- Cover paragraphs identical: `True`
- Cover tables identical: `True`
- Paragraphs 306 -> 327; tables 72 -> 72
- Images 8 -> 15; changed indices [1-7]; display sizes equal `True`

## SRS

Cover source: `C:\Users\kudot\Downloads\proposal test\FITAI - Documents\1. Proposal Document\C1SE.56_ProposalDocument_SHFA_ver1.2.docx`
Styles/theme/settings/numbering C14N equal: `{'word/styles.xml': True, 'word/theme/theme1.xml': True, 'word/settings.xml': True, 'word/numbering.xml': True}`
- Paragraphs 59 -> 69; tables 6 -> 11
- Images 4 -> 4; changed indices []; display sizes equal `True`

Expected: styles/theme/settings/numbering, page setup, header/footer and cover are unchanged.
Only image blobs for the explicitly edited diagram indices differ.
