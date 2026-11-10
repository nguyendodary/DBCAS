import { test, expect } from './browser-fixture.js'
import { call, createConceptUi, login, API } from './optional-capabilities.js'
import {
  register,
  start,
  take,
  api,
  vi,
  checkViewport,
  approveWithApi,
} from './practice-harness.js'
import AxeBuilder from '@axe-core/playwright'

test('learner practice preserves selected difficulty, saved state and score bounds', async ({
  page,
}) => {
  test.setTimeout(240000)
  await register(page, 'difficulty')
  for (const band of ['EASY', 'MEDIUM', 'HARD']) {
    const state = await start(page, 'ai', 5, { difficulties: [band] })
    const expires = state.expires_at
    const served = await api(page, `/sessions/${state.session_id}/questions`)
    expect(served).toHaveLength(1)
    expect(state.current_question.options.every((o) => !Object.hasOwn(o, 'is_correct'))).toBe(true)
    await take(page, state, { refresh: true })
    await expect(page.getByRole('heading', { name: 'Nhận xét từng câu' })).toBeVisible({
      timeout: 45000,
    })
    const final = await api(page, `/sessions/${state.session_id}`)
    expect(final.expires_at).toBe(expires)
    const evidence = await api(page, `/sessions/${state.session_id}/evidence`)
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

test('mobile early finish counts every planned unanswered item as zero', async ({ page }) => {
  await register(page, 'early')
  await page.setViewportSize({ width: 390, height: 844 })
  const state = await start(page, 'ai', 5)
  await page.getByRole('button', { name: vi.exam.finish, exact: true }).click()
  await page
    .getByRole('dialog')
    .getByRole('button', { name: vi.exam.confirmFinish, exact: true })
    .click()
  await approveWithApi(page, state.session_id)
  await page.reload()
  await expect(page.getByRole('heading', { name: 'Nhận xét từng câu' })).toBeVisible({
    timeout: 45000,
  })
  const evidence = await api(page, `/sessions/${state.session_id}/evidence`)
  expect(evidence.items).toHaveLength(5)
  expect(evidence.items.every((item) => Number(item.score) === 0 && item.submitted_at)).toBe(true)
  const history = await api(page, '/sessions')
  expect(
    Number(history.find((item) => item.session_id === state.session_id).overall_result_pct),
  ).toBe(0)
  expect((await api(page, `/evaluations/attempts/${state.session_id}`)).score.percentage).toBe(0)
  await checkViewport(page)
  expect(
    (await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze()).violations,
  ).toEqual([])
})

test('bank AI draft API retains human approval for MCQ, SQL and Vietnamese essay', async ({
  page,
}) => {
  test.setTimeout(180000)
  const admin = await login(page)
  const topic = await createConceptUi(page)
  await expect(
    page.locator('.app-sidebar nav').getByRole('link', { name: /Candidates/ }),
  ).toHaveCount(0)
  for (const kind of ['mcq', 'sql', 'essay']) {
    const [candidate] = await call(page, '/admin/question-candidates/generate', admin, 'POST', {
      concept_id: topic.concept_id,
      question_type: kind,
      locale: kind === 'essay' ? 'vi' : 'en',
      difficulty: 'MEDIUM',
      count: 1,
    })
    expect(candidate.promoted_question_id).toBeNull()
    expect(candidate.validation_status).toBe('validated')
    const noAttestation = await page.request.post(
      `${API}/admin/question-candidates/${candidate.candidate_id}/approve`,
      { headers: { Authorization: `Bearer ${admin}` } },
    )
    expect(noAttestation.status()).toBe(409)
    const approved = await call(
      page,
      `/admin/question-candidates/${candidate.candidate_id}/approve`,
      admin,
      'POST',
      { reviewed: true, content_hash: candidate.validation_detail.content_hash },
    )
    const question = await call(page, `/admin/questions/${approved.promoted_question_id}`, admin)
    expect(question.status).toBe('validated')
    expect(question.source).toBe('ai_generated')
    expect(question.original_locale).toBe(kind === 'essay' ? 'vi' : 'en')
    expect(question.ai_review.human_review.reviewer_id).toBeGreaterThan(0)
    expect(question.source_refs.length).toBeGreaterThan(0)
  }
})

test('bank AI draft API rejects invalid sources and duplicate promotion', async ({ page }) => {
  const admin = await login(page)
  const headers = { Authorization: `Bearer ${admin}` }
  const invalid = await createConceptUi(
    page,
    'Interpret query projection and filtering. [[GEN_INVALID]]',
  )
  const broken = await page.request.post(`${API}/admin/question-candidates/generate`, {
    headers,
    data: {
      concept_id: invalid.concept_id,
      question_type: 'mcq',
      locale: 'en',
      difficulty: 'MEDIUM',
      count: 1,
    },
  })
  expect(broken.status()).toBe(502)
  expect(
    (await call(page, '/admin/question-candidates', admin)).filter(
      (c) => c.concept_id === invalid.concept_id,
    ),
  ).toEqual([])
  const duplicate = await createConceptUi(
    page,
    'Interpret query projection and filtering. [[GEN_DUPLICATE]]',
  )
  const candidates = []
  for (let i = 0; i < 2; i++)
    candidates.push(
      (
        await call(page, '/admin/question-candidates/generate', admin, 'POST', {
          concept_id: duplicate.concept_id,
          question_type: 'mcq',
          locale: 'en',
          difficulty: 'MEDIUM',
          count: 1,
        })
      )[0],
    )
  expect(candidates[0].validation_status).toBe('validated')
  expect(candidates[1].validation_status).toBe('pending')
  const rejected = await page.request.post(
    `${API}/admin/question-candidates/${candidates[1].candidate_id}/approve`,
    {
      headers,
      data: { reviewed: true, content_hash: candidates[1].validation_detail.content_hash },
    },
  )
  expect(rejected.status()).toBe(409)
  await call(page, `/admin/question-candidates/${candidates[1].candidate_id}/reject`, admin, 'POST')
  expect(await call(page, `/admin/questions?concept_id=${duplicate.concept_id}`, admin)).toEqual([])
})
