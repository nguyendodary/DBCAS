# Final UI screenshot index — 2026-11-10

**102 images, 25 screen states, both themes at 1280/390 px, plus SQL at 768/1920 px.** All images are full-page renders of the real application against an isolated PostgreSQL 17 Compose stack. Production Vite preview: `127.0.0.1:5176`; API: `127.0.0.1:19100`. Desktop viewport: 1280 × 900; mobile: 390 × 844. Both demo accounts signed in through the browser. No real LLM call was used for the captures.

The complete matrix ran in **133.58s**, with **0 page overflow and 0 page errors**. Only the four landing images were refreshed after `25b0e0a`; after `26d7e6d`, the 32 affected auth/admin images were refreshed in **30.31s** and the other 70 captures retained. Unchanged screen code justifies that reuse; each record includes its capture source commit and image hash in [verification.json](verification.json). Every final image was opened and described in [visual-review.md](visual-review.md).

| Screen/state | 1280 light | 1280 dark | 390 light | 390 dark |
| --- | --- | --- | --- | --- |
| landing | [image](light/landing-light-1280.png) | [image](dark/landing-dark-1280.png) | [image](light/landing-light-390.png) | [image](dark/landing-dark-390.png) |
| login | [image](light/login-light-1280.png) | [image](dark/login-dark-1280.png) | [image](light/login-light-390.png) | [image](dark/login-dark-390.png) |
| register | [image](light/register-light-1280.png) | [image](dark/register-dark-1280.png) | [image](light/register-light-390.png) | [image](dark/register-dark-390.png) |
| forgot-password | [image](light/forgot-password-light-1280.png) | [image](dark/forgot-password-dark-1280.png) | [image](light/forgot-password-light-390.png) | [image](dark/forgot-password-dark-390.png) |
| reset-password | [image](light/reset-password-light-1280.png) | [image](dark/reset-password-dark-1280.png) | [image](light/reset-password-light-390.png) | [image](dark/reset-password-dark-390.png) |
| oauth-callback | [image](light/oauth-callback-light-1280.png) | [image](dark/oauth-callback-dark-1280.png) | [image](light/oauth-callback-light-390.png) | [image](dark/oauth-callback-dark-390.png) |
| dashboard | [image](light/dashboard-light-1280.png) | [image](dark/dashboard-dark-1280.png) | [image](light/dashboard-light-390.png) | [image](dark/dashboard-dark-390.png) |
| assessments | [image](light/assessments-light-1280.png) | [image](dark/assessments-dark-1280.png) | [image](light/assessments-light-390.png) | [image](dark/assessments-dark-390.png) |
| exam-mcq | [image](light/exam-mcq-light-1280.png) | [image](dark/exam-mcq-dark-1280.png) | [image](light/exam-mcq-light-390.png) | [image](dark/exam-mcq-dark-390.png) |
| exam-sql | [image](light/exam-sql-light-1280.png) | [image](dark/exam-sql-dark-1280.png) | [image](light/exam-sql-light-390.png) | [image](dark/exam-sql-dark-390.png) |
| exam-essay | [image](light/exam-essay-light-1280.png) | [image](dark/exam-essay-dark-1280.png) | [image](light/exam-essay-light-390.png) | [image](dark/exam-essay-dark-390.png) |
| evaluation | [image](light/evaluation-light-1280.png) | [image](dark/evaluation-dark-1280.png) | [image](light/evaluation-light-390.png) | [image](dark/evaluation-dark-390.png) |
| overall | [image](light/overall-light-1280.png) | [image](dark/overall-dark-1280.png) | [image](light/overall-light-390.png) | [image](dark/overall-dark-390.png) |
| history | [image](light/history-light-1280.png) | [image](dark/history-dark-1280.png) | [image](light/history-light-390.png) | [image](dark/history-dark-390.png) |
| evidence | [image](light/evidence-light-1280.png) | [image](dark/evidence-dark-1280.png) | [image](light/evidence-light-390.png) | [image](dark/evidence-dark-390.png) |
| settings | [image](light/settings-light-1280.png) | [image](dark/settings-dark-1280.png) | [image](light/settings-light-390.png) | [image](dark/settings-dark-390.png) |
| admin-dashboard | [image](light/admin-dashboard-light-1280.png) | [image](dark/admin-dashboard-dark-1280.png) | [image](light/admin-dashboard-light-390.png) | [image](dark/admin-dashboard-dark-390.png) |
| admin-grading | [image](light/admin-grading-light-1280.png) | [image](dark/admin-grading-dark-1280.png) | [image](light/admin-grading-light-390.png) | [image](dark/admin-grading-dark-390.png) |
| admin-review-detail | [image](light/admin-review-detail-light-1280.png) | [image](dark/admin-review-detail-dark-1280.png) | [image](light/admin-review-detail-light-390.png) | [image](dark/admin-review-detail-dark-390.png) |
| admin-accounts | [image](light/admin-accounts-light-1280.png) | [image](dark/admin-accounts-dark-1280.png) | [image](light/admin-accounts-light-390.png) | [image](dark/admin-accounts-dark-390.png) |
| admin-bank | [image](light/admin-bank-light-1280.png) | [image](dark/admin-bank-dark-1280.png) | [image](light/admin-bank-light-390.png) | [image](dark/admin-bank-dark-390.png) |
| admin-clo | [image](light/admin-clo-light-1280.png) | [image](dark/admin-clo-dark-1280.png) | [image](light/admin-clo-light-390.png) | [image](dark/admin-clo-dark-390.png) |
| admin-system | [image](light/admin-system-light-1280.png) | [image](dark/admin-system-dark-1280.png) | [image](light/admin-system-light-390.png) | [image](dark/admin-system-dark-390.png) |
| admin-learner-competency | [image](light/admin-learner-competency-light-1280.png) | [image](dark/admin-learner-competency-dark-1280.png) | [image](light/admin-learner-competency-light-390.png) | [image](dark/admin-learner-competency-dark-390.png) |
| admin-settings | [image](light/admin-settings-light-1280.png) | [image](dark/admin-settings-dark-1280.png) | [image](light/admin-settings-light-390.png) | [image](dark/admin-settings-dark-390.png) |

Additional SQL widths: [768 px](light/exam-sql-light-768.png), [1920 px](light/exam-sql-light-1920.png).

- **Contrast: 186/186 PASS** on the final CSS (`npm run ui:contrast`): reading text ≥4.5:1 and chart graphics ≥3:1, both themes.
- **Fonts:** self-hosted Inter 400/500/600/700 including Vietnamese glyphs; JetBrains Mono only for SQL. Actual computed-font assertions cover the interface, MCQ, essay, SQL and administrator prose/reference fields.
- **Charts:** 0–100% scales, token-based accessible colors, legends and numeric text equivalents. The one-date admin trend point is centered inside its plot.
- **Responsive layout:** page width remains within each viewport. Wide schema/result/admin tables and SQL lines scroll locally. The long concept label wraps while preserving both row actions.
- **Dark parity:** all 25 corresponding screen states were inspected. Dark surfaces, media, fields and cyan controls remain distinct; shared typography and chart accessibility fixes apply to both themes.
- **Result visibility:** screenshots use published seeded evaluation/evidence. The same capture run took MCQ/SQL/essay through the real UI, checked null score/correctness on submission and a pending approval result after finish. Pending history rows show no score; overall excludes them.
- **Auth states:** reset-password shows the real missing-token state; OAuth callback shows its retained localized handoff error. Success/error/reload behavior is additionally covered by the default browser suite.

Reference analysis: [Artificial Analysis](https://artificialanalysis.ai/), with retained [reference captures](reference/README.md). The design adopts its pale canvas, white bordered surfaces, restrained shadows and dense readable data layout while retaining Inter and the existing dark palette. The [light-theme spec](light-theme-spec.md) defines the tokens. The earlier focused SQL/dashboard captures remain in [index.md](index.md) as historical evidence.
