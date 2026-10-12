import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'
import fs from 'node:fs/promises'
import path from 'node:path'

const API = 'http://127.0.0.1:8100'
const PASSWORD = 'ReleaseTest123!'
const ARTIFACTS = path.resolve(process.env.DBCAS_E2E_OUTPUT ?? '../../_review/remediation', 'screenshots', process.env.DBCAS_BROWSER ?? 'chromium', 'localization')
const catalogs = Object.fromEntries(await Promise.all(['en', 'vi'].map(async locale => [locale, JSON.parse(await fs.readFile(new URL(`../src/i18n/${locale}.json`, import.meta.url), 'utf8'))])))
const label = (locale, key) => key.split('.').reduce((value, part) => value[part], catalogs[locale])
test.use({ locale: 'vi-VN', reducedMotion: 'reduce' })

async function api(page, route, { method = 'GET', data, token } = {}) {
  token ??= await page.evaluate(() => localStorage.getItem('dbcas_token'))
  const response = await page.request.fetch(`${API}${route}`, { method, data, headers: { Connection: 'close', ...(token ? { Authorization: `Bearer ${token}` } : {}) } })
  expect(response.ok(), `${method} ${route}: HTTP ${response.status()}`).toBe(true)
  return response.json()
}

async function switchLocale(page, locale) {
  await page.getByRole('combobox', { name: /^(Language|Ngôn ngữ)$/ }).selectOption(locale)
  await expect(page.locator('html')).toHaveAttribute('lang', locale)
  expect(await page.evaluate(() => localStorage.getItem('dbcas_locale'))).toBe(locale)
}

async function login(page, email, locale) {
  await page.goto('/login')
  await page.getByLabel(label(locale, 'common.email'), { exact: true }).fill(email)
  await page.getByLabel(label(locale, 'auth.password'), { exact: true }).fill(PASSWORD)
  await page.getByRole('button', { name: label(locale, 'auth.signIn'), exact: true }).click()
  await expect(page).toHaveURL(email === 'release-admin@test.dev' ? /\/admin$/ : /\/dashboard$/)
}

async function checkPage(page, locale, name) {
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  await expect(page.locator('.skeleton')).toHaveCount(0)
  await expect(page.getByRole('alert')).toHaveCount(0)
  await expect(page.locator('html')).toHaveAttribute('lang', locale)
  await page.evaluate(() => document.fonts.ready)
  const width = page.viewportSize().width
  expect(await page.evaluate(() => document.documentElement.scrollWidth), `${locale}/${name}: viewport overflow`).toBeLessThanOrEqual(width + 1)
  const scan = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze()
  expect(scan.violations.map(v => ({ id: v.id, nodes: v.nodes.map(n => n.target) })), `${locale}/${name}: accessibility`).toEqual([])
  await fs.mkdir(ARTIFACTS, { recursive: true })
  await page.screenshot({ path: path.join(ARTIFACTS, `${locale}-${name}-${width}.png`), fullPage: true })
}

for (const locale of ['en', 'vi']) for (const width of [390, 768, 1024, 1440]) {
  test(`${locale} real workspaces preserve answers and fit ${width}px`, async ({ page }) => {
    test.setTimeout(240_000)
    await page.setViewportSize({ width, height: 1000 })
    const errors = []
    const consoleErrors = [], failedRequests = [], cancelledRequests = [], failedModules = []
    page.on('pageerror', error => errors.push(error.message))
    page.on('console', entry => { if (entry.type() === 'error') consoleErrors.push(entry.text()) })
    page.on('requestfailed', request => {
      const failure = { path: new URL(request.url()).pathname, reason: request.failure()?.errorText }
      if (['NS_BINDING_ABORTED', 'net::ERR_ABORTED', 'cancelled', 'Cancelled'].includes(failure.reason)) cancelledRequests.push(failure)
      else failedRequests.push(failure)
    })
    page.on('response', response => {
      if (response.request().resourceType() === 'script' && response.status() >= 400) {
        failedModules.push({ path: new URL(response.url()).pathname, status: response.status() })
      }
    })
    await page.goto('/login')
    await expect(page.locator('html')).toHaveAttribute('lang', 'vi') // browser preference, no saved locale
    await switchLocale(page, locale)
    await page.reload()
    await checkPage(page, locale, 'login') // saved preference wins over vi-VN when English is chosen
    const email = `locale-${locale}-${width}-${Date.now()}@test.dev`
    await api(page, '/api/v1/auth/register', { method: 'POST', token: '', data: { name: 'Localization fixture learner', email, password: PASSWORD, password_confirm: PASSWORD } })
    await login(page, email, locale)
    await page.goto('/assessments')
    await checkPage(page, locale, 'assessments')
    await page.getByRole('button', { name: label(locale, 'assessment.start'), exact: true }).click()
    await expect(page).toHaveURL(/\/exam\/\d+$/)
    const sid = Number(page.url().split('/').at(-1))
    await expect(page.getByRole('radio').first()).toBeVisible()
    await page.getByRole('radio').first().locator('..').click()
    const selectedOption = await page.getByRole('radio').first().inputValue()
    const otherLocale = locale === 'en' ? 'vi' : 'en'
    await switchLocale(page, otherLocale)
    await expect(page.locator(`input[value="${selectedOption}"]`)).toBeChecked()
    await switchLocale(page, locale)
    await page.getByRole('button', { name: label(locale, 'exam.saveDraft'), exact: true }).click()
    await expect(page.getByText(label(locale, 'exam.draftSaved'), { exact: true })).toBeVisible()
    await checkPage(page, locale, 'exam-mcq')

    const admin = await api(page, '/api/v1/auth/login', { method: 'POST', token: '', data: { email: 'release-admin@test.dev', password: PASSWORD } })
    let sqlQuestion
    // Advance through the actual adaptive API; do not replace its order with a demo sequence.
    for (let i = 0; i < 13; i++) {
      const state = await api(page, `/api/v1/sessions/${sid}`)
      const question = state.current_question
      expect(question).toBeTruthy()
      if (question.question_type === 'sql') { sqlQuestion = question; break }
      const answer = await api(page, `/api/v1/admin/questions/${question.question_id}`, { token: admin.access_token })
      await api(page, `/api/v1/sessions/${sid}/submit`, { method: 'POST', data: { question_id: question.question_id,
        ...(question.question_type === 'mcq' ? { selected_option_id: answer.options.find(o => o.is_correct).option_id } : { essay_answer: answer.reference_answer }),
      } })
    }
    expect(sqlQuestion).toBeTruthy()
    await page.reload()
    const query = "SELECT 'Original learner SQL' AS value"
    await page.getByLabel(label(locale, 'sql.query'), { exact: true }).fill(query)
    await switchLocale(page, otherLocale)
    await expect(page.getByLabel(label(otherLocale, 'sql.query'), { exact: true })).toHaveValue(query)
    await switchLocale(page, locale)
    await page.getByRole('button', { name: label(locale, 'sql.run'), exact: true }).click()
    await expect(page.getByRole('cell', { name: 'Original learner SQL', exact: true })).toBeVisible()
    await checkPage(page, locale, 'exam-sql')
    await page.getByRole('button', { name: label(locale, 'exam.saveDraft'), exact: true }).click()
    await expect(page.getByText(label(locale, 'exam.draftSaved'), { exact: true })).toBeVisible()
    await page.reload()
    await expect(page.getByLabel(label(locale, 'sql.query'), { exact: true })).toHaveValue(query)
    await page.getByRole('button', { name: label(locale, 'exam.finish'), exact: true }).click()
    await expect(page.getByRole('dialog', { name: label(locale, 'exam.finishTitle') })).toBeVisible()
    await page.getByRole('button', { name: label(locale, 'exam.confirmFinish'), exact: true }).click()
    await expect(page).toHaveURL(/\/dashboard$/)
    await expect(page.locator('canvas')).toHaveCount(2)
    await checkPage(page, locale, 'dashboard')
    await page.goto('/history')
    await checkPage(page, locale, 'history')
    await page.goto(`/history/${sid}`)
    await expect(page.getByRole('region', { name: label(locale, 'evidence.submittedAnswer') })).toContainText(query)
    await checkPage(page, locale, 'evidence')

    await page.evaluate(() => localStorage.removeItem('dbcas_token'))
    await login(page, 'release-admin@test.dev', locale)
    await page.goto('/admin/questions')
    await expect(page.getByRole('heading', { name: locale === 'vi' ? 'Ngân hàng câu hỏi' : 'Question bank', exact: true })).toBeVisible()
    await page.getByRole('button', { name: label(locale, 'admin.questions.new'), exact: true }).click()
    await page.getByRole('textbox', { name: label(locale, 'admin.questions.prompt'), exact: true }).fill('Original authored question')
    await switchLocale(page, otherLocale)
    await expect(page.getByRole('textbox', { name: label(otherLocale, 'admin.questions.prompt'), exact: true })).toHaveValue('Original authored question')
    await switchLocale(page, locale)
    await checkPage(page, locale, 'admin-questions')
    await fs.writeFile(path.join(ARTIFACTS, `${locale}-browser-console-${width}.json`), JSON.stringify({ runtimeErrors: errors, consoleErrors, failedRequests, cancelledRequests, failedModules }, null, 2))
    expect(errors).toEqual([])
    expect(consoleErrors).toEqual([])
    expect(failedRequests).toEqual([])
    expect(failedModules).toEqual([])
  })
}

test('unsupported browser language falls back to English without a saved preference', async ({ browser }) => {
  const context = await browser.newContext({ locale: 'fr-FR', baseURL: 'http://127.0.0.1:5174' })
  try {
    const page = await context.newPage()
    await page.goto('/login')
    await expect(page.locator('html')).toHaveAttribute('lang', 'en')
    await expect(page.getByRole('heading', { name: 'Sign in to DBCAS' })).toBeVisible()
  } finally { await context.close() }
})
