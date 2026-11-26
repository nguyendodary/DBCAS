# Diff — ProposalDocument

Baseline: `C1SE.70_ProposalDocument_DBCAS_ver1.3.docx`
Final: `C1SE.70_ProposalDocument_DBCAS_ver1.3.docx`

## Summary

- Paragraphs: 35 changed, 58 added, 46 deleted
- Tables: 11 changed, 13 added, 11 deleted
- Figures: 4 replaced, 0 added, 0 removed
- Sections/headings changed: see detail below

## Figures

| Action | Baseline caption | Final caption |
|---|---|---|
| replaced | Figure 1: Agile Scrum Sprint Roadmap & Official Faculty Milestones | Figure 1: Agile delivery roadmap and official faculty milestones |
| replaced | Figure 2: DBCAS System Context Diagram | Figure 2: DBCAS System Context Diagram |
| replaced | Figure 3: DBCAS Logical System Architecture Diagram | Figure 3: DBCAS Logical System Architecture Diagram |
| replaced | Figure 4: Evidence-based Competency & Gap Evaluation Pipeline | Figure 4: Evidence-based Competency & Gap Evaluation Pipeline |

## Detail

### Changed paragraph — front matter

**Before:** Version 1.4

**After:** Version 1.3

### Changed paragraph — front matter

**Before:** Date: October 2nd, 2026

**After:** Date: November 26th, 2026

### Changed paragraph — front matter

**Before:** The following signatures are required for approval of this document.

**After:** The following signatures are required for approval of this document. Approval status: [OWNER TO PROVIDE: approval decisions and signature dates]. This document does not assert approval.

### Changed table — front matter

**Before:** TABLE rows=6 cols=4 :: Version | Date | Comments | Author || 1.0 | 05/09/2026 | Init | All members || 1.1 | 10/09/2026 | Update | All members || 1.2 | 19/09/2026 | Update | All members

**After:** TABLE rows=5 cols=4 :: Version | Date | Comments | Author || 1.0 | 05/09/2026 | Init | All members || 1.1 | 10/09/2026 | Update | All members || 1.2 | 19/09/2026 | Update | All members

### Changed paragraph — 3. Supervisor(s)

**Before:** The team is supervised and guided by academic faculty from the Software Engineering Department at the International School, Duy Tan University:

**After:** The team is supervised and guided by academic faculty from the CSE Center at the International School, Duy Tan University:

### Changed paragraph — 4.4. Problem Identification Through Online Research

**Before:** Our team did not conduct direct student interviews or surveys. Instead, we explored the problem by researching developer discussion forums, programming education communities, and technical learning articles online (such as discussions on Stack Overflow, Reddit threads on r/learnprogramming, and computer science teaching blogs). By looking into what learners and educators discuss online, we identified several recurring difficulties that learners experience when learning databases. These common online discussions helped shape our project idea and confirmed the need for DBCAS:

**After:** Our team did not conduct direct student interviews or surveys. Instead, we explored the problem by researching developer discussion forums, programming education communities, and technical learning articles online (such as discussions on Stack Overflow, Reddit threads on r/learnprogramming, and computer science teaching blogs). By looking into what learners and educators discuss online, we identified several recurring difficulties that learners experience when learning databases. These common online discussions helped shape our project idea and confirmed the need for DBCAS: The difficulties recur in the database-education literature and in public practitioner discussions [1], [2], [6], [8].

### Changed paragraph — 5.1. Online Query Practice Sites

**Before:** Websites like LeetCode, HackerRank, SQLZoo, and DataCamp allow learners to write SQL queries and compare their output against expected results. They are great for quick syntax practice. However, their scope is limited: they only check SQL queries, offering no support for Entity-Relationship modeling or database normalization theory. Also, their feedback only says 'Accepted' or 'Wrong Answer' without explaining the reasoning behind an error, and they do not link results to university course goals.

**After:** Websites like LeetCode, HackerRank, SQLZoo, and DataCamp allow learners to write SQL queries and compare their output against expected results. They are great for quick syntax practice. However, their scope is limited: they only check SQL queries, offering no support for Entity-Relationship modeling or database normalization theory. Also, their feedback only says 'Accepted' or 'Wrong Answer' without explaining the reasoning behind an error, and they do not link results to university course goals. The exact-output practice-site model is documented by LeetCode's database problem set [14].

### Changed paragraph — 5.2. Traditional Learning Management Systems (LMS)

**Before:** Systems like Moodle, Canvas, and Blackboard organize course materials and gradebooks well. However, their test tools usually return just one total score. They cannot run and test learner SQL code safely, and instructors must grade written answers by hand. They also do not point out specific competency gaps or tell learners what to review next.

**After:** Systems like Moodle, Canvas, and Blackboard organize course materials and gradebooks well. However, their test tools usually return just one total score. They cannot run and test learner SQL code safely, and instructors must grade written answers by hand. They also do not point out specific competency gaps or tell learners what to review next. Outcome-based course design is required by the ACM/IEEE curriculum guidance [3].

### Changed paragraph — 5.3. Conversational AI Chatbots

**Before:** General-purpose AI chatbots are useful for asking questions during study sessions. However, they are not designed for formal school exams. They do not have structured test workflows, can give different scores for similar answers, and cannot track learner skill progress over an entire semester.

**After:** General-purpose AI chatbots are useful for asking questions during study sessions. However, they are not designed for formal school exams. They do not have structured test workflows, can give different scores for similar answers, and cannot track learner skill progress over an entire semester. The opportunities and risks of generative AI in computing education are documented in [6] and [7].

### Changed table — 6.1. SMART Objectives

**Before:** TABLE rows=6 cols=2 :: SMART Dimension | Project Goal & Verification Method || S – Specific | Design, build, and deploy the DBCAS web platform to evaluate learner competency  || M – Measurable | • Verify that adaptive selection follows configured difficulty rules and that AI || A – Achievable | Build the system using well-known, reliable open-source tools (React, FastAPI, P

**After:** TABLE rows=6 cols=2 :: SMART Dimension | Project Goal & Verification Method || S – Specific | Design, build, and deploy the DBCAS web platform to evaluate learner competency  || M – Measurable | • Verify that every practice session spreads the plan across the selected concep || A – Achievable | Build the system using well-known, reliable open-source tools (React, FastAPI, P

### Changed table — 6.2. Project Scope

**Before:** TABLE rows=5 cols=4 :: Core Subject Area | Component Skills | Question Formats | Adaptive Session Coverage || 1. SQL Querying | • Core retrieval: SELECT, WHERE, ORDER BY, DISTINCT / • Joins & aggregation: JOI | • Multiple-choice questions / • Practical SQL sandbox tasks | MCQ + live SQL tasks / (adaptive mix by concept evidence) || 2. Data Manipulation & Definition | • DML statements: INSERT / UPDATE / DELETE / • DDL statements: CREATE / ALTER /  | • Multiple-choice questions / • Practical SQL s

**After:** TABLE rows=5 cols=4 :: Core Subject Area | Component Skills | Question Formats | Session Coverage || 1. SQL Querying | • Core retrieval: SELECT, WHERE, ORDER BY, DISTINCT / • Joins & aggregation: JOI | • Multiple-choice questions / • Read-only practical SQL tasks | MCQ + read-only SQL tasks / (bank or AI-selected items by concept) || 2. Data Manipulation & Definition | • DML statements: INSERT / UPDATE / DELETE / • DDL statements: CREATE / ALTER /  | • Multiple-choice questions / • Conceptual es

### Changed paragraph — 6.2. Project Scope

**Before:** Out-of-Scope Items: To maintain high engineering quality within the 15-week timeline, the following topics are outside the project scope:

**After:** Learner SQL is read-only by default: the sandbox accepts SELECT statements and rolls back every query. An opt-in demo profile (DBCAS_DEMO_PROFILE=writable) allows DDL/DML in a disposable ephemeral container that is always rolled back; grading remains read-only. DML and DDL knowledge is also assessed through multiple-choice and essay items. A demo-only Free/Pro plan badge is a UI simulation with no payment or backend charge.

### Changed paragraph — 6.2. Project Scope

**Before:** •  Personalized Learning Paths and RAG-Based Study Resources: Long-term adaptive study roadmaps, learning tracking, and course-document ingestion or retrieval are outside scope. “What to study next” is limited to ranked below-benchmark concepts and their descriptions when available.

**After:** •  Long-Term Learning Paths: Long-term adaptive study roadmaps and cross-course tracking are outside scope. Administrator course-document ingestion and grounded question generation are implemented. “What to study next” is limited to ranked below-benchmark concepts and their descriptions when available.

### Changed table — 7.1. Seven Key System Features

**Before:** TABLE rows=8 cols=4 :: No. | System Feature / Module | Functional Scope & Capabilities | Target Users & Educational Value || 1 | Course Outcomes & Concept Management | Enables administrators to define course learning goals, organize them into the C | Administrator: Ensures tight alignment between assessments and university curric || 2 | Question Bank & Concept Tagging | Maintains an Administrator-approved, validated library of multiple-choice questi | Administrator: Saves time when curating the 

**After:** TABLE rows=8 cols=4 :: No. | System Feature / Module | Functional Scope & Capabilities | Target Users & Educational Value || 1 | Course Outcomes & Concept Management | Enables administrators to define course learning goals, organize them into the C | Administrator: Ensures tight alignment between assessments and university curric || 2 | Question Bank & Concept Tagging | Maintains an Administrator-approved, validated library of multiple-choice questi | Administrator: Saves time when curating the 

### Changed paragraph — 7.2. Functional Requirements

**Before:** Table 8 outlines the functional requirements across primary human actors (Learner, Administrator), the core system (DBCAS), and the external AI service (LLM Provider):

**After:** Table 8 outlines the functional requirements across primary human actors (Learner, Administrator), the core system (DBCAS), the external AI service (LLM Provider), and the OAuth Identity Provider used for sign-in:

### Changed table — 7.2. Functional Requirements

**Before:** TABLE rows=17 cols=4 :: FR ID | Requirement Name | Functional Description | Primary Actor / Component || FR-01 | User Authentication | System authenticates users using secure tokens and distinguishes roles between L | Learner, Administrator || FR-02 | Outcome & Concept Setup | System allows administrators to define course learning outcomes (CLOs), the Core | Administrator || FR-03 | Outcome Mapping Assistance | System suggests connections between course outcomes and PostgreSQL concepts usin | Ad

**After:** TABLE rows=17 cols=4 :: FR ID | Requirement Name | Functional Description | Primary Actor / Component || FR-01 | User Authentication | System authenticates users with JWT-based sessions and implements exactly two ap | Learner, Administrator || FR-02 | Outcome & Concept Setup | System allows administrators to define course learning outcomes (CLOs), the Core | Administrator || FR-03 | Outcome Mapping Assistance | System suggests connections between course outcomes and PostgreSQL concepts usin | Ad

### Changed table — 7.3. Non-Functional Requirements

**Before:** TABLE rows=10 cols=4 :: NFR ID | Quality Area | Target Requirement & Acceptance Standard | Technical Approach || NFR-01 | Response Time | Web pages load within 1.5 seconds; API endpoints respond within 500 milliseconds | FastAPI asynchronous routes and optimized frontend bundles. || NFR-02 | Sandbox Security | Learner SQL queries run inside a dedicated isolated container with a 3-second st | A dedicated Docker container running PostgreSQL with a read-only learner role, e || NFR-03 | Service Reli

**After:** TABLE rows=10 cols=4 :: NFR ID | Quality Area | Target Requirement & Acceptance Standard | Technical Approach || NFR-01 | Response Time | Web pages load within 1.5 seconds; API endpoints respond within 500 milliseconds | FastAPI asynchronous routes and optimized frontend bundles. || NFR-02 | Sandbox Security | Learner SQL queries run inside a dedicated isolated container with a 3-second st | A dedicated Docker container running PostgreSQL with a read-only learner role th || NFR-03 | Service Reli

### Changed table — 8. Constraints and Assumptions

**Before:** TABLE rows=9 cols=3 :: Category | Constraint / Assumption Item | Detailed Technical Scope & Rationale || Technical Constraints | SQL Sandbox Resource Limits | Learner SQL queries run inside a dedicated Docker sandbox container with memory  || Technical Constraints | External LLM Provider Limits & Latency | External language model API calls are managed using PostgreSQL-backed response c || Technical Constraints | Modern Web Browser Compatibility | The web interface runs smoothly on standard moder

**After:** TABLE rows=10 cols=3 :: Category | Constraint / Assumption Item | Detailed Technical Scope & Rationale || Technical Constraints | SQL Sandbox Resource Limits | Learner SQL queries run inside a dedicated Docker sandbox container with memory  || Technical Constraints | External LLM Provider Limits & Latency | External language model API calls are managed using PostgreSQL-backed response c || Technical Constraints | Modern Web Browser Compatibility | The web interface runs smoothly on standard mode

### Changed table — 9. Target Users / Stakeholders

**Before:** TABLE rows=5 cols=4 :: Stakeholder / Role | Background & Context | Current Needs & Frustrations | Value Provided by DBCAS || Learner / (Primary Human Actor) | Undergraduate Computer Science and Software Engineering students taking Database | • Frustrated by single exam grades that do not explain mistakes. / • Want fast f | • Visual competency profiles showing exact strengths and weaknesses. / • Clear e || Administrator / (System Content Manager) | An authorized DBCAS Administrator responsible fo

**After:** TABLE rows=5 cols=4 :: Stakeholder / Role | Background & Context | Current Needs & Frustrations | Value Provided by DBCAS || Learner / (Primary Human Actor) | Undergraduate Computer Science and Software Engineering students taking Database | • Frustrated by single exam grades that do not explain mistakes. / • Want fast f | • Visual competency profiles showing exact strengths and weaknesses. / • Clear e || Administrator / (System Content Manager) | An authorized DBCAS Administrator responsible fo

### Changed paragraph — 10. Technology Stack

**Before:** The technology stack is organized across seven core system layers, selecting mature, widely adopted, and stable open-source technologies to guarantee platform reliability, security, and maintainability:

**After:** The technology stack is organized across nine core system layers, selecting mature, widely adopted, and stable open-source technologies to guarantee platform reliability, security, and maintainability:

### Changed table — 10. Technology Stack

**Before:** TABLE rows=8 cols=4 :: System Layer | Technology / Framework | Stable Version | Role in DBCAS & Technical Justification || Presentation Layer (Frontend) | React.js + Vite (JavaScript / JSX) | React 19.3 / Vite 8 (LTS) | Industry-standard component library using JavaScript (ES6+ / JSX) paired with Vi || UI Styling & Visualization | Tailwind CSS & Chart.js | Tailwind 4 / Chart.js 4.5 | Widely adopted utility CSS framework for clean layouts paired with a reliable ch || Backend API & Logic | FastAPI

**After:** TABLE rows=10 cols=4 :: System Layer | Technology / Framework | Stable Version | Role in DBCAS & Technical Justification || Presentation Layer (Frontend) | React.js + Vite (JavaScript / JSX) + i18next | React 19.3 / Vite 8.3.5 / i18next 26.4.3 | Industry-standard component library using JavaScript (ES6+ / JSX) paired with Vi || UI Styling & Visualization | Tailwind CSS & Chart.js | Tailwind 4.3 / Chart.js 4.5.1 | Widely adopted utility CSS framework for clean layouts paired with a reliable ch ||

### Changed paragraph — 11.2. Official Capstone Timeline & Sprint Roadmap

**Before:** The project development plan is structured around the official 15-week Capstone 1 schedule (September 14, 2026 – December 26, 2026), preceded by a preparatory phase beginning July 28, 2026, detailed in Table 13 and shown in Figure 1: In Figure 1, “Personalized Study Guidance” means a ranked list of below-benchmark concepts, with concept descriptions when available and evidence-linked gap explanations. Long-term learning paths and RAG-based course-document retrieval are outside scope. Table 13 specifies the current deliverables.

**After:** The project development plan is structured around the official 15-week Capstone 1 schedule (September 14, 2026 – December 26, 2026), preceded by a preparatory phase beginning July 28, 2026, detailed in Table 13 and shown in Figure 1: In Figure 1, “Personalized Study Guidance” means a ranked list of below-benchmark concepts, with concept descriptions when available and evidence-linked gap explanations. Long-term learning-path automation remains outside scope; administrator course-document grounding and grounded candidate generation are implemented. Table 13 specifies the current deliverables.

### Changed paragraph — 11.2. Official Capstone Timeline & Sprint Roadmap

**Before:** Figure 1: Agile Scrum Sprint Roadmap & Official Faculty Milestones

**After:** Figure 1: Agile delivery roadmap and official faculty milestones

### Changed paragraph — 12.1. System Context Diagram

**Before:** Figure 2 shows DBCAS, its two human actors, and the external LLM Provider. Directed flows cover registration, assessment responses, curriculum management, analytics, and assistive AI requests and results:

**After:** Figure 2 shows DBCAS, its two human actors, and the external systems it depends on: the LLM Provider, the OAuth Identity Provider and email delivery. Directed flows cover registration and sign-in, practice setup and responses, curriculum management, analytics, password-reset mail, and assistive AI requests and results:

### Changed paragraph — 12.1. System Context Diagram

**Before:** The System Context Diagram defines the high-level operational boundary of DBCAS and captures its interactions with exactly two human actors and one external software system:

**After:** The System Context Diagram defines the high-level operational boundary of DBCAS and captures its interactions with exactly two human actors and three external software systems: the LLM Provider, the OAuth Identity Provider and the email delivery service.

### Changed paragraph — 12.1. System Context Diagram

**Before:** •  Learner (Primary Human Actor): An undergraduate student taking database assessments. Learners submit registration and authentication requests, multiple-choice responses, live SQL queries, and written conceptual answers to DBCAS. In return, they receive visual competency profiles across core PostgreSQL concepts, evidence-linked competency-gap explanations, and a prioritized list of topics to study based on below-benchmark results.

**After:** •  Learner (Primary Human Actor): An undergraduate student taking database assessments. Learners sign in with email/password or Google/GitHub OAuth, recover a forgotten password through a single-use emailed link when mail delivery is configured, choose their concepts, difficulty bands, question count and source for practice sessions, and submit multiple-choice responses, SQL queries (read-only by default), and written conceptual answers to DBCAS. In return, they receive visual competency profiles across core PostgreSQL concepts (including cumulative published results), evidence-linked competency-gap explanations, a prioritized list of topics to study, and results released according to policy

### Changed paragraph — 12.1. System Context Diagram

**Before:** •  Administrator (System Content Manager): An authorized DBCAS Administrator responsible for academic content and system configuration. Administrators define Course Learning Outcomes (CLOs), configure the PostgreSQL concept model, set difficulty levels, approve AI-generated questions after automated checks, and curate the validated question bank and scoring rubrics, and configure adaptive assessment rules. In return, they receive cohort-wide competency gap analytics, individual learner performance records, and system-proposed CLO-to-concept mappings for review.

**After:** •  Administrator (System Content Manager): An authorized DBCAS Administrator responsible for academic content and system configuration. Administrators define Course Learning Outcomes (CLOs), configure the PostgreSQL concept model and prerequisites, set difficulty levels, approve AI-generated questions after automated checks, curate the validated question bank and scoring rubrics, configure system settings, manage roles (Administrator-only accounts cannot take practice sessions), and review SQL and essay grades for legacy/practice submissions before publication; FIXED Test results are AI-official V1; an Administrator can never review or publish a result for a session they own. In return, they

### Changed paragraph — 12.1. System Context Diagram

**Before:** •  DBCAS (System Under Study): The central educational software platform that coordinates assessment sessions, adaptively selects each next question from the approved bank, executes SQL queries in a sandboxed environment, stores standardized evaluation evidence, computes competency scores deterministically, and visualizes competency profiles.

**After:** Role mapping and separation: DBCAS defines exactly two application roles. The User role is implemented as Learner, and the Admin role is implemented as Administrator. There is no third role. Self-registration and OAuth create Learner accounts only; Administrator accounts are provisioned by an existing role manager and start disabled. Administrator accounts cannot start, serve or submit a practice session, and an Administrator cannot review or publish a result for a session they own. A Learner may request promotion to Administrator through the course team; an existing Administrator with role-management capability reviews the request and grants or denies it through the audited role-management 

### Changed paragraph — 12.1. System Context Diagram

**Before:** Architectural Boundary & Technology Encapsulation: In strict alignment with system context modeling standards, Figure 2 maintains a high-level view and does not include internal software modules, database engines, application frameworks, or development toolchains as external actors. Implementation technologies (such as React, Vite, Tailwind CSS, Chart.js, FastAPI, PostgreSQL, Docker, and Git) and internal processing modules (Internal Assessment Engine, Scoring Engine, Evidence Store, Competency Engine, Competency Gap Analyzer, and Adaptive Selection Engine) operate wholly within the logical architecture of DBCAS and are detailed in Section 12.2.

**After:** •  OAuth Identity Provider (External Software System): Google and GitHub OAuth 2.0 authorization servers used for sign-in and learner sign-up. DBCAS validates a signed state value, applies PKCE for Google, exchanges the authorization code server-side, requires a verified email, and never stores provider access tokens. New OAuth identities become Learners and never receive an Administrator role automatically.

### Changed paragraph — 12.1. System Context Diagram

**Before:** AI Ethics & Administrator-Configured Evaluation Principle: In strict compliance with academic ethics, fairness, and transparency, the external LLM Provider functions solely as an assistive component and never autonomously determines a learner's final competency. Administrators configure essay rubrics and competency benchmarks. LLM-assisted essay scores are recorded as answer evidence, and DBCAS applies predefined rules to aggregate that evidence into final concept competency scores and rank below-benchmark concepts by shortfall. LLM-generated gap explanations link to answer evidence and do not change scores or recommendation order.

**After:** •  Email Delivery Service (External Software System): SMTP delivery used only for single-use password-reset links; when SMTP is not configured the reset endpoints report that mail is unavailable.

### Added paragraph — 12.2. Multi-Tier Logical System Architecture

Note: Figure 3 shows the baseline four-tier layout. OAuth sign-in, personalized plan assembly, durable asynchronous grading, and the administrator review/publish workflow operate within the Application & Services and Data & Storage tiers.

### Changed paragraph — 12.2. Multi-Tier Logical System Architecture

**Before:** •  Presentation Tier (Web Frontend): A single-page web app built with React.js and Vite using JavaScript (ES6+ / JSX), styled with Tailwind CSS, and using Chart.js for data visualization. Includes learner portals for taking assessments and viewing radar charts, administrator portals for managing CLOs, questions, and rubrics, and the code editor for writing SQL queries.

**After:** •  Presentation Tier (Web Frontend): A single-page web app built with React.js and Vite using JavaScript (ES6+ / JSX), styled with Tailwind CSS, and using Chart.js for data visualization. Includes learner portals for practice sessions, results, and radar charts; administrator portals for managing CLOs, questions, rubrics, and result review and approval; the code editor for SQL queries; and English/Vietnamese and theme preferences.

### Changed paragraph — 12.2. Multi-Tier Logical System Architecture

**Before:** •  Application & Services Tier (FastAPI): A Python backend handling application logic through dedicated services: user authentication and role management, assessment session coordination, validated question bank management, grading engines, adaptive question selection and staged AI-question validation with Administrator approval, competency scoring, gap detection, and study-topic ranking.

**After:** •  Application & Services Tier (FastAPI): A Python backend handling application logic through dedicated services: JWT authentication, OAuth sign-in and role management with immutable audit, personalized plan assembly, session coordination with autosaved drafts, validated question bank management, grading engines with durable retry jobs, AI-official FIXED publication and human-verified LEGACY review, competency scoring and cumulative aggregation, gap detection, and study-topic ranking.

### Changed paragraph — 12.2. Multi-Tier Logical System Architecture

**Before:** •  Data & Storage Tier: A PostgreSQL database storing users, course outcomes, questions, test attempts, evaluation records, and cached LLM responses. Stateless JWT authentication removes the need for a separate session store.

**After:** •  Data & Storage Tier: A PostgreSQL 17 database (67 tables, 561 columns, 122 foreign keys, 159 indexes, 28 migrations) storing users and roles, course outcomes, questions and translations, test attempts, immutable evidence, review and release audit records, competency results, and cached LLM responses. Short-lived JWT access tokens and a PostgreSQL refresh-session table provide rotation and revocation without a separate session service.

### Changed paragraph — 12.2. Multi-Tier Logical System Architecture

**Before:** •  External AI & Execution Sandbox: A dedicated Docker container hosting an isolated PostgreSQL instance for learner SQL queries, with strict memory and runtime limits; every query executes inside a read-only transaction that is rolled back after evaluation. External language model APIs (provider-agnostic) that evaluate written conceptual answers using structured administrator rubrics.

**After:** •  External AI & Execution Sandbox: A dedicated Docker container hosting an isolated PostgreSQL instance for learner SQL, with strict memory and runtime limits. The default path is read-only and every query is rolled back; an opt-in demo profile allows DDL/DML in the disposable container. Grading remains read-only. External language model APIs (provider-agnostic) evaluate written conceptual answers using structured administrator rubrics, and OAuth 2.0 authorization servers support sign-in and learner sign-up without storing provider tokens or exposing them to the browser.

### Changed paragraph — 12.3. Evidence-Based Competency & Gap Evaluation Pipeline

**Before:** The central data flow in DBCAS processes learner answers through a live adaptive loop of scoring and question selection, as shown in Figure 4:

**After:** The central data flow in DBCAS turns learner answers into deterministic competency evidence through a personalized assessment pipeline, as shown in Figure 4:

### Changed paragraph — 12.3. Evidence-Based Competency & Gap Evaluation Pipeline

**Before:** How the Evaluation Pipeline Operates: Each answer is scored on submission by format. MCQs use verified keys; SQL runs in the Docker sandbox against expected rows and columns; essays use LLM assistance and the four-level administrator rubric. Scores become concept-linked evidence. The session starts with three validated MCQs at difficulty levels 1–2. Three correct answers raise difficulty, two keep a medium level, and zero or one trigger more basic items in weak concepts. After every answer, concept estimates are updated; from question four onward, the Adaptive Selection Engine chooses the next validated item. The session ends at the configured cap (at most 13 questions) or when the 60-minute

**After:** Note: Figure 4 shows the baseline evaluation pipeline. In the implemented system the complete practice plan is assembled and frozen before the first question is served, learner SQL is read-only by default (the opt-in writable demo is ephemeral and rolled back) and always drawn from the validated bank, and FIXED Test results publish AI-official V1; legacy/practice results publish after administrator review and approval. AI-official V1 has no per-question administrator comments; a separate seven-day review case may lead to V2 after reanalysis.

### Changed paragraph — 12.3. Evidence-Based Competency & Gap Evaluation Pipeline

**Before:** 12.4. Multi-Format Assessment & How Scores Are Calculated

**After:** How the Evaluation Pipeline Operates: Before a session, the learner selects the skills to be assessed and one or more difficulty bands. The system fixes the skills, bands, question source and length before question one and draws only content-validated items (approved bank or auto-validated AI-source items) with confirmed concept tags, spreading the plan across the selected skills as far as the count allows and never repeating a version family. A practice session freezes its complete plan at that point, meeting the exact length with the formats the bank allows. The complete plan is assembled from the validated bank (and, in AI mode, from generated MCQ and essay items) and frozen before questi

### Changed paragraph — 12.3. Evidence-Based Competency & Gap Evaluation Pipeline

**Before:** To ensure fair, understandable grading, DBCAS avoids mysterious black-box calculations. Instead, each question has an assigned point value and is linked to the specific PostgreSQL concepts it tests. When an assessment is submitted:

**After:** 12.4. Multi-Format Practice & How Scores Are Calculated

### Changed paragraph — 12.3. Evidence-Based Competency & Gap Evaluation Pipeline

**Before:** •  Practical SQL Queries: Executed inside the isolated PostgreSQL 17 Docker sandbox and graded semantically, never by exact string matching. Points are awarded deterministically for syntax validity, correct results across multiple test datasets including edge cases, and required-concept compliance when the question mandates a technique — equivalent SQL formulations receive full credit.

**After:** •  Practical SQL Queries: Read-only SELECT statements are executed inside the isolated PostgreSQL 17 Docker sandbox and graded semantically, never by exact string matching. Points are awarded deterministically for syntax validity, correct results across multiple test datasets including edge cases, and required-concept compliance when the question mandates a technique — equivalent SQL formulations receive full credit. DML/DDL execute only in the opt-in writable demo inside the disposable container and are always rolled back; grading remains read-only.

### Changed paragraph — 12.3. Evidence-Based Competency & Gap Evaluation Pipeline

**Before:** Deterministic Scoring & Human-Governed Competency: To calculate a learner's standing on any given PostgreSQL concept (such as JOINs or Window Functions), the system computes scores deterministically by comparing points earned on items testing that concept against total possible points available for it. If a learner's competency on a concept is lower than the administrator-set passing expectation, the system flags it as a competency gap. After showing the profile, DBCAS ranks those concepts by their shortfall from the target and presents them as study topics, using the concept name and its description when available to clarify what to review. The LLM Provider only generates evidence-linked, p

**After:** Deterministic Scoring & Human-Governed Competency: To calculate a learner's standing on any given PostgreSQL concept (such as JOINs or Window Functions), the system computes scores deterministically by comparing points earned on items testing that concept against total possible points available for it. The cumulative profile pools point totals across every published session instead of averaging session percentages. If a learner's competency on a concept is lower than the platform's 70% passing target, the system flags it as a competency gap. After showing the profile, DBCAS ranks those concepts by their shortfall from the target and presents them as study topics, using the concept name and i

### Changed table — 13. Potential Risks and Mitigation Strategies

**Before:** TABLE rows=7 cols=4 :: Risk ID & Category | Specific Risk Description | Likelihood & Impact | Mitigation Strategy || RSK-01 / Technical / Security | Learners writing harmful SQL queries or infinite loops that could overload the s | Likelihood: Low / Impact: High | • Enforce a strict 3-second statement timeout and a 256 MB memory limit on the s || RSK-02 / AI Consistency | Language model giving slightly different scores or inaccurate feedback on writte | Likelihood: Medium / Impact: Medium | • Us

**After:** TABLE rows=7 cols=4 :: Risk ID & Category | Specific Risk Description | Likelihood & Impact | Mitigation Strategy || RSK-01 / Technical / Security | Learners writing harmful SQL queries or infinite loops that could overload the s | Likelihood: Low / Impact: High | • Enforce a strict 3-second statement timeout and a 256 MB memory limit on the s || RSK-02 / AI Consistency | Language model giving slightly different scores or inaccurate feedback on writte | Likelihood: Medium / Impact: Medium | • Us

### Changed table — 14. Expected Outcomes / Deliverables

**Before:** TABLE rows=7 cols=4 :: No. | Deliverable Item | Detailed Description of Artifact | Delivery Format || 1 | Working DBCAS Web Application | A deployed web platform featuring learner portals for assessments, radar compete | Deployed online application with live demonstration URL and setup guide. || 2 | Complete Source Code Repository | Clean, modular source code for the React frontend (JavaScript / JSX), FastAPI ba | GitHub repository containing documentation, Docker Compose setup, and build scri |

**After:** TABLE rows=7 cols=4 :: No. | Deliverable Item | Detailed Description of Artifact | Delivery Format || 1 | Working DBCAS Web Application | A runnable local Docker Compose demo featuring OAuth and email/password sign-in, | Local demo and setup guide. Public deployment URL: [OWNER TO PROVIDE: confirmed  || 2 | Complete Source Code Repository | Clean, modular source code for the React frontend (JavaScript / JSX), FastAPI ba | GitHub repository containing documentation, Docker Compose setup, and buil

### Changed paragraph — 15. References

**Before:** Academic literature, curriculum guidelines, software tools, and online references with accurate source details and direct web addresses:

**After:** Appendix A. Open owner decisions

### Changed paragraph — 15. References

**Before:** [1]  A. Silberschatz, H. F. Korth, and S. Sudarshan, Database System Concepts, 7th ed. New York, NY, USA: McGraw-Hill Education, 2019. Official Companion Website: https://www.db-book.com/

**After:** The following values are not derivable from the repository. They stay owner-owned and are not asserted anywhere in this document.

### Changed paragraph — 15. References

**Before:** [3]  ACM and IEEE Computer Society, "Computer Science Curricula 2013: Curriculum Guidelines for Undergraduate Degree Programs in Computer Science," ACM/IEEE Joint Task Force on Computing Curricula, Tech. Rep., 2013. Available: https://www.acm.org/education/curricula-recommendations

**After:** Appendix B. Figure sources

### Changed paragraph — 15. References

**Before:** [4]  W. Spady, Outcome-Based Education: Critical Issues and Answers. Arlington, VA, USA: American Association of School Administrators, 1994. ERIC Document Reproduction Service No. ED380910: https://files.eric.ed.gov/fulltext/ED380910.pdf

**After:** Every shipped figure is traceable to a repository source. The figure number is the number used in the body and in the List of Figures.
