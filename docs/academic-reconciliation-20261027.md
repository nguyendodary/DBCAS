# Academic document reconciliation - 27 October 2026

These are **reviewable proposals**, not approved changes. Nothing in this file has been applied to
any university deliverable, and **no supervisor, owner or academic approval is claimed, implied or
invented** anywhere in it. The four root originals (`C1SE.70_ProposalDocument_DBCAS_ver1.5`,
`C1SE.70_ArchitectureDesign_DBCAS_ver1.3`, `C1SE.70_UserStoryDocument_DBCAS_ver1.4`,
`C1SE.70_DatabaseDesign_DBCAS_ver1.4`, with their PDF pairs) were **not opened for writing** during
this task; nor was any file under `FITAI - Documents/`.

It is the companion to [documentation-alignment-20261027.md](documentation-alignment-20261027.md),
which holds the evidence inventory, the mismatch matrix and the diagram preservation record. The
split is deliberate and follows the standing rule for this task: **objectively verifiable corrections
were applied inside the repository; anything that changes a requirement, a presented scope, or the
hand-drawn context figure is left as a proposal for the document owner.**

`docs/requirements-decisions.md` is the project's record of *owner-approved* decisions. Nothing from
this file was copied into it, because writing an unapproved decision into an approvals register would
itself be a fabrication. Each item below states where it must land once the owner decides.

## How to read each decision

| Field | Meaning |
|---|---|
| Current text / state | what the academic document, ledger or code does today, quoted or cited |
| Code evidence | file:line at HEAD `633fea3`, read at that line - not inferred from a README |
| Proposal | the exact wording or edit that can be applied on approval |
| If approved | what changes in the repository and in the academic deliverable |
| If declined | what is already true and stays true (no repository change is needed) |

Statuses used here are `PROPOSED - NOT APPROVED` and `HELD - NOT APPLIED`. There is no `APPROVED` row.

---

## 1. Decisions reserved to the document owner

Six items were identified where the code and the documentation can both be defended, and choosing
between them is a requirement or presentation judgement rather than a mechanical correction. They are
listed in descending order of academic consequence.

### H1 - the formal question mix for theory areas contradicts an owner-approved contract

**PROPOSED - NOT APPROVED.** This is the most important item in this file and the one that should be
decided first.

| Field | Detail |
|---|---|
| Current text / state | `docs/requirements-decisions.md:6-7`: "Formal assessments retain the 60-minute **10MCQ/2SQL/1Essay** contract." Repeated at `:42` for the knowledge assessment. |
| Current code | `backend/app/services/blueprints.py:23-30` defines `THEORY_AREAS` (Performance, PostgreSQL Administration, PostgreSQL Concurrency, PostgreSQL Performance, PostgreSQL Security, PostgreSQL Server Programming). For those areas `desired_mix` (`:68-73`) returns `{"mcq": total - essay, "sql": 0, "essay": min(3, max(2, round(total/4)))}` - at `max_questions = 13` that is **10 MCQ / 0 SQL / 3 essay**. Non-theory areas keep the published 10/2/1 (`:74-80`). |
| Where it takes effect | Only for a **FORMAL** session whose selected concepts span exactly **one** subject area and whose assessment is blueprint-managed: `personalized_assessment.py:237-245` resolves the approved version and overwrites the frozen quotas. Mixed-area selections, unmanaged/historical assessments and the legacy full-session path keep 10/2/1 (`blueprints.py:191-209` returns `mode: "legacy"`; `adaptive_engine.py:389-412`; `assessment_validation.py:12-16` still enforces 60/13/10/2/1 for bank activation). Publication is what creates the rows: `assessment_service.py:224-231` calls `seed_blueprints` on the `published` transition. |
| Intentionality | The behaviour is deliberate and test-locked, not a regression: `backend/tests/test_assessment_blueprints.py:108-112` asserts `(10, 0, 3)` for theory areas and `(10, 2, 1)` otherwise; `:180-185` asserts the same for a resolved single-area selection. `blueprints.py:20-23` records the reason: a read-only SELECT sandbox "cannot honestly execute EXPLAIN, index DDL, configuration, backup, transaction-control or server-programming statements, so no SQL practical is scheduled for them". |
| Proposal | Choose one: **(a)** amend the requirement so the formal contract is stated as "60 minutes, 13 items, and a format mix per subject area, with executable SQL scheduled only where the read-only sandbox can measure the competency" (exact text: amendment **A4** below); **(b)** keep the 10/2/1 requirement literally and treat the 0-SQL blueprint rows as a defect to be corrected in code. Option (b) means changing application behaviour, which this task was not authorised to do. |
| If approved (a) | Amendment A4 is incorporated into the next Architecture / Proposal revision by the owner; `docs/requirements-decisions.md` gains a dated entry written **by the owner**; the repository diagrams already show the blueprint path, so no diagram change is required. |
| If declined | H1 stays as an open contradiction: `docs/requirements-decisions.md` and the shipped blueprint policy disagree for six subject areas that exist in the activated bank (PostgreSQL Administration ×6, Concurrency ×4, Performance ×4, Security ×3, Server Programming ×4 concepts, plus the benchmark `Performance` concept in `db/postgres_knowledge_pack.json` / `db/benchmark_pack.json`). Nothing in the repository changes; the code, the tests and `docs/activation-release-20261025.md:81-84` remain as they are. |

### H2 - blueprint approval provenance is technical, not academic

**PROPOSED - NOT APPROVED.**

Migration `013` rows are seeded by the system, so every one of the 49 blueprints on the activated
database carries `approved_by = NULL`. `docs/activation-release-20261025.md:82` already says this
plainly: "`approval_basis` is technical prose, not named academic approval", and that document's own
residual-gate list already numbers it as **gap 3**, "Named academic approval of the 49 blueprints", at
`:172`. `blueprints.py:93-114` shows the basis text is generated from the subject area. The figures and
the physical schema call these rows "approved".

- **Proposal:** either state in the academic document that question-mix policy is a **system-managed
  curriculum rule** (which is what the code does), or require a named approver and have an
  Administrator approve a new blueprint version through a human action.
- **Repository option, if the owner wants the provenance visible:** re-seed as a new immutable version
  with `approved_by` set to the Administrator account. This task did **not** do that - it would write
  to persistent data and would change an assessment contract, both outside its authority.
- **If declined:** no change. The word "approved" in the diagrams keeps its recorded technical
  meaning, which `docs/diagrams/assessment-lifecycle.json` and the `bpv` box label ("Approved
  blueprint version") already scope to "one area + band; immutable version".

### H3 - the system context figure does not show the translation provider call

**HELD - NOT APPLIED.** This is the only architecture view that was *not* updated, on purpose.

| Field | Detail |
|---|---|
| Current state | `docs/diagrams/system-context.svg` is hand-authored (the SVG is its own editable source, not generated from `.dot`) and its ledger records 51 flows. Provider flows `C16-C21` and `C28-C31` cover the four AI task families that existed on 23 October, but not opt-in question-translation drafts. |
| Code evidence | `backend/app/routers/admin.py:321-325` -> `backend/app/services/question_translation.py:122`, with withheld-span restoration in the same module; a fourth administrator-facing provider task, disabled by default (see `docs/draft-question-translation.md`). |
| Proposal | Add `C52 dbcas -> llm: "Question translation draft requests (opt-in)"` and `C53 llm -> dbcas: "Unpersisted translation drafts"`, exactly as recorded in `docs/diagrams/system-context.json` `revalidated_20261027.pending_proposal`. |
| Why held | Adding two arrows to the context figure is a presentation decision about an academically scrutinised artefact, not a factual correction. The alternative - stating that provider calls are enumerated at the container/component level - is also defensible, and is what `abstraction` in that ledger already argues. |
| If approved | The owner (or a task authorised to edit the SVG) adds the two flows and their evidence rows; `scripts/validate_diagrams.py` then checks them like every other flow. The 21 original flows stay protected either way. |
| If declined | The ledger keeps the recorded proposal as the audit trail; no flow is invented in the figure and the SVG stays byte-identical to the version reviewed on 23 October. |

### H4 - whether opt-in translation drafts deserve their own use case

**PROPOSED - NOT APPROVED.**

`docs/diagrams/use-cases.dot` still shows exactly 20 goals and 30 associations, and
`docs/diagrams/use-cases.json` `revalidated_20261027.translation_drafts` records that the translation
draft path was mapped as a *means* inside UC07 "Curate validated question bank" and UC08 "Review
AI-recommended question tags" rather than as a new goal.

- **Option (a), applied here:** treat preparation as a means; no new use case. Justification: nothing
  is persisted without the existing save/approval path, and the actor's goal is unchanged.
- **Option (b), requires a decision:** name a UC21 "Prepare question translation drafts" if the
  curriculum treats bilingual content preparation as an independent administrative goal with its own
  acceptance criteria.
- **If approved (b):** add one goal node plus learner/administrator associations to
  `use-cases.dot`, with `evidence` and `justification` in the ledger, then re-render.
- **If declined:** the current diagram is already correct under interpretation (a); no edit happens.

### H5 - the component label "configurable duration" is true of storage and not of the API

**PROPOSED - NOT APPROVED.**

`docs/diagrams/components.dot` line 8 and `components.json` node `s1` read "Assessment session service
/ Timer, auto-submit, configurable duration; max 13". The session window genuinely comes from the
per-assessment column (`models.py:320`, read at `adaptive_engine.py:410`, `batch_adaptive.py:108`,
`personalized_assessment.py:286`), so the label is not false. But the Administrator API cannot
currently choose a duration: `schemas.py:776-780` pins
`max_questions/duration_min/target_mcq/target_sql/target_essay` to `Literal[13/60/10/2/1]`, and
`assessment_validation.py:12-16` rejects any other formal configuration.

- **Proposal:** replace with "Timer, auto-submit, per-assessment window (fixed at 60 by configuration
  validation); 13-item cap" if the owner wants the figure to express the API constraint rather than
  the storage capability.
- **Why it was not simply edited:** the wording on 23 October was itself a deliberate correction -
  `components.json` `caption_corrections` records "60 minutes / 13 questions are baseline defaults and
  configured constraints, not every session duration". Narrowing it again would partially undo a
  reviewed correction, and that is an editorial judgement about what the figure is for.
- **If declined:** leave the label; the mismatch is already recorded as `PARTIALLY MATCHES` in the
  alignment matrix.

### H6 - eleven of the fifteen university deliverable categories have no DBCAS document

**PROPOSED - NOT APPROVED. Contents were not invented.**

`docs/documentation-alignment-20261027.md` §1 marked a standalone SRS, a UI design document, a test
plan / test case sheet / test report and a technical report as NOT FOUND. The workspace does contain a
university deliverable structure that explains why that matters: `FITAI - Documents/` has **15
numbered categories** - Proposal, Project Plan, Product Backlog, User Stories, Architecture Design,
Database Design, User Interface, Test Plan, Test Case, Sprint Backlog, Code Standard, Meeting
Minutes, Reflection, Technologies Stack, AI Documentation - and **every file in every one of those 15
folders is an example from other projects** (`C1SE.56_*SHFA*`, plus one `C1SE.56_FitnessAI_FNAI*`).
None is a DBCAS deliverable, which is why this task treated the folder as out of scope and modified
nothing in it.

| Category | DBCAS document present? |
|---|---|
| 1 Proposal, 4 User Stories, 5 Architecture Design, 6 Database Design | **yes** - the four root `C1SE.70_*` originals (v1.5 / v1.4 / v1.3 / v1.4) |
| 2 Project Plan, 3 Product Backlog, 7 User Interface, 8 Test Plan, 9 Test Case, 10 Sprint Backlog, 11 Code Standard, 12 Meeting Minutes, 13 Reflection, 14 Technologies Stack, 15 AI Documentation | **no DBCAS file found** - only another project's example |
| Software Requirement Specification as its own deliverable | **not part of this 15-category list**, so the earlier "standalone SRS NOT FOUND" is a correct finding rather than a gap |

- **Proposal:** the owner decides which of the eleven categories are actually required for C1SE.70
  submission, and in which form. For several of them the raw material already exists inside the
  repository (`docs/testing-and-release-gates.md`, `docs/phase-2-first-time-user-acceptance-20261026.md`
  and `docs/supervisor-implementation.md` for test evidence; `CONTRIBUTING.md` and `AGENTS.md` for
  code standards; the `npm run diagrams:setup` transcript for the technology stack; the dated
  activation records for meeting/reflection chronology).
- **What this task did not do and will not do:** draft those eleven deliverables. Producing academic
  submissions is authorship, not alignment, and it would replace "NOT FOUND" with invented content -
  explicitly prohibited by the task ground rules.
- **If declined:** the table above stands as the inventory result, and no repository change is needed.

---

## 2. Exact amendment text (for the owner's revision, not applied to any original)

Amendment ids continue the 23 October set (U1/U2, A1/A2, D1-D4, P1-P3) so the two records can be read
as one series. None of this text has been written into a Word or PDF original.

### A4 - formal assembly quota policy (Architecture v1.3 §4.2 and the assessment-configuration requirement)

> A formal assessment has a fixed 60-minute window and a 13-item ceiling. The format mix is resolved
> per subject area from an immutable, versioned assessment blueprint. Areas whose competency cannot be
> measured by executable read-only SQL are assessed through conceptual MCQ and rubric-scored written
> analysis, and receive no scheduled SQL practical; areas whose competency can be measured that way
> retain the published 10 MCQ / 2 SQL / 1 essay mix. Mixed-area and historical assessments use the
> published mix. A missing or retired blueprint cell is an actionable error, never a silent
> substitution.

### P4 - sandbox evidence limitation (Proposal v1.5, SQL assessment description)

> The learner SQL sandbox is read-only and self-contained. Statements that require configuration,
> index construction, execution-plan inspection, backup or recovery, lock observation across sessions,
> or server-side programming cannot be executed by a learner inside it, so those competencies are
> evidenced by conceptual and written items rather than by execution. This is a property of the
> approved sandbox policy, not a reduction of the assessed competency.

### U3 - translation draft preparation (User Stories v1.4, Administrator curation)

> Preparing a translation draft is an opt-in assistance action inside the existing curation story. It
> requires its own credential, is disabled by default, never approves machine output, and persists
> nothing until an Administrator performs the normal reviewed save. Manual translation remains a
> first-class path. Whether this action is a means or a separate use case is the owner's editorial
> decision (H4).

### D5 - schema caption and new tables (Database Design v1.4)

> The physical catalog is 34 tables with 49 foreign keys through migration 014. Migration 013 adds
> `assessment_blueprint` (immutable, versioned per assessment x subject area x difficulty band, with a
> nullable `assessment_session.blueprint_id` link) and migration 014 adds `adaptive_event` (one
> immutable round-and-decision row per batch adaptive step). The conceptual figure remains a domain
> subset; the generated physical figure, `docs/diagrams/schema-catalog.json` and the DDL are
> exhaustive, and the DDL is authoritative.

### C1 - context figure caption, only if H3 is approved

> Fifty-three individually evidenced external interactions are shown. All 21 flows of the original
> figure are retained; the additions cover OAuth profile exchange, role management, candidate
> curation, grading review, cumulative results and the opt-in translation-draft task. The figure is a
> detailed external-interaction view, not a minimal C4 Level 1 summary and not a sequence diagram.

---

## 3. Deliberate non-actions

Recorded so that the absence of a change is not mistaken for an oversight.

- No academic original (DOCX or PDF) was opened for writing; the `_docread/` extractions were read only.
- `system-context.svg` was not re-rendered or edited (H3 held); its 21 original flows are asserted
  unremoved by `scripts/validate_diagrams.py`.
- No requirement was deleted because the implementation differs; contradicted claims were marked
  `CONTRADICTS` in the alignment matrix and carried here.
- No code was altered to match a document. `git status` before and after shows no file under
  `backend/app/` or `frontend/src/`.
- No new microservice, queue, datastore, sequence diagram, DFD level or star schema was invented.
- `docs/requirements-decisions.md` was not touched (see the preamble).
- The dated records of 23-26 October were left intact as history rather than silently corrected; the
  current counts live in this cycle's documents.
- The 26 legacy content repairs in `docs/activation-release-20261025.md` remain unapplied; they are
  outside this task and still an editorial change-control decision.

---

## 4. Local commits created by this task

All work is committed locally on `main` as five small logical commits, in dependency order. **Nothing
was pushed, tagged, rebased or force-updated**; `origin` (`github.com/nguyendodary/DBCAS`) still points
at `633fea3`, so the local branch is ahead by exactly these five commits and the owner decides when or
whether that gap is published.

| # | Subject | Contents |
|---|---|---|
| 1 | `build: add the pinned diagrams-as-code toolchain` | `package.json`, `package-lock.json`, `.gitignore`, `scripts/diagrams.mjs`, `scripts/python.mjs`, `scripts/inventory.mjs`, `scripts/render_diagrams.mjs` (now a shim), `docs/diagrams/sources/`, `docs/diagrams/rendered/` |
| 2 | `build: generate the schema catalog, ERD and route inventories` | `scripts/generate_schema_catalog.py`, `scripts/generate_route_inventory.py`, `scripts/validate_diagrams.py`, `docs/inventory/`, and the regenerated `docs/diagrams/schema-catalog.json`, `physical-schema-relationships.json`, `physical-schema.dot`, `physical-schema.svg` |
| 3 | `docs(diagrams): align the eight authored architecture views with HEAD 633fea3` | the remaining changed `docs/diagrams/*.dot`, `*.json`, `*.svg` plus `docs/diagrams/README.md` |
| 4 | `docs: correct the living guides for routes, migrations and the help guide` | `README.md`, `CONTRIBUTING.md`, `docs/api-conventions.md`, `docs/setup-and-migrations.md`, `docs/learner-and-admin-manual.md` |
| 5 | `docs: record the 27 October alignment audit and academic proposals` | `docs/documentation-alignment-20261027.md`, this file |

Commit 2 keeps every generated artifact with the generator that produces it, so a reviewer can tell
Generated from Authored without reading two commits together. `system-context.svg` is absent from the
whole list - the hand-authored context figure was not touched (H3).

Deliberately **not** committed: nothing. Scratch artefacts were removed instead of ignored -
`scripts/_probe.dot`, `scripts/_tmp_usecase_evidence.mjs` and `.vitest-reports/` are gone, and the
on-demand PlantUML jar lives in the gitignored `tools/` rather than in history, per the rule against
committing large rendering binaries. Backups, logs and database dumps under `dbcas-db-backups/`,
`_extract/`, `_review/` and `output/` were never touched by this task and stay as they were.

---

## 5. What must not change without owner approval

| Artefact | Why it is protected |
|---|---|
| The four root `C1SE.70_*` DOCX/PDF originals and the 43 inventoried DOCX companions | academic deliverables; amendment text is proposed above instead of applied |
| Everything under `FITAI - Documents/` | other projects' files; not DBCAS work product |
| `docs/requirements-decisions.md` | it is the owner-approved decisions register; only the owner may add to it (H1, H2) |
| `docs/diagrams/system-context.svg` | hand-authored, academically scrutinised; the proposed C52/C53 flows await H3 |
| `docs/diagrams/use-cases.dot` goal set | 20 goals is a reviewed scope decision pending H4 |
| `docs/supervisor-implementation.md` historical test counts (§39 "189 tests", §416-418 "901 tests", §701-703 "928 tests") | executed-run records; rewriting them destroys evidence, so the current counts are stated in the audit document instead |
| The 21 original context flows, 8 original lifecycle transitions, 21 original schema tables / 28 original FK associations | the preservation rule; `validate_diagrams.py` fails if they disappear |
| Persistent development data and the `schema_migration` ledger | this task inspected read-only; blueprint re-seeding under H2 would be a write |

---

## 6. Verification pointers

`npm run diagrams:check` (exit 0), `npm run diagrams:render` (idempotent re-render), `npm run
inventory:check` (exit 0) and `node scripts/diagrams.mjs setup` (prerequisite report) are transcribed in
[documentation-alignment-20261027.md](documentation-alignment-20261027.md) §5 and §8. Each H item above
carries its own file:line citations, read at HEAD `633fea3`.
