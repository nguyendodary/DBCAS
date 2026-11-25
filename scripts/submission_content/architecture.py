# -*- coding: utf-8 -*-
"""Architecture Design content: structure, flows, pipeline, sandbox, grading.

Facts are measured from backend/app, frontend/src, the Compose files and the
OpenAPI document; scripts/verify_submission_docs.py re-measures the numbers
that appear here.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "docs" / "submission" / "final" / "assets"
MODULE_VIEW = ROOT / "docs" / "diagrams" / "rebuild" / "module" / "module.png"
ALLOCATION_VIEW = ROOT / "docs" / "diagrams" / "rebuild" / "allocation" / "allocation.png"

BLOCKS = [
    ("h1", "1. Introduction"),
    ("h2", "1.1 Purpose and Scope"),
    ("p", "This document specifies the architecture of DBCAS, an AI-assisted "
          "database competency assessment system. It covers the architectural "
          "drivers, the system context, the container and module views, the "
          "main runtime flows, the AI pipeline, the SQL sandbox, grading and "
          "result versioning, security, the architectural decisions and the "
          "key algorithms. Requirements and schedule are in the Proposal; the "
          "schema and its dictionary are in the Database Design document; "
          "coding rules are in the Code Standards document."),
    ("h2", "1.2 How this Document Was Measured"),
    ("p", "Every structural statement is derived from the repository at the "
          "frozen commit: 106 OpenAPI paths and 118 operations generated from "
          "the running FastAPI application, 8 router modules, 73 service "
          "modules, 13 repository classes in one module, 25 React route "
          "elements with 24 distinct paths, and six Compose services in the "
          "default local profile. Figures are generated from "
          "docs/diagrams sources, not drawn for this document."),
    ("note", "Owner-facing caveats are marked [OWNER TO PROVIDE: ...]. They "
             "are collected in section 14 and in the verification report."),

    ("h1", "2. Architectural Drivers"),
    ("h2", "2.1 Functional Drivers"),
    ("bullets", [
        "Two human actors only: Learner and Administrator. Everything a "
        "learner sees is derived from their own attempts; everything an "
        "administrator does is auditable.",
        "Three answer formats with different execution semantics: stored "
        "options for MCQ, executed SQL for SQL, rubric text for essays.",
        "A practice plan that is frozen before the first question, so the "
        "session is reproducible and cannot be silently shortened.",
        "Publication gated by evidence: practice and legacy sessions need "
        "administrator review, fixed-test sessions publish an official V1.",
        "AI used only where it adds value (rubric assistance, question "
        "generation), always behind validation and a deterministic fallback.",
    ]),
    ("h2", "2.2 Quality Attributes"),
    ("table", {
        "caption": "Quality attribute scenarios and their architectural "
                   "response",
        "header": ["Attribute", "Scenario", "Architectural response"],
        "widths": [2.6, 6.4, 6.5],
        "font": 10,
        "rows": [
            ["Isolation", "A learner submits destructive SQL",
             "Statement policy rejects it before execution and the sandbox "
             "runs with no network, a read-only root and a non-root user"],
            ["Determinism", "The same answer is submitted twice",
             "The submission hash returns the stored result; a changed answer "
             "is rejected with 409"],
            ["Resilience", "The LLM provider times out during grading",
             "The answer is stored, a durable job is queued with three "
             "attempts, and the rubric fallback produces the grade"],
            ["Auditability", "An administrator overrides a grade",
             "The change is written to the grade audit table and a new result "
             "version is published"],
            ["Traceability", "A learner asks why a concept is weak",
             "Every score is linked to an attempt, a question version and a "
             "concept tag"],
            ["Capacity", "Two SQL answers arrive at the same time",
             "A two-slot admission gate bounds sandbox concurrency and "
             "rejects with an explicit busy error"],
        ],
    }),
    ("h2", "2.3 Constraints"),
    ("p", "The system is a single-host Docker Compose deployment. PostgreSQL "
          "17 is the only durable store. The sandbox is a throw-away "
          "PostgreSQL container started through the Docker API, so the host "
          "Docker socket is a deployment dependency. The AI provider is an "
          "external OpenAI-compatible endpoint configured only by key, base "
          "URL and model name; no model weights are stored. These constraints "
          "are repeated as C1–C10 in the Proposal and are not re-derived "
          "here."),

    ("h1", "3. System Context"),
    ("p", "The context view has two human actors and three external systems. "
          "The learner sends practice requests, answers and view requests; "
          "the administrator sends curriculum, bank, rubric and review "
          "requests. The system calls the LLM provider for essay evaluation "
          "and question generation, redirects to Google or GitHub for OAuth, "
          "and sends password-reset mail through SMTP."),
    ("figure", str(ASSETS / "context.png"),
     "System context: two actors, the system and three external services"),
    ("table", {
        "caption": "Context elements and their interfaces",
        "header": ["Element", "Kind", "Interface"],
        "widths": [3.4, 2.6, 9.5],
        "font": 10,
        "rows": [
            ["Learner", "Actor",
             "Browser: sign-in, practice session, answer submission, profile"],
            ["Administrator", "Actor",
             "Browser: curriculum, question bank, review queue, settings"],
            ["DBCAS", "System",
             "FastAPI on /api/v1 plus a React single-page frontend"],
            ["LLM provider", "External system",
             "HTTPS chat-completions with a structured JSON contract"],
            ["OAuth providers", "External system",
             "Google and GitHub authorisation-code redirect"],
            ["SMTP service", "External system",
             "Password-reset mail; Mailpit locally on port 11025/18025"],
        ],
    }),

    ("h1", "4. Overall Architecture"),
    ("h2", "4.1 Logical Tiers"),
    ("p", "DBCAS is a four-tier application: presentation (React 19 and Vite), "
          "application programming interface (FastAPI on Python 3.13), data "
          "(PostgreSQL 17 through SQLAlchemy) and execution (an ephemeral "
          "PostgreSQL container used only to run learner SQL). The browser "
          "never reaches the database; the API is the only client of the "
          "database and of the execution tier."),
    ("figure", str(ASSETS / "logical.png"),
     "Logical architecture: presentation, API, data and execution tiers"),
    ("h2", "4.2 Containers"),
    ("table", {
        "caption": "Containers in the default local profile",
        "header": ["Container", "Responsibility", "Port"],
        "widths": [3.2, 9.6, 2.7],
        "font": 10,
        "rows": [
            ["frontend", "Nginx serving the built SPA and proxying /api/v1",
             "18080"],
            ["app", "FastAPI application and in-process worker", "18000"],
            ["db", "PostgreSQL 17 with the migrated schema", "internal"],
            ["init", "One-shot migrate and seed, then exits", "none"],
            ["executor-image", "Builds the sandbox image used per execution",
             "none"],
            ["mailpit", "Local SMTP capture for password reset", "11025/18025"],
        ],
    }),
    ("p", "A seventh service, qa-ai, exists only in the QA Compose profile and "
          "returns deterministic fake provider JSON so browser tests never "
          "call a real model. The execution container is not a Compose "
          "service: it is created per SQL execution with a random name, "
          "labelled with its owner, and removed on exit."),
    ("h2", "4.3 Backend Layering"),
    ("p", "The backend is layered by responsibility. Routers declare HTTP "
          "contracts and dependencies; services hold use cases and "
          "transactions; repository classes hold queries. The repository "
          "layer has 13 repository classes in a single module of about 1 700 "
          "lines; models and schemas are single modules as well. The "
          "dependency direction is one-way: repositories import no service "
          "and services import no router. Six router handlers still query the "
          "session directly, which the Code Standards document records as a "
          "known exception rather than a rule."),
    ("figure", str(MODULE_VIEW),
     "Module view: routers, services, repositories and shared infrastructure"),
    ("h2", "4.4 Frontend Structure"),
    ("p", "The frontend is a single-page application with 25 route elements "
          "over 24 distinct paths, role-guarded at the route level. Server "
          "state is fetched through one API client with a /api/v1 base URL; "
          "the client maps machine-readable error codes to localised "
          "messages, so a backend error code is also an i18n key. Interface "
          "text and question translations are separate catalogues: 1 700 "
          "leaf keys in English and the same 1 700 in Vietnamese, with zero "
          "drift."),

    ("h1", "5. Main Flows"),
    ("h2", "5.1 Sign-In and Session Establishment"),
    ("numbers", [
        "The browser posts credentials to /api/v1/auth/login, or follows the "
        "OAuth redirect for Google or GitHub.",
        "The API verifies the password hash, applies the login throttle, and "
        "issues a short-lived access token plus a refresh token.",
        "Every later request carries the access token; the dependency layer "
        "resolves the account and its capabilities.",
        "A refresh rotates the refresh token; a reused token is rejected.",
    ]),
    ("h2", "5.2 Practice Session Start"),
    ("numbers", [
        "The learner chooses concepts, difficulty bands, question count within "
        "the published limits, and source (bank or AI).",
        "The API opens a transaction, takes an advisory lock for the "
        "learner-assessment pair, and looks for a live session to make start "
        "idempotent.",
        "The planner builds the complete plan: exact count, per-format "
        "quotas, concept spread and no repeated version family.",
        "With the AI source, MCQ and essay items may be generated and "
        "validated first; SQL items always come from the validated bank.",
        "The plan and its configuration snapshot are persisted and the first "
        "question is served. A bank shortage aborts the start with an "
        "explicit error instead of a shorter session.",
    ]),
    ("h2", "5.3 Answer Submission and Grading"),
    ("numbers", [
        "The answer is submitted with the question identifier; the attempt "
        "row is locked and ownership is re-checked.",
        "A repeated submission with the same answer hash returns the stored "
        "result; a different answer is rejected with 409.",
        "MCQ is scored by exact option matching; SQL is executed in the "
        "sandbox and compared with the expected grid or table state; essay "
        "text is graded by the rubric pipeline.",
        "When the provider or the sandbox fails, the answer is kept and a "
        "durable grading job is queued; nothing is fabricated.",
        "A background worker claims the job with a lease, grades it, and "
        "publishes either the grade or an explicit failure.",
    ]),
    ("h2", "5.4 Result Publication and Review"),
    ("numbers", [
        "For a fixed-test session the finalize transaction publishes an "
        "official V1 result version with per-question and per-criterion "
        "scores.",
        "For practice and legacy sessions the result stays pending until an "
        "administrator reviews it.",
        "A learner may request a review inside a seven-day window with a "
        "reason; the request is idempotent by header key.",
        "An administrator claims the case with a 30-minute lease, then rejects "
        "it or regrades it; a deviation above 30 % needs explicit "
        "confirmation.",
        "The learner's cumulative profile is recomputed from published "
        "sessions only, so an unpublished session cannot move the profile.",
    ]),
    ("h2", "5.5 Competency Recompute"),
    ("p", "Concept scores are recomputed from published evidence, not "
          "incremented in place: identical evidence rewrites identical "
          "values. The computation is therefore safe to repeat after a "
          "regrade, a review decision or a worker restart, and a gap record "
          "is created only when the recomputed score is below the 70 % "
          "target."),

    ("h1", "6. AI Pipeline"),
    ("p", "Two AI roles are separated. The first builds the evaluation prompt "
          "with a deterministic template and is not a model call; it always "
          "reports builder_fallback true because no model is used for prompt "
          "construction. The second calls the provider and is the only place "
          "where a model is involved."),
    ("figure", str(ASSETS / "pipeline.png"),
     "AI pipeline: prompt assembly, provider call, validation, fallback and "
     "publication"),
    ("h2", "6.1 Question Generation"),
    ("numbers", [
        "An administrator selects a concept, a difficulty band and a type, and "
        "supplies a generation request identifier.",
        "The request digest is computed over the payload and the "
        "administrator; a replay returns the stored candidates and a changed "
        "payload is rejected.",
        "The provider returns structured JSON; the candidate is stored as a "
        "draft, never as a servable question.",
        "An administrator reviews and approves the candidate before it can "
        "enter the validated bank.",
    ]),
    ("h2", "6.2 Validation"),
    ("table", {
        "caption": "Validation layers applied to generated content",
        "header": ["Layer", "What it checks", "Failure behaviour"],
        "widths": [3.0, 8.2, 4.3],
        "font": 10,
        "rows": [
            ["Schema", "Required fields, types and score caps",
             "Rejected; nothing persisted"],
            ["Domain", "Concept tags exist, options are distinct, the answer "
             "is one of them, documentation paths resolve",
             "Rejected with a field-level error"],
            ["Execution", "SQL fixtures run and the expected result is "
             "produced by the reference solution",
             "Rejected; the item never becomes validated"],
            ["Duplication", "Normalised prompt fingerprint compared with the "
             "bank", "Rejected as a duplicate"],
        ],
    }),
    ("h2", "6.3 Fallback Behaviour"),
    ("table", {
        "caption": "Fallback behaviour per AI use case",
        "header": ["Use case", "On provider failure", "User-visible effect"],
        "widths": [3.4, 7.0, 5.1],
        "font": 10,
        "rows": [
            ["Essay evaluation", "Deterministic rubric evaluation, flagged "
             "evaluator_fallback", "Score and feedback still returned"],
            ["Practice question AI source", "Bank items replace generated "
             "items", "One substitution notice on the session"],
            ["Administrator generation", "Hard failure, transaction rolled "
             "back", "Error with a machine-readable code"],
            ["Two-stage audit", "Bounded retry, three attempts, then FAILED",
             "Stage marked failed, predecessor untouched"],
        ],
    }),
    ("h2", "6.4 Review Queue"),
    ("p", "Review cases move through REQUESTED, IN_REVIEW, REGRADED, REJECTED "
          "and EXPIRED. A claim is a lease of 30 minutes; an expired claim "
          "returns the case to the queue rather than deciding it. The worker "
          "never approves or rejects on the learner's behalf. A regrade that "
          "moves a score by more than 30 % requires a confirmed deviation "
          "before it can be published."),
    ("table", {
        "caption": "Review case guards",
        "header": ["Transition", "Guard"],
        "widths": [4.2, 11.3],
        "font": 10,
        "rows": [
            ["Create", "Owner only, seven-day window, reason of at least ten "
             "characters, official V1 must exist"],
            ["Claim", "Administrator is not the learner; revision must match"],
            ["Decide", "Claimant only, live lease, documented reason"],
            ["Regrade", "All question reports resolved, per-criterion limits, "
             "deviation confirmation above 30 %"],
            ["Expire", "Worker-driven; returns to queue or expires the case"],
        ],
    }),

    ("h1", "7. SQL Sandbox"),
    ("h2", "7.1 Two Modes"),
    ("p", "By default every statement runs read-only. The opt-in writable demo "
          "profile allows DML and DDL inside the ephemeral container, captures "
          "the resulting table state, and then destroys the container, so the "
          "write never reaches the application database."),
    ("h2", "7.2 Isolation Controls"),
    ("table", {
        "caption": "Sandbox container controls",
        "header": ["Control", "Value", "Purpose"],
        "widths": [4.0, 6.0, 5.5],
        "font": 10,
        "rows": [
            ["Network", "none", "No egress, no access to the application "
             "database"],
            ["Memory", "256 MB, swap disabled", "Bounded query working set"],
            ["CPU / PIDs", "1 CPU, 128 PIDs", "No fork bombs or CPU starvation"],
            ["Filesystem", "read-only root, tmpfs data and run",
             "No persistent write inside the container"],
            ["User / capabilities", "UID 10001, all capabilities dropped, "
             "no-new-privileges", "Non-root, no privilege escalation"],
            ["Lifetime", "45 s container, 3 000 ms statement timeout",
             "Bounded execution time"],
            ["Result size", "1 000 rows, 256 KB result, 16 KB SQL",
             "Bounded response and payload"],
            ["Admission", "Two concurrent slots", "Protects the host and the "
             "database"],
        ],
    }),
    ("h2", "7.3 Statement Policy"),
    ("p", "The policy is AST-based: the script is parsed, statement types and "
          "functions are checked against an allowlist, and unknown constructs "
          "fail closed. A read-only database role is granted separately, so a "
          "parser gap still cannot write. Multi-statement scripts are off by "
          "default and, when enabled, are bounded by statement count, total "
          "time and rows."),
    ("h2", "7.4 DML Table-State Grading"),
    ("p", "A data-manipulation task is graded on the state it leaves behind, "
          "not on the rows a SELECT would return. The expected result declares "
          "the tables to capture, whether order matters, and whether a table "
          "must be missing. After execution the captured state is compared "
          "table by table: missing tables fail first, then column sets, then "
          "rows as an ordered list or as a multiset. The first failing table "
          "names the reason, so feedback can say which table diverged."),

    ("h1", "8. Grading and Result Versions"),
    ("h2", "8.1 Scoring"),
    ("bullets", [
        "MCQ: the selected option is compared with the keyed option; the "
        "score is the question weight.",
        "SQL: the result grid is normalised (value kinds, row order, column "
        "order) and compared with the expected grid, or the captured table "
        "state is compared with the expected state.",
        "Essay: rubric criteria are scored within their maxima; the provider "
        "may assist, and the deterministic rubric is used when it cannot.",
        "Every score is stored with the question version and the rubric "
        "profile version that produced it.",
    ]),
    ("h2", "8.2 Status Vocabularies"),
    ("table", {
        "caption": "Grading and publication statuses",
        "header": ["Object", "Statuses"],
        "widths": [3.6, 11.9],
        "font": 10,
        "rows": [
            ["Attempt grading", "pending, graded, failed"],
            ["Grading job", "pending, processing, completed, failed"],
            ["Publication", "pending, official, analysis failed, regraded"],
            ["Review case", "REQUESTED, IN_REVIEW, REGRADED, REJECTED, EXPIRED"],
        ],
    }),
    ("h2", "8.3 Result Versions"),
    ("p", "A session points at exactly one current result version. The "
          "official V1 is created once, inside the finalize transaction; a "
          "late caller reuses it instead of creating a second version. A "
          "regrade creates a new version and moves the current pointer, so "
          "the previous result remains readable and the learner sees which "
          "version is current."),

    ("h1", "9. Security"),
    ("table", {
        "caption": "Security controls",
        "header": ["Area", "Control", "Evidence"],
        "widths": [3.0, 8.0, 4.5],
        "font": 10,
        "rows": [
            ["Authentication", "Password hash verification, JWT access token, "
             "rotating refresh token, OAuth authorisation code",
             "auth service and OAuth router"],
            ["Brute force", "Login throttle with a capacity lock and a "
             "per-identity rate limit", "login throttle service"],
            ["Authorization", "Role and capability checks in the dependency "
             "layer; administrators cannot review their own work",
             "deps and review flow"],
            ["Transport", "Security headers set by middleware and re-set by "
             "the catch-all error handler", "main and errors"],
            ["Secrets", "Environment only; the scanner reports zero findings "
             "in the tree and in history", "secret scan gate"],
            ["Sandbox", "Network none, non-root, dropped capabilities, "
             "read-only root", "executor command"],
            ["Privacy", "Name, email and authentication identifiers only; "
             "prompt text retained 60 days then purged", "stage service"],
            ["Audit", "Role changes, grade edits and AI stage runs are "
             "recorded with actor and time", "audit tables"],
        ],
    }),
    ("p", "Production release remains on hold because provider retention "
          "terms for learner data are not approved. The application contains "
          "no vendor-specific zero-retention flag; that decision belongs to "
          "the operator and is recorded as an open owner decision, not as an "
          "implemented control."),

    ("h1", "10. Architectural Decisions"),
    ("table", {
        "caption": "Decision record",
        "header": ["ID", "Decision", "Rationale", "Consequence"],
        "widths": [1.2, 4.6, 5.2, 4.5],
        "font": 10,
        "rows": [
            ["AD-01", "Modular monolith with in-process worker",
             "One deployable unit suits a capstone and keeps transactions "
             "simple", "No independent scaling of the worker"],
            ["AD-02", "Repository classes instead of an ORM-only service layer",
             "Query ownership and locking stay in one place",
             "One 1 700-line module; six router exceptions remain"],
            ["AD-03", "Ephemeral PostgreSQL container per SQL execution",
             "Strong isolation and a real PostgreSQL dialect",
             "Docker socket dependency and two-slot capacity"],
            ["AD-04", "AST allowlist plus a read-only role",
             "Defence in depth against parser gaps", "Some valid statements "
             "are rejected conservatively"],
            ["AD-05", "Deterministic rubric fallback",
             "A provider outage must not block grading", "Feedback is less "
             "nuanced when the fallback is used"],
            ["AD-06", "Database job lease instead of an external queue",
             "No extra infrastructure; restart-safe claims", "Retry latency "
             "is bounded by the worker tick"],
            ["AD-07", "Freeze the practice plan before question one",
             "Reproducible sessions and honest counts", "A bank shortage "
             "aborts the start"],
            ["AD-08", "Publish only from published evidence",
             "One number per concept that cannot be inflated",
             "A pending review delays the profile update"],
            ["AD-09", "URL-path versioning /api/v1",
             "Explicit contract for the SPA", "No header-based negotiation"],
            ["AD-10", "English and Vietnamese catalogues with parity",
             "Two audiences, one key set", "Every new key must be added twice"],
        ],
    }),

    ("h1", "11. Key Algorithms"),
    ("h2", "11.1 Adaptive Difficulty"),
    ("p", "Selection is deterministic: every tie-break ends in the question "
          "identifier, so the same state always yields the same question."),
    ("code", """pick(assessment, attempts, pool):
  served = len(attempts)
  if served < 3:                      # opening: three basic MCQs
      choose the easiest MCQ covering a concept not yet seen
  if served == 3:                     # opening verdict sets the Q4 level
      correct = count(score >= points)
      bias = 3 if correct == 3 else 2 if correct == 2 else 1
  wanted = type with the highest quota pressure (need / slots left)
  concept = an uncovered target, else the weakest concept
  if bias:        preferred = clamp(bias, min_d, max_d)
  elif last_correct: preferred = min(last_d + 1, max_d)
  else:           preferred = max(last_d - 1, min_d)
  return argmin over candidates of
         (abs(difficulty - preferred), difficulty, question_id)"""),
    ("p", "Only validated questions with a confirmed tag to a target concept "
          "inside the configured difficulty range are eligible, so an AI draft "
          "can never be served directly. Each serve writes one selection log "
          "row and marks is_fallback when the served type differs from the "
          "wanted type or a constraint had to be relaxed."),
    ("h2", "11.2 DML Table-State Grading"),
    ("code", """compare_state(actual, expected):
  if {a.table} != {e.table}: fail("tables")
  for each expected table:
      if expected.missing:            pass iff actual.missing
      elif actual.missing:            fail("<t>:missing")
      elif expected.columns and actual.columns != expected.columns:
                                      fail("<t>:columns")
      elif expected.ordered:          compare row tuples with ==
      else:                           compare row multisets
  return passed iff no failure"""),
    ("h2", "11.3 Idempotency"),
    ("p", "Four independent keys make retries safe: the answer submission hash "
          "returns the stored result for the same answer and rejects a "
          "changed one; the session start request identifier returns the "
          "existing live session; the review Idempotency-Key header returns "
          "the existing case; and the generation request digest returns the "
          "stored candidates. Cross-owner reuse of a key is a conflict, not a "
          "replay."),
    ("h2", "11.4 Job Lease"),
    ("code", """claim_grading_job(include_essay, lease_seconds=180):
  select job  where status = 'pending' and available_at <= now()
               or status = 'processing' and lease_until < now()
  order by available_at  limit 1  for update skip locked
  set status = 'processing', lease_until = now() + lease
  commit                                  # provider work holds no lock"""),
    ("p", "After grading, the worker re-reads the job and publishes only if "
          "the attempt count and the lease are unchanged; otherwise another "
          "worker has recovered the lease and the result is dropped. A "
          "failure requeues with a backoff of retry seconds multiplied by the "
          "attempt number, and the third failure marks the job failed. The "
          "same compare-and-set pattern protects the two-stage AI audit."),

    ("h1", "12. Modules and Allocation"),
    ("p", "The module view groups the eight routers into seven registered "
          "routers and the service layer into domains: identity and accounts, "
          "curriculum and concepts, question bank and generation, practice and "
          "assessment, evaluation and grading, competency and analytics, and "
          "operations (settings, readiness, mail). The allocation view maps "
          "those modules onto the six Compose containers and the ephemeral "
          "executor."),
    ("figure", str(ALLOCATION_VIEW),
     "Allocation view: modules mapped to containers and the ephemeral executor"),
    ("table", {
        "caption": "Service-to-module allocation",
        "header": ["Container", "Modules"],
        "widths": [3.4, 12.1],
        "font": 10,
        "rows": [
            ["frontend", "Routing, session guard, API client, i18n, charts"],
            ["app", "All routers and services, worker tick, prompt builder, "
             "evaluator"],
            ["db", "Schema, migrations, seed data, job and audit tables"],
            ["executor-image / executor", "Statement policy, dataset "
             "provisioning, result capture"],
            ["mailpit", "Password-reset mail capture"],
        ],
    }),

    ("h1", "13. User Stories by Role"),
    ("p", "The two roles below are the roles the backend enforces. Stories are "
          "grouped by role and each one names the feature that satisfies it; "
          "the identifiers match the Proposal (FR-xx) so the traceability "
          "matrix can be checked mechanically."),
    ("table", {
        "caption": "Learner stories",
        "header": ["ID", "Story", "Requirement"],
        "widths": [1.4, 12.0, 2.1],
        "font": 10,
        "rows": [
            ["US-L1", "As a learner I can register, sign in with a password or "
             "an OAuth provider, and reset my password by email.", "FR-01/02"],
            ["US-L2", "As a learner I choose the concepts, difficulty bands, "
             "count and source before a session starts.", "FR-06"],
            ["US-L3", "As a learner I answer MCQ, run SQL in an editor and "
             "write a short essay in one session.", "FR-08/09"],
            ["US-L4", "As a learner I see a score, per-concept profile and a "
             "ranked list of what to study next.", "FR-14"],
            ["US-L5", "As a learner I can request a review of a published "
             "result within seven days with a reason.", "FR-12/13"],
            ["US-L6", "As a learner I can switch the interface between English "
             "and Vietnamese.", "FR-16"],
        ],
    }),
    ("table", {
        "caption": "Administrator stories",
        "header": ["ID", "Story", "Requirement"],
        "widths": [1.4, 12.0, 2.1],
        "font": 10,
        "rows": [
            ["US-A1", "As an administrator I define course learning outcomes "
             "and concepts, and approve suggested mappings.", "FR-04"],
            ["US-A2", "As an administrator I curate a validated question bank "
             "with versions, tags and explanations.", "FR-05"],
            ["US-A3", "As an administrator I generate candidates with AI and "
             "review them before use.", "FR-15"],
            ["US-A4", "As an administrator I work the review queue: claim, "
             "reject or regrade with an audit trail.", "FR-12/13"],
            ["US-A5", "As an administrator I see cohort performance and the "
             "concepts that fail most often.", "FR-14"],
            ["US-A6", "As an administrator I provision accounts and roles, and "
             "every role change is audited.", "FR-03"],
        ],
    }),

    ("h2", "13.1 Requirement Traceability"),
    ("p", "Each functional requirement of the Proposal is realised by a "
          "specific part of this architecture; the table is the machine-"
          "checked link between the two documents."),
    ("table", {
        "caption": "Functional requirement to architecture section",
        "header": ["Requirement", "Architecture section"],
        "widths": [2.4, 13.1],
        "font": 10,
        "rows": [
            ["FR-01", "9 Security — registration and password storage"],
            ["FR-02", "5.1 Sign-in and session establishment"],
            ["FR-03", "9 Security — roles, capabilities and audit"],
            ["FR-04", "12 Modules — curriculum and concepts"],
            ["FR-05", "4.1 Data model and question version families"],
            ["FR-06", "5.2 Practice session start"],
            ["FR-07", "5.2 Practice session start — frozen plan"],
            ["FR-08", "4 Overall architecture and 5.3 answer submission"],
            ["FR-09", "7 SQL sandbox — read-only execution"],
            ["FR-10", "7.4 DML table-state grading"],
            ["FR-11", "8.1 Scoring and 6.3 fallback behaviour"],
            ["FR-12", "5.4 Result publication and review"],
            ["FR-13", "6.4 Review queue"],
            ["FR-14", "5.5 Competency recompute"],
            ["FR-15", "6 AI pipeline — generation, validation and fallback"],
            ["FR-16", "4.4 Frontend structure and 9 Security — audit"],
        ],
    }),

    ("h1", "14. Open Items"),
    ("bullets", [
        "[OWNER TO PROVIDE: approval decisions and signature dates for this "
        "document]",
        "[OWNER TO PROVIDE: public document URL]",
        "[OWNER TO PROVIDE: whether production deployment is in scope for the "
        "defence]",
        "Capacity of the SQL sandbox (two slots) is a measured limit, not a "
        "target; the owner must confirm whether it is acceptable for the "
        "demonstration.",
        "One open defect remains: the result heading can be slow on very "
        "large sessions; it is logged and monitored, not fixed.",
    ]),
]
