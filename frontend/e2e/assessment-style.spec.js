import { expect, test } from '@playwright/test'

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

const fixedSession = {
  session_id: 98,
  assessment_id: null,
  status: 'completed',
  assessment_title: 'Free practice',
  runner_mode: null,
  result_kind: null,
  ability_estimate: null,
  study_suggestions: [],
  adaptive_progress: null,
}

test('adaptive style constrains the builder and never reports a percentage', async ({ page }) => {
  await stubApp(page, adaptiveSession)
  const starts = []
  page.on('request', (request) => {
    if (/\/api\/v1\/practice\/start$/.test(request.url())) starts.push(request.postDataJSON())
  })

  await page.goto('/assessments')
  await expect(page.getByRole('radio', { name: 'Free practice' })).toBeChecked()
  await expect(page.getByRole('radio', { name: 'Adaptive practice' })).toBeVisible()

  await page.getByRole('button', { name: 'SELECT', exact: true }).click()
  await page.getByRole('radio', { name: 'Adaptive practice' }).check()

  await expect(page.getByText('Adaptive practice constraints')).toBeVisible()
  await expect(page.getByText('Exactly one concept', { exact: true })).toBeVisible()
  await expect(page.getByText('Multiple-choice questions only')).toBeVisible()
  await expect(page.getByText('3–50 questions')).toBeVisible()
  await expect(page.getByRole('radio', { name: 'AI tạo câu hỏi' })).toHaveCount(0)
  await expect(page.getByLabel('Số câu (3–50)')).toHaveAttribute('min', '3')
  await expect(page.getByLabel('Số câu (3–50)')).toHaveAttribute('max', '50')

  await page.getByRole('button', { name: 'JOIN', exact: true }).click()
  await expect(page.getByRole('button', { name: 'SELECT', exact: true })).toHaveAttribute(
    'aria-pressed',
    'false',
  )
  await page.getByRole('button', { name: 'Bắt đầu' }).click()

  await expect.poll(() => starts.length).toBe(1)
  expect(starts[0]).toMatchObject({
    assessment_style: 'ADAPTIVE',
    source: 'bank',
    concept_ids: [2],
    difficulties: ['EASY'],
    question_count: 5,
  })

  await expect(page).toHaveURL(/\/evaluations\/99$/)
  await expect(page.getByText('Estimated ability')).toBeVisible()
  await expect(page.getByText('SELECT')).toBeVisible()
  await expect(page.getByText(/not an official score/i)).toBeVisible()
  await expect(page.locator('.content-wrap')).not.toContainText('%')
})

test('free practice labels its result as an official score', async ({ page }) => {
  await stubApp(page, fixedSession)
  await page.goto('/assessments')
  await page.getByRole('button', { name: 'SELECT', exact: true }).click()
  await page.getByRole('button', { name: 'Bắt đầu' }).click()

  await expect(page).toHaveURL(/\/evaluations\/98$/)
  await expect(page.getByText('Official score')).toBeVisible()
  await expect(page.getByText('80.00%')).toBeVisible()
  await expect(page.getByText('Estimated ability')).toHaveCount(0)
})
