import { test, expect } from './browser-fixture.js'
import { api, approveWithApi, login, register, start, vi } from './practice-harness.js'

test.describe.configure({ mode: 'serial' })

test('legacy practice is labelled practice, server-owned and excluded from cumulative', async ({
  page,
}) => {
  test.setTimeout(180_000)
  const email = await register(page, 'purpose-practice')
  const state = await start(page, 'bank', 3, { difficulties: ['EASY'] })
  expect(state.purpose).toBe('PRACTICE')

  const history = await api(page, '/sessions')
  const record = history.find((item) => item.session_id === state.session_id)
  expect(record.purpose).toBe('PRACTICE')
  expect((await api(page, `/sessions/${state.session_id}`)).purpose).toBe('PRACTICE')

  // The client cannot choose the purpose; extra request fields are rejected.
  const override = await page.request.fetch('/api/v1/practice/start', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${await page.evaluate(() => localStorage.getItem('dbcas_token'))}`,
    },
    data: { ...state._startRequest, purpose: 'TEST' },
  })
  expect(override.status()).toBe(422)

  await page.goto('/history')
  await expect(page.getByText(vi.sessionPurpose.PRACTICE, { exact: true })).toBeVisible()
  let cumulative = await api(page, '/sessions/competency/cumulative')
  expect(cumulative.summary.finalized_assessments).toBe(0)
  expect(cumulative.concepts).toEqual([])

  await api(page, `/sessions/${state.session_id}/finish`, 'POST')
  const formal = await api(page, '/assessments/1/sessions', 'POST')
  expect(formal.purpose).toBe('TEST')
  expect((await api(page, '/sessions')).some((item) => item.purpose === 'TEST')).toBe(true)
  await page.goto('/history')
  await expect(page.getByText(vi.sessionPurpose.TEST, { exact: true })).toBeVisible()
  await expect(page.getByText(vi.sessionPurpose.PRACTICE, { exact: true })).toBeVisible()
  cumulative = await api(page, '/sessions/competency/cumulative')
  expect(cumulative.summary.finalized_assessments).toBe(0)
  expect(cumulative.concepts).toEqual([])
  await api(page, `/sessions/${formal.session_id}/finish`, 'POST')
  expect(email).toBeTruthy()
})

test('a published adaptive estimate appears only in the separate cumulative table', async ({
  page,
  browser,
}) => {
  test.setTimeout(240_000)
  const email = await register(page, 'purpose-adaptive')
  const options = await api(page, '/practice/options')
  const token = await page.evaluate(() => localStorage.getItem('dbcas_token'))
  let state
  let conceptId
  for (const concept of options.concepts) {
    const response = await page.request.fetch('/api/v1/practice/start', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      data: {
        concept_ids: [concept.concept_id],
        difficulties: ['EASY'],
        source: 'bank',
        question_count: 3,
        assessment_style: 'ADAPTIVE',
        request_id: crypto.randomUUID(),
      },
    })
    if (response.ok()) {
      state = await response.json()
      conceptId = concept.concept_id
      break
    }
  }
  expect(state, 'no concept had enough approved EASY MCQs for adaptive practice').toBeTruthy()
  expect(conceptId).toBeTruthy()
  expect(state.purpose).toBe('TEST')
  const sid = state.session_id
  while (state.current_question) {
    const question = state.current_question
    state = (
      await api(page, `/sessions/${sid}/submit`, 'POST', {
        question_id: question.question_id,
        selected_option_id: question.options[0].option_id,
      })
    ).state
  }
  await api(page, `/sessions/${sid}/finish`, 'POST')
  await approveWithApi(page, sid)

  const cumulative = await api(page, '/sessions/competency/cumulative')
  expect(cumulative.concepts).toEqual([])
  expect(cumulative.adaptive_estimates.map((item) => item.session_id)).toEqual([sid])
  const estimate = cumulative.adaptive_estimates[0]
  expect(estimate.assessment_title).toBe('Luyện tập tự chọn')
  expect(estimate.evidence_count).toBeGreaterThan(0)

  const adminContext = await browser.newContext({ baseURL: test.info().project.use.baseURL })
  const admin = await adminContext.newPage()
  try {
    await login(admin, 'release-admin@test.dev', 'ReleaseTest123!')
    const learners = await api(admin, '/admin/learners')
    const learner = learners.find((item) => item.email === email)
    expect(learner).toBeTruthy()
    await admin.goto(`/admin/learners/${learner.account_id}/competency`)
    await expect(
      admin.getByRole('heading', { name: vi.cumulativeView.adaptiveTitle, exact: true }),
    ).toBeVisible()
    await expect(admin.getByText('Luyện tập tự chọn', { exact: true })).toBeVisible()
    await expect(admin.getByText(vi.supervisor.noEvidence, { exact: true })).toBeVisible()
  } finally {
    await adminContext.close()
  }
})
