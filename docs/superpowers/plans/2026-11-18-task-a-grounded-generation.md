# Task A Grounded Generation Implementation Plan

**Goal:** Deliver bounded, evidence-backed question drafts from approved CLO-linked documents, with administrator review before publication.

**Architecture:** Extend the existing Task A worktree implementation. Select a bounded set of document chunks using deterministic lexical relevance and stable tie breaks; preserve source hashes and offsets through the existing candidate review flow. Serialize document state changes with publication and retain PR #26 ingestion behavior.

**Tech Stack:** Python, FastAPI, SQLAlchemy, PostgreSQL 17, pytest, Ruff.

**Spec:** Repository owner request and PR #26 follow-up requirements.

## Global Constraints

- Preserve all existing uncommitted work; do not reset, clean, stash, switch, commit, push, merge, or remove worktrees.
- Do not use shared development databases or another agent's worktree for tests.
- Existing administrator authorization and document lifecycle remain authoritative.
- Untrusted document content must never become instructions or enter application logs.

## Review Focus

- Missing, mixed approved/unapproved, or foreign documents must fail before model invocation.
- Large document collections must use bounded retrieval, bounded prompt context, and deterministic ordering.
- Tampered source, citation, offsets, CLO or concept mappings must block approval.
- Repeated or concurrent requests and approvals must be idempotent and duplicates must not publish.
- Archived or unlinked documents must not race with generation or candidate publication.

## Tasks

1. Inspect the existing service, ingestion, approval, tests and PR #26. Preserve the original ten changed files outside the worktree and run baseline static checks.
2. Extend `backend/tests/test_document_generation.py` with focused cases for bounded relevance selection, explicit document eligibility, provenance tampering, duplicate generation, request retry, and concurrency. Verify failures before implementation where isolated integration infrastructure permits.
3. Complete `backend/app/services/document_generation.py` using capped deterministic retrieval, evidence checks, and existing candidate validation. Update document lifecycle synchronization only where necessary for concurrent publication safety.
4. Verify authorization, approval lifecycle, injection isolation and PR #26 compatibility with focused tests against uniquely owned ephemeral infrastructure. Run static checks and documentation consistency checks; report any gate that cannot safely run.
5. Review the final diff, preserve all owner work, and report delivery readiness and exact next commit/PR steps. Do not commit or publish.