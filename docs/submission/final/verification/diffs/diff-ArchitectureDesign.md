# Diff — ArchitectureDesign

Baseline: `C1SE.70_ArchitectureDesign_DBCAS_ver1.3.docx`
Final: `C1SE.70_ArchitectureDesign_DBCAS_ver1.3.docx`

## Summary

- Paragraphs: 74 changed, 85 added, 74 deleted
- Tables: 5 changed, 7 added, 5 deleted
- Figures: 8 replaced, 7 added, 0 removed
- Sections/headings changed: see detail below

## Figures

| Action | Baseline caption | Final caption |
|---|---|---|
| replaced | (uncaptioned baseline image) | Figure 2. System Context Diagram |
| replaced | (uncaptioned baseline image) | Figure 3. Container Diagram |
| replaced | (uncaptioned baseline image) | Figure 7. Entity relationship overview (1/2) |
| replaced | (uncaptioned baseline image) | Figure 7. Entity relationship index (2/2) |
| replaced | (uncaptioned baseline image) | Figure 8. Entity relationship diagram — Identity and access (1/11) |
| replaced | (uncaptioned baseline image) | Figure 8. Entity relationship diagram — Curriculum and concepts (2/11) |
| replaced | (uncaptioned baseline image) | Figure 8. Entity relationship diagram — Question bank and generation (3/11) |
| replaced | (uncaptioned baseline image) | Figure 8. Entity relationship diagram — Assessment and attempts (4/11) |
| added |  | Figure 8. Entity relationship diagram — Grading, results and competency (5/11) |
| added |  | Figure 8. Entity relationship diagram — Review workflow (6/11) |
| added |  | Figure 8. Entity relationship diagram — AI audit and retention (7/11) |
| added |  | Figure 8. Foreign-key ledger — rows 1–31 of 122 (8/11) |
| added |  | Figure 8. Foreign-key ledger — rows 32–62 of 122 (9/11) |
| added |  | Figure 8. Foreign-key ledger — rows 63–92 of 122 (10/11) |
| added |  | Figure 8. Foreign-key ledger — rows 93–122 of 122 (11/11) |

## Detail

### Changed paragraph — front matter

**Before:** Version 1.2

**After:** Version 1.3

### Changed paragraph — front matter

**Before:** Date: November 8th, 2026

**After:** Date: November 26th, 2026

### Changed paragraph — front matter

**Before:** The following signatures are required for approval of this document.

**After:** The following signatures are required for approval of this document. Approval status: [OWNER TO PROVIDE: approval decisions and signature dates]. This document does not assert approval.

### Changed table — front matter

**Before:** TABLE rows=4 cols=4 :: Version | Date | Comments | Author || 1.0 | 18/09/2026 | Initial release | C1SE.70 Team || 1.1 | 30/10/2026 | Update | C1SE.70 Team || 1.2 | 08/11/2026 | Correct project facts and diagrams | C1SE.70 Team

**After:** TABLE rows=5 cols=4 :: Version | Date | Comments | Author || 1.0 | 18/09/2026 | Initial release | C1SE.70 Team || 1.1 | 30/10/2026 | Update | C1SE.70 Team || 1.2 | 08/11/2026 | Correct project facts and diagrams | C1SE.70 Team

### Changed paragraph — 1.1. Actors

**Before:** Table . Actors of the DBCAS system

**After:** Table 1. Actors of the DBCAS system

### Changed paragraph — 1.2. Use Cases

**Before:** Table . Use cases of Learner before sign-in

**After:** Table 2. Use cases of Learner before sign-in

### Changed paragraph — 1.2. Use Cases

**Before:** Table . Use cases of Administrator

**After:** Table 3. Use cases of Administrator

### Changed paragraph — 1.2. Use Cases

**Before:** Table . Use cases of Learner

**After:** Table 4. Use cases of Learner

### Changed table — 1.2. Use Cases

**Before:** TABLE rows=10 cols=3 :: No. | Use case | Description || 1 | Login / Logout | Authenticate to access the assessment platform; log out to securely end the sess || 2 | Take a Personalized Practice Session | Complete a learner-defined practice session after choosing concepts, difficulty  || 3 | Write and Run SQL in the Embedded Editor | Solve SQL tasks in an editor with syntax highlighting and a schema viewer; queri

**After:** TABLE rows=10 cols=3 :: No. | Use case | Description || 1 | Login / Logout | Authenticate to access the assessment platform; log out to securely end the sess || 2 | Take a Personalized Practice Session / Two source modes: Mode 1 uses the reviewe | Complete a learner-defined practice session after choosing concepts, difficulty  || 3 | Write and Run SQL in the Embedded Editor | Solve SQL tasks in an editor with syntax highlighting and a schema viewer; queri

### Changed paragraph — 1.3. Use Case Diagram

**Before:** Figure . Use Case Diagram

**After:** Figure 1. Use Case Diagram

### Changed paragraph — 2. System Context Diagram

**Before:** Figure . System Context Diagram

**After:** Figure 2. System Context Diagram

### Changed paragraph — 2. System Context Diagram

**Before:** Table . Elements of the System Context Diagram

**After:** Table 5. Elements of the System Context Diagram

### Changed paragraph — 3.1. Use Case Entities

**Before:** Table . Use Case Entities: Administrator

**After:** Table 6. Use Case Entities: Administrator

### Changed paragraph — 3.1. Use Case Entities

**Before:** Table . Use Case Entities: Learner

**After:** Table 7. Use Case Entities: Learner

### Changed paragraph — 3.1. Use Case Entities

**Before:** Table . Use Case Entities: Learner before sign-in

**After:** Table 8. Use Case Entities: Learner before sign-in

### Changed paragraph — 3.1. Use Case Entities

**Before:** Table . Use Case Entities: LLM Provider (external system)

**After:** Table 9. Use Case Entities: LLM Provider (external system)

### Changed paragraph — 3.1. Use Case Entities

**Before:** Table . Use Case Entities: OAuth Identity Provider (external system)

**After:** Table 10. Use Case Entities: OAuth Identity Provider (external system)

### Changed paragraph — 3.2. Operational Use Cases

**Before:** Table . Operational Use Cases: Register Learner Account

**After:** Table 11. Operational Use Cases: Register Learner Account

### Changed paragraph — 3.2. Operational Use Cases

**Before:** Table . Operational Use Cases: Login

**After:** Table 12. Operational Use Cases: Login

### Changed paragraph — 3.2. Operational Use Cases

**Before:** Table . Operational Use Cases: Logout

**After:** Table 13. Operational Use Cases: Logout

### Changed paragraph — 3.2. Operational Use Cases

**Before:** Table . Operational Use Cases: Provision Administrator Accounts and Manage Roles

**After:** Table 14. Operational Use Cases: Provision Administrator Accounts and Manage Roles

### Changed paragraph — 3.2. Operational Use Cases

**Before:** Table . Operational Use Cases: Define CLOs and Concept Model

**After:** Table 15. Operational Use Cases: Define CLOs and Concept Model

### Changed paragraph — 3.2. Operational Use Cases

**Before:** Table . Operational Use Cases: Review AI-Suggested CLO-to-Concept Mappings

**After:** Table 16. Operational Use Cases: Review AI-Suggested CLO-to-Concept Mappings

### Changed paragraph — 3.2. Operational Use Cases

**Before:** Table . Operational Use Cases: Curate Validated Question Bank

**After:** Table 17. Operational Use Cases: Curate Validated Question Bank

### Changed paragraph — 3.2. Operational Use Cases

**Before:** Table . Operational Use Cases: Review AI-Recommended Question Tags

**After:** Table 18. Operational Use Cases: Review AI-Recommended Question Tags

### Changed paragraph — 3.2. Operational Use Cases

**Before:** Table . Operational Use Cases: Oversee AI-Generated Question Candidates

**After:** Table 20. Operational Use Cases: Oversee AI-Generated Question Candidates

### Changed paragraph — 3.2. Operational Use Cases

**Before:** Table . Operational Use Cases: View Learner Competency Profiles and Cohort Analytics

**After:** Table 21. Operational Use Cases: View Learner Competency Profiles and Cohort Analytics

### Changed paragraph — 3.2. Operational Use Cases

**Before:** Table . Operational Use Cases: Take a Personalized Practice Session

**After:** Table 22. Operational Use Cases: Take a Personalized Practice Session

### Changed paragraph — 3.2. Operational Use Cases

**Before:** Table . Operational Use Cases: Write and Run SQL in the Embedded Editor

**After:** Table 23. Operational Use Cases: Write and Run SQL in the Embedded Editor

### Changed table — 3.2. Operational Use Cases

**Before:** TABLE rows=8 cols=2 :: ID | UC13 || Title | Write and Run SQL in the Embedded Editor || Description | Allows learners to solve SELECT query tasks in a safe environment. || Entities Involved | E02: Learner

**After:** TABLE rows=8 cols=2 :: ID | UC13 || Title | Write and Run SQL in the Embedded Editor || Description | Allows learners to solve SQL tasks in a safe environment: SELECT-only by default || Entities Involved | E02: Learner

### Changed paragraph — 3.2. Operational Use Cases

**Before:** Table . Operational Use Cases: Answer Multiple-Choice and Essay Questions

**After:** Table 24. Operational Use Cases: Answer Multiple-Choice and Essay Questions

### Changed paragraph — 3.2. Operational Use Cases

**Before:** Table . Operational Use Cases: Receive Grading Results and Feedback

**After:** Table 25. Operational Use Cases: Receive Grading Results and Feedback

### Changed table — 3.2. Operational Use Cases

**Before:** TABLE rows=8 cols=2 :: ID | UC15 || Title | Receive Grading Results and Feedback || Description | Scores every answer on submission and queues every submitted session for adminis || Entities Involved | E02: Learner, E04: LLM Provider

**After:** TABLE rows=8 cols=2 :: ID | UC15 || Title | Receive Grading Results and Feedback || Description | Scores every answer on submission and applies the release policy: FIXED Test pub || Entities Involved | E02: Learner, E04: LLM Provider

### Changed paragraph — 3.2. Operational Use Cases

**Before:** Table . Operational Use Cases: View Visual Competency Profile

**After:** Table 26. Operational Use Cases: View Visual Competency Profile

### Changed paragraph — 3.2. Operational Use Cases

**Before:** Table . Operational Use Cases: View Competency Gap Explanations

**After:** Table 27. Operational Use Cases: View Competency Gap Explanations

### Changed paragraph — 3.2. Operational Use Cases

**Before:** Table . Operational Use Cases: Review Assessment History and Evidence Records

**After:** Table 28. Operational Use Cases: Review Assessment History and Evidence Records

### Changed paragraph — 3.2. Operational Use Cases

**Before:** Table . Operational Use Cases: Manage Interface Preferences

**After:** Table 29. Operational Use Cases: Manage Interface Preferences

### Changed table — 3.2. Operational Use Cases

**Before:** TABLE rows=8 cols=2 :: ID | UC20 || Title | Review and Approve Results || Description | Allows an administrator to review automated grades for every submitted SQL and e || Entities Involved | E01: Administrator

**After:** TABLE rows=8 cols=2 :: ID | UC20 || Title | Review and Approve Results || Description | Allows an administrator to review automated grades for legacy/practice SQL and e || Entities Involved | E01: Administrator

### Changed paragraph — 3.3. Quality Attribute Scenarios

**Before:** Table . Quality Attribute Scenarios: Page and API Response Time

**After:** Table 31. Quality Attribute Scenarios: Page and API Response Time

### Changed paragraph — 3.3. Quality Attribute Scenarios

**Before:** Table . Quality Attribute Scenarios: SQL Sandbox Execution Time

**After:** Table 32. Quality Attribute Scenarios: SQL Sandbox Execution Time

### Changed paragraph — 3.3. Quality Attribute Scenarios

**Before:** Table . Quality Attribute Scenarios: Sandbox Isolation

**After:** Table 33. Quality Attribute Scenarios: Sandbox Isolation

### Changed paragraph — 3.3. Quality Attribute Scenarios

**Before:** Table . Quality Attribute Scenarios: Unauthorized Access Attempt

**After:** Table 34. Quality Attribute Scenarios: Unauthorized Access Attempt

### Changed paragraph — 3.3. Quality Attribute Scenarios

**Before:** Table . Quality Attribute Scenarios: Learner Data Privacy

**After:** Table 35. Quality Attribute Scenarios: Learner Data Privacy

### Changed paragraph — 3.3. Quality Attribute Scenarios

**Before:** Table . Quality Attribute Scenarios: Scoring Consistency

**After:** Table 36. Quality Attribute Scenarios: Scoring Consistency

### Changed paragraph — 3.3. Quality Attribute Scenarios

**Before:** Table . Quality Attribute Scenarios: Question Generation Never Blocks a Session

**After:** Table 37. Quality Attribute Scenarios: Question Generation Never Blocks a Session

### Changed paragraph — 3.3. Quality Attribute Scenarios

**Before:** Table . Quality Attribute Scenarios: Concurrent Learners

**After:** Table 38. Quality Attribute Scenarios: Concurrent Learners

### Changed paragraph — 3.3. Quality Attribute Scenarios

**Before:** Table . Quality Attribute Scenarios: Replacing the LLM Provider

**After:** Table 39. Quality Attribute Scenarios: Replacing the LLM Provider

### Changed paragraph — 3.3. Quality Attribute Scenarios

**Before:** Table . Quality Attribute Scenarios: Code Quality and Bug Fixing

**After:** Table 40. Quality Attribute Scenarios: Code Quality and Bug Fixing

### Changed paragraph — 3.3. Quality Attribute Scenarios

**Before:** Table . Quality Attribute Scenarios: Practice Interface Usability

**After:** Table 41. Quality Attribute Scenarios: Practice Interface Usability

### Changed paragraph — 3.4. Technical Constraints

**Before:** Table . Technical Constraints: Technology Stack Limitation

**After:** Table 42. Technical Constraints: Technology Stack Limitation

### Changed paragraph — 3.4. Technical Constraints

**Before:** Table . Technical Constraints: SQL Sandbox Resource Limits

**After:** Table 43. Technical Constraints: SQL Sandbox Resource Limits

### Changed paragraph — 3.4. Technical Constraints

**Before:** Table . Technical Constraints: External LLM Provider Limits and Latency

**After:** Table 44. Technical Constraints: External LLM Provider Limits and Latency

### Changed paragraph — 3.4. Technical Constraints

**Before:** Table . Technical Constraints: Modern Web Browser Compatibility

**After:** Table 45. Technical Constraints: Modern Web Browser Compatibility

### Changed paragraph — 3.5. Business Constraints

**Before:** Table . Business Constraints: Timeline and Deliverables

**After:** Table 46. Business Constraints: Timeline and Deliverables

### Changed paragraph — 3.5. Business Constraints

**Before:** Table . Business Constraints: Independent Benchmark Data

**After:** Table 47. Business Constraints: Independent Benchmark Data

### Changed paragraph — 3.5. Business Constraints

**Before:** Table . Business Constraints: Human-Governed AI Evaluation

**After:** Table 48. Business Constraints: Human-Governed AI Evaluation

### Changed paragraph — 3.5. Business Constraints

**Before:** Table . Business Constraints: Learner Data Privacy

**After:** Table 49. Business Constraints: Learner Data Privacy

### Changed paragraph — 4.1. Container Diagram

**Before:** Figure . Container Diagram

**After:** Figure 3. Container Diagram

### Changed paragraph — 4.1. Container Diagram

**Before:** All persistent data is stored in a PostgreSQL 17 database (66 tables) that the API accesses via SQL, including immutable session and question snapshots, legacy assessment records, password-reset tokens and audit, result-release audit and cached LLM responses. Learner SQL is never run against this database: it is executed in a separate, isolated SQL Execution Sandbox (a Docker container running PostgreSQL 17) under a read-only role, SELECT-only validation, a 3-second statement timeout, and a 256 MB memory limit. The API Application also calls an external LLM Provider API for assistive tasks such as essay scoring against rubrics, mapping and tag suggestions, and gap explanations; final compete

**After:** All persistent data is stored in a PostgreSQL 17 database (67 tables, 561 columns, 122 foreign keys, 159 indexes, 28 migrations) that the API accesses via SQL, including immutable session and question snapshots, legacy assessment records, password-reset tokens and audit, result-release audit and cached LLM responses. Learner SQL is never run against this database: it is executed in a separate, isolated SQL Execution Sandbox (a Docker container running PostgreSQL 17) under a default read-only role and SELECT-only validation; the opt-in demo profile allows writable DDL/DML in the disposable container, a 3-second statement timeout, and a 256 MB memory limit. The API Application also calls an ex

### Changed paragraph — 4.1. Container Diagram

**Before:** Table . Responsibilities of Container Diagram

**After:** Table 50. Responsibilities of Container Diagram

### Changed paragraph — 4.2. Component Diagram

**Before:** Figure  (1/2). Component Diagram — controllers, services and repositories: Auth, Practice, Curriculum and Question Bank.

**After:** Figure 4 (1/2). Component Diagram — controllers, services and repositories: Auth, Practice, Curriculum and Question Bank.

### Changed paragraph — 4.2. Component Diagram

**Before:** Figure  (2/2). Component Diagram — Analytics/Competency & Gap, Grading and Accounts/Admin & Settings. The Database cylinder is repeated for connector context; it is identical to Figure 4 (1/2).

**After:** Figure 4 (2/2). Component Diagram — Analytics/Competency & Gap, Grading and Accounts/Admin & Settings. The Database cylinder is repeated for connector context; it is identical to Figure 4 (1/2).

### Changed paragraph — 4.2. Component Diagram

**Before:** The Service layer is the core of the system logic: it includes the Identity & Access Service (password and OAuth sign-in, self-service password recovery, login throttling, role management), the Practice Service (session scope, complete plan freeze and idempotent starts), the Question Serving component (planned question delivery and selection logging), the Grading Service (MCQ by answer key, SQL by sandbox execution, essays by rubric), the Assessment Lifecycle & Release Service (grading jobs, human review and publication), and the Competency & Guidance Service (deterministic per-session and cumulative competency, gaps and study ranking). Two infrastructure components support these services: t

**After:** The Service layer is the core of the system logic: it includes the Identity & Access Service (password and OAuth sign-in, self-service password recovery, login throttling, role management), the Practice Service (session scope, complete plan freeze and idempotent starts), the Question Serving component (planned question delivery and selection logging), the Grading Service (MCQ by answer key, SQL by sandbox execution, essays by rubric), the Assessment Lifecycle & Release Service (grading jobs, AI-official FIXED publication and human-verified LEGACY publication), and the Competency & Guidance Service (deterministic per-session and cumulative competency, gaps and study ranking). Two infrastructu

### Changed paragraph — 4.2. Component Diagram

**Before:** Table . Responsibilities of Component Diagram

**After:** Table 51. Responsibilities of Component Diagram

### Changed paragraph — 5. Module View

**Before:** Figure . Module View

**After:** Figure 5. Module View

### Changed paragraph — 5. Module View

**Before:** The module view of DBCAS is organized into functional modules that collaborate to deliver the assessment workflow. The Web UI Module provides the Learner and Administrator portals as a single-page application, and the API Gateway Module routes and secures every request. The Identity & Access Module handles registration, email/password and OAuth login, self-service password recovery, login throttling, role-based access control, and audited role management. The Curriculum Module manages CLOs, concepts, prerequisites and confirmed mappings, while the Question Bank Module manages validated questions, provenance, translations, version families, tags, and AI question candidates awaiting administra

**After:** The module view of DBCAS is organized into functional modules that collaborate to deliver the assessment workflow. The Web UI Module provides the Learner and Administrator portals as a single-page application, and the API Gateway Module routes and secures every request. The Identity & Access Module handles registration, email/password and OAuth login, self-service password recovery, login throttling, role-based access control, and audited role management. The Curriculum Module manages CLOs, concepts, prerequisites and confirmed mappings, while the Question Bank Module manages validated questions, provenance, translations, version families, tags, and AI question candidates awaiting administra

### Changed paragraph — 5. Module View

**Before:** Table . Responsibilities of Module View

**After:** Table 52. Responsibilities of Module View

### Changed paragraph — 6. Allocation View

**Before:** Figure . Allocation View

**After:** Figure 6. Allocation View

### Changed paragraph — 6. Allocation View

**Before:** For persistence, the Application Server sends DB requests to the Database (PostgreSQL 17), which stores users, roles and audit records, the question bank, translations, sessions, attempts, immutable snapshots, evidence, release events and cached LLM responses. Learner SQL is sent to a separate SQL Sandbox container (PostgreSQL 17) that runs with a read-only role, SELECT-only validation, no network access, a 256 MB memory limit, and a 3-second statement timeout, so it can never reach application data. Finally, the Application Server calls the external LLM Provider API with sanitized, structured requests for essay scoring, mapping, tagging, and gap explanations, redirects browsers to Google or

**After:** For persistence, the Application Server sends DB requests to the Database (PostgreSQL 17), which stores users, roles and audit records, the question bank, translations, sessions, attempts, immutable snapshots, evidence, release events and cached LLM responses. Learner SQL is sent to a separate SQL Sandbox container (PostgreSQL 17) that runs with a read-only role and SELECT-only validation by default; the opt-in writable demo is ephemeral and rolled back. It has no network access, a 256 MB memory limit, and a 3-second statement timeout, so it can never reach application data. Finally, the Application Server calls the external LLM Provider API with sanitized, structured requests for essay scor

### Changed paragraph — 6. Allocation View

**Before:** Table . Responsibilities of Allocation View

**After:** Table 53. Responsibilities of Allocation View

### Changed paragraph — 7. Entity Relationship Diagram

**Before:** Figure . Entity Relationship Diagram

**After:** Figure 7. Entity relationship overview (1/2)

### Changed paragraph — 7. Entity Relationship Diagram

**Before:** Figure . Table Relationship Diagram (1/5)

**After:** Figure 7. Entity relationship index (2/2)

### Changed paragraph — 7. Entity Relationship Diagram

**Before:** Figure . Table Relationship Diagram (2/5)

**After:** Figure 8. Entity relationship diagram — Identity and access (1/11)

### Changed paragraph — 7. Entity Relationship Diagram

**Before:** Figure . Table Relationship Diagram (3/5)

**After:** Figure 8. Entity relationship diagram — Curriculum and concepts (2/11)

### Changed paragraph — 7. Entity Relationship Diagram

**Before:** Figure . Table Relationship Diagram (4/5)

**After:** Figure 8. Entity relationship diagram — Question bank and generation (3/11)

### Changed paragraph — 7. Entity Relationship Diagram

**Before:** Figure . Table Relationship Diagram (5/5)

**After:** Figure 8. Entity relationship diagram — Assessment and attempts (4/11)

### Changed paragraph — 7. Entity Relationship Diagram

**Before:** The Entity Relationship Diagram (ERD) illustrates the structure of the DBCAS PostgreSQL 17 database (66 tables) and the relationships among its entities. Account is the access point for authentication, linked one-to-one to UserProfile, optionally to AccountIdentity for OAuth, and through the AccountRole junction to Role; role changes are recorded in AccountRoleAudit and grade edits in GradeEditAudit. Administrators define CourseLearningOutcome and Concept records (with prerequisites in ConceptDependency), map them through CLOConcept, and curate the Question bank together with QuestionConcept, MCQOption, QuestionTranslation, SQLTestDataset, and Rubric. QuestionCandidate holds AI-generated dra

**After:** The Entity Relationship Diagram (ERD) illustrates the structure of the DBCAS PostgreSQL 17 database (67 tables) and the relationships among its entities. Account is the access point for authentication, linked one-to-one to UserProfile, optionally to AccountIdentity for OAuth, and through the AccountRole junction to Role; role changes are recorded in AccountRoleAudit and grade edits in GradeEditAudit. Administrators define CourseLearningOutcome and Concept records (with prerequisites in ConceptDependency), map them through CLOConcept, and curate the Question bank together with QuestionConcept, MCQOption, QuestionTranslation, SQLTestDataset, and Rubric. QuestionCandidate holds AI-generated dra

### Changed paragraph — 7. Entity Relationship Diagram

**Before:** The conceptual model in Figure 7 is implemented physically by the core tables shown in Figure 8. The many-to-many relationships (assigned, maps to, tagged with, targets) are realized by the junction tables AccountRole, CLOConcept, QuestionConcept and the legacy AssessmentConcept; all 66 tables are described in Table 54.

**After:** The conceptual model in Figure 7 is implemented physically by the core tables shown in Figure 8. The many-to-many relationships (assigned, maps to, tagged with, targets) are realized by the junction tables AccountRole, CLOConcept, QuestionConcept and the legacy AssessmentConcept; the 41 core tables are described in Table 54 and the 26 additional tables added by migrations 020–028 are described in Appendix A of the Database Design document.

### Changed paragraph — 7. Entity Relationship Diagram

**Before:** Table . Details about ERD tables

**After:** Table 54. Details about the 41 core ERD tables

### Added paragraph — 7. Entity Relationship Diagram

Appendix A. Open owner decisions

### Added paragraph — 7. Entity Relationship Diagram

The following values are not derivable from the repository. They stay owner-owned and are not asserted anywhere in this document.

### Added table — 7. Entity Relationship Diagram

TABLE rows=11 cols=4 :: ID | Item | Owner action required | Status || O1 | Team identities | Confirm every student ID, email address and phone number in Table 1 | Open || O2 | Supervisor and faculty | Confirm the official faculty/department name and whether an industry co-supervis | Open || O3 | Approvals and signatures | Sign the approval table and supply the approval dates | Open

### Added paragraph — 7. Entity Relationship Diagram

Appendix B. Figure sources

### Added paragraph — 7. Entity Relationship Diagram

Every shipped figure is traceable to a repository source. The figure number is the number used in the body and in the List of Figures.

### Added table — 7. Entity Relationship Diagram

TABLE rows=9 cols=4 :: Figure | Title | Source of truth | Verification || Figure 1 | Use case diagram | docs/diagrams/rebuild/use-case; use-case.svg | UC01–UC18 reviewed || Figure 2 | System context | docker-compose.local.yml; routers; oauth/mail services | external services verified in configuration || Figure 3 | Container / logical view | backend/app/main.py; Dockerfile; compose files | 7 routers; 67/561/122/159/28
