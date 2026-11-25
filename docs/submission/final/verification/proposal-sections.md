# Proposal — required 15-section audit (final ver1.3)

Audited 2026-11-26 against the rendered 62-page Proposal. Status values:
**present** = required section and content exist; **wrong** = section exists but
contained a fact/structure defect that was fixed in place.

| # | Required section | Status | Fix applied |
|---:|---|---|---|
| 1 | Project Title (<15 words) | present | 9-word title; cover, project-information table and §1 agree. |
| 2 | Team Members (name, ID, email, role) | present | Five members with MSSV, email, phone, primary role and responsibilities; owner asked to confirm identities (O1). |
| 3 | Supervisor(s) (name, faculty, email, co-supervisor) | wrong → fixed | Department changed from “Software Engineering Department” to “CSE Center, International School” so §3 and Table 2 agree; owner asked to confirm the official faculty name and co-supervisor policy (O2). |
| 4 | Problem Statement | wrong → fixed | Added IEEE citations [1], [2], [6], [8] to the online-research paragraph; the problem/impact/why narrative is retained. |
| 5 | Survey / Existing Solutions | wrong → fixed | Comparison table retained; added [14] for LeetCode-style practice sites, [3] for curriculum alignment and [6], [7] for chatbot risks. |
| 6 | Objectives and Scope (SMART; in/out) | present | SMART table and in/out scope retained; implemented document grounding is outside the exclusion bullet; writable DML stays opt-in and rolled back. |
| 7 | Key Features & Requirements (5–7 features; FR/NFR) | wrong → fixed | Exactly seven features; FR-06 split so it no longer mixes runtime status with session configuration; the configuration text moved to FR-07; FR-01–FR-16 and NFR-01–NFR-09 remain. Explicit Mode 1 / Mode 2 paragraph added. |
| 8 | Constraints and Assumptions | present | Table 10 retained; sandbox wording separates default read-only from the opt-in ephemeral writable demo. |
| 9 | Target Users / Stakeholders | present | Four stakeholder groups and needs retained (learners, administrators, academic leaders, team). |
| 10 | Technology Stack | wrong → fixed | Nine layers now: added the AI/ML row (no trained model; OpenAI-compatible endpoint through `.env`) and the Testing & QA row (pytest, Vitest, Playwright, gates). |
| 11 | Methodology & Development Plan (Gantt/sprints) | wrong → fixed | Table 13 retained; Figure 1 replaced with a legible 13-row roadmap; final submission (10–13/12) precedes the defence (17–26/12); status reports are 03/10, 17/10, 20/11, 05/12. |
| 12 | System Architecture Overview (context + logical) | present | Figure 2 context and Figure 3 logical replaced with measured, legible versions; counts 67/561/122/159/28 and 106 paths/118 operations agree with the repository. |
| 13 | Potential Risks and Mitigation | wrong → fixed | RSK-01 no longer says DML/DDL are only assessed by MCQ/essay; it now describes the opt-in writable demo, rollback and read-only grading. |
| 14 | Expected Outcomes / Deliverables | wrong → fixed | `OWNER UNKNOWN` removed; the public-URL row is an explicit `[OWNER TO PROVIDE: …]` decision (O4). |
| 15 | References (IEEE/APA) | wrong → fixed | In-text citations added; [13] author corrected from “S. Ramírez” to “FastAPI project and contributors”; 14 IEEE entries retained. |

**Roll-up:** 15/15 present; 9 sections required a content or wording fix; no
section was removed or reordered. The two appendices (owner decisions, figure
sources) sit after §15 and do not count as proposal sections.
