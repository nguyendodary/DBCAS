# Final completion evidence — 2026-11-10

Branch `develop2`; one writer in `_worktrees/dbcas-dn-20261101`.
Current application fixes end at `26d7e6d`; final visual evidence is
`7301a7f`. Later documentation commits do not change the application.

The stale OpenCode PID **4372** and its 15 descendants were terminated after
checking the current Codex ancestry; the detached project Vite PID **9764**
was also removed. HEAD stayed `3ae57be` for **30 seconds** (21:55:31–21:56:01
+0700). Recovered `c4e578a`/`3ae57be`, fetch/checkout/pull, fsck and integrity
checks passed. Scan: **207 recent paths / 90 text / 6 JSON / 1 YAML /
12 Python AST, 0 errors, 0 restored files**. The preserved stash and original
four healthy `dbcas-local` container IDs remained untouched.

Six stopped, ownership-labelled `dbcas-sandbox-test` temporary containers
were removed after re-inspection: no persistent mounts, only tmpfs data;
plain `docker rm` stopped no service and removed no volume. Historical QA
Compose stacks remain untouched. See the [cleanup record](../cleanup-report.md).

| W | Evidence-based status | Evidence |
| --- | --- | --- |
| W1 fonts | DONE + verified | `b498012`, `d82669c`, `c6fff48`, `ad44cbd`, `26d7e6d`; Inter UI/essay and SQL-only Mono; computed fonts plus Vietnamese glyphs in all 102 captures |
| W2 SQL screen | DONE + verified | `b332022`; actual SQL execution and layout at 390/768/1280/1920 in the [matrix](../final-ui/screenshots.md) |
| W3 copy | DONE + verified | `b9c902c`, `25b0e0a`, `26d7e6d`; [copy audit](../ux-copy-audit.md), both-locale regressions and mobile/desktop inspection |
| W4 light theme | DONE + verified | `644d38c`, `1f903a0`, `25b0e0a`, `26d7e6d`, `7301a7f`; contrast 186/186, 102 reviewed images, 0 overflow/errors |
| W5 stable flows | DONE + verified baseline; final changed-source CI required | Regex `3c3f373` and green `9f3cd92`: 55 browser, 39 fake-provider, 3 smoke. OAuth fix `da60e88` adds three unit/one browser regressions; visual/landing regressions add five browser cases |
| W6 AI pipeline | DONE offline; real-model quality UNVERIFIED | `b954b2f`, unchanged 141 purity/hash tests within backend 1455; [audit](../ai-pipeline-audit.md), [bounded request ledger](live-request-ledger.json) |
| W7 cleanup | DONE + verified | `5d9715c`, `a816238`; final 52-module/0-unreferenced scan; [kept/deleted evidence](../cleanup-report.md); no additional file deletion, six stopped temporary sandboxes removed |
| W8 documents | DONE + verified | Earlier in-place English v1.2 edits retained; local Word COM 3/3; schema/runtime/API/routes audited; [Word audit](word-audit.md); no architecture/diagram change |

Every current practice result follows preliminary evaluation → administrator
review/optional reason-bearing score edits → approval → publication.
Pending scores remain hidden and excluded from published analytics. Historical
automatic-release cases keep their saved policy; the current UI offers no
release-flow selector.

| Gate/evidence | Actual result and source |
| --- | --- |
| Backend lint/build/pip/OpenAPI/bank/full tests | Green [CI 42825915679](https://github.com/nguyendodary/DBCAS/actions/runs/42825915679), `9f3cd92`: **1455/1455, 1148.02s**; backend/AI/db/Compose/dependency source unchanged this continuation |
| Frontend baseline full units | Same CI: **351/351**, 40 files, 37.50s; this-run pre-OAuth full **351/351, 91.63s** |
| Changed auth/components | Auth **38/38, 10.47s**; final affected localization/review components **32/32, 9.64s** |
| Final frontend lint/format/build | PASS; final production build **716ms**; dependencies unchanged, fresh-clone frontend audit **0 vulnerabilities** |
| Default browser baseline | Green `9f3cd92`: **55/55**, about 27.5m, no retries; current changed-source suite adds six regressions |
| New UI regressions | Landing **1/1, 1.8s**; four final visual cases **4/4, 3.6s**, no retries; real OAuth callback checked locally |
| Fake-provider scenario x3 | Green `9f3cd92`: **39/39** (13 each), about 16.9m; unchanged scenario/backend/provider code |
| Smoke / launcher | Same green CI: **3/3** smoke, **7/7** launcher |
| Final visual matrix | **102 images / 25 states**, 133.58s; scoped final 32 refresh **30.31s**, 70 unchanged captures reused; **0 overflow / 0 page errors** |
| Contrast/fonts | **186/186** pairs; Inter 400/500/600/700 with Vietnamese loaded, SQL-only Mono; actual computed-font assertions |
| Fresh clone without .env | Remote clone at `3ae57be`, root/UI ci **40.60s**, isolated reset **186.32s**, start **17.32s**; later fast-forward to `7301a7f` and final start **26.26s**, all healthy |
| Final production demo | Web readiness/API health **200/200**; learner/admin browser login and settings **2/2**, **0 page errors**, no provider calls; original four containers retain their IDs |
| Documents | `docs:check` PASS: **46 project + 41 Word assertions + 10 diagram gates**; actual Word COM verification **3/3**, no new PDF render for unchanged packages |

Final pushed-HEAD CI is the remaining release gate at this report's commit
time. Its authoritative outcome and exact final counts are recorded by the
[develop2 workflow](https://github.com/nguyendodary/DBCAS/actions?query=branch%3Adevelop2)
and the owner's final handover response. No local check is presented as a
green final-HEAD CI result. Earlier 14/15 and 21/24 incomplete browser reports
are historical; green `9f3cd92` closed that migration. Their logs remain.

The latest isolated demo is **http://localhost:19180**, API **19100**, Mailpit
**19125**; both requested accounts use `Demo12345!`. See the
[demo script](../../demo/demo-script.md) for the normal default ports and
the verified isolated profile. Initial stderr/SMTP startup failures were
root-caused; corrected success logs remain under
`_review/finish-20261110/`.

Unverified: real-model quality, external OAuth-provider credentials and
production deployment/load. The final round confirmed one rejected evaluator
request and conservatively consumed the second slot after Docker/WSL returned
no result JSON; **no retry and no request budget remain**. No key was printed
or committed. Jira statuses and human meeting/signature/reflection entries
remain owner-supplied; no names or dates were invented.
