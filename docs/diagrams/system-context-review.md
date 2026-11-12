# System Context — semantic comparison

The current root Architecture/Proposal DOCX retains the detailed original. The rejected collapsed redraw is not the baseline. External originals remain unchanged.

| Version | Nodes | Relationships |
|---|---:|---:|
| Original / current root DOCX | 4 | 21 directed flows |
| Rejected redraw | 5 | 4 broad bidirectional connections |
| Updated companion | 6 | 51 directed flows |

All four original nodes and all 21 original directed labels are retained. Thirty code-supported exchanges are added, including two separate OAuth services. No original relationship is removed, merged or relabeled. Independent grade review/publication, generation/curation, capability/audit/outcome exchanges remain distinct.

[Editable diagram](system-context.svg) · [Complete ledger](system-context.json)

| ID | Source → destination | Original / final label | Action | Evidence / justification |
|---|---|---|---|---|
| C01 | learner → dbcas | Assessment requests | KEEP | `backend/app/routers/sessions.py; backend/app/routers/auth.py; backend/app/services/guidance_service.py` — Preserves the original directed contractual interaction. |
| C02 | learner → dbcas | MCQ / SQL / Conceptual answers | KEEP | `backend/app/routers/sessions.py; backend/app/routers/auth.py; backend/app/services/guidance_service.py` — Preserves the original directed contractual interaction. |
| C03 | learner → dbcas | View requests | KEEP | `backend/app/routers/sessions.py; backend/app/routers/auth.py; backend/app/services/guidance_service.py` — Preserves the original directed contractual interaction. |
| C04 | learner → dbcas | Authentication requests | KEEP | `backend/app/routers/sessions.py; backend/app/routers/auth.py; backend/app/services/guidance_service.py` — Preserves the original directed contractual interaction. |
| C05 | learner → dbcas | Registration requests | KEEP | `backend/app/routers/sessions.py; backend/app/routers/auth.py; backend/app/services/guidance_service.py` — Preserves the original directed contractual interaction. |
| C06 | dbcas → learner | Assessment results | KEEP | `backend/app/routers/sessions.py; backend/app/routers/auth.py; backend/app/services/guidance_service.py` — Preserves the original directed contractual interaction. |
| C07 | dbcas → learner | Competency profile & gaps | KEEP | `backend/app/routers/sessions.py; backend/app/routers/auth.py; backend/app/services/guidance_service.py` — Preserves the original directed contractual interaction. |
| C08 | dbcas → learner | Study guidance | KEEP | `backend/app/routers/sessions.py; backend/app/routers/auth.py; backend/app/services/guidance_service.py` — Preserves the original directed contractual interaction. |
| C09 | admin → dbcas | CLOs & Concepts | KEEP | `backend/app/routers/admin.py` — Preserves the original directed contractual interaction. |
| C10 | admin → dbcas | Questions | KEEP | `backend/app/routers/admin.py` — Preserves the original directed contractual interaction. |
| C11 | admin → dbcas | Rubrics | KEEP | `backend/app/routers/admin.py` — Preserves the original directed contractual interaction. |
| C12 | admin → dbcas | Assessment configuration | KEEP | `backend/app/routers/admin.py` — Preserves the original directed contractual interaction. |
| C13 | dbcas → admin | Learner performance | KEEP | `backend/app/routers/admin.py` — Preserves the original directed contractual interaction. |
| C14 | dbcas → admin | Competency gap analytics | KEEP | `backend/app/routers/admin.py` — Preserves the original directed contractual interaction. |
| C15 | dbcas → admin | AI mapping suggestions | KEEP | `backend/app/routers/admin.py` — Preserves the original directed contractual interaction. |
| C16 | dbcas → llm | Gap explanation requests | KEEP | `backend/app/services/competency_service.py; backend/app/services/essay_grading.py; backend/app/services/ai_admin_service.py` — Preserves the original directed contractual interaction. |
| C17 | dbcas → llm | Essay evaluation requests | KEEP | `backend/app/services/competency_service.py; backend/app/services/essay_grading.py; backend/app/services/ai_admin_service.py` — Preserves the original directed contractual interaction. |
| C18 | dbcas → llm | CLO/Concept mapping requests | KEEP | `backend/app/services/competency_service.py; backend/app/services/essay_grading.py; backend/app/services/ai_admin_service.py` — Preserves the original directed contractual interaction. |
| C19 | llm → dbcas | Mapping suggestions | KEEP | `backend/app/services/competency_service.py; backend/app/services/essay_grading.py; backend/app/services/ai_admin_service.py` — Preserves the original directed contractual interaction. |
| C20 | llm → dbcas | Essay evaluation results | KEEP | `backend/app/services/competency_service.py; backend/app/services/essay_grading.py; backend/app/services/ai_admin_service.py` — Preserves the original directed contractual interaction. |
| C21 | llm → dbcas | Gap explanations | KEEP | `backend/app/services/competency_service.py; backend/app/services/essay_grading.py; backend/app/services/ai_admin_service.py` — Preserves the original directed contractual interaction. |
| C22 | admin → dbcas | Grade verification decisions | ADD | `backend/app/routers/admin.py:grading-reviews` — Implemented external interaction omitted from the original figure; no existing relationship replaced. |
| C23 | dbcas → admin | Grade review queue and evidence | ADD | `backend/app/routers/admin.py:grading-reviews` — Implemented external interaction omitted from the original figure; no existing relationship replaced. |
| C24 | admin → dbcas | Role changes (role manager only) | ADD | `backend/app/services/auth_service.py` — Implemented external interaction omitted from the original figure; no existing relationship replaced. |
| C25 | dbcas → admin | Role-management capability | ADD | `backend/app/routers/admin.py:role-management` — Implemented external interaction omitted from the original figure; no existing relationship replaced. |
| C26 | admin → dbcas | Question candidate generation requests | ADD | `backend/app/routers/admin.py:question-candidates` — Implemented external interaction omitted from the original figure; no existing relationship replaced. |
| C27 | dbcas → admin | Draft question candidates | ADD | `backend/app/services/ai_admin_service.py` — Implemented external interaction omitted from the original figure; no existing relationship replaced. |
| C28 | dbcas → llm | Question candidate generation requests | ADD | `backend/app/services/ai_admin_service.py` — Implemented external interaction omitted from the original figure; no existing relationship replaced. |
| C29 | llm → dbcas | Unreviewed question candidates | ADD | `backend/app/services/ai_admin_service.py` — Implemented external interaction omitted from the original figure; no existing relationship replaced. |
| C30 | dbcas → llm | Question concept tagging requests | ADD | `backend/app/services/ai_admin_service.py` — Implemented external interaction omitted from the original figure; no existing relationship replaced. |
| C31 | llm → dbcas | Unconfirmed question tags | ADD | `backend/app/services/ai_admin_service.py` — Implemented external interaction omitted from the original figure; no existing relationship replaced. |
| C32 | dbcas → google | Authorization redirect (via browser) | ADD | `backend/app/services/oauth.py` — Implemented external interaction omitted from the original figure; no existing relationship replaced. |
| C33 | google → dbcas | Authorization code + state (via browser) | ADD | `backend/app/services/oauth.py` — Implemented external interaction omitted from the original figure; no existing relationship replaced. |
| C34 | dbcas → google | Authorization-code token exchange | ADD | `backend/app/services/oauth.py` — Implemented external interaction omitted from the original figure; no existing relationship replaced. |
| C35 | google → dbcas | Access token / exchange error | ADD | `backend/app/services/oauth.py` — Implemented external interaction omitted from the original figure; no existing relationship replaced. |
| C36 | dbcas → google | Authenticated profile request | ADD | `backend/app/services/oauth.py` — Implemented external interaction omitted from the original figure; no existing relationship replaced. |
| C37 | google → dbcas | Profile / verified identity claims | ADD | `backend/app/services/oauth.py` — Implemented external interaction omitted from the original figure; no existing relationship replaced. |
| C38 | dbcas → github | Authorization redirect (via browser) | ADD | `backend/app/services/oauth.py` — Implemented external interaction omitted from the original figure; no existing relationship replaced. |
| C39 | github → dbcas | Authorization code + state (via browser) | ADD | `backend/app/services/oauth.py` — Implemented external interaction omitted from the original figure; no existing relationship replaced. |
| C40 | dbcas → github | Authorization-code token exchange | ADD | `backend/app/services/oauth.py` — Implemented external interaction omitted from the original figure; no existing relationship replaced. |
| C41 | github → dbcas | Access token / exchange error | ADD | `backend/app/services/oauth.py` — Implemented external interaction omitted from the original figure; no existing relationship replaced. |
| C42 | dbcas → github | Authenticated profile request | ADD | `backend/app/services/oauth.py` — Implemented external interaction omitted from the original figure; no existing relationship replaced. |
| C43 | github → dbcas | Profile / provider user ID | ADD | `backend/app/services/oauth.py` — Implemented external interaction omitted from the original figure; no existing relationship replaced. |
| C44 | dbcas → github | Verified email list request | ADD | `backend/app/services/oauth.py` — Implemented external interaction omitted from the original figure; no existing relationship replaced. |
| C45 | github → dbcas | Email addresses + verification flags | ADD | `backend/app/services/oauth.py` — Implemented external interaction omitted from the original figure; no existing relationship replaced. |
| C46 | admin → dbcas | Result publication requests | ADD | `backend/app/routers/admin.py:grading-reviews/publish` — Separate independent publication, role-audit and curation exchanges; no business command is merged with another. |
| C47 | dbcas → admin | Publication outcome | ADD | `backend/app/services/grading_review.py` — Separate independent publication, role-audit and curation exchanges; no business command is merged with another. |
| C48 | dbcas → admin | Role audit history | ADD | `backend/app/services/auth_service.py:list_role_audit` — Separate independent publication, role-audit and curation exchanges; no business command is merged with another. |
| C49 | admin → dbcas | Question candidate curation decisions | ADD | `backend/app/routers/admin.py:question-candidates` — Separate independent publication, role-audit and curation exchanges; no business command is merged with another. |
| C50 | dbcas → admin | Candidate curation outcome | ADD | `backend/app/services/ai_admin_service.py` — Separate independent publication, role-audit and curation exchanges; no business command is merged with another. |
| C51 | dbcas → admin | Role change outcome | ADD | `backend/app/services/auth_service.py:set_account_role` — Separate independent publication, role-audit and curation exchanges; no business command is merged with another. |

## Modeling decisions

- Learner assessment/view/authentication/registration inputs and result/profile/guidance outputs are separate original interactions. All original labels remain verbatim.
- The context represents business information exchanges, not every HTTP call in order. Review queue/detail reads share the evidence-viewing goal; provider token/error outputs are alternatives to one exchange. Independent administrative commands remain separate.
- CLO mapping, tagging and candidate generation each have separate LLM inputs and unreviewed outputs. LLM output cannot decide deterministic competency or publication.
- Google and GitHub are separate services. Authorization redirects/callbacks are browser-mediated; token/profile requests/responses are server-side. GitHub verified-email requests/responses remain additional distinct arrows.
- The SQL sandbox and application database are internal to DBCAS. Their isolation/dependencies belong in the container/allocation/physical diagrams.
- Automatic translation is not asserted: no translation task is approved/configured. Manual reviewed translations remain internal question-bank functionality.

### Acceptance amendment - 23 October 2026

C43 retains its GitHub-to-DBCAS direction and profile response. Its label is clarified from ?Profile / verified identity claims? to ?Profile / provider user ID?: `oauth.py:_github_identity` obtains verified email separately through C44-C45. All 51 relationships and all 21 original labels remain; no relationship is added, merged or removed in this acceptance pass. The context is a detailed external-interaction view, with retained OAuth protocol detail; it is not a time-ordered sequence or a minimal C4 summary.
