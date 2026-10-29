# Learner and administrator manual

## Personalized assessment and verified results

Assessments now offers Topic practice (an explicit short length with available
formats) and Formal assessment (the configured full mix). Choose one/multiple
curriculum skills or every skill of the published rules, plus a preferred
Easy/Medium/Hard band. Search skills by name or code; selected
skills remain visible and the form shows their count. Formal sessions freeze the
selected scope and delivery policy at the start, then serve questions adaptively
inside the assessment's allowed difficulty range (see
[formal adaptive delivery](formal-adaptive-delivery-20261029.md)). Where the
approved bank genuinely cannot supply the mandatory mix for a selection, the
start fails with an actionable shortage explanation and creates no session.

Administrators configure Immediate or Human verified release on assessment
drafts. Grading review shows provisional SQL/essay evidence, accepts/corrects
scores, can re-run a submitted SQL answer in the isolated sandbox, and explicitly
publishes completed human reviews. Unpublished results
show a pending state. Cumulative competency in learner navigation combines
published evidence across attempts; administrator analytics links to the same
learner calculation and historical grading audit. Concept editing also supports
keywords and learning objectives.

See the [full workflow, lifecycle, data policy and manual verification steps](supervisor-implementation.md).

## Learner workflow

Register at `/register`, then use email/password or an enabled provider at
`/login`. Administrators land in their management area; Learners land on
`/dashboard`. Administrator accounts cannot take assessments: learner assessment
routes reject them even on a legacy dual-role account. A transient session-check
failure offers retry without removing
the stored access token. Expired access is renewed within a bounded original
login window; a disabled or unauthenticated account is signed out.

At `/assessments`, use the personalized form to select a published rule set,
one or more skills (or every skill), Easy/Medium/Hard, and Topic practice or
Formal assessment. Practice uses the exact selected length and available formats
with its plan frozen at creation. Formal sessions retain the configured full mix
and duration, but questions are served adaptively: the selected band is the
starting band, three basic MCQs open the session, later questions move at most
one band at a time inside the assessment's allowed range, and the mix is served
in strict MCQ → SQL → essay order. An insufficient approved bank stops the start
with a precise explanation instead of reducing the count or relaxing validation.
A formal session also selects the question source: the approved bank (default)
or AI-generated delivery, which is offered only where the deployment provides an
LLM provider and session-question storage, keeps the three bank openers, and
validates every generated question before it appears. Without either requirement
the AI choice is refused with an explicit unavailable error, never a silent
substitution. The table also retains the original adaptive Start/Resume path;
both that path and the personalized formal flow open with three basic MCQs and
adapt later selection. Current
new formal rules are 60 minutes, 10 MCQ, two SQL and one essay; historical
published rules retain their captured limits. There is no backward navigator
or client-selected question order.

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

The interface language selector also requests question prompts, options, explanations
and rubric labels in that language. Only reviewed translations captured in the
frozen practice plan or snapshotted when a formal or legacy question is served can be displayed; otherwise the actual original remains visible
with a content-language notice. The recorded assessment locale is fixed, while this
read-only display can change. Answers, option IDs, SQL, timers, scores, grading
narratives and stored evidence are never translated or rewritten by this selector.
Legacy snapshots without language metadata remain English; snapshots without a
translation fall back to their original. A later bank translation does not retrofit
an earlier snapshot.

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
The prerequisite editor loads its current selections; an untouched Save preserves
them. Expand the editor and search/select prerequisites by name or code. Self edges and
cycles are rejected, including serialized concurrent writes.

CLO confirmed mappings likewise use named selections and load the actual confirmed set. AI suggest
adds pending links. Confirm or Reject is an explicit review decision. Generic
edits or a mapping Save do not implicitly approve pending AI links.

`/admin/questions` supports prompt search, type, concept, difficulty, status
filters and pagination. Create/edit all three formats. MCQ requires at least
two options with exactly one correct answer. SQL needs a permitted reference
SELECT and at least two executable datasets including an edge case, valid
expected rows, and explicit required-technique metadata. Essay requires
Incomplete, Partial, Mostly Complete, Complete with contiguous nonoverlapping
cent-precision score bands covering zero through the question's points.

To create a question:

1. Choose MCQ, SQL or Essay. Type the question in Vietnamese or English. The editor
   detects recognizable prose; check or correct the language for short text or SQL.
2. Enter the original prompt and relevant answers. MCQ uses one correct-answer
   radio button; option labels stay stable when other options are removed.
   SQL datasets remain an explicit technical authoring field with format guidance.
   Essay uses structured criteria and minimum/maximum score fields. Enter the
   reviewed score ranges yourself; the form never invents grading weights.
3. Choose a labeled difficulty (Easy 1–2, Medium 3, Hard 4–5) and search/select
   concepts by name or code. Mark required techniques where needed. The internal
   1–5 classification remains unchanged.
4. Optionally open **Optional reviewed translation**. Translate every relevant
   option, explanation and rubric criterion. Confirm review to save the translation.
   Unchecked translation edits are not saved. Original-only questions are allowed.
5. Use **Preview question**, select the preview language, then **Save draft**.
   Choose **Actions → Validate** when the question meets all grading requirements.

Drafts can omit concepts, datasets, rubric bands or all MCQ answers. If any MCQ
answers are supplied, complete at least two and identify exactly one correct
answer. Validation remains the serving gate. Errors appear next to the save
controls. The bank indicates original language and current reviewed translations.
The original language is fixed after creation; editing content does not relabel it.
Existing translations load for editing but are not silently reviewed again.
Source edits make unchanged translations stale and preserve their stored text.
Check review only after verifying them against the new original. Grade bands
keep their existing identifiers and boundaries; translated labels and criteria
are display text. Source references stay under the provenance disclosure.

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
Automatic checks are separate from human approval. Read the prompt, options,
reference answer and rubric criteria alongside the checks. Full JSON and datasets
are under **Advanced payload and datasets (JSON)** for technical inspection.
Approve a passing candidate into the bank or reject it.
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

## Built-in Help guide

Every signed-in page and the sign-in/sign-up screens carry a **Help** button
(`frontend/src/components/HelpGuide.jsx`, rendered through `HelpProvider` in
`frontend/src/App.jsx`). It opens one modal guide - not a separate route - with ten fixed sections: overview,
start, modes, question types, SQL, essay, results, language, accessibility and
troubleshooting, plus a learner-only or administrator-only section depending on your
role. The guide is context-aware: opening it from `/dashboard`, `/assessments`,
`/exam/…`, `/history`, `/history/…`, `/competency`, `/settings`, `/admin`,
`/admin/curriculum`, `/admin/questions`, `/admin/candidates`, `/admin/assessments`,
`/admin/grading` or `/admin/accounts` prepends the notes recorded for that screen, and
anything else falls back to the generic overview. Content follows the interface
language from the shared translation files, so switching language changes the guide text
only; nothing in the guide mutates a session, an answer or a grade. The modal behaves
like every other dialog here: it is `aria-modal`, locks the background inert, traps
focus, closes on Escape and restores focus to the Help button. There is no `/help` URL
to bookmark and no keyboard shortcut - use the button.

## Question-bank language and historical evidence

Bank titles follow the interface language when a current reviewed translation
exists, with the original as fallback. Search finds original and current reviewed
translated prompts. Editing always opens the original source and its separate
translation; switching interface language does not rewrite either.

Assessment display uses its captured content rather than later bank edits.
Legacy evidence without a captured question snapshot shows the known original
language; later bank translations are not treated as historical evidence.

When separately enabled by the operator, **Prepare translation draft** appears
under the optional translation section for missing translations. It prepares
text for your review; it does not approve or save it. Check every answer option,
technical expression and rubric criterion before confirming review and saving.
You can still save the original during preparation or after a provider error.
See [optional draft preparation](draft-question-translation.md) for its limits.
