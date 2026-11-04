import { test, expect } from '@playwright/test'
import {
  register,
  start,
  take,
  api,
  vi,
  demoPassword,
  checkArithmetic,
} from './practice-harness.js'

const provider = process.env.DBCAS_QA_PROVIDER_URL
if (!provider)
  throw new Error('Run browser-qa.spec.js with npm run test:qa and its local fake provider')
async function control(page, data) {
  expect((await page.request.post(`${provider}/control`, { data })).ok()).toBe(true)
}

test('a stalled workspace module offers Retry and recovers when the download completes', async ({
  page,
}, info) => {
  await page.addInitScript(() => {
    if (window.top === window && /^https?:$/.test(location.protocol))
      localStorage.setItem('dbcas_locale', 'vi')
  })
  let release
  const gate = new Promise((resolve) => {
    release = resolve
  })
  await page.route('**/assets/AdminPage-*.js', async (route) => {
    await gate
    await route.continue()
  })
  try {
    await page.goto('/login')
    await page.getByLabel(vi.auth.emailLabel, { exact: true }).fill('admin@dbcas.local')
    await page.getByLabel(vi.auth.password, { exact: true }).fill(demoPassword)
    const signedIn = page.waitForResponse(
      (r) => r.url().endsWith('/api/v1/auth/login') && r.request().method() === 'POST',
    )
    await page.getByRole('button', { name: vi.auth.signIn, exact: true }).click()
    expect(
      (await signedIn).status(),
      'Sign-in must succeed before the workspace module is opened',
    ).toBe(200)
    await expect(page).toHaveURL(/\/admin$/)
    await expect(page.getByRole('status')).toBeVisible()
    await expect(
      page.getByRole('heading', { name: vi.common.workspaceTimeoutTitle, exact: true }),
    ).toBeVisible()
    await expect(page.getByRole('alert')).toContainText(vi.errors.workspace_timeout)
    await expect(page.getByRole('button', { name: vi.common.retry, exact: true })).toBeEnabled()
    await expect(page.getByRole('status')).toHaveCount(0)
    await page.screenshot({
      path: info.outputPath('bounded-workspace-loading.png'),
      fullPage: true,
    })
    release()
    await expect(
      page.getByRole('heading', { name: vi.admin.analytics.title, exact: true }),
    ).toBeVisible()
    await expect(page.getByRole('alert')).toHaveCount(0)
  } finally {
    release()
    await page.unrouteAll({ behavior: 'wait' })
  }
})

test('two tabs and a double click commit one answer and restore the next question', async ({
  page,
  context,
}, info) => {
  await control(page, { delay_seconds: 1, failure: false })
  await register(page, 'double-submit')
  const state = await start(page, 'bank', 3)
  await page.getByRole('radio').first().check()
  await page.getByRole('button', { name: vi.exam.saveDraft, exact: true }).click()
  await expect(page.getByText(vi.exam.draftSaved, { exact: true })).toBeVisible()
  const other = await context.newPage()
  await other.goto(`/exam/${state.session_id}`)
  await expect(other.getByRole('radio').first()).toBeChecked()
  let release,
    calls = 0
  const gate = new Promise((resolve) => {
    release = resolve
  })
  const path = `**/api/v1/sessions/${state.session_id}/submit`
  await page.route(path, async (route) => {
    calls++
    await gate
    await route.continue()
  })
  try {
    const submitting = page.waitForRequest(
      (r) => r.url().endsWith(`/sessions/${state.session_id}/submit`) && r.method() === 'POST',
    )
    const button = page.getByRole('button', { name: vi.exam.submit, exact: true })
    await button.evaluate((node) => {
      node.click()
      node.click()
    })
    await submitting
    await expect.poll(() => calls).toBe(1)
    release()
    await expect
      .poll(async () => (await api(page, `/sessions/${state.session_id}`)).answered_count)
      .toBe(1)
    await other.reload()
    const resumed = await api(other, `/sessions/${state.session_id}`)
    expect(resumed.answered_count).toBe(1)
    expect(calls).toBe(1)
    expect(resumed.current_question.question_id).not.toBe(state.current_question.question_id)
    await other.close()
    await take(page, resumed)
    await expect(page.getByRole('heading', { name: 'Nhận xét từng câu' })).toBeVisible({
      timeout: 45000,
    })
    await checkArithmetic(page, state.session_id)
    await page.screenshot({ path: info.outputPath('double-submit-restored.png'), fullPage: true })
  } finally {
    release()
    await page.unrouteAll({ behavior: 'wait' })
  }
})

test('paused provider is bounded after reload and Retry keeps a cached result', async ({
  page,
}, info) => {
  await control(page, { delay_seconds: 1, failure: false, hold: true })
  try {
    await register(page, 'held-provider')
    const state = await start(page, 'bank', 3)
    const initialCalls = (await (await page.request.get(`${provider}/health`)).json()).calls
    await take(page, state)
    await expect(page.getByText('Đang chờ AI đánh giá...', { exact: true })).toBeVisible()
    await page.reload()
    await expect(page.getByText('Đang chờ AI đánh giá...', { exact: true })).toBeVisible()
    await expect
      .poll(async () => (await (await page.request.get(`${provider}/health`)).json()).calls)
      .toBeGreaterThan(initialCalls)
    await page.getByRole('button', { name: 'Thử lại', exact: true }).click()
    await expect(page.getByRole('heading', { name: 'Nhận xét từng câu' })).toBeVisible({
      timeout: 55000,
    })
    await expect(page.getByText(/Đánh giá dự phòng theo quy tắc/).first()).toBeVisible()
    const fallback = await api(page, `/evaluations/attempts/${state.session_id}`)
    expect(fallback.result.evaluator_fallback).toBe(true)
    await control(page, { delay_seconds: 0, failure: false, hold: false })
    const cached = await api(page, `/evaluations/attempts/${state.session_id}`)
    expect(cached.input_hash).toBe(fallback.input_hash)
    expect(cached.result).toEqual(fallback.result)
    await page.screenshot({
      path: info.outputPath('bounded-provider-fallback.png'),
      fullPage: true,
    })
  } finally {
    await control(page, { delay_seconds: 1, failure: false, hold: false })
  }
})

test('two tabs renew genuinely expired authentication and retain the saved draft', async ({
  page,
  context,
}, info) => {
  await register(page, 'expired-tabs')
  const state = await start(page, 'ai', 3)
  await page.getByRole('radio').first().check()
  await page.getByRole('button', { name: vi.exam.saveDraft, exact: true }).click()
  await expect(page.getByText(vi.exam.draftSaved, { exact: true })).toBeVisible()
  const other = await context.newPage()
  await other.goto(`/exam/${state.session_id}`)
  await expect(other.getByRole('radio').first()).toBeChecked()
  const original = await page.evaluate(() => localStorage.getItem('dbcas_token'))
  const expires = JSON.parse(Buffer.from(original.split('.')[1], 'base64url').toString()).exp * 1000
  await page.waitForTimeout(Math.max(0, expires - Date.now()) + 1500)
  expect(
    (
      await page.request.get('/api/v1/auth/me', {
        headers: { Authorization: `Bearer ${original}` },
      })
    ).status(),
  ).toBe(401)
  await Promise.all([page.reload(), other.reload()])
  for (const tab of [page, other]) {
    await expect(tab).toHaveURL(new RegExp(`/exam/${state.session_id}$`))
    await expect(tab.getByRole('radio').first()).toBeChecked()
  }
  expect(
    await page.evaluate(
      () => JSON.parse(atob(localStorage.getItem('dbcas_token').split('.')[1])).exp * 1000,
    ),
  ).toBeGreaterThan(expires)
  await page.screenshot({ path: info.outputPath('expired-two-tabs-restored.png'), fullPage: true })
  await other.close()
})
