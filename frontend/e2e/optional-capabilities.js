import { expect } from './browser-fixture.js'
import AxeBuilder from '@axe-core/playwright'

export const API = 'http://127.0.0.1:8100/api/v1'
export const PASSWORD = 'ReleaseTest123!'
export async function call(page, path, token, method = 'GET', data) {
  const response = await page.request.fetch(`${API}${path}`, { method, data, headers: token ? { Authorization: `Bearer ${token}` } : {} })
  expect(response.ok(), `${method} ${path}: ${response.status()} ${await response.text()}`).toBeTruthy()
  return response.json()
}
export async function login(page, email = 'release-admin@test.dev') {
  await page.goto('/login')
  await page.evaluate(() => localStorage.setItem('dbcas_locale', 'en'))
  await page.reload()
  await expect(page.getByRole('heading', { name: 'Sign in to DBCAS', exact: true })).toBeVisible()
  await page.getByLabel('Email', { exact: true }).fill(email)
  await page.getByLabel('Password', { exact: true }).fill(PASSWORD)
  const response = page.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith('/auth/login'))
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  expect((await response).status()).toBe(200)
  await expect(page).toHaveURL(email === 'release-admin@test.dev' ? /\/admin$/ : /\/dashboard$/)
  await expect(page.getByRole('heading', { name: email === 'release-admin@test.dev' ? 'Cohort Overview' : 'My competency', exact: true })).toBeVisible()
  return page.evaluate(() => localStorage.getItem('dbcas_token'))
}
export async function register(page) {
  const email = `adaptive-${Date.now()}-${Math.random().toString(16).slice(2, 7)}@test.dev`
  await page.evaluate(() => localStorage.removeItem('dbcas_token'))
  await page.goto('/register')
  for (const [name, value] of [['Full name', 'Adaptive practice learner'], ['Email', email], ['Password', PASSWORD], ['Confirm password', PASSWORD]]) await page.getByLabel(name, { exact: true }).fill(value)
  await page.getByRole('button', { name: 'Register', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Sign in to DBCAS', exact: true })).toBeVisible()
  return login(page, email)
}
export async function createConceptUi(page, description = 'Interpret SELECT projection and WHERE filtering using query results.') {
  await page.goto('/admin/curriculum')
  const name = `Optional query skill ${Date.now()}-${Math.random().toString(16).slice(2, 6)}`
  await page.getByLabel('Concept name', { exact: true }).fill(name)
  await page.getByLabel('Subject area', { exact: true }).fill('SQL Querying')
  await page.getByLabel('Concept description', { exact: true }).fill(description)
  await page.getByLabel('Concept keywords (comma separated)', { exact: true }).fill('SELECT, projection, WHERE')
  await page.getByLabel('Learning objectives (one per line)', { exact: true }).fill('Distinguish result-column projection from filtering of result rows.')
  const response = page.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith('/admin/concepts'))
  await page.getByRole('button', { name: 'Add concept', exact: true }).click()
  const result = await response
  expect(result.status()).toBe(201)
  return result.json()
}

export async function seedAdaptive(page, admin) {
  const topic = await createConceptUi(page)
  const bank = await call(page, '/admin/questions?status=validated', admin)
  const sources = {}
  for (const type of ['mcq', 'sql', 'essay']) sources[type] = await call(page, `/admin/questions/${bank.find(q => q.question_type === type).question_id}`, admin)
  const keys = new Map()
  for (const [type, count] of [['mcq', 18], ['sql', 2], ['essay', 1]]) {
    const source = sources[type]
    for (let i = 0; i < count; i++) {
      const difficulty = type === 'mcq' ? [1, 3, 4][Math.floor(i / 6)] : 3
      const created = await call(page, '/admin/questions', admin, 'POST', {
        question_type: type, prompt: `${topic.concept_name} item ${i}: ${source.prompt}`, difficulty_level: difficulty,
        points: source.points, reference_answer: source.reference_answer, explanation: source.explanation,
        concept_ids: [topic.concept_id], required_concept_ids: [],
        options: source.options.map(({ option_label, option_text, is_correct }) => ({ option_label, option_text, is_correct })),
        datasets: source.datasets.map(({ dataset_name, setup_sql, expected_result, is_edge_case }) => ({ dataset_name, setup_sql, expected_result, is_edge_case })),
        rubrics: source.rubrics.map(({ level_name, min_score, max_score, criteria }) => ({ level_name, min_score, max_score, criteria })),
      })
      await call(page, `/admin/questions/${created.question_id}`, admin, 'PATCH', { status: 'validated' })
      keys.set(created.question_id, created)
    }
  }
  const rule = await call(page, '/admin/assessments', admin, 'POST', { title: `${topic.concept_name} rules`, result_release_policy: 'IMMEDIATE',
    concepts: [{ concept_id: topic.concept_id, min_difficulty: 1, max_difficulty: 5, target_pct: 70 }] })
  await call(page, `/admin/assessments/${rule.assessment_id}`, admin, 'PATCH', { status: 'published' })
  return { topic, rule, keys }
}

export async function startAdaptiveUi(page, topic) {
  await page.goto('/assessments')
  await page.getByLabel('Search skills', { exact: true }).fill(topic.concept_name)
  await page.getByRole('checkbox', { name: topic.concept_name, exact: true }).check()
  await page.getByText('Assessment options', { exact: true }).click()
  await page.getByLabel('Assessment format', { exact: true }).selectOption('ADAPTIVE')
  await expect(page.getByLabel('Number of questions')).toHaveCount(0)
  const response = page.waitForResponse(r => r.request().method() === 'POST' && /\/assessments\/\d+\/sessions$/.test(r.url()))
  await page.getByRole('button', { name: 'Start assessment', exact: true }).click()
  const result = await response
  expect(result.status()).toBe(201)
  const state = await result.json()
  await expect(page).toHaveURL(new RegExp(`/exam/${state.session_id}$`))
  return state
}

export function adaptiveAcceptance(test) {
  test('optional adaptive practice: initial batch, saved state, harder rounds and final outcome', async ({ page }) => {
    test.setTimeout(240_000)
    const admin = await login(page)
    const fixture = await seedAdaptive(page, admin)
    const learner = await register(page)
    let state = await startAdaptiveUi(page, fixture.topic)
    const expires = state.expires_at
    const seen = []
    await expect(page.getByText('Round 1 · 0 / 5 answered', { exact: false })).toBeVisible()
    await page.getByRole('button', { name: 'Help', exact: true }).click()
    await expect(page.getByRole('dialog')).toContainText('Optional adaptive practice')
    await page.keyboard.press('Escape')
    await expect(page.getByRole('button', { name: 'Help', exact: true })).toBeFocused()
    expect((await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze()).violations).toEqual([])
    for (let i = 0; i < 13; i++) {
      const q = state.current_question
      expect(q.question_type).toBe('mcq')
      expect(q.options.every(option => !Object.hasOwn(option, 'is_correct'))).toBe(true)
      seen.push(q.question_id)
      const correct = fixture.keys.get(q.question_id).options.find(option => option.is_correct)
      await page.locator(`input[value="${correct.option_id}"]`).locator('..').click()
      const response = page.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith(`/sessions/${state.session_id}/submit`))
      await page.getByRole('button', { name: 'Submit answer & continue', exact: true }).click()
      const result = await response
      expect(result.status()).toBe(200)
      state = (await result.json()).state
      if (i === 0) {
        await page.reload()
        const recovered = await call(page, `/sessions/${state.session_id}`, learner)
        expect(recovered.expires_at).toBe(expires)
        expect(recovered.answered_count).toBe(1)
        expect(recovered.current_question.question_id).toBe(state.current_question.question_id)
      }
      if (i === 4 || i === 9) {
        expect(state.adaptive_progress.round).toBe(i === 4 ? 2 : 3)
        expect(state.adaptive_progress.band).toBe(i === 4 ? 'MEDIUM' : 'HARD')
        expect(state.current_question.difficulty_level).toBe(i === 4 ? 3 : 4)
      }
    }
    expect(new Set(seen).size).toBe(13)
    expect(state.status).toBe('completed')
    expect(state.adaptive_progress.stop_reason).toBe('maximum_questions')
    await expect(page).toHaveURL(new RegExp(`/history/${state.session_id}$`))
    await expect(page.getByText('Adaptive practice completed: question limit reached.', { exact: true })).toBeVisible()
    const profile = await call(page, '/sessions/competency/cumulative', learner)
    expect(profile.concepts).toEqual([])
  })

  test('optional adaptive practice: mobile early finish reports insufficient evidence', async ({ page }) => {
    test.setTimeout(240_000)
    const admin = await login(page)
    const fixture = await seedAdaptive(page, admin)
    await register(page)
    await page.setViewportSize({ width: 390, height: 844 })
    const state = await startAdaptiveUi(page, fixture.topic)
    await page.getByRole('button', { name: 'Finish assessment', exact: true }).click()
    const dialog = page.getByRole('dialog')
    await dialog.getByRole('button', { name: 'Yes, finish', exact: true }).click()
    await expect(page).toHaveURL(new RegExp(`/history/${state.session_id}$`))
    await expect(page.getByText('Fewer than five finalized answers: there is insufficient evidence for an adaptive outcome.', { exact: true })).toBeVisible()
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  })
}
