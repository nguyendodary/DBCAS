# DBCAS Verified Content Activation and Development Release

**Date:** 2026-10-25 (UTC+7)  
**Scope:** Authoritative verification of 271 staged questions, Vietnamese translation import, migration 013 and the 49 assessment blueprints on the persistent development database, post-activation testing, and Git synchronization.  
**Environment:** Development only (`127.0.0.1:5435/dbcas`). Production was not touched, and no university documentation was modified.

## 1. Release decision and authorization boundary

The persistent development database is now activated: migration 013 is applied, 271 technically accepted questions are imported with current Vietnamese translations, and 49 versioned blueprints are seeded. Every historical row was preserved byte-for-byte, and all release gates listed below pass.

This release does **not** claim human or academic approval. Technical acceptance (`question.status = validated`, produced by the production validation service including SQL Sandbox execution) is distinct from instructor review. No person's identity was written into `approved_by`; no reviewer was invented; no translation is labelled human-reviewed.

Authorized and completed:

1. Independent source-based verification of staged questions.
2. Automated technical acceptance with recorded provenance.
3. Vietnamese translation validation and import.
4. Migration 013 on the persistent **development** database.
5. Import of validated questions and blueprints.
6. Post-activation integration, API smoke and four-browser E2E testing.
7. Logical Git commits and a normal push to `origin/main`.

Explicitly not done: fabricated human approval, edits to retired Q5, deletion or rewriting of historical rows, production deployment, force-push, or test weakening.

| Gate | Result |
|---|---|
| 271 staged questions verified | 204 VERIFIED, 67 VERIFIED_WITH_QUALIFICATION, 0 rejected |
| 271 questions technically accepted | Pass; 271/271 `validated`, 0 failures |
| Vietnamese translations current | 271/271 current; labelled machine-verified, not human-reviewed |
| Blueprints seeded and validated | 49/49 (4/6/9/30), `approved_by = NULL` |
| Backup, restore and rollback drill | Pass; exact pre-activation restore verified |
| Migration 013 on persistent dev | Pass; checksum matches, historical data unchanged |
| Import + idempotent rerun | First run 271 created; rerun 0 created / 271 skipped |
| Blueprint coverage | 49/49 blueprinted cells; 0 deficits in blueprinted cells |
| Assembly simulation | 245/245 formal and 245/245 practice runs |
| Backend tests | 1,038 passed, 1 dependency warning |
| Frontend unit tests | 267/267 passed (33 files) |
| Release E2E, four browsers | 43/43 each on Chromium, Firefox, WebKit, Edge |
| Application E2E, four browsers | 10/10 each on Chromium, Firefox, WebKit, Edge |
| Human content approval | **Not obtained** |
| Human translation approval | **Not obtained** |
| Named blueprint approval | **Not obtained** |

## 2. Authoritative verification of the 271 questions

All 271 staged questions were reviewed against the archived PostgreSQL 17 documentation, Watt's *Database Design* (2nd edition, Open Textbook Library) and the Codd 1971 normalization paper, with short supporting quotations recorded per verdict.

- Verdicts: **204 VERIFIED**, **67 VERIFIED_WITH_QUALIFICATION**, **0 rejected**.
- Coverage: 15 subject areas, 71 concepts, 376 confirmed question–concept links.
- Provenance: 463 source references, 1–4 per question; 393 `www.postgresql.org`, 35 `open.umn.edu`, 24 `dblp.org`, 11 `doi.org`.
- Type mix: 199 MCQ, 31 SQL, 41 essay; difficulty 1–5: 9/89/77/78/18.
- Structural checks: 199/199 MCQ have four options and exactly one correct answer; 41/41 essays have four rubric bands spanning 0–5; 31/31 SQL questions have sandbox-derived expected results and edge-case datasets.

The 67 qualifications are predominantly provenance precision (23 incomplete source refs, 22 incorrect refs, 15 section mismatches, 10 broken URLs). Eight qualified questions also had content or explanation issues; each carries a recorded correction and was revalidated. Five substantive defects were fixed before import:

1. Q574 — invalid `ON CONFLICT ON CONSTRAINT` for a unique expression index.
2. Q594 — incorrect `websearch_to_tsquery` negation precedence.
3. Q625 — explanation counted two payments where the scenario defines three.
4. Q573 — absolute `RETURNING` claim scoped correctly to PostgreSQL 17.
5. Answer-position bias — correct option was A in 166/199 MCQs; normalized to 50/48/50/51.

All 271 were then validated again through the production service during import; no question failed. Verdicts and citations are committed under `_content/expansion-20261024/evidence/verification_20261025/verdicts/`.

## 3. Vietnamese translations

- 271/271 questions have Vietnamese prompt and explanation; 199 have translated option sets and 41 have translated rubric bands.
- Drafts were merged into `generated/translations_vi_pending.json` (271 keyed entries, `pending_human_review`, `imported = false`).
- Import used the production `upsert_question_translations`, which recomputes `source_fingerprint` and validates option/rubric key correspondence against canonical content.
- Post-import: **271 current**, **0 stale**; `generated/translations_vi_activated.json` records `review_status = machine_verified_not_human_reviewed` and `human_reviewed = false`.

SQL identifiers, fixtures and executable structure were preserved; MCQ option keys follow the deterministic normalization hash, and rubric keys remain the canonical level names. Terminology and semantic fidelity were machine-checked and spot-checked, **not human-approved**.

This activation therefore publishes machine-verified translations into the development bank without representing them as human-reviewed.

## 4. Assessment blueprints

Migration `013_assessment_blueprints.sql` adds the immutable `assessment_blueprint` table, a nullable `assessment_session.blueprint_id`, and the `assessment_blueprint_immutable` trigger. It is additive and does not rewrite historical sessions.

- 49 blueprints: assessment 2 → 4, 3 → 6, 4 → 9, 6 → 30.
- Bands: 17 EASY, 17 MEDIUM, 15 HARD; version 1 across all cells.
- Every row satisfies `target_mcq + target_sql + target_essay = max_questions`.
- All rows have `status = approved` from the system seed and `approved_by = NULL`; `approval_basis` is technical prose, not named academic approval.
- Runtime resolution was exercised: single-area MEDIUM selections resolve to a blueprint; mixed-area selections and unmanaged assessments use legacy quotas; a missing assessment/band cell raises `blueprint_not_available` (422).
- The immutability trigger rejects updates to seeded rows; versions are appended, never mutated.

Coverage on the activated database: **49 of 51** assessment × area × band cells are blueprinted with zero deficits. The two unblueprinted cells are assessment 2 Performance/HARD and Querying/HARD; their target concepts are capped at difficulty 3, so they are not selectable. Formal coverage is therefore 49/49 for selectable blueprint cells.

## 5. Legacy content handling

The legacy repair set contains **26 validated questions** (IDs 2, 3, 4, 6–27 and 450): explanatory text, tags and source references. It was validated against live rows but **was not applied to the persistent database**, because the release authorization does not cover rewriting historical content.

- Retired Q5 was removed from the repair specifications and a retired-row guard was added to `repair_existing.py`.
- Persistent Q5 remains untouched and retired (no explanation, no references, no tags).
- Persistent NULL explanations: 27 rows = 26 validated repair candidates + retired Q5.
- The 26 repairs remain proposals with validation evidence; applying them is a separate editorial change-control decision.

The release therefore preserves historical rows rather than silently improving them.

## 6. Backup, restore and rehearsal evidence

- Pre-activation dump: `_content/expansion-20261024/backups/persistent_pre_activation_20261025T102836.dump`, 337,188 bytes, SHA-256 `ccb8dbfb83a8cc454b3964fbb3e10bc297499c2a10eabcfb88a13aa33ae8bf1b`; a `.sha256` sidecar is present.
- The dump was restored into a fresh disposable database and compared table-by-table, sequence-by-sequence and ACL-by-ACL: 33 tables, 12 migrations, latest 012, **no differences**, migration checksum problems 0.
- A second restore reproduced the rollback point exactly: 442 questions (max ID 450), 18 sessions, 109 attempts, 109 selection-log rows, 442 translations, no blueprint table and no `blueprint_id` column.
- Migration checksums are compared using the same LF-normalized SHA-256 that `app.migrate` computes, avoiding false CRLF mismatches.
- Clean rehearsal on `dbcas_rehearsal_final`: 271 created, 271 translated, 49 blueprints, historical rows unchanged, 0 failures. Rerun: 0 created, 271 skipped, 0 failures.
- Rehearsal verification passed with no problems, including 271 current translations, 49 blueprints and zero historical-session blueprint bindings.

No destructive restore was executed against the persistent database. The dump is the tested rollback point and is retained locally outside Git because it contains account data.

## 7. Persistent development activation

Executed on `127.0.0.1:5435/dbcas` only.

1. **Migration 013** applied at `2026-10-25T10:38:17Z`; ledger now has 13 migrations. Applied checksum `d86406549986133cf237287a509ef6e7b50e9d50faef00d7c66e596587061fb2` matches the repository file. Table, nullable column and immutability trigger are present.
2. **Question import** through `_content/expansion-20261024/activate_dev.py`, guarded by `--confirm` plus the verified backup path and SHA-256. Results: 271 created, 271 translated, 0 failures; 49 blueprints seeded; historical rows unchanged; verdict pass.
3. **Idempotent rerun** with the same command against the persisted activation manifest: 0 created, 271 skipped, 271 translations still current, 0 new blueprints, historical rows unchanged; verdict pass.
4. **Post-activation verification**: 713 questions (max ID 721), 713 translations, 49 blueprints, 18 sessions, 109 attempts and 109 selection-log rows. Historical digests for questions ≤ 450, Q5, sessions, attempts, selection log and translations ≤ 450 are identical to the pre-activation baseline. All 271 staged rows are `validated`, `original_locale = en`, non-empty explanation, with source references; type mix 199/31/41; all 271 Vietnamese translations current; zero historical sessions bound to a blueprint.

IDs 451–721 were assigned in specification order, which differs from the canonical staging manifest order. This is the documented import constraint: the activation manifest is the authoritative key → question-ID map, and translations/reviews are resolved by JSON key, never by a stored canonical ID. All 271 prompt hashes were checked before creation; no drift.

## 8. Post-activation integration and acceptance

**Coverage and assembly (persistent database)**

- 49 blueprinted cells, zero deficits in blueprinted cells.
- Formal assembly: **245/245** runs passed concept coverage, exact type quotas and distinct-family selection.
- Practice assembly: **245/245** runs passed the same checks.
- 56 concepts still have fewer than three families in at least one band; this is a practice-depth roadmap item, not a formal blocker.

**Live read-only API smoke (`127.0.0.1:8010`, real dev DB and sandbox)**

- `/health` → `ok`; `/readiness` → `ready` with database and sandbox true.
- Learner assessments 2, 3, 4 and 6 are available.
- Concept graph: 82 nodes, 49 edges.
- Validated bank: 525 MCQ, 98 SQL, 89 essay (Q5 is the one retired essay).
- Imported questions 451 (MCQ, difficulty 2), 586 (essay, difficulty 2) and 721 (essay, difficulty 3) are served as validated English-origin content.
- Translation capability reports unavailable because the separate translation LLM opt-in remains disabled; imported translations are unaffected.

**Unit and component suites**

- Backend: **1,038 passed**, 1 dependency deprecation warning, 521.12 s.
- Frontend: **267 passed / 33 files**, 49.43 s.

**Browser E2E (disposable fixture containers; persistent dev unchanged before and after)**

| Engine | Release suite | Application suite |
|---|---|---|
| Chromium | 43/43, 17.9 min | 10/10, 3.8 min |
| Firefox | 43/43, 23.2 min | 10/10, 4.1 min |
| WebKit | 43/43, 24.9 min | 10/10, 4.6 min |
| Edge | 43/43, 18.1 min | 10/10, 3.8 min |

Zero unexpected, skipped or flaky tests in all eight runs. Results and logs are under `_review/release-20261025/` (`browser-results-<engine>.json` and `application/browser-results-<engine>.json`), which is intentionally outside Git. Automated axe checks are accessibility evidence, not WCAG certification.

The browser suites run against isolated fixture databases and identities; they do not log into the persistent development database. The activated data itself is covered by the database verification, coverage/assembly simulations and the read-only API smoke above.

## 9. Git release, residual gaps and rollback

**Git**

- `fc292d1` — chore(repo): keep local database snapshots out of Git.
- `b9a164c` — feat(blueprints): version assessment evidence mixes and session binding.
- `3f43146` — feat(content): add verified 271-question bilingual bank and activation tooling.
- A final docs commit publishes this report and the corrected legacy-repair count (26, with Q5 excluded).

These commits add source, tests, migration, staging specifications, translations, activation manifests and verified evidence. Database dumps and raw logs remain local by policy because dumps contain account data. Normal push to `origin/main` is performed after the release gates; no history was rewritten or force-pushed.

**Residual approval gaps (blocking human publication, not technical activation)**

1. Named human review/sign-off of the 271 questions, including the five repairs.
2. Human review of all Vietnamese content: 271 prompts/explanations, 199 option sets, 41 rubrics.
3. Named academic approval of the 49 blueprints (`approved_by` is NULL by design).
4. Decision on applying the 26 legacy repair proposals; historical rows remain untouched.

**Rollback**

The verified `persistent_pre_activation_20261025T102836.dump` restores the exact pre-activation state (migration 012, 442 questions, 18/109/109 activity, 442 translations, no blueprint table). That restore was proven twice in disposable databases. Migration 013 is additive and does not rewrite historical rows; nevertheless any real rollback of the persistent database requires explicit authorization, quiescing writers and a fresh safety dump. No automatic or destructive restore was performed.

**Release boundary**

This is a verified **development** activation. It does not deploy to production, does not modify university academic documentation, does not weaken SQL Sandbox controls, and does not change the AI model or OAuth configuration. The 271 questions are technically accepted and active in development; they are not represented as human-approved academic content, and the 49 blueprints are technically seeded, not academically approved.

## Evidence index

- `_content/expansion-20261024/evidence/verification_20261025/` — verdicts (271), repair proposals (26), blueprints (49), resolution checks, restore/rollback verification, activation baseline, final activation verification and API smoke.
- `_content/expansion-20261024/evidence/activation_import_report*.json` — rehearsal, persistent first run and idempotent rerun.
- `_content/expansion-20261024/evidence/coverage_persistent_post_activation.json` — 49/49 blueprinted coverage.
- `_content/expansion-20261024/evidence/assembly_simulation_persistent_post_activation.json` — 245/245 formal and practice runs.
- `_content/expansion-20261024/generated/activation_manifest.json` — authoritative key → question-ID map.
- `_content/expansion-20261024/generated/translations_vi_activated.json` — machine-verified translation record, not human-reviewed.
- `_content/expansion-20261024/backups/` — local verified dumps and checksum sidecars (not committed).
- `_review/release-20261025/` — four-browser release/application E2E JSON and logs (local, outside Git).
