# W1 screenshots — learner end-to-end audit

Captured with real Chromium against the **rebuilt** demo stack (web http://localhost:18080, API http://localhost:18000) on 2026-11-11, after the root `npm run test:qa` gate rebuilt the frontend from current source. Each image is a CSS-scale full-page capture at the stated viewport, theme and locale.

`screenshots/verification.json` records PNG dimensions and byte size for all 68 audit files; every file is non-zero and every filename matches its actual pixel width. Historical D1 evidence is preserved separately under `screenshots/pre-rebuild/` (two 1298 px images from the pre-rebuild running image). Four post-rebuild D1 recheck captures (`dashboard`/`assessments`, EN, 1280/390) are under `screenshots/post-rebuild/`; all are exactly 1280/390 px.

Method: `docs/qa/final-20261113/w1/audit.mjs` (Playwright; no provider key read or printed).

| File | State | Viewport | Theme | Locale | Bytes | Width check |
| --- | --- | ---: | --- | --- | ---: | --- |
| [login-vi-dark-1280.png](./login-vi-dark-1280.png) | Login page | 1280 | dark | vi | 402,590 | ok |
| [login-vi-dark-390.png](./login-vi-dark-390.png) | Login page | 390 | dark | vi | 101,271 | ok |
| [login-vi-light-1280.png](./login-vi-light-1280.png) | Login page | 1280 | light | vi | 381,135 | ok |
| [login-vi-light-390.png](./login-vi-light-390.png) | Login page | 390 | light | vi | 96,674 | ok |
| [register-vi-dark-1280.png](./register-vi-dark-1280.png) | Register page | 1280 | dark | vi | 394,941 | ok |
| [register-vi-dark-390.png](./register-vi-dark-390.png) | Register page | 390 | dark | vi | 97,071 | ok |
| [register-vi-light-1280.png](./register-vi-light-1280.png) | Register page | 1280 | light | vi | 371,626 | ok |
| [register-vi-light-390.png](./register-vi-light-390.png) | Register page | 390 | light | vi | 91,492 | ok |
| [oauth-notice-vi-dark-390.png](./oauth-notice-vi-dark-390.png) | Unconfigured provider: localized notice, no navigation | 390 | dark | vi | 97,390 | ok |
| [oauth-metadata-failure-vi-dark-1280.png](./oauth-metadata-failure-vi-dark-1280.png) | OAuth metadata 503: both controls safe | 1280 | dark | vi | 399,296 | ok |
| [forgot-password-sent-vi-dark-1280.png](./forgot-password-sent-vi-dark-1280.png) | Password reset request confirmation | 1280 | dark | vi | 493,744 | ok |
| [reset-success-vi-dark-1280.png](./reset-success-vi-dark-1280.png) | Password reset success | 1280 | dark | vi | 538,641 | ok |
| [reset-replay-rejected-vi-dark-1280.png](./reset-replay-rejected-vi-dark-1280.png) | Reset link replay rejected | 1280 | dark | vi | 519,556 | ok |
| [practice-setup-vi-dark-1280.png](./practice-setup-vi-dark-1280.png) | Practice setup: 80 concepts, difficulty, bank/AI, 3 questions | 1280 | dark | vi | 276,169 | ok |
| [practice-setup-vi-dark-390.png](./practice-setup-vi-dark-390.png) | Practice setup: 80 concepts, difficulty, bank/AI, 3 questions | 390 | dark | vi | 340,214 | ok |
| [practice-setup-vi-light-1280.png](./practice-setup-vi-light-1280.png) | Practice setup: 80 concepts, difficulty, bank/AI, 3 questions | 1280 | light | vi | 273,625 | ok |
| [practice-setup-vi-light-390.png](./practice-setup-vi-light-390.png) | Practice setup: 80 concepts, difficulty, bank/AI, 3 questions | 390 | light | vi | 338,138 | ok |
| [count-1-vi-dark-1280.png](./count-1-vi-dark-1280.png) | Exact count 1: one served question | 1280 | dark | vi | 198,219 | ok |
| [count-1-vi-dark-390.png](./count-1-vi-dark-390.png) | Exact count 1: one served question | 390 | dark | vi | 195,343 | ok |
| [count-1-vi-light-1280.png](./count-1-vi-light-1280.png) | Exact count 1: one served question | 1280 | light | vi | 208,158 | ok |
| [count-1-vi-light-390.png](./count-1-vi-light-390.png) | Exact count 1: one served question | 390 | light | vi | 210,309 | ok |
| [count-20-vi-dark-1280.png](./count-20-vi-dark-1280.png) | Exact count 20: twenty served cells | 1280 | dark | vi | 202,224 | ok |
| [count-20-vi-dark-390.png](./count-20-vi-dark-390.png) | Exact count 20: twenty served cells | 390 | dark | vi | 194,364 | ok |
| [count-20-vi-light-1280.png](./count-20-vi-light-1280.png) | Exact count 20: twenty served cells | 1280 | light | vi | 211,013 | ok |
| [count-20-vi-light-390.png](./count-20-vi-light-390.png) | Exact count 20: twenty served cells | 390 | light | vi | 203,796 | ok |
| [ai-source-vi-light-1280.png](./ai-source-vi-light-1280.png) | AI question source: bounded one-question session | 1280 | light | vi | 224,655 | ok |
| [ai-source-vi-light-390.png](./ai-source-vi-light-390.png) | AI question source: bounded one-question session | 390 | light | vi | 218,283 | ok |
| [assessment-active-session-vi-dark-390.png](./assessment-active-session-vi-dark-390.png) | Browser Back: active session resume card | 390 | dark | vi | 43,061 | ok |
| [exam-mcq-vi-dark-1280.png](./exam-mcq-vi-dark-1280.png) | MCQ workspace with autosaved choice | 1280 | dark | vi | 200,726 | ok |
| [exam-mcq-vi-dark-390.png](./exam-mcq-vi-dark-390.png) | MCQ workspace with autosaved choice | 390 | dark | vi | 196,982 | ok |
| [exam-mcq-vi-light-1280.png](./exam-mcq-vi-light-1280.png) | MCQ workspace with autosaved choice | 1280 | light | vi | 208,746 | ok |
| [exam-mcq-vi-light-390.png](./exam-mcq-vi-light-390.png) | MCQ workspace with autosaved choice | 390 | light | vi | 206,629 | ok |
| [exam-sql-vi-dark-1280.png](./exam-sql-vi-dark-1280.png) | SQL workspace: prompt, schema, editor, query result | 1280 | dark | vi | 154,122 | ok |
| [exam-sql-vi-dark-390.png](./exam-sql-vi-dark-390.png) | SQL workspace: prompt, schema, editor, query result | 390 | dark | vi | 138,103 | ok |
| [exam-sql-vi-light-1280.png](./exam-sql-vi-light-1280.png) | SQL workspace: prompt, schema, editor, query result | 1280 | light | vi | 151,894 | ok |
| [exam-sql-vi-light-390.png](./exam-sql-vi-light-390.png) | SQL workspace: prompt, schema, editor, query result | 390 | light | vi | 136,679 | ok |
| [exam-essay-vi-dark-1280.png](./exam-essay-vi-dark-1280.png) | Essay workspace with restored draft | 1280 | dark | vi | 207,995 | ok |
| [exam-essay-vi-dark-390.png](./exam-essay-vi-dark-390.png) | Essay workspace with restored draft | 390 | dark | vi | 198,608 | ok |
| [exam-essay-vi-light-1280.png](./exam-essay-vi-light-1280.png) | Essay workspace with restored draft | 1280 | light | vi | 217,906 | ok |
| [exam-essay-vi-light-390.png](./exam-essay-vi-light-390.png) | Essay workspace with restored draft | 390 | light | vi | 209,871 | ok |
| [two-tabs-essay-vi-dark-1280.png](./two-tabs-essay-vi-dark-1280.png) | Two tabs share the saved essay draft | 1280 | dark | vi | 208,299 | ok |
| [evaluation-waiting-vi-dark-390.png](./evaluation-waiting-vi-dark-390.png) | Evaluation waiting/review state | 390 | dark | vi | 33,146 | ok |
| [evaluation-attempt-vi-dark-1280.png](./evaluation-attempt-vi-dark-1280.png) | Per-attempt evaluation: score, 3 comments, approval | 1280 | dark | vi | 291,461 | ok |
| [evaluation-attempt-vi-dark-390.png](./evaluation-attempt-vi-dark-390.png) | Per-attempt evaluation: score, 3 comments, approval | 390 | dark | vi | 277,939 | ok |
| [evaluation-attempt-vi-light-1280.png](./evaluation-attempt-vi-light-1280.png) | Per-attempt evaluation: score, 3 comments, approval | 1280 | light | vi | 284,336 | ok |
| [evaluation-attempt-vi-light-390.png](./evaluation-attempt-vi-light-390.png) | Per-attempt evaluation: score, 3 comments, approval | 390 | light | vi | 266,898 | ok |
| [overall-0-vi-light-1280.png](./overall-0-vi-light-1280.png) | Overall evaluation: 0 attempts empty state | 1280 | light | vi | 47,542 | ok |
| [overall-0-vi-light-390.png](./overall-0-vi-light-390.png) | Overall evaluation: 0 attempts empty state | 390 | light | vi | 37,435 | ok |
| [overall-1-vi-light-1280.png](./overall-1-vi-light-1280.png) | Overall evaluation: 1 attempt, no trend yet | 1280 | light | vi | 248,800 | ok |
| [overall-1-vi-light-390.png](./overall-1-vi-light-390.png) | Overall evaluation: 1 attempt, no trend yet | 390 | light | vi | 232,686 | ok |
| [overall-3-vi-dark-1280.png](./overall-3-vi-dark-1280.png) | Overall evaluation: 3 attempts, trend and cumulative score | 1280 | dark | vi | 323,060 | ok |
| [overall-3-vi-dark-390.png](./overall-3-vi-dark-390.png) | Overall evaluation: 3 attempts, trend and cumulative score | 390 | dark | vi | 305,494 | ok |
| [overall-3-vi-light-1280.png](./overall-3-vi-light-1280.png) | Overall evaluation: 3 attempts, trend and cumulative score | 1280 | light | vi | 314,272 | ok |
| [overall-3-vi-light-390.png](./overall-3-vi-light-390.png) | Overall evaluation: 3 attempts, trend and cumulative score | 390 | light | vi | 293,063 | ok |
| [history-vi-dark-1280.png](./history-vi-dark-1280.png) | History with three published attempts | 1280 | dark | vi | 384,304 | ok |
| [history-vi-dark-390.png](./history-vi-dark-390.png) | History with three published attempts | 390 | dark | vi | 207,981 | ok |
| [history-vi-light-1280.png](./history-vi-light-1280.png) | History with three published attempts | 1280 | light | vi | 300,654 | ok |
| [history-vi-light-390.png](./history-vi-light-390.png) | History with three published attempts | 390 | light | vi | 176,891 | ok |
| [evidence-vi-dark-390.png](./evidence-vi-dark-390.png) | Evidence page with submitted SQL answer | 390 | dark | vi | 21,722 | ok |
| [settings-vi-dark-1280.png](./settings-vi-dark-1280.png) | Settings: account, theme, language | 1280 | dark | vi | 315,387 | ok |
| [settings-vi-dark-390.png](./settings-vi-dark-390.png) | Settings: account, theme, language | 390 | dark | vi | 142,426 | ok |
| [settings-vi-light-1280.png](./settings-vi-light-1280.png) | Settings: account, theme, language | 1280 | light | vi | 239,396 | ok |
| [settings-vi-light-390.png](./settings-vi-light-390.png) | Settings: account, theme, language | 390 | light | vi | 116,870 | ok |
| [settings-en-en-dark-390.png](./settings-en-en-dark-390.png) | Settings after EN switch and reload | 390 | dark | en | 154,493 | ok |
| [dashboard-en-en-dark-1280.png](./dashboard-en-en-dark-1280.png) | Dashboard in EN with a long account email | 1280 | dark | en | 334,026 | ok |
| [dashboard-en-en-dark-390.png](./dashboard-en-en-dark-390.png) | Dashboard in EN with a long account email | 390 | dark | en | 141,648 | ok |
| [assessments-en-en-dark-1280.png](./assessments-en-en-dark-1280.png) | Practice setup in EN (shell translated; setup copy still VI) | 1280 | dark | en | 242,083 | ok |
| [session-refresh-two-tabs-vi-dark-1280.png](./session-refresh-two-tabs-vi-dark-1280.png) | Two-tab refresh after simulated access-token expiry | 1280 | dark | vi | 202,915 | ok |
