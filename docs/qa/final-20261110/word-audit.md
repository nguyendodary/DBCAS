# Final Word/project audit — 2026-11-10

The three official v1.2 Word documents were audited against the final
`develop2` project. Their existing English edits remain in place; this
continuation found no factual change requiring another Word edit. Names,
dates, signatures, formatting and approved diagrams were preserved.

| Document | SHA-256 of the unchanged v1.2 package | Word open/fields |
| --- | --- | --- |
| Proposal | `16b07a2c9bd77b440249ac2123ac172202144eb45553351c898c02172dc000b3` | PASS |
| Architecture Design | `de733fb117ec968afcb76c030d631b35dfa6995c6bf2d09511a0dce4b6662b10` | PASS |
| Database Design | `f16ba032106385eabe717566d2e5837ef94baa11c93c8026ce991bfc726123a8` | PASS |

`npm run docs:verify-word -- --no-pdf` used **Word COM 16.0** locally:
**3/3 PASS**, zero unexplained format differences, run issues, new Vietnamese
words, diagram-layout differences or data mismatches. All three opened and
updated fields on temporary copies; source SHA-256 hashes stayed unchanged.
A separate full body-paragraph scan found **0 Vietnamese paragraphs in each
document**, and all ZIP/XML packages parsed successfully.

| Project surface | Evidence and result |
| --- | --- |
| Application schema | Canonical gate: **41 tables / 293 columns / 59 FKs / 87 indexes / 19 migrations**. Live isolated PostgreSQL introspection agrees on 41/293/59 and 19 applied migrations. The operational `schema_migration` adds one table/three columns when counted separately. |
| Compose/runtime | Six local service definitions; seven including optional QA provider. Four long-running services are healthy; initializer and executor-image jobs exit normally. PostgreSQL/sandbox version is 17. |
| API/routes | Inventory/OpenAPI gates: **82 paths / 92 operations / 23 frontend routes**. Final visual/auth fixes add no route or API. |
| AI pipeline | Finished attempt snapshots → one pure Prompt Builder output → exact Evaluator input. The unchanged 141-test purity/hash/fallback group is included in green backend **1455/1455** at `9f3cd92`. Builder does not grade. |
| Result flows | Every new practice attempt requires preliminary evaluation, administrator review, reason-bearing score edits when needed and approval. Pending scores stay hidden and excluded from published analytics. Existing Word paragraphs explicitly describe the mandatory workflow. |
| Current UI | Font, responsive layout, light surfaces and auth-error fixes change presentation/feedback only; no architecture element changed. |

`npm run docs:check` passed: **46 schema/project assertions**, **41 Word
content assertions** and **10 diagram gates**, including their negative
broken-input checks. The current generated Word reports are indexed in
[the verification summary](../word-verification/summary.md).

No architecture element changed, so **no diagram was rebuilt or inserted and
no owner diagram approval is pending**. The approved figure sources, layout
and embeddings remain untouched. The latest local audit used `--no-pdf`;
fresh PDF/page rendering was not repeated for unchanged packages. Prior
visual/page evidence remains in the
[November 9 reports](https://github.com/nguyendodary/DBCAS/tree/3ae57be/docs/qa/word-verification)
and the retained figure contact sheets. Current reports correctly mark that
PDF step skipped instead of claiming a new render.

Final verification logs and the full-hash/paragraph scan are retained locally
under `_review/finish-20261110/`. Real-model output quality is a separate
unverified limitation in the [request ledger](live-request-ledger.json);
the Word audit does not claim a successful live model evaluation.
