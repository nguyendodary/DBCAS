# OAuth restoration and project audit implementation plan

**Goal:** Restore discoverable Google/GitHub authentication, audit configuration and live flows, safely classify the workspace, and align the owner's three English Word documents.

**Execution:** One writer in this session, on `develop2` only. The owner's instruction to start and continue supplies the execution method. Commit and push each completed item after reviewing the staged diff and CONTRIBUTING.md.

**Baseline:** `60f075a`; clean worktree; HEAD stable from 09:19:08 to 09:19:38 +0700 on 2026-11-11. Fetch, checkout and pull/rebase completed. Existing OpenCode process has no observed project-writing child; no process was killed. Preserve all healthy demo containers during investigation.

## Constraints and review focus

- Never expose environment values or commit secrets. Automated tests disable live AI; real-key checks skip without a key. A new request ledger reserves at most five requests before transport, solely for one builder/evaluator and one generation check.
- Preserve tests and production behavior. Replace the regression's incorrect hide expectation with stronger visibility, availability and navigation assertions.
- Keep provider controls present during loading, absent configuration and metadata failure; safe localized feedback must prevent navigation.
- Verify server-side state, fixed callback destinations, verified-email linking, Learner creation, one-time handoff and rotating sessions using fake provider HTTP only.
- Compare live routes/configuration with docs and UI; report legitimate API-only operations separately from defects.
- Inventory first. Preserve main/stash/backups/personal and teammates' material. Quarantine only demonstrated unreferenced items, outside the repository. Permanent deletion requires owner confirmation.
- Edit only Proposal, Architecture and Database v1.2 in place, preserving runs. No diagram insertion without required owner approval.

## Items

- [x] Recover handover, process identity, stable HEAD, branch, commit identity and protected resources.
- [x] Capture login/register before state in both themes at 1280/390; trace frontend, endpoint, environment, history, CSS, translations and regression tests in that order.
- [x] Add failing visibility tests; fix provider UI and Compose callbacks; extend fake-provider backend/browser security and session checks; document OAuth setup; verify and update handover. Commit/push follows staged review.
- [ ] Audit route/UI/config coverage, learner/admin flows, accessibility, Mailpit, account lock/unlock and refresh rotation. Fix each evidenced defect with regression coverage and a separate reviewed commit/push.
- [ ] Run bounded live AI checks using a new ledger and verify exact builder/evaluator prompt equality, model negotiation, timeout and fallback offline.
- [ ] Inventory and classify every root item, main/stash delta and repository candidates. Quarantine proven DELETE entries; run affected gates; publish evidence and confirmation command.
- [ ] Audit and update only three owner Word documents plus current deliverables/index/status; verify Word and rendered pages, update handover, commit and push.
- [ ] Run affected final gates, fake OAuth scenario three times, no-env clone, rebuild/restart demo, both demo logins and pushed-HEAD CI. Record actual totals, limitations and final commit list.
