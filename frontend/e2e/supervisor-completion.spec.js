import { start as beginPractice } from './practice-harness.js'
import { test, expect } from './browser-fixture.js'
import AxeBuilder from '@axe-core/playwright'
import { entrypointCases, call, login, PASSWORD } from './supervisor-entrypoints.js'

entrypointCases()

test('approved SQL Medium bank: automatic assembly, saved-answer navigation, language and release', async ({ page }) => {
  test.setTimeout(240_000)
  const { access_token: admin } = await call(page, '/auth/login', null, 'POST', { email: 'release-admin@test.dev', password: PASSWORD })
  const concepts = await call(page, '/admin/concepts', admin)
  const sqlSkill = concepts.find(c => c.concept_code === 'PG-JOIN-TYPES')
  expect(sqlSkill).toBeTruthy()
  const sqlBank = (await call(page, '/admin/questions?question_type=sql&difficulty=3&status=validated', admin)).filter(q => q.source === 'bank')
  const executable = sqlBank.find(q => q.concepts.some(c => c.confirmed && c.concept_id === sqlSkill.concept_id)) || sqlBank[0]
  expect(executable).toBeTruthy()
  const scope = [...new Set([sqlSkill.concept_id, ...executable.concepts.filter(c => c.confirmed).map(c => c.concept_id)])].sort((a, b) => a-b)
    const email = `sql-medium-${Date.now()}@test.dev`
    await call(page, '/auth/register', null, 'POST', { name: 'Approved SQL learner', email, password: PASSWORD, password_confirm: PASSWORD })
    const learner = await login(page, email)
    expect((await call(page, '/sessions', learner)).length).toBe(0)
    let state = await beginPractice(page, 'bank', 3, { concept_ids: scope, difficulties: ['MEDIUM'] })
    expect(state.max_questions).toBe(3)
    expect(state.selected_concept_ids).toEqual(scope)
    const sid = state.session_id, expires = state.expires_at, kinds = new Set(), ids = new Set()
    for (let i = 0; i < 3; i++) {
      const q = state.current_question
      kinds.add(q.question_type); ids.add(q.question_id)
      expect(q.difficulty_level).toBe(3)
      const key = await call(page, `/admin/questions/${q.question_id}`, admin)
      expect(key.concepts.filter(c => c.confirmed).every(c => scope.includes(c.concept_id))).toBe(true)
      await expect(page.getByText(q.prompt, { exact: true })).toBeVisible()
      if (q.question_type === 'mcq') await page.locator(`input[value="${key.options.find(o => o.is_correct).option_id}"]`).locator('..').click()
      else await page.getByLabel(q.question_type === 'sql' ? 'Your query' : 'Your answer', { exact: true }).fill(key.reference_answer || key.rubrics.map(r => r.criteria).join('\n'))
      if (i > 0) {
        await page.getByRole('button', { name: 'Go to question 1', exact: true }).click()
        await expect(page.getByText('Your submitted answer is saved. Submitted answers cannot be changed.', { exact: true })).toBeVisible()
        expect((await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze()).violations).toEqual([])
        await page.getByRole('button', { name: 'Language', exact: true }).click()
        await page.getByRole('menuitemradio', { name: 'Tiếng Việt', exact: true }).click()
        await expect(page.getByText('Câu trả lời đã nộp được lưu an toàn và không thể chỉnh sửa.', { exact: true })).toBeVisible()
        await page.getByRole('button', { name: 'Ngôn ngữ', exact: true }).click()
        await page.getByRole('menuitemradio', { name: 'English', exact: true }).click()
        await page.getByRole('button', { name: 'Return to current question', exact: true }).click()
        const authoritative = await call(page, `/sessions/${sid}`, learner)
        expect(authoritative.expires_at).toBe(expires)
        expect(authoritative.answered_count).toBe(i)
        expect(authoritative.current_question.question_id).toBe(q.question_id)
        if (q.question_type !== 'mcq') await expect(page.getByRole('textbox')).toHaveValue(key.reference_answer || key.rubrics.map(r => r.criteria).join('\n'))
      }
      const submitting = page.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith(`/sessions/${sid}/submit`))
      await page.getByRole('button', { name: 'Submit answer & continue', exact: true }).click()
      const submitted = await submitting
      expect(submitted.status()).toBe(200)
      const payload = submitted.request().postDataJSON()
      state = (await submitted.json()).state
      expect(state.answered_count).toBe(i + 1)
      const retry = await call(page, `/sessions/${sid}/submit`, learner, 'POST', payload)
      expect(retry.state.answered_count).toBe(i + 1)
    }
    expect([...kinds].sort()).toEqual(['essay', 'mcq', 'sql'])
    expect(ids.size).toBe(3)
    expect((await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze()).violations).toEqual([])
    await page.getByRole('button', { name: 'Finish assessment', exact: true }).first().click()
    await page.getByRole('button', { name: 'Yes, finish', exact: true }).click()
    await expect(page).toHaveURL(new RegExp(`/evaluations/${sid}$`))
    await expect(page.getByRole('heading', { name: 'Nhận xét từng câu' })).toBeVisible({ timeout: 45000 })
    const result = await call(page, `/sessions/${sid}/evidence`, learner)
    expect(result.items).toHaveLength(3)
    const profile = await call(page, '/sessions/competency/cumulative', learner)
    expect(profile.summary.finalized_assessments).toBe(1)
    const evidencedConcepts = [...new Set(result.items.flatMap(item => item.concepts.map(c => c.concept_id)))].sort((a, b) => a-b)
    expect(profile.concepts.map(c => c.concept_id).sort((a, b) => a-b)).toEqual(evidencedConcepts)
    await page.goto('/competency')
    await expect(page.getByText('Làm thêm bài để xem xu hướng', { exact: true })).toBeVisible()
    expect((await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze()).violations).toEqual([])
})
