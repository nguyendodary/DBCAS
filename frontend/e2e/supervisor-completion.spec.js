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
  // Reuse actual reviewed questions and existing curriculum; only the
  // disposable assessment configuration is new, with no fabricated items.
  const adminRules = await call(page, '/admin/assessments', admin)
  // Other journeys create additional published rules. Bind to the seeded
  // benchmark rather than whichever unrelated fixture happens to sort first.
  const benchmark = adminRules.find(a => a.assessment_id === 1 && a.status === 'published')
  expect(benchmark).toBeTruthy()
  const baseline = await call(page, `/admin/assessments/${benchmark.assessment_id}`, admin)
  expect(baseline.concepts.some(c => c.concept_id === sqlSkill.concept_id)).toBe(false)
  const rule = await call(page, '/admin/assessments', admin, 'POST', {
    title: `Approved SQL bank ${Date.now()}`, result_release_policy: 'IMMEDIATE',
    concepts: [...baseline.concepts.map(c => ({ concept_id: c.concept_id, min_difficulty: 1, max_difficulty: 5, target_pct: 60 })),
      { concept_id: sqlSkill.concept_id, min_difficulty: 1, max_difficulty: 5, target_pct: 60 }],
  })
  await call(page, `/admin/assessments/${rule.assessment_id}`, admin, 'PATCH', { status: 'published' })
  try {
    // The area-wide practice selection is feasible within this published rule;
    // exercise it with a disposable learner so the main learner's competency
    // evidence below still contains exactly one finalized assessment.
    const stamp = Date.now()
    const areaEmail = `sql-area-${stamp}@test.dev`
    await call(page, '/auth/register', null, 'POST', { name: 'Area SQL learner', email: areaEmail, password: PASSWORD, password_confirm: PASSWORD })
    await login(page, areaEmail)
    await page.goto('/assessments')
    await expect(page.getByRole('heading', { name: 'Assess your database skills', exact: true })).toBeVisible()
    await expect(page.getByLabel('Number of questions', { exact: true })).not.toBeVisible()
    await page.getByText('Assessment options', { exact: true }).click()
    await page.getByLabel('Assessment rules', { exact: true }).selectOption(String(rule.assessment_id))
    await page.getByRole('button', { name: 'SQL Querying', exact: true }).click()
    await page.getByRole('radio', { name: 'Easy', exact: true }).focus()
    await page.keyboard.press('ArrowRight')
    await expect(page.getByRole('radio', { name: 'Medium', exact: true })).toBeChecked()
    await page.getByRole('radio', { name: 'Medium', exact: true }).check()
    const areaStart = page.waitForResponse(r => r.request().method() === 'POST' && /\/assessments\/\d+\/sessions$/.test(new URL(r.url()).pathname))
    await page.getByRole('button', { name: 'Start assessment', exact: true }).click()
    const areaResponse = await areaStart
    expect(areaResponse.status()).toBe(201)
    const areaState = await areaResponse.json()
    expect(areaState.selected_concept_ids).toEqual(rule.concepts.filter(c => c.subject_area === 'SQL Querying').map(c => c.concept_id).sort((a, b) => a - b))
    await expect(page).toHaveURL(/\/exam\/\d+$/)
    const areaSid = Number(page.url().split('/').at(-1))
    await page.getByRole('button', { name: 'Finish assessment', exact: true }).first().click()
    await page.getByRole('button', { name: 'Yes, finish', exact: true }).click()
    await expect(page).toHaveURL(new RegExp(`/history/${areaSid}$`))

    const email = `sql-medium-${stamp}@test.dev`
    await call(page, '/auth/register', null, 'POST', { name: 'Approved SQL learner', email, password: PASSWORD, password_confirm: PASSWORD })
    const learner = await login(page, email)
    await page.goto('/assessments')
    expect((await call(page, '/sessions', learner)).length).toBe(0)
    // Auto-selection would pick the first template that already carries the
    // skill; pin the newly approved rule so the start payload is deterministic.
    const options = page.locator('details').filter({ hasText: 'Assessment options' })
    if (!(await options.evaluate((node) => node.open))) await page.getByText('Assessment options', { exact: true }).click()
    await page.getByLabel('Assessment rules', { exact: true }).selectOption(String(rule.assessment_id))
    await page.getByRole('searchbox', { name: 'Search skills' }).fill(sqlSkill.concept_name)
    await page.getByRole('checkbox', { name: sqlSkill.concept_name, exact: true }).check()
    await page.getByRole('radio', { name: 'Medium', exact: true }).check()
    const starting = page.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith(`/assessments/${rule.assessment_id}/sessions`))
    await page.getByRole('button', { name: 'Start assessment', exact: true }).click()
    const response = await starting
    expect(response.status()).toBe(201)
    expect(response.request().postDataJSON().question_count).toBeNull()
    let state = await response.json()
    expect(state.max_questions).toBe(3)
    expect(state.selected_concept_ids).toEqual([sqlSkill.concept_id])
    const sid = state.session_id, expires = state.expires_at, kinds = new Set(), ids = new Set()
    for (let i = 0; i < 3; i++) {
      const q = state.current_question
      kinds.add(q.question_type); ids.add(q.question_id)
      expect(q.difficulty_level).toBe(3)
      const key = await call(page, `/admin/questions/${q.question_id}`, admin)
      expect(key.concepts.some(c => c.confirmed && c.concept_id === sqlSkill.concept_id)).toBe(true)
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
    await expect(page).toHaveURL(new RegExp(`/history/${sid}$`))
    const result = await call(page, `/sessions/${sid}/evidence`, learner)
    expect(result.items).toHaveLength(3)
    // This run uses the default PRACTICE format: its graded evidence stays
    // readable but must never enter official cumulative competency.
    const profile = await call(page, '/sessions/competency/cumulative', learner)
    expect(profile.summary.finalized_assessments).toBe(0)
    expect(profile.concepts).toEqual([])
    await page.goto('/competency')
    await expect(page.getByText('No published competency evidence yet', { exact: true })).toBeVisible()
    expect((await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze()).violations).toEqual([])
  } finally {
    await call(page, `/admin/assessments/${rule.assessment_id}`, admin, 'PATCH', { status: 'closed' })
  }
})
