# Development activation — 24 October 2026

The owner-authorized development activation is complete. This record supersedes
the pending-activation statements in the dated 23 October reports; those reports
retain their original observations and results.

## Database and recovery evidence

- Persistent database: `dbcas`, PostgreSQL 17.11, volume `dbcas_db-data`.
- PostgreSQL system identifier: `7691984040786436134`.
- A fresh PostgreSQL 17.11 custom archive, including ownership and ACL metadata,
  was created outside Git in restricted local storage. SHA-256:
  `472abd0bf2c51c77ee4bb7d1c91145027fe3d19e77dbd4d8808f690ed4d0c5c1`.
- An independent disposable PostgreSQL 17 restore matched all 33 public tables,
  deterministic row fingerprints, original roles, ownership/ACLs and sequences.
- The byte-identical accepted migration 012 passed on that restored copy first.
  Reapplication through the official runner was a no-op.
- The persistent ledger advanced from 001–011 to 001–012. Previous ledger rows
  and checksums remain intact. All 32 business-table fingerprints are unchanged
  after excluding only the new `question.original_locale` English default.
  All 442 existing source questions and reviewed translations remain valid.
- No database was reset, reseeded, replaced with preview data or restored over.
  Existing backups and the separate preview environment were retained.

## Current local application

- Frontend: `http://localhost:5173`.
- Backend: `http://127.0.0.1:8000`; `/readiness` returns HTTP 200.
- The backend now uses persistent `dbcas`, not `dbcas_preview`.
- Existing JWT, Google/GitHub OAuth, AI model/provider and sandbox settings are
  preserved. The root `.env` was not overwritten. Use the same `localhost`
  frontend origin as the configured OAuth callbacks.

Use the existing environment and normal commands from separate terminals:

```powershell
cd backend
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Check existing listeners first. These commands do not run migrations or clear
provider variables. Do not start another server when the service is already up.

## Acceptance scope

Fresh post-cutover checks include 582 backend regression cases, 267 frontend
cases, 16 restored-data integration cases and six audited dashboard reads.
Real Chromium browser checks authenticated existing development identities,
opened six Admin and four Learner pages, read historical evidence, switched
English/Vietnamese, checked Medium selection and rejected learner review access.
Those reads preserve the original historical records; mutating tests use
disposable databases and test accounts.

The earlier supervisor acceptance remains separate evidence: 1,026 backend,
267 frontend and 43 full plus 10 normal-application browser cases per engine
(Chromium, Firefox, WebKit and Edge). Executable source is unchanged from that
accepted candidate; expensive complete cross-browser suites are not represented
as newly rerun for this activation.

Google/GitHub configured entry points and safe start/callback parameters were
verified. Full external-account authentication and live AI/provider behavior
remain unverified. No live provider calls, production/staging deployment or
academic-document rewriting was performed. Optional translation preparation
still produces drafts requiring human review.

Editable architecture artifacts and their semantic traceability remain in the
[diagram inventory](diagrams/README.md); no diagram content was simplified.
