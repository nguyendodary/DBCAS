import { start as beginPractice, setFlow } from './practice-harness.js'
import { test, expect } from '@playwright/test'
import { readFile } from 'node:fs/promises'

const text = JSON.parse(await readFile(new URL('../src/i18n/vi.json', import.meta.url), 'utf8'))
const password = 'Demo12345!'

async function login(page, email, admin = false, credential = password) {
  await page.goto('/login')
  await expect(page.locator('html')).toHaveAttribute('lang', 'vi')
  await page.getByLabel(text.auth.emailLabel, { exact: true }).fill(email)
  await page.getByLabel(text.auth.password, { exact: true }).fill(credential)
  await page.getByRole('button', { name: text.auth.signIn, exact: true }).click()
  await expect(page).toHaveURL(admin ? /\/admin$/ : /\/dashboard$/)
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  await expect(page.locator('.skeleton')).toHaveCount(0)
  await expect(page.getByRole('alert')).toHaveCount(0)
}

async function api(page, route, { method = 'GET', data, token } = {}) {
  token ??= await page.evaluate(() => localStorage.getItem('dbcas_token'))
  const response = await page.request.fetch(`/api/v1${route}`, {
    method,
    data,
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  expect(response.ok(), `${method} ${route}: HTTP ${response.status()}`).toBe(true)
  return response.status() === 204 ? null : response.json()
}

async function visit(page, route, endpoint) {
  const loaded = page.waitForResponse(
    (response) => new URL(response.url()).pathname === `/api/v1${endpoint}` && response.ok(),
  )
  await page.goto(route)
  await loaded
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  await expect(page.locator('.skeleton')).toHaveCount(0)
  await expect(page.getByRole('alert')).toHaveCount(0)
}

test('local Admin and Learner complete grading, publication and competency with real APIs', async ({
  browser,
}, testInfo) => {
  const adminContext = await browser.newContext({ baseURL: testInfo.project.use.baseURL })
  const learnerContext = await browser.newContext({ baseURL: testInfo.project.use.baseURL })
  const admin = await adminContext.newPage()
  const learner = await learnerContext.newPage()
  const browserErrors = []
  for (const page of [admin, learner])
    page.on('pageerror', (error) => browserErrors.push(error.message))
  try {
    await login(admin, 'admin@dbcas.local', true)
    await setFlow(admin, 'HUMAN_VERIFIED')
    await visit(admin, '/admin', '/admin/analytics/statistics')
    const adminToken = await admin.evaluate(() => localStorage.getItem('dbcas_token'))
    const before = await api(admin, '/admin/analytics/statistics')
    expect(before.published_formal_sessions).toBeGreaterThanOrEqual(4)
    await expect(admin.getByRole('button', { name: text.analytics.export })).toBeEnabled()
    await admin.screenshot({ path: testInfo.outputPath('admin-dashboard.png'), fullPage: true })
    for (const [route, endpoint] of [
      ['/admin/curriculum', '/admin/clos'],
      ['/admin/accounts', '/admin/accounts'],
      ['/admin/questions', '/admin/questions'],
      ['/admin/grading', '/admin/grading-reviews'],
      ['/admin/system', '/admin/system'],
      ['/settings', '/auth/me'],
    ])
      await visit(admin, route, endpoint)

    await login(learner, 'learner@dbcas.local')
    const demo = await api(learner, '/sessions/statistics')
    expect(demo.published_formal_sessions).toBeGreaterThanOrEqual(2)
    const email = `smoke-${Date.now()}-${testInfo.repeatEachIndex}@dbcas.local`
    await api(learner, '/auth/register', {
      method: 'POST',
      data: {
        name: `Học viên kiểm thử ${testInfo.repeatEachIndex + 1}`,
        email,
        password,
        password_confirm: password,
      },
    })
    // Each repeat has its own real account; previous attempts cannot hide a failure.
    const demoLogout = learner.waitForResponse((response) =>
      response.url().endsWith('/auth/logout'),
    )
    await learner.getByRole('button', { name: text.nav.logout, exact: true }).click()
    expect((await demoLogout).status()).toBe(204)
    await expect(learner).toHaveURL(/\/login$/)
    await login(learner, email)
    await beginPractice(learner, 'bank', 13)
    await expect(learner).toHaveURL(/\/exam\/\d+$/)
    const sessionId = Number(new URL(learner.url()).pathname.split('/').at(-1))
    const formats = []
    for (let index = 0; index < 13; index++) {
      const state = await api(learner, `/sessions/${sessionId}`)
      const question = state.current_question
      expect(question).toBeTruthy()
      formats.push(question.question_type)
      const key = await api(admin, `/admin/questions/${question.question_id}`, {
        token: adminToken,
      })
      if (question.question_type === 'mcq') {
        const answer = key.options.find((option) => option.is_correct)
        await learner.locator(`input[type=radio][value="${answer.option_id}"]`).check()
        if (index === 0) {
          await learner.getByRole('button', { name: text.exam.saveDraft, exact: true }).click()
          await expect
            .poll(
              async () =>
                (
                  await api(
                    learner,
                    `/sessions/${sessionId}/draft?question_id=${question.question_id}`,
                  )
                ).revision,
            )
            .toBeGreaterThan(0)
          await learner.reload()
          await expect(
            learner.locator(`input[type=radio][value="${answer.option_id}"]`),
          ).toBeChecked()
        }
      } else if (question.question_type === 'sql') {
        await learner
          .getByRole('textbox', { name: text.sql.query, exact: true })
          .fill(key.reference_answer)
        const executed = learner.waitForResponse(
          (response) =>
            response.url().includes(`/sessions/${sessionId}/sql-run`) &&
            response.request().method() === 'POST',
        )
        await learner.getByRole('button', { name: text.sql.run, exact: true }).click()
        expect((await (await executed).json()).success).toBe(true)
      } else {
        await learner
          .locator('#essay-answer')
          .fill(
            'Chuẩn hóa giảm trùng lặp dữ liệu và các bất thường cập nhật. Xác định khóa và phụ thuộc hàm, tách quan hệ để nối lại không mất thông tin. Ví dụ thông tin khách hàng được tách khỏi đơn hàng để chỉ cập nhật địa chỉ ở một nơi.',
          )
      }
      const submitted = learner.waitForResponse(
        (response) =>
          new URL(response.url()).pathname === `/api/v1/sessions/${sessionId}/submit` &&
          response.request().method() === 'POST',
      )
      await learner.getByRole('button', { name: text.exam.submit, exact: true }).click()
      const response = await submitted
      expect(response.status()).toBe(200)
      expect((await response.json()).state.answered_count).toBe(index + 1)
    }
    expect(formats).toHaveLength(13)
    expect(new Set(formats)).toEqual(new Set(['mcq', 'sql', 'essay']))
    await learner.getByRole('button', { name: text.exam.finish, exact: true }).first().click()
    await learner
      .getByRole('dialog')
      .getByRole('button', { name: text.exam.confirmFinish, exact: true })
      .click()
    await expect(learner).toHaveURL(new RegExp(`/evaluations/${sessionId}$`))
    await expect(learner.getByText(/Kết quả tạm thời/)).toBeVisible()

    await visit(admin, `/admin/grading/${sessionId}`, `/admin/grading-reviews/${sessionId}`)
    await expect(admin.getByRole('button', { name: 'Duyệt', exact: true })).toBeEnabled({
      timeout: 45000,
    })
    await admin.getByText(text.local.autoMcq, { exact: true }).click()
    const reviews = admin.locator('form:visible').filter({ has: admin.getByRole('spinbutton') })
    await expect(reviews).toHaveCount(13)
    for (let index = 0; index < 3; index++) {
      const form = reviews.nth(index)
      const score = form.getByRole('spinbutton')
      await score.fill(await score.getAttribute('max'))
      await form
        .getByLabel('Lý do điều chỉnh')
        .fill('Đã kiểm tra câu trả lời và rubric; công bố điểm chính thức.')
      await form.getByRole('button', { name: 'Lưu điểm điều chỉnh', exact: true }).click()
      await expect(admin.getByRole('button', { name: 'Duyệt', exact: true })).toBeEnabled({
        timeout: 45000,
      })
    }
    await admin.getByRole('button', { name: 'Duyệt', exact: true }).click()
    await expect
      .poll(async () => (await api(admin, `/admin/grading-reviews/${sessionId}`)).release_status)
      .toBe('published')
    expect((await api(admin, `/admin/grading-reviews/${sessionId}`)).score_edits).toHaveLength(3)
    await expect(learner.getByText(/Đã được giảng viên duyệt/)).toBeVisible()
    await expect(
      learner.getByRole('heading', { name: 'Nhận xét từng câu', exact: true }),
    ).toBeVisible()
    const evidence = await api(learner, `/sessions/${sessionId}/evidence`)
    expect(evidence.items).toHaveLength(13)
    expect(evidence.items.every((item) => item.score != null)).toBe(true)
    await visit(learner, '/competency', '/evaluations/overall')
    const statistics = await api(learner, '/sessions/statistics')
    expect(statistics.published_formal_sessions).toBe(1)
    expect(statistics.dimensions.clos.length).toBeGreaterThan(0)
    await expect(learner.getByText('Làm thêm bài để xem xu hướng', { exact: true })).toBeVisible()
    await expect(learner.getByText(text.analytics.ownRank, { exact: true })).toHaveCount(0)
    await expect(learner.getByRole('heading', { name: text.analytics.progress })).toHaveCount(0)
    await learner.screenshot({
      path: testInfo.outputPath('learner-competency.png'),
      fullPage: true,
    })
    await learner.setViewportSize({ width: 390, height: 844 })
    expect(await learner.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
      391,
    )
    await visit(admin, '/admin', '/admin/analytics/statistics')
    const download = admin.waitForEvent('download')
    await admin.getByRole('button', { name: text.analytics.export }).click()
    const csv = await readFile(await (await download).path(), 'utf8')
    expect(csv).toContain(text.analytics.clos)
    expect(csv).toContain('Học viên kiểm thử')
    const access = await learner.evaluate(() => localStorage.getItem('dbcas_token'))
    const logout = learner.waitForResponse((response) => response.url().endsWith('/auth/logout'))
    await learner.getByRole('button', { name: text.nav.logout, exact: true }).click()
    expect((await logout).status()).toBe(204)
    await expect(learner).toHaveURL(/\/login$/)
    const revoked = await learner.request.get('/api/v1/auth/me', {
      headers: { Authorization: `Bearer ${access}` },
    })
    expect(revoked.status()).toBe(401)
    await learner.getByRole('link', { name: text.auth.forgotPassword, exact: true }).click()
    await expect(
      learner.getByRole('heading', { name: text.auth.forgotTitle, exact: true }),
    ).toBeVisible()
    await learner.getByLabel(text.auth.emailLabel, { exact: true }).fill(email)
    await learner.getByRole('button', { name: text.auth.sendResetLink, exact: true }).click()
    await expect(learner.getByRole('link', { name: text.local.mailbox })).toBeVisible()
    const inbox = process.env.DBCAS_MAILPIT_API || 'http://localhost:18025'
    let resetUrl
    await expect
      .poll(async () => {
        const messages = await (await learner.request.get(`${inbox}/api/v1/messages`)).json()
        const message = messages.messages.find((message) =>
          message.To.some((recipient) => recipient.Address === email),
        )
        if (!message) return false
        const detail = await (
          await learner.request.get(`${inbox}/api/v1/message/${message.ID}`)
        ).json()
        resetUrl = detail.Text.match(
          /https?:\/\/[^\s<>]+\/reset-password\?token=[A-Za-z0-9_-]+/,
        )?.[0]
        return Boolean(resetUrl)
      })
      .toBe(true)
    await learner.goto(resetUrl)
    const recoveredPassword = 'RecoveredDemo12345!'
    await learner.getByLabel(text.auth.newPassword, { exact: true }).fill(recoveredPassword)
    await learner.getByLabel(text.auth.confirmPassword, { exact: true }).fill(recoveredPassword)
    await learner.getByRole('button', { name: text.auth.resetPassword, exact: true }).click()
    await expect(learner.getByText(text.auth.resetSuccessTitle, { exact: true })).toBeVisible()
    await login(learner, email, false, recoveredPassword)
    expect(browserErrors).toEqual([])
  } finally {
    await setFlow(admin, 'IMMEDIATE')
    await learnerContext.close()
    await adminContext.close()
  }
})
