# Phase 0 — detailed review of the large historical sync (2026-11-25)

This completes the disposition of the 236 paths left unresolved by
[phase0-survey](phase0-survey.md). The comparison used `07e4985^`, `07e4985`,
the E2E baseline `253f272`, and current `develop2` `52b9064`. No file, ref,
test, migration or Docker state was changed by this review.

## Result

All 236 paths exist in the sync, baseline and current trees with different
content; current content is exactly baseline content for every one of them.
The ten paths whose pre-sync content equals baseline remain excluded, as
recorded in the survey. Of the 236, 167 were additions relative to `07e4985^`
and 69 were modifications; none was mode-only.

| Category | Paths | Disposition |
|---|---:|---|
| Runtime, configuration, infrastructure and tooling | 99 | Superseded by reviewed/freeze work |
| Backend and frontend tests | 61 | Superseded; sync-only cases encode retired contracts |
| Authored documentation | 27 | Superseded; stale counts, routes and provider assumptions |
| Generated diagrams, catalogs and API/fact contracts | 44 | Superseded by later regeneration |
| DOCX deliverables | 3 | Superseded by later revisions |
| Binary media | 2 | Superseded by smaller re-encodes |
| Potentially useful freeze-scope work to import | **0** | No owner-review import candidate |

A wholesale import is unsafe for all 236 paths: each would overwrite newer
baseline content. The risk classes are 129 runtime/infrastructure/generated
artifact paths, 61 contradictory test-contract paths, and 46 documentation or
tooling paths.

## Representative evidence

- `07e4985:backend/app/services/practice_config.py` has `MAX_QUESTIONS = 20`;
  `253f272` has `LEGACY_MAX_QUESTIONS = MAX_QUESTIONS = 13` plus typed limits.
  The sync-only twenty-question test corresponds to the current thirteen-question
  test after `d402af3`.
- `07e4985:backend/app/services/llm/provider.py` contains OpenRouter-only
  request fields; `1c1936d` deliberately removed vendor-only fields and guards
  while introducing the generic `openai_compatible` provider.
- `07e4985:backend/app/services/prompt_builder.py` invokes local `ai/infer.py`
  through `subprocess`; baseline is template-only after `9b9c0ea`, `5a15274`
  and `eb3216e`.
- `deploy/nginx.conf` is `1m` in the sync and `30m` in the baseline; `efb15e1`
  accepted the current upload limit. The sync's `.github/workflows/dn-backend.yml`
  is 104 lines versus 403 currently and lacks the nine-shard aggregator added
  by `766af9b`, `7dfa33d` and `b34d8c6`.
- `frontend/src/i18n/` has 1,302 keys per locale in the sync versus 1,700 at
  baseline, with zero sync-only keys. Later localization commits include
  `59a41df` and `974b92b`.
- `docs/openapi.json` has 82 paths/92 operations in the sync versus 106/118
  currently, with no sync-only route or operation. Schema evidence changed
  from 41 tables/59 FKs/87 indexes/19 migrations to 66/120/158/27; `97bb97c`
  and `e5ffd16` record the later regeneration.
- `frontend/src/assets/brand/hinhnen_Home.mp4` is 9,869,525 bytes in the sync
  and 4,844,777 at baseline, consistent with the deferred re-encode in
  `94885c9`.
- Extracted DOCX body text in the sync contains stale 41-table wording;
  `aac18c9` later revised the academic documents.

## Limitation

This is a detailed semantic disposition of every path, not an exhaustive
literal line-by-line audit of binary and generated formatting content. Twenty
files are binary (15 PNG, 3 DOCX, 2 MP4) and 29 generated text artifacts were
compared semantically. DOCX body text was extracted; PNG dimensions, media
sizes, histories and generated contracts were checked against current sources.
The disposition above does not claim more than that evidence supports.
