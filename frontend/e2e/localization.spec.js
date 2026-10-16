import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'
import fs from 'node:fs/promises'
import path from 'node:path'
import { isBenignResolvedCancellation, isBenignResolvedWebkitAuthError, webkitCancelledAuthPath } from './requestFailurePolicy.js'

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
  const theme = await page.evaluate(() => localStorage.getItem('dbcas_theme'))
  await page.getByRole('button', { name: /^(Language|Ngôn ngữ)$/ }).click()
  await page.getByRole('menuitemradio', { name: locale === 'vi' ? 'Tiếng Việt' : 'English', exact: true }).click()
  await expect(page.locator('html')).toHaveAttribute('lang', locale)
  expect(await page.evaluate(() => localStorage.getItem('dbcas_locale'))).toBe(locale)
  expect(await page.evaluate(() => localStorage.getItem('dbcas_theme'))).toBe(theme)
}

async function assertSqlTableContrast(page, phase) {
  if (!await page.locator('.data-table tbody td').count()) return
  const tableColors = await page.evaluate(() => {
    const resolvedColor = property => {
      const probe = document.createElement('span')
      probe.style.color = `var(${property})`
      document.body.append(probe)
      const color = getComputedStyle(probe).color
      probe.remove()
      return color
    }
    const root = document.documentElement
    const tokens = {
      text: resolvedColor('--text'),
      muted: resolvedColor('--text-muted'),
      subtle: resolvedColor('--text-subtle'),
    }
    const table = document.querySelector('.data-table')
    const cells = [...table.querySelectorAll('th, td')].map(node => {
      const style = getComputedStyle(node)
      const expected = node.classList.contains('text-mute') || node.closest('thead') ? tokens.subtle
        : node.classList.contains('text-sub') ? tokens.muted : tokens.text
      return { tag: node.tagName, text: node.textContent.trim().slice(0, 50), color: style.color, expected }
    })
    return {
      theme: root.dataset.theme,
      transitioning: root.hasAttribute('data-theme-transitioning'),
      transition: getComputedStyle(table).transitionProperty,
      mismatches: cells.filter(cell => cell.color !== cell.expected),
    }
  })
  expect(tableColors.mismatches, `${phase}: SQL table semantic colors ${JSON.stringify(tableColors)}`).toEqual([])
  if (tableColors.transitioning) expect(tableColors.transition, `${phase}: transitions are disabled while resolving theme`).toBe('none')
  const contrast = await page.evaluate(() => {
    const cell = document.querySelector('.data-table tbody td')
    const channels = value => {
      const oklab = value.match(/oklab\(([\d.-]+)\s+([\d.-]+)\s+([\d.-]+)(?:\s*\/\s*([\d.]+))?\)/)
      if (oklab) {
        const [lightness, a, b] = oklab.slice(1, 4).map(Number)
        const l = (lightness + 0.3963377774 * a + 0.2158037573 * b) ** 3
        const m = (lightness - 0.1055613458 * a - 0.0638541728 * b) ** 3
        const s = (lightness - 0.0894841775 * a - 1.291485548 * b) ** 3
        const linear = [
          4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
          -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
          -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s,
        ]
        const rgb = linear.map(channel => Math.min(1, Math.max(0, channel <= 0.0031308 ? 12.92 * channel : 1.055 * channel ** (1 / 2.4) - 0.055)) * 255)
        return { rgb, alpha: oklab[4] ? Number(oklab[4]) : 1 }
      }
      const normalized = value.match(/color\(srgb\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)(?:\s*\/\s*([\d.]+))?\)/)
      if (normalized) return { rgb: normalized.slice(1, 4).map(Number).map(channel => channel * 255), alpha: normalized[4] ? Number(normalized[4]) : 1 }
      const rgb = value.match(/rgba?\(([^)]+)\)/)
      const parts = rgb?.[1].replace(/[,/]/g, ' ').trim().split(/\s+/).map(Number) ?? [0, 0, 0, 1]
      return { rgb: parts.slice(0, 3), alpha: parts.length > 3 ? parts[3] : 1 }
    }
    const layers = []
    for (let node = cell; node; node = node.parentElement) {
      const backgroundColor = getComputedStyle(node).backgroundColor
      const color = channels(backgroundColor)
      if (color.alpha > 0) layers.push({ ...color, source: backgroundColor })
    }
    let background = [255, 255, 255]
    for (const layer of layers.reverse()) background = layer.rgb.map((value, index) => value * layer.alpha + background[index] * (1 - layer.alpha))
    const foregroundColor = getComputedStyle(cell).color
    const foreground = channels(foregroundColor).rgb
    const luminance = rgb => rgb.map(value => value / 255).map(value => value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4)
      .reduce((sum, value, index) => sum + value * [0.2126, 0.7152, 0.0722][index], 0)
    const [a, b] = [luminance(foreground), luminance(background)].sort((left, right) => right - left)
    return { ratio: (a + 0.05) / (b + 0.05), foregroundColor, background, layers }
  })
  expect(contrast.ratio, `${phase}: normal SQL table text contrast (${JSON.stringify(contrast)})`).toBeGreaterThanOrEqual(4.5)
  const scan = await new AxeBuilder({ page }).include('.data-table').withRules(['color-contrast']).analyze()
  expect(scan.violations.map(violation => ({ id: violation.id, nodes: violation.nodes.map(node => ({ html: node.html, failureSummary: node.failureSummary, any: node.any })) })), `${phase}: SQL table contrast`).toEqual([])
}

async function switchTheme(page, locale, mode) {
  if (await page.locator('html').getAttribute('data-theme') !== mode) {
    await page.getByRole('button', { name: label(locale, mode === 'light' ? 'theme.switchToLight' : 'theme.switchToDark'), exact: true }).first().click()
  }
  await assertSqlTableContrast(page, `${locale}/${mode}/immediate`)
  const resolved = mode
  await expect(page.locator('html')).toHaveAttribute('data-theme', resolved)
  await expect(page.locator('html')).toHaveAttribute('data-theme-mode', mode)
  await expect(page.locator('html')).not.toHaveAttribute('data-theme-transitioning', 'true')
  await assertSqlTableContrast(page, `${locale}/${mode}/settled`)
  expect(await page.evaluate(() => localStorage.getItem('dbcas_theme') ?? 'dark')).toBe(mode)
  await expect(page.locator('html')).toHaveAttribute('lang', locale)
}

async function login(page, email, locale) {
  await page.goto('/login')
  await page.getByLabel(label(locale, 'common.email'), { exact: true }).fill(email)
  await page.getByLabel(label(locale, 'auth.password'), { exact: true }).fill(PASSWORD)
  await page.getByRole('button', { name: label(locale, 'auth.signIn'), exact: true }).click()
  const isAdmin = email === 'release-admin@test.dev'
  await expect(page).toHaveURL(isAdmin ? /\/admin$/ : /\/dashboard$/)
  await expect(page.getByRole('heading', {
    level: 1,
    name: label(locale, isAdmin ? 'admin.analytics.title' : 'dashboard.title'),
    exact: true,
  })).toBeVisible()
  await expect(page.locator('.skeleton')).toHaveCount(0)
}

async function checkPage(page, locale, name) {
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  await expect(page.locator('.skeleton')).toHaveCount(0)
  await expect(page.getByRole('alert')).toHaveCount(0)
  await expect(page.locator('html')).toHaveAttribute('lang', locale)
  await page.evaluate(() => document.fonts.ready)
  const width = page.viewportSize().width
  const theme = await page.locator('html').getAttribute('data-theme')
  if (name.startsWith('exam-')) {
    const timer = await page.locator('.timer-box').boundingBox()
    for (const part of await page.locator('.timer-label, .timer-value strong, .timer-value span').all()) {
      const bounds = await part.boundingBox()
      expect(bounds.x, `${locale}/${name}: timer text left edge`).toBeGreaterThanOrEqual(timer.x)
      expect(bounds.x + bounds.width, `${locale}/${name}: timer text right edge`).toBeLessThanOrEqual(timer.x + timer.width)
    }
  }
  for (const language of await page.getByRole('button', { name: label(locale, 'common.language'), exact: true }).all()) {
    await language.hover()
    const menu = page.getByRole('menu', { name: label(locale, 'common.language'), exact: true })
    await expect(menu).toBeVisible()
    await menu.getByRole('menuitemradio').first().hover()
    await page.waitForTimeout(160)
    await expect(menu).toBeVisible()
    const menuBounds = await menu.boundingBox()
    expect(menuBounds.x, `${locale}/${name}: language menu left edge`).toBeGreaterThanOrEqual(0)
    expect(menuBounds.x + menuBounds.width, `${locale}/${name}: language menu right edge`).toBeLessThanOrEqual(width)
    await page.mouse.move(width - 1, 999)
    await expect(menu).toBeHidden()
  }
  const layout = await page.evaluate(() => {
    const boundary = document.documentElement.clientWidth
    return {
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: boundary,
      innerWidth: window.innerWidth,
      offenders: [...document.querySelectorAll('body *')].flatMap(node => {
        const rect = node.getBoundingClientRect()
        return rect.width && (rect.left < -0.5 || rect.right > boundary + 0.5)
          ? [{ tag: node.tagName, className: typeof node.className === 'string' ? node.className : '', left: rect.left, right: rect.right, width: rect.width }]
          : []
      }).slice(0, 12),
    }
  })
  expect(layout.scrollWidth, `${locale}/${name}: viewport overflow ${JSON.stringify(layout)}`).toBeLessThanOrEqual(width + 1)
  const scan = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze()
  expect(scan.violations.map(v => ({ id: v.id, nodes: v.nodes.map(n => ({ target: n.target, failureSummary: n.failureSummary, html: n.html })) })), `${locale}/${name}: accessibility`).toEqual([])
  await fs.mkdir(ARTIFACTS, { recursive: true })
  await page.screenshot({ path: path.join(ARTIFACTS, `${locale}-${theme}-${name}-${width}.png`), fullPage: true })
}

async function checkBothThemes(page, locale, name) {
  let chartImage = null
  let chartPalette = null
  for (const mode of ['light', 'dark']) {
    await switchTheme(page, locale, mode)
    await checkPage(page, locale, name)
    if (name === 'dashboard') {
      const next = await page.locator('canvas').evaluateAll(canvases => canvases.map(canvas => canvas.toDataURL()))
      const palette = await page.evaluate(() => Array.from({ length: 10 }, (_, index) =>
        getComputedStyle(document.documentElement).getPropertyValue(`--chart-${index + 1}`).trim()))
      expect(new Set(palette).size, `${locale}/${mode}: chart palette colors are distinct`).toBe(10)
      if (chartImage) expect(next).not.toEqual(chartImage)
      if (chartPalette) expect(palette).not.toEqual(chartPalette)
      chartImage = next
      chartPalette = palette

      const refresh = page.getByRole('button', { name: label(locale, 'dashboard.refresh'), exact: true })
      const wasDisabled = await refresh.isDisabled()
      await refresh.evaluate(button => { button.disabled = true })
      const disabledScan = await new AxeBuilder({ page }).include('button.btn-ghost:disabled').withRules(['color-contrast']).analyze()
      expect(disabledScan.violations.map(violation => violation.id), `${locale}/${mode}: disabled ghost button contrast`).toEqual([])
      await refresh.evaluate((button, disabled) => { button.disabled = disabled }, wasDisabled)
    }
  }
  await switchTheme(page, locale, 'dark')
}

for (const locale of ['en', 'vi']) for (const width of [390, 768, 1024, 1440]) {
  test(`${locale} real workspaces preserve answers and fit ${width}px`, async ({ page }) => {
    test.setTimeout(240_000)
    await page.setViewportSize({ width, height: 1000 })
    const errors = [], browserPageErrors = [], benignBrowserErrors = []
    const consoleErrors = [], failedRequests = [], cancelledRequests = [], cancellationCandidates = [], failedModules = [], dashboardModuleResponses = []
    const successfulScriptPaths = new Set(), successfulReadPaths = new Set(), successfulGetPaths = new Set(), unexpectedHttpResponses = []
    let dashboardVerified = false
    page.on('pageerror', error => browserPageErrors.push({ message: error.message, stack: error.stack }))
    page.on('console', entry => { if (entry.type() === 'error') consoleErrors.push(entry.text()) })
    page.on('requestfailed', request => {
      const failure = { path: new URL(request.url()).pathname, reason: request.failure()?.errorText,
        method: request.method(), resourceType: request.resourceType(), isNavigationRequest: request.isNavigationRequest(),
        route: request.frame()?.url() ?? page.url() }
      cancellationCandidates.push(failure)
    })
    page.on('response', response => {
      const path = new URL(response.url()).pathname
      if (response.status() >= 400) unexpectedHttpResponses.push({ path, status: response.status() })
      if (response.status() < 400 && response.request().method() === 'GET') successfulGetPaths.add(path)
      if (response.status() < 400 && response.request().resourceType() === 'script') successfulScriptPaths.add(path)
      if (response.status() < 400 && ['xhr', 'fetch'].includes(response.request().resourceType()) &&
          ['/api/v1/auth/me', '/api/v1/auth/oauth/providers'].includes(path)) successfulReadPaths.add(path)
      if (path === '/src/pages/DashboardPage.jsx' || path.startsWith('/node_modules/.vite/deps/chart') || path.startsWith('/node_modules/.vite/deps/react-chartjs-2')) {
        dashboardModuleResponses.push({ path, status: response.status() })
      }
      if (response.request().resourceType() === 'script' && response.status() >= 400) {
        failedModules.push({ path: new URL(response.url()).pathname, status: response.status() })
      }
    })
    await page.emulateMedia({ colorScheme: 'light' })
    await page.goto('/login')
    await expect(page.locator('html')).toHaveAttribute('lang', 'vi') // browser preference, no saved locale
    await switchLocale(page, locale)
    await switchTheme(page, locale, 'light')
    await page.evaluate(() => document.fonts.ready)
    await page.reload()
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'light')
    await checkPage(page, locale, 'login') // saved preferences win after refresh
    await switchTheme(page, locale, 'dark')
    await checkPage(page, locale, 'login')
    // OS changes never override the explicit selection. Legacy state migrates safely.
    await page.emulateMedia({ colorScheme: 'light' })
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')
    for (const saved of ['system', 'unexpected']) {
      await page.evaluate(value => localStorage.setItem('dbcas_theme', value), saved)
      await page.reload()
      await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')
      await expect(page.locator('html')).toHaveAttribute('data-theme-mode', 'dark')
      expect(await page.evaluate(() => localStorage.getItem('dbcas_theme'))).toBe('dark')
    }
    await page.goto('/')
    await checkBothThemes(page, locale, 'landing')
    await page.goto('/register')
    await checkBothThemes(page, locale, 'register')
    const email = `locale-${locale}-${width}-${Date.now()}@test.dev`
    await api(page, '/api/v1/auth/register', { method: 'POST', token: '', data: { name: 'Localization fixture learner', email, password: PASSWORD, password_confirm: PASSWORD } })
    await login(page, email, locale)
    await page.goto('/assessments')
    await checkBothThemes(page, locale, 'assessments')
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
    await checkBothThemes(page, locale, 'exam-mcq')

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
    if (width === 390) {
      await page.locator('.data-table tbody tr').first().hover()
      await assertSqlTableContrast(page, `${locale}/light/hover`)
      await page.mouse.move(0, 0)
      await page.getByLabel(label(locale, 'sql.query'), { exact: true }).fill('SELECT * FROM missing_theme_review_table')
      await page.getByRole('button', { name: label(locale, 'sql.run'), exact: true }).click()
      await expect(page.getByRole('alert')).toBeVisible()
      const errorScan = await new AxeBuilder({ page }).include('[role="alert"]').withRules(['color-contrast']).analyze()
      expect(errorScan.violations.map(violation => violation.id), `${locale}: SQL error contrast`).toEqual([])
      await page.getByLabel(label(locale, 'sql.query'), { exact: true }).fill(query)
      await page.getByRole('button', { name: label(locale, 'sql.run'), exact: true }).click()
      await expect(page.getByRole('cell', { name: 'Original learner SQL', exact: true })).toBeVisible()
    }
    await checkBothThemes(page, locale, 'exam-sql')
    await page.getByRole('button', { name: label(locale, 'exam.saveDraft'), exact: true }).click()
    await expect(page.getByText(label(locale, 'exam.draftSaved'), { exact: true })).toBeVisible()
    if (width === 390) {
      await page.emulateMedia({ colorScheme: 'dark' })
      await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')
      await assertSqlTableContrast(page, `${locale}/explicit-dark/immediate`)
      await expect(page.locator('html')).not.toHaveAttribute('data-theme-transitioning', 'true')
      await assertSqlTableContrast(page, `${locale}/explicit-dark/settled`)
      await checkPage(page, locale, 'exam-sql-explicit-dark')
      await switchTheme(page, locale, 'dark')
      await page.reload()
      await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')
      await expect(page.getByLabel(label(locale, 'sql.query'), { exact: true })).toHaveValue(query)
      await page.getByRole('button', { name: label(locale, 'sql.run'), exact: true }).click()
      await expect(page.getByRole('cell', { name: 'Original learner SQL', exact: true })).toBeVisible()
      await assertSqlTableContrast(page, `${locale}/dark/reload`)
      await page.goto('/dashboard')
      await expect(page).toHaveURL(/\/dashboard$/)
      await page.waitForLoadState('networkidle')
      await page.goto(`/exam/${sid}`)
      await expect(page.getByLabel(label(locale, 'sql.query'), { exact: true })).toHaveValue(query)
      await page.getByRole('button', { name: label(locale, 'sql.run'), exact: true }).click()
      await expect(page.getByRole('cell', { name: 'Original learner SQL', exact: true })).toBeVisible()
      await assertSqlTableContrast(page, `${locale}/dark/navigation`)
    }
    await page.reload()
    await expect(page.getByLabel(label(locale, 'sql.query'), { exact: true })).toHaveValue(query)
    await page.getByRole('button', { name: label(locale, 'exam.finish'), exact: true }).click()
    await expect(page.getByRole('dialog', { name: label(locale, 'exam.finishTitle') })).toBeVisible()
    await page.getByRole('button', { name: label(locale, 'exam.confirmFinish'), exact: true }).click()
    await expect(page).toHaveURL(/\/dashboard$/)
    await expect(page.locator('canvas')).toHaveCount(2)
    dashboardVerified = true
    await checkBothThemes(page, locale, 'dashboard')
    await page.goto('/settings')
    await checkBothThemes(page, locale, 'settings')
    await page.goto('/history')
    await checkBothThemes(page, locale, 'history')
    await page.goto(`/history/${sid}`)
    await expect(page.getByRole('region', { name: label(locale, 'evidence.submittedAnswer') })).toContainText(query)
    await checkBothThemes(page, locale, 'evidence')

    await page.evaluate(() => localStorage.removeItem('dbcas_token'))
    await login(page, 'release-admin@test.dev', locale)
    await checkBothThemes(page, locale, 'admin')
    await page.goto('/admin/questions')
    await expect(page.getByRole('heading', { name: locale === 'vi' ? 'Ngân hàng câu hỏi' : 'Question bank', exact: true })).toBeVisible()
    await page.getByRole('button', { name: label(locale, 'admin.questions.new'), exact: true }).click()
    await page.getByRole('textbox', { name: label(locale, 'admin.questions.prompt'), exact: true }).fill('Original authored question')
    await switchLocale(page, otherLocale)
    await expect(page.getByRole('textbox', { name: label(otherLocale, 'admin.questions.prompt'), exact: true })).toHaveValue('Original authored question')
    await switchLocale(page, locale)
    await checkBothThemes(page, locale, 'admin-questions')
    for (const route of ['accounts', 'curriculum', 'candidates', 'assessments']) {
      await page.goto(`/admin/${route}`)
      await checkBothThemes(page, locale, `admin-${route}`)
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
      } else errors.push(error)
    }
    await fs.writeFile(path.join(ARTIFACTS, `${locale}-browser-console-${width}.json`), JSON.stringify({ runtimeErrors: errors, consoleErrors, failedRequests, cancelledRequests, benignBrowserErrors, failedModules, dashboardModuleResponses, successfulReadPaths: [...successfulReadPaths] }, null, 2))
    expect(errors).toEqual([])
    expect(consoleErrors).toEqual([])
    expect(failedRequests).toEqual([])
    expect(unexpectedHttpResponses, `${locale}: unexpected HTTP error responses`).toEqual([])
    expect(failedModules).toEqual([])
  })
}

test('unsupported browser language falls back while saved light appearance wins at startup', async ({ browser }) => {
  const context = await browser.newContext({
    locale: 'fr-FR', colorScheme: 'dark', baseURL: 'http://127.0.0.1:5174',
    storageState: { cookies: [], origins: [{ origin: 'http://127.0.0.1:5174', localStorage: [{ name: 'dbcas_theme', value: 'light' }] }] },
  })
  try {
    const page = await context.newPage()
    await page.goto('/login')
    await expect(page.locator('html')).toHaveAttribute('lang', 'en')
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'light')
    await expect(page.locator('html')).toHaveAttribute('data-theme-mode', 'light')
    expect(await page.evaluate(() => localStorage.getItem('dbcas_theme'))).toBe('light')
    await expect(page.getByRole('heading', { name: 'Sign in to DBCAS' })).toBeVisible()
  } finally { await context.close() }
})

test('admin tablet filter fits long assessment titles without hiding table scrolling', async ({ page }) => {
  await page.setViewportSize({ width: 768, height: 1000 })
  await login(page, 'release-admin@test.dev', 'vi')
  const selector = page.getByRole('combobox', { name: label('vi', 'admin.analytics.selector') })
  // Stress the native select's intrinsic width without changing stored assessment data.
  await selector.locator('option').last().evaluate(option => {
    option.textContent = 'PostgreSQL assessment with a deliberately long descriptive title for tablet layout regression coverage'
  })
  for (const theme of ['dark', 'light']) {
    await switchTheme(page, 'vi', theme)
    const layout = await selector.evaluate(select => {
      const bounds = select.getBoundingClientRect()
      const header = select.closest('header')
      const headerBounds = header.getBoundingClientRect()
      const style = getComputedStyle(header)
      return {
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
        bodyWidth: document.body.scrollWidth,
        selectRight: bounds.right,
        contentRight: headerBounds.right - parseFloat(style.paddingRight) - parseFloat(style.borderRightWidth),
      }
    })
    expect(layout.scrollWidth).toBe(layout.clientWidth)
    expect(layout.bodyWidth).toBe(layout.clientWidth)
    expect(layout.selectRight).toBeLessThanOrEqual(layout.contentRight + 0.01)
    const table = page.getByRole('region', { name: label('vi', 'admin.analytics.gapTable') })
    if (await table.count()) {
      const scrolling = await table.evaluate(region => {
        region.scrollLeft = region.scrollWidth
        return { width: region.clientWidth, scrollWidth: region.scrollWidth, scrollLeft: region.scrollLeft }
      })
      expect(scrolling.scrollWidth).toBeGreaterThan(scrolling.width)
      expect(scrolling.scrollLeft).toBeGreaterThan(0)
    }
  }
})
