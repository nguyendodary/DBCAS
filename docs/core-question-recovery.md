# Core question recovery and separate rubric repair

## Evidence and identity

On 2026-10-15, all-ref pack/seed history, migration/test fixtures, refs and
unreachable objects were searched before the development database was read.
No exact canonical definitions were found in repository history. The existing
database supplied four validated records, corroborated by 18 immutable attempt
snapshots. No development database writes were made.

| Existing ID | Source key | Type | Concept | Snapshots |
| --- | --- | --- | --- | --- |
| 2 | legacy-mcq-select-filter | MCQ | SELECT | 7 |
| 3 | legacy-mcq-inner-join | MCQ | JOIN | 5 |
| 4 | legacy-sql-customer-names | SQL | SELECT | 4 |
| 5 | legacy-essay-index-read-write | Essay | IDX | 2 |

Commit `6233e7c` restores the exact canonical question content, answer keys,
rubric, points, difficulty and SQL fixtures plus Vietnamese display content.
The importer matches existing validated content without assigning replacement
IDs. Fresh databases allocate their own surrogate IDs; source keys identify
the same logical records. The bank contains 441 questions, not 882.

## Rubric repair prepared for owner review

The owner requested a separately reviewable repair after the recovered rubric
failed the existing four-band validator. Pack 1.2 changes only this Essay's
rubric and its Vietnamese presentation. The original is retained in the
recovery commit. This source change has not been applied to the development
database. Existing imports deliberately conflict on the old rubric by default.
The separately reviewable `--repair-legacy-index-rubric` import option accepts
only the exact known historical question/rubric and otherwise identical source
fields. It requires every existing attempt to have a rubric snapshot, replaces
only the current rubric, increments the content version once, and imports the
new VI presentation under the same question ID. Reimport is idempotent. No
snapshots, answers or scores are updated. Attempts without snapshots cause a
clear rejection. Do not delete/recreate the question or overwrite evidence.

After owner review, this reproducible upgrade can accompany the ordinary import:

```text
python -m app.benchmark --admin-email <existing-administrator> --fill-missing-techniques --include-sql-knowledge --include-postgres-knowledge --repair-legacy-index-rubric
```

This command is documented for a later approved deployment; it was tested only
against disposable databases during this task.

| Historical band | Historical scores | Proposed band | Proposed scores |
| --- | --- | --- | --- |
| Missing | 0 | Incomplete | 0–0.99 |
| Partial | 1–3 | Partial | 1–3 |
| No band | 3.01–3.99 | Mostly Complete | 3.01–3.99 |
| Complete | 4–5 | Complete | 4–5 |

Incomplete means no relevant explanation of lookup benefit or write cost.
Partial retains the original criterion: mentions lookup benefit OR write cost.
Mostly Complete explains both effects but does not fully explain B-tree lookup
cost or write amplification. Complete retains the original criterion: covers
B-tree lookup cost and write amplification.

This is a scoring-semantic change: previously undefined fractional scores gain
bands, the zero-score label changes, and an intermediate criterion is added.
Maximum points (5), difficulty (3), concept (IDX), prompt, assessment targets
and existing integer-score Partial/Complete ranges stay unchanged.
The grader continues to consume canonical English criteria and its existing
four-band contract; Vietnamese text is display-only. No live provider call is
needed to validate this repair.
