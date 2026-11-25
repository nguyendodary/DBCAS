# Proposal — required 15-section check (ver1.3)

Audited against `C1SE.70_ProposalDocument_DBCAS_ver1.3.docx`. The document
already carried the fifteen sections in the required order before this pass; the
table records the state found and what was fixed. The section order is asserted
mechanically by `scripts/verify_submission_docs.py`.

| # | Section | State found | Fix applied |
|---:|---|---|---|
| 1 | Project Title (under 15 words) | Present — 9 words | Kept; metadata lines shortened |
| 2 | Team Members (name, ID, email, role) | Present | Rebuilt as a four-column table; phone numbers dropped as not required; effort-allocation gap marked for the owner |
| 3 | Supervisor(s) (name, faculty/department, email, industry co-supervisor) | Present — department contradictory | Table keeps `CSE Center`; email kept; the prose/table conflict and a possible co-supervisor are explicit owner fields |
| 4 | Problem Statement (difficulties, impact, why chosen) | Present — unsourced web research | Replaced with cited literature [1]–[8]; difficulties table now names evidence and impact |
| 5 | Survey / Existing Solutions (comparison, differences) | Present — no citations, only LeetCode documented | Comparison table kept and condensed; LeetCode cited [14]; the six undocumented products are listed as an owner question |
| 6 | Objectives and Scope (SMART; in/out) | Present — implemented feature inside an exclusion bullet | SMART table kept; scope split into in-scope and out-of-scope lists; document-ingestion grounding moved into scope |
| 7 | Key Features & Requirements (5–7 features, FR, NFR) | Present — `FR01` vs `FR-01`, compound `FR-06` | Seven features kept; IDs normalised to `FR-01`…`FR-16` and `NFR-01`…`NFR-09`; compound requirement split |
| 8 | Constraints and Assumptions | Present | Split into ten numbered constraints C1–C10 with consequences |
| 9 | Target Users / Stakeholders | Present | Kept as a four-row stakeholder table |
| 10 | Technology Stack (frontend, backend, database, AI/ML, tools) | Present — no AI/ML or testing row | Added an explicit AI/ML row (external endpoint, no trained model) and a testing row |
| 11 | Methodology & Development Plan (model, plan, tasks by role) | Present — Gantt omitted the buffer week | Sprint table rebuilt with the buffer week and status-report dates; the real roadmap figure is reused; RACI kept; velocity gap marked for the owner |
| 12 | System Architecture Overview (context, logical) | Present | Kept both diagrams; text reduced to a summary with cross-references to the Architecture Design document |
| 13 | Potential Risks and Mitigation | Present — mitigation contradicted the writable demo | Risk table rebuilt from the seven real risks, with the writable-demo control stated |
| 14 | Expected Outcomes / Deliverables | Present — `OWNER UNKNOWN` shipped as content | Replaced with the local-demo statement and a deliverables table that matches the five documents |
| 15 | References (IEEE) | Present — 14 entries, zero in-text citations | Citations added throughout; IEEE formatting completed with DOIs; the FastAPI entry corrected |

Result: **15 of 15 sections present and in order; 0 missing; 10 corrected.**
The only content that is not verifiable from the repository is written as
`[OWNER TO PROVIDE: ...]` and listed in
[doc-verify.md section 8](../../agent/freeze-logs/doc-verify.md#8-owner-questions-raised-by-this-verification).
