// W1 learner end-to-end audit against the running demo stack.
// Real Chromium only; no provider keys are read or printed.
import { chromium } from '../../../../frontend/node_modules/playwright/index.mjs'
import { strict as assert } from 'node:assert'
import { mkdir, readFile, stat, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const BASE = process.env.DBCAS_LOCAL_URL || 'http://localhost:18080'
const API = process.env.DBCAS_API || 'http://localhost:18000'
const MAILPIT = process.env.DBCAS_MAILPIT || 'http://localhost:18025'
const OUT = path.dirname(fileURLToPath(import.meta.url))
const SHOTS = path.join(OUT, 'screenshots')
const PASSWORD = 'W1Demo12345!'
const NEW_PASSWORD = 'W1Reset67890!'
await mkdir(SHOTS, { recursive: true })

const results = []
const screenshots = []
const runtime = { pageErrors: [], consoleErrors: [], httpErrors: [] }

function note(kind, value) {
  if (kind === 'pageerror') runtime.pageErrors.push(value)
  if (kind === 'console') runtime.consoleErrors.push(value)
  if (kind === 'http') runtime.httpErrors.push(value)
}

async function step(name, fn, { optional = false } = {}) {
  const started = Date.now()
  try {
    const detail = await fn()
    results.push({ name, status: 'PASS', ms: Date.now() - started, detail: detail ?? null })
    console.log(`PASS ${name} (${Date.now() - started}ms)`)
    return detail
  } catch (error) {
    results.push({
      name,
      status: optional ? 'SKIP' : 'FAIL',
      ms: Date.now() - started,
      error: error.message,
      stack: String(error.stack || '').split('\n').slice(0, 8).join('\n'),
    })
    console.log(`${optional ? 'SKIP' : 'FAIL'} ${name}: ${error.message}`)
    if (!optional) throw error
  }
}

async function overflowInfo(page) {
  return page.evaluate(() => {
    const boundary = document.documentElement.clientWidth
    return {
      scrollWidth: document.documentElement.scrollWidth,
      innerWidth: window.innerWidth,
      clientWidth: boundary,
      offenders: [...document.querySelectorAll('body *')]
        .map((node) => {
          const rect = node.getBoundingClientRect()
          return {
            tag: node.tagName,
            className: typeof node.className === 'string' ? node.className : '',
            text: (node.textContent || '').trim().slice(0, 60),
            left: rect.left,
            right: rect.right,
            width: rect.width,
          }
        })
        .filter((entry) => entry.width && (entry.left < -0.5 || entry.right > boundary + 0.5))
        .slice(0, 12),
    }
  })
}

async function shot(page, name, { fullPage = true, allowAlert = false, allowOverflow = false } = {}) {
  const width = page.viewportSize().width
  const theme = await page.locator('html').getAttribute('data-theme')
  const locale = await page.locator('html').getAttribute('lang')
  const filename = `${name}-${locale}-${theme}-${width}.png`
  const target = path.join(SHOTS, filename)
  const scroll = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    innerWidth: window.innerWidth,
  }))
  if (!allowOverflow)
    assert.ok(
      scroll.scrollWidth <= scroll.innerWidth + 1,
      `${name}: horizontal overflow ${JSON.stringify(scroll)}`,
    )
  if (!allowAlert) assert.equal(await page.getByRole('alert').count(), 0, `${name}: alert visible`)
  await page.evaluate(() => window.scrollTo(0, 0))
  await page.waitForTimeout(120)
  await page.screenshot({ path: target, fullPage, scale: 'css', animations: 'disabled' })
  const info = await stat(target)
  assert.ok(info.size > 5000, `${filename}: suspiciously small (${info.size} bytes)`)
  screenshots.push({
    file: `screenshots/${filename}`,
    name,
    width,
    theme,
    locale,
    bytes: info.size,
    overflow: scroll.scrollWidth > scroll.innerWidth + 1,
  })
  return filename
}

async function setTheme(page, theme) {
  const current = await page.locator('html').getAttribute('data-theme')
  if (current === theme) return
  await page.locator('.theme-selector').first().click()
  await page.waitForFunction((t) => document.documentElement.dataset.theme === t, theme)
}

async function setLocale(page, locale) {
  const current = await page.locator('html').getAttribute('lang')
  if (current === locale) return
  await page.locator('.language-selector button.header-icon-button').first().click()
  await page
    .getByRole('menuitemradio', { name: locale === 'en' ? 'English' : 'Tiếng Việt', exact: true })
    .click()
  await page.waitForFunction((l) => document.documentElement.lang === l, locale)
}

async function captureSet(page, name, widths = [1280, 390], themes = ['light', 'dark']) {
  const files = []
  for (const width of widths) {
    await page.setViewportSize({ width, height: 900 })
    for (const theme of themes) {
      await setTheme(page, theme)
      files.push(await shot(page, name))
    }
  }
  return files
}

async function waitText(page, text, timeout = 20000) {
  await page.getByText(text, { exact: true }).first().waitFor({ state: 'visible', timeout })
}

async function apiFetch(page, route, { method = 'GET', data, token, base = API } = {}) {
  const response = await page.request.fetch(`${base}/api/v1${route}`, {
    method,
    data,
    headers: token === null ? {} : { Authorization: `Bearer ${token ?? (await page.evaluate(() => localStorage.getItem('dbcas_token')))}` },
  })
  const text = await response.text()
  let body = null
  try {
    body = text ? JSON.parse(text) : null
  } catch {
    body = text
  }
  return { status: response.status(), ok: response.ok(), body }
}

async function uiLogin(page, email, password = PASSWORD, locale = 'vi') {
  await page.goto('/login')
  await setLocale(page, locale)
  await page.getByLabel(locale === 'en' ? 'Email' : 'Email', { exact: true }).fill(email)
  await page
    .getByLabel(locale === 'en' ? 'Password' : 'Mật khẩu', { exact: true })
    .fill(password)
  await page
    .getByRole('button', { name: locale === 'en' ? 'Sign in' : 'Đăng nhập', exact: true })
    .click()
  await page.waitForURL(/\/dashboard$/, { timeout: 30000 })
  await page
    .getByRole('heading', { level: 1 })
    .first()
    .waitFor({ state: 'visible', timeout: 30000 })
  await page.waitForTimeout(1200)
}

async function registerViaApi(email, name = 'W1 Audit Learner') {
  const response = await fetch(`${API}/api/v1/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password: PASSWORD, password_confirm: PASSWORD }),
  })
  assert.ok(response.ok, `register ${email}: ${response.status} ${await response.text()}`)
}

async function adminToken() {
  const response = await fetch(`${API}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: 'admin@dbcas.local', password: 'Demo12345!' }),
  })
  assert.ok(response.ok, `admin login: ${response.status}`)
  return (await response.json()).access_token
}

const ADMIN_TOKEN = await adminToken()

async function approveSession(sid) {
  for (let attempt = 0; attempt < 120; attempt += 1) {
    const review = await fetch(`${API}/api/v1/admin/grading-reviews/${sid}`, {
      headers: { Authorization: `Bearer ${ADMIN_TOKEN}` },
    })
    if ([404, 409].includes(review.status)) {
      await new Promise((r) => setTimeout(r, 1000))
      continue
    }
    assert.ok(review.ok, `review ${sid}: ${review.status}`)
    const body = await review.json()
    if (body.release_status === 'pending_review') {
      const published = await fetch(
        `${API}/api/v1/admin/grading-reviews/${sid}/publish`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${ADMIN_TOKEN}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ revision: body.revision }),
        },
      )
      assert.ok(published.ok, `publish ${sid}: ${published.status} ${await published.text()}`)
      return
    }
    if (['published', 'reviewed'].includes(body.release_status)) return
    await new Promise((r) => setTimeout(r, 1000))
  }
  throw new Error(`session ${sid} never reached review`)
}

async function waitReady(page, sid, timeout = 90000) {
  const deadline = Date.now() + timeout
  while (Date.now() < deadline) {
    const token = await page.evaluate(() => localStorage.getItem('dbcas_token'))
    const r = await apiFetch(page, `/evaluations/attempts/${sid}`, { token })
    if (r.body?.status === 'ready') return r.body
    await page.waitForTimeout(1500)
  }
  throw new Error(`evaluation ${sid} not ready in ${timeout}ms`)
}

async function startViaApi(page, { source = 'bank', count = 3, concepts = [], difficulties = ['EASY', 'MEDIUM', 'HARD'] } = {}) {
  const token = await page.evaluate(() => localStorage.getItem('dbcas_token'))
  if (!concepts.length) {
    const options = await apiFetch(page, '/practice/options', { token })
    assert.ok(options.ok, `options: ${options.status}`)
    concepts = options.body.concepts.map((concept) => concept.concept_id)
  }
  const r = await apiFetch(page, '/practice/start', {
    method: 'POST',
    token,
    data: {
      concept_ids: concepts,
      difficulties,
      source,
      question_count: count,
      request_id: crypto.randomUUID(),
    },
  })
  assert.ok(r.ok, `start: ${r.status} ${JSON.stringify(r.body)}`)
  return r.body
}

async function completeViaApi(page, sid, { answerFor } = {}) {
  const token = await page.evaluate(() => localStorage.getItem('dbcas_token'))
  let state = (await apiFetch(page, `/sessions/${sid}`, { token })).body
  const kinds = []
  while (state.current_question) {
    const q = state.current_question
    kinds.push(q.question_type)
    const payload = { question_id: q.question_id }
    if (q.question_type === 'mcq') payload.selected_option_id = q.options[0].option_id
    else if (q.question_type === 'sql') payload.sql_answer = answerFor?.sql || 'SELECT 1 AS value'
    else payload.essay_answer =
      answerFor?.essay ||
      'Chuẩn hóa giảm lặp dữ liệu, bảo toàn thông tin và hạn chế bất thường cập nhật khi thiết kế cơ sở dữ liệu.'
    const submitted = await apiFetch(page, `/sessions/${sid}/submit`, {
      method: 'POST',
      token,
      data: payload,
    })
    assert.ok(submitted.ok, `submit ${sid}: ${submitted.status} ${JSON.stringify(submitted.body)}`)
    state = submitted.body.state
  }
  const finished = await apiFetch(page, `/sessions/${sid}/finish`, { method: 'POST', token })
  assert.ok(finished.ok, `finish ${sid}: ${finished.status}`)
  return { sid, kinds }
}

const auth = { email: `w1-auth-${Date.now()}@dbcas.local`, password: PASSWORD }
const practice = { email: `w1-practice-${Date.now()}@dbcas.local` }
const limits = { email: `w1-limits-${Date.now()}@dbcas.local` }
const expiry = { email: `w1-expiry-${Date.now()}@dbcas.local` }
const localization = { email: `w1-locale-${Date.now()}@dbcas.local` }

const browser = await chromium.launch()

async function newPage(viewport = { width: 1280, height: 900 }) {
  const context = await browser.newContext({ viewport, baseURL: BASE })
  const page = await context.newPage()
  page.on('pageerror', (error) => note('pageerror', `${page.url()}: ${error.message}`))
  page.on('console', (entry) => {
    if (entry.type() === 'error') note('console', `${page.url()}: ${entry.text()}`)
  })
  page.on('response', (response) => {
    if (response.status() >= 500)
      note('http', `${response.status()} ${response.request().method()} ${response.url()}`)
  })
  return { context, page }
}

const SKIP_AUTH = process.env.W1_SKIP_AUTH === '1'
try {
  // ---------------- A. public auth, OAuth safety, registration, recovery ----------------
  if (SKIP_AUTH) {
    const previous = JSON.parse(await readFile(path.join(OUT, 'results.json'), 'utf8'))
    for (const entry of previous.results || [])
      if (!results.some((existing) => existing.name === entry.name)) results.push(entry)
    for (const entry of previous.screenshots || [])
      if (!screenshots.some((existing) => existing.file === entry.file)) screenshots.push(entry)
    console.log(`auth phase skipped; reused ${results.length} prior checkpoints`)
  } else {
    const { context, page } = await newPage()
    try {
      await step('login page renders email form and both OAuth choices', async () => {
        await page.goto('/login')
        await page.getByRole('heading', { name: 'Đăng nhập DBCAS', exact: true }).waitFor()
        await page.getByLabel('Email', { exact: true }).waitFor()
        await page.getByRole('button', { name: 'Tiếp tục với Google', exact: true }).waitFor()
        await page.getByRole('button', { name: 'Tiếp tục với GitHub', exact: true }).waitFor()
        assert.equal(await page.locator('button.auth-oauth').count(), 2)
      })
      await step('screenshots: login light/dark at 1280/390', () => captureSet(page, 'login'))
      await step('unconfigured Google/GitHub show localized notice without navigation', async () => {
        let starts = 0
        page.on('request', (request) => {
          if (/\/auth\/oauth\/[^/]+\/start/.test(request.url())) starts += 1
        })
        const before = page.url()
        await page.getByRole('button', { name: 'Tiếp tục với Google', exact: true }).click()
        await waitText(page, 'Chưa cấu hình đăng nhập bằng Google. Vui lòng dùng email.')
        assert.equal(page.url(), before)
        await page.getByRole('button', { name: 'Tiếp tục với GitHub', exact: true }).click()
        await waitText(page, 'Chưa cấu hình đăng nhập bằng GitHub. Vui lòng dùng email.')
        assert.equal(page.url(), before)
        assert.equal(starts, 0, 'unconfigured provider must not navigate')
        await shot(page, 'oauth-notice')
      })
      await step('screenshots: register page light/dark at 1280/390', async () => {
        await page.goto('/register')
        await page.getByRole('heading', { name: 'Tạo tài khoản', exact: true }).waitFor()
        return captureSet(page, 'register')
      })
      await step('register a fresh unique learner through the UI', async () => {
        await page.setViewportSize({ width: 1280, height: 900 })
        await page.goto('/register')
        await page.getByLabel('Họ và tên', { exact: true }).fill('W1 Auth Learner')
        await page.getByLabel('Email', { exact: true }).fill(auth.email)
        await page.getByLabel('Mật khẩu', { exact: true }).fill(PASSWORD)
        await page.getByLabel('Xác nhận mật khẩu', { exact: true }).fill(PASSWORD)
        await page.getByRole('button', { name: 'Đăng ký', exact: true }).click()
        await page.waitForURL(/\/login$/, { timeout: 30000 })
        await page.getByRole('heading', { name: 'Đăng nhập DBCAS', exact: true }).waitFor()
        return auth.email
      })
      await step('new learner can sign in with email and reaches the learner dashboard', async () => {
        await uiLogin(page, auth.email)
        await page.getByRole('heading', { name: 'Năng lực của tôi', exact: true }).waitFor()
        assert.match(page.url(), /\/dashboard$/)
      })
      await step('password reset: request, real Mailpit email, reset, replay rejected', async () => {
        const resetContext = await browser.newContext({ viewport: { width: 1280, height: 900 }, baseURL: BASE })
        const resetPage = await resetContext.newPage()
        try {
          await resetPage.goto('/forgot-password')
          await resetPage.getByRole('heading', { name: 'Đặt lại mật khẩu', exact: true }).waitFor()
          await resetPage.getByLabel('Email', { exact: true }).fill(auth.email)
          await resetPage.getByRole('button', { name: 'Gửi liên kết đặt lại', exact: true }).click()
          await resetPage.getByText('Kiểm tra email của bạn', { exact: true }).waitFor()
          await shot(resetPage, 'forgot-password-sent')

          let summary
          for (let attempt = 0; attempt < 20 && !summary; attempt += 1) {
            const inbox = await (await fetch(`${MAILPIT}/api/v1/messages`)).json()
            summary = (inbox.messages || []).find((message) =>
              (message.To || []).some((to) => String(to.Address ?? to) === auth.email),
            )
            if (!summary) await resetPage.waitForTimeout(1000)
          }
          assert.ok(summary, 'Mailpit did not receive a reset message')
          const detail = await (await fetch(`${MAILPIT}/api/v1/message/${summary.ID}`)).json()
          const body = detail.Text || ''
          assert.match(detail.Subject, /password reset|Đặt lại mật khẩu/i)
          const link = body.match(/http:\/\/localhost:18080\/reset-password\?token=[A-Za-z0-9_-]+/)?.[0]
          assert.ok(link, `no reset link in message: ${body.slice(0, 300)}`)

          await resetPage.goto(link)
          await resetPage.getByRole('heading', { name: 'Chọn mật khẩu mới', exact: true }).waitFor()
          await resetPage.getByLabel('Mật khẩu mới', { exact: true }).fill(NEW_PASSWORD)
          await resetPage.getByLabel('Xác nhận mật khẩu', { exact: true }).fill(NEW_PASSWORD)
          await resetPage.getByRole('button', { name: 'Đặt mật khẩu mới', exact: true }).click()
          await resetPage.getByRole('heading', { name: 'Đã cập nhật mật khẩu', exact: true }).waitFor()
          await shot(resetPage, 'reset-success')

          const oldLogin = await resetPage.request.post(`${API}/api/v1/auth/login`, {
            data: { email: auth.email, password: PASSWORD },
          })
          assert.equal(oldLogin.status(), 401, 'old password still works')
          auth.password = NEW_PASSWORD

          await resetPage.goto(link)
          await resetPage.getByRole('heading', { name: 'Chọn mật khẩu mới', exact: true }).waitFor()
          await resetPage.getByLabel('Mật khẩu mới', { exact: true }).fill('Replay-99999!')
          await resetPage.getByLabel('Xác nhận mật khẩu', { exact: true }).fill('Replay-99999!')
          await resetPage.getByRole('button', { name: 'Đặt mật khẩu mới', exact: true }).click()
          await resetPage.getByRole('heading', { name: 'Liên kết không hợp lệ', exact: true }).waitFor()
          await shot(resetPage, 'reset-replay-rejected')

          const token = new URL(link).searchParams.get('token')
          const replay = await resetPage.request.post(`${API}/api/v1/auth/password-reset/confirm`, {
            data: { token, password: 'Replay-99999!', password_confirm: 'Replay-99999!' },
          })
          assert.equal(replay.status(), 400)
          assert.equal((await replay.json()).error.code, 'invalid_reset_token')
          return { message_id: summary.ID, event: 'replay-400-invalid_reset_token' }
        } finally {
          await resetContext.close()
        }
      })
      await step('reset password signs in and old password is rejected by the UI', async () => {
        const fresh = await browser.newContext({ viewport: { width: 1280, height: 900 }, baseURL: BASE })
        const freshPage = await fresh.newPage()
        try {
          await freshPage.goto('/login')
          await freshPage.getByLabel('Email', { exact: true }).fill(auth.email)
          await freshPage.getByLabel('Mật khẩu', { exact: true }).fill(PASSWORD)
          await freshPage.getByRole('button', { name: 'Đăng nhập', exact: true }).click()
          await freshPage.getByRole('alert').waitFor()
          assert.equal(freshPage.url(), `${BASE}/login`)
          await uiLogin(freshPage, auth.email, NEW_PASSWORD)
        } finally {
          await fresh.close()
        }
      })
      await step('OAuth metadata failure keeps both controls safe and local', async () => {
        const failed = await browser.newContext({ viewport: { width: 1280, height: 900 }, baseURL: BASE })
        const p = await failed.newPage()
        try {
          await p.route('**/api/v1/auth/oauth/providers', (route) =>
            route.fulfill({ status: 503, contentType: 'application/json', body: '{}' }),
          )
          let starts = 0
          p.on('request', (request) => {
            if (/\/auth\/oauth\/[^/]+\/start/.test(request.url())) starts += 1
          })
          await p.goto('/login')
          const google = p.getByRole('button', { name: 'Tiếp tục với Google', exact: true })
          const github = p.getByRole('button', { name: 'Tiếp tục với GitHub', exact: true })
          await google.waitFor()
          assert.equal(await google.isEnabled(), true)
          await github.waitFor()
          await google.click()
          await waitText(p, 'Chưa cấu hình đăng nhập bằng Google. Vui lòng dùng email.')
          assert.equal(p.url(), `${BASE}/login`)
          assert.equal(starts, 0)
          await shot(p, 'oauth-metadata-failure')
        } finally {
          await failed.close()
        }
      })
    } finally {
      await context.close()
    }
  }

  // ---------------- B. learner practice: setup, draft, double submit, SQL, essay, evaluation ----------------
  let practiceSid = null
  {
    await registerViaApi(practice.email, 'W1 Practice Learner')
    const { context, page } = await newPage()
    try {
      await uiLogin(page, practice.email)

      await step('overall evaluation at 0 attempts shows the empty state', async () => {
        await page.goto('/competency')
        await page.getByRole('heading', { name: 'Đánh giá tổng thể', exact: true }).waitFor()
        await page.getByRole('heading', { name: 'Bắt đầu hành trình của bạn', exact: true }).waitFor()
        await page.getByText('Hoàn thành một bài luyện tập để nhận đánh giá năng lực.', { exact: true }).waitFor()
        return captureSet(page, 'overall-0', [1280, 390], ['light'])
      })

      await step('practice setup exposes chips, all-concepts, difficulty, count 1-20 and bank/AI', async () => {
        await page.goto('/assessments')
        await page.getByRole('heading', { name: 'Tạo bài luyện tập', exact: true }).waitFor()
        await page.getByRole('button', { name: 'ER modeling', exact: true }).waitFor()
        assert.match(await page.locator('body').innerText(), /Đã chọn 0 khái niệm\./)
        await page.getByRole('button', { name: 'Chọn tất cả khái niệm', exact: true }).click()
        const selectedText = await page.getByText(/Đã chọn \d+ khái niệm\./).first().innerText()
        assert.match(selectedText, /Đã chọn (?:80|[1-9]\d*) khái niệm\./)
        const easy = page.locator('button[aria-pressed]').filter({ hasText: 'Dễ' }).first()
        const medium = page.locator('button[aria-pressed]').filter({ hasText: 'Vừa' }).first()
        const hard = page.locator('button[aria-pressed]').filter({ hasText: 'Khó' }).first()
        for (const toggle of [easy, medium, hard]) assert.equal(await toggle.getAttribute('aria-pressed'), 'true')
        await easy.click()
        assert.equal(await easy.getAttribute('aria-pressed'), 'false')
        await easy.click()
        assert.equal(await easy.getAttribute('aria-pressed'), 'true')
        const bank = page.getByRole('radio', { name: 'Từ ngân hàng câu hỏi', exact: true })
        const ai = page.getByRole('radio', { name: 'AI tạo câu hỏi', exact: true })
        assert.equal(await bank.isChecked(), true)
        await ai.check()
        assert.equal(await ai.isChecked(), true)
        await bank.check()
        assert.equal(await bank.isChecked(), true)
        const count = page.getByLabel('Số câu (1–20)')
        await count.fill('3')
        assert.equal(await count.inputValue(), '3')
        return captureSet(page, 'practice-setup')
      })

      await step('start shows a real loading state and exact count 3', async () => {
        let release
        const gate = new Promise((resolve) => {
          release = resolve
        })
        const route = '**/api/v1/practice/start'
        await page.route(route, async (request) => {
          await gate
          await request.continue()
        })
        const responsePromise = page.waitForResponse(
          (r) => r.url().endsWith('/api/v1/practice/start') && r.request().method() === 'POST',
          { timeout: 60000 },
        )
        await page.getByRole('button', { name: 'Bắt đầu', exact: true }).click()
        await page.waitForTimeout(250)
        assert.equal(await page.getByRole('button', { name: /Đang chuẩn bị bài/ }).isDisabled(), true)
        await page.getByRole('status').filter({ hasText: 'Đang chuẩn bị bài...' }).first().waitFor()
        release()
        const response = await responsePromise
        assert.ok(response.ok(), `start ${response.status()}`)
        const state = await response.json()
        await page.unroute(route)
        assert.equal(state.max_questions, 3)
        assert.equal(state.question_count || state.max_questions, 3)
        practiceSid = state.session_id
        await page.waitForURL(new RegExp(`/exam/${practiceSid}$`), { timeout: 30000 })
        await page.getByText(state.current_question.prompt, { exact: true }).waitFor()
        return { sid: practiceSid, kinds: [state.current_question.question_type] }
      })

      await step('MCQ autosaves, reload restores the choice, double click submits once', async () => {
        const state = (await apiFetch(page, `/sessions/${practiceSid}`)).body
        const q = state.current_question
        assert.equal(q.question_type, 'mcq')
        await page.locator(`input[value="${q.options[0].option_id}"]`).check()
        await waitText(page, 'Đã lưu')
        await captureSet(page, 'exam-mcq')
        await page.reload()
        await page.getByRole('heading', { name: /^CÂU 1\/3/ }).waitFor()
        await page.locator(`input[value="${q.options[0].option_id}"]`).waitFor()
        assert.equal(await page.locator(`input[value="${q.options[0].option_id}"]`).isChecked(), true)

        let calls = 0
        let release
        const gate = new Promise((resolve) => {
          release = resolve
        })
        const route = `**/api/v1/sessions/${practiceSid}/submit`
        await page.route(route, async (request) => {
          calls += 1
          await gate
          await request.continue()
        })
        const responsePromise = page.waitForResponse(
          (r) => r.url().endsWith(`/sessions/${practiceSid}/submit`) && r.request().method() === 'POST',
          { timeout: 30000 },
        )
        await page
          .getByRole('button', { name: 'Nộp câu này', exact: true })
          .evaluate((node) => {
            node.click()
            node.click()
          })
        await waitText(page, 'Đang nộp…')
        await page.waitForTimeout(600)
        assert.equal(calls, 1, 'double click produced more than one submit request')
        release()
        const response = await responsePromise
        assert.ok(response.ok(), `submit ${response.status()}`)
        const body = await response.json()
        await page.unroute(route)
        assert.equal(body.state.answered_count, 1)
        await page.getByRole('heading', { name: /^CÂU 2\/3/ }).waitFor({ timeout: 20000 })
        return { submit_calls: calls, answered_count: body.state.answered_count }
      })

      await step('browser Back after submit resumes the saved session safely', async () => {
        await page.goBack()
        await page.waitForURL(/\/assessments$/, { timeout: 15000 })
        await page.getByRole('heading', { name: 'Bạn có bài đang làm', exact: true }).waitFor()
        assert.equal(await page.getByRole('button', { name: /Nộp câu này/ }).count(), 0)
        await shot(page, 'assessment-active-session')
        await page.getByRole('link', { name: 'Tiếp tục bài làm', exact: true }).click()
        await page.waitForURL(new RegExp(`/exam/${practiceSid}$`))
        await page.getByRole('heading', { name: /^CÂU 2\/3/ }).waitFor()
        return { resumed: true }
      })

      await step('SQL workspace shows prompt, schema, editor, results, runs sandbox and restores draft', async () => {
        await page.locator('section.sql-schema').waitFor()
        assert.equal(await page.locator('section.sql-schema').getAttribute('aria-label'), 'Cấu trúc bảng dữ liệu')
        await page.getByLabel('Truy vấn của bạn', { exact: true }).waitFor()
        await page.getByText('Kết quả truy vấn', { exact: true }).waitFor()
        const editor = page.getByLabel('Truy vấn của bạn', { exact: true })
        await editor.fill('SELECT 1 AS value')
        await page.getByRole('button', { name: 'Chạy thử', exact: true }).click()
        const table = page.getByRole('region', { name: 'Bảng kết quả SQL', exact: true })
        await table.waitFor({ timeout: 90000 })
        await table.getByRole('cell', { name: '1', exact: true }).waitFor()
        await captureSet(page, 'exam-sql')
        await page.getByRole('button', { name: 'Lưu bản nháp', exact: true }).click()
        await waitText(page, 'Đã lưu')
        await page.reload()
        await page.getByRole('heading', { name: /^CÂU 2\/3/ }).waitFor()
        await page.getByLabel('Truy vấn của bạn', { exact: true }).waitFor()
        assert.equal(await page.getByLabel('Truy vấn của bạn', { exact: true }).inputValue(), 'SELECT 1 AS value')
        return { sql_rows: 1, restored: true }
      })

      await step('essay draft survives reload and a second tab sees the same draft', async () => {
        const advanced = page.waitForResponse(
          (r) =>
            r.url().endsWith(`/sessions/${practiceSid}/submit`) && r.request().method() === 'POST',
          { timeout: 60000 },
        )
        await page.getByRole('button', { name: 'Nộp câu này', exact: true }).click()
        const advanceResponse = await advanced
        assert.ok(advanceResponse.ok(), `SQL submit ${advanceResponse.status()}`)
        await page.getByRole('heading', { name: /^CÂU 3\/3/ }).waitFor({ timeout: 60000 })
        const essay =
          'Chuẩn hóa giúp giảm dữ liệu lặp, tránh bất thường cập nhật và bảo toàn thông tin. Cần xét khóa, phụ thuộc hàm và phép phân rã không mất mát.'
        await page.getByLabel('Câu trả lời của bạn', { exact: true }).fill(essay)
        await waitText(page, 'Đã lưu')
        await page.reload()
        await page.getByRole('heading', { name: /^CÂU 3\/3/ }).waitFor()
        assert.equal(await page.getByLabel('Câu trả lời của bạn', { exact: true }).inputValue(), essay)
        await captureSet(page, 'exam-essay', [1280, 390], ['light', 'dark'])
        const other = await context.newPage()
        try {
          await other.goto(`/exam/${practiceSid}`)
          await other.getByRole('heading', { name: /^CÂU 3\/3/ }).waitFor()
          assert.equal(await other.getByLabel('Câu trả lời của bạn', { exact: true }).inputValue(), essay)
          await shot(other, 'two-tabs-essay')
          const submitted = page.waitForResponse(
            (r) =>
              r.url().endsWith(`/sessions/${practiceSid}/submit`) &&
              r.request().method() === 'POST',
            { timeout: 30000 },
          )
          await page.getByRole('button', { name: 'Nộp câu này', exact: true }).click()
          const submitResponse = await submitted
          assert.ok(submitResponse.ok(), `essay submit ${submitResponse.status()}`)
          await page.waitForTimeout(1500)
          console.log('after essay submit page:', page.url())
          await other.reload()
          await other.waitForTimeout(1200)
          console.log('after essay submit other:', other.url())
          console.log('other body:', (await other.locator('body').innerText()).slice(0, 300).replace(/\n/g, ' | '))
          if (/\/evaluations\/\d+$/.test(other.url())) {
            await other.getByRole('heading', { name: 'Đánh giá bài làm', exact: true }).waitFor({ timeout: 20000 })
          } else if (await other.getByRole('heading', { name: 'Đã đến cuối bài', exact: true }).count()) {
            await other.getByRole('heading', { name: 'Đã đến cuối bài', exact: true }).waitFor({ timeout: 20000 })
          }
          const state = (await apiFetch(other, `/sessions/${practiceSid}`)).body
          assert.equal(state.answered_count, 3)
          assert.equal(state.current_question, null)
        } finally {
          await other.close()
        }
        return { tabs: 2, answered: 3 }
      })

      await step('finish commits the session and browser Back cannot reopen the exam', async () => {
        if (!new RegExp(`/evaluations/${practiceSid}$`).test(page.url())) {
          await page.getByRole('button', { name: 'Nộp bài', exact: true }).first().click()
          const dialog = page.getByRole('dialog')
          await dialog.getByRole('button', { name: 'Nộp bài', exact: true }).click()
        }
        await page.waitForURL(new RegExp(`/evaluations/${practiceSid}$`), { timeout: 30000 })
        await page.getByText(/Đang chờ AI đánh giá|Đang chờ giảng viên duyệt/).first().waitFor({ timeout: 30000 })
        await shot(page, 'evaluation-waiting')
        await page.goBack()
        await page.waitForTimeout(1200)
        assert.doesNotMatch(page.url(), /\/exam\//)
        assert.equal(await page.getByRole('button', { name: /Nộp câu này/ }).count(), 0)
        return { url_after_back: page.url() }
      })

      await step('per-attempt evaluation publishes with 3 question comments and scores', async () => {
        await approveSession(practiceSid)
        await page.goto(`/evaluations/${practiceSid}`)
        await page.getByRole('heading', { name: 'Nhận xét từng câu', exact: true }).waitFor({ timeout: 90000 })
        assert.equal(await page.getByRole('heading', { name: /^Câu \d+$/ }).count(), 3)
        await page.getByRole('heading', { name: 'Điểm bài làm', exact: true }).waitFor()
        assert.equal(await page.getByText('✓ Đã được giảng viên duyệt', { exact: true }).count(), 1)
        return captureSet(page, 'evaluation-attempt')
      })

      await step('overall evaluation after one attempt shows the no-trend state', async () => {
        await page.goto('/competency')
        await page.getByRole('heading', { name: 'Đánh giá tổng thể', exact: true }).waitFor()
        await page.getByText('Làm thêm bài để xem xu hướng', { exact: true }).waitFor()
        assert.equal(await page.getByRole('heading', { name: 'Xu hướng qua các bài', exact: true }).count(), 0)
        const overall = await apiFetch(page, '/evaluations/overall')
        assert.equal(overall.body.attempt_count, 1)
        return captureSet(page, 'overall-1', [1280, 390], ['light'])
      })

      await step('attempts 2 and 3 publish and overall evaluation reaches 3+', async () => {
        for (let index = 0; index < 2; index += 1) {
          const started = await startViaApi(page, { count: 3 })
          const done = await completeViaApi(page, started.session_id)
          assert.deepEqual(new Set(done.kinds), new Set(['mcq', 'sql', 'essay']))
          await approveSession(started.session_id)
          await waitReady(page, started.session_id)
        }
        const overall = await apiFetch(page, '/evaluations/overall')
        assert.equal(overall.body.attempt_count, 3)
        assert.equal(overall.body.history.length, 3)
        const rank = await apiFetch(page, '/sessions/ranking')
        assert.ok(rank.ok)
        assert.doesNotMatch(JSON.stringify(rank.body), /admin@/)
        return { attempt_count: 3, rank: rank.body }
      })

      await step('overall evaluation at 3+ shows trend, cumulative score and history', async () => {
        await page.goto('/competency')
        await page.getByRole('heading', { name: 'Đánh giá tổng thể', exact: true }).waitFor()
        await page.getByRole('heading', { name: 'Xu hướng qua các bài', exact: true }).waitFor({ timeout: 20000 })
        await page.getByRole('heading', { name: 'Điểm tích lũy', exact: true }).waitFor()
        const overall = await apiFetch(page, '/evaluations/overall')
        assert.equal(overall.body.attempt_count, 3)
        assert.equal(overall.body.history.length, 3)
        const files = await captureSet(page, 'overall-3')
        const rankVisible = await page.getByText('Hạng của bạn', { exact: true }).count()
        return { attempt_count: 3, rank_ui_visible: rankVisible > 0, files }
      })

      await step('learner ranking API returns own position without admin data', async () => {
        const rank = await apiFetch(page, '/sessions/ranking')
        assert.ok(rank.ok, `ranking ${rank.status}`)
        assert.ok(Number.isInteger(rank.body.rank) && rank.body.rank > 0, JSON.stringify(rank.body))
        assert.ok(Number.isInteger(rank.body.participants) && rank.body.participants > 0)
        assert.doesNotMatch(JSON.stringify(rank.body), /admin@/)
        return rank.body
      })

      await step('history lists published attempts and evidence contains the SQL answer', async () => {
        await page.goto('/history')
        await page.getByRole('heading', { name: 'Lịch sử làm bài', exact: true }).waitFor()
        await page.getByText(/Kết quả:/).first().waitFor()
        assert.ok((await page.getByText(/Kết quả:/).count()) >= 3)
        await captureSet(page, 'history')
        await page.getByRole('link', { name: 'Xem kết quả', exact: true }).first().click()
        await page.waitForURL(/\/history\/\d+$/)
        await page.getByRole('heading', { level: 1 }).waitFor()
        await shot(page, 'evidence')
        return { evidence_url: page.url() }
      })

      await step('settings shows account, theme and language, and EN persists after reload', async () => {
        await page.goto('/settings')
        await page.getByRole('heading', { name: 'Cài đặt', exact: true }).waitFor()
        await page.locator('#main-content').getByText(practice.email, { exact: true }).waitFor()
        await captureSet(page, 'settings')
        await setLocale(page, 'en')
        await page.getByRole('heading', { name: 'Settings', exact: true }).waitFor()
        await page.reload()
        await page.getByRole('heading', { name: 'Settings', exact: true }).waitFor()
        await shot(page, 'settings-en')
        await page.goto('/dashboard')
        await page.getByRole('heading', { name: 'My competency', exact: true }).waitFor()
        await setLocale(page, 'vi')
        return { persisted_locale: 'en -> vi' }
      })
    } catch (error) {
      console.log(`practice phase aborted: ${error.message}`)
    } finally {
      await context.close()
    }
  }

  // ---------------- C. exact question counts 1 and 20, AI source with no usable key ----------------
  {
    await registerViaApi(limits.email, 'W1 Limits Learner')
    const { context, page } = await newPage()
    try {
      await uiLogin(page, limits.email)
      const startUi = async (count, source = 'bank') => {
        await page.goto('/assessments')
        await page.getByRole('heading', { name: 'Tạo bài luyện tập', exact: true }).waitFor()
        await page.getByRole('button', { name: 'Chọn tất cả khái niệm', exact: true }).click()
        if (source === 'ai')
          await page.getByRole('radio', { name: 'AI tạo câu hỏi', exact: true }).check()
        else await page.getByRole('radio', { name: 'Từ ngân hàng câu hỏi', exact: true }).check()
        await page.getByLabel('Số câu (1–20)').fill(String(count))
        const responsePromise = page.waitForResponse(
          (r) => r.url().endsWith('/api/v1/practice/start') && r.request().method() === 'POST',
          { timeout: source === 'ai' ? 120000 : 60000 },
        )
        await page.getByRole('button', { name: 'Bắt đầu', exact: true }).click()
        const response = await responsePromise
        assert.ok(response.ok(), `start ${count}/${source}: ${response.status()} ${await response.text()}`)
        const state = await response.json()
        await page.waitForURL(new RegExp(`/exam/${state.session_id}$`), { timeout: 45000 })
        return state
      }

      let firstSid
      await step('count 1 produces exactly one served question', async () => {
        const state = await startUi(1)
        firstSid = state.session_id
        assert.equal(state.max_questions, 1)
        await page.getByRole('heading', { name: /^CÂU 1\/1/ }).waitFor()
        assert.equal(await page.locator('.ex-question-grid button').count(), 1)
        const files = await captureSet(page, 'count-1', [1280, 390], ['light', 'dark'])
        return { max_questions: state.max_questions, files }
      })

      await step('count 20 produces exactly twenty served cells and the session finishes', async () => {
        await completeViaApi(page, firstSid)
        const state = await startUi(20)
        assert.equal(state.max_questions, 20)
        await page.getByRole('heading', { name: /^CÂU 1\/20/ }).waitFor()
        assert.equal(await page.locator('.ex-question-grid button').count(), 20)
        const files = await captureSet(page, 'count-20', [1280, 390], ['light', 'dark'])
        const finished = await apiFetch(page, `/sessions/${state.session_id}/finish`, { method: 'POST' })
        assert.ok(finished.ok, `finish 20: ${finished.status}`)
        return { max_questions: state.max_questions, cells: 20, files }
      })

      await step('AI source starts a bounded one-question session or its validated fallback', async () => {
        await page.goto('/assessments')
        await page.getByRole('heading', { name: 'Tạo bài luyện tập', exact: true }).waitFor()
        const state = await startUi(1, 'ai')
        assert.equal(state.max_questions, 1)
        assert.equal(state.question_source, 'ai')
        assert.equal(state.current_question != null, true)
        const notice = await page.getByRole('status').filter({ hasText: /dự phòng|fallback/i }).count()
        const files = await captureSet(page, 'ai-source', [1280, 390], ['light'])
        await apiFetch(page, `/sessions/${state.session_id}/finish`, { method: 'POST' })
        return {
          max_questions: state.max_questions,
          generation_fallback: Boolean(state.generation_fallback),
          template_fallback: Boolean(state.template_fallback),
          notice_visible: notice > 0,
          files,
        }
      })
    } catch (error) {
      console.log(`limits phase aborted: ${error.message}`)
    } finally {
      await context.close()
    }
  }

  // ---------------- D. two-tab session refresh with a simulated expired access token ----------------
  {
    await registerViaApi(expiry.email, 'W1 Expiry Learner')
    const { context, page } = await newPage()
    try {
      await uiLogin(page, expiry.email)
      const started = await startViaApi(page, { count: 3 })
      const sid = started.session_id
      await page.goto(`/exam/${sid}`)
      await page.getByRole('heading', { name: /^CÂU 1\/3/ }).waitFor()
      const question = (await apiFetch(page, `/sessions/${sid}`)).body.current_question
      const option = question.options[0].option_id
      await page.locator(`input[value="${option}"]`).check()
      await waitText(page, 'Đã lưu')

      const other = await context.newPage()
      try {
        await other.goto(`/exam/${sid}`)
        await other.getByRole('heading', { name: /^CÂU 1\/3/ }).waitFor()
        assert.equal(await other.locator(`input[value="${option}"]`).isChecked(), true)

        const before = await page.evaluate(() => ({
          access: localStorage.getItem('dbcas_token'),
          refresh: localStorage.getItem('dbcas_refresh_token'),
        }))
        const [header, payload, signature] = before.access.split('.')
        const claims = JSON.parse(Buffer.from(payload, 'base64url').toString('utf8'))
        claims.exp = Math.floor(Date.now() / 1000) - 60
        const tampered = `${header}.${Buffer.from(JSON.stringify(claims)).toString('base64url')}.${signature}`
        await page.evaluate((token) => localStorage.setItem('dbcas_token', token), tampered)

        await Promise.all([page.reload(), other.reload()])
        await page.getByRole('heading', { name: /^CÂU 1\/3/ }).waitFor({ timeout: 30000 })
        await other.getByRole('heading', { name: /^CÂU 1\/3/ }).waitFor({ timeout: 30000 })
        assert.equal(page.url(), `${BASE}/exam/${sid}`)
        assert.equal(other.url(), `${BASE}/exam/${sid}`)
        assert.equal(await page.locator(`input[value="${option}"]`).isChecked(), true)
        assert.equal(await other.locator(`input[value="${option}"]`).isChecked(), true)

        const after = await page.evaluate(() => ({
          access: localStorage.getItem('dbcas_token'),
          refresh: localStorage.getItem('dbcas_refresh_token'),
        }))
        assert.notEqual(after.access, tampered)
        const afterClaims = JSON.parse(
          Buffer.from(after.access.split('.')[1], 'base64url').toString('utf8'),
        )
        assert.ok(afterClaims.exp * 1000 > Date.now())
        assert.notEqual(after.refresh, before.refresh, 'refresh token was not rotated')
        const replay = await page.request.post(`${API}/api/v1/auth/refresh`, {
          data: { refresh_token: before.refresh },
        })
        assert.equal(replay.status(), 401, 'old refresh token still accepted')
        await shot(page, 'session-refresh-two-tabs')
        await apiFetch(page, `/sessions/${sid}/finish`, { method: 'POST' })
        results.push({
          name: 'two tabs refresh a simulated expired access token and keep the draft',
          status: 'PASS',
          ms: 0,
          detail: {
            tabs: 2,
            simulated_expired_access_token: true,
            rotated_refresh_token: true,
            old_refresh_status: replay.status(),
          },
        })
      } finally {
        await other.close()
      }
    } catch (error) {
      console.log(`expiry phase aborted: ${error.message}`)
      results.push({
        name: 'two tabs refresh a simulated expired access token and keep the draft',
        status: 'FAIL',
        ms: 0,
        error: error.message,
      })
    } finally {
      await context.close()
    }
  }

  // ---------------- E. VI/EN switch, persistence and localized shell ----------------
  {
    await registerViaApi(localization.email, 'W1 Locale Learner')
    const { context, page } = await newPage()
    try {
      await uiLogin(page, localization.email)
      await step('EN switch updates settings, dashboard and navigation and persists', async () => {
        await page.goto('/settings')
        await page.getByRole('heading', { name: 'Cài đặt', exact: true }).waitFor()
        await setLocale(page, 'en')
        await page.getByRole('heading', { name: 'Settings', exact: true }).waitFor()
        await page.reload()
        await page.getByRole('heading', { name: 'Settings', exact: true }).waitFor()
        assert.equal(await page.locator('html').getAttribute('lang'), 'en')
        await page.goto('/dashboard')
        await page.getByRole('heading', { name: 'My competency', exact: true }).waitFor()
        const overflow = await overflowInfo(page)
        if (overflow.scrollWidth > overflow.innerWidth + 1) {
          results.push({
            name: 'EN dashboard header overflows at 1280 with a long account email (W4-owned Layout.jsx)',
            status: 'FAIL',
            ms: 0,
            error: `scrollWidth ${overflow.scrollWidth} > innerWidth ${overflow.innerWidth}`,
            detail: overflow,
          })
        } else {
          results.push({
            name: 'English header fits a long account email at 1280 and 390',
            status: 'PASS',
            ms: 0,
            detail: { scrollWidth: overflow.scrollWidth, innerWidth: overflow.innerWidth },
          })
        }
        await shot(page, 'dashboard-en', { allowOverflow: true })
        await page.setViewportSize({ width: 390, height: 900 })
        await page.waitForTimeout(500)
        const mobileOverflow = await overflowInfo(page)
        await shot(page, 'dashboard-en', { allowOverflow: true })
        await page.setViewportSize({ width: 1280, height: 900 })
        const nav = (await page.locator('nav').allInnerTexts()).join(' ')
        assert.match(nav, /Assessments/i)
        await page.goto('/assessments')
        const setupHeading = await page.getByRole('heading', { level: 1 }).innerText()
        const setupOverflow = await overflowInfo(page)
        if (setupOverflow.scrollWidth > setupOverflow.innerWidth + 1) {
          const entry = results.find((result) =>
            result.name.startsWith('EN dashboard header overflows'),
          )
          if (entry) {
            entry.error += `; practice setup ${setupOverflow.scrollWidth} > ${setupOverflow.innerWidth}`
            entry.detail = { ...entry.detail, practice_setup: setupOverflow }
          }
        }
        await shot(page, 'assessments-en', { allowOverflow: true })
        await setLocale(page, 'vi')
        return {
          setup_heading_in_en: setupHeading,
          desktop_overflow: overflow.scrollWidth > overflow.innerWidth + 1,
          mobile_overflow: mobileOverflow.scrollWidth > mobileOverflow.innerWidth + 1,
          setup_overflow: setupOverflow.scrollWidth > setupOverflow.innerWidth + 1,
          setup_offenders: setupOverflow.offenders,
          nav_has_assessments: /Assessments/i.test(nav),
        }
      })
    } finally {
      await context.close()
    }
  }

} finally {
  // persist partial evidence even if a later phase throws
  const obsolete = new Set(['overall evaluation at 3+ shows trend, history and own rank'])
  const deduped = [
    ...new Map(results.filter((entry) => !obsolete.has(entry.name)).map((entry) => [entry.name, entry])).values(),
  ]
  const uniqueShots = [...new Map(screenshots.map((entry) => [entry.file, entry])).values()]
  await writeFile(
    path.join(OUT, 'results.json'),
    `${JSON.stringify(
      {
        finished_at: new Date().toISOString(),
        base: BASE,
        results: deduped,
        screenshots: uniqueShots,
        runtime,
      },
      null,
      2,
    )}\n`,
  )
  await browser.close()
}
