import { test, expect } from '@playwright/test'
import { readFile } from 'node:fs/promises'

const vi = JSON.parse(await readFile(new URL('../src/i18n/vi.json', import.meta.url), 'utf8'))
const ai = process.env.DBCAS_QA_MODE === 'ai'
const password = 'Demo12345!'
const essay = 'Enrollment biểu diễn quan hệ nhiều-nhiều giữa Student và Course. Khóa của Enrollment là (student_id, course_id), xác định grade. 1NF yêu cầu giá trị nguyên tố. Tách Student(student_id, student_name, dept_id), Course(course_id, course_title), Enrollment(student_id, course_id, grade) để loại phụ thuộc bộ phận và đạt 2NF. Tách Department(dept_id, dept_name) để loại phụ thuộc bắc cầu và đạt 3NF. Các khóa ngoại tham chiếu khóa chính nên phép nối không mất mát. Các phụ thuộc được bảo toàn trong từng quan hệ. Cần kiểm tra khóa và các phụ thuộc hàm trước khi phân rã.'

async function shot(page, info, name) {
  await page.screenshot({ path: info.outputPath(`${name}.png`), fullPage: true })
}

async function login(page, email, admin = false) {
  await page.goto('/login')
  await page.getByLabel(vi.auth.emailLabel, { exact: true }).fill(email)
  await page.getByLabel(vi.auth.password, { exact: true }).fill(password)
  await page.getByRole('button', { name: vi.auth.signIn, exact: true }).click()
  await expect(page).toHaveURL(admin ? /\/admin$/ : /\/dashboard$/)
  await expect(page.locator('.skeleton')).toHaveCount(0)
}

async function register(page, info, suffix = '') {
  const email = `qa-${Date.now()}-${info.repeatEachIndex}${suffix}@dbcas.local`
  await page.goto('/register')
  await page.getByLabel(vi.common.fullName, { exact: true }).fill(ai ? 'Học viên QA AI' : 'Học viên QA thủ công')
  await page.getByLabel(vi.auth.emailLabel, { exact: true }).fill(email)
  await page.getByLabel(vi.auth.password, { exact: true }).fill(password)
  await page.getByLabel(vi.auth.confirmPassword, { exact: true }).fill(password)
  await page.getByRole('button', { name: vi.auth.register, exact: true }).click()
  await expect(page).toHaveURL(/\/login$/)
  await login(page, email)
  return email
}

// Answers are derived from the visible Vietnamese seed questions, not an
// administrator answer-key endpoint. Deliberate mistakes exercise partial scores.
const choices = [
  /Danh sách thuộc tính ngay sau SELECT/, /amount >= 20/, /Loại dòng không khớp/,
  /Một kết quả tổng hợp cho mỗi region_id/, /Sau khi các nhóm/, /Trả về NULL/,
  /Dùng bảng kết hợp/, /Chuyển các giá trị sang một quan hệ/, /Mỗi student_id xác định/,
  /Mỗi dòng đăng ký ứng với một sinh viên/,
]

async function start(page) {
  await page.goto('/assessments')
  await page.getByRole('button', { name: new RegExp(`^(${vi.assessment.start}|${vi.assessment.startAgain})$`) }).first().click()
  await expect(page).toHaveURL(/\/exam\/\d+$/)
  await expect(page.getByRole('main')).toHaveCount(1)
  return Number(new URL(page.url()).pathname.split('/').at(-1))
}

async function take(page, info, round, suffix = '') {
  const sessionId = await start(page)
  let mcq = 0, sql = 0, essays = 0
  for (let index = 0; index < 13; index++) {
    await expect(page.locator('#question-number')).toHaveText(vi.exam.questionOf.replace('{{number}}', String(index + 1)).replace('{{max}}', '13'))
    const body = await page.locator('.question-content').innerText()
    if (await page.getByRole('radio').count()) {
      const options = await page.locator('.answer-list').innerText()
      const correct = choices.find(pattern => pattern.test(options))
      expect(correct, `A known visible seed question: ${body}`).toBeTruthy()
      const wrong = (round === 0 && body.includes('INNER JOIN')) || (round === 1 && (body.includes('INNER JOIN') || body.includes('amount bằng NULL')))
      const radio = wrong ? page.getByRole('radio').first() : page.getByRole('radio', { name: correct })
      await radio.check()
      mcq += 1
      if (index === 0) {
        await expect(page.getByText(vi.exam.draftSaved, { exact: true })).toBeVisible()
        const timer = await page.locator('.timer-value strong').innerText()
        const selected = await radio.getAttribute('value')
        await page.reload()
        await expect(page.locator(`input[type=radio][value="${selected}"]`)).toBeChecked()
        expect((await page.locator('.timer-value strong').innerText()).localeCompare(timer)).toBeLessThanOrEqual(0)
        await shot(page, info, `attempt-${round + 1}${suffix}-restored`)
      }
    } else if (await page.locator('#essay-answer').count()) {
      await page.locator('#essay-answer').fill(`${essay} Lần làm bài ${round + 1}${suffix}.`)
      essays += 1
      await shot(page, info, `attempt-${round + 1}${suffix}-essay`)
    } else {
      const query = body.includes('JOIN') ? 'SELECT s.id, r.label FROM sales s JOIN regions r ON r.id = s.region_id' : 'SELECT id, amount FROM sales'
      await page.getByRole('textbox', { name: vi.sql.query, exact: true }).fill(query)
      await page.getByRole('button', { name: vi.sql.run, exact: true }).click()
      await expect(page.locator('.ex-results-body table tbody tr')).toHaveCount(4)
      sql += 1
      await shot(page, info, `attempt-${round + 1}${suffix}-sql-${sql}`)
    }
    const submitted = page.waitForResponse(r => new URL(r.url()).pathname === `/api/v1/sessions/${sessionId}/submit` && r.request().method() === 'POST')
    await page.getByRole('button', { name: vi.exam.submit, exact: true }).click()
    const response = await submitted
    expect(response.status()).toBe(200)
    expect((await response.json()).state.answered_count).toBe(index + 1)
  }
  expect([mcq, sql, essays]).toEqual([10, 2, 1])
  await page.getByRole('button', { name: vi.exam.finish, exact: true }).first().click()
  const finish = page.getByRole('dialog').getByRole('button', { name: vi.exam.confirmFinish, exact: true })
  // Two rapid clicks must not create a second finalization.
  await finish.dblclick()
  await expect(page).toHaveURL(new RegExp(`/history/${sessionId}$`))
  return sessionId
}

async function approve(admin, sessionId, essayScore, info, label, expectAI = ai) {
  await admin.goto(`/admin/grading/${sessionId}`)
  const reviews = admin.locator('form').filter({ has: admin.getByRole('spinbutton') })
  await expect(reviews).toHaveCount(3)
  for (let remaining = 3; remaining; remaining--) {
    const form = reviews.first()
    const card = form.locator('..')
    const isEssay = (await card.innerText()).includes('Tự luận')
    if (isEssay && expectAI) {
      await expect(card).toContainText('4,38 / 5')
      await card.getByText(vi.supervisor.automatedEvidence, { exact: true }).click()
      await expect(card.getByText('Phản hồi xác định từ provider kiểm thử local.', { exact: true })).toBeVisible()
    }
    await form.getByRole('spinbutton').fill(String(isEssay ? essayScore : 5))
    await form.getByRole('textbox').fill('Đã kiểm tra kết quả SQL, phụ thuộc hàm và rubric; xác nhận điểm chính thức.')
    await form.getByRole('button', { name: vi.supervisor.approve, exact: true }).click()
    await expect(reviews).toHaveCount(remaining - 1)
  }
  await shot(admin, info, `${label}-review`)
  await admin.getByRole('button', { name: vi.supervisor.publish, exact: true }).click()
  await expect(admin.getByRole('status')).toContainText(vi.supervisor.published)
}

function scoreCard(page, label) {
  return page.getByText(label, { exact: true }).locator('..')
}

async function provider(request, data) {
  const response = await request.post(`${process.env.DBCAS_QA_PROVIDER_URL || 'http://localhost:18099'}/control`, { data })
  expect(response.ok()).toBe(true)
}

test('Learner and Admin journey: drafts, three attempts, grading and adaptive analysis', async ({ browser }, info) => {
  const learnerContext = await browser.newContext({ baseURL: info.project.use.baseURL })
  const adminContext = await browser.newContext({ baseURL: info.project.use.baseURL })
  const learner = await learnerContext.newPage(), admin = await adminContext.newPage()
  const errors = []
  for (const page of [learner, admin]) {
    page.on('pageerror', error => errors.push(error.message))
    page.on('console', msg => { if (msg.type() === 'error' && /Content Security Policy|Refused to/.test(msg.text())) errors.push(msg.text()) })
  }
  try {
    if (ai) await provider(learner.request, { delay_seconds: 20, failure: false })
    await login(admin, 'admin@dbcas.local', true)
    const beforeCount = Number(await scoreCard(admin, vi.analytics.sessions).locator('p').last().innerText())
    await shot(admin, info, 'admin-dashboard')
    for (const [url, name] of [['/admin/curriculum', 'clo'], ['/admin/accounts', 'learners'], ['/admin/questions', 'questions'], ['/admin/assessments', 'exams']]) {
      await admin.goto(url)
      await expect(admin.locator('.skeleton')).toHaveCount(0)
      await expect(admin.getByRole('heading', { level: 1 })).toBeVisible()
      await expect(admin.getByRole('alert')).toHaveCount(0)
      await shot(admin, info, `admin-${name}`)
    }
    await register(learner, info, ai ? '-ai' : '-manual')
    await learner.getByRole('navigation', { name: vi.nav.primary }).getByRole('link', { name: vi.supervisor.cumulative, exact: true }).click()
    await expect(learner.getByText(vi.analytics.empty, { exact: true })).toBeVisible()
    await expect(learner.getByText(vi.analytics.ownRank, { exact: true })).toHaveCount(0)
    await expect(learner.getByRole('link', { name: vi.supervisor.start, exact: true })).toBeVisible()
    await shot(learner, info, 'analysis-zero')
    const totals = [93, 84, 100], essayScores = [4.25, 3, 5]
    for (let round = 0; round < 3; round++) {
      if (ai) await provider(learner.request, { delay_seconds: 20, failure: false, hold: true })
      const id = await take(learner, info, round)
      if (ai) {
        await expect(learner.getByRole('heading', { name: vi.gradingWait.gradingTitle })).toBeVisible()
        await expect(learner.getByRole('status')).toHaveAttribute('aria-busy', 'true')
        await expect(learner.getByText(vi.gradingWait.timingNote)).toBeVisible()
        await shot(learner, info, `attempt-${round + 1}-ai-waiting`)
        await learner.reload()
        await expect(learner.getByRole('heading', { name: vi.gradingWait.gradingTitle })).toBeVisible()
        await provider(learner.request, { delay_seconds: 20, failure: false, hold: false })
      }
      await expect(learner.getByRole('heading', { name: vi.gradingWait.reviewTitle })).toBeVisible({ timeout: 60000 })
      await expect(learner.locator('.animate-spin')).toHaveCount(0)
      await shot(learner, info, `attempt-${round + 1}-manual-waiting`)
      // Keep results and analysis open while an independent Admin publishes.
      const analysis = await learnerContext.newPage()
      await analysis.goto('/competency')
      await expect(analysis.getByText(/1 bài đang chờ chấm hoặc công bố/)).toBeVisible()
      if (!round) await expect(analysis.getByText(vi.analytics.empty, { exact: true })).toBeVisible()
      else await expect(scoreCard(analysis, vi.analytics.sessions)).toContainText(String(round))
      await approve(admin, id, essayScores[round], info, `attempt-${round + 1}`)
      await expect(learner.getByRole('heading', { name: vi.evidence.title, exact: true })).toBeVisible({ timeout: 40000 })
      await expect(learner.locator('.hero-band')).toContainText(`${totals[round]}%`)
      await shot(learner, info, `attempt-${round + 1}-result`)
      const cumulative = Number((totals.slice(0, round + 1).reduce((s, n) => s + n, 0) / (round + 1)).toFixed(2))
      const displayed = new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 2 }).format(cumulative) + '%'
      await expect(scoreCard(analysis, round ? vi.analytics.score : vi.analytics.singleScore)).toContainText(displayed, { timeout: 40000 })
      await expect(analysis.getByText(/bài đang chờ chấm hoặc công bố/)).toHaveCount(0)
      if (!round) {
        await expect(analysis.getByRole('heading', { name: vi.analytics.singleTitle })).toBeVisible()
        await expect(analysis.getByText(vi.analytics.singleNote)).toBeVisible()
        await expect(analysis.getByRole('heading', { name: vi.analytics.progress })).toHaveCount(0)
        await expect(analysis.getByText(vi.analytics.ownRank, { exact: true })).toHaveCount(0)
        await expect(analysis.getByText('93,75%', { exact: true })).toHaveCount(2)
      } else {
        await analysis.getByText(vi.analytics.details, { exact: true }).click()
        await expect(analysis.getByRole('heading', { name: vi.analytics.progress })).toBeVisible()
        await expect(analysis.getByText(vi.analytics.ownRank, { exact: true })).toBeVisible()
        await expect(analysis.getByRole('link', { name: /2 thg 11|thg/ })).toHaveCount(round + 1)
        if (round === 2) {
          await expect(analysis.getByText('93,75%', { exact: true })).toHaveCount(2)
          await expect(analysis.getByText('89,81%', { exact: true })).toHaveCount(2)
          await expect(scoreCard(analysis, vi.analytics.ownRank)).toContainText(`2 / ${ai ? 5 : 4}`)
        }
      }
      await expect(analysis.getByRole('main')).not.toContainText('linh@dbcas.local')
      await shot(analysis, info, `analysis-${round + 1}`)
      await analysis.setViewportSize({ width: 390, height: 844 })
      expect(await analysis.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true)
      await shot(analysis, info, `analysis-${round + 1}-mobile`)
      await analysis.close()
      await learner.goto('/history')
      await expect(learner.getByText(vi.history.result.replace('{{value}}', `${totals[round]}%`), { exact: true })).toBeVisible()
      await learner.goto('/dashboard')
      await expect(learner.locator('.hero-stat-value .cyan')).toHaveText(`${totals[round]}%`)
    }
    await learner.goto('/settings')
    await learner.setViewportSize({ width: 390, height: 844 })
    await expect(learner.getByText(vi.settings.storageNote)).toBeVisible()
    expect(await learner.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true)
    await shot(learner, info, 'settings-mobile')
    await admin.goto('/admin')
    await expect(scoreCard(admin, vi.analytics.sessions)).toContainText(String(beforeCount + 3))
    const downloaded = admin.waitForEvent('download')
    await admin.getByRole('button', { name: vi.analytics.export }).click()
    const csv = await readFile(await (await downloaded).path(), 'utf8')
    expect(csv).toContain(vi.analytics.clos)
    if (ai) {
      await admin.getByText(vi.analytics.details, { exact: true }).click()
      const ranking = admin.getByRole('heading', { name: vi.analytics.ranking, exact: true }).locator('..')
      await expect(ranking.getByRole('link', { name: /^2\./ })).toHaveCount(2)
      await expect(ranking.getByRole('link', { name: /^3\./ })).toHaveCount(0)
    }
    await shot(admin, info, 'admin-report-updated')
    expect(errors).toEqual([])
  } finally {
    await learnerContext.close()
    await adminContext.close()
  }
})

test('AI failure and bounded waiting remain recoverable after reload', async ({ page }, info) => {
  test.skip(!ai, 'Requires the explicit local QA provider override')
  await provider(page.request, { delay_seconds: 20, failure: true, hold: true })
  // Install before navigation so the page's polling deadline is controlled too.
  await page.clock.install()
  await register(page, info, '-failure')
  const id = await take(page, info, 0, '-failure')
  await expect(page.getByRole('heading', { name: vi.gradingWait.gradingTitle })).toBeVisible()
  await page.clock.fastForward(300001)
  await expect(page.getByRole('heading', { name: vi.gradingWait.takingLongerTitle })).toBeVisible()
  await expect(page.getByRole('status')).toHaveAttribute('aria-busy', 'false')
  await expect(page.locator('.animate-spin')).toHaveCount(0)
  await expect(page.getByRole('button', { name: vi.gradingWait.refresh })).toBeEnabled()
  await shot(page, info, 'ai-timeout-fallback')
  await page.clock.resume()
  await provider(page.request, { delay_seconds: 20, failure: true, hold: false })
  await page.getByRole('button', { name: vi.gradingWait.refresh }).click()
  await expect(page.getByRole('heading', { name: vi.gradingWait.reviewTitle })).toBeVisible({ timeout: 60000 })
  await page.reload()
  await expect(page.getByRole('heading', { name: vi.gradingWait.reviewTitle })).toBeVisible()
  await shot(page, info, 'ai-error-instructor-fallback')
  // Human review can take longer than the AI budget. Keep this page open and
  // verify a later publication still arrives automatically, with no refresh.
  await page.clock.fastForward(360001)
  const adminContext = await page.context().browser().newContext({ baseURL: info.project.use.baseURL })
  try {
    const admin = await adminContext.newPage()
    await login(admin, 'admin@dbcas.local', true)
    await approve(admin, id, 4.25, info, 'failed-ai-instructor', false)
    await expect(page.getByRole('heading', { name: vi.evidence.title, exact: true })).toBeVisible({ timeout: 40000 })
    await expect(page.locator('.hero-band')).toContainText('93%')
    await shot(page, info, 'long-instructor-wait-published')
  } finally { await adminContext.close() }
  await provider(page.request, { delay_seconds: 20, failure: false })
})

test('two tabs refresh expiring authentication without losing a saved draft', async ({ page, context }, info) => {
  test.skip(!ai, 'The QA override issues genuine short-lived access tokens')
  await register(page, info, '-tabs')
  const id = await start(page)
  await page.getByRole('radio').first().check()
  await expect(page.getByText(vi.exam.draftSaved, { exact: true })).toBeVisible()
  const other = await context.newPage()
  await other.goto(`/exam/${id}`)
  // Both tabs need renewal at the same time; no tokens are forged or logged.
  await Promise.all([page.reload(), other.reload()])
  for (const tab of [page, other]) {
    await expect(tab).toHaveURL(new RegExp(`/exam/${id}$`))
    await expect(tab.getByRole('radio').first()).toBeChecked()
  }
  await page.waitForTimeout(61000)
  await Promise.all([page.reload(), other.reload()])
  for (const tab of [page, other]) {
    await expect(tab).toHaveURL(new RegExp(`/exam/${id}$`))
    await expect(tab.getByRole('radio').first()).toBeChecked()
  }
  await shot(page, info, 'two-tabs-expired-session-restored')
  await other.close()
})
