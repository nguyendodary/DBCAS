# Phase 4 — real UI review (2026-11-25)

Application commit `253f272`; local Compose project `dbcas-baseline-local` in
the isolated recovery worktree, example-based `.env` with no real key. The
review used the existing Playwright MCP browser in a new isolated context and
did not modify application code, translation catalogs, snapshots, images or
product behavior. No console errors or warnings were recorded across the
reviewed pages.

## Reviewed surfaces

| Surface | Evidence |
|---|---|
| Signed-out landing, Vietnamese, 1440×1000 | [screenshot](ui-review/landing-desktop.png), [snapshot](ui-review/landing-desktop.snapshot.txt) |
| Login, Vietnamese | [screenshot](ui-review/login-vi.png) |
| Learner dashboard, Free demo | [screenshot](ui-review/learner-dashboard.png) |
| Learner dashboard after demo upgrade to Pro | [screenshot](ui-review/learner-pro-demo.png) |
| Assessment setup, Vietnamese / English | [vi](ui-review/learner-assessments.png), [en](ui-review/learner-assessments-en.png) |
| Assessment setup, English, 390×844 | [screenshot](ui-review/assessments-mobile-390.png) |
| Admin cohort, English | [screenshot](ui-review/admin-dashboard.png) |
| Admin documents, English | [screenshot](ui-review/admin-documents-loaded.png) |
| Admin system, English | [screenshot](ui-review/admin-system-loaded.png) |

## Observations

- The landing page loaded with `document.documentElement.lang = vi`, a visible
  background video, working sign-in/register controls and no horizontal
  document overflow at 1440 px.
- Email/password sign-in routed admin to `/admin` and learner to `/dashboard`.
  Learner navigation, competency charts and theFree/Pro demo card rendered.
  The demo upgrade changed only `localStorage.dbcas_demo_plan` from absent to
  `pro` and replaced the card label with “Pro (Demo) · 99.000 VND / 30 ngày”;
  the card itself states that there is no payment, no API call and no stored
  data. This confirms the accepted UI-only Free/Pro simulation.
- The language selector exposed `[role="menuitemradio"][lang="vi|en"]`. Choosing
  English changed `html[lang]` and the whole navigation/assessment chrome to
  English. The seeded account display name stayed “Quản trị demo”; that is a
  data value, not untranslated chrome.
- Mode 1 and Mode 2 radio cards were visible, with stable
  `input[name="assessment-style"][value="FIXED|ADAPTIVE"]`. At 390 px the
  document itself had zero horizontal overflow and the mode cards fit; only
  the deliberately scrollable navigation row extended beyond the viewport.
- Admin navigation showed six focused screens. `/admin/documents` rendered its
  upload, CLO/concept selection and grounded-draft controls with “No documents
  yet” in the isolated stack; no personal data was shown. `/admin/system`
  showed the template fallback, rule-based evaluator fallback, PostgreSQL 17
  and the generic key-only LLM note.
- No application behavior was changed. In particular, no existing image
  snapshot, UI asset, translation, validator or product setting was edited.

## Findings requiring an owner decision (gated by D4)

1. The landing statistic displays **20** under “Câu hỏi tối đa” while its own
   subtitle reads “TÙY CHỌN 1–13 · MẶC ĐỊNH 5” (`frontend/src/i18n/vi.json:1311-1312`)
   and `backend/app/services/practice_config.py` defines a 13-question legacy
   maximum plus typed limits. The large number is stale product copy. No edit
   was made; changing displayed product content is an owner-gated D4 change.
2. `/admin/system` still says every submission requires administrator review
   and that only approved attempts count (`frontend/src/i18n/en.json:1280-1287`).
   The accepted lifecycle auto-publishes `AI_OFFICIAL_REVIEW` results through
   `ensure_official_v1` and `transition(..., "published")`
   (`backend/app/services/assessment_lifecycle.py:233-238`). This is an
   outdated explanation of the release workflow, separate from the standing
   decision that AI-official results have no per-question comments. No copy,
   translation or test was changed; the correction needs D4 approval.

These two items are recorded only as proposals. The UI otherwise matched the
accepted freeze behavior without product changes.
