import { test, expect } from '../e2e/browser-fixture.js'
import { API, call, createConceptUi, login } from '../e2e/optional-capabilities.js'
import { register, start, take, api, vi, checkViewport } from '../e2e/practice-harness.js'
import AxeBuilder from '@axe-core/playwright'

// Learner-defined practice supersedes the retired adaptive-round UI. Exercise
// its difficulty, recovery and early-finish contracts against app.main itself.
test('real application: selected difficulty, saved state and finalized score bounds', async ({
  page,
}) => {
  test.setTimeout(240000)
  await register(page, 'application-difficulty')
  for (const band of ['EASY', 'MEDIUM', 'HARD']) {
    const state = await start(page, 'ai', 5, { difficulties: [band] })
    expect(state.current_question.options.every((o) => !Object.hasOwn(o, 'is_correct'))).toBe(true)
    await take(page, state, { refresh: true })
    await expect(page.getByRole('heading', { name: 'Nhận xét từng câu' })).toBeVisible({
      timeout: 45000,
    })
    expect((await api(page, `/sessions/${state.session_id}`)).expires_at).toBe(state.expires_at)
    const evidence = await api(page, `/sessions/${state.session_id}/evidence`)
    expect(evidence.items).toHaveLength(5)
    expect(new Set(evidence.items.map((q) => q.question_id)).size).toBe(5)
    for (const q of evidence.items) {
      expect(q.difficulty_level).toBeGreaterThanOrEqual(
        band === 'EASY' ? 1 : band === 'MEDIUM' ? 3 : 4,
      )
      expect(q.difficulty_level).toBeLessThanOrEqual(
        band === 'EASY' ? 2 : band === 'MEDIUM' ? 3 : 5,
      )
      expect(Number(q.score)).toBeGreaterThanOrEqual(0)
      expect(Number(q.score)).toBeLessThanOrEqual(Number(q.points))
    }
  }
  expect((await api(page, '/sessions/competency/cumulative')).summary.finalized_assessments).toBe(3)
})

test('real application: 390px early finish scores all planned unanswered items as zero', async ({
  page,
}) => {
  await register(page, 'application-early')
  await page.setViewportSize({ width: 390, height: 844 })
  const state = await start(page, 'ai', 5)
  await page.getByRole('button', { name: vi.exam.finish, exact: true }).click()
  await page
    .getByRole('dialog')
    .getByRole('button', { name: vi.exam.confirmFinish, exact: true })
    .click()
  await expect(page.getByRole('heading', { name: 'Nhận xét từng câu' })).toBeVisible({
    timeout: 45000,
  })
  const evidence = await api(page, `/sessions/${state.session_id}/evidence`)
  expect(evidence.items).toHaveLength(5)
  expect(evidence.items.every((q) => Number(q.score) === 0 && q.submitted_at)).toBe(true)
  expect((await api(page, `/evaluations/attempts/${state.session_id}`)).score.percentage).toBe(0)
  await checkViewport(page)
  expect(
    (await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze()).violations,
  ).toEqual([])
})

test('real application: unavailable bank AI generation rejects without a fabricated draft', async ({
  page,
}) => {
  const admin = await login(page)
  const topic = await createConceptUi(page)
  // Candidate generation remains an admin API. The retired candidates screen
  // is absent from navigation; a missing key must still fail without writes.
  await expect(
    page.locator('.app-sidebar nav').getByRole('link', { name: /Candidates/ }),
  ).toHaveCount(0)
  const result = await page.request.post(`${API}/admin/question-candidates/generate`, {
    headers: { Authorization: `Bearer ${admin}` },
    data: {
      concept_id: topic.concept_id,
      question_type: 'mcq',
      locale: 'vi',
      difficulty: 'MEDIUM',
      count: 1,
    },
  })
  expect(result.status()).toBe(503)
  expect((await result.json()).error.code).toBe('llm_not_configured')
  expect(
    (await call(page, '/admin/question-candidates', admin)).filter(
      (c) => c.concept_id === topic.concept_id,
    ),
  ).toEqual([])
})
