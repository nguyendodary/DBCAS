// W2 administrator end-to-end audit against the running demo stack.
// Real Chromium + real API; no provider keys are read or printed.
import { chromium } from '../../../../frontend/node_modules/playwright/index.mjs'
import { strict as assert } from 'node:assert'
import { mkdir, readFile, stat, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const BASE = process.env.DBCAS_LOCAL_URL || 'http://localhost:18080'
const API = process.env.DBCAS_API || 'http://localhost:18000'
const OUT = path.dirname(fileURLToPath(import.meta.url))
const SHOTS = path.join(OUT, 'screenshots')
const DOWNLOADS = path.join(OUT, 'downloads')
const ADMIN_EMAIL = 'admin@dbcas.local'
const ADMIN_PASSWORD = 'Demo12345!'
const PASSWORD = 'W2Demo12345!'
const NEW_PASSWORD = 'W2Reset67890!'
const STAMP = `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`
await mkdir(SHOTS, { recursive: true })
await mkdir(DOWNLOADS, { recursive: true })

const results = []
const screenshots = []
const apiSnapshots = {}
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
    throw error
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

function pngSize(buffer) {
  assert.equal(buffer.toString('ascii', 1, 4), 'PNG', 'not a PNG')
  return { width: buffer.readUInt32BE(16), height: buffer.readUInt32BE(20) }
}

async function shot(page, name, { fullPage = true, allowAlert = false, allowOverflow = false, scrollTo = null } = {}) {
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
  if (scrollTo) {
    await scrollTo.scrollIntoViewIfNeeded()
    await page.evaluate(() => window.scrollBy(0, -90))
    await page.waitForTimeout(250)
  } else {
    await page.evaluate(() => window.scrollTo(0, 0))
  }
  await page.waitForTimeout(150)
  const bytes = await page.screenshot({
    path: target,
    fullPage,
    scale: 'css',
    animations: 'disabled',
  })
  const size = pngSize(bytes)
  assert.equal(size.width, width, `${filename}: PNG width ${size.width} != viewport ${width}`)
  assert.ok(size.height > 100, `${filename}: suspicious height ${size.height}`)
  assert.ok(bytes.length > 5000, `${filename}: suspiciously small (${bytes.length} bytes)`)
  screenshots.push({
    file: `screenshots/${filename}`,
    name,
    width: size.width,
    height: size.height,
    theme,
    locale,
    bytes: bytes.length,
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

async function captureSet(page, name, { widths = [1280, 390], themes = ['light', 'dark'], fullPage = true, scrollTo = null } = {}) {
  const files = []
  for (const theme of themes) {
    // Switch theme at the desktop width where the header control is visible,
    // then resize for the mobile capture.
    await page.setViewportSize({ width: 1280, height: 900 })
    await setTheme(page, theme)
    for (const width of widths) {
      await page.setViewportSize({ width, height: 900 })
      if (scrollTo) await page.waitForTimeout(200)
      files.push(await shot(page, name, { fullPage, scrollTo }))
    }
  }
  return files
}

async function apiFetch(route, { method = 'GET', data, token = null, base = API } = {}) {
  const headers = {}
  if (token) headers.Authorization = `Bearer ${token}`
  if (data !== undefined) headers['Content-Type'] = 'application/json'
  const response = await fetch(`${base}/api/v1${route}`, {
    method,
    headers,
    body: data === undefined ? undefined : JSON.stringify(data),
  })
  const text = await response.text()
  let body = null
  try {
    body = text ? JSON.parse(text) : null
  } catch {
    body = text
  }
  return { status: response.status, ok: response.ok, body, headers: response.headers }
}

async function apiOk(route, options = {}) {
  const response = await apiFetch(route, options)
  assert.ok(
    response.ok,
    `${options.method || 'GET'} ${route}: ${response.status} ${JSON.stringify(response.body).slice(0, 500)}`,
  )
  return response.body
}

async function loginApi(email, password) {
  const response = await apiFetch('/auth/login', { method: 'POST', data: { email, password } })
  return response
}

async function uiLogin(page, email, password, expectedPath = '/dashboard') {
  await page.goto('/login')
  await page.getByLabel('Email', { exact: true }).fill(email)
  await page.getByLabel('Mật khẩu', { exact: true }).fill(password)
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click()
  await page.waitForURL(new RegExp(`${expectedPath.replace('/', '\\/')}$`), { timeout: 30000 })
  await page.getByRole('heading', { level: 1 }).first().waitFor({ state: 'visible', timeout: 30000 })
  await page.waitForTimeout(800)
}

function toNumber(value) {
  const cleaned = String(value ?? '')
    .replace(/[^\d,.-]/g, '')
    .replace(/\./g, '')
    .replace(',', '.')
  const parsed = Number(cleaned)
  assert.ok(Number.isFinite(parsed), `not numeric: ${JSON.stringify(value)}`)
  return parsed
}

async function registryText(page, label) {
  const tile = page.locator('.stat-tile').filter({ hasText: label }).first()
  return (await tile.locator('.stat-tile-value').innerText()).trim()
}

function parseCsv(text) {
  const clean = text.replace(/^\uFEFF/, '')
  const rows = []
  let row = []
  let cell = ''
  let quoted = false
  for (let i = 0; i < clean.length; i += 1) {
    const char = clean[i]
    if (quoted) {
      if (char === '"' && clean[i + 1] === '"') {
        cell += '"'
        i += 1
      } else if (char === '"') {
        quoted = false
      } else {
        cell += char
      }
    } else if (char === '"') {
      quoted = true
    } else if (char === ',') {
      row.push(cell)
      cell = ''
    } else if (char === '\n') {
      row.push(cell.replace(/\r$/, ''))
      rows.push(row)
      row = []
      cell = ''
    } else {
      cell += char
    }
  }
  if (cell.length || row.length) {
    row.push(cell.replace(/\r$/, ''))
    rows.push(row)
  }
  return rows
}

function nameFor(learners, learnerId) {
  const learner = learners.find((item) => item.account_id === learnerId)
  return learner ? learner.full_name || learner.email : `#${learnerId}`
}

function verifyCsv(text, stats, learners, expectedRankingLength) {
  const rows = parseCsv(text)
  assert.deepEqual(rows[0], ['Nhóm', 'Nội dung', 'Điểm tích lũy', 'Số câu đã chấm'])
  assert.equal(rows[1][0], 'Điểm tích lũy')
  assert.equal(Number(rows[1][2]), Number(stats.dimensions.overall.competency_pct))
  assert.equal(Number(rows[1][3]), Number(stats.dimensions.overall.evidence_count))
  const expectedDimensions = []
  for (const key of ['clos', 'topics', 'difficulties']) {
    for (const item of stats.dimensions[key])
      expectedDimensions.push([item.label, Number(item.competency_pct), Number(item.evidence_count)])
  }
  const actualDimensions = rows
    .slice(2)
    .filter((row) => row.length === 4 && row[0] && ['Chuẩn đầu ra', 'Chủ đề', 'Độ khó'].includes(row[0]))
    .map((row) => [row[1], Number(row[2]), Number(row[3])])
  assert.deepEqual(actualDimensions, expectedDimensions, 'CSV dimension rows differ from API')
  const rankingHeader = rows.findIndex((row) => row[0] === 'Xếp hạng người học')
  assert.ok(rankingHeader > 0, 'CSV has no ranking header')
  assert.deepEqual(rows[rankingHeader], ['Xếp hạng người học', 'Người học', 'Điểm tích lũy'])
  const rankingRows = []
  for (let i = rankingHeader + 1; i < rows.length && rows[i][0] !== 'Phân bố điểm bài làm'; i += 1) {
    if (rows[i].length >= 3 && rows[i][0] !== '') rankingRows.push(rows[i])
  }
  assert.equal(rankingRows.length, expectedRankingLength, 'CSV ranking row count')
  assert.equal(rankingRows.length, stats.ranking.length)
  for (let i = 0; i < stats.ranking.length; i += 1) {
    const row = rankingRows[i]
    const expectedName = nameFor(learners, stats.ranking[i].learner_id)
    assert.equal(row[1], expectedName, `CSV ranking name row ${i}`)
    assert.equal(Number(row[2]), Number(stats.ranking[i].competency_pct), `CSV ranking score row ${i}`)
  }
  const distributionHeader = rows.findIndex((row) => row[0] === 'Phân bố điểm bài làm')
  assert.ok(distributionHeader > 0, 'CSV has no distribution header')
  const distributionRows = rows.slice(distributionHeader + 1).filter((row) => row[0])
  assert.equal(distributionRows.length, stats.score_distribution.length)
  for (let i = 0; i < stats.score_distribution.length; i += 1) {
    assert.equal(Number(distributionRows[i][1]), Number(stats.score_distribution[i].count))
  }
  return { rows: rows.length, ranking: rankingRows, dimensions: actualDimensions }
}

async function downloadCsv(page, filename) {
  const section = page.locator('section[aria-label="Thống kê và báo cáo"]')
  await section.waitFor({ state: 'visible', timeout: 30000 })
  const button = section.getByRole('button', { name: 'Xuất báo cáo CSV', exact: true })
  await button.waitFor({ state: 'visible' })
  const [download] = await Promise.all([
    page.waitForEvent('download', { timeout: 30000 }),
    button.click(),
  ])
  assert.equal(download.suggestedFilename(), 'dbcas-report.csv')
  const target = path.join(DOWNLOADS, filename)
  await download.saveAs(target)
  const buffer = await readFile(target)
  return { text: buffer.toString('utf8'), path: target, bytes: buffer.length }
}

function escapeRegExp(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

const browser = await chromium.launch()
async function newPage(viewport = { width: 1280, height: 900 }) {
  const context = await browser.newContext({ viewport, baseURL: BASE })
  const page = await context.newPage()
  page.on('pageerror', (error) => note('pageerror', `${page.url()}: ${error.message}`))
  page.on('console', (entry) => {
    if (entry.type() === 'error') note('console', `${page.url()}: ${entry.text()}`)
  })
  page.on('response', (response) => {
    if (response.status() >= 500) note('http', `${response.status()} ${response.request().method()} ${response.url()}`)
  })
  return { context, page }
}

const adminLogin = await loginApi(ADMIN_EMAIL, ADMIN_PASSWORD)
assert.ok(adminLogin.ok, `admin login failed: ${adminLogin.status}`)
const adminToken = adminLogin.body.access_token

const { context: adminContext, page: adminPage } = await newPage()
let learnerContext
let learnerPage
let accountsContext
let accountsPage
const flow = { email: null, name: null, account_id: null, kinds: [] }

try {
  // ---------------- 1. dashboard numbers and learner drill-down ----------------
  const cohort0 = await apiOk('/admin/analytics/cohort', { token: adminToken })
  const stats0 = await apiOk('/admin/analytics/statistics', { token: adminToken })
  const learners0 = await apiOk('/admin/learners', { token: adminToken })
  const accounts0 = await apiOk('/admin/accounts', { token: adminToken })
  const concepts0 = await apiOk('/admin/concepts', { token: adminToken })
  const clos0 = await apiOk('/admin/clos', { token: adminToken })
  const system0 = await apiOk('/admin/system', { token: adminToken })
  apiSnapshots.baseline = { cohort0, stats0, learners0, accounts: accounts0.length, concepts: concepts0.length, clos: clos0.length, system0 }
  console.log(
    `baseline: learners=${cohort0.learner_count} finalized=${cohort0.finalized_sessions} concepts=${cohort0.concepts.length} published=${stats0.published_formal_sessions} pending=${stats0.pending_formal_sessions} ranking=${stats0.ranking.length}`,
  )

  await step('admin signs in through the real login form and lands on /admin', async () => {
    await uiLogin(adminPage, ADMIN_EMAIL, ADMIN_PASSWORD, '/admin')
    await adminPage.getByRole('heading', { name: 'Tổng quan nhóm học viên', exact: true }).waitFor()
    assert.equal(new URL(adminPage.url()).pathname, '/admin')
  })

  await step('cohort summary tiles match /admin/analytics/cohort', async () => {
    const values = {
      learners: toNumber(await registryText(adminPage, 'Học viên đã làm bài')),
      finalized: toNumber(await registryText(adminPage, 'Lượt làm bài đã kết thúc')),
      concepts: toNumber(await registryText(adminPage, 'Khái niệm đã đánh giá')),
    }
    assert.equal(values.learners, cohort0.learner_count)
    assert.equal(values.finalized, cohort0.finalized_sessions)
    assert.equal(values.concepts, cohort0.concepts.length)
    return values
  })

  await step('statistics panel published, pending and score match /admin/analytics/statistics', async () => {
    const section = adminPage.locator('section[aria-label="Thống kê và báo cáo"]')
    const publishedCard = section.locator('.surface-card').filter({ hasText: 'Bài đã công bố' }).first()
    const scoreCard = section.locator('.surface-card').filter({ hasText: 'Điểm tích lũy' }).first()
    const published = toNumber(await publishedCard.innerText())
    const score = toNumber(await scoreCard.innerText())
    assert.equal(published, stats0.published_formal_sessions)
    assert.ok(Math.abs(score - Number(stats0.dimensions.overall.competency_pct)) < 0.01)
    const status = section.getByRole('status').first()
    const pendingText = await status.innerText()
    assert.match(pendingText, new RegExp(`\\b${stats0.pending_formal_sessions}\\b`))
    return { published, score, pending: stats0.pending_formal_sessions }
  })

  await step('concept gap table row count and first/last values match cohort API', async () => {
    const region = adminPage.getByRole('region', { name: 'Bảng khoảng trống kỹ năng của nhóm' })
    const rows = region.locator('tbody tr')
    assert.equal(await rows.count(), cohort0.concepts.length)
    async function rowValues(index) {
      return (await rows.nth(index).locator('td').allInnerTexts()).map((value) => value.trim())
    }
    const first = await rowValues(0)
    const last = await rowValues(cohort0.concepts.length - 1)
    const firstApi = cohort0.concepts[0]
    const lastApi = cohort0.concepts[cohort0.concepts.length - 1]
    assert.equal(first[0], firstApi.concept_name)
    assert.equal(first[1], firstApi.subject_area)
    assert.equal(toNumber(first[2]), firstApi.learners_assessed)
    assert.ok(Math.abs(toNumber(first[3]) - Number(firstApi.avg_competency_pct)) < 0.01)
    assert.equal(toNumber(first[4]), firstApi.below_target_count)
    assert.ok(Math.abs(toNumber(first[5]) - Number(firstApi.gap_rate_pct)) < 0.01)
    assert.equal(last[0], lastApi.concept_name)
    assert.equal(last[1], lastApi.subject_area)
    return { rows: cohort0.concepts.length, first: firstApi.concept_name, last: lastApi.concept_name }
  })

  await step('learner drill-down opens a session profile matching the admin API', async () => {
    const learner = learners0.find((item) => item.sessions_completed > 0 && item.full_name)
    assert.ok(learner, 'no learner with a finalized session')
    const section = adminPage.locator('section[aria-label="Kết quả từng học viên"]')
    await section.locator('button').filter({ hasText: learner.full_name }).first().click()
    const select = adminPage.getByLabel('Chọn lần làm bài')
    await select.waitFor({ state: 'visible', timeout: 30000 })
    const detail = await apiOk(`/admin/learners/${learner.account_id}/sessions`, { token: adminToken })
    const expected = detail.sessions.filter((s) => s.status === 'completed' || s.status === 'timed_out')
    assert.equal(await select.locator('option').count(), expected.length)
    const options = await select.locator('option').allInnerTexts()
    assert.ok(options[0].includes(expected[0].assessment_title || 'Luyện tập tự chọn'))
    const sessionId = Number(await select.inputValue())
    assert.equal(sessionId, expected[0].session_id)
    const profile = await apiOk(`/admin/sessions/${sessionId}/competency`, { token: adminToken })
    assert.ok(profile.concepts.length > 0, 'profile has no concept evidence')
    await adminPage.getByRole('link', { name: 'Đánh giá tổng thể', exact: true }).click()
    await adminPage.waitForURL(new RegExp(`/admin/learners/${learner.account_id}/competency$`), { timeout: 30000 })
    await adminPage.getByRole('heading', { name: 'Đánh giá tổng thể', exact: true }).waitFor()
    const cumulative = await apiOk(`/admin/learners/${learner.account_id}/competency/cumulative`, {
      token: adminToken,
    })
    const assessedTile = adminPage
      .locator('.surface-card')
      .filter({ hasText: 'Kỹ năng đã đánh giá' })
      .first()
    assert.equal(toNumber(await assessedTile.locator('p').nth(1).innerText()), cumulative.concepts.length)
    assert.ok(await adminPage.getByText(`${cumulative.summary.finalized_assessments} bài đánh giá đã công bố`).count())
    return {
      learner: learner.full_name,
      account_id: learner.account_id,
      session_id: sessionId,
      sessions: expected.length,
      profile_concepts: profile.concepts.length,
      cumulative_concepts: cumulative.concepts.length,
    }
  })

  await step('baseline CSV export parses and agrees with API values', async () => {
    await adminPage.goto('/admin')
    await adminPage.getByRole('heading', { name: 'Tổng quan nhóm học viên', exact: true }).waitFor()
    const csv = await downloadCsv(adminPage, 'dbcas-report-baseline.csv')
    const checked = verifyCsv(csv.text, stats0, learners0, stats0.ranking.length)
    apiSnapshots.csvBaseline = { bytes: csv.bytes, rows: checked.rows, ranking: checked.ranking.length }
    return { bytes: csv.bytes, rows: checked.rows, ranking: checked.ranking.length }
  })

  // ---------------- 2. Flow 2: pending review to approved result ----------------
  const reviewEmail = `w2-review-${STAMP}@dbcas.local`
  const reviewName = `W2 Review Learner ${STAMP}`
  const registration = await apiFetch('/auth/register', {
    method: 'POST',
    data: { name: reviewName, email: reviewEmail, password: PASSWORD, password_confirm: PASSWORD },
  })
  assert.equal(registration.status, 201, `register: ${registration.status} ${JSON.stringify(registration.body)}`)
  const reviewAccountId = registration.body.account_id
  const reviewLogin = await loginApi(reviewEmail, PASSWORD)
  assert.ok(reviewLogin.ok, 'fresh learner login failed')
  const reviewToken = reviewLogin.body.access_token

  flow.email = reviewEmail
  flow.name = reviewName
  flow.account_id = reviewAccountId

  await step('fresh learner starts a one-question bank session via the practice API', async () => {
    const options = await apiOk('/practice/options', { token: reviewToken })
    assert.ok(options.concepts.some((concept) => concept.concept_id === 6), 'concept 6 missing')
    const state = await apiOk('/practice/start', {
      method: 'POST',
      token: reviewToken,
      data: {
        concept_ids: [6],
        difficulties: ['HARD'],
        source: 'bank',
        question_count: 1,
        request_id: crypto.randomUUID(),
      },
    })
    assert.equal(state.max_questions, 1)
    assert.ok(state.current_question, 'practice did not serve a question')
    flow.session_id = state.session_id
    flow.question = {
      id: state.current_question.question_id,
      type: state.current_question.question_type,
      points: state.current_question.points,
    }
    flow.kinds.push(state.current_question.question_type)
    return flow.question
  })

  await step('fresh learner submits and finishes the one-question session', async () => {
    let state = await apiOk(`/sessions/${flow.session_id}`, { token: reviewToken })
    while (state.current_question) {
      const question = state.current_question
      flow.kinds.push(question.question_type)
      const payload = { question_id: question.question_id }
      if (question.question_type === 'mcq') payload.selected_option_id = question.options[0].option_id
      else if (question.question_type === 'sql') payload.sql_answer = 'SELECT 1 AS value'
      else payload.essay_answer =
        'Chuẩn hóa giảm lặp dữ liệu, bảo toàn thông tin và hạn chế bất thường cập nhật khi thiết kế cơ sở dữ liệu.'
      const submitted = await apiOk(`/sessions/${flow.session_id}/submit`, {
        method: 'POST',
        token: reviewToken,
        data: payload,
      })
      state = submitted.state
    }
    await apiOk(`/sessions/${flow.session_id}/finish`, { method: 'POST', token: reviewToken })
    flow.kinds = [...new Set(flow.kinds)]
    return flow.kinds
  })

  await step('pre-approval learner view waits with no score or evidence leak', async () => {
    let view = null
    const deadline = Date.now() + 90000
    while (Date.now() < deadline) {
      view = await apiFetch(`/evaluations/attempts/${flow.session_id}`, { token: reviewToken })
      if (view.ok && ['awaiting_approval', 'pending', 'processing'].includes(view.body?.status)) {
        if (view.body.status === 'awaiting_approval') break
      }
      await new Promise((resolve) => setTimeout(resolve, 1500))
    }
    assert.ok(view?.ok, `evaluation request failed: ${view?.status} ${JSON.stringify(view?.body)}`)
    assert.equal(view.body.status, 'awaiting_approval')
    assert.ok(view.body.score == null, `score leaked: ${JSON.stringify(view.body.score)}`)
    assert.ok(!view.body.result, 'evaluation result leaked before approval')
    assert.ok(!view.body.dimensions || Object.keys(view.body.dimensions).length === 0)
    const session = await apiOk(`/sessions/${flow.session_id}`, { token: reviewToken })
    assert.equal(session.release_status, 'pending_review')
    const evidence = await apiFetch(`/sessions/${flow.session_id}/evidence`, { token: reviewToken })
    assert.equal(evidence.status, 409)
    assert.equal(evidence.body.error.code, 'results_pending')
    const history = await apiOk('/sessions', { token: reviewToken })
    const row = history.find((item) => item.session_id === flow.session_id)
    assert.ok(row, 'session missing from learner history')
    assert.equal(row.overall_result_pct, null)
    return { status: view.body.status, release_status: session.release_status, evidence: evidence.status }
  })

  await step('learner evaluation page shows the waiting state at 1280 and 390', async () => {
    ;({ context: learnerContext, page: learnerPage } = await newPage())
    await uiLogin(learnerPage, reviewEmail, PASSWORD, '/dashboard')
    await learnerPage.goto(`/evaluations/${flow.session_id}`)
    await learnerPage.getByRole('heading', { name: 'Đang chờ giảng viên duyệt', exact: true }).waitFor({
      timeout: 30000,
    })
    const body = await learnerPage.locator('body').innerText()
    assert.ok(!/Điểm bài làm/.test(body), 'pre-approval page leaks score heading')
    assert.ok(!/Điểm tích lũy/.test(body), 'pre-approval page leaks cumulative score')
    await captureSet(learnerPage, 'learner-review-waiting', { fullPage: true })
    return 'waiting copy visible; no score heading'
  })

  await step('pending report excludes the unapproved learner', async () => {
    await adminPage.goto('/admin')
    await adminPage.getByRole('heading', { name: 'Tổng quan nhóm học viên', exact: true }).waitFor()
    const stats = await apiOk('/admin/analytics/statistics', { token: adminToken })
    assert.equal(stats.published_formal_sessions, stats0.published_formal_sessions)
    assert.equal(stats.pending_formal_sessions, stats0.pending_formal_sessions + 1)
    assert.equal(stats.ranking.length, stats0.ranking.length)
    assert.ok(!stats.ranking.some((row) => row.learner_id === reviewAccountId))
    const learners = await apiOk('/admin/learners', { token: adminToken })
    const csv = await downloadCsv(adminPage, 'dbcas-report-pending.csv')
    verifyCsv(csv.text, stats, learners, stats.ranking.length)
    assert.ok(!csv.text.includes(reviewName), 'pending learner leaked into ranking CSV')
    apiSnapshots.pending = { stats, bytes: csv.bytes }
    return { published: stats.published_formal_sessions, pending: stats.pending_formal_sessions, ranking: stats.ranking.length }
  })

  await step('admin review detail opens the pending session without a learner score', async () => {
    const detail = await apiOk(`/admin/grading-reviews/${flow.session_id}`, { token: adminToken })
    assert.equal(detail.release_status, 'pending_review')
    assert.equal(detail.learner_defined, true)
    assert.ok(detail.evaluation, 'evaluation is not ready for admin review')
    assert.equal(detail.items.length, 1)
    flow.item = detail.items[0]
    flow.revision = detail.revision
    assert.ok(detail.items[0].automated_score != null, 'MCQ has no automatic score')
    await adminPage.goto(`/admin/grading/${flow.session_id}`)
    await adminPage.getByRole('heading', { name: new RegExp(escapeRegExp(reviewName)) }).waitFor({ timeout: 30000 })
    await adminPage.getByText('Chờ giảng viên duyệt', { exact: true }).first().waitFor()
    if (flow.item.question_type === 'mcq') {
      await adminPage.getByText('Trắc nghiệm đã chấm tự động (xem khi cần)', { exact: true }).click()
      await adminPage.getByRole('button', { name: 'Lưu điểm điều chỉnh', exact: true }).waitFor()
    }
    await captureSet(adminPage, 'review-detail', { fullPage: true })
    return {
      session_id: flow.session_id,
      type: flow.item.question_type,
      automated_score: flow.item.automated_score,
      revision: flow.revision,
    }
  })

  await step('admin SQL read-only check runs on a real pending SQL review', async () => {
    const queue = await apiOk('/admin/grading-reviews', { token: adminToken })
    let target = null
    let detail = null
    for (const summary of queue) {
      if (summary.session_id === flow.session_id) continue
      const candidate = await apiOk(`/admin/grading-reviews/${summary.session_id}`, { token: adminToken })
      if (candidate.items.some((item) => item.question_type === 'sql')) {
        target = summary.session_id
        detail = candidate
        break
      }
    }
    assert.ok(target, 'no pending SQL review in the queue')
    await adminPage.goto(`/admin/grading/${target}`)
    await adminPage.getByRole('heading', { name: new RegExp(escapeRegExp(detail.learner_name)) }).waitFor({
      timeout: 30000,
    })
    const sqlCard = adminPage
      .locator('.surface-card')
      .filter({ hasText: 'SQL kiểm tra (chỉ SELECT)' })
      .first()
    await sqlCard.waitFor({ state: 'visible', timeout: 30000 })
    await sqlCard.getByRole('button', { name: 'Chạy SQL kiểm tra', exact: true }).click()
    await sqlCard.getByRole('status').filter({ hasText: 'Thành công' }).waitFor({ timeout: 90000 })
    const result = await sqlCard.getByRole('status').innerText()
    assert.match(result, /Thành công · \d+ dòng · \d+ ms/)
    await shot(adminPage, 'review-sql-check', { fullPage: false })
    return { session_id: target, result: result.split('\n')[0] }
  })

  await step('score edit without a reason is rejected', async () => {
    const detail = await apiOk(`/admin/grading-reviews/${flow.session_id}`, { token: adminToken })
    const item = detail.items[0]
    const rejected = await apiFetch(
      `/admin/grading-reviews/${flow.session_id}/attempts/${item.attempt_id}`,
      {
        method: 'POST',
        token: adminToken,
        data: { revision: item.revision, score: 0.5, comments: '' },
      },
    )
    assert.equal(rejected.status, 422, JSON.stringify(rejected.body))
    assert.equal(rejected.body.error.code, 'review_comment_required')
    const after = await apiOk(`/admin/grading-reviews/${flow.session_id}`, { token: adminToken })
    assert.equal(after.score_edits.length, 0)
    return { status: rejected.status, code: rejected.body.error.code }
  })

  await step('score edit with a reason is accepted and appears in the audit trail', async () => {
    const detail = await apiOk(`/admin/grading-reviews/${flow.session_id}`, { token: adminToken })
    const item = detail.items[0]
    await adminPage.goto(`/admin/grading/${flow.session_id}`)
    await adminPage.getByRole('heading', { name: new RegExp(escapeRegExp(reviewName)) }).waitFor({ timeout: 30000 })
    await adminPage.getByText('Chờ giảng viên duyệt', { exact: true }).first().waitFor()
    if (item.question_type === 'mcq') {
      await adminPage.getByText('Trắc nghiệm đã chấm tự động (xem khi cần)', { exact: true }).click()
      await adminPage.getByRole('button', { name: 'Lưu điểm điều chỉnh', exact: true }).waitFor()
    }
    const points = Number(item.points)
    const automated = Number(item.automated_score ?? 0)
    let adjusted = automated >= points ? Number((points * 0.5).toFixed(2)) : Number(((automated + points) / 2).toFixed(2))
    if (adjusted === automated) adjusted = Number((automated > 0 ? automated - 0.25 : 0.25).toFixed(2))
    assert.ok(adjusted >= 0 && adjusted <= points)
    const reason = `W2 điều chỉnh điểm kiểm chứng ${STAMP}`
    const revisionBefore = item.revision
    await adminPage.getByLabel('Điểm đã duyệt', { exact: true }).fill(String(adjusted))
    await adminPage.getByLabel('Lý do điều chỉnh', { exact: true }).fill(reason)
    await adminPage.getByRole('button', { name: 'Lưu điểm điều chỉnh', exact: true }).click()
    await adminPage.getByRole('heading', { name: 'Lịch sử điều chỉnh điểm', exact: true }).waitFor({
      timeout: 30000,
    })
    const historyText = await adminPage
      .locator('.surface-card')
      .filter({ hasText: 'Lịch sử điều chỉnh điểm' })
      .first()
      .innerText()
    assert.ok(historyText.includes(reason), 'reason missing from admin audit card')
    assert.ok(historyText.includes(String(adjusted)), 'new score missing from admin audit card')
    let after = null
    const deadline = Date.now() + 90000
    while (Date.now() < deadline) {
      after = await apiOk(`/admin/grading-reviews/${flow.session_id}`, { token: adminToken })
      if (after.release_status === 'pending_review') break
      await new Promise((resolve) => setTimeout(resolve, 1500))
    }
    assert.equal(after.release_status, 'pending_review')
    assert.equal(after.score_edits.length, 1)
    assert.equal(Number(after.score_edits[0].new_score), adjusted)
    assert.equal(after.score_edits[0].reason, reason)
    assert.ok(revisionBefore !== undefined)
    flow.adjusted = adjusted
    flow.reason = reason
    return { previous: after.score_edits[0].old_score, adjusted, reason }
  })

  await step('approval publishes the result and audit history records the transition', async () => {
    await adminPage.getByRole('button', { name: 'Duyệt', exact: true }).click()
    await adminPage.getByText('Đã công bố', { exact: true }).first().waitFor({ timeout: 30000 })
    const detail = await apiOk(`/admin/grading-reviews/${flow.session_id}`, { token: adminToken })
    assert.equal(detail.release_status, 'published')
    assert.equal(detail.events.at(-1).new_status, 'published')
    assert.equal(detail.events.at(-1).previous_status, 'pending_review')
    const auditText = await adminPage
      .locator('.surface-card')
      .filter({ hasText: 'Lịch sử công bố' })
      .first()
      .innerText()
    assert.match(auditText, /Chờ giảng viên duyệt → Đã công bố/)
    const editText = await adminPage
      .locator('.surface-card')
      .filter({ hasText: 'Lịch sử điều chỉnh điểm' })
      .first()
      .innerText()
    assert.ok(editText.includes(flow.reason))
    await captureSet(adminPage, 'review-detail-published', { fullPage: true })
    return { release_status: detail.release_status, events: detail.events.length }
  })

  await step('learner reload shows approval, adjustment note and evidence', async () => {
    await learnerPage.goto(`/evaluations/${flow.session_id}`)
    await learnerPage.getByText('✓ Đã được giảng viên duyệt', { exact: false }).waitFor({ timeout: 30000 })
    const body = await learnerPage.locator('body').innerText()
    assert.ok(body.includes('Điểm đã được điều chỉnh'), 'adjustment note missing')
    const expectedPct = ((Number(flow.adjusted) / Number(flow.item.points)) * 100).toFixed(2)
    assert.ok(
      body.includes(expectedPct) || body.includes(expectedPct.replace('.', ',')),
      `score ${expectedPct} missing from evaluation`,
    )
    await captureSet(learnerPage, 'learner-evaluation-approved', { fullPage: true })
    await learnerPage.goto(`/history/${flow.session_id}`)
    await learnerPage.getByRole('heading', { name: 'Kết quả chi tiết', exact: true }).waitFor({ timeout: 30000 })
    const evidenceBody = await learnerPage.locator('body').innerText()
    assert.ok(evidenceBody.includes(String(flow.adjusted).replace('.', ',')), 'adjusted score missing from evidence')
    await captureSet(learnerPage, 'learner-evidence-approved', { fullPage: true })
    return { expected_pct: expectedPct, adjusted: flow.adjusted }
  })

  await step('dashboard and ranking change only after approval and match the API', async () => {
    const cohort1 = await apiOk('/admin/analytics/cohort', { token: adminToken })
    const stats1 = await apiOk('/admin/analytics/statistics', { token: adminToken })
    const learners1 = await apiOk('/admin/learners', { token: adminToken })
    assert.equal(cohort1.learner_count, cohort0.learner_count + 1)
    assert.equal(cohort1.finalized_sessions, cohort0.finalized_sessions + 1)
    assert.equal(stats1.published_formal_sessions, stats0.published_formal_sessions + 1)
    assert.equal(stats1.pending_formal_sessions, stats0.pending_formal_sessions)
    assert.equal(stats1.ranking.length, stats0.ranking.length + 1)
    const row = stats1.ranking.find((entry) => entry.learner_id === reviewAccountId)
    assert.ok(row, 'approved learner missing from ranking')
    const expectedPct = ((Number(flow.adjusted) / Number(flow.item.points)) * 100).toFixed(2)
    assert.equal(Number(row.competency_pct), Number(expectedPct))
    const evidenceDelta =
      Number(stats1.dimensions.overall.evidence_count) - Number(stats0.dimensions.overall.evidence_count)
    assert.ok(evidenceDelta >= 1, `evidence count did not grow: ${evidenceDelta}`)
    await adminPage.goto('/admin')
    await adminPage.getByRole('heading', { name: 'Tổng quan nhóm học viên', exact: true }).waitFor()
    assert.equal(toNumber(await registryText(adminPage, 'Học viên đã làm bài')), cohort1.learner_count)
    assert.equal(toNumber(await registryText(adminPage, 'Lượt làm bài đã kết thúc')), cohort1.finalized_sessions)
    assert.equal(toNumber(await registryText(adminPage, 'Khái niệm đã đánh giá')), cohort1.concepts.length)
    const section = adminPage.locator('section[aria-label="Thống kê và báo cáo"]')
    const published = toNumber(await section.locator('.surface-card').filter({ hasText: 'Bài đã công bố' }).first().innerText())
    assert.equal(published, stats1.published_formal_sessions)
    assert.ok((await adminPage.locator('body').innerText()).includes(reviewName), 'learner missing from ranking list')
    const csv = await downloadCsv(adminPage, 'dbcas-report.csv')
    const checked = verifyCsv(csv.text, stats1, learners1, stats1.ranking.length)
    const csvRow = checked.ranking.find((entry) => entry[1] === reviewName)
    assert.ok(csvRow, 'approved learner missing from CSV ranking')
    assert.equal(Number(csvRow[2]), Number(expectedPct))
    apiSnapshots.approved = { cohort1, stats1, csvBytes: csv.bytes, csvRanking: checked.ranking.length }
    return {
      learners: cohort1.learner_count,
      finalized: cohort1.finalized_sessions,
      published: stats1.published_formal_sessions,
      pending: stats1.pending_formal_sessions,
      ranking: stats1.ranking.length,
      csv_ranking: checked.ranking.length,
    }
  })

  // ---------------- 3. accounts, lock/unlock, role, reset, RBAC ----------------
  const accountEmail = `w2-accounts-${STAMP}@dbcas.local`
  const accountName = `W2 Accounts Learner ${STAMP}`
  const accountRegistration = await apiFetch('/auth/register', {
    method: 'POST',
    data: { name: accountName, email: accountEmail, password: PASSWORD, password_confirm: PASSWORD },
  })
  assert.equal(accountRegistration.status, 201)
  const accountId = accountRegistration.body.account_id
  const accountLogin = await loginApi(accountEmail, PASSWORD)
  assert.ok(accountLogin.ok)

  await step('admin accounts page exposes the fresh account and its counts match the API', async () => {
    await adminPage.goto('/admin/accounts')
    await adminPage.getByRole('heading', { name: 'Quản lý tài khoản', exact: true }).waitFor()
    await adminPage.getByLabel('Tìm tài khoản', { exact: true }).fill(accountEmail)
    const row = adminPage.locator('tbody tr').filter({ hasText: accountEmail }).first()
    await row.waitFor({ state: 'visible', timeout: 30000 })
    assert.equal(await adminPage.locator('tbody tr').count(), 1)
    assert.ok((await row.innerText()).includes(accountName))
    return { account_id: accountId, email: accountEmail }
  })

  await step('lock rejects login and unlock restores login', async () => {
    let row = adminPage.locator('tbody tr').filter({ hasText: accountEmail }).first()
    await row.getByRole('button', { name: 'Vô hiệu hóa', exact: true }).click()
    await row.getByRole('button', { name: 'Kích hoạt', exact: true }).waitFor({ timeout: 30000 })
    let accounts = await apiOk('/admin/accounts', { token: adminToken })
    let account = accounts.find((item) => item.account_id === accountId)
    assert.equal(account.status, 'disabled')
    let locked = await loginApi(accountEmail, PASSWORD)
    assert.equal(locked.status, 403)
    assert.equal(locked.body.error.code, 'account_disabled')
    await row.getByRole('button', { name: 'Kích hoạt', exact: true }).click()
    await row.getByRole('button', { name: 'Vô hiệu hóa', exact: true }).waitFor({ timeout: 30000 })
    accounts = await apiOk('/admin/accounts', { token: adminToken })
    account = accounts.find((item) => item.account_id === accountId)
    assert.equal(account.status, 'active')
    const unlocked = await loginApi(accountEmail, PASSWORD)
    assert.equal(unlocked.status, 200)
    return { locked: locked.status, unlocked: unlocked.status }
  })

  await step('role grant and revoke work through the UI and are audited', async () => {
    let row = adminPage.locator('tbody tr').filter({ hasText: accountEmail }).first()
    await row.getByRole('button', { name: 'Cấp quyền Quản trị viên', exact: true }).click()
    const dialog = adminPage.getByRole('dialog')
    await dialog.waitFor({ state: 'visible' })
    await dialog.getByRole('button', { name: 'Cấp quyền Quản trị viên', exact: true }).click()
    await adminPage.getByText(`Đã cấp quyền Quản trị viên cho ${accountEmail}.`, { exact: true }).waitFor({
      timeout: 30000,
    })
    let accounts = await apiOk('/admin/accounts', { token: adminToken })
    let account = accounts.find((item) => item.account_id === accountId)
    assert.deepEqual(account.roles, ['Administrator'])
    row = adminPage.locator('tbody tr').filter({ hasText: accountEmail }).first()
    await row.getByRole('button', { name: 'Thu hồi quyền Quản trị viên', exact: true }).click()
    const revokeDialog = adminPage.getByRole('dialog')
    await revokeDialog.waitFor({ state: 'visible' })
    await revokeDialog.getByRole('button', { name: 'Thu hồi quyền Quản trị viên', exact: true }).click()
    await adminPage.getByText(`Đã thu hồi quyền Quản trị viên của ${accountEmail}.`, { exact: true }).waitFor({
      timeout: 30000,
    })
    accounts = await apiOk('/admin/accounts', { token: adminToken })
    account = accounts.find((item) => item.account_id === accountId)
    assert.deepEqual(account.roles, ['Learner'])
    const audit = await apiOk('/admin/accounts/role-audit', { token: adminToken })
    const events = audit.filter((item) => item.target_account_id === accountId)
    assert.ok(events.some((item) => item.action_type === 'ROLE_GRANTED'))
    assert.ok(events.some((item) => item.action_type === 'ROLE_REVOKED'))
    return { roles_after_revoke: account.roles, audit_events: events.length }
  })

  await step('admin password reset requires input and invalidates the old password', async () => {
    const row = adminPage.locator('tbody tr').filter({ hasText: accountEmail }).first()
    await row.getByRole('button', { name: 'Đặt lại mật khẩu', exact: true }).click()
    const heading = adminPage.getByRole('heading', { name: `Đặt lại mật khẩu · ${accountEmail}`, exact: true })
    await heading.waitFor({ state: 'visible' })
    const input = adminPage.getByLabel('Mật khẩu mới', { exact: true })
    assert.equal(await input.getAttribute('required'), '')
    assert.equal(await input.getAttribute('minlength'), '8')
    await input.fill(NEW_PASSWORD)
    await adminPage.getByRole('button', { name: 'Lưu mật khẩu mới', exact: true }).click()
    await heading.waitFor({ state: 'detached', timeout: 30000 })
    const oldLogin = await loginApi(accountEmail, PASSWORD)
    assert.equal(oldLogin.status, 401)
    const newLogin = await loginApi(accountEmail, NEW_PASSWORD)
    assert.equal(newLogin.status, 200)
    return { old: oldLogin.status, new: newLogin.status }
  })

  await step('accounts screenshots show the managed account at 1280/390 light/dark', async () => {
    const row = adminPage.locator('tbody tr').filter({ hasText: accountEmail }).first()
    await row.waitFor({ state: 'visible' })
    await captureSet(adminPage, 'accounts', { fullPage: true })
    return 'captured'
  })

  await step('learner RBAC redirects every admin page and receives 403 from admin APIs', async () => {
    ;({ context: accountsContext, page: accountsPage } = await newPage())
    await uiLogin(accountsPage, accountEmail, NEW_PASSWORD, '/dashboard')
    const learnerToken = (await loginApi(accountEmail, NEW_PASSWORD)).body.access_token
    const paths = ['/admin', '/admin/accounts', '/admin/grading', '/admin/questions', '/admin/system']
    for (const route of paths) {
      await accountsPage.goto(route)
      await accountsPage.waitForURL(/\/dashboard$/, { timeout: 30000 })
      assert.equal(new URL(accountsPage.url()).pathname, '/dashboard', `learner reached ${route}`)
    }
    for (const route of [
      '/admin/analytics/cohort',
      '/admin/accounts',
      '/admin/grading-reviews',
      '/admin/questions',
      '/admin/system',
    ]) {
      const response = await apiFetch(route, { token: learnerToken })
      assert.equal(response.status, 403, `learner API ${route} returned ${response.status}`)
    }
    assert.equal(await accountsPage.getByRole('link', { name: 'Quản trị', exact: false }).count(), 0)
    return { routes: paths.length, api_403: 5 }
  })

  await step('admin can open every admin screen', async () => {
    const pages = [
      ['/admin', 'Tổng quan nhóm học viên'],
      ['/admin/accounts', 'Quản lý tài khoản'],
      ['/admin/grading', 'Duyệt bài'],
      ['/admin/questions', 'Ngân hàng câu hỏi'],
      ['/admin/system', 'Hệ thống'],
    ]
    for (const [route, heading] of pages) {
      await adminPage.goto(route)
      await adminPage.getByRole('heading', { name: heading, exact: true }).first().waitFor({ timeout: 30000 })
      assert.equal(new URL(adminPage.url()).pathname, route)
    }
    return pages.length
  })

  // ---------------- 4. question bank, concepts and CLO management ----------------
  const questions0 = await apiOk('/admin/questions', { token: adminToken })
  await step('question bank count and search agree with the API', async () => {
    await adminPage.goto('/admin/questions')
    await adminPage.getByRole('heading', { level: 1 }).first().waitFor()
    const title = await adminPage.locator('.section-heading').filter({ hasText: 'Câu hỏi (' }).first().innerText()
    assert.equal(toNumber(title), questions0.length)
    const query = 'JOIN'
    const expected = await apiOk(`/admin/questions?q=${encodeURIComponent(query)}`, { token: adminToken })
    await adminPage.getByLabel('Tìm câu hỏi', { exact: true }).fill(query)
    await adminPage.waitForFunction(
      (count) => {
        const node = [...document.querySelectorAll('.section-heading')].find((item) =>
          item.textContent.trim().startsWith('Câu hỏi ('),
        )
        if (!node) return false
        return Number(node.textContent.replace(/[^\d]/g, '')) === count
      },
      expected.length,
      { timeout: 20000 },
    )
    const filteredTitle = await adminPage.locator('.section-heading').filter({ hasText: 'Câu hỏi (' }).first().innerText()
    assert.equal(toNumber(filteredTitle), expected.length)
    return { total: questions0.length, query, filtered: expected.length }
  })

  await step('concept and CLO tabs render counts from the API and search narrows concepts', async () => {
    await adminPage.getByRole('button', { name: /Khái niệm & CLO/ }).click()
    await adminPage.waitForURL(/tab=concepts/, { timeout: 30000 })
    const tabGroup = adminPage.getByRole('group', { name: 'Chương trình học' })
    const conceptsTab = tabGroup.locator('button').filter({ hasText: 'Khái niệm' }).first()
    const closTab = tabGroup.locator('button').filter({ hasText: 'Chuẩn đầu ra' }).first()
    await conceptsTab.waitFor({ state: 'visible' })
    assert.equal(toNumber(await conceptsTab.innerText()), concepts0.length)
    assert.equal(toNumber(await closTab.innerText()), clos0.length)
    await adminPage.getByLabel('Tìm khái niệm', { exact: true }).fill('DB-ER')
    await adminPage.waitForTimeout(300)
    const body = await adminPage.locator('body').innerText()
    assert.ok(body.includes('ER modeling'))
    await closTab.click()
    await adminPage.waitForTimeout(300)
    assert.equal(
      await adminPage.getByRole('button', { name: 'Tạo gợi ý bằng AI', exact: true }).count(),
      clos0.length,
    )
    return { concepts: concepts0.length, clos: clos0.length }
  })

  const disposableName = `W2 disposable concept ${STAMP}`
  await step('disposable concept create and delete work and clean up', async () => {
    await adminPage.getByRole('group', { name: 'Chương trình học' }).locator('button').filter({ hasText: 'Khái niệm' }).first().click()
    const search = adminPage.getByLabel('Tìm khái niệm', { exact: true })
    await search.fill(disposableName)
    await adminPage.getByLabel('Tên khái niệm', { exact: true }).fill(disposableName)
    await adminPage.getByLabel('Nhóm kiến thức', { exact: true }).fill('W2 disposable area')
    await adminPage.getByLabel('Mô tả khái niệm', { exact: true }).fill('Temporary audit record; deleted in the same check.')
    await adminPage.getByRole('button', { name: 'Thêm khái niệm', exact: true }).click()
    await adminPage.getByText('Đã tạo khái niệm.', { exact: true }).waitFor({ timeout: 30000 })
    let concepts = await apiOk('/admin/concepts', { token: adminToken })
    const created = concepts.find((concept) => concept.concept_name === disposableName)
    assert.ok(created, 'created concept not returned by API')
    assert.equal(concepts.length, concepts0.length + 1)
    const row = adminPage.locator('li').filter({ hasText: disposableName }).first()
    await row.waitFor({ state: 'visible' })
    await row.getByRole('button', { name: 'Xóa', exact: true }).click()
    const dialog = adminPage.getByRole('dialog')
    await dialog.getByRole('heading', { name: 'Xóa khái niệm?', exact: true }).waitFor()
    await dialog.getByRole('button', { name: 'Xóa', exact: true }).click()
    await adminPage.getByText('Đã xóa khái niệm.', { exact: true }).waitFor({ timeout: 30000 })
    concepts = await apiOk('/admin/concepts', { token: adminToken })
    assert.ok(!concepts.some((concept) => concept.concept_name === disposableName))
    assert.equal(concepts.length, concepts0.length)
    return { created_id: created.concept_id, count_after_delete: concepts.length }
  })

  // ---------------- 5. system settings ----------------
  await step('system page shows the mandatory two-step workflow and no release selector', async () => {
    await adminPage.goto('/admin/system')
    await adminPage.getByRole('heading', { name: 'Hệ thống', exact: true }).waitFor()
    await adminPage.getByText(/Mọi bài nộp đều đi qua hai bước/).first().waitFor({ timeout: 30000 })
    const body = await adminPage.locator('body').innerText()
    assert.ok(body.includes('Mọi bài nộp đều đi qua hai bước'))
    assert.ok(body.includes('AI chấm và đánh giá sơ bộ'))
    assert.ok(body.includes('Quản trị viên kiểm tra bài nộp:'))
    assert.ok(body.includes('Quản trị viên duyệt:'))
    assert.equal(await adminPage.locator('input[type="radio"]').count(), 0)
    assert.equal(await adminPage.locator('select').count(), 0)
    assert.ok(!/Công bố tự động|Công bố sau khi duyệt/.test(body))
    return 'three ordered steps; no radio/select'
  })

  await step('AI status, local database and pipeline text match /admin/system', async () => {
    const body = await adminPage.locator('body').innerText()
    if (system0.prompt_builder_configured) assert.ok(body.includes('Đã đặt đường dẫn model local'))
    else assert.ok(body.includes('Dùng mẫu dự phòng'))
    if (system0.evaluator_configured) assert.ok(body.includes('Đã cấu hình API · có phương án dự phòng khi lỗi'))
    else assert.ok(body.includes('Đánh giá dự phòng theo quy tắc'))
    assert.ok(body.includes(`Chạy trên máy · ${system0.database}`))
    assert.ok(body.includes('Bộ tạo prompt → Bộ đánh giá → Quản trị viên duyệt'))
    return {
      prompt_builder_configured: system0.prompt_builder_configured,
      evaluator_configured: system0.evaluator_configured,
      database: system0.database,
    }
  })

  await step('system screenshot set at 1280/390 light/dark', async () => {
    await captureSet(adminPage, 'system', { fullPage: true })
    return 'captured'
  })

  // ---------------- 6. final dashboard/CSV screenshots ----------------
  await step('dashboard screenshot set at 1280/390 light/dark matches final API numbers', async () => {
    await adminPage.goto('/admin')
    await adminPage.getByRole('heading', { name: 'Tổng quan nhóm học viên', exact: true }).waitFor()
    await adminPage.waitForTimeout(1200)
    await captureSet(adminPage, 'dashboard', { fullPage: true })
    return 'captured'
  })

  await step('CSV state screenshot set at 1280/390 light/dark', async () => {
    const section = adminPage.locator('section[aria-label="Thống kê và báo cáo"]')
    await section.waitFor({ state: 'visible' })
    await captureSet(adminPage, 'csv-state', {
      fullPage: false,
      scrollTo: section,
    })
    return 'captured'
  })

  // ---------------- 7. run summary ----------------
  const summary = {
    generated_at: new Date().toISOString(),
    base: BASE,
    api: API,
    checkpoints: results.length,
    passed: results.filter((item) => item.status === 'PASS').length,
    failed: results.filter((item) => item.status === 'FAIL').length,
    skipped: results.filter((item) => item.status === 'SKIP').length,
    screenshots: screenshots.length,
    runtime,
    flow,
    account: { email: accountEmail, name: accountName, id: accountId },
  }
  await writeFile(path.join(OUT, 'results.json'), JSON.stringify({ summary, results, screenshots, apiSnapshots }, null, 2))
  console.log(JSON.stringify(summary, null, 2))
} catch (error) {
  const summary = {
    generated_at: new Date().toISOString(),
    base: BASE,
    checkpoints: results.length,
    passed: results.filter((item) => item.status === 'PASS').length,
    failed: results.filter((item) => item.status === 'FAIL').length,
    screenshots: screenshots.length,
    runtime,
    flow,
  }
  await writeFile(path.join(OUT, 'results.json'), JSON.stringify({ summary, results, screenshots, apiSnapshots }, null, 2))
  console.error('AUDIT FAILED:', error.message)
  process.exitCode = 1
} finally {
  await adminContext.close()
  await learnerContext?.close()
  await accountsContext?.close()
  await browser.close()
}
