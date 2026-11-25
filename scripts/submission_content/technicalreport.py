# -*- coding: utf-8 -*-
"""Technical Report content: a scientific-style account of DBCAS.

Measured values are re-checked by scripts/verify_submission_docs.py; the
experiment table cites the command or log that produced each number.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "docs" / "submission" / "final" / "assets"

BLOCKS = [
    ("h1", "Abstract"),
    ("p", "Database courses still assess a term with a single weighted mark, "
          "which cannot say which concept a learner has not mastered. This "
          "report presents DBCAS, a practice and assessment system that "
          "measures PostgreSQL competence per concept across three answer "
          "formats: multiple-choice questions, SQL executed in an isolated "
          "sandbox, and short rubric-graded essays. The system freezes a "
          "practice plan before the first question, grades deterministically "
          "where possible, uses an external language model only behind "
          "validation and a deterministic fallback, and publishes a result "
          "only from stored evidence. We describe the design, the "
          "implementation and a set of reproducible experiments: a "
          "67-table schema with 122 foreign keys and 28 forward migrations, "
          "an API of 106 paths and 118 operations, 1 940 passing backend "
          "tests, 463 frontend tests and 152 browser tests across nine CI "
          "shards, and zero secret-scan findings across the whole tree. The "
          "contribution is not a new model but an evidence discipline: every "
          "reported number is traceable to a stored attempt, a question "
          "version and a concept, and every figure in this report was "
          "re-measured from the repository. Limitations are stated: there is "
          "no controlled user study, no public deployment, and the sandbox "
          "admits two concurrent SQL executions."),

    ("h1", "1. Introduction"),
    ("p", "Assessment in database education has two problems that compound. "
          "The first is resolution: a single mark aggregates heterogeneous "
          "skills, so a learner who writes correct joins but cannot normalise "
          "a schema and a learner with the opposite profile receive the same "
          "grade [4], [5]. The second is feedback latency and consistency: "
          "grading SQL and written answers by hand is slow, and two markers "
          "may apply a rubric differently [8]. Practice sites address volume "
          "but stop at accepted or rejected output [14]; learning management "
          "systems store material and marks but cannot execute a query "
          "safely; general-purpose chatbots converse but do not preserve a "
          "measurement."),
    ("p", "DBCAS starts from the curriculum rather than from the question "
          "bank. Course learning outcomes are mapped to concepts, concepts "
          "carry prerequisite edges, and questions are tagged to concepts. A "
          "practice session fixes its concepts, difficulty bands, length and "
          "source before the first question, so the session is reproducible. "
          "Each attempt produces evidence; the profile is computed from "
          "published evidence only. The research question of the project is "
          "therefore engineering-oriented: can a small team build an "
          "assessment pipeline whose numbers are reproducible, whose AI use "
          "is auditable, and whose failures are explicit?"),
    ("p", "The report is organised as follows. Section 2 positions the work "
          "against related research and tools. Section 3 states the method: "
          "requirements, architecture and the measurement protocol. Section 4 "
          "describes the implementation. Section 5 reports experiments with "
          "the command or log behind every number. Section 6 discusses "
          "validity and limitations, and section 7 concludes."),

    ("h1", "2. Related Work"),
    ("p", "Four strands inform the design."),
    ("p", "Outcome-based assessment. Spady argues that instruction should be "
          "organised around explicit outcomes and that assessment should "
          "report progress toward them [4]; Biggs and Tang make the same point "
          "as constructive alignment between intended learning outcomes, "
          "activities and assessment [5]. DBCAS implements the alignment "
          "literally as a three-level mapping from course outcome to concept "
          "to question, and reports at the concept level rather than the "
          "course level."),
    ("p", "Automated feedback. Keuning, Jeuring and Heeren review automated "
          "feedback for programming exercises and show that feedback which "
          "explains the error is more useful than a pass/fail verdict [8]. "
          "DBCAS therefore stores an explanation and documentation reference "
          "with every validated question, and its SQL grading reports the "
          "first diverging table or column rather than a boolean."),
    ("p", "Generative AI in computing education. Denny et al. describe both "
          "the opportunities and the risks of generative models in computing "
          "education [6], and Leinonen et al. compare explanations written by "
          "students and by models [7]. Both motivate a design in which the "
          "model assists a rubric but does not own the score. DBCAS validates "
          "model output against a schema and a domain contract, keeps a "
          "deterministic rubric as the fallback, and records which path "
          "produced the grade."),
    ("p", "Practice tools and database systems. Query-practice sites provide "
          "large problem sets and exact-output judging but no course-outcome "
          "mapping and no explanation of a wrong answer beyond the failing "
          "case [14]. The database literature that defines the concepts being "
          "measured is the standard textbook material [1], [2], and the "
          "curriculum guidance that defines expected competence is the "
          "ACM/IEEE computer science curricula [3]. The execution environment "
          "follows PostgreSQL 17 documentation [10] and Docker isolation "
          "guidance [11]."),

    ("h1", "3. Method"),
    ("h2", "3.1 Requirements and Scope"),
    ("p", "The requirements were derived from the curriculum mapping and from "
          "the failure modes of the alternatives: per-concept reporting, "
          "three answer formats, a frozen plan, explicit publication states, "
          "auditability, and a sandbox that cannot reach the application "
          "database. The system is a single-institution deployment; "
          "multi-tenancy, payment, proctoring and trained models are out of "
          "scope."),
    ("h2", "3.2 Architecture"),
    ("p", "DBCAS is a four-tier modular monolith: a React single-page "
          "frontend, a FastAPI application that also hosts a bounded worker, "
          "PostgreSQL 17, and an ephemeral PostgreSQL container created per "
          "SQL execution. The application is layered into routers, services "
          "and repository classes; transactions and locks live in services "
          "and repositories. The Architecture Design document specifies the "
          "views, the flows and the decisions; this report uses them without "
          "reproducing them."),
    ("figure", str(ASSETS / "pipeline.png"),
     "The evaluation pipeline: deterministic prompt assembly, provider call, "
     "validation, fallback and evidence publication"),
    ("h2", "3.3 Measurement Protocol"),
    ("p", "Every quantity in this report is produced by a command that reads "
          "the repository or the running system, and every command is "
          "recorded with its output in a log file. Schema facts come from "
          "PostgreSQL 17.12 introspection after all migrations, not from "
          "reading DDL. API facts come from the OpenAPI document generated by "
          "the application. Test facts come from running the suites. Secret "
          "facts come from the scanner. Document facts come from the final "
          "DOCX packages. No number in this report is estimated, rounded from "
          "memory, or copied from an earlier document; where a value could "
          "not be measured it is marked as an open item instead."),

    ("h1", "4. Implementation"),
    ("h2", "4.1 Data Model"),
    ("p", "The schema has 67 application tables and 561 columns, 122 foreign "
          "keys and 159 indexes, built by 28 forward-only migrations. History "
          "is carried by dedicated tables rather than by mutating rows: "
          "result versions, per-criterion score snapshots, rubric profiles, "
          "AI stage runs and append-only audit tables, protected by 41 "
          "triggers. The migration runner stores the SHA-256 of every applied "
          "file and refuses to continue if a file changed, so an applied "
          "migration is immutable."),
    ("h2", "4.2 Practice and Grading"),
    ("p", "A session plan is assembled from the validated bank, optionally "
          "with generated and validated items, and frozen with its "
          "configuration snapshot. Selection is deterministic: the opening "
          "three questions are basic multiple-choice items covering unseen "
          "concepts, the fourth question is biased by the opening result, and "
          "later questions follow quota pressure, weakest-concept selection "
          "and one-step difficulty adjustment, with every tie broken by the "
          "question identifier. MCQ is graded by exact option matching; SQL "
          "by comparing a normalised result grid or the captured table state "
          "after a data-manipulation task; essays by rubric criteria, with "
          "the provider assisting and a deterministic rubric as fallback. A "
          "repeated submission with the same answer hash returns the stored "
          "result instead of grading twice."),
    ("h2", "4.3 Isolation"),
    ("p", "Learner SQL runs in a container with no network, 256 MB of memory "
          "without swap, one CPU, 128 PIDs, a read-only root filesystem, a "
          "non-root user, all capabilities dropped and no-new-privileges, "
          "with a 45-second container lifetime and a 3 000 ms statement "
          "timeout. The statement policy parses the script and rejects any "
          "construct outside an allowlist; a read-only database role provides "
          "a second, independent barrier. Two executions may run at once, and "
          "the third waits or is rejected with an explicit busy error."),
    ("h2", "4.4 Audit and Publication"),
    ("p", "Two publication paths exist. A fixed-test session publishes an "
          "official V1 result inside the finalize transaction, with a "
          "result hash and per-question scores. A practice or legacy session "
          "stays pending until an administrator reviews it; a learner may "
          "request a review inside seven days, an administrator claims it "
          "with a 30-minute lease and either rejects or regrades it, and a "
          "deviation above 30 % needs a second confirmation. The worker "
          "never decides on the learner's behalf. Every transition is "
          "recorded, and the learner's cumulative profile is recomputed from "
          "published evidence only."),

    ("h1", "5. Experiments"),
    ("p", "The experiments are reproducibility checks rather than a user "
          "study. Each row states what was measured, the measured value and "
          "the command or log that produced it. All values were re-measured "
          "for this report."),
    ("table", {
        "caption": "Measured results",
        "header": ["ID", "Measurement", "Result", "Evidence"],
        "widths": [1.1, 4.4, 5.2, 4.8],
        "font": 9,
        "rows": [
            ["E1", "Schema objects after all migrations",
             "67 tables, 561 columns, 122 foreign keys, 159 indexes",
             "schema introspection + docs:check"],
            ["E2", "Forward migrations applied",
             "28 files, latest 028, checksum-verified",
             "schema_migration ledger"],
            ["E3", "API contract",
             "106 paths, 118 operations (51 POST, 50 GET, 7 PUT, 5 PATCH, "
             "5 DELETE)", "app.openapi() and OpenAPI check"],
            ["E4", "Backend test suite",
             "1 940 passed, 7 skipped", "pytest -q, backend/"],
            ["E5", "Frontend unit suite", "54 files, 463 tests passed",
             "vitest run"],
            ["E6", "Browser suites",
             "11 localization + 72 end-to-end + 12 practice + 3 smoke + 54 QA "
             "= 152 passed, 4 skipped", "Playwright and QA logs"],
            ["E7", "CI jobs on the frozen commit",
             "14 of 14 successful", "workflow run 45597486074"],
            ["E8", "Secret scan",
             "Whole tree, 0 findings; 1 042 commits, 0 matching real keys",
             "secrets:scan and history scan"],
            ["E9", "Frontend contrast pairs", "186 pairs, 0 failures",
             "npm run ui:contrast"],
            ["E10", "Document set built from one generator",
             "5 documents, every figure re-measured, XML layout checked",
             "build_submission_docs + verify_submission_docs"],
            ["E11", "Cold demo seed", "about three minutes",
             "seed diagnostics log"],
        ],
    }),
    ("h2", "5.1 What the Numbers Show"),
    ("p", "Three observations follow. First, the test surface is large "
          "relative to the application: 1 940 backend tests and 463 frontend "
          "tests cover 28 567 lines of backend code and 32 434 lines of "
          "frontend code. Second, the browser suites are sharded by "
          "configuration rather than by retry: nine shards run disjoint "
          "specifications and a fan-in job requires exactly nine success "
          "reports, which removes the incentive to make a flaky test pass by "
          "rerunning it. Third, the schema is intentionally conservative: "
          "122 foreign keys and 41 triggers exist so that a wrong update "
          "fails in the database rather than in a report."),
    ("h2", "5.2 Reproducibility"),
    ("p", "A clean clone reproduces the numbers with the documented commands: "
          "the schema from db/schema.sql plus 28 migrations, the API contract "
          "from the application, the tests from the suites, and the documents "
          "from one generator that reads the same facts. The document "
          "generator refuses to guess: anything the repository cannot prove "
          "is emitted as an explicit owner field rather than a plausible "
          "value."),

    ("h1", "6. Discussion and Limitations"),
    ("p", "Internal validity. The measurements are exact counts of artefacts, "
          "not estimates, and the scripts that produce them are committed. "
          "The main internal risk is drift between the documents and the "
          "code; it is mitigated by a verification script that re-reads the "
          "DOCX and compares every number with the measured value, and by a "
          "documentation gate in CI."),
    ("p", "External validity. DBCAS was evaluated on one PostgreSQL concept "
          "model, one institution and two roles. The corpus contains 446 "
          "questions over 98 concepts and 12 course learning outcomes, which "
          "is enough to demonstrate the pipeline but not enough to claim "
          "learning gains. No controlled study with learners was run, so this "
          "report makes no claim about learning outcomes."),
    ("p", "Construct validity. Concept scores are computed from question "
          "scores; a question that is tagged to the wrong concept would "
          "distort the profile. The system mitigates this with confirmed tags "
          "and an administrator review of suggested mappings, but the "
          "tagging itself is not independently validated."),
    ("p", "Reliability. Deterministic grading is reproducible by "
          "construction. The model-assisted path is not: the same essay may "
          "receive a slightly different rubric comment, which is why the "
          "fallback exists and why AI-assisted grades require verification "
          "in the practice flow. Provider availability, latency and retention "
          "terms are operational risks and are recorded as such; production "
          "release remains on hold until the retention question is decided."),
    ("p", "Capacity. The sandbox admits two concurrent executions. A third "
          "request waits five seconds and then fails with an explicit busy "
          "error. This is adequate for a demonstration and for a small "
          "class, not for a faculty-wide deployment; horizontal scaling would "
          "require a broker, which is designed but not enabled by default."),
    ("p", "Threats to the document set itself. The documents are generated, "
          "so a fact that no script checks could still be wrong. The "
          "mitigation is coverage: schema, API, test, secret, route and "
          "document facts are machine-checked; owner facts such as student "
          "identities or approval dates are not derivable from code and are "
          "marked for the owner instead of being asserted."),

    ("h1", "7. Conclusion"),
    ("p", "DBCAS shows that a small team can build an assessment system whose "
          "claims are reproducible. The design separates what is measured "
          "(attempts, question versions, concept tags), what is computed "
          "(scores, profiles, gaps) and what is decided (publication, review), "
          "and it makes every failure explicit: a bank shortage stops a "
          "session, a provider outage falls back to a deterministic rubric, a "
          "sandbox refusal is a named error, and a retried submission returns "
          "the stored result. The measured evidence - 67 tables, 106 API "
          "paths, 1 940 backend tests, 152 browser tests, 14 green CI jobs and "
          "zero secret findings - describes a system that is small in scope "
          "and strict in evidence. Future work is a controlled study with "
          "learners, a wider concept corpus, and a brokered sandbox that "
          "raises capacity without weakening isolation."),

    ("h1", "References"),
]
REFERENCES = [
    'A. Silberschatz, H. F. Korth, and S. Sudarshan, Database System Concepts, '
    '7th ed. New York, NY, USA: McGraw-Hill Education, 2019.',
    'R. Ramakrishnan and J. Gehrke, Database Management Systems, 3rd ed. '
    'New York, NY, USA: McGraw-Hill, 2003.',
    'ACM and IEEE Computer Society, "Computer Science Curricula 2013: '
    'Curriculum Guidelines for Undergraduate Degree Programs in Computer '
    'Science," ACM/IEEE Joint Task Force on Computing Curricula, Tech. Rep., '
    '2013.',
    'W. Spady, Outcome-Based Education: Critical Issues and Answers. '
    'Arlington, VA, USA: American Association of School Administrators, 1994.',
    'J. Biggs and C. Tang, Teaching for Quality Learning at University: What '
    'the Student Does, 4th ed. Maidenhead, UK: Open University Press, 2011.',
    'P. Denny, J. Prather, B. A. Becker et al., "Computing Education in the '
    'Era of Generative AI," Communications of the ACM, vol. 67, no. 2, '
    'pp. 56–67, 2024, doi: 10.1145/3624720.',
    'J. Leinonen, P. Denny, S. MacNeil et al., "Comparing Code Explanations '
    'Created by Students and Large Language Models," in Proc. ITiCSE \'23, '
    '2023, pp. 124–130, doi: 10.1145/3587102.3588785.',
    'H. Keuning, J. Jeuring, and B. Heeren, "A Systematic Literature Review '
    'of Automated Feedback Generation for Programming Exercises," ACM Trans. '
    'Computing Education, vol. 19, no. 1, pp. 1–43, 2018, '
    'doi: 10.1145/3231711.',
    'Google, "Gemini: A Family of Highly Capable Multimodal Models," arXiv '
    'preprint arXiv:2312.11805, 2023.',
    'PostgreSQL Global Development Group, "PostgreSQL 17 Documentation," '
    '2024. [Online]. Available: https://www.postgresql.org/docs/17/',
    'Docker Inc., "Docker Documentation: Resource Constraints and Container '
    'Security," 2024. [Online]. '
    'Available: https://docs.docker.com/engine/security/',
    'Meta Open Source, "React Documentation," 2024. [Online]. '
    'Available: https://react.dev/',
    'S. Ramírez and contributors, "FastAPI Documentation," 2024. [Online]. '
    'Available: https://fastapi.tiangolo.com/',
    'LeetCode LLC, "LeetCode Database Problem Set and Automated Query '
    'Evaluation Engine," 2024. [Online]. '
    'Available: https://leetcode.com/problemset/database/',
]
for _index, _ref in enumerate(REFERENCES, 1):
    BLOCKS.append(("ref", f"[{_index}] {_ref}"))
