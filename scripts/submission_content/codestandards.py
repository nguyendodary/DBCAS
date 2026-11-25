# -*- coding: utf-8 -*-
"""Code Standards content: only the rules that are actually present and enforced.

Each rule names the file that enforces it.  Rules that are policy but not
mechanically checked are marked as review standards; rules that do not exist
(coverage thresholds, type checking, Python formatting) are stated as absent
instead of being invented.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

BLOCKS = [
    ("h1", "1. Purpose and Scope"),
    ("p", "This document records the coding standards that the DBCAS "
          "repository actually applies, and separates them from advice. A "
          "rule appears here only if a configuration file, a script, a hook "
          "or a CI job enforces it, or if the repository states it as review "
          "policy. Where the project does not enforce something that a "
          "standard document usually claims, this document says so."),
    ("table", {
        "caption": "Enforcement levels used in this document",
        "header": ["Level", "Meaning", "Example"],
        "widths": [3.2, 7.0, 5.3],
        "font": 10,
        "rows": [
            ["Enforced", "A tool fails the build or the commit",
             "ruff correctness rules, ESLint, Prettier, secret scan"],
            ["Gated", "A CI job must pass before merge",
             "pytest, vitest, Playwright shards, docs:check"],
            ["Review", "A reviewer checks it; no tool fails",
             "commit message format, naming, layering"],
            ["Absent", "Not enforced anywhere in the repository",
             "coverage threshold, mypy, ruff format"],
        ],
    }),

    ("h1", "2. Repository Structure"),
    ("code", """DBCAS/
├── backend/            FastAPI application, tests, manage.py, pyproject.toml
│   ├── app/            26 modules, routers/ (8 files), services/ (73 files)
│   └── tests/          94 test modules + tests/dn/ (24 contract modules)
├── frontend/           React 19 + Vite SPA, vitest, Playwright configs
│   ├── src/            components, pages, hooks, i18n, test
│   └── e2e/            25 specs; e2e-application/ 3 specs
├── db/                 schema.sql, migrations/ (28 files), seed data
├── scripts/            gates, generators, document build and verification
├── docs/               architecture, diagrams, deliverables, submission
└── deploy/, sandbox/   deployment and executor assets"""),
    ("p", "The layout is by technical role, not by feature. A feature touches "
          "a router, a service, a repository method, a React page and one or "
          "two i18n keys; the pull request template asks for all of them."),

    ("h1", "3. Naming Conventions"),
    ("table", {
        "caption": "Naming rules",
        "header": ["Element", "Rule", "Example"],
        "widths": [3.4, 7.8, 4.3],
        "font": 10,
        "rows": [
            ["Python modules", "lower_snake_case", "grading_review.py"],
            ["Python classes", "PascalCase, suffix by role",
             "AssessmentRepository, GradeReview"],
            ["Python functions", "lower_snake_case, verb first",
             "claim_grading_job, compare_state"],
            ["Constants", "UPPER_SNAKE_CASE",
             "REVIEW_STATUSES, CLAIM_LEASE_MINUTES"],
            ["React components", "PascalCase file and export",
             "CompetencyRadar.jsx"],
            ["React hooks", "use prefix, camelCase", "useSessionGuard"],
            ["Routes", "kebab-case path segments", "/admin/review-queue"],
            ["Database tables", "lower_snake_case, singular", "question_concept"],
            ["Database keys", "<table>_id, foreign keys <table>_<col>_fkey",
             "attempt_id, attempt_session_id_fkey"],
            ["i18n keys", "camelCase groups, one flat leaf per string",
             "errors.sandbox_busy"],
            ["Error codes", "lower_snake_case string literal",
             "sandbox_busy, review_window_closed"],
            ["Commits", "Conventional Commits", "fix(api): handle null response"],
        ],
    }),

    ("h1", "4. Backend Layering"),
    ("p", "The backend separates HTTP contracts, use cases and queries. "
          "Routers declare paths, request models and dependencies; services "
          "own transactions and rules; repository classes own SQLAlchemy "
          "queries and locks. The dependency direction is one-way and is "
          "checked in review: no repository imports a service, no service "
          "imports a router."),
    ("table", {
        "caption": "Layer responsibilities",
        "header": ["Layer", "Owns", "Must not"],
        "widths": [3.0, 7.4, 5.1],
        "font": 10,
        "rows": [
            ["Router", "Path, status code, request and response schema, "
             "dependency", "Open a transaction or build a query"],
            ["Service", "Use case, transaction boundary, error codes",
             "Return an ORM object to the router without a schema"],
            ["Repository", "Queries, locks, pagination",
             "Raise HTTP errors or know about request data"],
            ["Model / schema", "Table mapping, validation and serialisation",
             "Contain business rules"],
        ],
    }),
    ("p", "One measured exception exists: six router handlers query the "
          "session directly (practice.py lines 148 and 167, sessions.py 167, "
          "admin.py 227 and two adjacent handlers). They are listed here as "
          "known debt, not as an accepted pattern, and a change touching them "
          "should move the query into a repository method."),

    ("h1", "5. API Conventions"),
    ("bullets", [
        "Versioning is a URL path segment: every business route is under "
        "/api/v1. Two infrastructure routes (/health and /readiness) are "
        "unversioned by design.",
        "Resources are plural nouns; actions that are not CRUD use a verb "
        "segment (/sessions/{id}/submit, /admin/reviews/{id}/claim).",
        "Request and response bodies are Pydantic models; a handler never "
        "returns a raw ORM object.",
        "The OpenAPI document is generated from the application and checked "
        "into CI: python scripts/export_openapi.py --check fails when the "
        "committed contract differs from the code.",
        "Machine-readable errors use the envelope {error: {code, message, "
        "details}} with a stable lower_snake_case code; the frontend "
        "translates by that code, so a code is part of the public contract.",
        "List endpoints paginate with limit and offset and return the total "
        "when the UI needs it; a missing bound is a review finding.",
        "Authentication is a bearer token resolved by a dependency; "
        "authorisation is a capability check in the same dependency chain, "
        "never an if-statement in a handler.",
    ]),
    ("table", {
        "caption": "Status code usage",
        "header": ["Code", "Used for"],
        "widths": [2.4, 13.1],
        "font": 10,
        "rows": [
            ["200", "Successful read, replay of an idempotent request"],
            ["201", "Resource created"],
            ["204", "Successful delete without a body"],
            ["409", "State conflict: already submitted, claim expired, "
             "idempotency conflict"],
            ["422", "Validation failure or an invalid state transition"],
            ["403", "Authenticated but not permitted"],
            ["503", "Database unavailable, sandbox unavailable or provider "
             "unavailable"],
        ],
    }),

    ("h1", "6. Error Handling"),
    ("p", "One application exception class, AppError, carries a status code, "
          "a machine-readable code, a human message and optional details. "
          "Seven handlers translate exceptions at the boundary: LLM errors, "
          "database programming and operational errors, the catch-all, "
          "AppError, HTTP exceptions and request-validation errors. The "
          "catch-all re-applies the security headers because it short-"
          "circuits the middleware, a detail that must be preserved in any "
          "refactor."),
    ("bullets", [
        "Raise AppError with a new code rather than returning an error body "
        "from a handler.",
        "Never leak a driver message, a stack trace or a prompt to the client.",
        "Log the code and the identifiers, never the answer text or the key.",
        "A provider failure must degrade to a documented fallback; an "
        "unexpected validation failure must not fabricate a score.",
    ]),

    ("h1", "7. Frontend Conventions"),
    ("bullets", [
        "Components are function components with hooks; no class components.",
        "Data access goes through the single API client, which owns the base "
        "URL, the bearer token and error-code translation.",
        "Route guards check the role at the route level; a page does not "
        "re-implement authorisation.",
        "Every user-visible string is an i18n key; a literal string in JSX is "
        "a review finding.",
        "Charts read prepared series from the API; no scoring is recomputed "
        "in the browser.",
        "Styling uses Tailwind utility classes; shared visual tokens live in "
        "one place.",
    ]),

    ("h1", "8. Internationalization"),
    ("p", "English and Vietnamese catalogues are flat JSON with the same key "
          "set: 1 700 leaf keys in 34 groups in each language, zero drift. "
          "Question text is translated separately in the database, with "
          "English as the canonical original and a source hash per "
          "translation. Error codes are also i18n keys, so a new backend code "
          "requires a matching entry in both catalogues."),

    ("h1", "9. Testing Standards"),
    ("table", {
        "caption": "Test layers",
        "header": ["Layer", "Tool", "Location", "Rule"],
        "widths": [3.0, 2.6, 4.4, 5.5],
        "font": 10,
        "rows": [
            ["Backend unit and integration", "pytest 9.1.1",
             "backend/tests (94 modules)",
             "One behaviour per test; no network or provider call"],
            ["Backend contract", "pytest",
             "backend/tests/dn (24 modules)",
             "Contract and migration behaviour, separately linted"],
            ["Frontend unit", "vitest 4.1.12, Testing Library",
             "frontend/src/test (54 files)",
             "Component behaviour, not snapshots of markup"],
            ["Browser end-to-end", "Playwright 1.64, chromium",
             "frontend/e2e (25 specs)",
             "Every spec belongs to exactly one shard"],
            ["Application flow", "Playwright",
             "frontend/e2e-application (3 specs)",
             "Full journey across two roles"],
            ["Gate scripts", "unittest and node --test", "scripts/tests",
             "The gates themselves are tested"],
        ],
    }),
    ("bullets", [
        "A bug fix adds a regression test that fails before the fix.",
        "A test never calls a real provider: the QA profile serves "
        "deterministic fake JSON.",
        "A test may not be skipped or weakened to make a gate pass; a skip "
        "must name the reason in the test.",
        "There is no coverage threshold. Coverage is not measured anywhere in "
        "the repository, so no percentage is claimed in this document.",
    ]),

    ("h1", "10. Lint and Format"),
    ("table", {
        "caption": "Configured tools",
        "header": ["Tool", "Configuration", "What it enforces"],
        "widths": [2.6, 6.4, 6.5],
        "font": 10,
        "rows": [
            ["ruff 0.14.2", "backend/pyproject.toml: target py313, line "
             "length 120, select E9, F63, F7, F82",
             "Correctness only: syntax errors, undefined names, invalid "
             "escapes. Not a style or import-order gate."],
            ["ESLint 10.14.0", "frontend/eslint.config.js: js recommended, "
             "jsx, no-unused-vars with _ pattern",
             "Errors and unused variables; run with --max-warnings=0"],
            ["Prettier 3.9.10", "frontend/.prettierrc.json: no semicolons, "
             "single quotes, trailing commas, width 100, LF",
             "Formatting; format:check fails on any difference"],
            ["EditorConfig", ".editorconfig: UTF-8, LF, final newline",
             "Editor-level consistency"],
        ],
    }),
    ("p", "Python formatting is not automated: there is no ruff format "
          "configuration and no formatter job. Python style is therefore a "
          "review standard. Line endings are normalised at the Git layer "
          "(.gitattributes) so the formatter sees the same text on Windows "
          "and Linux."),

    ("h1", "11. Commit and Branch Conventions"),
    ("p", "Commits follow Conventional Commits: <type>(<scope>): "
          "<description>, with ten accepted types (feat, fix, docs, style, "
          "refactor, test, chore, perf, ci, build), a lowercase imperative "
          "description of 50–72 characters without a trailing period, and an "
          "optional body of lines up to 72 characters. One commit does one "
          "thing. The integration branch is develop2; main receives merges by "
          "pull request only."),
    ("p", "Attribution is the one mechanically enforced part: the commit-msg "
          "hook rejects AI or tool credit trailers and bot co-authors. The "
          "message format itself is a review standard, not a hook or a CI "
          "gate; the repository has no commitlint job."),

    ("h1", "12. Pull Requests and CI"),
    ("p", "The pull request template requires a summary, a verification list "
          "(tests, lint and format, manual verification, STATUS and BACKLOG "
          "when state changed), a risk section naming affected users and data "
          "with a rollback path, migration and breaking-change flags, and an "
          "independent-review flag."),
    ("table", {
        "caption": "CI workflows and jobs",
        "header": ["Workflow", "Job", "Gate"],
        "widths": [3.6, 3.2, 8.7],
        "font": 10,
        "rows": [
            ["Local quality gate", "changes", "Classifies a documentation-only "
             "change; docs/qa always forces a full run"],
            ["Local quality gate", "secrets", "Secret-scan unit tests and a "
             "full tree scan"],
            ["Local quality gate", "backend", "ruff, compile, OpenAPI check, "
             "bank validation, pytest, pip-audit, image build"],
            ["Local quality gate", "frontend-static", "ESLint, Prettier, "
             "vitest, build, security audit, npm audit, inventory, diagrams, "
             "docs:check"],
            ["Local quality gate", "frontend-shard", "Nine legs: e2e 1–3, "
             "QA 1–3, smoke 1–3"],
            ["Local quality gate", "frontend-local", "Fan-in: requires all "
             "nine shard artifacts to report success"],
            ["Demo seed benchmark", "measure", "Manual: seed and snapshot "
             "timing"],
            ["QA provider OOM repro", "repro", "Manual: provider memory "
             "reproduction"],
        ],
    }),
    ("p", "There is no coverage job, no static-analysis security job beyond "
          "the dependency audits and the custom frontend audit, and no "
          "type-checking job."),

    ("h1", "13. Secret Handling"),
    ("p", "Secrets live in the environment only. .env is ignored and never "
          "committed; .env.example documents every variable name and is "
          "checked by the environment inventory gate. The scanner applies "
          "seven patterns to the working tree, to staged blobs in the "
          "pre-commit hook, and to archives up to 128 MiB; it reports paths, "
          "never values."),
    ("bullets", [
        "The allowlist has six entries, each pinned by path, rule, SHA-256 "
        "and a reason that must start with “Fake fixture:”; it cannot be "
        "widened to hide a real secret.",
        "A finding is fixed at the source; deleting the line from history is "
        "an owner decision, not a routine fix.",
        "The measured result at this commit is zero findings in the tree and "
        "zero matching commits in history.",
    ]),

    ("h1", "14. Review Checklist"),
    ("table", {
        "caption": "Reviewer checklist",
        "header": ["#", "Check", "Why"],
        "widths": [1.2, 8.3, 6.0],
        "font": 10,
        "rows": [
            ["1", "The change has one purpose and one commit", "Revertability"],
            ["2", "Router, service and repository responsibilities are "
             "respected", "Layering"],
            ["3", "New error codes are added to both i18n catalogues",
             "User-visible message"],
            ["4", "New user-visible strings are i18n keys", "Localization"],
            ["5", "A new query has an index or a bounded scan", "Performance"],
            ["6", "A migration is a new file, forward-only, with a checksum",
             "Applied history is immutable"],
            ["7", "A bug fix has a regression test", "Prevention"],
            ["8", "No secret, no .env, no stray file", "Hygiene"],
            ["9", "Docs, STATUS and BACKLOG updated when state changed",
             "Traceability"],
            ["10", "The PR names a rollback path", "Operability"],
        ],
    }),

    ("h1", "15. Known Gaps"),
    ("bullets", [
        "No coverage measurement or threshold exists.",
        "No Python type checker or formatter is configured.",
        "ruff checks only four correctness families and skips backend/tests "
        "outside tests/dn.",
        "Six router handlers still access the database session directly.",
        "Two foreign-key columns lack a dedicated index.",
        "[OWNER TO PROVIDE: whether commitlint and a coverage gate should be "
        "added before the defence]",
    ]),
]
