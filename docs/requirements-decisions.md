# Owner-approved requirement decisions

## 15 October supervisor feedback — implemented 18 October 2026

Learner-selected skills/difficulty reuse existing concepts and levels 1–5.
EASY maps to 1–2, MEDIUM to 3 and HARD to 4–5. Formal assessments retain the
60-minute 10MCQ/2SQL/1Essay contract. Explicit short Topic practice uses an exact
requested length and the approved formats available for the selected topic;
the existing bank has no single-concept pool satisfying the full formal mix
at one band. No unverified classifications or generated questions are added.
Result release is assessment-configurable, human grading uses Administrator
authorization, and cumulative competency pools only published evidence.
See the [implementation, audit matrix and verification](supervisor-implementation.md).

## 15 October 2026 — future PostgreSQL Foundations coverage

The owner selected the current formal contract for future assessments:
60 minutes, 10 MCQ, two SQL, one Essay. Published assessment 2 retains its
historical 30-minute/4MCQ/2SQL/2Essay configuration and original targets.
The distinct current template uses PG-SELECT-LIST, PG-JOIN-TYPES and IDX,
with the same 40/30/30 targets and difficulty 1–3. Existing bank questions,
including IDX successor 450, provide sufficient coverage; no additional
questions or development publications were needed. See
[the full audit](pg-m089-assessment-2-reconciliation.md).

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
