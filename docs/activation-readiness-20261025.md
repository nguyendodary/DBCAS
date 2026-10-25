# DBCAS Activation Readiness Report

**Date:** 2026-10-25 (UTC+7)  
**Scope:** 49/49 blueprint implementation and the 271-question bilingual expansion, prepared for controlled activation.  
**Mode:** Evidence-based review; persistent database intentionally not mutated.

**Status note:** This is the pre-activation snapshot. Persistent activation was later authorized and completed; see `docs/activation-release-20261025.md`.

## Verdict

The implementation and staged content are technically ready for a controlled activation rehearsal, and the post-activation state has been proven by restoring a verified dump. They are **not yet ready for persistent activation** because human content/translation approval, named blueprint approval, and explicit authorization to mutate the persistent database are still missing.

No migration or import has been applied to the persistent database. Git has not been committed or pushed.

| Gate | State |
|---|---|
| 49/49 blueprint coverage and assembly | Pass (245/245 formal and practice simulations) |
| 271 staged questions structurally valid | Pass |
| 31/31 SQL expected results sandbox-verified | Pass |
| 271 Vietnamese drafts complete | Pass structurally; human review pending |
| Migration 013 + import + rollback on disposable clone | Pass |
| Post-activation dump restore | Pass (exact counts) |
| Persistent activation authorized | Not granted |
| Human content approval | Not performed |
| Human translation approval | Not performed |
| Named blueprint approval | Not performed (`approved_by` is NULL on all 49) |

---

## 1. Git, database, and runtime state

**Git**

- Nested repository: `DBCAS/`; branch `main`; HEAD `66c9401`.
- 15 working-tree entries: 10 modified files and 5 untracked paths; no commit, push, reset, or history rewrite.
- Modified: `backend/app/models.py`, `backend/app/repositories.py`, `backend/app/services/assessment_service.py`, `backend/app/services/personalized_assessment.py`, `backend/requirements.txt`, `backend/tests/conftest.py`, `backend/tests/release_server.py`, `backend/tests/test_final_acceptance.py`, `backend/tests/test_migrations.py`, `db/schema.sql`.
- Untracked: `_content/`, `backend/app/seed_blueprints.py`, `backend/app/services/blueprints.py`, `backend/tests/test_assessment_blueprints.py`, `db/migrations/013_assessment_blueprints.sql`.
- `_content` is the staging/evidence tree; it is not a second question bank.

**Persistent PostgreSQL (`127.0.0.1:5435`, database `dbcas`)**

- 12 migrations, latest `012_question_original_locale.sql`.
- 442 questions (max ID 450), 18 assessment sessions, 109 attempts, 109 selection-log rows, 442 translations.
- No `assessment_blueprint` table and no `assessment_session.blueprint_id` column.
- 26 validated questions still have NULL explanations (including Q2, Q3, Q4); this matches the un-applied legacy repair set. Q5 is retired with no explanation and is excluded from that set and from all repairs.
- Re-checked after all regression and E2E runs: unchanged.

**Disposable clone after the activation drill**

The original clone container's `dcas_clone` catalog row became unreachable by name (`FATAL: database "dcas_clone" does not exist`) although the catalog row and data directory exist. This is isolated to the disposable clone container; the persistent database is healthy. To avoid relying on the anomalous catalog entry, the verified post-activation dump was restored into a fresh disposable database `dcas_clone_verify`:

- 13 migrations, latest `013_assessment_blueprints.sql`, checksum `d86406549986133cf237287a509ef6e7b50e9d50faef00d7c66e596587061fb2`.
- 713 questions: 442 historical (IDs 1–450) + 271 staged (IDs 451–721).
- Staged types: 199 MCQ, 31 SQL, 41 essay; all `validated`; all `original_locale = en`.
- 18 sessions, 109 attempts, 109 selection-log rows; all 18 historical sessions have `blueprint_id = NULL`.
- 49 blueprints across assessments 2/3/4/6 (4/6/9/30); 17 EASY, 17 MEDIUM, 15 HARD.
- All 49 are `approved`; all 49 have `approved_by = NULL`; quota consistency mismatches = 0.
- 442 translations total; 0 translations for staged questions (pending review by design).
- Immutability trigger present; nullable `assessment_session.blueprint_id` present.
- Restore exit code 0. Evidence: `DBCAS/_content/expansion-20261024/evidence/clone_restore_verification.json`.

**Runtime and safety controls**

- PostgreSQL 17.11; SQL Sandbox remains the read-only learner-role configuration on port 5434. No sandbox policy was weakened.
- AI model and OAuth configuration unchanged. E2E runs used live AI disabled and state-only OAuth callbacks.
- All mutating migration/import tests ran against disposable PostgreSQL/sandbox containers; no persistent mutation.

**Backups** (`DBCAS/_content/expansion-20261024/backups/`)

| Dump | Bytes | SHA-256 |
|---|---:|---|
| `persistent_pre_activation_20261025T125702.dump` | 337,188 | `fc2549bb23db3e137498b4302e3655f5071d2f9e96736366a8f5e918d7c277f7` |
| `clone_pre_drill_20261025T125702.dump` | 457,927 | `c931f8ba9da97a370582dbde31d3dde6965cf100145f96299e47f0c3d0f9daca` |
| `clone_post_activation_20261025T130455.dump` | 451,742 | `fa20cf8836d5c6ea419a33ec65941a3382f564ef1df3c2e03ac2fd9cc6a73111` |
| `dbcas_clone_pre_blueprints.dump` | 418,245 | `502c8904d11bda32a1806db32d4919046f656361d1186d176aa1ed74b1dec45f` |

All four passed `pg_restore --list`. Two full restores were also performed into fresh disposable databases: the post-activation clone dump (713 questions, 49 blueprints) and the persistent pre-activation dump (442 questions, 12 migrations, no blueprint table). Both restore to their expected states exactly.

---

## 2. Content reused

- **271 staged questions**, IDs 451–721, mapped by `DBCAS/_content/expansion-20261024/generated/staging_manifest.json`.
- Types: **199 MCQ / 31 SQL / 41 essay**.
- Difficulty: level 1 = 9, level 2 = 89, level 3 = 77, level 4 = 78, level 5 = 18.
- 15 subject areas; 71 distinct concepts; 376 confirmed question–concept links.
- 463 source references across 271 questions (1–4 per question); hosts: 393 `www.postgresql.org`, 35 `open.umn.edu`, 24 `dblp.org`, 11 `doi.org`.
- Every staged question has a non-empty explanation, at least one source reference, and at least one confirmed concept link.
- Structural checks: 199/199 MCQ have exactly four options and exactly one correct answer; 41/41 essay have four rubric bands spanning 0–5; 31/31 SQL have sandbox-derived expected results and edge datasets.
- Difficulty and concept alignment was reviewed against the spec definitions; no cross-wave duplicates and zero remaining findings in `content_review.json`.
- The 442 historical questions, 18 sessions, 109 attempts, and 442 translations were preserved additively; no historical row was rewritten by the drill.

---

## 3. Defects fixed

Five substantive defects were identified during review and corrected:

1. **Q574** — `ON CONFLICT ON CONSTRAINT` was invalid for a unique expression index.
2. **Q594** — `websearch_to_tsquery` negation precedence was explained incorrectly.
3. **Q625** — the explanation claimed two payments where the scenario defines three.
4. **Q573** — an absolute `RETURNING` rule was scoped correctly to PostgreSQL 17.
5. **Answer-position bias** — the correct MCQ option was A in 166/199 questions; options were normalized deterministically, producing A/B/C/D = **50/48/50/51**.

Post-repair validation: 271/271 staged questions validated, 0 failures. The repair run made 0 further content changes, rotated 48 pending VI drafts and left 27 unchanged. Two stale manifest hashes (Q573, Q574) were reconciled to the repaired prompts, after which the manifest matched specs, pending translations, and clone rows with 0 mismatches. Evidence: `review_repairs.json`, `manifest_hash_reconciliation.json`.

A separate legacy repair set addressed **26 validated historical questions** (explanations, tags, source references), and rejected one candidate as a duplicate of Q211. Retired Q5 was explicitly excluded and guarded from mutation. The persistent database still has NULL explanations for those 26 questions; applying that backfill remains an explicit editorial/change-control decision.

---

## 4. Vietnamese translations drafted

- **271/271** staged questions have Vietnamese drafts for prompt and explanation.
- 199 drafts include translated option text with option-label mapping preserved; 41 essays include translated rubrics.
- 196 drafts are in `DBCAS/_content/expansion-20261024/translations/vi_*.py`; 75 are inline in the specs. `translation_merge.json` reports 196 checked, 271 refreshed, 0 missing.
- The pending manifest `generated/translations_vi_pending.json` is keyed by JSON key, carries `source_sha256`, and marks all 271 entries `pending_human_review` with `imported = false`.
- MCQ option normalization uses the deterministic key hash (`option_normalization: 2026-10-25-key-hash`); the correct-answer mapping is carried through the translated option text and rotation metadata rather than by changing labels.
- SQL syntax, identifiers, fixture names, and executable structure are preserved by construction; sampled checks covered JOIN/NULL/three-valued/aggregation cases and the repaired Q573/Q574/Q594/Q625 items.
- Terminology and explanation semantics were spot-checked, not human-approved. No draft has been imported, and none is marked reviewed.

**Import constraint:** a fresh spec import assigns different IDs than the canonical manifest. The drill found **199 of 271 key→ID assignments differ** (e.g., `pilot-db-3nf-mcq` canonical 451 vs fresh 647; `db-easy-weak-entity` canonical 454 vs fresh 451). Translation and review import must resolve by JSON key plus the activation manifest, never by a stored canonical ID. The approved import path must also call `upsert_question_translations`, which recomputes `source_fingerprint`; copying the pending `source_sha256` into the database would fail validation.

---

## 5. Remaining editorial review

Still required before publication:

1. **Content approval** — named human review/sign-off of all 271 questions, including the five repairs and the repaired SQL semantics. The current review is automated/structural; it is not academic approval.
2. **Translation approval** — human review of all 271 Vietnamese prompts/explanations, 199 option sets, and 41 rubrics for terminology, semantic fidelity, and rubric equivalence. The schema has no translation-approval column, so approval must be recorded through the administrative review workflow or an auditable approval record.
3. **Blueprint approval** — all 49 rows are `approved` but have `approved_by = NULL`; `approval_basis` is technical prose. A named academic authority must approve the blueprints or the seed must be rerun with an approver identity.
4. **Legacy backfill decision** — decide whether to apply the 26-question legacy explanation/tag/source repair set to persistent data, or leave those historical records untouched.
5. **Non-blocking content-depth gaps** — assessment 2 has two unblueprinted HARD cells (Performance/IDX and Querying/JOIN/SELECT). Its target concepts are capped at difficulty 3, so those cells are not selectable. Separately, 85 practice cells have fewer than three question families (56 concepts fall below three in at least one band); formal blueprint coverage is unaffected.

Source traceability is adequate for editorial review: every staged question has at least one traceable source reference, and the reference hosts are recorded.

---

## 6. Migration and import dry-run results

All mutating tests used disposable PostgreSQL containers.

**Migration 013**

- Applied to the clone; checksum matches the checked-in migration.
- Re-running `migrate.py` reported “already current”; no duplicate table, index, column, or trigger was created.
- Rollback restored the clone to migration 012, 442 questions, 18/109/109, and 442 translations.
- Persistent remains at migration 012; migration 013 has **not** been applied there.

**Blueprint seeding**

- Dry run: assessment 2 → 4 versions, 3 → 6, 4 → 9, 6 → 30 (49 total).
- `--confirm` inserted 49 rows; all approved; quota sums match `max_questions`; 0 mismatches; immutability trigger installed.
- All 49 rows have `approved_by = NULL`.

**Question import**

- First run: 36 spec reports, 271 questions validated, 0 errors, IDs 451–721.
- Re-run: 271 `skipped_existing_prompt`, 0 failures; import is idempotent.
- Historical fingerprints remained stable: 18 sessions, 109 attempts, 109 selection-log rows.
- `build.py` deliberately refuses any database not named `dcas_clone`; persistent import therefore requires an authorized importer/change, not a guard bypass.

**Backup and restore**

- All four dumps are readable.
- The post-activation dump was restored into a fresh database with the exact expected state (see section 1).
- The persistent pre-activation dump was also restored into a fresh database and returned exactly to the rollback point: migration 012, 442 questions (max ID 450), 18 sessions, 109 attempts, 109 selection-log rows, 442 translations, no `assessment_blueprint` table, and 27 NULL explanations (26 repairable validated rows plus retired Q5).

---

## 7. Coverage after import simulation

- 51 assessment × area × band cells; **49 blueprinted**.
- Blueprinted cells with deficits: **0**.
- Formal assembly: **245/245** runs passed coverage, exact type quotas, and distinct family selection.
- Practice assembly: **245/245** runs passed the same checks.
- Aggregate formal quota per full run across the 49 blueprints: 470 MCQ, 64 SQL, 83 essay (617 selections).
- The only deficits are the two unblueprinted assessment-2 HARD cells described above. They are outside the assessment’s difficulty range (target max = 3) and do not block activation.
- Practice-depth inventory: 80 concepts × 3 bands = 240 cells; 155 have at least three families, 85 have fewer, and 56 concepts fall below three in at least one band. This is a content-roadmap item, not a formal blueprint blocker.

---

## 8. Actual regression test results

| Suite | Result | Evidence |
|---|---|---|
| Backend pytest | **1,038 passed**, 1 warning, 569.67 s | Full suite run in this work session |
| Frontend Vitest | **267 passed / 33 files**, 51.72 s | Full suite run in this work session |
| Release E2E, Chromium | **43/43 passed**, 0 unexpected/skipped/flaky, 1,102.9 s (18.4 min) | `_review/remediation/browser-results-chromium.json`, start 2026-10-25T06:11:43Z |
| Application E2E, Chromium | **10/10 passed**, 0 unexpected/skipped/flaky, 220.5 s (3.7 min) | `_review/activation-readiness/application/browser-results-chromium.json`, start 2026-10-25T06:31:18Z |
| Prior four-browser release | 43/43 on Chromium, Firefox, WebKit, Edge | `_review/dbcas-redo-20261025/release-*/` |
| Prior four-browser application | 10/10 on Chromium, Firefox, WebKit, Edge | `_review/dbcas-redo-20261025/application-*/` |

The fresh release run logged one `[WebServer] Maintenance tick failed: OperationalError` during teardown; all 43 tests passed and the run exited 0. It is treated as non-blocking teardown noise, not a product failure.

---

## 9. Precise remaining steps

1. **Authorize persistent activation.** Obtain explicit change authorization before touching `127.0.0.1:5435/dbcas`. No persistent mutation has occurred yet.
2. **Record human content approval.** Review the 271 staged questions, the five repairs, and the 26 legacy repairs; record reviewer identity and decision. Do not mark content approved without an actual authorized review.
3. **Record human Vietnamese approval.** Review all 271 drafts (prompts, explanations, 199 option sets, 41 rubrics) and record approval through the administrative review workflow.
4. **Approve blueprints by name.** Rerun/seeding must set `approved_by` to the authorized academic approver; do not treat the current technical seed as academic approval.
5. **Take or confirm a fresh persistent backup.** The existing `persistent_pre_activation_20261025T125702.dump` is verified; refresh it if any persistent data changes.
6. **Apply migration 013 to persistent** with `migrate.py` under the authorized change, then verify migration count = 13 and the migration checksum.
7. **Run the authorized importer** for the 271 questions using the canonical manifest/key mapping. Either preserve canonical order/IDs or resolve every translation and review item by JSON key; a fresh spec import shifts 199 IDs. Keep the `build.py` clone guard in place until an authorized importer exists.
8. **Seed the 49 blueprints** and verify: 49 rows, 4/6/9/30 per assessment, quota sums valid, named approver present, immutability trigger present.
9. **Import approved Vietnamese translations** through `upsert_question_translations` so `source_fingerprint` is recomputed; verify 271 staged translations and no pending/unapproved rows.
10. **Run post-activation verification** — 442 historical + 271 staged questions, 18/109/109 historical activity unchanged, 49 blueprints, 49/49 blueprinted coverage, 245/245 assembly simulation, and a release E2E smoke. Rehearse rollback from the fresh dump before declaring completion.

Optional, non-blocking follow-ups: close the assessment-2 HARD content gap, deepen the 85 practice cells below three families, and decide the 26-question legacy backfill.

---

## Evidence index

- `DBCAS/_content/expansion-20261024/generated/staging_manifest.json` — canonical 271-entry map.
- `DBCAS/_content/expansion-20261024/generated/translations_vi_pending.json` — 271 pending drafts.
- `DBCAS/_content/expansion-20261024/evidence/content_review.json` / `.txt` — structural and duplicate review.
- `DBCAS/_content/expansion-20261024/evidence/review_repairs.json` — repair validation and answer normalization.
- `DBCAS/_content/expansion-20261024/evidence/repairs_report.json` — 26 legacy repairs, clone only.
- `DBCAS/_content/expansion-20261024/evidence/translation_merge.json` — 196 files, 271 total drafts, 0 missing.
- `DBCAS/_content/expansion-20261024/evidence/manifest_hash_reconciliation.json` — Q573/Q574 hash fixes.
- `DBCAS/_content/expansion-20261024/evidence/id_mapping_constraint.json` — 199 key→ID differences.
- `DBCAS/_content/expansion-20261024/evidence/coverage_activation_drill.json` — 49/49 blueprinted coverage.
- `DBCAS/_content/expansion-20261024/evidence/assembly_simulation.json` — 245/245 runs.
- `DBCAS/_content/expansion-20261024/evidence/activation_pre_state.txt` — persistent pre-state and fingerprints.
- `DBCAS/_content/expansion-20261024/evidence/activation_rollback.txt` — rollback verification.
- `DBCAS/_content/expansion-20261024/evidence/clone_restore_verification.json` — post-activation restore proof (new).
- `DBCAS/_content/expansion-20261024/backups/` — four verified dumps.
- `_review/remediation/browser-results-chromium.json` — fresh release E2E.
- `_review/activation-readiness/application/browser-results-chromium.json` — fresh application E2E.
- `_review/dbcas-redo-20261025/` — prior four-browser E2E evidence.
