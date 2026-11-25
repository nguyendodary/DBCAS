# -*- coding: utf-8 -*-
"""Proposal content: the fifteen required sections, in the required order.

Every figure, count and identifier in this module is re-measured by
scripts/verify_submission_docs.py against the repository.  Owner facts come
from the verified v1.2/ver1.3 sources; anything they do not contain is written
as [OWNER TO PROVIDE: ...] instead of being invented.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "docs" / "submission" / "final" / "assets"

TITLE = ("DBCAS – AI-Assisted Database Competency Assessment "
         "and Skill Gap Analysis")

TEAM = [
    ("Thu, Nguyen Ngoc Anh", "29209245799", "01258319907anhthu@gmail.com",
     "Project Manager, Scrum Master, Frontend Developer"),
    ("Nguyen, Nguyen Nhat", "26211227029", "nhnguyen240602@gmail.com",
     "Backend Developer, QA Tester"),
    ("Truong, Nguyen Quang", "29212730635", "quangtruongtt8@gmail.com",
     "Database Developer"),
    ("Do, Nguyen Quoc", "29211156881", "nguyenquocdodary@gmail.com",
     "Backend Developer"),
    ("Han, Nguyen Ngoc", "29204423268", "Hannguyenngoc0506@gmail.com",
     "Frontend Developer, QA Tester"),
]

REFERENCES = [
    'A. Silberschatz, H. F. Korth, and S. Sudarshan, Database System Concepts, '
    '7th ed. New York, NY, USA: McGraw-Hill Education, 2019. '
    '[Online]. Available: https://www.db-book.com/',
    'R. Ramakrishnan and J. Gehrke, Database Management Systems, 3rd ed. '
    'New York, NY, USA: McGraw-Hill, 2003. [Online]. '
    'Available: http://pages.cs.wisc.edu/~dbbook/',
    'ACM and IEEE Computer Society, "Computer Science Curricula 2013: '
    'Curriculum Guidelines for Undergraduate Degree Programs in Computer '
    'Science," ACM/IEEE Joint Task Force on Computing Curricula, Tech. Rep., '
    '2013. [Online]. '
    'Available: https://www.acm.org/education/curricula-recommendations',
    'W. Spady, Outcome-Based Education: Critical Issues and Answers. '
    'Arlington, VA, USA: American Association of School Administrators, 1994. '
    '[Online]. Available: https://files.eric.ed.gov/fulltext/ED380910.pdf',
    'J. Biggs and C. Tang, Teaching for Quality Learning at University: What '
    'the Student Does, 4th ed. Maidenhead, UK: Open University Press, 2011.',
    'P. Denny, J. Prather, B. A. Becker et al., "Computing Education in the '
    'Era of Generative AI," Communications of the ACM, vol. 67, no. 2, '
    'pp. 56–67, 2024, doi: 10.1145/3624720.',
    'J. Leinonen, P. Denny, S. MacNeil et al., "Comparing Code Explanations '
    'Created by Students and Large Language Models," in Proc. 2023 Conf. '
    'Innovation and Technology in Computer Science Education (ITiCSE \'23), '
    '2023, pp. 124–130, doi: 10.1145/3587102.3588785.',
    'H. Keuning, J. Jeuring, and B. Heeren, "A Systematic Literature Review '
    'of Automated Feedback Generation for Programming Exercises," ACM Trans. '
    'Computing Education, vol. 19, no. 1, pp. 1–43, 2018, '
    'doi: 10.1145/3231711.',
    'Google, "Gemini: A Family of Highly Capable Multimodal Models," arXiv '
    'preprint arXiv:2312.11805, 2023. [Online]. '
    'Available: https://arxiv.org/abs/2312.11805',
    'PostgreSQL Global Development Group, "PostgreSQL 17 Documentation: SQL '
    'Language and Server Administration," 2024. [Online]. '
    'Available: https://www.postgresql.org/docs/17/',
    'Docker Inc., "Docker Documentation: Resource Constraints and Container '
    'Security," 2024. [Online]. Available: https://docs.docker.com/engine/security/',
    'Meta Open Source, "React Documentation: Building Modern User '
    'Interfaces," 2024. [Online]. Available: https://react.dev/',
    'S. Ramírez and contributors, "FastAPI Documentation: High Performance Web '
    'Framework with Python," 2024. [Online]. '
    'Available: https://fastapi.tiangolo.com/',
    'LeetCode LLC, "LeetCode Database Problem Set and Automated Query '
    'Evaluation Engine," 2024. [Online]. '
    'Available: https://leetcode.com/problemset/database/',
]

BLOCKS = [
    ("h1", "1. Project Title"),
    ("p", TITLE),
    ("p", "Field of study: educational technology, database systems, software "
          "engineering and applied artificial intelligence. Academic "
          "affiliation: Capstone Project 1, team C1SE.70, International "
          "School, Duy Tan University. Timeline: 14/09/2026 – 26/12/2026 "
          "(Fall Semester 2026)."),
    ("p", "DBCAS is a web application that measures database competence one "
          "concept at a time. A course grade such as 7/10 tells a learner "
          "whether they passed, not which PostgreSQL concept they have not "
          "mastered: two learners with the same grade may fail on different "
          "topics. DBCAS links course learning outcomes to a concept model, "
          "serves multiple-choice, SQL and short-essay questions in an "
          "isolated sandbox, and reports a per-concept profile with a ranked "
          "list of the concepts to study next."),
    ("p", "The product is scoped to a local, reproducible deployment: one "
          "Docker Compose stack, PostgreSQL 17, a FastAPI backend with 106 "
          "documented API paths and a React 19 single-page frontend. It is an "
          "academic capstone deliverable, not a public service; no production "
          "URL is claimed."),

    ("h1", "2. Team Members"),
    ("p", "Team C1SE.70 consists of five software engineering students of the "
          "International School, Duy Tan University, working in two-week "
          "Scrum sprints with one named lead per workstream. The roster and "
          "contact addresses are the ones printed on the approved covers of "
          "the v1.2 documents."),
    ("table", {
        "caption": "Project team members and main roles",
        "header": ["Member", "Student ID", "Email", "Main role"],
        "widths": [4.0, 2.6, 4.6, 4.3],
        "font": 10,
        "rows": [[n, i, e, r] for n, i, e, r in TEAM],
    }),
    ("note", "Per-member effort allocation, personal handles and weekly hour "
             "commitments are not recorded in any project source. "
             "[OWNER TO PROVIDE: per-member effort allocation and handles]"),

    ("h1", "3. Supervisor(s)"),
    ("p", "The team is supervised by academic faculty of the International "
          "School, Duy Tan University. The supervisory arrangement is the one "
          "recorded in the v1.2 proposal and repeated in the project "
          "information block of every document."),
    ("table", {
        "caption": "Capstone project supervisor",
        "header": ["Name", "Title", "Faculty / department", "Institution",
                   "Email"],
        "widths": [3.4, 2.6, 3.6, 3.6, 2.3],
        "font": 10,
        "rows": [["Huynh Duc Viet", "MSc", "CSE Center",
                  "International School, Duy Tan University",
                  "huynhducviet@duytan.edu.vn"]],
    }),
    ("p", "MSc Huynh Duc Viet meets the team every two weeks to review sprint "
          "progress, architecture and grading rules, and to check alignment "
          "with the university curriculum. No industry co-supervisor is "
          "recorded: the v1.2 proposal states that an outside enterprise "
          "supervisor is not required for an on-campus educational project."),
    ("note", "The prose of the previous version called the unit “Software "
             "Engineering Department” while its table said “CSE Center”. The "
             "table value is kept. [OWNER TO PROVIDE: official faculty and "
             "department name, and whether a co-supervisor is required] "
             "[OWNER TO PROVIDE: review panel representative]"),

    ("h1", "4. Problem Statement"),
    ("p", "Four difficulties motivate DBCAS. They were identified from "
          "database textbooks and curriculum guidance [1], [2], [3], from the "
          "outcome-based assessment literature [4], [5], and from computing "
          "education research on feedback and generative AI [6], [7], [8]."),
    ("table", {
        "caption": "Difficulties, evidence and impact",
        "header": ["Difficulty", "Evidence", "Impact on learners and staff"],
        "widths": [4.0, 6.0, 5.5],
        "rows": [
            ["One grade hides per-concept strengths and weaknesses",
             "A single weighted mark is the only feedback most course "
             "assessments return [4], [5]",
             "Learners cannot tell which concept to revise; two learners with "
             "the same mark need different remediation"],
            ["Feedback says wrong, not why",
             "Automated feedback studies show that outcome-only feedback "
             "rarely changes the next attempt [8]",
             "The same mistake is repeated; instructors answer the same "
             "questions individually"],
            ["Manual grading of SQL and essays does not scale",
             "Hand-marking query logic and written answers is the bottleneck "
             "reported for large database classes [8]",
             "Slow turnaround, inconsistent rubrics between markers"],
            ["Practice tools check output, not competence",
             "Query-practice sites compare result sets and stop at "
             "accepted/rejected [14]",
             "No link from practice to course learning outcomes or to a study "
             "plan"],
        ],
    }),
    ("p", "The problem was chosen because all four difficulties are "
          "observable in the team's own database course, and because the "
          "curriculum already defines the missing link: course learning "
          "outcomes are expected to be assessed and reported separately "
          "[3], [4]. DBCAS therefore does not add another question bank; it "
          "adds the measurement layer between a question and a course "
          "outcome."),
    ("note", "The earlier version grounded this section in an informal "
             "review of Stack Overflow, Reddit and teaching blogs without "
             "naming a source. Those claims are replaced by the cited "
             "literature above. [OWNER TO PROVIDE: results of any local "
             "student survey, if one was conducted]"),

    ("h1", "5. Survey / Existing Solutions"),
    ("p", "Seven products are named in the project's own survey material: "
          "query-practice sites (LeetCode, HackerRank, SQLZoo, DataCamp), "
          "learning management systems (Moodle, Canvas, Blackboard), and "
          "general-purpose AI chatbots. Only LeetCode is documented in enough "
          "detail to compare feature by feature [14]; the other six are "
          "grouped, not individually assessed."),
    ("table", {
        "caption": "Existing solutions compared with DBCAS",
        "header": ["Criterion", "Query-practice sites [14]",
                   "Traditional LMS", "AI chatbots", "DBCAS"],
        "widths": [3.3, 3.1, 3.1, 3.0, 3.0],
        "font": 10,
        "rows": [
            ["Question formats", "SQL only",
             "MCQ; essays marked by hand", "Free-form chat",
             "MCQ, SQL and short essay"],
            ["Executes learner SQL", "Yes, vendor cloud", "No",
             "No database execution",
             "Yes, isolated PostgreSQL sandbox"],
            ["Per-concept profile", "No, problem count",
             "No, one overall grade", "No", "Yes, radar and bar by concept"],
            ["Gap diagnosis", "Failed test case only",
             "Instructor explains", "Free text only",
             "Ranked shortfall from a 70 % target"],
            ["Question selection", "Fixed problem sets", "Fixed exams",
             "Free-form chat",
             "Plan frozen at start from concepts, bands, count, source"],
            ["Course-outcome mapping", "Not supported", "Basic tagging",
             "Not supported", "CLO → concept → question"],
            ["Scoring consistency", "Exact output match", "Rules + manual essay",
             "Varies between prompts",
             "Deterministic rules; AI rubric with human verification"],
            ["Deployment", "Vendor cloud", "Institutional server",
             "External cloud", "Standalone Docker Compose stack"],
        ],
    }),
    ("p", "The difference is the unit of measurement. Practice sites "
          "optimise for solving many queries; an LMS optimises for storing "
          "course material and marks; a chatbot optimises for conversation. "
          "DBCAS keeps the practice loop but attaches every attempt to a "
          "concept and a course outcome, and publishes a result only after "
          "deterministic scoring or human verification (section 7)."),
    ("note", "Survey date, method and the sources used for HackerRank, "
             "SQLZoo, DataCamp, Moodle, Canvas and Blackboard are not recorded "
             "in any project file. [OWNER TO PROVIDE: surveyed competitors, "
             "survey date and one citation per product]"),

    ("h1", "6. Objectives and Scope"),
    ("h2", "6.1 SMART Objectives"),
    ("table", {
        "caption": "SMART breakdown of the project objective",
        "header": ["Letter", "Commitment", "Verification"],
        "widths": [2.2, 9.0, 4.3],
        "rows": [
            ["Specific", "Measure PostgreSQL competence per concept for the "
             "three question formats", "Concept-tagged attempts and a "
             "per-concept profile"],
            ["Measurable", "Every published result carries a score per "
             "concept and a ranked study list", "Profile API and UI "
             "reproduced from stored evidence"],
            ["Achievable", "Five two-week sprints with one named lead per "
             "workstream", "Sprint roadmap (section 11)"],
            ["Relevant", "Aligns assessment with course learning outcomes "
             "[3], [4]", "CLO → concept → question traceability"],
            ["Time-bound", "Feature freeze 06/12/2026, delivery 10–13/12/2026, "
             "defence 17–26/12/2026", "Official capstone calendar"],
        ],
    }),
    ("h2", "6.2 Project Scope"),
    ("p", "In scope:"),
    ("bullets", [
        "Account registration, sign-in, OAuth sign-in with Google and GitHub, "
        "password reset by email, and two roles (Learner, Administrator).",
        "Course learning outcomes, a PostgreSQL concept model with "
        "prerequisite edges, and administrator review of suggested mappings.",
        "A validated question bank with version families, concept tags, "
        "explanations and reference documentation, plus AI-generated "
        "candidates that pass validation before use.",
        "Practice sessions with a plan frozen before question one: concepts, "
        "difficulty bands (EASY 1–2, MEDIUM 3, HARD 4–5), question count, and "
        "source (bank or AI).",
        "SQL execution in an isolated container (read-only by default, "
        "opt-in writable demo with rollback), MCQ scoring and rubric-based "
        "essay scoring.",
        "Per-concept competency profile, gap diagnosis, ranked study list, "
        "administrator review queue and an official V1 result version.",
        "English and Vietnamese interfaces and question translations.",
    ]),
    ("p", "Out of scope:"),
    ("bullets", [
        "Public cloud deployment, marketing site and payment: the Free/Pro "
        "switch is a UI-only demo badge; no billing route or table exists.",
        "Long-term learning paths, adaptive curricula across semesters and "
        "retrieval-augmented generation over course documents at request "
        "time (course documents are ingested to ground question generation, "
        "not to answer learners).",
        "Mobile native applications, proctoring, plagiarism detection and "
        "institutional single sign-on.",
        "Trained or fine-tuned models: the AI features call an external "
        "OpenAI-compatible endpoint and keep no model weights.",
    ]),

    ("h1", "7. Key Features & Requirements"),
    ("h2", "7.1 Key Features"),
    ("table", {
        "caption": "Seven key features",
        "header": ["#", "Feature", "What it does"],
        "widths": [1.0, 4.2, 10.3],
        "rows": [
            ["F1", "Curriculum and concept model",
             "Administrators define course learning outcomes, concepts, "
             "prerequisite edges and suggested mappings"],
            ["F2", "Validated question bank",
             "Versioned MCQ, SQL and essay items with concept tags, "
             "explanations and documentation references"],
            ["F3", "Practice session with a frozen plan",
             "Concepts, bands, count and source are fixed before question "
             "one; the plan is spread across concepts without repeated "
             "version families"],
            ["F4", "Multi-format answering",
             "MCQ options, an embedded SQL editor and a short-essay editor "
             "with autosaved drafts"],
            ["F5", "Isolated SQL execution",
             "Read-only PostgreSQL sandbox by default, opt-in writable demo "
             "with rollback, bounded time and memory"],
            ["F6", "Grading and result versions",
             "Deterministic MCQ and SQL scoring, rubric essay scoring, human "
             "review queue and an official V1 result version"],
            ["F7", "Competency profile and study guidance",
             "Per-concept radar and bar profile from published evidence, gap "
             "diagnosis and a ranked “what to study next” list"],
        ],
    }),
    ("h2", "7.2 Functional Requirements"),
    ("table", {
        "caption": "Functional requirements",
        "header": ["ID", "Requirement"],
        "widths": [1.6, 13.9],
        "font": 10,
        "rows": [
            ["FR-01", "A visitor can register with name, email and password; "
             "passwords are stored only as a password hash."],
            ["FR-02", "A learner can sign in with email and password, Google "
             "or GitHub, and can request a password-reset link by email."],
            ["FR-03", "The system enforces two roles, Learner and "
             "Administrator; administrator accounts are provisioned by an "
             "administrator, and role changes are audited."],
            ["FR-04", "An administrator can create course learning outcomes "
             "and concepts, link them, define prerequisite edges and approve "
             "or reject suggested concept mappings."],
            ["FR-05", "An administrator can curate question-bank items with a "
             "version family, concept tags, difficulty 1–5, explanation and "
             "documentation references."],
            ["FR-06", "A learner starts a practice session by choosing "
             "concepts, difficulty bands, question count within the published "
             "limits, and question source (bank or AI)."],
            ["FR-07", "At start the system freezes the complete plan: exact "
             "count, per-format quotas, coverage of the selected concepts and "
             "no repeated version family; a bank shortage stops the start "
             "with an explicit error instead of shortening the session."],
            ["FR-08", "A session serves multiple-choice, SQL and short-essay "
             "questions, with a countdown and a 30-minute expiry."],
            ["FR-09", "A learner can run a SQL answer in an isolated "
             "PostgreSQL container that has no network, a statement timeout "
             "and a row limit."],
            ["FR-10", "When the writable demo profile is enabled, DML and DDL "
             "answers are executed and then rolled back, and the resulting "
             "table state is compared with the expected state."],
            ["FR-11", "Submitted answers are graded automatically: exact "
             "option matching for MCQ, result-set or table-state comparison "
             "for SQL, and rubric criteria for essays with an AI assist and a "
             "deterministic fallback."],
            ["FR-12", "Practice and legacy sessions enter an administrator "
             "review queue before publication; fixed-test sessions publish an "
             "AI-official V1 result at finalize."],
            ["FR-13", "An administrator can request a review, claim it, "
             "approve or reject it, trigger a regrade, and the queue expires "
             "stale claims."],
            ["FR-14", "A learner sees a per-concept competency profile, a gap "
             "diagnosis against the 70 % target and a ranked study list built "
             "only from published evidence."],
            ["FR-15", "When the AI source is selected, generated items are "
             "validated before entering a plan; if generation fails, bank "
             "items replace them and one notice explains the substitution."],
            ["FR-16", "Interface text is available in English and Vietnamese, "
             "and role, grade-edit and AI-stage events are auditable."],
        ],
    }),
    ("h2", "7.3 Non-Functional Requirements"),
    ("table", {
        "caption": "Non-functional requirements",
        "header": ["ID", "Quality attribute", "Requirement and verification"],
        "widths": [1.6, 3.4, 10.5],
        "font": 10,
        "rows": [
            ["NFR-01", "Security of secrets",
             "No credential in the tree or in Git history; `secrets:scan` "
             "reports zero findings."],
            ["NFR-02", "Sandbox isolation",
             "No network, 256 MB memory, one CPU, 128 PIDs, read-only root "
             "filesystem, non-root user; asserted by the container command."],
            ["NFR-03", "Determinism",
             "Identical answers produce identical scores; a repeated submit "
             "returns the stored summary instead of a second grade."],
            ["NFR-04", "Grading resilience",
             "A provider or sandbox failure leaves a durable job that is "
             "retried up to three times and then failed explicitly; no silent "
             "success."],
            ["NFR-05", "Data integrity",
             "122 foreign keys and 159 indexes across 67 tables; 28 forward "
             "migrations apply from an empty database."],
            ["NFR-06", "Privacy",
             "Only name, email and authentication identifiers are stored; no "
             "answer text leaves the deployment except the essay text sent "
             "for rubric assistance."],
            ["NFR-07", "Maintainability",
             "Backend correctness gate (ruff), frontend ESLint and Prettier, "
             "118 backend and 54 frontend test modules, all green in CI."],
            ["NFR-08", "Localization",
             "English and Vietnamese catalogues have the same 1 700 keys, "
             "zero drift."],
            ["NFR-09", "Usability",
             "Desktop and 390 px layouts reviewed; interactive contrast gate "
             "passes on the checked public pages."],
        ],
    }),

    ("h1", "8. Constraints and Assumptions"),
    ("table", {
        "caption": "Constraints and assumptions",
        "header": ["#", "Type", "Constraint or assumption", "Consequence"],
        "widths": [1.0, 2.8, 7.0, 4.7],
        "font": 10,
        "rows": [
            ["C1", "Technical", "Single Docker Compose stack on one host",
             "No horizontal scaling; concurrency bounded by two sandbox slots"],
            ["C2", "Technical", "Sandbox: 3 000 ms statement timeout, 45 s "
             "container lifetime, 1 000 rows, 16 KB SQL",
             "Long analytical queries are rejected by design"],
            ["C3", "Technical", "External OpenAI-compatible endpoint",
             "Latency, quota and model name are operator settings; output is "
             "validated before use"],
            ["C4", "Technical", "PostgreSQL 17 and Python 3.13 images",
             "Version pinned in the Dockerfile and Compose files"],
            ["C5", "Academic", "15-week capstone calendar, five sprints",
             "Scope frozen at the last sprint; no feature after freeze"],
            ["C6", "Academic", "No public URL is provisioned",
             "The demo runs locally; the documents name no public address"],
            ["C7", "Academic", "Human verification of AI-assisted grades",
             "Essay and AI-suggested items require administrator action"],
            ["C8", "Assumption", "Learners have a modern browser and a "
             "keyboard", "The SQL editor is desktop-first; mobile layout is "
             "supported for reading"],
            ["C9", "Assumption", "Course staff maintain the concept model",
             "An empty or stale concept model degrades selection quality"],
            ["C10", "Assumption", "The provider is reachable with a valid key",
             "Without it the AI source degrades to bank items, never to an "
             "error page"],
        ],
    }),

    ("h1", "9. Target Users / Stakeholders"),
    ("table", {
        "caption": "Stakeholders",
        "header": ["Stakeholder", "Background", "Need", "Value"],
        "widths": [2.8, 4.3, 4.4, 4.0],
        "font": 10,
        "rows": [
            ["Learner", "Undergraduate taking a relational database course",
             "Know which concept is weak and what to practise next",
             "Per-concept profile and ranked study list"],
            ["Administrator", "Lecturer or teaching assistant",
             "Curate items, supervise AI output, release results",
             "Question bank, review queue and audit trail"],
            ["Academic leader", "Course coordinator or programme head",
             "Evidence that assessment maps to course outcomes",
             "CLO → concept → question traceability and cohort view"],
            ["Capstone team", "Five software engineering students",
             "A defensible, reproducible deliverable",
             "Measured documents, test evidence and a runnable stack"],
        ],
    }),

    ("h1", "10. Technology Stack"),
    ("table", {
        "caption": "Technology stack",
        "header": ["Layer", "Technology", "Role"],
        "widths": [2.8, 6.0, 6.7],
        "rows": [
            ["Frontend", "React 19, Vite, Tailwind CSS 4, i18next, Chart.js",
             "Single-page interface, charts, English/Vietnamese catalogues"],
            ["Backend", "FastAPI on Python 3.13, SQLAlchemy, Pydantic",
             "106 REST paths, 118 operations, OpenAPI contract"],
            ["Database", "PostgreSQL 17",
             "67 tables, 561 columns, 122 foreign keys, 28 migrations"],
            ["SQL execution", "Docker, ephemeral PostgreSQL image, pglast",
             "Isolated statement execution and AST-based read-only policy"],
            ["AI/ML", "External OpenAI-compatible chat-completions endpoint",
             "Essay rubric assistance and question generation; no trained "
             "model, no training pipeline, no stored weights"],
            ["Background work", "In-process worker with database job leases",
             "Grading retries, AI stage runs, no external queue"],
            ["Testing", "pytest, Vitest, Playwright, custom Python gates",
             "118 backend and 54 frontend test modules, 28 browser specs"],
            ["Tools", "Git and GitHub Actions, Docker Compose, ruff, ESLint, "
             "Prettier", "Version control, CI, local stack, lint and format"],
        ],
    }),

    ("h1", "11. Methodology & Development Plan"),
    ("h2", "11.1 Agile Scrum"),
    ("p", "The team works in five two-week sprints on the official capstone "
          "calendar, preceded by a preparation phase from 28/07/2026. Each "
          "sprint starts with planning, runs three stand-ups per week, and "
          "ends with a review and a retrospective. Work is tracked as "
          "deliverables in the repository; one member is accountable per "
          "workstream (section 11.3). Two status reports and two faculty "
          "milestones fall inside the calendar."),
    ("h2", "11.2 Sprint Roadmap"),
    ("table", {
        "caption": "Capstone plan and sprint schedule",
        "header": ["Phase", "Dates", "Main tasks", "Lead"],
        "widths": [3.2, 3.4, 6.6, 2.3],
        "font": 10,
        "rows": [
            ["Preparation", "28/07 – 14/08/2026",
             "Team formed, repositories and workspace, initial research",
             "All (Thu)"],
            ["Advisor assignment", "10/08 – 16/08/2026",
             "Mentor assigned; scope and expectations agreed", "Mentor"],
            ["Proposal drafting", "17/08 – 23/08/2026",
             "Title, problem, literature, SMART objectives, diagrams",
             "Thu, Nguyen, Han"],
            ["Proposal submission", "24/08 – 05/09/2026",
             "Proposal v1.1 in Word and PDF; review slides", "All (Thu)"],
            ["Sprint 1 — architecture and data", "14/09 – 27/09/2026",
             "Git and Docker baseline, concept model, PostgreSQL schema",
             "Truong, Do, Nguyen"],
            ["Sprint 2 — identity and MCQ", "28/09 – 11/10/2026",
             "JWT and roles, MCQ scoring, SQL editor; status report 1 "
             "(03/10)", "Do, Nguyen, Thu"],
            ["Sprint 3 — sandbox and AI", "12/10 – 25/10/2026",
             "Sandbox limits and safety validation, rubric essay scoring, "
             "bank assembly; status report 2 (17/10)", "Do, Truong, Nguyen"],
            ["Midterm buffer", "26/10 – 31/10/2026",
             "Integration defects, demo rehearsal", "All (Thu)"],
            ["Midterm review", "01/11 – 07/11/2026",
             "End-to-end demo: MCQ, sandbox, essay scoring, architecture",
             "All (Thu)"],
            ["Sprint 4 — competency", "08/11 – 22/11/2026",
             "Scoring engine, radar dashboard, gap detection and ranked list; "
             "status report 3 (20/11)", "Do, Thu, Han"],
            ["Sprint 5 — plan and analytics", "23/11 – 06/12/2026",
             "Plan assembly, cohort API, integration testing; status report 4 "
             "(05/12)", "Do, Nguyen, Han"],
            ["Final delivery", "10/12 – 13/12/2026",
             "Performance and security checks, code freeze, documents, video",
             "All (Thu)"],
            ["Capstone defence", "17/12 – 26/12/2026",
             "Rehearsal, live demo, defence before the committee", "All (Thu)"],
        ],
    }),
    ("figure", str(ASSETS / "gantt-roadmap.png"),
     "Sprint roadmap and faculty milestones (same plan as the table above)",
     {"width_cm": 15.5}),
    ("h2", "11.3 Tasks by Role"),
    ("table", {
        "caption": "RACI matrix (A accountable, R responsible, C consulted, "
                   "I informed)",
        "header": ["Workstream", "Thu", "Nguyen", "Truong", "Do", "Han"],
        "widths": [7.5, 1.6, 1.6, 1.6, 1.6, 1.6],
        "font": 10,
        "rows": [
            ["Coordination, Scrum, backlog", "A/R", "C", "I", "I", "C"],
            ["Requirements and specifications", "A", "R", "C", "C", "R"],
            ["Database architecture and queries", "I", "C", "A/R", "C", "I"],
            ["Frontend and dashboards", "A/R", "I", "I", "C", "R"],
            ["SQL sandbox", "C", "R", "I", "A/R", "I"],
            ["Rubric grading and AI integration", "I", "R", "C", "A/R", "C"],
            ["Competency calculation", "C", "R", "C", "A/R", "C"],
            ["Question bank, rubrics, benchmark data", "I", "I", "A/R", "I", "R"],
            ["Testing and quality assurance", "C", "R", "C", "C", "A/R"],
            ["Report and presentation", "A/R", "R", "R", "R", "R"],
        ],
    }),
    ("note", "Story points, velocity and per-sprint meeting minutes are not "
             "recorded. [OWNER TO PROVIDE: velocity or story points, sprint "
             "review dates and attendance]"),

    ("h1", "12. System Architecture Overview"),
    ("p", "DBCAS has two human actors and three external systems. A learner "
          "practises and reviews results; an administrator curates the "
          "curriculum, the bank and the review queue. The external systems "
          "are the LLM provider used for rubric assistance and question "
          "generation, the OAuth identity providers, and the SMTP service "
          "used for password reset. The internal decomposition, the flow "
          "catalogue and the architectural decisions are specified in "
          "C1SE.70_ArchitectureDesign_DBCAS_ver1.3.docx; this section only "
          "summarises the context and the logical tiers."),
    ("figure", str(ASSETS / "context.png"),
     "System context: actors, system and external services"),
    ("p", "Logically the system is a four-tier application. The browser tier "
          "is a React single-page app that never talks to the database. The "
          "API tier is a FastAPI process that authenticates, authorises and "
          "orchestrates. The data tier is PostgreSQL 17, reached only through "
          "SQLAlchemy. The execution tier is a throw-away PostgreSQL "
          "container with no network, used only to run learner SQL; it is "
          "created per execution and removed on exit."),
    ("figure", str(ASSETS / "logical.png"),
     "Logical architecture: tiers, modules and external interfaces"),
    ("note", "Container, component, module and allocation views are in the "
             "Architecture Design document, section 4 and section 5."),

    ("h1", "13. Potential Risks and Mitigation"),
    ("p", "The risks below are the ones the team actually met while building "
          "and freezing the system; each mitigation is a control that exists "
          "in the repository, not a plan."),
    ("table", {
        "caption": "Risk register",
        "header": ["ID", "Risk", "Impact", "Mitigation and evidence"],
        "widths": [1.4, 4.3, 2.4, 7.4],
        "font": 10,
        "rows": [
            ["RSK-01", "Sandbox capacity: two concurrent slots; concurrent SQL "
             "can return sandbox_busy", "High",
             "Explicit 503-style error with retry guidance, slot diagnostics "
             "and admission logging; capacity remains an owner decision"],
            ["RSK-02", "Result heading slow to render on very large sessions",
             "Medium",
             "Bounded queries, job status logging with latency; the timeout "
             "remains an open owner issue"],
            ["RSK-03", "LLM latency, quota or outage", "High",
             "Validation before use, bank fallback with one substitution "
             "notice, durable retry job with three attempts"],
            ["RSK-04", "Cold seed takes about three minutes", "Medium",
             "Documented in the runbook; snapshot restore path for demos"],
            ["RSK-05", "Docker socket and GID differences on Windows hosts",
             "Medium", "Compose fallback documented in the README; no code "
             "change to the sandbox isolation"],
            ["RSK-06", "AI-generated questions may be wrong or duplicated",
             "High", "Three validation layers, fingerprint duplicate check, "
             "and an administrator review queue before publication"],
            ["RSK-07", "Provider data-retention terms are not approved for "
             "learner data", "High",
             "Production stays on hold; no real learner data is sent"],
        ],
    }),

    ("h1", "14. Expected Outcomes / Deliverables"),
    ("p", "Final documentation is submitted between 10/12/2026 and "
          "13/12/2026 and defended between 17/12/2026 and 26/12/2026, per the "
          "official calendar in section 11.2."),
    ("table", {
        "caption": "Deliverables",
        "header": ["#", "Deliverable", "Format", "Evidence of completion"],
        "widths": [1.0, 4.6, 3.0, 6.9],
        "font": 10,
        "rows": [
            ["D1", "Proposal document", "DOCX and PDF",
             "This document, ver1.3"],
            ["D2", "Architecture design document", "DOCX and PDF",
             "C1SE.70_ArchitectureDesign_DBCAS_ver1.3.docx"],
            ["D3", "Database design document", "DOCX and PDF",
             "C1SE.70_DatabaseDesign_DBCAS_ver1.3.docx"],
            ["D4", "Code standards document", "DOCX and PDF",
             "C1SE.70_CodeStandards_DBCAS_ver1.3.docx"],
            ["D5", "Technical report", "DOCX and PDF",
             "C1SE.70_TechnicalReport_DBCAS_ver1.3.docx"],
            ["D6", "Source code and runbook", "Git repository and "
             "SOURCE_CODE.md", "Tests, gates and CI evidence in the "
             "repository"],
        ],
    }),
    ("p", "A working system is demonstrated locally with one command. No "
          "public deployment URL exists, so none is claimed: the published "
          "address is deliberately out of scope (constraint C6)."),

    ("h1", "15. References"),
    ("p", "References follow IEEE style and are cited in the text above."),
]
for index, ref in enumerate(REFERENCES, 1):
    BLOCKS.append(("ref", f"[{index}] {ref}"))
