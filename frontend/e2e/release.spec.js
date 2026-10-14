import { test, expect, request as apiRequest } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'
import fs from 'node:fs/promises'
import path from 'node:path'
import { isBenignResolvedCancellation, isBenignResolvedWebkitAuthError, webkitCancelledAuthPath } from './requestFailurePolicy.js'

const API = 'http://127.0.0.1:8100'
const PASSWORD = 'ReleaseTest123!'
const ARTIFACTS = path.resolve(process.env.DBCAS_E2E_OUTPUT ?? '../../_review/remediation', 'screenshots', process.env.DBCAS_BROWSER ?? 'chromium')
let finalizedSession
let learnerEmail
let apiContext

test.beforeEach(async () => { apiContext = await apiRequest.newContext({ baseURL: API, timeout: 15_000 }) })
test.afterEach(async () => { await apiContext.dispose() })

async function request(page, route, { method = 'GET', data, token } = {}) {
  token ??= await page.evaluate(() => localStorage.getItem('dbcas_token'))
  const response = await apiContext.fetch(`${API}${route}`, {
    method, data, headers: { Connection: 'close', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
  })
  expect(response.ok(), `${method} ${route}: HTTP ${response.status()}`).toBeTruthy()
  return response.json()
}

async function adminToken(page) {
  const response = await request(page, '/api/v1/auth/login', {
    method: 'POST', data: { email: 'release-admin@test.dev', password: PASSWORD }, token: '',
  })
  return response.access_token
}

async function login(page, email) {
  await page.goto('/login')
  await page.getByLabel('Email', { exact: true }).fill(email)
  await page.getByLabel('Password', { exact: true }).fill(PASSWORD)
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page).toHaveURL(email === 'release-admin@test.dev' ? /\/admin$/ : /\/dashboard$/)
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  await expect(page.locator('.skeleton')).toHaveCount(0)
  await expect(page.getByRole('alert')).toHaveCount(0)
}

async function selectTheme(page, mode) {
  if (await page.locator('html').getAttribute('data-theme') !== mode) {
    await page.getByRole('button', { name: mode === 'light' ? 'Switch to light theme' : 'Switch to dark theme', exact: true }).click()
  }
  const resolved = mode
  await expect(page.locator('html')).toHaveAttribute('data-theme', resolved)
  await expect(page.locator('html')).toHaveAttribute('data-theme-mode', mode)
  await expect(page.locator('html')).not.toHaveAttribute('data-theme-transitioning', 'true')
  expect(await page.evaluate(() => localStorage.getItem('dbcas_theme') ?? 'dark')).toBe(mode)
}

async function checkBothThemes(page, name) {
  for (const mode of ['light', 'dark']) {
    await selectTheme(page, mode)
    await checkPage(page, name)
  }
  await selectTheme(page, 'dark')
}

async function register(page, suffix) {
  const email = `browser-${suffix}-${Date.now()}@test.dev`
  await page.goto('/register')
  await page.getByLabel('Full name', { exact: true }).fill('Browser fixture learner')
  await page.getByLabel('Email', { exact: true }).fill(email)
  await page.getByLabel('Password', { exact: true }).fill(PASSWORD)
  await page.getByLabel('Confirm password', { exact: true }).fill(PASSWORD)
  await page.getByRole('button', { name: 'Register', exact: true }).click()
  await expect(page).toHaveURL(/\/login$/)
  await login(page, email)
  return email
}

async function checkPage(page, name, { axe = true } = {}) {
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  await expect(page.locator('.skeleton')).toHaveCount(0)
  await expect(page.getByRole('alert')).toHaveCount(0)
  await page.evaluate(() => document.fonts.ready)
  if (name === 'dashboard') await expect(page.locator('canvas')).toHaveCount(2)
  const width = page.viewportSize().width
  const theme = await page.locator('html').getAttribute('data-theme')
  expect(await page.evaluate(() => document.documentElement.scrollWidth), `${name}: viewport overflow`).toBeLessThanOrEqual(width + 1)
  if (await page.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches)) {
    // WebKit can report the un-reduced duration for a moment on a freshly
    // mounted node right after an SPA navigation; re-sample until the reduced
    // media rule has settled, then assert the final read is fully reduced.
    let durations = []
    for (let i = 0; i < 8; i++) {
      durations = await page.locator('.page-enter, .auth-enter').evaluateAll(nodes => nodes.map(node => parseFloat(getComputedStyle(node).animationDuration)))
      if (durations.every(duration => duration <= .001)) break
      await page.waitForTimeout(50)
    }
    expect(durations.every(duration => duration <= .001), `${name}: reduced-motion reveal ${JSON.stringify(durations)}`).toBeTruthy()
  }
  if (axe) {
    const scan = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze()
    const findings = await Promise.all(scan.violations.map(async v => ({ id: v.id, impact: v.impact, nodes: await Promise.all(v.nodes.map(async n => ({
      target: n.target,
      failureSummary: n.failureSummary,
      html: n.html,
      computed: await page.locator(n.target[0]).evaluateAll(elements => elements.map(el => {
        const css = getComputedStyle(el)
        return { color: css.color, backgroundColor: css.backgroundColor, opacity: css.opacity, disabled: el.disabled, fieldsetDisabled: Boolean(el.closest('fieldset:disabled')) }
      })),
    }))) })))
    expect(findings, `${name}: automated accessibility`).toEqual([])
  }
  await fs.mkdir(ARTIFACTS, { recursive: true })
  await page.screenshot({ path: path.join(ARTIFACTS, `${name}-${theme}-${width}.png`), fullPage: true })
}

test.describe.configure({ mode: 'serial' })

test('learner completes the real adaptive assessment, drafts, recovery and evidence', async ({ page }) => {
  test.setTimeout(300_000)
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  const token = await adminToken(page)
  learnerEmail = await register(page, 'journey')
  await page.goto('/assessments')
  await page.getByRole('button', { name: 'Start', exact: true }).click()
  await expect(page).toHaveURL(/\/exam\/\d+$/)
  const sid = Number(page.url().split('/').at(-1))
  const kinds = []
  for (let index = 0; index < 13; index++) {
    const state = await request(page, `/api/v1/sessions/${sid}`)
    const q = state.current_question
    expect(q).toBeTruthy()
    kinds.push(q.question_type)
    const key = await request(page, `/api/v1/admin/questions/${q.question_id}`, { token })
    if (q.question_type === 'mcq') {
      const option = key.options.find(o => o.is_correct === (index >= 3))
      await page.getByRole('radio', { name: `${option.option_label}: ${option.option_text}`, exact: true }).locator('..').click()
    } else if (q.question_type === 'sql') {
      await page.getByLabel('Your query', { exact: true }).fill(key.reference_answer)
      await page.getByRole('button', { name: 'Run in sandbox' }).click()
      await expect(page.getByText(/\d+ rows? · [\d,.]+ ms/)).toBeVisible()
      await expect(page.locator('.sql-keyword').first()).toBeVisible()
      await checkBothThemes(page, 'exam-sql')
    } else {
      await page.getByLabel('Your answer', { exact: true }).fill(key.reference_answer)
      await checkBothThemes(page, 'exam-essay')
    }
    await page.getByRole('button', { name: 'Save draft', exact: true }).click()
    await expect(page.getByText('Draft saved', { exact: true })).toBeVisible()
    if (index === 0 || q.question_type !== 'mcq') {
      await page.reload()
      if (q.question_type === 'mcq') {
        const saved = await request(page, `/api/v1/sessions/${sid}/draft?question_id=${q.question_id}`)
        await expect(page.locator(`input[value="${saved.answer.selected_option_id}"]`)).toBeChecked()
        await checkBothThemes(page, 'exam-mcq')
        await page.goto('/assessments')
        await page.getByRole('button', { name: 'Resume', exact: true }).click()
        await expect(page).toHaveURL(new RegExp(`/exam/${sid}$`))
      } else {
        await expect(page.getByLabel(q.question_type === 'sql' ? 'Your query' : 'Your answer', { exact: true })).toHaveValue(key.reference_answer)
      }
    }
    if (index === 0) {
      // The API commits successfully, but the browser loses that response.
      await page.route(`**/api/v1/sessions/${sid}/submit`, async route => {
        const committed = await route.fetch()
        expect(committed.status()).toBe(200)
        expect((await committed.json()).state.answered_count).toBe(1)
        await route.abort('failed')
      }, { times: 1 })
    }
    await page.getByRole('button', { name: 'Submit answer & continue', exact: true }).click()
    if (index === 0) await expect(page.getByText('Answer submitted. Your session has been restored.')).toBeVisible()
    await expect.poll(async () => (await request(page, `/api/v1/sessions/${sid}`)).answered_count).toBe(index + 1)
    await expect(page.getByRole('button', { name: 'Submitting…' })).toHaveCount(0)
  }
  expect(kinds.slice(0, 3)).toEqual(['mcq', 'mcq', 'mcq'])
  expect(kinds.filter(k => k === 'mcq')).toHaveLength(10)
  expect(kinds.filter(k => k === 'sql')).toHaveLength(2)
  expect(kinds.filter(k => k === 'essay')).toHaveLength(1)
  await page.getByRole('button', { name: 'Finish assessment', exact: true }).first().click()
  const dialog = page.getByRole('dialog', { name: 'Finish this assessment?' })
  await expect(dialog).toBeVisible()
  await expect(dialog.getByRole('button', { name: 'Keep going', exact: true })).toBeFocused()
  expect(await page.locator('#root').evaluate(el => el.inert)).toBe(true)
  await page.keyboard.press('Escape')
  await expect(dialog).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'Finish assessment', exact: true }).first()).toBeFocused()
  for (const [index, mode] of ['light', 'dark'].entries()) {
    await selectTheme(page, mode)
    await page.getByRole('button', { name: 'Finish assessment', exact: true }).first().click()
    await expect(dialog).toBeVisible()
    await page.screenshot({ path: path.join(ARTIFACTS, `finish-dialog-${mode}-1440.png`), fullPage: true })
    if (index === 0) {
      await page.keyboard.press('Escape')
      await expect(dialog).toHaveCount(0)
      await expect(page.getByRole('button', { name: 'Finish assessment', exact: true }).first()).toBeFocused()
    }
  }
  await page.getByRole('button', { name: 'Yes, finish', exact: true }).click()
  await expect(page).toHaveURL(/\/dashboard$/)
  const evidence = await request(page, `/api/v1/sessions/${sid}/evidence`)
  expect(evidence.items).toHaveLength(13)
  expect(evidence.items.every(i => i.score !== null && i.submitted_at !== null)).toBe(true)
  finalizedSession = sid
  await page.goto('/history')
  await checkBothThemes(page, 'history')
  await page.goto(`/history/${sid}`)
  await checkBothThemes(page, 'evidence')
  await page.goto('/dashboard')
  await checkBothThemes(page, 'dashboard')
  const guidance = await request(page, `/api/v1/sessions/${sid}/guidance`)
  const shortfalls = guidance.guidance.map(i => Number(i.shortfall))
  expect(shortfalls).toEqual([...shortfalls].sort((a, b) => b - a))
  expect(errors).toEqual([])
})

test('server timeout submits the saved draft once and refresh shows final state', async ({ page }) => {
  await register(page, 'timeout')
  await page.goto('/assessments')
  await page.getByRole('button', { name: 'Start', exact: true }).click()
  await expect(page).toHaveURL(/\/exam\/\d+$/)
  const sid = Number(page.url().split('/').at(-1))
  await page.getByRole('radio').first().locator('..').click()
  await page.getByRole('button', { name: 'Save draft', exact: true }).click()
  await expect(page.getByText('Draft saved', { exact: true })).toBeVisible()
  await request(page, `/__test/sessions/${sid}/deadline?seconds=2`, { method: 'POST' })
  await page.reload()
  await expect(page).toHaveURL(/\/dashboard$/, { timeout: 20_000 })
  const state = await request(page, `/api/v1/sessions/${sid}`)
  expect(state.status).toBe('timed_out')
  expect(state.answered_count).toBe(1)
  const duplicate = await request(page, `/api/v1/sessions/${sid}/finish`, { method: 'POST' })
  expect(duplicate.submitted_at).toBe(state.submitted_at)
  await page.goto(`/exam/${sid}`)
  await expect(page).toHaveURL(/\/dashboard$/)
})

test('browser guards and APIs reject admin and cross-user session access', async ({ page }) => {
  await register(page, 'rbac')
  await page.goto('/admin/questions')
  await expect(page).not.toHaveURL(/\/admin/)
  const token = await page.evaluate(() => localStorage.getItem('dbcas_token'))
  for (const [route, status] of [[`/api/v1/sessions/${finalizedSession}`, 404], ['/api/v1/admin/questions', 403]]) {
    const r = await page.request.get(`${API}${route}`, { headers: { Authorization: `Bearer ${token}` } })
    expect(r.status()).toBe(status)
  }
  await page.evaluate(() => localStorage.clear())
  await login(page, 'release-admin@test.dev')
  const r = await page.request.get(`${API}/api/v1/sessions/${finalizedSession}`, { headers: { Authorization: `Bearer ${await page.evaluate(() => localStorage.getItem('dbcas_token'))}` } })
  expect(r.status()).toBe(403)
})

test('admin completes provisioning, curriculum, human AI review, activation and analytics', async ({ page }) => {
  test.setTimeout(300_000)
  await login(page, 'release-admin@test.dev')
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  const fixture = await request(page, '/__test/fixture')
  await page.goto('/admin/accounts')
  const email = `second-admin-${Date.now()}@test.dev`
  await page.getByLabel('Full name', { exact: true }).fill('Browser fixture administrator')
  await page.getByLabel('Email address').fill(email)
  await page.getByLabel('Temporary password').fill(PASSWORD)
  await expect(page.getByLabel('Account role')).toHaveValue('Administrator')
  await page.getByRole('button', { name: 'Provision', exact: true }).click()
  const accountRow = page.getByRole('row').filter({ hasText: email })
  await expect(page.getByRole('status')).toContainText(`Provisioned ${email}`)
  // Other browser cases can populate more than one account page.
  const nextAccounts = page.getByRole('navigation', { name: 'Pagination' }).getByRole('button', { name: 'Next', exact: true })
  while (await accountRow.count() === 0 && await nextAccounts.isVisible() && await nextAccounts.isEnabled()) {
    await nextAccounts.click()
  }
  await expect(accountRow).toContainText('Disabled')
  await accountRow.getByRole('button', { name: 'Activate', exact: true }).click()
  await expect(accountRow).toContainText('Active')
  await page.goto('/admin/curriculum')
  await page.getByLabel('Concept code', { exact: true }).fill('BROWSER-C')
  await page.getByLabel('Concept name', { exact: true }).fill('Browser fixture concept')
  await page.getByLabel('Subject area', { exact: true }).fill('Database Design')
  await page.getByRole('button', { name: 'Add concept', exact: true }).click()
  const conceptRow = page.locator('li').filter({ has: page.getByLabel('Prerequisites for BROWSER-C', { exact: true }) })
  await expect(conceptRow).toBeVisible()
  await conceptRow.getByRole('button', { name: 'Edit', exact: true }).click()
  await page.getByLabel('Concept name', { exact: true }).fill('Edited browser fixture concept')
  await page.getByRole('button', { name: 'Save concept', exact: true }).click()
  await expect(conceptRow).toContainText('Edited browser fixture concept')
  const concepts = await request(page, '/api/v1/admin/concepts')
  const cid = concepts.find(c => c.concept_code === 'BROWSER-C').concept_id
  const prerequisites = page.getByLabel('Prerequisites for SQL-WHERE', { exact: true })
  const before = await prerequisites.inputValue()
  await prerequisites.locator('..').getByRole('button', { name: 'Save', exact: true }).click()
  await expect(prerequisites).toHaveValue(before)
  await page.getByLabel('Prerequisites for BROWSER-C', { exact: true }).fill(String(fixture.concept_ids['SQL-SELECT']))
  await conceptRow.getByRole('button', { name: 'Save', exact: true }).click()
  await expect(page.getByLabel('Prerequisites for BROWSER-C', { exact: true })).toHaveValue(String(fixture.concept_ids['SQL-SELECT']))
  await page.getByLabel('CLO code', { exact: true }).fill('BROWSER-CLO')
  await page.getByLabel('CLO title', { exact: true }).fill('Browser fixture outcome')
  await page.getByRole('button', { name: 'Add CLO', exact: true }).click()
  const cloRow = page.locator('li').filter({ has: page.getByLabel('Confirmed concepts for BROWSER-CLO', { exact: true }) })
  await cloRow.getByRole('button', { name: 'Edit', exact: true }).click()
  await page.getByLabel('CLO title', { exact: true }).fill('Edited browser fixture outcome')
  await page.getByRole('button', { name: 'Save CLO', exact: true }).click()
  await page.getByLabel('Confirmed concepts for BROWSER-CLO', { exact: true }).fill(String(cid))
  await cloRow.getByRole('button', { name: 'Save set', exact: true }).click()
  await expect(page.getByLabel('Confirmed concepts for BROWSER-CLO', { exact: true })).toHaveValue(String(cid))
  await cloRow.getByRole('button', { name: 'Save set', exact: true }).click()
  await expect(page.getByLabel('Confirmed concepts for BROWSER-CLO', { exact: true })).toHaveValue(String(cid))
  await cloRow.getByRole('button', { name: 'AI suggest', exact: true }).click()
  await expect(cloRow).toContainText('Pending')
  await cloRow.getByRole('button', { name: 'Confirm', exact: true }).click()
  await expect(cloRow.getByRole('button', { name: 'Confirm', exact: true })).toHaveCount(0)
  await page.goto('/admin/questions')
  await page.getByRole('button', { name: 'New question', exact: true }).click()
  const prompt = `Browser curation ${Date.now()}: choose SELECT`
  await page.getByLabel('Question prompt', { exact: true }).fill(prompt)
  await page.getByLabel('Option 1 text').fill('SELECT')
  await page.getByLabel('Option 2 text').fill('DROP')
  await page.getByRole('checkbox').first().check()
  await page.getByRole('checkbox').nth(1).uncheck()
  const createdQuestion = page.waitForResponse(response => response.url().endsWith('/api/v1/admin/questions') && response.request().method() === 'POST')
  await page.getByRole('button', { name: 'Create', exact: true }).click()
  expect((await createdQuestion).status()).toBe(201)
  await page.getByLabel('Search prompt').fill(prompt)
  const questionRow = page.locator('li').filter({ hasText: prompt })
  await expect(questionRow).toBeVisible()
  await questionRow.getByRole('button', { name: 'AI tags', exact: true }).click()
  await expect(questionRow).toContainText('Pending')
  await questionRow.getByRole('button', { name: 'Edit', exact: true }).click()
  await page.getByRole('button', { name: 'Save changes', exact: true }).click()
  await expect(questionRow).toContainText('Pending')
  await questionRow.getByRole('button', { name: 'Confirm', exact: true }).click()
  await questionRow.getByRole('button', { name: 'Approve difficulty and criteria' }).click()
  await questionRow.getByRole('button', { name: 'Validate', exact: true }).click()
  await expect(questionRow).toContainText('Validated')
  await page.getByLabel('Filter by type').selectOption('mcq')
  await page.getByLabel('Filter by difficulty').selectOption('2')
  await expect(questionRow).toBeVisible()
  await page.goto('/admin/assessments')
  await page.getByRole('button', { name: 'New assessment', exact: true }).click()
  await page.getByLabel('Assessment title').fill('Browser fixture assessment')
  await page.getByLabel('Target concept 1', { exact: true }).selectOption(String(fixture.concept_ids['SQL-SELECT']))
  await page.getByRole('button', { name: '+ add concept', exact: true }).click()
  await page.getByLabel('Target concept 2', { exact: true }).selectOption(String(fixture.concept_ids['DB-3NF']))
  await page.getByRole('button', { name: 'Create draft', exact: true }).click()
  const assessmentRow = page.locator('li').filter({ hasText: 'Browser fixture assessment' })
  await expect(assessmentRow).toContainText('Draft')
  // A single SQL concept cannot cover two distinct SQL families: actionable error.
  await assessmentRow.getByRole('button', { name: 'Publish', exact: true }).click()
  await expect(page.getByRole('alert').first()).toBeVisible()
  await assessmentRow.getByRole('button', { name: 'Edit', exact: true }).click()
  for (const [i, code] of ['SQL-WHERE', 'SQL-JOIN', 'SQL-GROUP', 'SQL-HAVING', 'SQL-SUBQUERY', 'DB-ER', 'DB-NORM', 'DB-FD', 'DB-1NF', 'DB-2NF'].entries()) {
    await page.getByRole('button', { name: '+ add concept', exact: true }).click()
    await page.getByLabel(`Target concept ${i + 3}`, { exact: true }).selectOption(String(fixture.concept_ids[code]))
  }
  await page.getByRole('button', { name: 'Save changes', exact: true }).click()
  await expect(assessmentRow).toContainText('12 concepts')
  const published = page.waitForResponse(response => /\/api\/v1\/admin\/assessments\/\d+$/.test(response.url()) && response.request().method() === 'PATCH')
  await assessmentRow.getByRole('button', { name: 'Publish', exact: true }).click()
  const publication = await published
  expect(publication.status(), JSON.stringify(await publication.json())).toBe(200)
  await expect(assessmentRow).toContainText('Published')
  await page.goto('/admin/candidates')
  await page.getByRole('combobox', { name: 'Concept', exact: true }).selectOption(String(cid))
  await page.getByRole('button', { name: 'Generate', exact: true }).click()
  await expect(page.getByRole('button', { name: 'Approve into bank', exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'Approve into bank', exact: true }).click()
  await expect(page.getByText(/promoted → question/)).toBeVisible()
  await page.goto('/admin')
  await page.getByLabel('Analytics assessment').selectOption(String(fixture.assessment_ids[0]))
  await expect(page.getByRole('heading', { name: 'Cohort Overview' })).toBeVisible()
  await checkPage(page, 'admin-analytics')
  expect(errors).toEqual([])
})

test('admin native select controls use readable theme surfaces', async ({ page }) => {
  await login(page, 'release-admin@test.dev')
  const routes = [
    ['/admin', null],
    ['/admin/accounts', null],
    ['/admin/curriculum', null],
    ['/admin/questions', null],
    ['/admin/candidates', null],
    ['/admin/assessments', 'New assessment'],
  ]

  for (const mode of ['dark', 'light']) {
    await selectTheme(page, mode)
    for (const [route, openButton] of routes) {
      await page.goto(route)
      await page.waitForLoadState('networkidle')
      if (openButton) await page.getByRole('button', { name: openButton, exact: true }).click()

      const selects = page.locator('select:visible')
      await expect(selects.first()).toBeVisible()
      const styles = await selects.evaluateAll(nodes => nodes.map(select => {
        const control = getComputedStyle(select)
        return {
          label: select.getAttribute('aria-label') || select.closest('label')?.innerText?.trim() || '',
          background: control.backgroundColor,
          color: control.color,
          border: control.borderColor,
          options: [...select.options].map(option => {
            const style = getComputedStyle(option)
            return { background: style.backgroundColor, color: style.color }
          }),
        }
      }))

      for (const select of styles) {
        expect(select.background, `${route} ${mode} ${select.label}: select surface`).not.toBe('rgba(0, 0, 0, 0)')
        expect(select.color, `${route} ${mode} ${select.label}: select text`).not.toBe('rgba(0, 0, 0, 0)')
        expect(select.border, `${route} ${mode} ${select.label}: select border`).not.toBe('rgba(0, 0, 0, 0)')
        expect(select.options.length, `${route} ${mode} ${select.label}: options`).toBeGreaterThan(0)
        for (const option of select.options) {
          expect(option.background, `${route} ${mode} ${select.label}: option surface`).not.toBe('rgba(0, 0, 0, 0)')
          expect(option.color, `${route} ${mode} ${select.label}: option text`).not.toBe('rgba(0, 0, 0, 0)')
        }
      }
      expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(await page.evaluate(() => document.documentElement.clientWidth) + 1)
    }
  }
})

for (const width of [390, 768, 1024, 1440]) {
  test(`critical routes remain accessible and fit ${width}px`, async ({ page }) => {
    test.setTimeout(300_000)
    await page.setViewportSize({ width, height: 1000 })
    await page.emulateMedia({ reducedMotion: 'reduce' })
    const errors = [], browserPageErrors = [], benignBrowserErrors = []
    const consoleErrors = [], warnings = [], failedRequests = [], cancelledRequests = [], cancellationCandidates = [], calls = new Map()
    const successfulScriptPaths = new Set(), successfulReadPaths = new Set(), successfulGetPaths = new Set(), unexpectedHttpResponses = []
    let dashboardVerified = false
    page.on('pageerror', error => browserPageErrors.push({ message: error.message, stack: error.stack }))
    page.on('console', message => {
      if (message.type() === 'error') consoleErrors.push(message.text())
      if (message.type() === 'warning') warnings.push(message.text())
    })
    page.on('requestfailed', req => {
      cancellationCandidates.push({ path: new URL(req.url()).pathname, reason: req.failure()?.errorText,
        method: req.method(), resourceType: req.resourceType(), isNavigationRequest: req.isNavigationRequest() })
    })
    page.on('response', response => {
      const path = new URL(response.url()).pathname
      if (response.status() >= 400) unexpectedHttpResponses.push({ path, status: response.status() })
      if (response.status() < 400 && response.request().method() === 'GET') successfulGetPaths.add(path)
      if (response.status() < 400 && response.request().resourceType() === 'script') successfulScriptPaths.add(path)
      if (response.status() < 400 && ['xhr', 'fetch'].includes(response.request().resourceType()) &&
          ['/api/v1/auth/me', '/api/v1/auth/oauth/providers'].includes(path)) successfulReadPaths.add(path)
    })
    page.on('request', req => {
      const route = new URL(req.url()).pathname
      if (route.startsWith('/api/')) calls.set(route, (calls.get(route) ?? 0) + 1)
    })
    await page.goto('/login')
    await checkPage(page, 'login')
    await page.goto('/register')
    await checkPage(page, 'register')
    await login(page, learnerEmail)
    for (const [route, name] of [['/assessments', 'assessments'], ['/dashboard', 'dashboard'], ['/history', 'history'], [`/history/${finalizedSession}`, 'evidence']]) {
      calls.clear()
      await page.goto(route)
      await page.waitForLoadState('networkidle')
      await checkPage(page, name)
      if (name === 'dashboard') dashboardVerified = true
      expect([...calls].filter(([, count]) => count > 8), `${name}: repeated request loop`).toEqual([])
    }
    await page.goto('/assessments')
    await page.getByRole('button', { name: 'Start again', exact: true }).click()
    await expect(page).toHaveURL(/\/exam\/\d+$/)
    const sid = Number(page.url().split('/').at(-1))
    await checkPage(page, 'exam-mcq')
    const admin = await adminToken(page)
    for (let i = 0; i < 13; i++) {
      const state = await request(page, `/api/v1/sessions/${sid}`)
      const q = state.current_question
      if (q.question_type === 'sql') break
      const key = await request(page, `/api/v1/admin/questions/${q.question_id}`, { token: admin })
      await request(page, `/api/v1/sessions/${sid}/submit`, { method: 'POST', data: {
        question_id: q.question_id, ...(q.question_type === 'mcq' ? { selected_option_id: key.options.find(o => o.is_correct).option_id } : { essay_answer: key.reference_answer }),
      } })
    }
    await page.reload()
    await expect(page.getByLabel('Your query', { exact: true })).toBeVisible()
    await page.getByLabel('Your query', { exact: true }).fill('SELECT 1 AS value')
    await page.getByRole('button', { name: 'Run in sandbox' }).click()
    await expect(page.getByText(/\d+ rows? · [\d,.]+ ms/)).toBeVisible()
    await checkPage(page, 'exam-sql')
    await page.getByRole('button', { name: 'Finish assessment', exact: true }).click()
    const dialog = page.getByRole('dialog')
    await expect(dialog).toBeVisible()
    const bounds = await dialog.locator('..').boundingBox()
    expect(bounds.x).toBe(0)
    expect(bounds.width).toBe(width)
    expect(bounds.height).toBe(1000)
    const modalScan = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze()
    expect(modalScan.violations.map(v => v.id)).toEqual([])
    await page.getByRole('button', { name: 'Yes, finish' }).click()
    await expect(page).toHaveURL(/\/dashboard$/)
    await page.waitForLoadState('networkidle')
    await page.evaluate(() => localStorage.clear())
    await login(page, 'release-admin@test.dev')
    for (const [route, name] of [['/admin', 'admin'], ['/admin/accounts', 'admin-accounts'], ['/admin/curriculum', 'admin-curriculum'], ['/admin/questions', 'admin-questions'], ['/admin/assessments', 'admin-assessments'], ['/admin/candidates', 'admin-candidates']]) {
      calls.clear()
      await page.goto(route)
      await page.waitForLoadState('networkidle')
      await checkPage(page, name)
      expect([...calls].filter(([, count]) => count > 8), `${name}: repeated request loop`).toEqual([])
    }
    for (const failure of cancellationCandidates) {
      if (isBenignResolvedCancellation(failure, { successfulScriptPaths, successfulReadPaths, successfulGetPaths, routeVerified: dashboardVerified })) {
        cancelledRequests.push({ ...failure, resolution: 'same resource succeeded and dashboard route was verified' })
      } else failedRequests.push(failure)
    }
    for (const error of browserPageErrors) {
      const path = webkitCancelledAuthPath(error)
      if (isBenignResolvedWebkitAuthError(error, { successfulReadPaths, routeVerified: dashboardVerified })) {
        benignBrowserErrors.push({ path, resolution: 'WebKit reports a cancelled optional auth XHR as a page error; same endpoint returned successfully and route checks passed' })
      } else errors.push(error.message)
    }
    expect(errors).toEqual([])
    expect(consoleErrors).toEqual([])
    expect(failedRequests).toEqual([])
    expect(unexpectedHttpResponses).toEqual([])
    await fs.writeFile(path.join(ARTIFACTS, `browser-console-${width}.json`), JSON.stringify({ runtimeErrors: errors, consoleErrors, failedRequests, cancelledRequests, benignBrowserErrors, unexpectedHttpResponses, warnings }, null, 2))
  })
}

test('normal motion stays bounded and keyboard focus remains visible', async ({ page, browser }) => {
  await page.emulateMedia({ reducedMotion: 'no-preference' })
  await page.goto('/login')
  await expect(page.getByRole('heading', { name: 'Sign in to DBCAS' })).toBeVisible()
  const duration = await page.locator('.auth-enter').evaluate(node => parseFloat(getComputedStyle(node).animationDuration))
  expect(duration).toBeGreaterThan(0)
  expect(duration).toBeLessThanOrEqual(.36)
  await page.getByLabel('Email', { exact: true }).focus()
  await expect(page.getByLabel('Email', { exact: true })).toBeFocused()
  const focus = await page.getByLabel('Email', { exact: true }).evaluate(node => ({ shadow: getComputedStyle(node).boxShadow, outline: getComputedStyle(node).outlineStyle }))
  expect(focus.shadow !== 'none' || focus.outline !== 'none').toBeTruthy()
  await page.waitForTimeout(400)
  expect(await page.locator('.auth-enter').evaluate(node => getComputedStyle(node).transform)).toMatch(/none|matrix\(1, 0, 0, 1, 0, 0\)/)
  // Verify native keyboard use on the shared header controls.
  const language = page.getByRole('button', { name: 'Language', exact: true })
  await language.focus()
  await page.keyboard.press('ArrowDown')
  await expect(page.getByRole('menuitemradio', { name: 'Tiếng Việt' })).toBeFocused()
  await page.keyboard.press('Escape')
  await expect(language).toBeFocused()
  await expect(page.getByRole('menu')).toBeHidden()
  await page.getByRole('button', { name: 'Switch to light theme' }).focus()
  await page.keyboard.press('Enter')
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light')
  await page.keyboard.press('Space')
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')

  // Sample moving media, not just the presence of a video element or poster.
  await page.goto('/')
  const verifyVideo = async name => {
    for (const mode of ['dark', 'light']) {
      await selectTheme(page, mode)
      const video = page.locator('video').first()
      await expect(video).toBeVisible()
      await expect.poll(() => video.evaluate(node => !node.paused && node.readyState >= 2)).toBe(true)
      const before = await video.evaluate(node => node.currentTime)
      await expect.poll(() => video.evaluate(node => node.currentTime)).not.toBe(before)
      await page.screenshot({ path: path.join(ARTIFACTS, `moving-${name}-${mode}.png`), fullPage: true })
    }
  }
  await verifyVideo('landing')
  await register(page, 'media')
  await verifyVideo('dashboard')
  await page.goto('/assessments')
  await verifyVideo('assessments')

  const touchContext = await browser.newContext({ hasTouch: true, viewport: { width: 390, height: 844 }, locale: 'en-US', baseURL: 'http://127.0.0.1:5174' })
  try {
    const touchPage = await touchContext.newPage()
    await touchPage.goto('/')
    await touchPage.getByRole('button', { name: 'Language', exact: true }).tap()
    await expect(touchPage.getByRole('menu')).toBeVisible()
    await touchPage.getByRole('menuitemradio', { name: 'Tiếng Việt' }).tap()
    await expect(touchPage.getByRole('menu')).toBeHidden()
    await touchPage.reload()
    await expect(touchPage.locator('html')).toHaveAttribute('lang', 'vi')
    await touchPage.getByRole('button', { name: 'Ngôn ngữ', exact: true }).tap()
    await touchPage.getByRole('heading', { level: 1 }).tap()
    await expect(touchPage.getByRole('menu')).toBeHidden()
  } finally { await touchContext.close() }
})
