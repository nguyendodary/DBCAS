# Requirements completion and release hardening

Starting point: develop2, 9f7353df9a359f710c901d09f0b11bd9fd7a0df9.
Remote baseline: b32742603983d11eb04a120261123cfe538a16f4 (0 behind, 6 ahead).
The six existing UI commits are preserved. No push or history rewrite is authorized.

## Authority

1. User Story Document 1.3 acceptance criteria (2 October 2026).
2. Architecture Design 1.2 behavior/security (2 October 2026).
3. Proposal 1.4 FR01–FR16, NFR01–NFR09 (2 October 2026).
4. Database Design 1.3 persistence contract (2 October 2026).
5. API conventions; implementation extensions are subordinate.

The four authoritative DOCX documents live in the parent workspace, as required
by CONTRIBUTING.md. Their extracted text and document alignment reports were
reviewed. The preceding full audit supplies R01–R75 and F01–F34; the trackers
record its findings and require fresh implementation/test/runtime evidence.

## Formal conflict resolved by owner scope decision

Proposal section 6.2 includes practical DML/DDL sandbox tasks. User Story
Learner 4 and Architecture UC13/QA03 explicitly require a read-only learner role
and a read-only rolled-back transaction. Preserve read-only assessment execution;
assess DML/DDL through MCQ/essay. On 11 October 2026 the owner explicitly selected
this scope; see ../requirements-decisions.md. The supplemental reviewed bank
provides these knowledge questions. No shared/system-database mutation is permitted.

Guidance is not an unresolved conflict: formal shortfall-descending priority wins.
Prerequisite state may explain readiness without reordering the list.

## Implementation groups

1. Production authentication/configuration, token purpose, error envelopes.
2. Additive migrations and historical context/draft/job persistence.
3. SQL typed semantics, resource limits, setup validation and bank eligibility.
4. Strict rubric/LLM validation, validated cache, privacy and human review.
5. Transactional drafts, idempotent submission, authoritative timeout/background jobs.
6. Historical competency/gaps, formal guidance and safe curriculum operations.
7. Complete admin/learner controls; retain premium UI and improve accessibility.
8. Benchmark pack, browser/migration/load release gates and deployment manuals.

Run targeted tests after each major group, then complete frontend/backend suites,
real PostgreSQL/sandbox tests, migration matrix, browser journeys, load test and
build/compile/import/compose checks. Tests must isolate application data and mock
the provider HTTP transport; no paid LLM call is authorized.

## Completion evidence

requirements.json: all R01–R75, before status, authority, change, acceptance,
planned tests and final verification. findings.json: all F01–F34, severity,
remediation and verification. OPEN cannot become VERIFIED without recorded tests
and runtime evidence. Retained archival history is documented, never rewritten.

Before each commit: reread CONTRIBUTING.md and AGENTS.md, inspect status/staged
diff and full message, verify human attribution and no tool-credit trailers.
