# Diff — DatabaseDesign

Baseline: `C1SE.70_DatabaseDesign_DBCAS_ver1.3.docx`
Final: `C1SE.70_DatabaseDesign_DBCAS_ver1.3.docx`

## Summary

- Paragraphs: 5 changed, 162 added, 7 deleted
- Tables: 22 changed, 70 added, 22 deleted
- Figures: 2 replaced, 11 added, 0 removed
- Sections/headings changed: see detail below

## Figures

| Action | Baseline caption | Final caption |
|---|---|---|
| replaced | Figure 1: Entity Relationship Diagram | Figure 1: Entity relationship overview (1/2) |
| replaced | Figure 2: Table Relationship Diagram | Figure 1: Entity relationship index (2/2) |
| added |  | Figure 2: Entity relationship diagram — Identity and access (1/11) |
| added |  | Figure 2: Entity relationship diagram — Curriculum and concepts (2/11) |
| added |  | Figure 2: Entity relationship diagram — Question bank and generation (3/11) |
| added |  | Figure 2: Entity relationship diagram — Assessment and attempts (4/11) |
| added |  | Figure 2: Entity relationship diagram — Grading, results and competency (5/11) |
| added |  | Figure 2: Entity relationship diagram — Review workflow (6/11) |
| added |  | Figure 2: Entity relationship diagram — AI audit and retention (7/11) |
| added |  | Figure 2: Foreign-key ledger — rows 1–31 of 122 (8/11) |
| added |  | Figure 2: Foreign-key ledger — rows 32–62 of 122 (9/11) |
| added |  | Figure 2: Foreign-key ledger — rows 63–92 of 122 (10/11) |
| added |  | Figure 2: Foreign-key ledger — rows 93–122 of 122 (11/11) |

## Detail

### Changed paragraph — front matter

**Before:** TABLE OF CONTENTS

**After:** Table of Contents

### Changed paragraph — Introduction about PostgreSQL

**Before:** In PostgreSQL, data is organized into tables with well-defined schemas. Constraints such as primary keys, foreign keys, unique constraints, and default values enforce data integrity across the 21 tables of the DBCAS schema, while JSONB columns keep flexible evidence payloads — grading detail, adaptive selection decisions, and cached LLM responses — queryable.

**After:** The versioned schema behind this document contains 67 tables, 561 columns, 122 foreign keys, 159 indexes and 28 forward migrations (PostgreSQL 17.12 introspection after migration 028). The 159 indexes comprise 67 primary-key indexes, 50 unique indexes and 42 standalone performance indexes; unique constraints are counted separately from the indexes that enforce them.

### Changed table — Table Overview

**Before:** TABLE rows=22 cols=2 :: Table Name | Short Description || Account | Stores login credentials for learners and administrators, including email, passw || Role | Defines the two system roles used for role-based access control: Learner and Adm || AccountRole | Junction table resolving the many-to-many relationship between Account and Role,

**After:** TABLE rows=68 cols=2 :: Table Name | Short Description || Account | Stores login credentials for learners and administrators, including email, passw || Role | Defines the two system roles used for role-based access control: Learner and Adm || AccountRole | Junction table resolving the many-to-many relationship between Account and Role,

### Changed paragraph — Entity Relationship Diagram

**Before:** Figure 1: Entity Relationship Diagram

**After:** Figures 1 and 2 show the domain overview, the table index, seven module ERDs with intra-module relationship lines, and four ledgers that enumerate every foreign key. All 67 tables, 561 columns and 122 foreign keys are covered; the full column dictionary follows in Section 3 and Appendix A.

### Changed paragraph — Entity Relationship Diagram

**Before:** Figure 1 is the conceptual model: the four M : N relationships (assigned, maps to, tagged with, targets) are implemented by the junction tables AccountRole, CLOConcept, QuestionConcept and AssessmentConcept shown in Figure 2. LLMCache is a stand-alone technical table.

**After:** Figure 1: Entity relationship overview (1/2)

### Changed paragraph — Entity Relationship Diagram

**Before:** Figure 2: Table Relationship Diagram

**After:** Figure 1: Entity relationship index (2/2)

### Changed table — Account

**Before:** TABLE rows=6 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || account_id | INT | Not | PK |  | IDENTITY || email | VARCHAR(255) | Not |  |  | Unique || password_hash | VARCHAR(255) | Not |  |  | 

**After:** TABLE rows=9 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || account_id | INT | Not | PK |  | Owning account identifier. || email | VARCHAR(255) | Not | UNIQUE |  | Account email address. || password_hash | VARCHAR(255) | Not |  |  | bcrypt password hash.

### Changed table — Role

**Before:** TABLE rows=4 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || role_id | INT | Not | PK |  | IDENTITY || role_name | VARCHAR(50) | Not |  |  | Unique (Learner / Administrator) || description | TEXT | Yes |  |  | 

**After:** TABLE rows=4 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || role_id | INT | Not | PK |  | Role identifier. || role_name | VARCHAR(50) | Not | UNIQUE |  | Role name. || description | TEXT | Yes |  |  | Human-readable description.

### Changed table — AccountRole

**Before:** TABLE rows=4 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || account_id | INT | Not | PK,FK |  | FK → Account || role_id | INT | Not | PK,FK |  | FK → Role || assigned_at | TIMESTAMPTZ | Not |  | NOW() | 

**After:** TABLE rows=4 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || account_id | INT | Not | PK, FK |  | Owning account identifier. || role_id | INT | Not | PK, FK |  | Role identifier. || assigned_at | TIMESTAMPTZ | Not |  | now() | Time the role was assigned.

### Changed table — UserProfile

**Before:** TABLE rows=7 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || user_id | INT | Not | PK |  | IDENTITY || account_id | INT | Not | FK |  | FK → Account, Unique (1-1) || full_name | VARCHAR(100) | Not |  |  | PII — stripped before LLM calls

**After:** TABLE rows=7 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || user_id | INT | Not | PK |  | User profile identifier. || account_id | INT | Not | UNIQUE, FK |  | Owning account identifier. || full_name | VARCHAR(100) | Not |  |  | Display name.

### Changed table — CourseLearningOutcome

**Before:** TABLE rows=8 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || clo_id | INT | Not | PK |  | IDENTITY || clo_code | VARCHAR(20) | Not |  |  | Unique (e.g. CLO-01) || title | VARCHAR(200) | Not |  |  | 

**After:** TABLE rows=8 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || clo_id | INT | Not | PK |  | Course learning outcome identifier. || clo_code | VARCHAR(20) | Not | UNIQUE |  | Short course-learning-outcome code. || title | VARCHAR(200) | Not |  |  | Title.

### Changed table — Concept

**Before:** TABLE rows=7 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || concept_id | INT | Not | PK |  | IDENTITY || concept_code | VARCHAR(30) | Not |  |  | Unique (e.g. SQL-JOIN) || concept_name | VARCHAR(100) | Not |  |  | 

**After:** TABLE rows=10 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || concept_id | INT | Not | PK |  | Concept identifier. || concept_code | VARCHAR(30) | Not | UNIQUE |  | Short concept code. || concept_name | VARCHAR(100) | Not |  |  | Concept name.

### Changed table — CLOConcept

**Before:** TABLE rows=6 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || clo_id | INT | Not | PK,FK |  | FK → CourseLearningOutcome || concept_id | INT | Not | PK,FK |  | FK → Concept || mapping_source | VARCHAR(10) | Not |  | 'admin' | admin / ai

**After:** TABLE rows=6 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || clo_id | INT | Not | PK, FK |  | Course learning outcome identifier. || concept_id | INT | Not | PK, FK |  | Concept identifier. || mapping_source | VARCHAR(10) | Not |  | 'admin'::character varying | Whether the mapping came from an administrator or AI.

### Changed table — Question

**Before:** TABLE rows=12 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || question_id | INT | Not | PK |  | IDENTITY || question_type | VARCHAR(10) | Not |  |  | mcq / sql / essay || prompt | TEXT | Not |  |  | 

**After:** TABLE rows=19 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || question_id | INT | Not | PK |  | Question identifier. || question_type | VARCHAR(10) | Not |  |  | Question format: mcq, sql or essay. || prompt | TEXT | Not |  |  | Question prompt text.

### Changed table — QuestionConcept

**Before:** TABLE rows=6 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || question_id | INT | Not | PK,FK |  | FK → Question || concept_id | INT | Not | PK,FK |  | FK → Concept || tag_source | VARCHAR(10) | Not |  | 'admin' | admin / ai

**After:** TABLE rows=7 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || question_id | INT | Not | PK, FK |  | Question identifier. || concept_id | INT | Not | PK, FK |  | Concept identifier. || tag_source | VARCHAR(10) | Not |  | 'admin'::character varying | Whether the tag came from admin, auto or AI.

### Changed table — MCQOption

**Before:** TABLE rows=6 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || option_id | INT | Not | PK |  | IDENTITY || question_id | INT | Not | FK |  | FK → Question || option_label | VARCHAR(5) | Not |  |  | A / B / C / D

**After:** TABLE rows=6 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || option_id | INT | Not | PK |  | Identifier of the related option. || question_id | INT | Not | FK |  | Question identifier. || option_label | VARCHAR(5) | Not |  |  | Option label.

### Changed table — SQLTestDataset

**Before:** TABLE rows=7 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || dataset_id | INT | Not | PK |  | IDENTITY || question_id | INT | Not | FK |  | FK → Question (sql type) || dataset_name | VARCHAR(100) | Not |  |  | 

**After:** TABLE rows=7 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || dataset_id | INT | Not | PK |  | SQL test dataset identifier. || question_id | INT | Not | FK |  | Question identifier. || dataset_name | VARCHAR(100) | Not |  |  | Dataset name.

### Changed table — Rubric

**Before:** TABLE rows=7 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || rubric_id | INT | Not | PK |  | IDENTITY || question_id | INT | Not | FK |  | FK → Question (essay type) || level_name | VARCHAR(30) | Not |  |  | Complete / Mostly Complete / Partial / Incomplete

**After:** TABLE rows=7 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || rubric_id | INT | Not | PK |  | Identifier of the related rubric. || question_id | INT | Not | FK |  | Question identifier. || level_name | VARCHAR(30) | Not |  |  | Rubric level label.

### Changed table — Assessment

**Before:** TABLE rows=12 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || assessment_id | INT | Not | PK |  | IDENTITY || title | VARCHAR(200) | Not |  |  |  || description | TEXT | Yes |  |  | 

**After:** TABLE rows=15 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || assessment_id | INT | Not | PK |  | Assessment identifier. || title | VARCHAR(200) | Not |  |  | Title. || description | TEXT | Yes |  |  | Human-readable description.

### Changed table — AssessmentConcept

**Before:** TABLE rows=6 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || assessment_id | INT | Not | PK,FK |  | FK → Assessment || concept_id | INT | Not | PK,FK |  | FK → Concept || min_difficulty | SMALLINT | Not |  | 1 | 1–5 scale

**After:** TABLE rows=6 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || assessment_id | INT | Not | PK, FK |  | Assessment identifier. || concept_id | INT | Not | PK, FK |  | Concept identifier. || min_difficulty | SMALLINT | Not |  | 1 | Min difficulty.

### Changed table — AssessmentSession

**Before:** TABLE rows=8 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || session_id | INT | Not | PK |  | IDENTITY || assessment_id | INT | Not | FK |  | FK → Assessment || learner_id | INT | Not | FK |  | FK → Account (learner)

**After:** TABLE rows=23 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || session_id | INT | Not | PK, FK |  | Assessment session identifier. || assessment_id | INT | Yes | FK |  | Assessment identifier. || learner_id | INT | Not | FK |  | Learner account identifier.

### Changed table — Attempt

**Before:** TABLE rows=12 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || attempt_id | INT | Not | PK |  | IDENTITY || session_id | INT | Not | FK |  | FK → AssessmentSession || question_id | INT | Not | FK |  | FK → Question

**After:** TABLE rows=22 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || attempt_id | INT | Not | PK |  | Attempt identifier. || session_id | INT | Not | FK |  | Assessment session identifier. || question_id | INT | Not | FK |  | Question identifier.

### Changed table — SelectionLog

**Before:** TABLE rows=8 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || log_id | INT | Not | PK |  | IDENTITY || session_id | INT | Not | FK |  | FK → AssessmentSession || seq_no | SMALLINT | Not |  |  | 

**After:** TABLE rows=8 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || log_id | INT | Not | PK |  | Identifier of the related log. || session_id | INT | Not | FK |  | Assessment session identifier. || seq_no | SMALLINT | Not |  |  | Seq no.

### Changed table — ConceptCompetency

**Before:** TABLE rows=9 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || competency_id | INT | Not | PK |  | IDENTITY || session_id | INT | Not | FK |  | FK → AssessmentSession || concept_id | INT | Not | FK |  | FK → Concept; Unique per session

**After:** TABLE rows=9 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || competency_id | INT | Not | PK |  | Identifier of the related competency. || session_id | INT | Not | FK |  | Assessment session identifier. || concept_id | INT | Not | FK |  | Concept identifier.

### Changed table — CompetencyGap

**Before:** TABLE rows=7 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || gap_id | INT | Not | PK |  | IDENTITY || session_id | INT | Not | FK |  | FK → AssessmentSession || concept_id | INT | Not | FK |  | FK → Concept

**After:** TABLE rows=8 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || gap_id | INT | Not | PK |  | Competency gap identifier. || session_id | INT | Not | FK |  | Assessment session identifier. || concept_id | INT | Not | FK |  | Concept identifier.

### Changed table — LLMCache

**Before:** TABLE rows=7 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || cache_id | INT | Not | PK |  | IDENTITY || request_hash | VARCHAR(64) | Not |  |  | Unique (SHA-256 of sanitized prompt) || task_type | VARCHAR(30) | Not |  |  | essay_score / clo_map / tag / gap_explain

**After:** TABLE rows=8 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || cache_id | INT | Not | PK |  | Identifier of the related cache. || request_hash | VARCHAR(64) | Not | UNIQUE |  | Hash of the start request payload. || task_type | VARCHAR(30) | Not |  |  | Task type.

### Changed table — QuestionCandidate

**Before:** TABLE rows=9 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || candidate_id | INT | Not | PK |  | IDENTITY || concept_id | INT | Not | FK |  | FK → Concept || question_type | VARCHAR(10) | Not |  |  | mcq / sql / essay

**After:** TABLE rows=9 cols=6 :: Attributes | Datatype | Null | Key | Default | Extra || candidate_id | INT | Not | PK |  | Identifier of the related candidate. || concept_id | INT | Not | FK |  | Concept identifier. || question_type | VARCHAR(10) | Not |  |  | Question format: mcq, sql or essay.

### Added paragraph — Hardware and Software Requirements

Appendix B. Open owner decisions

### Added paragraph — Hardware and Software Requirements

The following values are not derivable from the repository. They stay owner-owned and are not asserted anywhere in this document.

### Added table — Hardware and Software Requirements

TABLE rows=11 cols=4 :: ID | Item | Owner action required | Status || O1 | Team identities | Confirm every student ID, email address and phone number in Table 1 | Open || O2 | Supervisor and faculty | Confirm the official faculty/department name and whether an industry co-supervis | Open || O3 | Approvals and signatures | Sign the approval table and supply the approval dates | Open

### Added paragraph — Hardware and Software Requirements

Appendix C. Figure sources

### Added paragraph — Hardware and Software Requirements

Every shipped figure is traceable to a repository source. The figure number is the number used in the body and in the List of Figures.

### Added table — Hardware and Software Requirements

TABLE rows=4 cols=4 :: Figure | Title | Source of truth | Verification || Figure 1 | ERD overview and index (1/2, 2/2) | schema-028/schema-introspection.json | 67 tables / 561 columns / 122 FKs / 159 indexes / 28 migrations || Figure 2 | Module ERDs (1/7–7/7) | schema-028/schema-introspection.json | 67 tables mapped once to seven domains; intra-module FK lines || Figure 2 | FK ledgers (8/11–11/11) | schema-028/schema-introspection.json | 122 foreign keys with cardinality and delete/update rules
