import { expect, test } from '@playwright/test'
import en from '../src/i18n/en.json' with { type: 'json' }

// Deterministic style-picker coverage: every endpoint is fulfilled locally, so
// the spec needs no bank seeding, grading worker, fixed delay or provider.
const ACCOUNT = {
  account_id: 7,
  email: 'style@example.com',
  full_name: 'Style Tester',
  roles: ['Learner'],
}
const OPTIONS = {
  question_count: { min: 1, default: 5, max: 13, presets: [5, 10, 13] },
  concepts: [
    { concept_id: 1, concept_name: 'SELECT', clos: [] },
    { concept_id: 2, concept_name: 'JOIN', clos: [] },
  ],
}
const PREVIEW = {
  can_start: true,
  question_count: 5,
  type_counts: { mcq: 5 },
  covered_concepts: [],
  uncovered_concepts: [],
  notice: null,
}
const EVALUATION = {
  status: 'ready',
  attempt_count: 3,
  pending_count: 0,
  dimensions: {},
  history: [],
  score: { percentage: '80.00', earned: '8', possible: '10' },
  result: {
    evaluation: {
      summary: 'Graded summary',
      strengths: [],
      weaknesses: [],
      suggestions: [],
      learning_path: [],
      question_comments: [],
    },
  },
  approved: false,
  adjusted: false,
  details_truncated: false,
  input_hash: 'hash',
  concept_results: [],
  question_results: [],
  uncovered_concepts: [],
}

const json = (body) => ({
  status: 200,
  contentType: 'application/json',
  body: JSON.stringify(body),
})

async function stubApp(page, session) {
  await page.addInitScript(() => {
    // A non-JWT token keeps the auth renewal timer dormant.
    localStorage.setItem('dbcas_token', 'fake.token.value')
    localStorage.setItem('dbcas_locale', 'en')
  })
  await page.route(/\/api\/v1\/auth\/me$/, (route) => route.fulfill(json(ACCOUNT)))
  await page.route(/\/api\/v1\/sessions$/, (route) => route.fulfill(json([])))
  await page.route(/\/api\/v1\/practice\/options$/, (route) => route.fulfill(json(OPTIONS)))
  await page.route(/\/api\/v1\/practice\/preview$/, (route) => route.fulfill(json(PREVIEW)))
  await page.route(/\/api\/v1\/practice\/start$/, (route) =>
    route.fulfill(json({ session_id: session.session_id })),
  )
  await page.route(/\/api\/v1\/sessions\/\d+$/, (route) => route.fulfill(json(session)))
  await page.route(/\/api\/v1\/evaluations\/attempts\/\d+$/, (route) =>
    route.fulfill(json(EVALUATION)),
  )
}

const adaptiveSession = {
  session_id: 99,
  assessment_id: null,
  status: 'completed',
  assessment_title: 'Adaptive practice',
  runner_mode: 'adaptive',
  result_kind: 'estimated_ability',
  ability_estimate: {
    band: 'MEDIUM',
    index: 3.4,
    confidence: 'medium',
    evidence_count: 6,
    provisional: true,
  },
  study_suggestions: [
    {
      concept_id: 1,
      concept_code: 'C1',
      concept_name: 'SELECT',
      subject_area: 'SQL',
      reason: 'below_target',
    },
  ],
  adaptive_progress: null,
}

const NOW = '2030-01-01T00:00:00.000Z'
const END = '2030-01-01T00:30:00.000Z'
const fixedSession = {
  session_id: 98,
  assessment_id: null,
  status: 'in_progress',
  assessment_title: 'Test',
  runner_mode: 'fixed',
  result_kind: 'official_score',
  ability_estimate: null,
  study_suggestions: [],
  adaptive_progress: null,
  server_now: NOW,
  expires_at: END,
  remaining_seconds: 1800,
}
const paperMetadata = {
  session_id: 98,
  runner_mode: 'fixed',
  status: 'in_progress',
  assessment_title: 'Test',
  started_at: NOW,
  expires_at: END,
  server_now: NOW,
  remaining_seconds: 1800,
  question_count: 13,
  answered_count: 0,
  flagged_count: 0,
  last_opened_seq: 1,
  tab_leave_count: 0,
  tab_leave_grace_seconds: 3,
  tab_leave_violation_limit: 3,
  questions: Array.from({ length: 13 }, (_, index) => ({
    seq_no: index + 1,
    question_id: 101 + index,
    question_type: 'mcq',
    answered: false,
    flagged: false,
    opened: index === 0,
    draft_revision: 0,
  })),
}
const paperQuestion = {
  seq_no: 1,
  question_id: 101,
  question_type: 'mcq',
  content_locale: 'en',
  prompt: 'First test question',
  options: [
    { option_id: 1, option_label: 'A', option_text: 'First option' },
    { option_id: 2, option_label: 'B', option_text: 'Second option' },
  ],
  schema_sql: null,
  draft: null,
  draft_revision: 0,
  answered: false,
  flagged: false,
  flag_revision: 0,
  first_opened_at: null,
  remaining_seconds: 1800,
  server_now: NOW,
}

test('adaptive style constrains the builder and never reports a percentage', async ({ page }) => {
  await stubApp(page, adaptiveSession)
  const starts = []
  page.on('request', (request) => {
    if (/\/api\/v1\/practice\/start$/.test(request.url())) starts.push(request.postDataJSON())
  })

  await page.goto('/assessments')
  await expect(page.locator('input[name="assessment-style"][value="FIXED"]')).toBeChecked()
  await expect(page.locator('input[name="assessment-style"][value="ADAPTIVE"]')).toBeVisible()

  await page.getByRole('button', { name: 'SELECT', exact: true }).click()
  await page.locator('input[name="assessment-style"][value="ADAPTIVE"]').check()

  await expect(page.getByText(en.ui.mode.aiConstraintsTitle)).toBeVisible()
  await expect(page.getByText(en.ui.mode.aiConstraintConcept, { exact: true })).toBeVisible()
  await expect(page.getByText(en.ui.mode.aiConstraintBand, { exact: true })).toBeVisible()
  await expect(page.getByText(en.ui.mode.aiConstraintLive, { exact: true })).toBeVisible()
  await expect(page.getByText(en.ui.mode.aiConstraintFallback, { exact: true })).toBeVisible()
  await expect(
    page.getByRole('spinbutton', { name: en.assessmentStyle.fixed.types.mcq }),
  ).toHaveValue('1')
  await expect(
    page.getByRole('spinbutton', { name: en.assessmentStyle.fixed.types.sql }),
  ).toHaveValue('1')
  await expect(
    page.getByRole('spinbutton', { name: en.assessmentStyle.fixed.types.essay }),
  ).toHaveValue('1')
  await expect(page.getByText(en.ui.assessments.mixTotal.replace('{{total}}', '3'))).toBeVisible()

  await page.getByRole('button', { name: 'JOIN', exact: true }).click()
  await expect(page.getByRole('button', { name: 'SELECT', exact: true })).toHaveAttribute(
    'aria-pressed',
    'false',
  )
  await page.getByRole('button', { name: 'Start' }).click()

  await expect.poll(() => starts.length).toBe(1)
  expect(starts[0]).toMatchObject({
    assessment_style: 'ADAPTIVE',
    source: 'ai',
    concept_ids: [2],
    difficulties: ['EASY'],
    question_count: 3,
    question_mix: { mcq: 1, sql: 1, essay: 1 },
  })

  await expect(page).toHaveURL(/\/evaluations\/99$/)
  await expect(page.getByText('Estimated ability')).toBeVisible()
  await expect(page.getByText('SELECT')).toBeVisible()
  await expect(page.getByText(/not an official score/i)).toBeVisible()
  await expect(page.locator('.content-wrap')).not.toContainText('%')
})

test('test mode creates a FIXED paper and lands in the free-navigation runner', async ({
  page,
}) => {
  await stubApp(page, fixedSession)
  await page.route(/\/api\/v1\/sessions\/98\/paper$/, (route) => route.fulfill(json(paperMetadata)))
  await page.route(/\/api\/v1\/sessions\/98\/paper\/1$/, (route) =>
    route.fulfill(json(paperQuestion)),
  )
  const starts = []
  page.on('request', (request) => {
    if (/\/api\/v1\/practice\/start$/.test(request.url())) starts.push(request.postDataJSON())
  })

  await page.goto('/assessments')
  await expect(page.locator('input[name="assessment-style"][value="FIXED"]')).toBeChecked()
  await page.getByRole('button', { name: 'SELECT', exact: true }).click()
  await page.getByRole('button', { name: 'Start' }).click()

  await expect.poll(() => starts.length).toBe(1)
  expect(starts[0]).toMatchObject({
    assessment_style: 'FIXED',
    source: 'bank',
    concept_ids: [1],
    difficulties: ['EASY'],
    question_count: 13,
    question_mix: { mcq: 10, sql: 2, essay: 1 },
  })

  await expect(page).toHaveURL(/\/exam\/98$/)
  await expect(page.getByText('QUESTION 1 / 13')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Submit final answers' })).toBeVisible()
})
