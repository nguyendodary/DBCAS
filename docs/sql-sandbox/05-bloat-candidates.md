# 05 — Top Five Bloat Candidates

Ranked by measurable cost and confidence. Every item is evidence-backed; none
is a recommendation to delete data or production artifacts.

## 1. Executor image payload: 899 MB, with test tooling in the runtime

**Evidence**

- `docker images`: `dbcas-sql-ephemeral:local` = **899 MB**;
  `dbcas-local-api:local` = **423 MB**; frontend = **129 MB**.
- `sandbox/Dockerfile.ephemeral:1-13` starts from `postgres:17`, installs
  Python 3 + venv, and installs **all** of `backend/requirements.txt`.
- `backend/requirements.txt:13` includes `pytest==9.1.1`, a test-only package,
  in the runtime requirements used by both the API and executor images.
- `backend/Dockerfile:1-3` copies a **44.3 MB** Docker CLI binary into the API
  image; measured inside `dbcas-local-api:local`.
- The API image has **129 MB** of Python site-packages; the local venv's
  largest packages are SQLAlchemy 18.1 MB, PIL 15.5 MB, cryptography 10.6 MB,
  Pygments 8.6 MB, lxml 8.6 MB, psycopg-binary 8.1 MB, sqlglot 6.0 MB.
- The audit host also holds many stale tagged variants (423 MB API, 899 MB
  executor, 129 MB web) from previous smoke runs; these are not in the repo
  but amplify local disk use.

**Why it matters**

The executor is pulled/built for every ephemeral stack and every CI shard.
A 899 MB image is the single largest artifact in the delivery path. `pytest`
in production also expands the attack surface and is never needed at runtime.

**Options (in order)**

1. Move `pytest` to `backend/requirements-dev.txt`; keep
   `requirements.txt` runtime-only. Low risk, immediate.
2. Split `requirements-runtime.txt` for the executor: it needs psycopg,
   sqlglot, pydantic, and the app modules used by `sandbox_job`, not FastAPI,
   uvicorn, PyJWT, bcrypt, pypdf, or pytest.
3. Build the executor in two stages: install wheels in a builder, copy only
   the venv into the runtime; drop pip caches and `.pyc`.
4. Evaluate `postgres:17-alpine` for the executor after the psycopg binary
   compatibility check. Do not switch without the full sandbox test suite.
5. Add a periodic `docker image prune`/tag retention policy for local and CI
   hosts.

**Expected impact:** 100–250 MB off the executor, less on the API; faster
pulls and lower CI disk pressure. Exact savings require a prototype build.

## 2. Frontend media assets: 15.2 MB tracked, 17.3 MB build output

**Evidence**

- `frontend/src/assets` tracked media:
  `hinhnen_Home.mp4` **9.41 MB**, `video1.mp4` **3.90 MB**,
  `hinhnen.png` **1.88 MB**, `nen1.jpg` 0.40 MB, `SQL.jpg` 0.27 MB,
  `hinhnen_Home.jpg` 0.27 MB.
- `frontend/dist` total **17,756 KB (17.3 MiB)** across 41 files; the two MP4s
  and the PNG account for **15.19 MB**.
- The web image is **129 MB**; the media is copied into it by
  `frontend/Dockerfile:11`.
- First load is **1,174 KB transfer / 65–91 ms DOMContentLoaded** because the
  media is not on the critical path (see `02-measurements.md` §9). The cost is
  repository clone, image size, and CI build context, not first paint.

**Why it matters**

Every clone, worktree, CI checkout, and web image carries 15 MB of decorative
video/image. The hero video is larger than the entire JS bundle (954 KB raw).

**Options**

1. Re-encode the two MP4s to WebM/H.265 at a lower bitrate; target < 2 MB
   total. Keep a poster image for the first frame.
2. Replace the hero video with a static poster on small screens and
   `prefers-reduced-motion`; lazy-load the video only when visible.
3. Move large media to object storage/CDN if the deployment has one; keep only
   the poster in the image.
4. Compress the PNG to WebP/AVIF; 1.88 MB should be well under 300 KB at the
   displayed size.

**Expected impact:** 12–14 MB off the web image and repository; faster CI
checkout. No functional change if posters are preserved.

## 3. CI matrix: 9 full-stack legs, 76.3 machine-minutes per run

**Evidence**

- `.github/workflows/dn-backend.yml:166-282` defines nine `frontend-shard`
  legs: 3 e2e, 3 QA, 3 smoke, each with its own Compose project and ports.
- Run `44706644787`: e2e-1 13.3 min, e2e-2 10.1, e2e-3 7.6, qa-1 10.8,
  qa-2 10.6, qa-3 9.6, smoke-1 5.5, smoke-2 4.4, smoke-3 4.4 =
  **76.3 machine-minutes**.
- Each leg starts a full Compose stack and seeds the demo database. The seed
  alone is **121.9–144.0 s** in the smoke artifacts (`02-measurements.md` §6),
  so roughly **18–22 machine-minutes per run** are spent re-seeding.
- `backend` is 22.8 min and is the wall-clock critical path; the 9 shards run
  in parallel and finish in 13.3 min or less.

**Why it matters**

The matrix buys reliability coverage (3 QA loads, 3 smoke repeats) at a high
machine cost. On a docs-only PR the entire matrix is skipped by design, but on
code PRs it is the dominant CI cost.

**Options**

1. On `pull_request`: run one e2e shard pair, one QA leg, one smoke leg; keep
   the full 3× QA/smoke matrix on `push` to `develop2`/`main` and on a nightly
   schedule.
2. Keep the 3× repeats only for the QA load profile that actually differs
   (`qa-1` has `qa_load: '1'`; `qa-2`/`qa-3` are both `'0'`). If the repeats
   are for flake detection, move them to nightly.
3. Cache the built images and the seeded database volume between jobs; the
   seed is deterministic synthetic data.
4. Split `backend` (22.8 min) only if its runtime is dominated by a subset
   that can be sharded safely; do not shard blindly.

**Expected impact:** roughly **30–40 machine-minutes** saved per code PR,
without reducing the pre-merge signal if one leg of each kind is kept.

## 4. Cold seed/init: 144 s, paid once per stack and once per CI shard

**Evidence**

- CI artifact `seed-init-smoke-1/init-state.json` for run `44706644787`:
  start `08:59:02.161Z`, finish `09:01:26.182Z` = **144.0 s**.
- Previous run `44701525065`: **121.9 s**.
- `backend/app/seed_demo.py` creates 4 history sessions × 13 questions and
  runs SQL through the sandbox; the init log shows repeated
  `ai_call role=prompt_builder` / `evaluator` entries and a final
  "Local demo data ready".
- Local `dbcas-local-init-1` takes **5.0 s** when it detects existing data
  ("Existing local data preserved"), so the cost is the fresh seed, not the
  container.

**Why it matters**

Every CI shard pays ~2 minutes before tests start; the full matrix pays it
nine times. Developers also wait ~2 minutes on a fresh local stack.

**Options**

1. Build a **seed template volume**: run the seed once in a builder job,
   snapshot the PostgreSQL data directory, and mount it read-only/copy it for
   each shard. The data is synthetic and deterministic.
2. Split `seed_demo` into schema/reference data (fast) and history sessions
   (slow); run history generation only for tests that need it, or in the
   background after readiness.
3. Avoid executing SQL through the sandbox while generating history; store the
   expected grading detail directly for demo rows, or use a precomputed
   fixture.
4. Keep the current path as a fallback for a clean, from-scratch validation
   job (one leg), so the template does not hide seed regressions.

**Expected impact:** 90–120 s off each fresh stack; 15–20 machine-minutes per
full matrix. Must be validated against `seed_demo` correctness tests.

## 5. Redundant shared sandbox in the ephemeral DN stack (and the API Docker CLI)

**Evidence**

- `docker-compose.dn.yml:17-26` starts a shared `sandbox` service with
  `mem_limit: 256m`, `cpus: 1`, `pids_limit: 200`.
- `docker-compose.dn.yml:50` sets `SANDBOX_MODE=ephemeral`, and `:67-71`
  builds the ephemeral executor image.
- `backend/app/services/sandbox_runner.py` `build_sandbox_runner` returns
  `EphemeralSandboxRunner` when `sandbox_mode == "ephemeral"`; the ephemeral
  runner creates its own containers and does not use the shared `sandbox`
  service.
- `backend/Dockerfile:1-3` puts a 44.3 MB Docker CLI in the API image; it is
  only needed for ephemeral mode.

**Why it matters**

The DN stack pays for a 256 MB / 1 CPU PostgreSQL service that no request
uses, plus its image pull and healthcheck. The API image pays 44.3 MB for a
CLI that is dead weight in shared mode. Both are small compared with items
1–4, but they are pure waste and easy to reason about.

**Options**

1. Remove the shared `sandbox` service from `docker-compose.dn.yml` when
   `SANDBOX_MODE=ephemeral`; keep it only in the shared-mode profile. Update
   `depends_on` and readiness accordingly.
2. Build two API image variants: `api-shared` (no Docker CLI) and
   `api-ephemeral` (with CLI), or install the CLI only when the mode needs it.
3. If removing the shared service is too invasive, document it as a legacy
   fallback and stop publishing its port in ephemeral stacks.

**Expected impact:** 256 MB RAM and 1 CPU freed in DN; ~44 MB off the shared
API image. Low risk, but touches Compose, so it belongs in a separate change
from the SQL sandbox rollout.

## Not bloat (checked and rejected)

- **`assessment`, `assessment_blueprint`, `assessment_concept`,
  `assessment_question` have 0 local rows**, but `assessment` is used by
  `backend/app/services/adaptive_engine.py` and the admin assessment flow.
  Empty demo data is not evidence of dead code.
- **`frontend/dist` is not tracked** (`git ls-files frontend/dist` returns 0);
  it is build output. The tracked cost is `frontend/src/assets`, covered above.
- **`qa-ai`** is a local-only Compose override
  (`docker-compose.qa.yml:1-34`) and is not part of the release stack. It is
  test infrastructure, not production bloat.
- **`llm_cache` (150 rows / 532 KB)** is small and used by the LLM service;
  there is no evidence it is unbounded in the local snapshot.
