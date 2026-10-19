import { test, expect } from '../e2e/browser-fixture.js'
import fs from 'node:fs/promises'
import path from 'node:path'

const API = 'http://127.0.0.1:8100/api/v1'
const PASSWORD = 'ReleaseTest123!'
const artifacts = path.resolve(process.env.DBCAS_E2E_OUTPUT ?? '../../_review/e2e-application')

async function call(page, route, token, method = 'GET', data) {
  const response = await page.request.fetch(`${API}${route}`, { method, data,
    headers: token ? { Authorization: `Bearer ${token}` } : {} })
  expect(response.ok(), `${method} ${route}: ${response.status()}`).toBeTruthy()
  return response.json()
}
async function login(page, email) {
  if (!page.url().endsWith('/login')) await page.goto('/login')
  await expect(page.getByRole('heading', { name: 'Sign in to DBCAS', exact: true })).toBeVisible()
  await page.getByLabel('Email', { exact: true }).fill(email)
  await page.getByLabel('Password', { exact: true }).fill(PASSWORD)
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page).toHaveURL(email === 'release-admin@test.dev' ? /\/admin$/ : /\/dashboard$/)
  return page.evaluate(() => localStorage.getItem('dbcas_token'))
}
async function register(page) {
  const email = `real-app-${Date.now()}-${Math.random().toString(16).slice(2, 8)}@test.dev`
  await page.goto('/register')
  for (const [name, value] of [['Full name', 'Isolated application learner'], ['Email', email], ['Password', PASSWORD], ['Confirm password', PASSWORD]]) await page.getByLabel(name, { exact: true }).fill(value)
  await page.getByRole('button', { name: 'Register', exact: true }).click()
  await expect(page).toHaveURL(/\/login$/)
  return login(page, email)
}

test('real role manager promotes and revokes an account with immediate token enforcement', async ({ page, browser, browserDiagnostics }) => {
  test.setTimeout(120_000)
  const adminContext = await browser.newContext({ baseURL: 'http://127.0.0.1:5174', locale: 'en-US' })
  browserDiagnostics.observe(adminContext)
  const adminPage = await adminContext.newPage()
  const targetContext = await browser.newContext({ baseURL: 'http://127.0.0.1:5174', locale: 'en-US' })
  browserDiagnostics.observe(targetContext)
  const targetPage = await targetContext.newPage()
  try {
    const adminToken = await login(adminPage, 'release-admin@test.dev')
    const email = `role-target-${Date.now()}@test.dev`
    const created = await adminPage.request.post(`${API}/auth/register`, { data: {
      name: 'Role management E2E learner', email, password: PASSWORD, password_confirm: PASSWORD,
    } })
    expect(created.status()).toBe(201)
    const targetToken = await login(targetPage, email)

    await adminPage.goto('/admin/accounts')
    const row = adminPage.getByRole('row').filter({ hasText: email })
    await expect(row).toBeVisible()
    await row.getByRole('button', { name: 'Grant Administrator Access', exact: true }).click()
    const grantDialog = adminPage.getByRole('dialog', { name: 'Grant Administrator access to this user?' })
    await expect(grantDialog).toContainText('They will be able to access administrative features.')
    await grantDialog.getByRole('button', { name: 'Grant Administrator Access', exact: true }).click()
    await expect(row).toContainText('Administrator')
    await expect(adminPage.getByRole('status')).toContainText(`Administrator access granted to ${email}`)

    const adminAccess = await targetPage.request.get(`${API}/admin/accounts`, {
      headers: { Authorization: `Bearer ${targetToken}` },
    })
    expect(adminAccess.status()).toBe(200)
    await targetPage.reload()
    await targetPage.goto('/admin')
    await expect(targetPage).toHaveURL(/\/admin$/)
    await expect(targetPage.getByRole('heading', { level: 1 })).toBeVisible()

    await row.getByRole('button', { name: 'Revoke Administrator Access', exact: true }).click()
    const revokeDialog = adminPage.getByRole('dialog', { name: 'Revoke Administrator access?' })
    await expect(revokeDialog).toContainText('This user will lose access to administrative features.')
    await revokeDialog.getByRole('button', { name: 'Revoke Administrator Access', exact: true }).click()
    await expect(row).toContainText('Learner')
    const revokedAccess = await targetPage.request.get(`${API}/admin/accounts`, {
      headers: { Authorization: `Bearer ${targetToken}` },
    })
    expect(revokedAccess.status()).toBe(403)
    await targetPage.reload()
    await targetPage.goto('/admin')
    await expect(targetPage).toHaveURL(/\/dashboard$/)
    const audit = await adminPage.request.get(`${API}/admin/accounts/role-audit`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    })
    expect(audit.status()).toBe(200)
    const changes = (await audit.json()).filter(event => event.target_account_id > 0)
    expect(changes).toEqual(expect.arrayContaining([
      expect.objectContaining({ action_type: 'ROLE_GRANTED', previous_role: 'Learner', new_role: 'Administrator' }),
      expect.objectContaining({ action_type: 'ROLE_REVOKED', previous_role: 'Administrator', new_role: 'Learner' }),
    ]))
  } finally {
    await targetContext.close()
    await adminContext.close()
  }
})
async function setTheme(page, theme) {
  await page.goto('/settings')
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  if (await page.locator('html').getAttribute('data-theme') !== theme) {
    await page.locator('#main-content').getByRole('button', { name: `Switch to ${theme} theme`, exact: true }).click()
  }
  await expect(page.locator('html')).toHaveAttribute('data-theme', theme)
  await expect(page.locator('html')).not.toHaveAttribute('data-theme-transitioning', 'true')
}
async function start(page, rule, topic, difficulty = 'EASY', count = 1) {
  await page.goto('/assessments')
  await page.getByLabel('Assessment rules', { exact: true }).selectOption(String(rule.assessment_id))
  await page.getByLabel('Assessment format', { exact: true }).selectOption('PRACTICE')
  await page.getByLabel('Number of questions', { exact: true }).selectOption(String(count))
  await page.getByLabel(new RegExp(topic.concept_name)).check()
  await page.getByLabel('Assessment difficulty', { exact: true }).selectOption(difficulty)
  const starting = page.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith(`/assessments/${rule.assessment_id}/sessions`))
  await page.getByRole('button', { name: 'Start personalized assessment', exact: true }).click()
  const response = await starting
  expect(response.status()).toBe(201)
  const payload = response.request().postDataJSON()
  await expect(page).toHaveURL(/\/exam\/\d+$/)
  return { state: await response.json(), payload }
}
async function finish(page) {
  const sessionId = page.url().split('/').at(-1)
  await page.getByRole('button', { name: 'Finish assessment', exact: true }).first().click()
  await page.getByRole('button', { name: 'Yes, finish', exact: true }).click()
  await expect(page).toHaveURL(new RegExp(`/history/${sessionId}$`))
}
async function fixture(adminPage, token) {
  const bank = await call(adminPage, '/admin/questions?status=validated', token)
  const sources = {}
  for (const kind of ['mcq', 'sql', 'essay']) sources[kind] = await call(adminPage, `/admin/questions/${bank.find(q => q.question_type === kind).question_id}`, token)
  const label = `E2E-${Date.now()}`
  await adminPage.goto('/admin/curriculum')
  await adminPage.getByLabel('Concept code', { exact: true }).fill(label)
  await adminPage.getByLabel('Concept name', { exact: true }).fill(`${label} approved database examples`)
  await adminPage.getByLabel('Subject area', { exact: true }).fill('Database competency')
  // The concept form has one technique select; all other controls are text inputs.
  await adminPage.locator('form').filter({ has: adminPage.getByLabel('Concept code', { exact: true }) }).getByRole('combobox').selectOption('select')
  await adminPage.getByLabel('Concept keywords (comma separated)', { exact: true }).fill('projection, approved bank')
  await adminPage.getByLabel('Learning objectives (one per line)', { exact: true }).fill('Execute read-only SQL\nExplain the supplied database concepts')
  const creating = adminPage.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith('/admin/concepts'))
  await adminPage.getByRole('button', { name: 'Add concept', exact: true }).click()
  const created = await creating
  expect(created.status()).toBe(201)
  const topic = await created.json()
  expect(topic.keywords).toEqual(['projection', 'approved bank'])
  expect(topic.learning_objectives).toHaveLength(2)
  for (const [kind, levels] of [['mcq', [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 5]], ['sql', [3, 3]], ['essay', [3]]]) {
    for (const [i, difficulty] of levels.entries()) {
      const source = sources[kind]
      const q = await call(adminPage, '/admin/questions', token, 'POST', {
        question_type: kind, prompt: `${label} ${kind} ${i}: ${source.prompt}`, points: source.points,
        difficulty_level: difficulty, reference_answer: source.reference_answer, explanation: source.explanation,
        concept_ids: [topic.concept_id], required_concept_ids: kind === 'sql' ? [topic.concept_id] : [],
        options: source.options.map(({ option_label, option_text, is_correct }) => ({ option_label, option_text, is_correct })),
        datasets: source.datasets.map(({ dataset_name, setup_sql, expected_result, is_edge_case }) => ({ dataset_name, setup_sql, expected_result, is_edge_case })),
        rubrics: source.rubrics.map(({ level_name, min_score, max_score, criteria }) => ({ level_name, min_score, max_score, criteria })),
        translations: source.translations.filter(item => item.current).map(item => ({
          locale: item.locale, prompt: `${label}: ${item.prompt}`, explanation: item.explanation,
          option_texts: item.option_texts, rubrics: item.rubrics,
        })),
      })
      await call(adminPage, `/admin/questions/${q.question_id}`, token, 'PATCH', { status: 'validated' })
    }
  }
  const rules = {}
  for (const policy of ['IMMEDIATE', 'HUMAN_VERIFIED']) {
    rules[policy] = await call(adminPage, '/admin/assessments', token, 'POST', {
      title: `${label} ${policy}`, result_release_policy: policy,
      concepts: [{ concept_id: topic.concept_id, min_difficulty: 1, max_difficulty: 5, target_pct: 70 }],
    })
    await call(adminPage, `/admin/assessments/${rules[policy].assessment_id}`, token, 'PATCH', { status: 'published' })
  }
  return { topic, rules }
}

test('real entrypoint: authentication, refresh, logout and role boundaries', async ({ page }) => {
  const schema = await (await page.request.get('http://127.0.0.1:8100/openapi.json')).json()
  expect(Object.keys(schema.paths).some(p => p.startsWith('/__test'))).toBe(false)
  expect((await page.request.get('http://127.0.0.1:8100/readiness')).status()).toBe(200)
  await page.goto('/admin/grading')
  await expect(page).toHaveURL(/\/login$/)
  await page.getByLabel('Email', { exact: true }).fill(`invalid-${Date.now()}@test.dev`)
  await page.getByLabel('Password', { exact: true }).fill(PASSWORD)
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page.getByRole('alert')).toBeVisible()
  const learner = await register(page)
  await page.reload()
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  await expect(page).toHaveURL(/\/dashboard$/)
  await page.goto('/admin/grading')
  await expect(page).toHaveURL(/\/dashboard$/)
  expect((await page.request.get(`${API}/admin/grading-reviews`, { headers: { Authorization: `Bearer ${learner}` } })).status()).toBe(403)
  await page.getByRole('banner').getByRole('button', { name: 'Log out', exact: true }).click()
  await page.goto('/history')
  await expect(page).toHaveURL(/\/login$/)
})

for (const [width, height] of [[1440, 900], [1366, 768], [768, 1024], [390, 844]]) {
  test(`real entrypoint ${width}x${height}: learner/admin navigation in both themes`, async ({ page, browser, browserDiagnostics }) => {
    test.setTimeout(180_000)
    await page.setViewportSize({ width, height })
    await register(page)
    const adminContext = await browser.newContext({ baseURL: 'http://127.0.0.1:5174', locale: 'en-US', viewport: { width, height } })
    browserDiagnostics.observe(adminContext)
    const adminPage = await adminContext.newPage()
    try {
      await login(adminPage, 'release-admin@test.dev')
      for (const [actor, routes] of [[page, ['/dashboard', '/assessments', '/history', '/competency', '/settings']],
        [adminPage, ['/admin', '/admin/curriculum', '/admin/questions', '/admin/assessments', '/admin/grading', '/admin/accounts', '/settings']]]) {
        for (const theme of ['light', 'dark']) {
          await setTheme(actor, theme)
          for (const route of routes) {
            await actor.goto(route)
            await expect(actor.getByRole('heading', { level: 1 })).toBeVisible()
            await expect(actor.locator('.skeleton')).toHaveCount(0)
            await expect(actor.getByRole('alert')).toHaveCount(0)
            expect(await actor.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width + 1)
            if (actor === adminPage && width >= 768) {
              const sidebar = await actor.locator('.app-sidebar').boundingBox()
              const footer = await actor.getByRole('contentinfo').boundingBox()
              expect(footer.x, 'Administrator footer must clear the fixed sidebar').toBeGreaterThanOrEqual(sidebar.x + sidebar.width)
            }
            await fs.mkdir(path.join(artifacts, 'screenshots'), { recursive: true })
            await actor.screenshot({ path: path.join(artifacts, 'screenshots', `${route.replaceAll('/', '-')}-${theme}-${width}x${height}.png`), fullPage: true })
          }
          await actor.reload()
          await expect(actor.locator('html')).toHaveAttribute('data-theme', theme)
          // Theme initializes before authentication: await the actual page
          // before the next navigation, rather than cancelling bootstrap XHRs.
          await expect(actor.getByRole('heading', { level: 1 })).toBeVisible()
          await expect(actor.locator('.skeleton')).toHaveCount(0)
        }
      }
      expect(browserDiagnostics.records.pageErrors).toEqual([])
    } finally { await adminContext.close() }
  })
}

test('real entrypoint: strict difficulty, drafts, unavailable AI, human correction and cumulative evidence', async ({ page, browser, browserDiagnostics }) => {
  test.setTimeout(240_000)
  const schema = await (await page.request.get('http://127.0.0.1:8100/openapi.json')).json()
  expect(Object.keys(schema.paths).some(p => p.startsWith('/__test'))).toBe(false)
  const adminContext = await browser.newContext({ baseURL: 'http://127.0.0.1:5174', locale: 'en-US' })
  browserDiagnostics.observe(adminContext)
  const adminPage = await adminContext.newPage()
  try {
    const admin = await login(adminPage, 'release-admin@test.dev')
    const { topic, rules } = await fixture(adminPage, admin)
    const learner = await register(page)
    const evidence = []
    for (const [difficulty, level] of [['EASY', 1], ['MEDIUM', 3], ['HARD', 5]]) {
      const { state, payload } = await start(page, rules.IMMEDIATE, topic, difficulty)
      expect(state.current_question.difficulty_level).toBe(level)
      const q = await call(adminPage, `/admin/questions/${state.current_question.question_id}`, admin)
      expect(q.concepts.filter(c => c.confirmed).map(c => c.concept_id)).toEqual([topic.concept_id])
      await page.locator(`input[value="${q.options.find(o => o.is_correct).option_id}"]`).locator('..').click()
      const submitted = page.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith(`/sessions/${state.session_id}/submit`))
      await page.getByRole('button', { name: 'Submit answer & continue', exact: true }).click()
      expect((await submitted).status()).toBe(200)
      await finish(page)
      const result = await call(page, `/sessions/${state.session_id}/evidence`, learner)
      expect(Number(result.items[0].score)).toBe(Number(q.points))
      evidence.push(...result.items)
      expect((await call(page, `/assessments/${rules.IMMEDIATE.assessment_id}/sessions`, learner, 'POST', payload)).session_id).toBe(state.session_id)
    }
    await page.goto('/assessments')
    await page.getByLabel('Assessment rules', { exact: true }).selectOption(String(rules.IMMEDIATE.assessment_id))
    await page.getByLabel('Assessment format', { exact: true }).selectOption('FORMAL')
    await page.getByRole('button', { name: 'Select all skills (comprehensive)', exact: true }).click()
    await page.getByLabel('Assessment difficulty', { exact: true }).selectOption('HARD')
    const invalid = page.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith(`/assessments/${rules.IMMEDIATE.assessment_id}/sessions`))
    await page.getByRole('button', { name: 'Start personalized assessment', exact: true }).click()
    const rejected = await invalid
    expect(rejected.status()).toBe(422)
    expect((await rejected.json()).error.code).toBe('insufficient_question_pool')
    await expect(page.getByRole('alert')).toBeVisible()
    expect((await call(page, '/sessions', learner)).length).toBe(3)
    const { state: initial } = await start(page, rules.HUMAN_VERIFIED, topic, 'MEDIUM', 3)
    const sid = initial.session_id
    const seen = new Set()
    const kinds = new Set()
    for (let i = 0; i < 3; i++) {
      const before = await call(page, `/sessions/${sid}`, learner)
      const q = before.current_question
      expect(seen.has(q.question_id)).toBe(false)
      seen.add(q.question_id); kinds.add(q.question_type)
      const key = await call(adminPage, `/admin/questions/${q.question_id}`, admin)
      if (q.question_type === 'mcq') await page.locator(`input[value="${key.options.find(o => o.is_correct).option_id}"]`).locator('..').click()
      else {
        const field = page.getByLabel(q.question_type === 'sql' ? 'Your query' : 'Your answer', { exact: true })
        const text = key.reference_answer ?? key.rubrics.find(r => r.level_name === 'Complete').criteria
        await field.fill('Initial editable draft')
        await field.fill(text)
        const saving = page.waitForResponse(r => r.request().method() === 'PUT' && r.url().includes(`/sessions/${sid}/draft`))
        await page.getByRole('button', { name: 'Save draft', exact: true }).click()
        expect((await saving).status()).toBe(200)
        await page.reload()
        await expect(page.getByLabel(q.question_type === 'sql' ? 'Your query' : 'Your answer', { exact: true })).toHaveValue(text)
        const resumed = await call(page, `/sessions/${sid}`, learner)
        expect(resumed.expires_at).toBe(before.expires_at)
        expect(resumed.current_question.question_id).toBe(q.question_id)
      }
      const submitting = page.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith(`/sessions/${sid}/submit`))
      await page.getByRole('button', { name: 'Submit answer & continue', exact: true }).click()
      const submitted = await submitting
      expect(submitted.status()).toBe(200)
      const answer = (await submitted.json()).answer
      expect(answer.score).toBeNull(); expect(answer.is_correct).toBeNull()
    }
    expect([...kinds].sort()).toEqual(['essay', 'mcq', 'sql'])
    await finish(page)
    const waitHeading = page.getByRole('heading', { name: /we’re grading your assessment|your submission is received|instructor review is complete|grading needs attention|result is taking longer than expected/i })
    await expect(waitHeading).toBeVisible()
    await page.reload()
    await expect(waitHeading).toBeVisible()
    for (const endpoint of ['evidence', 'competency', 'gaps', 'guidance']) expect((await page.request.get(`${API}/sessions/${sid}/${endpoint}`, { headers: { Authorization: `Bearer ${learner}` } })).status()).toBe(409)
    expect((await call(page, '/sessions/competency/cumulative', learner)).summary.finalized_assessments).toBe(3)
    let detail = await call(adminPage, `/admin/grading-reviews/${sid}`, admin)
    const essay = detail.items.find(q => q.question_type === 'essay')
    expect(essay.automated_score).toBeNull()
    expect(essay.automated_detail.error_code).toBe('llm_not_configured')
    await adminPage.goto('/admin/grading')
    await adminPage.getByRole('button', { name: new RegExp(rules.HUMAN_VERIFIED.title) }).click()
    await expect(adminPage.getByRole('button', { name: 'Publish verified results', exact: true })).toBeDisabled()
    for (const item of detail.items.filter(q => q.question_type !== 'mcq')) {
      const card = adminPage.getByRole('heading', { name: item.prompt, exact: true }).locator('..')
      if (item.question_type === 'essay') {
        await card.getByLabel('Approved score', { exact: true }).fill(String(Number(item.points) / 2))
        await card.getByLabel('Grader comments', { exact: true }).fill('Manual rubric verification because no AI provider is configured.')
      } else expect(Number(item.automated_score)).toBe(Number(item.points))
      const approving = adminPage.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith(`/attempts/${item.attempt_id}`))
      await card.getByRole('button', { name: 'Approve score', exact: true }).click()
      expect((await approving).status()).toBe(200)
    }
    await expect(adminPage.getByRole('button', { name: 'Publish verified results', exact: true })).toBeEnabled()
    await adminPage.getByRole('button', { name: 'Publish verified results', exact: true }).click()
    await expect(adminPage.getByRole('status')).toHaveText('Published')
    await page.getByRole('button', { name: 'Refresh status', exact: true }).click()
    await expect(page.getByRole('heading', { name: 'Assessment evidence', exact: true })).toBeVisible()
    const final = await call(page, `/sessions/${sid}/evidence`, learner)
    evidence.push(...final.items)
    const finalEssay = final.items.find(q => q.question_type === 'essay')
    expect(Number(finalEssay.score)).toBe(Number(finalEssay.points) / 2)
    detail = await call(adminPage, `/admin/grading-reviews/${sid}`, admin)
    const stale = await adminPage.request.post(`${API}/admin/grading-reviews/${sid}/publish`, { headers: { Authorization: `Bearer ${admin}` }, data: { revision: detail.revision - 1 } })
    expect(stale.status()).toBe(409)
    const cumulative = await call(page, '/sessions/competency/cumulative', learner)
    expect(cumulative.summary.finalized_assessments).toBe(4)
    const earned = evidence.reduce((sum, q) => sum + Math.round(Number(q.score) * 100), 0)
    const possible = evidence.reduce((sum, q) => sum + Math.round(Number(q.points) * 100), 0)
    expect(Number(cumulative.concepts.find(c => c.concept_id === topic.concept_id).competency_pct)).toBe(Math.round(earned * 10000 / possible) / 100)
    await page.goto('/competency')
    await expect(page.getByText('4 published assessments', { exact: true })).toBeVisible()
    await page.reload()
    expect(await call(page, '/sessions/competency/cumulative', learner)).toEqual(cumulative)
  } finally { await adminContext.close() }
})

test('real entrypoint: a start request used to resume remains idempotent after completion', async ({ page, browser, browserDiagnostics }) => {
  test.setTimeout(120_000)
  const adminContext = await browser.newContext({ baseURL: 'http://127.0.0.1:5174', locale: 'en-US' })
  browserDiagnostics.observe(adminContext)
  const adminPage = await adminContext.newPage()
  try {
    const admin = await login(adminPage, 'release-admin@test.dev')
    const { topic, rules } = await fixture(adminPage, admin)
    const learner = await register(page)
    const first = await start(page, rules.IMMEDIATE, topic)
    // A fresh selection form creates a fresh UUID but resumes the active plan.
    const resumed = await start(page, rules.IMMEDIATE, topic)
    expect(resumed.payload.request_id).not.toBe(first.payload.request_id)
    expect(resumed.state.session_id).toBe(first.state.session_id)
    const q = await call(adminPage, `/admin/questions/${first.state.current_question.question_id}`, admin)
    await page.locator(`input[value="${q.options.find(o => o.is_correct).option_id}"]`).locator('..').click()
    const submitted = page.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith(`/sessions/${first.state.session_id}/submit`))
    await page.getByRole('button', { name: 'Submit answer & continue', exact: true }).click()
    expect((await submitted).status()).toBe(200)
    await finish(page)
    const retry = await call(page, `/assessments/${rules.IMMEDIATE.assessment_id}/sessions`, learner, 'POST', resumed.payload)
    expect(retry.session_id).toBe(first.state.session_id)
    expect((await call(page, '/sessions', learner)).length).toBe(1)
  } finally { await adminContext.close() }
})
