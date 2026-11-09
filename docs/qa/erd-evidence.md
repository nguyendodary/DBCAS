# ERD relationship evidence (figure 09, owner fix round F5)

Sources of truth, in order:

1. `db/schema.sql` (PostgreSQL 17 schema, lines cited below).
2. `docs/qa/schema-introspection.json` — PostgreSQL 17.11 introspection:
   **41 tables, 293 columns, 59 foreign keys** (also recorded in
   `docs/qa/rebuild-preview/trd/report.md`).
3. Stage A trace `docs/diagrams/rebuild/erd/stage-a/spec-stage-a.json`
   (17 entities, 24 diamonds, 17 keys, 120 connector segments, 112 labels).

No relationship below is inferred from a name alone.  Each row names the
actual FK/constraint; the cardinality is derived from the PK/UNIQUE/NULL
declarations, not from the verb.

## Kept original relationships (24)

| Relationship | FK / constraint (table.columns → table.columns) | Cardinality derivation | Status |
| --- | --- | --- | --- |
| assigned | `account_role.account_id → account.account_id`; `account_role.role_id → role.role_id`; PK(`account_id`, `role_id`) — schema.sql 23–28, 270–271 | PK is the pair, neither column unique alone → Account **M:N** Role | kept |
| has | `user_profile.account_id → account.account_id`, `NOT NULL UNIQUE` — 30–37, 272 | `account_id` UNIQUE → Account **1:1** UserProfile (0..1) | kept |
| defines | `course_learning_outcome.created_by → account.account_id`, NOT NULL — 50–58, 274 | One creator per CLO; an account creates many CLOs → Account **1:N** CLO | kept |
| configures | `assessment.created_by → account.account_id`, NOT NULL — 162–176, 285 | One creator per assessment; an account creates many → Account **1:N** Assessment | kept |
| authors | `question.created_by → account.account_id`, NOT NULL — 91–105, 279 | One author per question; an account authors many → Account **1:N** Question | kept |
| graded by | `rubric.question_id → question.question_id`, NOT NULL — 152–160, 284 | A question has many rubric levels; each rubric row belongs to one question → **Question 1:N Rubric** (drawn Rubric→Question) | kept |
| tested by | `sql_test_dataset.question_id → question.question_id`, NOT NULL — 143–150, 283 | A question has many datasets; each dataset belongs to one question → **Question 1:N SQLTestDataset** | kept |
| takes | `assessment_session.learner_id → account.account_id`, NOT NULL — 190–200, 289 | One learner per session; an account takes many sessions → Account **1:N** Session | kept |
| seeds | `question_candidate.concept_id → concept.concept_id`, NOT NULL — 259–268, 299 | One concept per candidate; a concept seeds many candidates → Concept **1:N** QuestionCandidate | kept |
| promoted to | `question_candidate.promoted_question_id → question.question_id`, NULL, **UNIQUE** — 266, 300 | UNIQUE → each candidate promotes to at most one question; NULL for un-promoted → **QuestionCandidate 1:0..1 Question** | kept |
| instantiates | `assessment_session.assessment_id → assessment.assessment_id`, nullable since migration 018 — 190–200, 288, 872 | One assessment per session; many sessions per assessment → Assessment **1:N** Session | kept |
| tagged with | `question_concept.question_id → question.question_id`; `question_concept.concept_id → concept.concept_id`; PK(`question_id`, `concept_id`) — 107–114, 280–281 | Pair PK, both sides many → Question **M:N** Concept | kept |
| maps to | `clo_concept.clo_id → course_learning_outcome.clo_id`; `clo_concept.concept_id → concept.concept_id`; PK(`clo_id`, `concept_id`) — 70–77, 275–276 | Pair PK → CLO **M:N** Concept | kept |
| targets | `assessment_concept.assessment_id → assessment.assessment_id`; `assessment_concept.concept_id → concept.concept_id`; PK(`assessment_id`, `concept_id`) — 178–188, 286–287 | Pair PK → Assessment **M:N** Concept. This is also the legacy **AssessmentConcept** junction table (see note below) | kept |
| chosen in | `selection_log.question_id → question.question_id`, NOT NULL — 217–226, 294 | A question can be logged in many selection rows; each row has one question → Question **1:N** SelectionLog | kept |
| offers | `mcq_option.question_id → question.question_id`, NOT NULL — 116–122, 282 | A question has many options; each option belongs to one question → Question **1:N** MCQOption | kept |
| logs | `selection_log.session_id → assessment_session.session_id`, NOT NULL — 217–226, 293 | A session has many selection rows; each row belongs to one session → Session **1:N** SelectionLog | kept |
| answered in | `attempt.question_id → question.question_id`, NOT NULL — 202–215, 291 | A question is answered in many attempts; each attempt has one question → Question **1:N** Attempt | kept |
| selected in | `attempt.selected_option_id → mcq_option.option_id`, NULL — 207, 292 | Each attempt selects at most one option; an option is selected in many attempts → MCQOption **1:N** Attempt (optional) | kept |
| measured by | `concept_competency.concept_id → concept.concept_id`, NOT NULL — 228–238, 296 | A concept has many competency rows; each row is one concept → Concept **1:N** ConceptCompetency | kept |
| yields | `concept_competency.session_id → assessment_session.session_id`, NOT NULL — 228–238, 295 | A session yields many competency rows; each row is one session → Session **1:N** ConceptCompetency | kept |
| flags | `competency_gap.session_id → assessment_session.session_id`, NOT NULL — 240–248, 297 | A session has many gaps; each gap is one session → Session **1:N** CompetencyGap | kept |
| diagnosed in | `competency_gap.concept_id → concept.concept_id`, NOT NULL — 240–248, 298 | A concept appears in many gaps; each gap is one concept → Concept **1:N** CompetencyGap | kept |
| records | `attempt.session_id → assessment_session.session_id`, NOT NULL — 202–215, 290 | A session records many attempts; each attempt is one session → Session **1:N** Attempt | kept |

## Added relationships (4)

| Relationship | FK / constraint (table.columns → table.columns) | Cardinality derivation | Status |
| --- | --- | --- | --- |
| updates | `system_setting.updated_by → account.account_id`, NULL — schema.sql 873–878, introspection `system_setting_updated_by_fkey` | `setting_key` is the PK; one updater (0..1) per setting; an account updates many settings → Account **1:N** SystemSetting | added |
| pools | `assessment_question.assessment_id → assessment.assessment_id`, NOT NULL — 864–869, introspection `assessment_question_assessment_id_fkey`; PK(`assessment_id`, `question_id`) | Many pool rows per assessment, one assessment per row → Assessment **1:N** AssessmentQuestion | added |
| versions | `assessment_blueprint.assessment_id → assessment.assessment_id`, NOT NULL — 768–804, 807–808; UNIQUE(`assessment_id`, `subject_area`, `difficulty_band`, `version_no`) | Many blueprint versions per assessment; each row belongs to one assessment → Assessment **1:N** AssessmentBlueprint | added |
| uses | `assessment_session.blueprint_id → assessment_blueprint.blueprint_id`, NULL — 807–808, introspection `assessment_session_blueprint_id_fkey` | One blueprint (0..1) per session; one blueprint can be used by many sessions → Session **N:1** AssessmentBlueprint | added |

### Junction association (not a diamond)

| Association | FK / constraint (table.columns → table.columns) | Cardinality derivation | Status |
| --- | --- | --- | --- |
| retained `targets` diamond ↔ `AssessmentConcept` table | `assessment_concept.assessment_id → assessment.assessment_id`; `assessment_concept.concept_id → concept.concept_id`; PK(`assessment_id`, `concept_id`) — schema.sql 178–188, 286–287 | Each junction row is one (assessment, concept) pair; the conceptual relation is the original Assessment **M:N** Concept `targets` diamond. The line is a table annotation, not a second relationship and not a new verb; it is labelled `assessment_concept` / `junction` in the drawing. Path: (900,1000) → (900,800) → (990,800) → (990,752) → targets left vertex (1019,752). | added (association only) |

## Removals (0)

No original Stage A entity, key ellipse, diamond or connector was removed.
The final spec keeps all 17/17 entities, 17/17 key ellipses, 24/24
original diamonds and 120/120 original connector segments.  Proof:
`docs/qa/rebuild-preview/erd/delta-f5.txt` (exact bbox/name/label/segment
comparison) and `docs/qa/rebuild-preview/erd/overlay-stage-a-final.png`.

The previous Stage B had dropped five original entities and nine original
relationships.  This round restores them.  The exact evidence they still
exist in the schema:

| Previously dropped item | Evidence it still exists | Restored as |
| --- | --- | --- |
| Rubric entity | `rubric` table, schema.sql 152–160; `rubric_question_id_fkey` | original `Rubric` slot + `graded by` diamond |
| QuestionCandidate entity | `question_candidate` table, 259–268; FKs `concept_id`, `promoted_question_id` | original slot + `seeds` / `promoted to` |
| SQLTestDataset entity | `sql_test_dataset` table, 143–150; `sql_test_dataset_question_id_fkey` | original slot + `tested by` |
| SelectionLog entity | `selection_log` table, 217–226; FKs `session_id`, `question_id` | original slot + `chosen in` / `logs` |
| LLMCache entity | `llm_cache` table, 250–257 (standalone, no FK in the original either) | original slot + `cache id` |
| `graded by` | `rubric.question_id` FK | kept (original routing) |
| `tested by` | `sql_test_dataset.question_id` FK | kept (original routing) |
| `authors` | `question.created_by` FK | kept (original routing) |
| `promoted to` | `question_candidate.promoted_question_id` FK/UNIQUE | kept (original routing) |
| `seeds` | `question_candidate.concept_id` FK | kept (original routing) |
| `maps to` | `clo_concept` PK/FKs | kept (original routing) |
| `chosen in` | `selection_log.question_id` FK | kept (original routing) |
| `logs` | `selection_log.session_id` FK | kept (original routing) |
| `answered in` | `attempt.question_id` FK | kept (original routing) |

## Rejected additions / naming decisions

| Candidate | Decision | Evidence / reason |
| --- | --- | --- |
| `requires` (Concept–Concept) | **not added** | `concept_dependency` exists, but this diamond is not part of the Stage A figure or the owner's allowed additions. It is not needed and would be an invented addition to this figure. |
| core `versions` (Question self-FK) | **not added** | `question.family_id` exists, but the owner asked for the original figure plus the specified additions, not new core diamonds. |
| duplicate `targets` (Assessment–AssessmentConcept) | **not added** | The owner explicitly forbids a duplicate `targets`. The original `targets` diamond is already the `assessment_concept` junction (`assessment_id` + `concept_id`), so AssessmentConcept is joined to that retained diamond by a short labelled junction association instead. |
| `holds` | **not added** | Not in the owner's allowed original/add list. Its only possible FK is `assessment_concept.assessment_id`, already represented by the retained `targets` diamond; adding a second diamond for the same junction would duplicate the semantics. |
| `pools`/`versions` between AssessmentQuestion and AssessmentBlueprint | **not drawn** | No FK exists between `assessment_question` and `assessment_blueprint` in schema.sql or the 59-FK introspection. |

## Conclusion

- Original relationships: **24 kept, 0 removed**.
- Added relationships: **4** (`updates`, `pools`, `versions`, `uses`).
- Final diamonds: **28**.
- Junction associations: **1** (retained `targets` diamond ↔
  AssessmentConcept); it is not a diamond and carries no cardinalities.
- AssessmentConcept is a legacy junction table shown with its composite key
  and `LEGACY` tag; its assessment/concept FKs are the retained original
  `targets` diamond, joined by one short labelled junction association —
  not a second diamond and not a new relationship verb.
