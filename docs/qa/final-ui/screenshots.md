# Final UI screenshot index — 2026-11-10

Captured from the `develop2` worktree against a real local stack: an isolated
PostgreSQL 18 database copied from the demo seed, the FastAPI backend on
`127.0.0.1:8001`, and Vite on `127.0.0.1:5175`. Every image is a full-page
browser render, not mock markup. Sizes are CSS pixels; mobile viewport is
390 × 844, desktop 1280 × 900.

| Screen | 1280 light | 1280 dark | 390 light | 390 dark | What it proves |
| --- | --- | --- | --- | --- | --- |
| landing | [`landing-light-1280.png`](light/landing-light-1280.png) | [`landing-dark-1280.png`](dark/landing-dark-1280.png) | [`landing-light-390.png`](light/landing-light-390.png) | [`landing-dark-390.png`](dark/landing-dark-390.png) | Brand landing page with the light media veil, hero copy, sample SQL workspace and three feature cards. |
| login | [`login-light-1280.png`](light/login-light-1280.png) | [`login-dark-1280.png`](dark/login-dark-1280.png) | [`login-light-390.png`](light/login-light-390.png) | [`login-dark-390.png`](dark/login-dark-390.png) | Split auth card: value panel and sign-in form on one calm light surface. |
| register | [`register-light-1280.png`](light/register-light-1280.png) | [`register-dark-1280.png`](dark/register-dark-1280.png) | [`register-light-390.png`](light/register-light-390.png) | [`register-dark-390.png`](dark/register-dark-390.png) | Learner registration form; same auth shell and input treatment. |
| forgot-password | [`forgot-password-light-1280.png`](light/forgot-password-light-1280.png) | [`forgot-password-dark-1280.png`](dark/forgot-password-dark-1280.png) | [`forgot-password-light-390.png`](light/forgot-password-light-390.png) | [`forgot-password-dark-390.png`](dark/forgot-password-dark-390.png) | Password-recovery request form; one primary action, one secondary link. |
| dashboard | [`dashboard-light-1280.png`](light/dashboard-light-1280.png) | [`dashboard-dark-1280.png`](dark/dashboard-dark-1280.png) | [`dashboard-light-390.png`](light/dashboard-light-390.png) | [`dashboard-dark-390.png`](dark/dashboard-dark-390.png) | Learner home: light hero with the white media veil, four stat tiles, radar plus category bars, strength/gap panels, dense concept table and recent activity. |
| assessments | [`assessments-light-1280.png`](light/assessments-light-1280.png) | [`assessments-dark-1280.png`](dark/assessments-dark-1280.png) | [`assessments-light-390.png`](light/assessments-light-390.png) | [`assessments-dark-390.png`](dark/assessments-dark-390.png) | Practice setup: all concept chips visible (no clipped row), difficulty, source, count and the mandatory review note. |
| exam-mcq | [`exam-mcq-light-1280.png`](light/exam-mcq-light-1280.png) | [`exam-mcq-dark-1280.png`](dark/exam-mcq-dark-1280.png) | [`exam-mcq-light-390.png`](light/exam-mcq-light-390.png) | [`exam-mcq-dark-390.png`](dark/exam-mcq-dark-390.png) | MCQ workspace: question navigator, one question, lettered option rows, draft/clear/submit actions. |
| exam-sql | [`exam-sql-light-1280.png`](light/exam-sql-light-1280.png) | [`exam-sql-dark-1280.png`](dark/exam-sql-dark-1280.png) | [`exam-sql-light-390.png`](light/exam-sql-light-390.png) | [`exam-sql-dark-390.png`](dark/exam-sql-dark-390.png) | SQL workspace: two-zone prompt and schema/editor, sample rows, result panel, run/draft actions; 390 px stacks without page overflow. |
| exam-essay | [`exam-essay-light-1280.png`](light/exam-essay-light-1280.png) | [`exam-essay-dark-1280.png`](dark/exam-essay-dark-1280.png) | [`exam-essay-light-390.png`](light/exam-essay-light-390.png) | [`exam-essay-dark-390.png`](dark/exam-essay-dark-390.png) | Essay workspace: long prompt wraps, answer textarea and the same action row. |
| evaluation | [`evaluation-light-1280.png`](light/evaluation-light-1280.png) | [`evaluation-dark-1280.png`](dark/evaluation-dark-1280.png) | [`evaluation-light-390.png`](light/evaluation-light-390.png) | [`evaluation-dark-390.png`](dark/evaluation-dark-390.png) | Published result: release banner, 100% score, AI summary, CLO/topic/difficulty charts on a 0–100 axis and per-question comments. |
| overall | [`overall-light-1280.png`](light/overall-light-1280.png) | [`overall-dark-1280.png`](dark/overall-dark-1280.png) | [`overall-light-390.png`](light/overall-light-390.png) | [`overall-dark-390.png`](dark/overall-dark-390.png) | Cumulative evaluation: trend line, CLO/topic/difficulty bars, strengths, gaps and study logic. |
| history | [`history-light-1280.png`](light/history-light-1280.png) | [`history-dark-1280.png`](dark/history-dark-1280.png) | [`history-light-390.png`](light/history-light-390.png) | [`history-dark-390.png`](dark/history-dark-390.png) | Session history list with status badges, dates, score summaries and links to evidence. |
| evidence | [`evidence-light-1280.png`](light/evidence-light-1280.png) | [`evidence-dark-1280.png`](dark/evidence-dark-1280.png) | [`evidence-light-390.png`](light/evidence-light-390.png) | [`evidence-dark-390.png`](dark/evidence-dark-390.png) | Per-question evidence: prompts, answers, rubrics, SQL, scores and reviewer comments. |
| settings | [`settings-light-1280.png`](light/settings-light-1280.png) | [`settings-dark-1280.png`](dark/settings-dark-1280.png) | [`settings-light-390.png`](light/settings-light-390.png) | [`settings-dark-390.png`](dark/settings-dark-390.png) | Account summary and appearance/language controls on the neutral card surface. |
| admin-dashboard | [`admin-dashboard-light-1280.png`](light/admin-dashboard-light-1280.png) | [`admin-dashboard-dark-1280.png`](dark/admin-dashboard-dark-1280.png) | [`admin-dashboard-light-390.png`](light/admin-dashboard-light-390.png) | [`admin-dashboard-dark-390.png`](dark/admin-dashboard-dark-390.png) | Cohort overview: KPIs, trend, 32-row competency table, learner list and detail panel. |
| admin-grading | [`admin-grading-light-1280.png`](light/admin-grading-light-1280.png) | [`admin-grading-dark-1280.png`](dark/admin-grading-dark-1280.png) | [`admin-grading-light-390.png`](light/admin-grading-light-390.png) | [`admin-grading-dark-390.png`](dark/admin-grading-dark-390.png) | Review queue: every pending practice attempt with its review state. |
| admin-accounts | [`admin-accounts-light-1280.png`](light/admin-accounts-light-1280.png) | [`admin-accounts-dark-1280.png`](dark/admin-accounts-dark-1280.png) | [`admin-accounts-light-390.png`](light/admin-accounts-light-390.png) | [`admin-accounts-dark-390.png`](dark/admin-accounts-dark-390.png) | Account management: create-admin form, filters, role/status badges and row actions. |
| admin-bank | [`admin-bank-light-1280.png`](light/admin-bank-light-1280.png) | [`admin-bank-dark-1280.png`](dark/admin-bank-dark-1280.png) | [`admin-bank-light-390.png`](light/admin-bank-light-390.png) | [`admin-bank-dark-390.png`](dark/admin-bank-dark-390.png) | Question bank: filters, 5482-question list, type/validity/locale badges, pagination. |
| admin-clo | [`admin-clo-light-1280.png`](light/admin-clo-light-1280.png) | [`admin-clo-dark-1280.png`](dark/admin-clo-dark-1280.png) | [`admin-clo-light-390.png`](light/admin-clo-light-390.png) | [`admin-clo-dark-390.png`](dark/admin-clo-dark-390.png) | Concepts and CLO tab: add-concept form and the full concept list with difficulty badges. |
| admin-system | [`admin-system-light-1280.png`](light/admin-system-light-1280.png) | [`admin-system-dark-1280.png`](dark/admin-system-dark-1280.png) | [`admin-system-light-390.png`](light/admin-system-light-390.png) | [`admin-system-dark-390.png`](dark/admin-system-dark-390.png) | System page: the single mandatory AI-then-administrator workflow and AI fallback status. |

## Checks run on the captured set

- **80/80** screenshots were produced; each capture asserted
  `document.documentElement.scrollWidth === window.innerWidth` and the script
  aborted on any positive value. Result: **0 horizontal overflow**.
- **186/186** token contrast pairs pass (`npm run ui:contrast`): every text
  token on every reading surface at 4.5:1, every chart series at 3:1, both
  themes.
- Inter 400/500/600/700 plus Vietnamese glyphs load from the self-hosted
  subset; JetBrains Mono is used only for SQL/code and tabular labels.
- Charts use a 0–100 axis, dashed light grid, 11–12 px labels, direct numeric
  values and a text legend; no series is distinguished by colour alone.
- Screens viewed in words: dashboard, setup, MCQ, SQL, essay, evaluation,
  overall, history, evidence, settings, all six admin screens, auth and
  landing, at 1280 and 390. Dark captures were compared with the
  pre-redesign dark set: palette, chrome, density and chart legibility remain
  intact; the only chart change is the shared axis/legend treatment.

## Notes

- `../final-ui/index.md` is the earlier focused evidence page for the SQL
  workspace; this file is the complete screen matrix for the light-theme round.
- The reference captures used for analysis (not shipped UI) are in
  `reference/` with their own README.
