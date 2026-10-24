# Diagram acceptance review - 23 October 2026

This acceptance pass re-read the ten existing editable companions, their original inventory and the code paths below. It does not replace the earlier [complete semantic baseline](semantic-review.md). Original university DOCX/raster figures remain unchanged. Counts are evidence, not targets.

## System Context: every relationship

The figure is a **detailed external-interaction context**. It communicates one DBCAS boundary, two human roles, and three optional provider systems. C32-C45 deliberately retain OAuth protocol detail; this is finer than a minimal C4 Level 1 context, but no chronology, lifeline or internal implementation component is implied. The semantic ledger is the navigable detail companion; no valid exchange is silently moved or dropped.

C03 covers history/evidence view requests; C01 starts an assessment. C09/C10/C11 distinguish curriculum, items and grading criteria even though some share CRUD payloads. C13/C14 distinguish performance records from aggregate gaps. C15/C19, C27/C29 and C31 describe different boundaries/stages of proposals, not duplicate messages on one boundary. C22/C46 and their outcomes preserve independent verification/publication decisions. Token, profile and verified-email exchanges have distinct purposes. Alternative token/error outcomes share one response contract.

| Flow | Source → destination | Meaning / displayed label | Requirement and exact code evidence | Abstraction / duplicate verdict |
|---|---|---|---|---|
| C01 | learner → dbcas | Assessment requests | UC12; R1-R3; [`routers/assessments.py`](../../backend/app/routers/assessments.py) `start_assessment_session` (line 27) | Business boundary interaction; distinct meaning, retained |
| C02 | learner → dbcas | MCQ / SQL / Conceptual answers | UC13-14; [`routers/sessions.py`](../../backend/app/routers/sessions.py) `submit_and_advance` (line 57) | Business boundary interaction; distinct meaning, retained |
| C03 | learner → dbcas | View requests | UC16-18; [`routers/sessions.py`](../../backend/app/routers/sessions.py) `list_sessions` (line 72) | Business boundary interaction; distinct meaning, retained |
| C04 | learner → dbcas | Authentication requests | UC02; [`routers/auth.py`](../../backend/app/routers/auth.py) `login` (line 24) | Business boundary interaction; distinct meaning, retained |
| C05 | learner → dbcas | Registration requests | UC01; [`routers/auth.py`](../../backend/app/routers/auth.py) `register` (line 18) | Business boundary interaction; distinct meaning, retained |
| C06 | dbcas → learner | Assessment results | UC15; R5-R6; [`routers/sessions.py`](../../backend/app/routers/sessions.py) `get_session_evidence` (line 118) | Business boundary interaction; distinct meaning, retained |
| C07 | dbcas → learner | Competency profile & gaps | UC16-17; R7; [`routers/sessions.py`](../../backend/app/routers/sessions.py) `get_competency_profile` (line 146) | Business boundary interaction; distinct meaning, retained |
| C08 | dbcas → learner | Study guidance | UC17; [`routers/sessions.py`](../../backend/app/routers/sessions.py) `get_study_guidance` (line 170) | Business boundary interaction; distinct meaning, retained |
| C09 | admin → dbcas | CLOs & Concepts | UC05; R8; [`routers/admin.py`](../../backend/app/routers/admin.py) `create_concept` (line 191) | Business boundary interaction; distinct meaning, retained |
| C10 | admin → dbcas | Questions | UC07; R4; [`routers/admin.py`](../../backend/app/routers/admin.py) `create_question` (line 336) | Business boundary interaction; distinct meaning, retained |
| C11 | admin → dbcas | Rubrics | UC07 rubric payload; [`routers/admin.py`](../../backend/app/routers/admin.py) `replace_question` (line 354) | Business boundary interaction; distinct meaning, retained |
| C12 | admin → dbcas | Assessment configuration | UC09; R5; [`routers/admin.py`](../../backend/app/routers/admin.py) `create_assessment` (line 543) | Business boundary interaction; distinct meaning, retained |
| C13 | dbcas → admin | Learner performance | UC11; [`routers/admin.py`](../../backend/app/routers/admin.py) `learner_sessions` (line 623) | Business boundary interaction; distinct meaning, retained |
| C14 | dbcas → admin | Competency gap analytics | UC11; R7; [`routers/admin.py`](../../backend/app/routers/admin.py) `cohort_overview` (line 600) | Business boundary interaction; distinct meaning, retained |
| C15 | dbcas → admin | AI mapping suggestions | UC06; [`routers/admin.py`](../../backend/app/routers/admin.py) `suggest_clo_concepts` (line 271) | Business boundary interaction; distinct meaning, retained |
| C16 | dbcas → llm | Gap explanation requests | UC17; [`services/competency_service.py`](../../backend/app/services/competency_service.py) `_explain_gap` (line 292) | Business boundary interaction; distinct meaning, retained |
| C17 | dbcas → llm | Essay evaluation requests | UC14-15; [`services/essay_grading.py`](../../backend/app/services/essay_grading.py) `grade_essay` (line 125) | Business boundary interaction; distinct meaning, retained |
| C18 | dbcas → llm | CLO/Concept mapping requests | UC06; [`services/ai_admin_service.py`](../../backend/app/services/ai_admin_service.py) `suggest_clo_concepts` (line 122) | Business boundary interaction; distinct meaning, retained |
| C19 | llm → dbcas | Mapping suggestions | UC06; [`services/ai_admin_service.py`](../../backend/app/services/ai_admin_service.py) `suggest_clo_concepts` (line 122) | Business boundary interaction; distinct meaning, retained |
| C20 | llm → dbcas | Essay evaluation results | UC14-15; [`services/essay_grading.py`](../../backend/app/services/essay_grading.py) `grade_essay` (line 125) | Business boundary interaction; distinct meaning, retained |
| C21 | llm → dbcas | Gap explanations | UC17; [`services/competency_service.py`](../../backend/app/services/competency_service.py) `_explain_gap` (line 292) | Business boundary interaction; distinct meaning, retained |
| C22 | admin → dbcas | Grade verification decisions | UC20; R6; [`services/grading_review.py`](../../backend/app/services/grading_review.py) `approve` (line 109) | Business boundary interaction; distinct meaning, retained |
| C23 | dbcas → admin | Grade review queue and evidence | UC20; R6; [`routers/admin.py`](../../backend/app/routers/admin.py) `grading_review_detail` (line 70) | Business boundary interaction; distinct meaning, retained |
| C24 | admin → dbcas | Role changes (role manager only) | UC04 role capability; [`services/auth_service.py`](../../backend/app/services/auth_service.py) `set_account_role` (line 148) | Business boundary interaction; distinct meaning, retained |
| C25 | dbcas → admin | Role-management capability | UC04 role capability; [`services/auth_service.py`](../../backend/app/services/auth_service.py) `role_management_capability` (line 144) | Business boundary interaction; distinct meaning, retained |
| C26 | admin → dbcas | Question candidate generation requests | UC10; [`routers/admin.py`](../../backend/app/routers/admin.py) `generate_question_candidates` (line 463) | Business boundary interaction; distinct meaning, retained |
| C27 | dbcas → admin | Draft question candidates | UC10; [`routers/admin.py`](../../backend/app/routers/admin.py) `get_question_candidate` (line 482) | Business boundary interaction; distinct meaning, retained |
| C28 | dbcas → llm | Question candidate generation requests | UC10; [`services/ai_admin_service.py`](../../backend/app/services/ai_admin_service.py) `generate_candidates` (line 568) | Business boundary interaction; distinct meaning, retained |
| C29 | llm → dbcas | Unreviewed question candidates | UC10; [`services/ai_admin_service.py`](../../backend/app/services/ai_admin_service.py) `generate_candidates` (line 568) | Business boundary interaction; distinct meaning, retained |
| C30 | dbcas → llm | Question concept tagging requests | UC08; [`services/ai_admin_service.py`](../../backend/app/services/ai_admin_service.py) `suggest_question_tags` (line 217) | Business boundary interaction; distinct meaning, retained |
| C31 | llm → dbcas | Unconfirmed question tags | UC08; [`services/ai_admin_service.py`](../../backend/app/services/ai_admin_service.py) `suggest_question_tags` (line 217) | Business boundary interaction; distinct meaning, retained |
| C32 | dbcas → google | Authorization redirect (via browser) | UC02 optional OAuth; [`routers/oauth.py`](../../backend/app/routers/oauth.py) `start` (line 71) | Detailed OAuth boundary exchange; separate contract, retained |
| C33 | google → dbcas | Authorization code + state (via browser) | UC02 optional OAuth; [`routers/oauth.py`](../../backend/app/routers/oauth.py) `callback` (line 95) | Detailed OAuth boundary exchange; separate contract, retained |
| C34 | dbcas → google | Authorization-code token exchange | UC02 optional OAuth; [`services/oauth.py`](../../backend/app/services/oauth.py) `_exchange_code` (line 289) | Detailed OAuth boundary exchange; separate contract, retained |
| C35 | google → dbcas | Access token / exchange error | UC02 optional OAuth; [`services/oauth.py`](../../backend/app/services/oauth.py) `_exchange_code` (line 289) | Detailed OAuth boundary exchange; separate contract, retained |
| C36 | dbcas → google | Authenticated profile request | UC02 optional OAuth; [`services/oauth.py`](../../backend/app/services/oauth.py) `_google_identity` (line 319) | Detailed OAuth boundary exchange; separate contract, retained |
| C37 | google → dbcas | Profile / verified identity claims | UC02 optional OAuth; [`services/oauth.py`](../../backend/app/services/oauth.py) `_google_identity` (line 319) | Detailed OAuth boundary exchange; separate contract, retained |
| C38 | dbcas → github | Authorization redirect (via browser) | UC02 optional OAuth; [`routers/oauth.py`](../../backend/app/routers/oauth.py) `start` (line 71) | Detailed OAuth boundary exchange; separate contract, retained |
| C39 | github → dbcas | Authorization code + state (via browser) | UC02 optional OAuth; [`routers/oauth.py`](../../backend/app/routers/oauth.py) `callback` (line 95) | Detailed OAuth boundary exchange; separate contract, retained |
| C40 | dbcas → github | Authorization-code token exchange | UC02 optional OAuth; [`services/oauth.py`](../../backend/app/services/oauth.py) `_exchange_code` (line 289) | Detailed OAuth boundary exchange; separate contract, retained |
| C41 | github → dbcas | Access token / exchange error | UC02 optional OAuth; [`services/oauth.py`](../../backend/app/services/oauth.py) `_exchange_code` (line 289) | Detailed OAuth boundary exchange; separate contract, retained |
| C42 | dbcas → github | Authenticated profile request | UC02 optional OAuth; [`services/oauth.py`](../../backend/app/services/oauth.py) `_github_identity` (line 339) | Detailed OAuth boundary exchange; separate contract, retained |
| C43 | github → dbcas | Profile / provider user ID | UC02 optional OAuth; [`services/oauth.py`](../../backend/app/services/oauth.py) `_github_identity` (line 339) | Detailed OAuth boundary exchange; separate contract, retained; label corrected: profile ID is distinct from verified email in C45 |
| C44 | dbcas → github | Verified email list request | UC02 verified-email linking; [`services/oauth.py`](../../backend/app/services/oauth.py) `_github_identity` (line 339) | Detailed OAuth boundary exchange; separate contract, retained |
| C45 | github → dbcas | Email addresses + verification flags | UC02 verified-email linking; [`services/oauth.py`](../../backend/app/services/oauth.py) `_github_identity` (line 339) | Detailed OAuth boundary exchange; separate contract, retained |
| C46 | admin → dbcas | Result publication requests | UC20; R5-R6; [`services/grading_review.py`](../../backend/app/services/grading_review.py) `publish` (line 155) | Business boundary interaction; distinct meaning, retained |
| C47 | dbcas → admin | Publication outcome | UC20; R5-R6; [`services/grading_review.py`](../../backend/app/services/grading_review.py) `publish` (line 155) | Business boundary interaction; distinct meaning, retained |
| C48 | dbcas → admin | Role audit history | UC04 role audit; [`services/auth_service.py`](../../backend/app/services/auth_service.py) `list_role_audit` (line 197) | Business boundary interaction; distinct meaning, retained |
| C49 | admin → dbcas | Question candidate curation decisions | UC10 human curation; [`services/ai_admin_service.py`](../../backend/app/services/ai_admin_service.py) `approve_candidate` (line 703) | Business boundary interaction; distinct meaning, retained |
| C50 | dbcas → admin | Candidate curation outcome | UC10 human curation; [`services/ai_admin_service.py`](../../backend/app/services/ai_admin_service.py) `approve_candidate` (line 703) | Business boundary interaction; distinct meaning, retained |
| C51 | dbcas → admin | Role change outcome | UC04 role audit; [`services/auth_service.py`](../../backend/app/services/auth_service.py) `set_account_role` (line 148) | Business boundary interaction; distinct meaning, retained |

### Acceptance before/after

| Baseline | Nodes | Directed relationships |
|---|---:|---:|
| University original | 4 | 21 |
| Start of acceptance pass | 6 | 51 |
| Final acceptance companion | 6 | 51 |

- Preserved: every relationship C01-C51; all C01-C21 original labels remain verbatim.
- Modified: C43 label “Profile / verified identity claims” → “Profile / provider user ID”. `_github_identity` explicitly distrusts the public profile email and requests C44-C45 separately. Direction and meaning remain the profile response.
- Added or removed in this pass: none. Earlier 30 additions remain individually traceable.
- Source/render parity: the validator now checks exact context labels, direction and IDs; JSON text corruption is rejected.

## All ten figures: semantic and visual verdict

| Figure | Nodes / relationships at start and end | Implementation check | Render inspection / limitation |
|---|---|---|---|
| System Context | 6 / 51 | All 51 contracts above; internal databases correctly excluded | Parallel labeled arrows, clear boundary, no crossings or clipping. Large canvas; inspect at native size. |
| Use Case | 25 / 30 | UC01-UC20; Admin capability qualification; plain actor associations; optional provider actors | No clipped labels or nodes. Shared actor associations cross in the left margin; the 30 paths remain individually inspectable. Zoom rather than shrinking to a page thumbnail. |
| Container | 12 / 13 | React browser vs static host; FastAPI process, migrate job, optional worker, system DB and separate sandbox | Runtime/system grouping clear; curved peripheral edges readable at native size. |
| Component | 33 / 47 | Real router/service/shared repository responsibilities; candidate dispatch, grading lifecycle, personal plan and cumulative branch | Most dense figure. Layer bands and IDs clarify shared responsibilities; 3439×3568 canvas requires zoom. Curves cross between bands; syntax/clipping success alone is not claimed as one-page readability. |
| Module | 24 / 25 | Original chains and actual shared LLM/sandbox/persistence dependencies | Module bands distinguish responsibilities. Some shared dependency curves cross below modules; no node overlap or clipped text. |
| Deployment | 13 / 15 | Release Compose internal networks, loopback Nginx, migrate dependency, opt-in worker; TLS gateway explicitly external/unverified | Dev/release claims remain distinguished. Arrowheads clear; no unsupported built-in HTTPS service. |
| Conceptual ER | 18 / 26 | Original entities/keys; profile optionality; conceptual role M:N via AccountRole; actual candidate Concept FK | Labels and keys readable; arrows describe named conceptual associations. Physical FK/cardinality detail remains linked rather than silently omitted. |
| Physical schema | 32 / 45 | Every table, FK, key and optionality against catalog/DDL; 012 prepared, not applied | 3947×5383 detailed canvas, intentionally zoomable. FK labels and column targets inspected. Not suitable as an unzoomed A4 thumbnail. |
| Logical architecture | 17 / 27 | Stateless JWT plus persisted identity/throttle; application-origin LLM calls; sandbox inside system boundary | Tier boundaries clear; external-call and persistence curves cross. No false microservice/deployment claim. |
| Assessment lifecycle | 17 / 27 | Legacy vs frozen personalized plan; asynchronous grading, failure/retry, authorized human takeover, reviewed then publish | Branches preserved and visually inspected; loop curves cross near grading/evidence. No missing pending/failed/reviewed branch. Fixed corrupted R1-R3 JSON metadata; DOT/SVG wording already correct. |

No DFD or sequence diagram source exists in this ten-figure set. None was fabricated. The existing historical Mermaid excerpt and release workflow remain inventoried; neither is promoted to a complete new architectural model. All nine DOT sources were rendered again, the editable context SVG was browser-rendered again, and the ten images were visually inspected. Browser checks found zero clipped text; they do not automatically prove that crossing arrows are semantically correct. The code/requirement review above and Matrix B provide that separate evidence.

The component and physical figures are detailed engineering companions, not compact overview figures. Retain links to the SVG and ledgers when incorporating them in Word; do not flatten the full models to unreadable page-width screenshots.
