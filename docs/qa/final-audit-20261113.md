# Final audit — 20261113

Baseline: clean `develop2` at `05920ad`, CI run `42962843780` green (59m29s).
Actual execution: 2026-11-11 +0700; the request identifier is 20261113.
Evidence root: `docs/qa/final-20261113/`. Branch only `develop2`; no main,
master or force-push; no destructive Git command; main checkout untouched.

## Safety

- Sole writer: active OpenCode session plus its tool servers. No stale writer
  was evidenced; no process was killed.
- HEAD `05920ad` stable for 30 s; `git fsck --no-dangling` clean.
- Recently modified Python sources compile; only one zero-byte generated log
  existed (not source); no truncated/parse-error file found.
- `.env` and `.env.*` ignored; 5,535 reachable blobs and tracked files scanned,
  **0 secret findings**. No secret value is stored in this report.
- `dbcas-local` and unrelated healthy containers were preserved. The demo was
  rebuilt from final source at the end.

## Workstreams

| Workstream | State | Evidence |
| --- | --- | --- |
| W1 Learner E2E | **DONE** | `w1-learner.md`; post-rebuild **30/30**, 68 screenshots; `test:practice` 6 pass/3 skip, OAuth 16/16, recovery 2/2, smoke 3/3 ×3; fake provider **39/39, 18.3m** in the final repeat (first run 32/1/6 retained as D4) |
| W2 Admin E2E | **DONE** | `w2-admin.md`; **33/33**, 37 screenshots, 0 errors; dashboard/API+CSV, Flow 2 reason/approval/audit, accounts, bank/CLO, system, RBAC |
| W3 Backend/AI | **DONE** | `w3-backend-ai.md`; 1,067 targeted tests; matrix 2,291,100/0; bank 5,482/0; SQL rejection; prompt byte-equality; deps/secrets clean |
| W4 Logo | **DONE** | `logo-20261113/inventory.md`; 22 captures / 0 issues; 9/9 brand test; 375→376 unit; contrast 186/186 |
| W5 Cleanup | **DONE** | `w5-cleanup-inventory.md`; 84 paths / 8,552,970,863 B / 186,321 files quarantined; 0 in-repo dead modules/deps/services/DB objects |
| W6 Documents | **DONE** | `w6-documents.md`; 0 Word edits / 0 diagrams; Word COM **3/3**, 59/70/40 pages; TOC 36/17/50; 0 Vietnamese paragraphs |

## Defects

| Defect | Symptom | Root cause | Fix | Commit | Test |
| --- | --- | --- | --- | --- | --- |
| D1 Long-email header overflow | EN learner dashboard/assessments at 1280 with a 36-char email: `scrollWidth 1298 > 1280`, logout clipped | Wider brand lockup plus non-shrinking account cluster; email shown at `xl` | Keep account text to `2xl`, cap/truncate both blocks with titles; nav moves to `xl`; W4 measured overlap | `d9c324b` | `BrandAssets` + 22 browser captures; W1 post-rebuild recheck 1280/1280; final demo long-email 1280/1280 |
| D2 Manifest MIME | nginx served `/brand/manifest.webmanifest` as `application/octet-stream` | Unknown extension fell back to nginx default type | Explicit `default_type application/manifest+json` location | `5a4a3a2` | BrandAssets 10/10 pins the server mapping; final demo HTTP check |
| D3 Inventory response models | `/health`, `/api/v1/ping`, `/readiness` had blank `response_model` in generated inventory | Generator hard-coded `""` for `main.py` routes and did not bind the matched decorator | Pass the matched decorator to `response_model()` in both branches; regenerate | `df46c08` | New test failed 1/1 before, **4/4** after; inventory 92 routes/0 drift |
| D5 Lifecycle clock-hook import | Full suite `test_draft_lifecycle` failed: `assessment_lifecycle` has no attribute `datetime` | Dead-import cleanup removed a module attribute that the regression test monkeypatches to prove timestamps use the DB clock | Restore `datetime` with an explanatory `noqa`; keep the DB-clock assertion | `2fae1dc` | `tests/test_draft_lifecycle.py` **21/21**; ruff clean |
| D4 Fake-provider cold sandbox timeout | First `test:qa` Flow 2 repeat 1: admin `POST .../run-sql` stayed “Đang chạy…” >20 s; trace status -1 | App logs at that moment: `Database readiness failed: OperationalError`, `Ephemeral cleanup deferred ... sandbox_unavailable`; Docker sandbox connectivity, not validation | No code change: same test passed repeats 2/3 and standalone; final full repeat **39/39, 18.3m**, no retry inside the gate, no assertion weakened | — | `fake-provider-final.log`; `test-qa-root.log`; `flow2-diagnostic.log`; direct API `SELECT 1` 3.8 s |

No other runtime/security defect was found. Dead-code cleanup removed 24
unused imports and 3 dead locals (`daceccf`); four intentional
`practice_generation` re-exports remain annotated for test/QA harnesses.

## Gates (real numbers)

| Gate | Result |
| --- | --- |
| Backend lint/build | PASS; `ruff` F401/F811/F841/F821 clean |
| Backend targeted (W3) | **1,067 passed** across contract/security/AI/SQL/migrations/readiness suites; full suite delegated to CI |
| Exact-count matrix | **2,291,100 cases / 0 failed**, 281.74 s |
| Bank validator | **5,482** = 2,006 MCQ / 1,747 SQL / 1,729 essay; 0 invalid |
| Frontend unit | **376/376**, 43 files, 124.31 s |
| Frontend lint/format/build | PASS; build **854 ms** |
| Frontend audit | **0 vulnerabilities** |
| Contrast | **186/186** |
| Learner browser | **30/30** post-rebuild; 68 screenshots; 0 page/console/5xx |
| Admin browser | **33/33**, 37 screenshots, 0 page/console/HTTP errors |
| Fake provider ×3 | **39/39 passed**, 18.3m, 0 failed/skipped/retry in the final repeat; first-run D4 timeout retained above |
| Default browser suite | delegated to pushed-HEAD CI |
| Docs/Word | `docs:check` 48 project + 52 Word + 10 figure gates PASS; `docs:verify-word` **3/3 PASS**, 59/70/40 pages, 0 mismatches |
| Secret hygiene | 5,535 blobs, **0 findings** |
| Dependencies | backend 0; frontend 0; root 2 low (dev Mermaid/KaTeX) |
| Demo | rebuilt from final source; web 18080/API 18000/Mailpit 18025; both demo logins verified; long-email 1280/1280; logo assets served |

## LLM usage

**0 real provider calls this round.** The previous/new-key ledger remains
**3/5** requests, all HTTP **403** before a completion. The key is masked and
was not printed or committed; no retry was made. Prompt Builder purity,
byte-identical evaluator input, timeout/cache/fallback and bank recovery were
verified offline/fake-provider. Real-model quality remains unverified.

## Cleanup

- In-repo: **0** unreferenced frontend/backend modules, **0** unused npm/Python
  dependencies, **0** unused Compose services, **0** unused environment names,
  **0** unreferenced DB tables. One byte-identical tracked script removed;
  27 unused imports/locals cleared.
- Quarantine: **84 paths / 8,552,970,863 B / 186,321 files** in
  `C:\Users\kudot\Downloads\proposal test\_trash-20261113`.
- Prior quarantine `_trash-20261112`: **370,225 B / 12 files** (367,401 B
  payload). Nothing permanently deleted.

```powershell
Remove-Item -LiteralPath 'C:\Users\kudot\Downloads\proposal test\_trash-20261112' -Recurse -Force
Remove-Item -LiteralPath 'C:\Users\kudot\Downloads\proposal test\_trash-20261113' -Recurse -Force
```

## Unverified / human input

- Real LLM output quality and gateway acceptance (external 403).
- External Google/GitHub OAuth credentials (buttons and safe unconfigured
  behavior verified; real provider consent not exercised).
- CI green on the final pushed HEAD (pending).
- D4 first-run transient sandbox timeout root cause is Docker connectivity; the
  clean final repeat passed 39/39. CI's fake-provider run is the independent
  confirmation.
- English learner practice/evaluation copy remains partially Vietnamese by
  current product scope; not a regression in this round.
- AI practice generation has no per-user rate limit (documented ASK).
- Root diagram toolchain retains 2 low dev-only advisories.
