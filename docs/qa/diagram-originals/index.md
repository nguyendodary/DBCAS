# Original v1.1 figures — extraction inventory (2026-11-08)

Source: `docs/academic/C1SE.70_*_DBCAS_ver1.1.docx` (untouched originals).
Extraction: `word/media/*` from each package, copied verbatim (no re-render)
to `docs/qa/diagram-originals/` (18 PNGs: 3 logos + 14 figure instances).
Pixels from `Pillow.Image.size`; pages from `List of Figures` fields
(e.g. “Figure 4: …43”); display size from `wp:extent` (EMU, 1 in = 914400 EMU).

| Doc | Figure | Caption (exact) | Page | Display (EMU → in) | Pixels | File | Type |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Proposal v1.1 | cover logo | (cover, `rId8`) | 1 | 1887220×556260 → 2.06×0.61 in | 454×134 | `ProposalDocument_ver1.1_image1.png` | logo (not a figure) |
| Proposal v1.1 | Figure 1 | Agile Scrum Sprint Roadmap & Official Faculty Milestones | 36 | 5580000×4141184 → 6.10×4.53 in | 4712×3497 (2.2 MB) | `ProposalDocument_ver1.1_image2.png` | roadmap / other |
| Proposal v1.1 | Figure 2 | DBCAS System Context Diagram | 38 | 5580000×4120615 → 6.10×4.51 in | 1431×1061 | `ProposalDocument_ver1.1_image3.png` | context |
| Proposal v1.1 | Figure 3 | DBCAS Logical System Architecture Diagram | 41 | 5486400×5463549 → 6.00×5.97 in | 3200×3160 | `ProposalDocument_ver1.1_image4.png` | logical |
| Proposal v1.1 | Figure 4 | Evidence-based Competency & Gap Evaluation Pipeline | 43 | 5579745×3167891 → 6.10×3.46 in | 1342×762 | `ProposalDocument_ver1.1_image5.png` | pipeline / other |
| Architecture v1.1 | header logo | (header, `rId7`) | — | 1809750×533400 → 1.98×0.58 in | 420×124 | `ArchitectureDesign_ver1.1_image1.png` | logo |
| Architecture v1.1 | Figure 1 | Use Case Diagram | 5 | 5580000×6138000 → 6.10×6.71 in | 3000×3300 | `ArchitectureDesign_ver1.1_image2.png` | use case |
| Architecture v1.1 | Figure 2 | System Context Diagram | 6 | 5580000×4136285 → 6.10×4.52 in | 1431×1061 | `ArchitectureDesign_ver1.1_image3.png` | context (dup of Proposal Fig 2) |
| Architecture v1.1 | Figure 3 | Container Diagram | 37 | 5238750×5143500 → 5.73×5.63 in | 1444×1418 | `ArchitectureDesign_ver1.1_image4.png` | container |
| Architecture v1.1 | Figure 4 | Component Diagram | 40 | 8366760×5047488 → 9.15×5.52 in | 2361×1423 | `ArchitectureDesign_ver1.1_image5.png` | component |
| Architecture v1.1 | Figure 5 | Module View | 44 | 8193024×5084064 → 8.96×5.56 in | 3300×2050 | `ArchitectureDesign_ver1.1_image6.png` | module |
| Architecture v1.1 | Figure 6 | Allocation View | 47 | 4191000×4038600 → 4.58×4.42 in | 1331×1283 | `ArchitectureDesign_ver1.1_image7.png` | allocation |
| Architecture v1.1 | Figure 7 | Entity Relationship Diagram | 50 | 8124825×4191000 → 8.89×4.58 in | 3251×1677 | `ArchitectureDesign_ver1.1_image8.png` | ERD (Chen) |
| Architecture v1.1 | Figure 8 | Table Relationship Diagram | 51 | 7877175×4762500 → 8.62×5.21 in | 3440×2080 | `ArchitectureDesign_ver1.1_image9.png` | TRD (crow's foot) |
| Database v1.1 | header logos | (`rId14`, `rId15`) | — | 5943600×8793480 → 6.50×9.62 in (header band) | 420×124 ×2 | `DatabaseDesign_ver1.1_image1.png`, `image2.png` | logo (dup ×2) |
| Database v1.1 | Figure 1 | Entity Relationship Diagram | 5 | 8649335×4461684 → 9.46×4.88 in | 3251×1677 | `DatabaseDesign_ver1.1_image3.png` | ERD (= Arch Fig 7) |
| Database v1.1 | Figure 2 | Table Relationship Diagram | 7 | 8649335×5229831 → 9.46×5.72 in | 3440×2080 | `DatabaseDesign_ver1.1_image4.png` | TRD (= Arch Fig 8) |

Totals: 14 figure instances → 11 unique diagram images (Context ×2 dup,
ERD ×2 dup, TRD ×2 dup) + 3 logos (Proposal 1 + Architecture 1 + Database 2
dup). CAPTIONS use “Figure N: …” in Proposal/Database and “Figure N. …” in
Architecture; redraws keep the original caption style. User Story v1.1 has
one logo and no figures (out of scope, unchanged).

v1.2 redraws in `docs/qa/doc-v2-new-diagrams/` (Proposal Fig 2; Arch Figs
1, 3, 4, 5, 6, 7, 8) are the earlier in-place redraws at original extents —
compared in `style-spec.md`.
