import { test, expect, request as apiRequest } from './browser-fixture.js'
import AxeBuilder from '@axe-core/playwright'

const API = 'http://127.0.0.1:8100'
const PASSWORD = 'ReleaseTest123!'

test('supervisor journeys A–E: classification, personalization, both release policies and cumulative evidence', async ({ page, browser, browserDiagnostics }) => {
  test.setTimeout(360_000)
  const errors = []
  page.on('pageerror', e => errors.push(e.message))
  const api = await apiRequest.newContext({ baseURL: API, timeout: 30_000 })
  const adminContext = await browser.newContext()
  browserDiagnostics.observe(adminContext)
  const adminPage = await adminContext.newPage()
  adminPage.on('pageerror', e => errors.push(e.message))
  const unique = `supervisor-${Date.now()}`
  async function request(route, { token, method = 'GET', data } = {}) {
    const response = await api.fetch(route, { method, data, headers: { Connection: 'close', ...(token ? { Authorization: `Bearer ${token}` } : {}) } })
    expect(response.ok(), `${method} ${route}: ${await response.text()}`).toBeTruthy()
    return response.status() === 204 ? null : response.json()
  }
  async function login(target, email) {
    await target.addInitScript(() => localStorage.setItem('dbcas_locale', 'en'))
    await target.goto('/login')
    await target.getByLabel('Email', { exact: true }).fill(email)
    await target.getByLabel('Password', { exact: true }).fill(PASSWORD)
    await target.getByRole('button', { name: 'Sign in', exact: true }).click()
    await expect(target).toHaveURL(email === 'release-admin@test.dev' ? /\/admin$/ : /\/dashboard$/)
    return target.evaluate(() => localStorage.getItem('dbcas_token'))
  }
  try {
    const admin = await login(adminPage, 'release-admin@test.dev')
    const questions = await request('/api/v1/admin/questions?status=validated', { token: admin })
    const sources = {}
    for (const kind of ['mcq', 'sql', 'essay']) {
      sources[kind] = await request(`/api/v1/admin/questions/${questions.find(q => q.question_type === kind).question_id}`, { token: admin })
    }
    const conceptIds = [...new Set(Object.values(sources).flatMap(q => q.concepts.filter(c => c.confirmed).map(c => c.concept_id)))]
    const assessmentIds = {}
    await test.step('Journey E: classify a bank item and configure shared release rules in the administrator UI', async () => {
      let first
      for (const [kind, count] of [['mcq', 10], ['sql', 2], ['essay', 1], ['opening', 3]]) {
        const source = sources[kind === 'opening' ? 'mcq' : kind]
        for (let i = 0; i < count; i++) {
          const result = await request('/api/v1/admin/questions', { token: admin, method: 'POST', data: {
            question_type: source.question_type, prompt: `${unique} ${kind} ${i}: ${source.prompt}`,
            reference_answer: source.reference_answer, points: source.points,
            explanation: source.explanation,
            difficulty_level: kind === 'opening' || kind === 'mcq' && i === 0 ? 1 : 3,
            concept_ids: source.concepts.filter(c => c.confirmed).map(c => c.concept_id),
            required_concept_ids: source.concepts.filter(c => c.confirmed && c.is_required).map(c => c.concept_id),
            options: source.options.map(({ option_label, option_text, is_correct }) => ({ option_label, option_text, is_correct })),
            datasets: source.datasets.map(({ dataset_name, setup_sql, expected_result, is_edge_case }) => ({ dataset_name, setup_sql, expected_result, is_edge_case })),
            rubrics: source.rubrics.map(({ level_name, min_score, max_score, criteria }) => ({ level_name, min_score, max_score, criteria })),
            translations: source.translations.filter(item => item.current).map(item => ({
              locale: item.locale, prompt: `${unique} ${kind} ${i}: ${item.prompt}`,
              explanation: item.explanation, option_texts: item.option_texts, rubrics: item.rubrics,
            })),
          } })
          if (kind === 'mcq' && i === 0) first = result
          else await request(`/api/v1/admin/questions/${result.question_id}`, { token: admin, method: 'PATCH', data: { status: 'validated' } })
        }
      }
      await adminPage.goto('/admin/questions')
      await adminPage.getByLabel('Search prompt', { exact: true }).fill(first.prompt)
      const row = adminPage.locator('li').filter({ hasText: first.prompt })
      await row.getByRole('button', { name: 'Details', exact: true }).click()
      await row.getByRole('button', { name: 'Edit', exact: true }).click()
      await adminPage.getByLabel('Difficulty', { exact: true }).selectOption('3')
      for (const concept of first.concepts.filter(c => c.confirmed)) {
        const name = `${concept.concept_name} (${concept.concept_code})`
        await adminPage.getByRole('checkbox', { name, exact: true }).check()
      }
      const saved = adminPage.waitForResponse(r => r.request().method() === 'PUT' && r.url().endsWith(`/admin/questions/${first.question_id}`))
      await adminPage.getByRole('button', { name: 'Save changes', exact: true }).click()
      const savedResponse = await saved
      expect(savedResponse.status()).toBe(200)
      const classified = await savedResponse.json()
      expect(classified.difficulty_level).toBe(3)
      expect(classified.concepts.filter(c => c.confirmed).map(c => c.concept_id).sort((a, b) => a - b))
        .toEqual(first.concepts.filter(c => c.confirmed).map(c => c.concept_id).sort((a, b) => a - b))
      await row.getByRole('button', { name: 'Actions', exact: true }).click()
      await adminPage.getByRole('menuitem', { name: 'Validate', exact: true }).click()
      await expect(row).toContainText('Validated')
      for (const policy of ['IMMEDIATE', 'HUMAN_VERIFIED']) {
        await adminPage.goto('/admin/assessments')
        await adminPage.getByRole('button', { name: 'New assessment', exact: true }).click()
        await adminPage.getByLabel('Assessment title', { exact: true }).fill(`${unique} ${policy}`)
        await adminPage.getByLabel('Result release policy', { exact: true }).selectOption(policy)
        for (const [index, cid] of conceptIds.entries()) {
          if (index) await adminPage.getByRole('button', { name: '+ add concept', exact: true }).click()
          await adminPage.getByLabel(`Target concept ${index + 1}`, { exact: true }).selectOption(String(cid))
        }
        const created = adminPage.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith('/admin/assessments'))
        await adminPage.getByRole('button', { name: 'Create draft', exact: true }).click()
        assessmentIds[policy] = (await (await created).json()).assessment_id
        const rule = adminPage.locator('li').filter({ hasText: `${unique} ${policy}` })
        await rule.getByRole('button', { name: 'Publish', exact: true }).click()
        await expect(rule).toContainText('Published')
      }
    })
    const email = `${unique}@test.dev`
    await request('/api/v1/auth/register', { method: 'POST', data: { name: 'Supervisor browser learner', email, password: PASSWORD, password_confirm: PASSWORD } })
    const learner = await login(page, email)
    for (const policy of ['IMMEDIATE', 'HUMAN_VERIFIED']) {
      let sid
      await test.step(`Journey A: learner chooses skills and medium difficulty (${policy})`, async () => {
        await page.goto('/assessments')
        await page.getByText('Assessment options', { exact: true }).click()
        await page.getByLabel('Assessment format', { exact: true }).selectOption('FORMAL')
        await page.getByLabel('Assessment rules', { exact: true }).selectOption(String(assessmentIds[policy]))
        await page.getByRole('button', { name: 'Select all skills (comprehensive)', exact: true }).click()
        await page.getByRole('radio', { name: 'Medium', exact: true }).check()
        await page.getByRole('button', { name: 'Start assessment', exact: true }).click()
        await expect(page).toHaveURL(/\/exam\/\d+$/)
        sid = Number(page.url().split('/').at(-1))
        const seen = new Set()
        for (let i = 0; i < 13; i++) {
          const state = await request(`/api/v1/sessions/${sid}`, { token: learner })
          const q = state.current_question
          expect(q.difficulty_level).toBe(3)
          expect(seen.has(q.question_id)).toBe(false)
          seen.add(q.question_id)
          const key = await request(`/api/v1/admin/questions/${q.question_id}`, { token: admin })
          await expect(page.getByText(q.prompt, { exact: true })).toBeVisible()
          if (q.question_type === 'mcq') {
            const option = key.options.find(o => o.is_correct)
            await page.locator(`input[value="${option.option_id}"]`).locator('..').click()
          } else {
            const answer = key.reference_answer || key.rubrics.map(r => r.criteria).join('\n')
            expect(typeof answer).toBe('string')
            expect(answer.length).toBeGreaterThan(0)
            await page.getByLabel(q.question_type === 'sql' ? 'Your query' : 'Your answer', { exact: true }).fill(answer)
          }
          if (i === 0) {
            await page.getByRole('button', { name: 'Save draft', exact: true }).click()
            await expect.poll(async () => (await request(`/api/v1/sessions/${sid}/draft?question_id=${q.question_id}`, { token: learner })).revision).toBeGreaterThan(0)
            await page.reload()
            await expect(page.getByText(q.prompt, { exact: true })).toBeVisible()
          }
          const submitted = page.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith(`/sessions/${sid}/submit`))
          await page.getByRole('button', { name: 'Submit answer & continue', exact: true }).click()
          const result = await (await submitted).json()
          expect(result.state.answered_count).toBe(i + 1)
          if (policy === 'HUMAN_VERIFIED') { expect(result.answer.score).toBeNull(); expect(result.answer.is_correct).toBeNull() }
        }
        await page.getByRole('button', { name: 'Finish assessment', exact: true }).first().click()
        await page.getByRole('button', { name: 'Yes, finish', exact: true }).click()
        await expect(page).toHaveURL(new RegExp(`/history/${sid}$`))
      })
      await test.step(policy === 'IMMEDIATE' ? 'Journey B: immediate official results' : 'Journey C: pending, grader correction and explicit publication', async () => {
        await page.goto(`/history/${sid}`)
        if (policy === 'HUMAN_VERIFIED') {
          await expect(page.getByRole('heading', { name: 'Your submission is received', exact: true })).toBeVisible()
          const history = await request('/api/v1/sessions', { token: learner })
          expect(history.find(s => s.session_id === sid).concepts).toEqual([])
          const review = await request(`/api/v1/admin/grading-reviews/${sid}`, { token: admin })
          await adminPage.goto('/admin/grading')
          await adminPage.getByRole('button', { name: new RegExp(`${unique} HUMAN_VERIFIED`) }).click()
          await expect(adminPage.getByRole('button', { name: 'Publish verified results' })).toBeDisabled()
          for (const item of review.items.filter(i => ['sql', 'essay'].includes(i.question_type))) {
            const card = adminPage.getByRole('heading', { name: item.prompt, exact: true }).locator('..')
            if (item.question_type === 'essay') {
              await card.getByLabel('Approved score', { exact: true }).fill('0')
              await card.getByLabel('Grader comments', { exact: true }).fill('Corrected against the supplied rubric during browser verification')
            }
            const approved = adminPage.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith(`/attempts/${item.attempt_id}`))
            await card.getByRole('button', { name: 'Approve score', exact: true }).click()
            expect((await approved).status()).toBe(200)
          }
          await expect(adminPage.getByRole('button', { name: 'Publish verified results' })).toBeEnabled()
          await adminPage.getByRole('button', { name: 'Publish verified results' }).click()
          await expect(adminPage.getByRole('status')).toHaveText('Published')
          await page.getByRole('button', { name: 'Refresh status' }).click()
        }
        await expect(page.getByRole('heading', { name: 'Assessment evidence', exact: true })).toBeVisible()
        const evidence = await request(`/api/v1/sessions/${sid}/evidence`, { token: learner })
        expect(evidence.items).toHaveLength(13)
        expect(evidence.items.every(i => i.score !== null)).toBe(true)
      })
    }
    await test.step('Journey D: multiple published assessments contribute to cumulative competency', async () => {
      await page.goto('/competency')
      await expect(page.getByText('2 published assessments', { exact: true })).toBeVisible()
      await expect(page.locator('canvas')).toHaveCount(1)
      const cumulative = await request('/api/v1/sessions/competency/cumulative', { token: learner })
      expect(cumulative.summary.finalized_assessments).toBe(2)
      expect(cumulative.concepts.some(c => c.contributing_sessions.length === 2)).toBe(true)
      for (const width of [390, 1440]) {
        await page.setViewportSize({ width, height: 1000 })
        expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width + 1)
        const scan = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze()
        expect(scan.violations).toEqual([])
      }
    })
    expect(errors).toEqual([])
  } finally {
    await adminContext.close()
    await api.dispose()
  }
})

test('single-topic practice works with the existing approved bank at a narrow viewport', async ({ page }) => {
  const api = await apiRequest.newContext({ baseURL: API, timeout: 30_000 })
  async function call(path, token, data) {
    const response = await api.fetch(path, { method: data ? 'POST' : 'GET', data,
      headers: token ? { Authorization: `Bearer ${token}` } : {} })
    expect(response.ok(), `${path}: ${await response.text()}`).toBeTruthy()
    return response.json()
  }
  try {
    const { access_token: admin } = await call('/api/v1/auth/login', null, { email: 'release-admin@test.dev', password: PASSWORD })
    const bank = await call('/api/v1/admin/questions?status=validated', admin)
    const email = `single-topic-${Date.now()}@test.dev`
    await call('/api/v1/auth/register', null, { name: 'Single topic learner', email, password: PASSWORD, password_confirm: PASSWORD })
    await page.goto('/login')
    await page.evaluate(() => localStorage.setItem('dbcas_locale', 'en'))
    await page.reload()
    await page.getByLabel('Email', { exact: true }).fill(email)
    await page.getByLabel('Password', { exact: true }).fill(PASSWORD)
    await page.getByRole('button', { name: 'Sign in', exact: true }).click()
    await expect(page).toHaveURL(/\/dashboard$/)
    const learner = await page.evaluate(() => localStorage.getItem('dbcas_token'))
    const rules = (await call('/api/v1/assessments', learner)).filter(a => a.result_release_policy === 'IMMEDIATE')
    const addedConcepts = new Set(bank.filter(q => q.prompt.startsWith('supervisor-')).flatMap(q => q.concepts.map(c => c.concept_id)))
    const choices = rules.flatMap(rule => rule.concepts.filter(c => bank.some(q => q.question_type === 'mcq' && q.difficulty_level <= 2 && !q.prompt.startsWith('supervisor-') && q.concepts.some(tag => tag.confirmed && tag.concept_id === c.concept_id))).map(concept => ({ rule, concept })))
    const choice = choices.find(({ concept }) => !addedConcepts.has(concept.concept_id)) || choices[0]
    expect(choice).toBeTruthy()
    await page.setViewportSize({ width: 390, height: 900 })
    await page.goto('/assessments')
    await page.getByText('Assessment options', { exact: true }).click()
    await page.getByLabel('Assessment rules', { exact: true }).selectOption(String(choice.rule.assessment_id))
    await page.getByLabel('Assessment format', { exact: true }).selectOption('PRACTICE')
    await page.getByLabel('Number of questions', { exact: true }).selectOption('1')
    const index = choice.rule.concepts.findIndex(c => c.concept_id === choice.concept.concept_id)
    await page.getByRole('checkbox').nth(index).check()
    expect((await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze()).violations).toEqual([])
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(391)
    await page.getByRole('button', { name: 'Start assessment', exact: true }).click()
    await expect(page).toHaveURL(/\/exam\/\d+$/)
    const sid = Number(page.url().split('/').at(-1))
    const state = await call(`/api/v1/sessions/${sid}`, learner)
    expect(state.max_questions).toBe(1)
    expect(state.selected_concept_ids).toEqual([choice.concept.concept_id])
    expect(state.current_question.difficulty_level).toBeLessThanOrEqual(2)
    const key = await call(`/api/v1/admin/questions/${state.current_question.question_id}`, admin)
    await page.locator(`input[value="${key.options.find(o => o.is_correct).option_id}"]`).locator('..').click()
    await page.getByRole('button', { name: 'Submit answer & continue', exact: true }).click()
    await expect(page.getByText('All questions served', { exact: true })).toBeVisible()
    await page.getByRole('button', { name: 'Finish assessment', exact: true }).first().click()
    await page.getByRole('button', { name: 'Yes, finish', exact: true }).click()
    await expect(page).toHaveURL(new RegExp(`/history/${sid}$`))
    await page.goto(`/history/${sid}`)
    await expect(page.getByRole('heading', { name: 'Assessment evidence', exact: true })).toBeVisible()
    expect((await call(`/api/v1/sessions/${sid}/evidence`, learner)).items).toHaveLength(1)
  } finally { await api.dispose() }
})
