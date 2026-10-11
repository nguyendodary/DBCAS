# Owner-approved requirement decisions

## 11 October 2026 — learner DML/DDL scope

Proposal1.4 §6.2 includes practical DML/DDL. Architecture1.2 UC13/QA03 and
User Story Learner4 require read-only learner execution and rollback.
The owner explicitly selected:

> Keep SQL execution read-only; assess DML/DDL knowledge through MCQ and essay

This decision resolves the release scope; it does not rewrite the original
documents or weaken sandbox boundaries. Learner SQL execution accepts SELECT
only. DML/DDL commands can appear as conceptual MCQ/essay content and grading
criteria, but are never executed by those answer formats.

`db/sql_knowledge_pack.json` provides two knowledge concepts, two MCQs and a
four-level essay plus a separately titled formal assessment. It supplements
the core benchmark and preserves its existing targets and historical sessions.
The knowledge assessment uses the formal 60-minute/10MCQ/2SQL/1essay mix.
Its reviewed target subset yields ten eligible MCQs, including both knowledge
topics; the original complete twelve-topic benchmark remains separate.
Executable SQL questions come from the reviewed SELECT bank.

After reviewing the content, add it with the existing Administrator:

```powershell
cd backend
.venv/Scripts/python.exe -m app.benchmark --admin-email admin@dbcas.local --fill-missing-techniques --include-sql-knowledge
```

This import is additive and repeatable. It never creates learner records,
overwrites assessment targets or enables learner mutations. The real-PostgreSQL
bank regression checks repeatability, formal activation, preserved original
targets and that all executed learner reference queries remain SELECT.
