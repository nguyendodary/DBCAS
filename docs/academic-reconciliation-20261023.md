# Academic document reconciliation - 23 October 2026

These are incorporation-ready **draft amendments**, reviewed against the current
working tree. They are not approved changes to academic requirements. The four
root originals were inspected again through their actual DOCX XML. All 43
inventoried DOCX originals remain protected by SHA-256 comparison. No original
Word/PDF file is overwritten by this deliverable.

## Document-by-document reconciliation

| Document | Current issue | Code / requirement evidence | Proposed correction | Status |
|---|---|---|---|---|
| User Stories v1.4, Admin 5 | Requires English canonical content and only optional Vietnamese translations | `QuestionUpsertRequest.original_locale`; `question_service`; migration 012; single editor | Amendment U1 below | READY draft; original unchanged |
| User Stories v1.4, learner preferences | Says question content follows session locale, without the new display projection | `sessions.get_session_state/get_session_evidence`; `adaptive_engine`; `ExamPage` | U2; distinguish recorded locale from visible reviewed snapshot prose | READY draft; owner acceptance required for this policy clarification |
| User Stories v1.4, personalized sessions and result release | Frozen plans and human verification already described accurately | `personalized_assessment`, `grading_review`, R1-R7 | Retain those requirements; reference the reviewed lifecycle figure | MATCH; no simplification of scoring/release |
| Architecture v1.3, UC07 main step 4 / alternative A2 | English-only source and rejection of English translations | `question_localization.translation_problems`; API original-language immutability | A1 below | READY draft; original unchanged |
| Architecture v1.3, UC12 | Full plan is frozen before question one; any easy-opening language must be scoped to legacy dispatch | `personalized_assessment`; `adaptive_engine.serve_next`; R1-R3 | A2 below; retain selected band, coverage and configured mix | READY clarification; do not replace personalized policy with legacy bias |
| Architecture v1.3, UC19 / interface preferences | Recorded locale immutability is correct; visible-content projection is missing | Session trigger, `evidence_context`, `display_locale` API | U2 wording, preserving the original immutable-session requirement | READY draft; original unchanged |
| Architecture v1.3, eight architectural figures | Earlier core scope, false candidate dispatch/repository names and network shorthand | [Complete relationship matrix](diagrams/semantic-review.md), [acceptance review](diagrams/acceptance-review-20261023.md) | Incorporate corresponding context/use-case/container/component/module/deployment/conceptual/physical companions and their captions; retain the detailed SVG/ledger links | READY companion set; original figures unchanged |
| Database Design v1.4, Question / table 28 | Missing original locale; translation locale/hash described as Vietnamese/English-specific | `db/schema.sql`; `012_question_original_locale.sql`; `source_fingerprint` | D1-D3 below | READY draft; persistent 012 still pending |
| Database Design v1.4, conceptual/physical figures | Figures are a core subset even though text acknowledges 32-table schema | Full catalog: 32 tables, 45 FKs; original 21 tables / 28 FKs retained | Caption D4; link exhaustive physical figure/catalog | READY; no invented entities or star schema |
| Proposal v1.5, context figure and actors | Detailed original flows are valid; separate OAuth providers and later review/role/candidate exchanges absent from figure | All 51 individually evidenced relationships in acceptance review | P1; retain every original flow; clarify detailed context abstraction | READY companion; C43 profile/email distinction corrected |
| Proposal v1.5, FR07/FR12 and assessment pipeline | Personalized frozen-plan requirements are current; pipeline must show distinct legacy, pending, failed, reviewed and publication branches | `assessment_lifecycle`, `grading_jobs`, `grading_review`, R1-R7 | A2/P2; preserve formal mix, exact practice length, timing and scoring | READY companion; requirements retained |
| Proposal v1.5, SQL sandbox description | “Disabled network access” can imply no backend connectivity; implementation uses separate restricted networks | `sandbox/Dockerfile`, both Compose files, `SandboxRunner`; SQL/security requirements | P3 below; retain no learner-controlled network/production access as a requirement | Runtime isolation NOT VERIFIED; do not waive the requirement |
| Supervisor R1-R8 notes | Original historical before/after statuses and past tests must remain historical | Current requirement/implementation matrix in bilingual report; source review above | Retain historical sections; dated acceptance link records new results and blocked gates | MATCH by source; standard runtime acceptance remains incomplete |
| README, manual, API, setup/deployment/testing guides | Must distinguish approved translation display, absent machine translation, pending activation and non-Docker checks | Current code and final acceptance evidence | Link latest acceptance and activation procedure; retain earlier dated reports | UPDATED current navigation; historical facts retained |
| Standalone formal SRS, UI Design, university Test Plan/Cases, current university Test Report, separate Technical Report | No available DBCAS original identified | Authorized workspace inventory; unrelated project documents excluded | None fabricated | NOT REVIEWED / unavailable |

## Exact amendment text

### U1 / A1 - question creation and reviewed translation

Administrators create a question in Vietnamese or English using one editor.
The editor infers recognizable prose and offers a simple language correction;
short, unaccented, mixed or code-only input may require that correction. Existing
originals cannot be relabeled. Original prompts, options and rubric criteria are
stored with their original content language. The other language is optional and
is maintained separately as a reviewed translation. Changing source prose or
grading criteria can invalidate the translation; it is not silently reapproved.
Missing or stale translations never prevent saving an original-only draft.
Question validation/publication still enforces concepts, difficulty, answer keys,
SQL fixtures and grading criteria. A translation targeting the original language
is rejected; an English translation of a Vietnamese original is permitted.

Acceptance follow-up: optional machine draft preparation is now implemented,
disabled by default under a separate opt-in. General LLM credentials for existing
grading/curation tasks do not enable it or establish translation approval. A
prepared draft stays in the editor and is not official assessment content until
an Administrator reviews it and performs the normal save. Manual translation
remains available. See [the exact draft contract](draft-question-translation.md);
live-provider verification is not claimed. This updates the amendment text only,
not any original academic Word/PDF file.

### U2 - preferences and historical assessment language

The language selector changes menus and visible question content. Reviewed
translations captured with the assessment question may be displayed in the
chosen interface language. If absent, the original appears with a clear language
indicator. The recorded session locale, answer IDs, SQL code, datasets, scoring,
captured question content and official grading narrative remain unchanged.
Personalized plans capture content before question one; legacy sessions capture
an item when served. Later bank changes do not retrofit a captured assessment.
Legacy evidence without a captured question snapshot uses its known original,
not a newer bank translation. Normal session timeout finalization still applies
to session reads. Language switching does not restart the clock or clear drafts.

### A2 / P2 - assembly and publication

Personalized formal/practice assembly freezes a complete validated question plan
covering all selected skills and the selected difficulty band, with no repeated
version family. Preserve formal 13 questions / 60 minutes / 10 MCQ, 2 SQL, 1 essay
and the configured exact practice lengths. The three easy opening MCQs and
subsequent performance bias belong to the legacy adaptive path, not a mandate to
override a learner-selected personalized band. Submission, pending/failed bounded
grading, authorized human verification/manual takeover, reviewed and published
states remain distinct. IMMEDIATE release waits for usable automatic grades;
HUMAN_VERIFIED release requires the prescribed reviews and explicit publication.
Cumulative competency uses published evidence and existing scoring weights.

### D1-D4 - source storage, translations and schema caption

- Question adds `original_locale VARCHAR(16) NOT NULL DEFAULT 'en'`, constrained
  to `en` or `vi`. Existing source values retain the English default; 012 does not
  rewrite prompts or infer historical language.
- QuestionTranslation is reviewed display prose keyed by question and locale.
  The existing locale-format check and indexes remain. English translations are
  permitted; the API requires the translation locale to differ from the source.
  Option labels and rubric level keys remain stable; SQL datasets, executable
  answers and score boundaries remain source technical data.
- `source_hash` binds translated content to the source content version. Existing
  English-source hashes remain compatible. Vietnamese source hashes additionally
  bind source locale. New snapshot version 3 records original locale; historical
  snapshots are not backfilled. Read-only bank `localized_prompts` is an API
  projection, not another database column or a replacement canonical prompt.
- The conceptual figure shows the core domain and original keys. The linked
  physical model/catalog supplies all 32 current application tables and 45 FKs,
  including prepared migration 012. The migration bookkeeping table is created
  by the runner and is outside that fresh application-schema count. These
  diagrams describe the prepared revision, not persistent migration activation.

### P1 - context caption

Detailed external-interaction context for DBCAS. All 21 original directional
relationships are retained, with 30 implemented additions and separate optional
Google/GitHub providers. The diagram is not a chronological sequence or a minimal
C4 Level 1 summary. OAuth browser redirects/callbacks and server token/profile/
verified-email exchanges are retained as explicit detail. GitHub profile/user ID
is separate from verified email. Internal databases, sandbox, services and
deployment topology appear in their corresponding companion views. Provide the
SVG and ledger links alongside any reduced printed figure.

### P3 - sandbox requirement clarification

The learner executes validated SELECT statements through a restricted read-only
role in a separate PostgreSQL sandbox. Privileged dataset setup is backend-only;
the learner query uses its own bounded transaction with timeout, result limits
and rollback. Preserve the requirement for no learner-controlled network access
and no access to system/production data. The backend necessarily connects to the
sandbox over its dedicated network. Development uses separate bridges with
masquerade disabled; release uses separate internal networks. These configuration
facts do not by themselves prove runtime isolation. PostgreSQL 17 Docker sandbox
and network acceptance must pass before claiming that requirement verified.

## Incorporation status

Each text block is ready for owner/academic review and incorporation into a
separately revised deliverable. READY does not mean already incorporated,
supervisor-approved or fully runtime-verified. No new Word/PDF was supplied, and
no original diagram or historical test report was rewritten. See the
[final acceptance report](final-integration-acceptance-20261023.md) for remaining
environment, translation and activation gates.
