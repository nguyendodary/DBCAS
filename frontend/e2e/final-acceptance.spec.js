import { test, expect, request as apiRequest } from '@playwright/test'

const PASSWORD = 'ReleaseTest123!'

test('final acceptance: single, multiple and comprehensive skills, resume, retries and reserved bank editing', async ({ page, browser }) => {
  test.setTimeout(360_000)
  const api = await apiRequest.newContext({ baseURL: 'http://127.0.0.1:8100', timeout: 30_000 })
  const adminContext = await browser.newContext()
  const adminPage = await adminContext.newPage()
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  adminPage.on('pageerror', error => errors.push(error.message))
  const unique = `acceptance-${Date.now()}`
  let ownedRuleId, adminToken
  async function call(path, token, method = 'GET', data) {
    const response = await api.fetch(path, { method, data, headers: token ? { Authorization: `Bearer ${token}` } : {} })
    expect(response.ok(), `${method} ${path}: ${await response.text()}`).toBeTruthy()
    return response.json()
  }
  async function login(target, email) {
    await target.goto('/login')
    await target.evaluate(() => localStorage.setItem('dbcas_locale', 'en'))
    await target.reload()
    await target.getByLabel('Email', { exact: true }).fill(email)
    await target.getByLabel('Password', { exact: true }).fill(PASSWORD)
    await target.getByRole('button', { name: 'Sign in', exact: true }).click()
    await expect(target).toHaveURL(email === 'release-admin@test.dev' ? /\/admin$/ : /\/dashboard$/)
    return target.evaluate(() => localStorage.getItem('dbcas_token'))
  }
  try {
    const admin = await login(adminPage, 'release-admin@test.dev')
    adminToken = admin
    const bank = await call('/api/v1/admin/questions?status=validated', admin)
    const sources = {}
    for (const kind of ['mcq', 'sql', 'essay']) {
      sources[kind] = await call(`/api/v1/admin/questions/${bank.find(q => q.question_type === kind).question_id}`, admin)
    }
    const topics = []
    for (let i = 0; i < 3; i++) {
      topics.push(await call('/api/v1/admin/concepts', admin, 'POST', {
        concept_code: `${unique}-${i}`, concept_name: `${unique} skill ${i + 1}`, subject_area: 'SQL',
        description: 'Isolated acceptance fixture copied from the reviewed SQL bank.',
        keywords: ['SELECT'], learning_objectives: ['Interpret the supplied query and evidence'],
      }))
    }
    const sourcePayload = (source, prompt, difficulty, conceptIds) => ({
      question_type: source.question_type, prompt, difficulty_level: difficulty, points: source.points,
      reference_answer: source.reference_answer, explanation: source.explanation,
      concept_ids: conceptIds, required_concept_ids: [],
      options: source.options.map(({ option_label, option_text, is_correct }) => ({ option_label, option_text, is_correct })),
      datasets: source.datasets.map(({ dataset_name, setup_sql, expected_result, is_edge_case }) => ({ dataset_name, setup_sql, expected_result, is_edge_case })),
      rubrics: source.rubrics.map(({ level_name, min_score, max_score, criteria }) => ({ level_name, min_score, max_score, criteria })),
      translations: source.translations.filter(item => item.current).map(item => ({
        locale: item.locale, prompt: `${unique}: ${item.prompt}`, explanation: item.explanation,
        option_texts: item.option_texts, rubrics: item.rubrics,
      })),
    })
    // All mutations belong to this disposable browser fixture's own records.
    for (const [kind, count] of [['mcq', 10], ['sql', 2], ['essay', 1]]) {
      for (let i = 0; i < count; i++) {
        const source = sources[kind]
        const question = await call('/api/v1/admin/questions', admin, 'POST',
          sourcePayload(source, `${unique} ${kind} ${i}: ${source.prompt}`, kind === 'mcq' && i < 3 ? 1 : 3,
            [topics[i % topics.length].concept_id]))
        await call(`/api/v1/admin/questions/${question.question_id}`, admin, 'PATCH', { status: 'validated' })
      }
    }
    const rule = await call('/api/v1/admin/assessments', admin, 'POST', {
      title: `${unique} shared rules`, result_release_policy: 'IMMEDIATE',
      concepts: topics.map(c => ({ concept_id: c.concept_id, min_difficulty: 1, max_difficulty: 3, target_pct: 70 })),
    })
    ownedRuleId = rule.assessment_id
    await call(`/api/v1/admin/assessments/${rule.assessment_id}`, admin, 'PATCH', { status: 'published' })
    const email = `${unique}@test.dev`
    await call('/api/v1/auth/register', null, 'POST', {
      name: 'Isolated final acceptance learner', email, password: PASSWORD, password_confirm: PASSWORD,
    })
    const learner = await login(page, email)
    const sessions = []
    for (const count of [1, 2, 3]) {
      await page.goto('/assessments')
      await page.getByLabel('Assessment rules', { exact: true }).selectOption(String(rule.assessment_id))
      await page.getByLabel('Assessment format', { exact: true }).selectOption('PRACTICE')
      await page.getByLabel('Number of questions', { exact: true }).selectOption(String(count))
      if (count === 3) await page.getByRole('button', { name: 'Select all skills (comprehensive)', exact: true }).click()
      else for (const topic of topics.slice(0, count)) await page.getByLabel(new RegExp(`${topic.concept_name}`)).check()
      const starting = page.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith(`/assessments/${rule.assessment_id}/sessions`))
      await page.getByRole('button', { name: 'Start personalized assessment', exact: true }).click()
      const startResponse = await starting
      expect(startResponse.status()).toBe(201)
      const selection = startResponse.request().postDataJSON()
      await expect(page).toHaveURL(/\/exam\/\d+$/)
      const sid = Number(page.url().split('/').at(-1))
      sessions.push(sid)
      const retry = await call(`/api/v1/assessments/${rule.assessment_id}/sessions`, learner, 'POST', selection)
      expect(retry.session_id).toBe(sid)
      const seen = new Set()
      const answers = []
      for (let i = 0; i < count; i++) {
        const before = await call(`/api/v1/sessions/${sid}`, learner)
        const question = before.current_question
        expect(question.difficulty_level).toBe(1)
        expect(before.selected_concept_ids).toEqual(topics.slice(0, count).map(c => c.concept_id))
        expect(seen.has(question.question_id)).toBe(false)
        seen.add(question.question_id)
        const original = await call(`/api/v1/admin/questions/${question.question_id}`, admin)
        expect(original.concepts.filter(c => c.confirmed).every(c => selection.concept_ids.includes(c.concept_id))).toBe(true)
        const option = original.options.find(o => o.is_correct)
        if (count === 3 && i === 2) {
          await page.locator(`input[value="${option.option_id}"]`).locator('..').click()
          await page.getByRole('button', { name: 'Save draft', exact: true }).click()
          await expect.poll(async () => (await call(`/api/v1/sessions/${sid}/draft?question_id=${question.question_id}`, learner)).revision).toBeGreaterThan(0)
          await adminPage.goto('/admin/questions')
          await adminPage.getByLabel('Search prompt', { exact: true }).fill(original.prompt)
          const row = adminPage.locator('li').filter({ hasText: original.prompt })
          await row.getByRole('button', { name: 'Details', exact: true }).click()
          await row.getByRole('button', { name: 'Edit', exact: true }).click()
          await adminPage.getByLabel('Question prompt', { exact: true }).fill(`${unique} revised prompt`)
          const editing = adminPage.waitForResponse(r => r.request().method() === 'PUT' && r.url().endsWith(`/questions/${question.question_id}`))
          await adminPage.getByRole('button', { name: 'Save changes', exact: true }).click()
          const editedResponse = await editing
          expect(editedResponse.status()).toBe(200)
          expect((await editedResponse.json()).question_id).not.toBe(question.question_id)
          const deletion = await api.delete(`/api/v1/admin/questions/${question.question_id}`, { headers: { Authorization: `Bearer ${admin}` } })
          expect(deletion.status()).toBe(409)
          await page.reload()
          await expect(page.getByText(original.prompt, { exact: true })).toBeVisible()
          await expect(page.locator(`input[value="${option.option_id}"]`)).toBeChecked()
          const resumed = await call(`/api/v1/sessions/${sid}`, learner)
          expect(resumed.answered_count).toBe(2)
          expect(resumed.expires_at).toBe(before.expires_at)
          expect(resumed.remaining_seconds).toBeLessThanOrEqual(before.remaining_seconds)
          expect(resumed.current_question.question_id).toBe(question.question_id)
          expect((await call(`/api/v1/assessments/${rule.assessment_id}/sessions`, learner, 'POST', selection)).session_id).toBe(sid)
        }
        await page.locator(`input[value="${option.option_id}"]`).locator('..').click()
        const submitted = page.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith(`/sessions/${sid}/submit`))
        await page.getByRole('button', { name: 'Submit answer & continue', exact: true }).click()
        expect((await submitted).status()).toBe(200)
        answers.push({ question_id: question.question_id, selected_option_id: option.option_id })
      }
      await page.getByRole('button', { name: 'Finish assessment', exact: true }).first().click()
      await page.getByRole('button', { name: 'Yes, finish', exact: true }).click()
      await expect(page).toHaveURL(/\/dashboard$/)
      const evidence = await call(`/api/v1/sessions/${sid}/evidence`, learner)
      expect(evidence.items).toHaveLength(count)
      for (const answer of answers) expect(evidence.items.find(item => item.question_id === answer.question_id).selected_option_id).toBe(answer.selected_option_id)
      expect((await call(`/api/v1/assessments/${rule.assessment_id}/sessions`, learner, 'POST', selection)).session_id).toBe(sid)
    }
    const history = (await call('/api/v1/sessions', learner)).filter(s => s.assessment_id === rule.assessment_id)
    expect(history).toHaveLength(3)
    expect(new Set(sessions).size).toBe(3)
    for (const [index, sid] of sessions.entries()) {
      const record = history.find(s => s.session_id === sid)
      expect(record.selected_concept_ids).toEqual(topics.slice(0, index + 1).map(c => c.concept_id))
      expect(record.difficulty).toBe('EASY')
      expect(Number(record.overall_result_pct)).toBe(100)
    }
    await page.goto('/competency')
    await expect(page.getByText('3 published assessments', { exact: true })).toBeVisible()
    const cumulative = await call('/api/v1/sessions/competency/cumulative', learner)
    expect(cumulative.concepts.every(c => Number(c.competency_pct) === 100)).toBe(true)
    await page.reload()
    await expect(page.getByText('3 published assessments', { exact: true })).toBeVisible()
    expect(await call('/api/v1/sessions/competency/cumulative', learner)).toEqual(cumulative)
    expect(errors).toEqual([])
  } finally {
    if (ownedRuleId && adminToken) {
      const closed = await api.patch(`/api/v1/admin/assessments/${ownedRuleId}`, {
        headers: { Authorization: `Bearer ${adminToken}` }, data: { status: 'closed' },
      })
      expect(closed.ok()).toBeTruthy()
    }
    await adminContext.close()
    await api.dispose()
  }
})
