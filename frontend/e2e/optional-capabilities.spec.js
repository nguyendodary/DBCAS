import { test, expect } from './browser-fixture.js'
import { adaptiveAcceptance, call, createConceptUi, login, API } from './optional-capabilities.js'

adaptiveAcceptance(test)

test('AI authoring: MCQ, SQL and Vietnamese essay remain drafts until an identified human approves', async ({ page }) => {
  test.setTimeout(180_000)
  const admin = await login(page)
  const topic = await createConceptUi(page)
  await page.goto('/admin/questions')
  await page.getByRole('link', { name: 'Generate candidates', exact: true }).click()
  await expect(page).toHaveURL(/\/admin\/candidates$/)
  await page.getByRole('combobox', { name: 'Concept', exact: true }).selectOption(String(topic.concept_id))
  for (const kind of ['mcq', 'sql', 'essay']) {
    await page.getByRole('combobox', { name: 'Type', exact: true }).selectOption(kind)
    await page.getByRole('combobox', { name: 'Question language', exact: true }).selectOption(kind === 'essay' ? 'vi' : 'en')
    const response = page.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith('/question-candidates/generate'))
    await page.getByRole('button', { name: 'Generate', exact: true }).click()
    const result = await response
    expect(result.status()).toBe(201)
    const candidate = (await result.json())[0]
    expect(candidate.promoted_question_id).toBeNull()
    expect(candidate.validation_status).toBe('validated')
    expect((await call(page, `/admin/questions?concept_id=${topic.concept_id}`, admin)).length).toBe(['mcq', 'sql', 'essay'].indexOf(kind))
    await expect(page.getByRole('button', { name: 'Approve into bank', exact: true })).toBeDisabled()
    const noAttestation = await page.request.post(`${API}/admin/question-candidates/${candidate.candidate_id}/approve`, { headers: { Authorization: `Bearer ${admin}` } })
    expect(noAttestation.status()).toBe(409)
    await page.getByRole('checkbox', { name: /I have checked the answer/ }).check()
    const approval = page.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith(`/question-candidates/${candidate.candidate_id}/approve`))
    await page.getByRole('button', { name: 'Approve into bank', exact: true }).click()
    const approvedResponse = await approval
    expect(approvedResponse.status()).toBe(200)
    const approved = await approvedResponse.json()
    const question = await call(page, `/admin/questions/${approved.promoted_question_id}`, admin)
    expect(question.status).toBe('validated')
    expect(question.source).toBe('ai_generated')
    expect(question.original_locale).toBe(kind === 'essay' ? 'vi' : 'en')
    expect(question.ai_review.human_review.reviewer_id).toBeGreaterThan(0)
    expect(question.source_refs.length).toBeGreaterThan(0)
    await expect(page.getByText(/promoted → question/)).toBeVisible()
  }
})

test('AI authoring: invalid sources are rejected and duplicate drafts cannot be approved', async ({ page }) => {
  test.setTimeout(120_000)
  const admin = await login(page)
  const invalid = await createConceptUi(page, 'Interpret query projection and filtering. [[GEN_INVALID]]')
  await page.goto('/admin/candidates')
  await page.getByRole('combobox', { name: 'Concept', exact: true }).selectOption(String(invalid.concept_id))
  const invalidResponse = page.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith('/question-candidates/generate'))
  await page.getByRole('button', { name: 'Generate', exact: true }).click()
  expect((await invalidResponse).status()).toBe(502)
  await expect(page.getByRole('alert').first()).toBeVisible()
  expect((await call(page, '/admin/question-candidates', admin)).filter(c => c.concept_id === invalid.concept_id)).toEqual([])
  const duplicate = await createConceptUi(page, 'Interpret query projection and filtering. [[GEN_DUPLICATE]]')
  await page.goto('/admin/candidates')
  await page.getByRole('combobox', { name: 'Concept', exact: true }).selectOption(String(duplicate.concept_id))
  const candidates = []
  for (let i = 0; i < 2; i++) {
    const response = page.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith('/question-candidates/generate'))
    await page.getByRole('button', { name: 'Generate', exact: true }).click()
    const result = await response
    expect(result.status()).toBe(201)
    candidates.push((await result.json())[0])
  }
  expect(candidates[0].validation_status).toBe('validated')
  expect(candidates[1].validation_status).toBe('pending')
  await expect(page.getByRole('button', { name: 'Approve into bank', exact: true })).toHaveCount(0)
  const rejected = await page.request.post(`${API}/admin/question-candidates/${candidates[1].candidate_id}/approve`, { headers: { Authorization: `Bearer ${admin}` },
    data: { reviewed: true, content_hash: candidates[1].validation_detail.content_hash } })
  expect(rejected.status()).toBe(409)
  await page.getByRole('button', { name: 'Reject', exact: true }).click()
  await expect(page.getByText('Rejected.', { exact: true })).toBeVisible()
  expect((await call(page, `/admin/questions?concept_id=${duplicate.concept_id}`, admin))).toEqual([])
})
