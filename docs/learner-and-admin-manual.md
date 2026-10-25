# Learner and administrator manual

## Personalized assessment and verified results

Assessments now offers Topic practice (an explicit short length with available
formats) and Formal assessment (the configured full mix). Choose one/multiple
curriculum skills and Easy/Medium/Hard. The selected bank questions and settings
are frozen when the assessment starts. Unsupported pools show an error.

Learners choose automatic release after grading or human verification in the
Finish confirmation dialog. This choice is recorded once per session before
finalization and cannot be changed after submission. Automatic release still
waits for all answers to finish grading. If time expires before the learner
chooses, the assessment's existing default applies. Older finalized results
and immutable start/configuration snapshots retain their original history.
Grading review shows provisional SQL/essay evidence, accepts/corrects
scores and explicitly publishes completed human reviews. Unpublished results
show a pending state. Cumulative competency in learner navigation combines
published evidence across attempts; administrator analytics links to the same
learner calculation and historical grading audit. Concept editing also supports
keywords and learning objectives.

See the [full workflow, lifecycle, data policy and manual verification steps](supervisor-implementation.md).

## Learner workflow

Register at `/register`, then use email/password or an enabled provider at
`/login`. Administrators land in their management area; Learners land on
`/dashboard`. A transient session-check failure offers retry without removing
the stored access token. Expired access is renewed within a bounded original
login window; a disabled or unauthenticated account is signed out.

At `/assessments`, choose Start, Resume, View result, or Start again as shown
by actual session state. Assessments have 60 minutes and a maximum of 13
questions: 10 MCQ, two SQL, one essay. The first three are basic MCQs at
difficulty 1–2. The server adaptively selects each later question; there is
no fixed question navigator and no client-selected question order.

At `/exam/:sessionId`, choose a lettered MCQ option, write SQL in the
highlighted editor with its schema viewer, or write an essay. Tab leaves the
SQL editor normally. Run in sandbox inspects SQL output; it does not submit
an answer. It supports PostgreSQL SELECT only, in a temporary isolated
schema, under a read-only role/transaction and resource limits. DML/DDL is
not enabled in the shared sandbox.

DML/DDL knowledge can be assessed through MCQ and essay questions, under the
owner-approved scope in requirements-decisions.md. The optional reviewed
knowledge benchmark adds these topics while retaining SELECT-only SQL execution.

Answers autosave to the server after a brief pause. Save draft saves
immediately. Draft saved means durable persistence, not grading. Refresh,
resume or reconnect restores that draft. A newer saved draft conflict is
explicit; load it before saving again. Submit answer & continue atomically
submits and advances; a lost response recovers authoritative server state.
Only the currently served question is available.

The countdown derives from the server expiry timestamp, not a browser's
wall clock. Warnings appear once at ten and five minutes. Finish requests
confirmation and includes the persisted current nonempty draft. At expiry,
the server finalizes once even if the browser is closed. Unsaved browser
keystrokes cannot be reconstructed; save the draft before disconnecting.
Empty drafts remain unanswered and provide no competency evidence.

MCQs grade deterministically. SQL uses typed semantic comparison over all
datasets and required techniques. Essays use the reviewed four-level rubric
and strictly validated AI output. Infrastructure failures can leave a saved
answer explicitly pending with bounded retries; invalid AI scoring never
becomes an invented score. Results show pending/failed grading clearly.

`/history` lists date, assessment, final status, overall result and concept
summaries. `/history/:sessionId` shows immutable prompts, submitted answers,
grading evidence and permitted answer keys after finalization. Question or
assessment edits cannot change that captured context.

Question content uses the locale selected when the assessment starts. The
question locale stays pinned for the session and its history even if the UI
language is changed; timer and saved answers are unaffected. English is the
canonical source. A missing Vietnamese translation falls back to English and
is flagged in the administrator question bank.

`/dashboard` presents server-provided competency and target comparisons.
Per-concept competency is earned points / possible points × 100, rounded
to two decimals. Only submitted, graded attempts and confirmed tags count.
A concept is a gap strictly below its target. Unbenchmarked concepts are
not counted as meeting a target. Category charts explicitly display the
mean of assessed concept percentages; this is a display summary, not a
separate official competency formula. Overall session result is a weighted
evidence result, unavailable while submitted answers await grading.

Study guidance is ranked by shortfall descending, then concept ID.
Prerequisite information explains readiness without reordering priorities.
AI explanations cannot alter scores or order and are invalidated when their
evidence/context changes. Only your own learner sessions are accessible.

## Administrator workflow

`/admin/accounts` displays each account's current role. Only a designated
role manager sees the account-provisioning and Grant/Revoke Administrator
actions. Each role change requires confirmation; grant only after verifying
the account owner. A newly promoted Administrator does not receive role
management authority. Ordinary Administrators can continue other admin work
but cannot grant/revoke roles, provision privileged accounts, or disable an
existing Administrator. Role changes are audited and take effect on the next
API request, including for existing tokens. The page also prevents
self-demotion; the backend protects the last active Administrator and role
manager transactionally.

The first deployment administrator is created with the trusted bootstrap CLI
described in the deployment guide, never through public registration. On an
existing installation, a database operator provisions the initial role
manager with the account-ID bootstrap command in the setup guide. The role
audit is available to role managers from `GET /api/v1/admin/accounts/role-audit`.

At `/admin/curriculum`, create/view/edit/delete Concepts and CLOs. Concept
codes and CLO codes identify existing records; edit their mutable fields.
Referenced concepts or mapped CLOs return an actionable deletion conflict.
The prerequisite editor loads its current IDs; an untouched Save preserves
them. Add/remove edges using the explicit ID set. Duplicates, self edges and
cycles are rejected, including serialized concurrent writes.

CLO confirmed mappings likewise load the actual confirmed set. AI suggest
adds pending links. Confirm or Reject is an explicit review decision. Generic
edits or a mapping Save do not implicitly approve pending AI links.

`/admin/questions` supports prompt search, type, concept, difficulty, status
filters and pagination. Create/edit all three formats. MCQ requires at least
two options with exactly one correct answer. SQL needs a permitted reference
SELECT and at least two executable datasets including an edge case, valid
expected rows, and explicit required-technique metadata. Essay requires
Incomplete, Partial, Mostly Complete, Complete with contiguous nonoverlapping
cent-precision score bands covering zero through the question's points.

The editor shows EN and VI prompt, explanation, MCQ option and essay rubric
display fields on the same question row. The `VI` bank marker indicates
whether current Vietnamese text matches the canonical content version. Rubric
band names and score ranges remain canonical for grading; localized labels and
criteria are presentation text.

Validate an item before it can enter a live assessment. SQL references are
checked in the real sandbox before validation. AI tags, difficulty and
criteria stay pending until their dedicated approval actions. Generic
question edits preserve AI review status. Editing a validated question
demotes it to draft; editing a used question creates an immutable historical
version and a new draft. Retire obsolete items instead of deleting evidence.

`/admin/assessments` fixes the formal question/time mix and edits target
concepts, allowed difficulty ranges and passing targets. Activation requires
enough distinct valid families for the whole mix, target coverage and the
mandatory opening MCQs. Fix the returned bank problems before trying again.
Use Close to end availability. Closed → draft creates a new version;
historical sessions retain their configuration. Competing actions are
disabled while an assessment save/activation is in progress.

`/admin/candidates` generates reviewed AI candidates outside the live bank.
Automatic checks are separate from human approval. Inspect the structured
payload/checks, then approve a passing candidate into the bank or reject it.
No unreviewed AI dataset runs with broad database administrative privileges.

`/admin` selects an assessment cohort, shows concept breakdown, categories,
gap prevalence and a daily result trend, and supports learner/session
drill-down. Cohort means learners assessed in the selected assessment; the
formal schema has no independent class/cohort entity. All metrics come from
the backend. Empty cohorts and pending grades are explicit states.

## Keyboard, motion and small screens

Use visible focus rings and normal tab order. Scrollable schema/result/data
regions can receive keyboard focus. Dialogs cover the viewport, lock page
scroll, make the background inert, trap focus, close on Escape when idle,
and restore focus. Destructive dialogs initially focus the safe action.
Reduced-motion preference disables reveals and decorative transforms.
Tables scroll within their region on small screens.
