# Diff — TechnicalReport

Baseline: `C1SE.70_TechnicalReport_DBCAS_ver1.3.docx`
Final: `C1SE.70_TechnicalReport_DBCAS_ver1.3.docx`

## Summary

- Paragraphs: 62 changed, 66 added, 109 deleted
- Tables: 2 changed, 5 added, 2 deleted
- Figures: 0 replaced, 1 added, 0 removed
- Sections/headings changed: see detail below

## Figures

| Action | Baseline caption | Final caption |
|---|---|---|
| added |  | Figure 1. The evaluation pipeline: deterministic prompt assembly, provider call, validation, fallback and evidence publication |

## Detail

### Changed table — front matter

**Before:** TABLE rows=15 cols=5 :: PROJECT INFORMATION | PROJECT INFORMATION | PROJECT INFORMATION | PROJECT INFORMATION | PROJECT INFORMATION || Project acronym | SHFA | SHFA | SHFA | SHFA || Project Title | FitAI – Smart Health & Fitness Assistant | FitAI – Smart Health & Fitness Assistant | FitAI – Smart Health & Fitness Assistant | FitAI – Smart Health & Fitness Assistant || Start Date | 09 Sep 2025 | End Date | End Date | 15 Dec 2025

**After:** TABLE rows=15 cols=5 :: PROJECT INFORMATION | PROJECT INFORMATION | PROJECT INFORMATION | PROJECT INFORMATION | PROJECT INFORMATION || Project acronym | DBCAS | DBCAS | DBCAS | DBCAS || Project Title | DBCAS – AI-Assisted Database Competency Assessment and Skill Gap Analysis | DBCAS – AI-Assisted Database Competency Assessment and Skill Gap Analysis | DBCAS – AI-Assisted Database Competency Assessment and Skill Gap Analysis | DBCAS – AI-Assisted Database Competency Assessment and Skill Gap Analy

### Changed table — front matter

**Before:** TABLE rows=3 cols=5 :: Version | Date | Comments | Author | Approval || 1.0 | 14/12/2025 | Initial Release | All members |  || 2.0 | 15/12/2025 | Final | All members | 

**After:** TABLE rows=3 cols=5 :: Version | Date | Comments | Author | Approval || 1.0 | 18/09/2026 | Initial release | C1SE.70 Team |  || 1.3 | 26/11/2026 | Rebuilt from the FITAI AI Documentation frame with measured DBCAS evidence | Do, Nguyen Quoc | 

### Changed paragraph — front matter

**Before:** TABLE OF CONTENT

**After:** Table of Contents

### Changed paragraph — 1. Introduction

**Before:** The FitAI system is an integrated intelligent health assistant designed to provide safe, personalized, and culturally contextualized fitness and nutrition recommendations for Vietnamese users. It addresses a critical limitation found in most conventional health applications: the inability to provide scientifically grounded guidance tailored to individual physiology, lifestyle, and local dietary culture.

**After:** Assessment in database education has two problems that compound. The first is resolution: a single mark aggregates heterogeneous skills, so a learner who writes correct joins but cannot normalise a schema and a learner with the opposite profile receive the same grade [4], [5]. The second is feedback latency and consistency: grading SQL and written answers by hand is slow, and two markers may apply a rubric differently [8]. Practice sites address volume but stop at accepted or rejected output [14]; learning management systems store material and marks but cannot execute a query safely; general-purpose chatbots converse but do not preserve a measurement.

### Changed paragraph — 1. Introduction

**Before:** The system integrates multiple artificial intelligence technologies — including semantic retrieval, machine learning–based metabolic prediction, rule-based health evaluation, and large language model reasoning — to form a hybrid intelligent engine capable of analyzing queries, retrieving relevant domain knowledge, and generating structured, actionable health plans. By combining retrieved knowledge with user-specific health profiles, FitAI ensures that recommendations are safe, coherent, and highly personalized.

**After:** DBCAS starts from the curriculum rather than from the question bank. Course learning outcomes are mapped to concepts, concepts carry prerequisite edges, and questions are tagged to concepts. A practice session fixes its concepts, difficulty bands, length and source before the first question, so the session is reproducible. Each attempt produces evidence; the profile is computed from published evidence only. The research question of the project is therefore engineering-oriented: can a small team build an assessment pipeline whose numbers are reproducible, whose AI use is auditable, and whose failures are explicit?

### Changed paragraph — 1. Introduction

**Before:** Furthermore, FitAI supports multi-dimensional health goals such as weight loss, muscle gain, metabolic improvement, lifestyle coaching, injury prevention, and long-term habit formation. Through the use of dynamic profiling modules, the system adapts to variations in user attributes such as age, gender, body composition, regional dietary habits, and activity level. This increases the accuracy and reliability of the system and helps users receive scientifically valid, culturally appropriate guidance.

**After:** The report is organised as follows. Section 2 positions the work against related research and tools. Section 3 states the method: requirements, architecture and the measurement protocol. Section 4 describes the implementation. Section 5 reports experiments with the command or log behind every number. Section 6 discusses validity and limitations, and section 7 concludes.

### Changed paragraph — 1. Introduction

**Before:** 2. System Architecture

**After:** 2. Related Work

### Changed paragraph — 1. Introduction

**Before:** The FitAI system architecture is composed of three major components:

**After:** Four strands inform the design.

### Changed paragraph — 1. Introduction

**Before:** 1. Indexing Pipeline

**After:** Outcome-based assessment. Spady argues that instruction should be organised around explicit outcomes and that assessment should report progress toward them [4]; Biggs and Tang make the same point as constructive alignment between intended learning outcomes, activities and assessment [5]. DBCAS implements the alignment literally as a three-level mapping from course outcome to concept to question, and reports at the concept level rather than the course level.

### Changed paragraph — 1. Introduction

**Before:** 2. Inference Engine

**After:** Automated feedback. Keuning, Jeuring and Heeren review automated feedback for programming exercises and show that feedback which explains the error is more useful than a pass/fail verdict [8]. DBCAS therefore stores an explanation and documentation reference with every validated question, and its SQL grading reports the first diverging table or column rather than a boolean.

### Changed paragraph — 1. Introduction

**Before:** 3. Web Service Layer

**After:** Generative AI in computing education. Denny et al. describe both the opportunities and the risks of generative models in computing education [6], and Leinonen et al. compare explanations written by students and by models [7]. Both motivate a design in which the model assists a rubric but does not own the score. DBCAS validates model output against a schema and a domain contract, keeps a deterministic rubric as the fallback, and records which path produced the grade.

### Changed paragraph — 1. Introduction

**Before:** These components interact closely to deliver an end-to-end intelligent health recommendation experience, ensuring both computational efficiency and contextual accuracy.

**After:** Practice tools and database systems. Query-practice sites provide large problem sets and exact-output judging but no course-outcome mapping and no explanation of a wrong answer beyond the failing case [14]. The database literature that defines the concepts being measured is the standard textbook material [1], [2], and the curriculum guidance that defines expected competence is the ACM/IEEE computer science curricula [3]. The execution environment follows PostgreSQL 17 documentation [10] and Docker isolation guidance [11].

### Changed paragraph — 1. Introduction

**Before:** 2.1. Indexing Pipeline

**After:** 3. Method

### Changed paragraph — 1. Introduction

**Before:** The indexing pipeline is responsible for transforming raw datasets into a structured semantic knowledge base stored within Qdrant. This process includes data ingestion, cleaning, chunking, metadata generation, embedding generation, and vector storage.

**After:** 3.1 Requirements and Scope

### Changed paragraph — 1. Introduction

**Before:** Raw datasets include Vietnamese workout descriptions, food calorie tables, fitness program structures, and domain-specific explanatory resources. These datasets often come in various formats and with inconsistent linguistic structures, especially when sourced from community-contributed platforms or public repositories. The pipeline normalizes these sources and prepares them for high-quality retrieval.

**After:** The requirements were derived from the curriculum mapping and from the failure modes of the alternatives: per-concept reporting, three answer formats, a frozen plan, explicit publication states, auditability, and a sandbox that cannot reach the application database. The system is a single-institution deployment; multi-tenancy, payment, proctoring and trained models are out of scope.

### Changed paragraph — 1. Introduction

**Before:** Through text chunking and semantic hashing, the system ensures non-redundant storage of domain information while capturing essential meaning units. BGE-M3 embeddings are computed for each chunk, producing high-dimensional vectors that represent contextual meaning across both Vietnamese and English content. The vectors, along with metadata such as exercise difficulty, muscle group, meal type, or caloric range, are stored in Qdrant Cloud for efficient semantic search

**After:** 3.2 Architecture

### Changed paragraph — 1. Introduction

**Before:** 2.2. Inference Engine

**After:** DBCAS is a four-tier modular monolith: a React single-page frontend, a FastAPI application that also hosts a bounded worker, PostgreSQL 17, and an ephemeral PostgreSQL container created per SQL execution. The application is layered into routers, services and repository classes; transactions and locks live in services and repositories. The Architecture Design document specifies the views, the flows and the decisions; this report uses them without reproducing them.

### Changed paragraph — 1. Introduction

**Before:** The inference engine integrates the Qdrant semantic retriever with a local reasoning model (Qwen2.5-3B) and a smart health profile analyzer. When a user submits a query, the inference engine performs several coordinated tasks

**After:** Figure 1. The evaluation pipeline: deterministic prompt assembly, provider call, validation, fallback and evidence publication

### Changed paragraph — 1. Introduction

**Before:** 2.2.1. Health Profile Estimation:

**After:** 3.3 Measurement Protocol

### Changed paragraph — 1. Introduction

**Before:** The system examines available inputs (age, gender, weight, height, region). If missing, it uses default demographic assumptions drawn from Vietnamese health statistics. Using this, it computes BMI, BMR, and TDEE via hybrid metabolic models.

**After:** Every quantity in this report is produced by a command that reads the repository or the running system, and every command is recorded with its output in a log file. Schema facts come from PostgreSQL 17.12 introspection after all migrations, not from reading DDL. API facts come from the OpenAPI document generated by the application. Test facts come from running the suites. Secret facts come from the scanner. Document facts come from the final DOCX packages. No number in this report is estimated, rounded from memory, or copied from an earlier document; where a value could not be measured it is marked as an open item instead.

### Changed paragraph — 1. Introduction

**Before:** 2.2.2. Semantic Retrieval:

**After:** 4. Implementation

### Changed paragraph — 1. Introduction

**Before:** The query is encoded using the same embedding model used during indexing. Qdrant returns the top-k semantically relevant text chunks, which may include workout procedures, nutritional guidelines, or safety constraints.

**After:** 4.1 Data Model

### Changed paragraph — 1. Introduction

**Before:** 2.2.3. Context Filtering:

**After:** The schema has 67 application tables and 561 columns, 122 foreign keys and 159 indexes, built by 28 forward-only migrations. History is carried by dedicated tables rather than by mutating rows: result versions, per-criterion score snapshots, rubric profiles, AI stage runs and append-only audit tables, protected by 41 triggers (36 row-level guards and five constraint triggers). The migration runner stores the SHA-256 of every applied file and refuses to continue if a file changed, so an applied migration is immutable.

### Changed paragraph — 1. Introduction

**Before:** Retrieved chunks are ranked using a hybrid scoring approach that includes semantic similarity, keyword presence, goal relevance (e.g., fat loss vs. hypertrophy), and user-specific constraints (e.g., obesity, injury risk).

**After:** 4.2 Practice and Grading

### Changed paragraph — 1. Introduction

**Before:** 2.2.4. Knowledge Synthesis with LLM:

**After:** A session plan is assembled from the validated bank, optionally with generated and validated items, and frozen with its configuration snapshot. Selection is deterministic: the opening three questions are basic multiple-choice items covering unseen concepts, the fourth question is biased by the opening result, and later questions follow quota pressure, weakest-concept selection and one-step difficulty adjustment, with every tie broken by the question identifier. MCQ is graded by exact option matching; SQL by comparing a normalised result grid or the captured table state after a data-manipulation task; essays by rubric criteria, with the provider assisting and a deterministic rubric as fallbac

### Changed paragraph — 1. Introduction

**Before:** The retrieved context and the computed health profile are fed into a structured prompt. Qwen2.5-3B evaluates the evidence, synthesizes insights, and provides a detailed, human-readable explanation customized for the user’s physiological and cultural context.

**After:** 4.3 Isolation

### Changed paragraph — 1. Introduction

**Before:** 2.3. Web Service Layer

**After:** Learner SQL runs in a container with no network, 256 MB of memory without swap, one CPU, 128 PIDs, a read-only root filesystem, a non-root user, all capabilities dropped and no-new-privileges, with a 45-second container lifetime and a 3 000 ms statement timeout. The statement policy parses the script and rejects any construct outside an allowlist; a read-only database role provides a second, independent barrier. Two executions may run at once, and the third waits or is rejected with an explicit busy error.

### Changed paragraph — 1. Introduction

**Before:** The system exposes its capabilities through a Fast API-based HTTP interface. This ensures a modular, upgradeable structure that can be used by web applications, mobile apps, or integration systems.

**After:** 4.4 Audit and Publication

### Changed paragraph — 1. Introduction

**Before:** The service handles CORS, request validation, asynchronous processing, caching through Redis, and error handling. It also includes monitoring endpoints for debugging the retrieval pipeline, allowing developers to inspect which chunks were used to produce an answer — enhancing system transparency.

**After:** Two publication paths exist. A fixed-test session publishes an official V1 result inside the finalize transaction, with a result hash and per-question scores. A practice or legacy session stays pending until an administrator reviews it; a learner may request a review inside seven days, an administrator claims it with a 30-minute lease and either rejects or regrades it, and a deviation above 30 % needs a second confirmation. The worker never decides on the learner's behalf. Every transition is recorded, and the learner's cumulative profile is recomputed from published evidence only.

### Changed paragraph — 1. Introduction

**Before:** 3. Technologies Used

**After:** 5. Experiments

### Changed paragraph — 1. Introduction

**Before:** The FitAI system integrates multiple modern technologies to ensure performance, reliability, and adaptability:

**After:** The experiments are reproducibility checks rather than a user study. Each row states what was measured, the measured value and the command or log that produced it. All values were re-measured for this report.

### Changed paragraph — 1. Introduction

**Before:** Python serves as the primary development language.

**After:** Table 1. Measured results

### Changed paragraph — 1. Introduction

**Before:** Reasoning Model: Qwen 2.5–3B via Ollama for efficient local inference and chain-of-thought compression.

**After:** 5.1 What the Numbers Show

### Changed paragraph — 1. Introduction

**Before:** Qdrant Cloud: A high-performance vector database used to store and retrieve semantic embeddings.

**After:** Three observations follow. First, the test surface is large relative to the application: 1 940 backend tests and 463 frontend tests cover a backend of 24 956 Python lines under backend/app and 49 915 under backend/app plus backend/tests, and a frontend of 26 441 JavaScript lines under frontend/src. Second, the browser suites are sharded by configuration rather than by retry: nine shards run disjoint specifications and a fan-in job requires exactly nine success reports, which removes the incentive to make a flaky test pass by rerunning it. Third, the schema is intentionally conservative: 122 foreign keys and 41 triggers exist so that a wrong update fails in the database rather than in a repor

### Changed paragraph — 1. Introduction

**Before:** PostgreSQL (Neon): Stores structured metadata such as user profiles and processed datasets.

**After:** 5.2 Reproducibility

### Changed paragraph — 1. Introduction

**Before:** Redis Cloud: Accelerates responses with caching and temporary session storage.

**After:** A clean clone reproduces the numbers with the documented commands: the schema from db/schema.sql plus 28 migrations, the API contract from the application, the tests from the suites, and the documents from one generator that reads the same facts. The document generator refuses to guess: anything the repository cannot prove is emitted as an explicit owner field rather than a plausible value.

### Changed paragraph — 1. Introduction

**Before:** Fast API: Provides a scalable and developer-friendly framework for web service deployment.

**After:** 6. Discussion and Limitations

### Changed paragraph — 1. Introduction

**Before:** ONNX Runtime: Enhances CPU-side embedding speed for large dataset indexing.

**After:** Internal validity. The measurements are exact counts of artefacts, not estimates, and the scripts that produce them are committed. The main internal risk is drift between the documents and the code; it is mitigated by a verification script that re-reads the DOCX and compares every number with the measured value, and by a documentation gate in CI.

### Changed paragraph — 1. Introduction

**Before:** Pandas, NumPy: Handle data processing during ingestion and profiling tasks.

**After:** External validity. DBCAS was evaluated on one PostgreSQL concept model, one institution and two roles. The corpus contains 446 questions over 98 concepts and 12 course learning outcomes, which is enough to demonstrate the pipeline but not enough to claim learning gains. No controlled study with learners was run, so this report makes no claim about learning outcomes.

### Changed paragraph — 1. Introduction

**Before:** 4. Data Processing and Preprocessing

**After:** Construct validity. Concept scores are computed from question scores; a question that is tagged to the wrong concept would distort the profile. The system mitigates this with confirmed tags and an administrator review of suggested mappings, but the tagging itself is not independently validated.

### Changed paragraph — 1. Introduction

**Before:** 4.1 Dataset

**After:** Reliability. Deterministic grading is reproducible by construction. The model-assisted path is not: the same essay may receive a slightly different rubric comment, which is why the fallback exists and why AI-assisted grades require verification in the practice flow. Provider availability, latency and retention terms are operational risks and are recorded as such; production release remains on hold until the retention question is decided.

### Changed paragraph — 1. Introduction

**Before:** The FitAI system utilizes multiple fitness and nutrition-related datasets collected from public sources such as Kaggle and open fitness repositories. These datasets include information about workout programs, exercise descriptions, fitness goals, training levels, and general health-related text data.

**After:** Capacity. The sandbox admits two concurrent executions. A third request waits five seconds and then fails with an explicit busy error. This is adequate for a demonstration and for a small class, not for a faculty-wide deployment; horizontal scaling would require a broker, which is designed but not enabled by default.

### Changed paragraph — 1. Introduction

**Before:** Key datasets used in the system include:

**After:** Threats to the document set itself. The documents are generated, so a fact that no script checks could still be wrong. The mitigation is coverage: schema, API, test, secret, route and document facts are machine-checked; owner facts such as student identities or approval dates are not derivable from code and are marked for the owner instead of being asserted.

### Changed paragraph — 1. Introduction

**Before:** GYM.csv: Contains gym exercise names, descriptions, and equipment information.

**After:** 7. Conclusion

### Changed paragraph — 1. Introduction

**Before:** Program_summary.csv: Provides summarized workout programs with training goals and difficulty levels.

**After:** DBCAS shows that a small team can build an assessment system whose claims are reproducible. The design separates what is measured (attempts, question versions, concept tags), what is computed (scores, profiles, gaps) and what is decided (publication, review), and it makes every failure explicit: a bank shortage stops a session, a provider outage falls back to a deterministic rubric, a sandbox refusal is a named error, and a retried submission returns the stored result. The measured evidence - 67 tables, 106 API paths, 1 940 backend tests, 152 browser tests, 14 green CI jobs at commit d6df804 and zero secret findings - describes a system that is small in scope and strict in evidence. Future w

### Changed paragraph — 1. Introduction

**Before:** Programs_detailed_boostcamp_kaggle.csv: Includes detailed workout program content, schedules, and exercise breakdowns.

**After:** References

### Changed paragraph — 1. Introduction

**Before:** Fitness_and_workout_dataset.csv: Contains mixed fitness and workout-related textual data.

**After:** [1] A. Silberschatz, H. F. Korth, and S. Sudarshan, Database System Concepts, 7th ed. New York, NY, USA: McGraw-Hill Education, 2019.

### Changed paragraph — 1. Introduction

**Before:** All datasets are processed and indexed into the Qdrant vector database, enabling semantic search and retrieval during chatbot inference.

**After:** [2] R. Ramakrishnan and J. Gehrke, Database Management Systems, 3rd ed. New York, NY, USA: McGraw-Hill, 2003.

### Changed paragraph — 1. Introduction

**Before:** 4.2 Data Augmentation

**After:** [3] ACM and IEEE Computer Society, "Computer Science Curricula 2013: Curriculum Guidelines for Undergraduate Degree Programs in Computer Science," ACM/IEEE Joint Task Force on Computing Curricula, Tech. Rep., 2013.

### Changed paragraph — 1. Introduction

**Before:** To enhance data diversity and improve retrieval quality, the system applies lightweight data augmentation techniques during preprocessing, including:

**After:** [4] W. Spady, Outcome-Based Education: Critical Issues and Answers. Arlington, VA, USA: American Association of School Administrators, 1994.

### Changed paragraph — 1. Introduction

**Before:** Text Chunking: Long textual records are split into smaller overlapping chunks to preserve semantic meaning while increasing retrievable units.

**After:** [5] J. Biggs and C. Tang, Teaching for Quality Learning at University: What the Student Does, 4th ed. Maidenhead, UK: Open University Press, 2011.

### Changed paragraph — 1. Introduction

**Before:** Content Combination: Multiple related attributes (exercise name, description, goal, and level) are merged into a unified text representation.

**After:** [6] P. Denny, J. Prather, B. A. Becker et al., "Computing Education in the Era of Generative AI," Communications of the ACM, vol. 67, no. 2, pp. 56–67, 2024, doi: 10.1145/3624720.

### Changed paragraph — 1. Introduction

**Before:** Deduplication: MD5-based hashing is used to remove duplicated text chunks before indexing, reducing redundant embeddings.

**After:** [7] J. Leinonen, P. Denny, S. MacNeil et al., "Comparing Code Explanations Created by Students and Large Language Models," in Proc. ITiCSE '23, 2023, pp. 124–130, doi: 10.1145/3587102.3588785.

### Changed paragraph — 1. Introduction

**Before:** These techniques help the system better handle varied user queries and improve contextual coverage during retrieval.

**After:** [8] H. Keuning, J. Jeuring, and B. Heeren, "A Systematic Literature Review of Automated Feedback Generation for Programming Exercises," ACM Trans. Computing Education, vol. 19, no. 1, pp. 1–43, 2018, doi: 10.1145/3231711.

### Changed paragraph — 1. Introduction

**Before:** 4.3 Normalization

**After:** [9] Google, "Gemini: A Family of Highly Capable Multimodal Models," arXiv preprint arXiv:2312.11805, 2023.

### Changed paragraph — 1. Introduction

**Before:** Normalization is applied to ensure consistency and efficiency in downstream processing:

**After:** [10] PostgreSQL Global Development Group, "PostgreSQL 17 Documentation," 2024. [Online]. Available: https://www.postgresql.org/docs/17/

### Changed paragraph — 1. Introduction

**Before:** Text Normalization: All text is cleaned by removing null values, unnecessary symbols, and redundant whitespace.

**After:** [11] Docker Inc., "Docker Documentation: Resource Constraints and Container Security," 2024. [Online]. Available: https://docs.docker.com/engine/security/

### Changed paragraph — 1. Introduction

**Before:** Embedding Normalization: All vector embeddings are L2-normalized before being stored in Qdrant to ensure stable cosine similarity calculations.

**After:** [12] Meta Open Source, "React Documentation," 2024. [Online]. Available: https://react.dev/

### Changed paragraph — 1. Introduction

**Before:** Metadata Standardization: Metadata fields such as data source and excerpt length are standardized to support filtering and traceability.

**After:** [13] FastAPI project and contributors, "FastAPI Documentation," 2024. [Online]. Available: https://fastapi.tiangolo.com/

### Changed paragraph — 1. Introduction

**Before:** 5. Model Architecture

**After:** [14] LeetCode LLC, "LeetCode Database Problem Set and Automated Query Evaluation Engine," 2024. [Online]. Available: https://leetcode.com/problemset/database/

### Changed paragraph — 1. Introduction

**Before:** 5.1 Base Model

**After:** Appendix A. Open owner decisions

### Changed paragraph — 1. Introduction

**Before:** The FitAI system employs a Retrieval-Augmented Generation (RAG) architecture to support intelligent health and fitness recommendations. Unlike traditional supervised learning systems, FitAI does not rely on a single classification model but instead integrates semantic embedding models and large language models to generate context-aware responses.

**After:** The following values are not derivable from the repository. They stay owner-owned and are not asserted anywhere in this document.

### Changed paragraph — 1. Introduction

**Before:** The embedding model enables:

**After:** Appendix B. Figure sources

### Changed paragraph — 1. Introduction

**Before:** Semantic similarity matching between user queries and indexed fitness knowledge

**After:** Every shipped figure is traceable to a repository source. The figure number is the number used in the body and in the List of Figures.
