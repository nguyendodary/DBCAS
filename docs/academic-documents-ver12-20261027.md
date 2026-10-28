# Academic documents reconciled in place as ver1.2 — 27 October 2026

The four DBCAS academic originals were **edited in place** for the first time, under a written
instruction from the document owner. The result is four improved versions of the same documents —
Proposal `ver1.5` → `ver1.2`, Architecture Design `ver1.3` → `ver1.2`, User Stories `ver1.4` →
`ver1.2`, Database Design `ver1.4` → `ver1.2` — not four regenerated replacements. Every earlier
version is still on disk and still byte-identical. No application code, no migration, no
question-bank row, no blueprint row and no sandbox rule was changed by this task.

Companion records: [academic-edit-ledger-20261027.md](academic-edit-ledger-20261027.md) holds every
single edit by document address with the original text preserved;
[academic-reconciliation-20261027.md](academic-reconciliation-20261027.md) holds the proposals that
preceded this instruction and remains as the audit trail;
[documentation-alignment-20261027.md](documentation-alignment-20261027.md) holds the repository-side
mismatch matrix and the diagrams-as-code record.

---

## 0. What the owner directed, and what it changed

| Owner directive (27 October) | Effect on this task |
|---|---|
| Direct editing of the Proposal, Architecture Design, Database Design and User Stories is authorised; "this is a real documentation editing and validation task, not merely an audit". | The held items H1–H6 of `academic-reconciliation-20261027.md` stop being proposals where the owner has decided. Amendments A4, D5, P4 and U3 are now applied (see §3 and §4). |
| Intended formal composition is **10 MCQ / 2 SQL / 1 essay**; the code still serves 10 / 0 / 3 for six theory areas; "**Do not falsely claim that the implementation has already been converted to 10/2/1**". | The target is stated as the requirement; the 10/0/3 behaviour is recorded in the Architecture document as **an unresolved implementation discrepancy, not an approved exception** (§4.1). |
| "This task authorizes documentation reconciliation, not changes to the assessment algorithm, question bank or database." | `backend/app/services/blueprints.py`, `db/migrations/*`, the question tables and the sandbox are untouched; the change recommendation in §4.3 is prepared, not executed. |
| Version ceiling **1.2** for all four documents, fixed v1.0 dates (Proposal 05/09, User Stories 14/09, Architecture 18/09, Database 25/09), "verify actual historical evidence and do not fabricate revisions or approvals", "preserve all existing document versions byte-identically", final deliverables saved as `ver1.2.docx`. | §1 and §2. Each v1.0 date was checked against the revision table inside the corresponding original before being relied on. |
| Use the repository `.dot` sources as canonical **but** preserve each figure's visual identity; "if a regenerated diagram substantially changes the original visual identity or loses meaningful information, keep the existing figure and report the issue instead of forcing replacement"; the System Context Diagram is specially protected. | Measured rather than assumed (§5). **Every embedded figure is kept byte-identical** and the content delta is carried in prose. The report required by the fallback clause is §5.2–§5.4. |
| "Regenerate only diagrams whose content materially differs… Preserve all diagrams that are still accurate, including their original embedded image bytes." | No figure was re-rendered. Media SHA-256 maps of each document are identical before and after (§7). |

---

## 1. Deliverables and preservation evidence

| Document | New active deliverable | Content baseline | Original (unchanged, sha256 prefix) | Rendered pages | Embedded figures |
|---|---|---|---|---|---|
| Proposal | `C1SE.70_ProposalDocument_DBCAS_ver1.2.docx` | `…_ver1.5.docx` | `69d467e599a45a2e…` | 58 → 58 | 4 + cover mark, all byte-identical |
| Architecture Design | `C1SE.70_ArchitectureDesign_DBCAS_ver1.2.docx` | `…_ver1.3.docx` | `d80be1f4513ceef3…` | 62 → 62 | 8 + cover mark, all byte-identical |
| User Stories | `C1SE.70_UserStoryDocument_DBCAS_ver1.2.docx` | `…_ver1.4.docx` | `7160977975fb1e6f…` | 24 → 24 | 1 + cover mark, byte-identical |
| Database Design | `C1SE.70_DatabaseDesign_DBCAS_ver1.2.docx` | `…_ver1.4.docx` | `58fb037e9c5a06da…` | 31 → 33 (+2 for the two inserted entity sections) | 2, byte-identical |

Page counts and figure geometry were produced by driving the installed Word engine read-only
(`_docread/render_ver12_20261027.py`, logs kept in `_docread/render_20261027/`). Documents are opened
with `ReadOnly=True` and closed with `wdDoNotSaveChanges`; the SHA-256 of every `.docx` is re-read
after the export and reported unchanged by the tool itself.

The scripts and logs referenced here (`_docread/*.py`, `_docread/render_20261027/`,
`_docread/backup_docs/`) live in the workspace next to the repository, outside it, as in every
previous documentation cycle, and so do the four `.docx` deliverables. The 28 October release audit
tested whether they should move inside Git and found `CONTRIBUTING.md` rule 3 — *"Không commit file
môi trường (`.env`) hay tài liệu dự án (docx/pdf) vào repo"*. That standing rule was followed rather
than bypassed: the binaries stay outside the repository and their exact bytes are named by SHA-256 in
[release-audit-20261028.md](release-audit-20261028.md) §4.

`_docread/backup_docs/` additionally holds pre-task copies of all four originals.

---

## 2. Revision-history integrity under the 1.2 ceiling

The four originals carried 6, 4, 5 and 5 revision rows up to 1.5 / 1.3 / 1.4 / 1.4. Collapsing to a
1.2 ceiling must not fabricate history, so the rule applied was: keep the verified first row, keep one
honest intermediate row, and make the 1.2 row state explicitly which superseded revisions it
consolidates.

| Document | v1.0 date in the original revision table | Owner's fixed v1.0 date | Verified | 1.2 row comment |
|---|---|---|---|---|
| Proposal | 05/09/2026 | 05/09/2026 | yes | names the consolidated 1.2–1.5 rows and their dates |
| User Stories | 14/09/2026 | 14/09/2026 | yes | names the consolidated 1.2–1.4 rows |
| Architecture Design | 18/09/2026 | 18/09/2026 | yes | names the consolidated 1.2–1.3 rows |
| Database Design | 25/09/2026 | 25/09/2026 | yes | names the consolidated 1.2–1.4 rows (this document's revision table is ordered `Version \| Person(s) \| Date \| Description`) |

Every row removed from a document table is preserved verbatim in the ledger, so nothing is lost
between the 1.5/1.4/1.3 originals and the 1.2 deliverable. Author strings are unchanged
("All members", "C1SE.70 Team", "C1SE.70 Project Team", "Truong, Nguyen Quang & C1SE.70 Team");
no name was added and no approval was invented. Cover "Version" and "Date:" lines, and the DOCUMENT
INFORMATION table (date 27/10/2026 plus the matching `…_ver1.2.docx` file name) were updated to agree
with the revision table.

---

## 3. Reconciliation matrix

Material changes only. The complete address-by-address record, with original and revised text, is
[academic-edit-ledger-20261027.md](academic-edit-ledger-20261027.md) (27 addressed edits plus the
notes on the two inserted sections).

| Document | Section | Original claim | Revised claim | Code / schema evidence | Reason | Class |
|---|---|---|---|---|---|---|
| Proposal | §7 Data & Storage tier (P181) | "A PostgreSQL 17 database (32 tables)" | "(34 tables)" and the stored-data list gains "blueprint versions and adaptive-round evidence" | `docs/diagrams/schema-catalog.json` (34 tables, 49 FKs), `db/migrations/013_assessment_blueprints.sql`, `014_adaptive_events.sql` | two tables added after the document was written | implemented |
| Proposal | §8 evaluation pipeline (P188) | "the formal 10 MCQ / 2 SQL / 1 essay mix … is met" | "the formal **target** mix of 10 MCQ / 2 SQL / 1 essay … is met **for the approved blueprint version of the selected subject area and difficulty band**" | `blueprints.py:68-80`, `personalized_assessment.py:237-245`, `schemas.py:776-780` | the unqualified claim is false for six subject areas | intended, with the difference stated |
| Proposal | Table 9 (competency-based selection row) | selection described without mix policy | adds "Competencies the read-only sandbox cannot execute are blueprinted as MCQ + essays with no scheduled SQL practical." | `blueprints.py:20-30, 93-114` | records why the exception exists without approving it | implemented + intended |
| Architecture | P192, P202, P230, P231; Tables 53–56 | 32 tables; entity/service lists | 34 tables; the Assessment Blueprint Policy added to the service list; `AssessmentBlueprint`, its frozen session binding and `AdaptiveEvent` added to the entity narrative and to Table 57 | as above + `models.py` `AssessmentBlueprint`, `AdaptiveEvent` | the view predated migrations 013/014 | implemented |
| Architecture | UC07 primary flow (Table 22), UC10 (Table 25) | step wording implied a single fixed mix | step 3 states the target mix 10/2/1 as the configured contract; new step 3a describes blueprint seeding on publication and single-area binding; UC10 step 2 states "target mix … or the approved blueprint version for a single-area selection" | `assessment_service.py:224-231`, `blueprints.py:139-165, 191-209` | requirement kept visible, mechanism described accurately | implemented + intended |
| Architecture | new paragraph after P202 | *(absent)* | "**Formal composition is an open implementation discrepancy, not an approved exception.**" — records the 15 October owner requirement, the six areas' shipped 10/0/3, the 27 October bank inspection finding no SQL item in any band, the refusal to weaken the read-only sandbox, and that no document claims conversion | `blueprints.py:23-30, 68-80`; probe §4.2 | required by the owner's instruction | discrepancy, documented |
| User Stories | new paragraph after P36 | *(absent)* | requirement baseline and the open difference, plus "no story claims functionality that is not delivered" | 25 story ids verified present, none renumbered | §8 of the instruction: correct criteria, invent nothing | intended |
| Database Design | P62, P70, Table 3 | "the 32 tables of the DBCAS schema", no foreign-key count, migrations listed only through 012, no blueprint or adaptive rows | "34 tables … (49 declared foreign keys)"; later-migration list extended; Table 3 gains AssessmentBlueprint and AdaptiveEvent rows | catalog + `compare_db_schema_20261027.py` | the physical catalog moved | implemented |
| Database Design | Question (Table 9), AssessmentSession (Table 16) | no `original_locale`; no `blueprint_id` | both rows added, matching the DDL | `db/migrations/012_question_original_locale.sql`, `013_assessment_blueprints.sql` | two columns were undocumented | implemented |
| Database Design | two new entity sections, Tables 34 and 35 | *(absent)* | AssessmentBlueprint (16 attribute rows) and AdaptiveEvent (5 attribute rows), cloned from the existing block so heading level, lead-in, caption style and table style are inherited | catalog + migrations 013/014 | the conceptual/logical/physical distinction is preserved: these are physical tables, so they belong in the physical sections | implemented |

Nothing was deleted. No chapter was reorganised, no section renumbered, no existing requirement,
traceability id, figure reference, caption or citation removed.

---

## 4. Formal assessment: the 10/2/1 requirement against the implemented behaviour

### 4.1 What the documents now say

All four documents state the owner's requirement — a 60-minute, 13-item formal session targeted at
10 MCQ / 2 SQL / 1 essay. Where a document describes what the running system does, the six theory
subject areas are described as they are: bound to an immutable blueprint version whose quota is
10 MCQ / 0 SQL / 3 essay. The Architecture document carries the discrepancy paragraph; the Proposal
and User Stories carry the qualifying wording; no document claims the implementation has been
converted, and no document calls the 10/0/3 rows an approved exception.

### 4.2 Feasibility against the real bank and the real sandbox

Measured read-only on the development database (`_docread/feasibility_probe_20261027.sql`),
validated questions with confirmed concept tags only, difficulty bands per
`blueprints.py:19` (`EASY` 1–2, `MEDIUM` 3, `HARD` 4–5):

| Subject area | SQL items available, EASY / MEDIUM / HARD | Can 10 / 2 / 1 be served today? |
|---|---|---|
| PostgreSQL Administration | 0 / 0 / 0 | **no** |
| PostgreSQL Concurrency | 0 / 0 / 0 | **no** |
| PostgreSQL Performance | 0 / 0 / 0 | **no** |
| `Performance` (the benchmark concept area, distinct string) | 0 / 0 / *no items in the HARD band at all* | **no** |
| PostgreSQL Security | 0 / 0 / 0 | **no** |
| PostgreSQL Server Programming | 0 / 0 / 0 | **no** |
| PostgreSQL Querying | 13 / 30 / 16 | yes |
| SQL Querying | 13 / 6 / 2 | yes |
| PostgreSQL Functions | 3 / 8 / 2 | yes |
| Database Design | 2 / 3 / 2 | yes |
| PostgreSQL Data Types | 2 / 3 / 2 | yes |
| PostgreSQL Data Definition, Data Manipulation, SQL Foundations, Querying | 2 / 2 / 2 each | yes |

Two further measurements matter:

- A second query over **all** statuses (`validated`, `draft`, `retired`) for the six theory areas
  returns **zero rows**: there is no SQL item to promote, only items that must be authored.
- `Performance` holds only **6** validated MCQ items in EASY and 6 in MEDIUM. Even setting SQL aside,
  a 10-MCQ quota in those bands cannot be filled from distinct items today;
  `select_questions` raises `insufficient_question_pool` rather than substituting
  (`personalized_assessment.py:127-131`), and `validate_assessment_bank` already refuses activation
  below the quota (`assessment_validation.py:43-45`).
- `question.family_id` is NULL across the bank, so the deduplication in
  `assessment_validation.py:35-38` and the plan assembler currently treats every question as its own
  version family. "10 distinct MCQs" and "10 distinct families" are the same requirement today and
  will diverge the moment families are populated.

### 4.3 Implementation change recommendation — **prepared, not implemented**

To make the requirement true in code without weakening anything, in this order:

1. **Author SQL items for the six theory areas, 4 per area × band minimum** (2 selected + 2 reserve,
   so a withdrawal or a retirement does not make a published cell unfillable). Each item must be
   answerable by a read-only `SELECT` that the sandbox can actually run: catalog inspection
   (`pg_indexes`, `pg_stat_user_tables`, `pg_locks`, `pg_settings`, `pg_roles`), `EXPLAIN` output
   *read as text where the fixture allows the planner to run*, and `SELECT`-only diagnosis against a
   seeded fixture. Items that would require the learner to run `CREATE INDEX`, `VACUUM`,
   `pg_dump`, `SET TRANSACTION`, `ALTER SYSTEM` or `CREATE FUNCTION` must stay MCQ/essay — the
   sandbox remains SELECT-only, 3-second statement timeout, 256 MB, rolled back.
2. **Administrator validation**: every new item goes through the existing draft → validated path with
   confirmed concept tags, and through `verify_sql_fixtures` so its expected result set is executed,
   not asserted.
3. **Append new blueprint versions** for the affected area × band cells (`seed_blueprints` on the
   next publication, or a new immutable version), with `approved_by` set by a named Administrator
   action — closing held item H2 in the same step — and quota 10 / 2 / 1.
4. **Delete the `THEORY_AREAS` zero-SQL branch** in `blueprints.py:68-73` only once step 3 has
   produced filled cells, and update `test_assessment_blueprints.py:108-112` and `:180-185` to assert
   10/2/1 for those areas. Removing the branch first would make every single-area formal session in
   those six areas fail with `insufficient_question_pool`.
5. **Top up the `Performance` MCQ pool to ≥ 10 distinct validated items per band** before enabling
   the change for that area.
6. **Re-verify and re-document**: re-run the probe, then update the Architecture discrepancy paragraph
   and the Proposal wording so the "target" qualifier can become a statement of fact. Until then the
   wording in §4.1 stays.

Explicitly out of scope for this task, and requiring separate authorisation: steps 1–6 themselves,
any change to `schemas.py:776-780`, any migration, any edit to existing blueprint rows or historical
session plans, any change to sandbox limits, and any AI credential change.

### 4.4 What was not done to make the numbers look right

No filler SQL question was generated to meet a quota. No blueprint row was edited. No test was
relaxed. No historical session snapshot was rewritten. No sandbox rule was touched. The documents
were corrected to describe the difference instead of concealing it.

---

## 5. Diagrams: measured, then deliberately left alone

### 5.1 Fidelity gate (`_docread/figure_fidelity_20261027.py`, output kept with the render logs)

Each embedded figure was compared with its repository source by placed aspect ratio:

| Embedded figure | in the document | from `docs/diagrams/*.svg` | delta |
|---|---|---|---|
| Proposal Figure 1, sprint roadmap | 1.347 | *no `.dot` source exists* | n/a |
| Proposal Figure 2, system context | 1.354 | `system-context.svg` 1.213 | −10% |
| Proposal Figure 3, logical architecture | 1.004 | `logical-architecture.svg` 2.121 | **+111%** |
| Proposal Figure 4, evaluation pipeline | 1.762 | nearest view `assessment-lifecycle.svg` 0.810 | **−54%** |
| Architecture Figure 1, use case | 0.909 | `use-cases.svg` 0.466 | **−49%** |
| Architecture Figure 2, system context | 1.349 | `system-context.svg` 1.213 | −10% |
| Architecture Figure 3, container | 1.019 | `containers.svg` 2.282 | **+124%** |
| Architecture Figure 4, component | 1.658 | `components.svg` 1.148 | **−31%** |
| Architecture Figure 5, module view | 1.612 | `modules.svg` 3.080 | **+91%** |
| Architecture Figure 6, allocation | 1.038 | `deployment.svg` 1.578 | **+52%** |
| Architecture Figure 7 / Database Figure 1, ERD | 1.939 | `conceptual-core.svg` 1.832 | −6% |
| Architecture Figure 8 / Database Figure 2, table relationship | 1.654 | `physical-schema.svg` 1.008 | **−39%** |

### 5.2 Decision: keep every embedded figure, byte-identical

Nine of the fourteen diagram placements differ by more than 30% in aspect ratio, four sit within about
10%, and one has no reproducible source at all. Aspect ratio is only the measurable part: the embedded
figures are the team's own drawings, each saved at the 300 dpi of its matplotlib source
(`_docread/draw_*.py` on the shared `_docread/diagrams_common.py`, which composes
`matplotlib.patches.FancyBboxPatch` / `Rectangle` / `Ellipse` / `FancyArrowPatch` and writes
`fig.savefig(path, dpi=fig.dpi)` at `:30` and `:206`; that is the save-time density, not the
resolution a reader sees after Word scales the placement — the effective per-placement ppi is
measured in [release-audit-20261028.md](release-audit-20261028.md) §5), with
their own box styling, colour coding, font sizes and manual placement, whereas the repository views
are Graphviz `dot` layouts. Substituting them would redraw almost every figure in the four documents,
force a resize of every placement, and
change the visual identity the owner told me to preserve — including for the System Context Diagram,
which the owner singled out. The rendering pipeline emits SVG only; there is no pinned PNG
rasterizer, so a swap would also require a new tool.

The owner's fallback clause applies: *keep the existing figure and report the issue instead of
forcing replacement.* That is what happened, and §5.1 is the report.

### 5.3 What carried the content delta instead

The documents already have a convention for exactly this: each figure is introduced as the baseline
view, with a "Note:" paragraph that states what the implemented system adds. Those notes were extended
in place — blueprint policy, frozen plan assembly, per-area evidence mixes, `AdaptiveEvent` — so the
prose and tables are current while the figures remain the originals. No caption number changed, and no
figure reference broke.

### 5.4 If editable figures are wanted later

The repository sources are canonical for *content*: `docs/diagrams/*.dot` plus their `.json` ledgers
are validated by `npm run diagrams:check` (10 models, 34 tables / 49 FKs verified against the DDL).
Producing document figures from them is a separate, reversible decision that needs (a) a pinned
PNG/SVG rasterizer, and (b) an owner decision per figure about accepting the new layout. Nothing in
this task forecloses that.

---

## 6. Database Design accuracy

Compared attribute-by-attribute with `docs/diagrams/schema-catalog.json`, extracted read-only from a
disposable PostgreSQL 17.11 (`_docread/compare_db_schema_20261027.py`):

| Measure | `ver1.4` original | `ver1.2` deliverable |
|---|---|---|
| Tables with a documented attribute section | 32 of 34 | **34 of 34** |
| Documented columns vs catalog columns | 228 of 251 | **251 of 251** |
| Undocumented columns | 23 (`assessment_blueprint` 16, `adaptive_event` 5, `question.original_locale`, `assessment_session.blueprint_id`) | **0** |
| Foreign keys stated in the document | not stated numerically | **49 declared**, matched to the catalog |
| Migrations covered | through 012 | **through 014** |

Caption numbering was handled as field behaviour, not typed text: the two inserted captions carry
correct cached SEQ values, the Hardware caption's cached value moved 34 → 36, and
`<w:updateFields w:val="true"/>` was added to this document only, so Word refreshes every caption, the
list of tables and the page numbers on first open. Verified in Word: the refreshed list reads
Table 33 ResultReleaseEvent (24), **Table 34 AssessmentBlueprint (24)**, **Table 35 AdaptiveEvent
(25)**, Table 36 Hardware and Software Requirements (25), body captions 1–36 with no duplicates or
gaps.

---

## 7. Validation performed

| Check | Result |
|---|---|
| Four originals byte-identical before/after | pass (`69d467e5…`, `d80be1f4…`, `7160977975…`, `58fb037e…`) |
| ZIP integrity of all four deliverables | pass (`testzip()` None), all parts readable |
| Embedded media preserved | pass — per-document media entry SHA-256 maps identical (Proposal 5, Architecture 9, User Stories 1, Database 4); inline shape counts and widths unchanged |
| Paragraph-style inventory preserved | pass for all four (no style added, removed or reassigned) |
| Table row counts and traceability ids | pass; all 25 User Story ids present, none renumbered or duplicated |
| Expected new strings present / stale strings absent | pass ("34 tables" present; "32 tables", "Version 1.3/1.4/1.5" absent) |
| Opens in the real Word engine without repair | pass, all four; 0 degenerate picture shapes |
| Rendered page counts | Proposal 58, Architecture 62, User Stories 24, Database 33 |
| PDF export of the rendered result | produced to `_docread/render_20261027/` for inspection only; source `.docx` hash re-verified unchanged after each export |
| Schema comparison | pass — 34/34 tables, 251/251 columns |
| `npm run diagrams:check` | pass — 10 model/render inventories, 34 tables, 49 foreign keys, `schema.sql` and 14 migration fingerprints match |
| `npm run inventory:check` | pass — API and frontend route inventories match their sources |
| Relative links in `docs/*.md` | pass — 223 relative links across 39 project documents resolve, 0 broken |

---

## 8. Limitations and non-actions

- **No PDF original exists.** There is no `C1SE.70_*.pdf` in the workspace root. The four
  `output/*_references_fixed.pdf` files are 2 October derived exports, not originals; they are now
  stale relative to ver1.2 and were **not** regenerated, because inventing a PDF pair the owner never
  had would misrepresent the deliverable set. Earlier references to "their PDF pairs" and to a
  "root DOCX/PDF set" have been corrected.
- **One Proposal list entry reflows**: "Table 7: Core Functional Modules…" moves from page 13 to 14
  when fields refresh, a consequence of the added words. Total page count is unchanged.
- **The Architecture List of Tables is stale in the original**, not in my edit: its 54 cached entries
  are consecutive while the actual in-table labels skip 13, 21 and 24. That document does **not** carry
  `updateFields`, so it opens exactly as before; forcing a refresh would expose the pre-existing gap.
  Flagged for the owner rather than silently renumbered, because renumbering would break in-text
  references to Tables 14–54.
- `docs/requirements-decisions.md` was not written to. It is the owner's approvals register; the
  directives in §0 are recorded here instead, and the register entry for the reaffirmed 10/2/1 target
  plus the documentation-only ruling awaits the owner.
- Blueprint provenance is unchanged: all 49 rows still carry `approved_by = NULL` (held item H2).
- No application file was modified. `git status` shows no change under `backend/app/`,
  `frontend/src/` or `db/`.
- Development data was read, never written. No container was created, stopped or removed. One is
  worth reporting: `dbcas-catalog-7baff1` (`postgres:17`) was already running when this phase began,
  and its name matches the *disposable* catalog container that
  [documentation-alignment-20261027.md](documentation-alignment-20261027.md) §0 reported as removed —
  so either that removal did not take effect or something recreated it. It holds no academic or
  production data this task touched, and deleting a container is a destructive act outside this
  task's authority, so it is flagged for the owner instead of removed.
- The 11 university deliverable categories with no DBCAS document (held item H6) remain undrafted.
- Nothing was pushed, tagged, rebased or force-updated.

---

## 9. Local commits created by this task

Two further local commits follow the five recorded in §4 of
[academic-reconciliation-20261027.md](academic-reconciliation-20261027.md):

| Subject | Contents |
|---|---|
| `docs(academic): reconcile the four university documents in place as ver1.2` | this record and [academic-edit-ledger-20261027.md](academic-edit-ledger-20261027.md) |
| `docs: apply the owner's 27 October direction to the held academic proposals` | the supersession note and the corrected original inventory in [academic-reconciliation-20261027.md](academic-reconciliation-20261027.md) and [documentation-alignment-20261027.md](documentation-alignment-20261027.md) |

`origin` still points at `633fea3`; the local branch is ahead by these seven commits and publishing
them remains the owner's decision. *(That count was true when it was written and has since been
superseded: five more documentation commits landed before the 28 October audit, which re-counted the
pending range and recorded the result in
[release-audit-20261028.md](release-audit-20261028.md) §1.)* The workspace-root `.docx` deliverables
are not repository content, as they have never been. *(Confirmed rather than assumed on 28 October:
the release audit checked for
a policy excluding binary academic documents, found `CONTRIBUTING.md` rule 3, and left the four files
outside Git — see [release-audit-20261028.md](release-audit-20261028.md) §4.)*
