import { test, expect, request as apiRequest } from './browser-fixture.js'
import AxeBuilder from '@axe-core/playwright'

const API = 'http://127.0.0.1:8100'
const PASSWORD = 'ReleaseTest123!'
const DIFFICULTY_LABEL = { EASY: 'Easy', MEDIUM: 'Medium', HARD: 'Hard' }
const BANDS = { EASY: [1, 2], MEDIUM: [3, 3], HARD: [4, 5] }

// Approved version-1 blueprint matrix activated for the four published
// assessments. Theory areas schedule no executable SQL because the read-only
// sandbox cannot honestly execute those statements.
const EXPECTED = [
  { assessment: 2, area: 'Performance', bands: ['EASY', 'MEDIUM'], mix: { mcq: 6, sql: 0, essay: 2 } },
  { assessment: 2, area: 'Querying', bands: ['EASY', 'MEDIUM'], mix: { mcq: 4, sql: 2, essay: 2 } },
  { assessment: 3, area: 'Database Design', bands: ['EASY', 'MEDIUM', 'HARD'], mix: { mcq: 10, sql: 2, essay: 1 } },
  { assessment: 3, area: 'SQL Querying', bands: ['EASY', 'MEDIUM', 'HARD'], mix: { mcq: 10, sql: 2, essay: 1 } },
  { assessment: 4, area: 'Database Design', bands: ['EASY', 'MEDIUM', 'HARD'], mix: { mcq: 10, sql: 2, essay: 1 } },
  { assessment: 4, area: 'SQL Foundations', bands: ['EASY', 'MEDIUM', 'HARD'], mix: { mcq: 10, sql: 2, essay: 1 } },
  { assessment: 4, area: 'SQL Querying', bands: ['EASY', 'MEDIUM', 'HARD'], mix: { mcq: 10, sql: 2, essay: 1 } },
  { assessment: 6, area: 'PostgreSQL Administration', bands: ['EASY', 'MEDIUM', 'HARD'], mix: { mcq: 10, sql: 0, essay: 3 } },
  { assessment: 6, area: 'PostgreSQL Concurrency', bands: ['EASY', 'MEDIUM', 'HARD'], mix: { mcq: 10, sql: 0, essay: 3 } },
  { assessment: 6, area: 'PostgreSQL Data Definition', bands: ['EASY', 'MEDIUM', 'HARD'], mix: { mcq: 10, sql: 2, essay: 1 } },
  { assessment: 6, area: 'PostgreSQL Data Manipulation', bands: ['EASY', 'MEDIUM', 'HARD'], mix: { mcq: 10, sql: 2, essay: 1 } },
  { assessment: 6, area: 'PostgreSQL Data Types', bands: ['EASY', 'MEDIUM', 'HARD'], mix: { mcq: 10, sql: 2, essay: 1 } },
  { assessment: 6, area: 'PostgreSQL Functions', bands: ['EASY', 'MEDIUM', 'HARD'], mix: { mcq: 10, sql: 2, essay: 1 } },
  { assessment: 6, area: 'PostgreSQL Performance', bands: ['EASY', 'MEDIUM', 'HARD'], mix: { mcq: 10, sql: 0, essay: 3 } },
  { assessment: 6, area: 'PostgreSQL Querying', bands: ['EASY', 'MEDIUM', 'HARD'], mix: { mcq: 10, sql: 2, essay: 1 } },
  { assessment: 6, area: 'PostgreSQL Security', bands: ['EASY', 'MEDIUM', 'HARD'], mix: { mcq: 10, sql: 0, essay: 3 } },
  { assessment: 6, area: 'PostgreSQL Server Programming', bands: ['EASY', 'MEDIUM', 'HARD'], mix: { mcq: 10, sql: 0, essay: 3 } },
]

async function json(api, path, { token, method = 'GET', data } = {}) {
  const response = await api.fetch(`${API}${path}`, {
    method,
    data,
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  expect(response.ok(), `${method} ${path}: ${await response.text()}`).toBeTruthy()
  return response.status() === 204 ? null : response.json()
}

async function registerViaApi(api, email, name = 'First-time learner') {
  await json(api, '/api/v1/auth/register', {
    method: 'POST', data: { name, email, password: PASSWORD, password_confirm: PASSWORD },
  })
}

async function login(page, email, redirect = /\/dashboard$/) {
  await page.addInitScript(() => localStorage.setItem('dbcas_locale', 'en'))
  await page.goto('/login')
  await page.getByLabel('Email', { exact: true }).fill(email)
  await page.getByLabel('Password', { exact: true }).fill(PASSWORD)
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page).toHaveURL(redirect)
  await expect(page.getByRole('heading', { name: email === 'release-admin@test.dev' ? 'Cohort Overview' : 'My competency', exact: true })).toBeVisible()
  return page.evaluate(() => localStorage.getItem('dbcas_token'))
}

async function adminToken(api) {
  return (await json(api, '/api/v1/auth/login', {
    method: 'POST', data: { email: 'release-admin@test.dev', password: PASSWORD },
  })).access_token
}

async function openOptions(page) {
  const details = page.locator('details').filter({ hasText: 'Assessment options' })
  if (!(await details.evaluate((node) => node.open))) {
    await page.getByText('Assessment options', { exact: true }).click()
  }
}

async function startViaUi(page, { assessmentId, area, difficulty, mode = 'FORMAL', count }) {
  await page.goto('/assessments')
  await expect(page.getByRole('heading', { name: 'Assess your database skills', exact: true })).toBeVisible()
  await openOptions(page)
  await page.getByLabel('Assessment rules', { exact: true }).selectOption(String(assessmentId))
  if (area) await page.getByRole('button', { name: area, exact: true }).click()
  await page.getByRole('radio', { name: DIFFICULTY_LABEL[difficulty], exact: true }).check()
  await page.getByLabel('Assessment format', { exact: true }).selectOption(mode)
  if (count) await page.getByLabel('Number of questions', { exact: true }).selectOption(String(count))
  const response = page.waitForResponse((r) => r.request().method() === 'POST'
    && new URL(r.url()).pathname.endsWith(`/assessments/${assessmentId}/sessions`))
  await page.getByRole('button', { name: 'Start assessment', exact: true }).click()
  const started = await response
  return started
}

async function finishViaUi(page) {
  await page.getByRole('button', { name: 'Finish assessment', exact: true }).first().click()
  await page.getByRole('button', { name: 'Yes, finish', exact: true }).click()
  await expect(page).toHaveURL(/\/history\/\d+$/)
  return Number(page.url().split('/').at(-1))
}

async function openHelp(page) {
  await page.getByRole('button', { name: /^(Help|Hướng dẫn)$/ }).click()
  const dialog = page.getByRole('dialog')
  await expect(dialog).toBeVisible()
  // Entrance must not fade the panel: mid-animation text would render below
  // AA contrast even though the settled colors pass.
  expect(await dialog.evaluate((element) => getComputedStyle(element).opacity)).toBe('1')
  return dialog
}

test('first-time user: registration, role boundary, help discovery and accessibility', async ({ page }) => {
  test.setTimeout(180_000)
  const api = await apiRequest.newContext({ baseURL: API, timeout: 30_000 })
  const email = `ftu-onboarding-${Date.now()}@test.dev`
  try {
    await page.addInitScript(() => localStorage.setItem('dbcas_locale', 'en'))
    await page.goto('/register')
    const help = page.getByRole('button', { name: 'Help', exact: true })
    await expect(help).toBeVisible()
    await expect(page.getByRole('dialog')).toHaveCount(0)

    let dialog = await openHelp(page)
    await expect(dialog.getByRole('heading', { name: 'How to use DBCAS', exact: true })).toBeVisible()
    expect(await page.evaluate(() => getComputedStyle(document.body).overflow)).toBe('hidden')
    await expect(page.locator('#root')).toHaveAttribute('inert', '')
    await page.keyboard.press('Escape')
    await expect(dialog).toHaveCount(0)
    await expect(help).toBeFocused()

    dialog = await openHelp(page)
    await dialog.getByRole('button', { name: 'SQL sandbox', exact: true }).click()
    await expect.poll(() => page.evaluate(() => document.activeElement?.id)).toBe('help-section-sql')
    await dialog.getByRole('button', { name: 'Close help', exact: true }).click()
    await expect(dialog).toHaveCount(0)

    await page.getByRole('button', { name: 'Language', exact: true }).click()
    await page.getByRole('menuitemradio', { name: 'Tiếng Việt', exact: true }).click()
    const viDialog = await openHelp(page)
    await expect(viDialog.getByRole('heading', { name: 'Cách sử dụng DBCAS', exact: true })).toBeVisible()
    await expect(viDialog.getByText('Hướng dẫn trong ứng dụng', { exact: true })).toBeVisible()
    await page.keyboard.press('Escape')
    await page.getByRole('button', { name: 'Ngôn ngữ', exact: true }).click()
    await page.getByRole('menuitemradio', { name: 'English', exact: true }).click()

    await page.getByLabel('Full name', { exact: true }).fill('First-time Learner')
    await page.getByLabel('Email', { exact: true }).fill(email)
    await page.getByLabel('Password', { exact: true }).fill(PASSWORD)
    await page.getByLabel('Confirm password', { exact: true }).fill(PASSWORD)
    await page.getByRole('button', { name: 'Register', exact: true }).click()
    await expect(page).toHaveURL(/\/login$/)
    await expect(page.getByRole('heading', { name: 'Sign in to DBCAS', exact: true })).toBeVisible()
    await page.getByLabel('Email', { exact: true }).fill(email)
    await page.getByLabel('Password', { exact: true }).fill(PASSWORD)
    const signedIn = page.waitForResponse((response) => response.request().method() === 'POST'
      && new URL(response.url()).pathname === '/api/v1/auth/login')
    await page.getByRole('button', { name: 'Sign in', exact: true }).click()
    expect((await signedIn).status()).toBe(200)
    await expect(page).toHaveURL(/\/dashboard$/)
    await expect(page.getByRole('heading', { name: 'My competency', exact: true })).toBeVisible()

    // Learner role: no administration navigation and the guarded route returns home.
    await expect(page.locator('a[href="/admin"]')).toHaveCount(0)
    await page.goto('/admin')
    await expect(page).toHaveURL(/\/dashboard$/)
    await expect(page.getByRole('heading', { name: 'My competency', exact: true })).toBeVisible()
    await page.goto('/dashboard')
    await expect(page.getByRole('heading', { name: 'My competency', exact: true })).toBeVisible()

    for (const [path, context] of [
      ['/dashboard', 'Your dashboard'],
      ['/assessments', 'Starting an assessment'],
      ['/history', 'Your assessment history'],
      ['/competency', 'Cumulative competency'],
      ['/settings', 'Account settings'],
    ]) {
      await page.goto(path)
      await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
      const drawer = await openHelp(page)
      await expect(drawer.getByText(context, { exact: true })).toBeVisible()
      await page.keyboard.press('Escape')
    }

    // Learner-only guide section; no administrator guide for this role.
    await page.goto('/dashboard')
    await expect(page.getByRole('heading', { name: 'My competency', exact: true })).toBeVisible()
    let drawer = await openHelp(page)
    await expect(drawer.getByRole('heading', { name: 'Learner guide', exact: true })).toBeVisible()
    await expect(drawer.getByRole('heading', { name: 'Administrator guide', exact: true })).toHaveCount(0)
    let scan = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze()
    expect(scan.violations).toEqual([])
    await page.keyboard.press('Escape')

    // Theme and mobile layout.
    const themeBefore = await page.evaluate(() => document.documentElement.dataset.theme)
    await page.getByRole('button', { name: /Switch to (light|dark) theme/ }).click()
    await expect.poll(() => page.evaluate(() => document.documentElement.dataset.theme)).not.toBe(themeBefore)
    await page.setViewportSize({ width: 390, height: 844 })
    await page.reload()
    drawer = await openHelp(page)
    const box = await drawer.boundingBox()
    expect(box.width).toBeLessThanOrEqual(391)
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(391)
    scan = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze()
    expect(scan.violations).toEqual([])
    await page.keyboard.press('Escape')
    await page.setViewportSize({ width: 1440, height: 1000 })

    // Public guide content covers learner and administrator roles plus support.
    await page.goto('/assessments')
    await page.getByRole('button', { name: 'Log out', exact: true }).first().click()
    await expect(page).toHaveURL(/\/login$/)
    await expect(page.getByRole('heading', { name: 'Sign in to DBCAS', exact: true })).toBeVisible()
    drawer = await openHelp(page)
    await expect(drawer.getByRole('heading', { name: 'Administrator guide', exact: true })).toBeVisible()
    for (const section of ['Overview', 'Getting started', 'Practice vs Formal', 'Question types', 'SQL sandbox',
      'Essay and AI processing', 'Results and release', 'Language and theme', 'Accessibility', 'Troubleshooting']) {
      await expect(drawer.getByRole('button', { name: section, exact: true })).toBeVisible()
    }
    await page.keyboard.press('Escape')
  } finally {
    await api.dispose()
  }
})

test('all 49 approved blueprint scopes start through the visible learner UI', async ({ page }) => {
  test.setTimeout(900_000)
  const api = await apiRequest.newContext({ baseURL: API, timeout: 60_000 })
  const email = `ftu-blueprints-${Date.now()}@test.dev`
  try {
    await registerViaApi(api, email)
    const learner = await login(page, email)
    const admin = await adminToken(api)
    const assessments = await json(api, '/api/v1/assessments', { token: learner })
    // The disposable pack also seeds an assessment-1 legacy bank; only the
    // approved activation matrix for assessments 2/3/4/6 is under test.
    const approvedIds = new Set(EXPECTED.map((group) => group.assessment))
    const rows = (await json(api, '/__test/blueprints', { token: admin }))
      .filter((row) => approvedIds.has(row.assessment_id))
    expect(rows).toHaveLength(49)
    expect(rows.every((row) => row.status === 'approved' && row.approved_by === null)).toBe(true)
    const expectedScopes = EXPECTED.flatMap((group) => group.bands.map((band) => ({
      assessment: group.assessment, area: group.area, band, mix: group.mix,
    })))
    expect(expectedScopes).toHaveLength(49)
    const actual = new Map(rows.map((row) => [`${row.assessment_id}|${row.subject_area}|${row.difficulty_band}`, row]))
    expect(actual.size).toBe(49)
    for (const scope of expectedScopes) {
      const row = actual.get(`${scope.assessment}|${scope.area}|${scope.band}`)
      expect(row, `missing blueprint ${scope.assessment} ${scope.area} ${scope.band}`).toBeTruthy()
      expect(row.version_no).toBe(1)
      expect(row.target_mcq).toBe(scope.mix.mcq)
      expect(row.target_sql).toBe(scope.mix.sql)
      expect(row.target_essay).toBe(scope.mix.essay)
      expect(row.max_questions).toBe(scope.mix.mcq + scope.mix.sql + scope.mix.essay)
    }

    const byId = new Map(assessments.map((assessment) => [assessment.assessment_id, assessment]))
    const sessions = new Set()
    for (const scope of expectedScopes) {
      const assessment = byId.get(scope.assessment)
      expect(assessment, `assessment ${scope.assessment} is published`).toBeTruthy()
      const concepts = assessment.concepts.filter((c) => c.subject_area === scope.area).map((c) => c.concept_id)
      expect(concepts.length).toBeGreaterThan(0)
      const response = await startViaUi(page, {
        assessmentId: scope.assessment, area: scope.area, difficulty: scope.band, mode: 'FORMAL',
      })
      expect(response.status(), `${scope.assessment} ${scope.area} ${scope.band}`).toBe(201)
      const body = await response.json()
      expect(body.assembly_mode).toBe('FORMAL')
      const sid = body.session_id
      expect(sessions.has(sid)).toBe(false)
      sessions.add(sid)
      await expect(page).toHaveURL(new RegExp(`/exam/${sid}$`))
      const plan = await json(api, `/__test/sessions/${sid}/assembly`, { token: learner })
      expect(plan.assessment_id).toBe(scope.assessment)
      expect(plan.assembly_mode).toBe('FORMAL')
      expect(plan.difficulty).toBe(scope.band)
      expect(plan.status).toBe('in_progress')
      expect([...plan.selected_concept_ids].sort()).toEqual([...concepts].sort())
      expect(plan.blueprint.subject_area).toBe(scope.area)
      expect(plan.blueprint.difficulty_band).toBe(scope.band)
      expect(plan.blueprint.version_no).toBe(1)
      expect(plan.max_questions).toBe(scope.mix.mcq + scope.mix.sql + scope.mix.essay)
      expect(plan.plan).toHaveLength(plan.max_questions)
      expect(plan.type_mix).toEqual(scope.mix)
      expect(plan.duplicate_families).toBe(0)
      expect(new Set(plan.plan.map((item) => item.question_id)).size).toBe(plan.plan.length)
      const [low, high] = BANDS[scope.band]
      const covered = new Set()
      for (const item of plan.plan) {
        expect(item.difficulty_level).toBeGreaterThanOrEqual(low)
        expect(item.difficulty_level).toBeLessThanOrEqual(high)
        expect(item.concept_ids.some((id) => concepts.includes(id)), 'question scope').toBe(true)
        item.concept_ids.filter((id) => concepts.includes(id)).forEach((id) => covered.add(id))
      }
      expect([...covered].sort()).toEqual([...concepts].sort())
      // A repeated request id is idempotent; an identical selection under a
      // new id resumes the same frozen plan instead of creating another one.
      const again = await api.fetch(`${API}/api/v1/assessments/${scope.assessment}/sessions`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${learner}` },
        data: { concept_ids: concepts, difficulty: scope.band, request_id: crypto.randomUUID(), mode: 'FORMAL' },
      })
      expect(again.ok(), await again.text()).toBeTruthy()
      expect((await again.json()).session_id).toBe(sid)
      const finished = await finishViaUi(page)
      expect(finished).toBe(sid)
      const after = await json(api, `/api/v1/sessions/${sid}`, { token: learner })
      expect(after.status).not.toBe('in_progress')
      expect(after.answered_count).toBe(0)
    }
    expect(sessions.size).toBe(49)
  } finally {
    await api.dispose()
  }
})
