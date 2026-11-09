import { expect } from '@playwright/test'
import { readFile } from 'node:fs/promises'
export const vi = JSON.parse(
  await readFile(new URL('../src/i18n/vi.json', import.meta.url), 'utf8'),
)
export const demoPassword = 'Demo12345!'

export async function api(page, path, method = 'GET', data) {
  const token = await page.evaluate(() => localStorage.getItem('dbcas_token'))
  const r = await page.request.fetch(`/api/v1${path}`, {
    method,
    data,
    headers: { Authorization: `Bearer ${token}` },
  })
  expect(r.ok(), `${method} ${path}: ${r.status()} ${await r.text()}`).toBe(true)
  return r.status() === 204 ? null : r.json()
}
export async function login(page, email, password = demoPassword) {
  await page.addInitScript(() => {
    if (window.top === window && /^https?:$/.test(location.protocol))
      localStorage.setItem('dbcas_locale', 'vi')
  })
  await page.goto('/login')
  await page.getByLabel(vi.auth.emailLabel, { exact: true }).fill(email)
  await page.getByLabel(vi.auth.password, { exact: true }).fill(password)
  await page.getByRole('button', { name: vi.auth.signIn, exact: true }).click()
  await expect(page).toHaveURL(email.includes('admin') ? /\/admin$/ : /\/dashboard$/)
  if (email.includes('admin'))
    await expect(
      page.getByRole('heading', { name: vi.admin.analytics.title, exact: true }),
    ).toBeVisible()
  else
    await expect(page.getByRole('heading', { level: 1 })).toHaveText(
      new RegExp(`^(?:${vi.dashboard.title}|${vi.dashboard.greeting.split('{{')[0]})`),
    )
}
export async function register(page, label = 'practice') {
  const email = `${label}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@dbcas.local`
  await page.addInitScript(() => {
    if (window.top === window && /^https?:$/.test(location.protocol))
      localStorage.setItem('dbcas_locale', 'vi')
  })
  await page.goto('/register')
  await page.getByLabel(vi.common.fullName, { exact: true }).fill('Học viên kiểm thử')
  await page.getByLabel(vi.auth.emailLabel, { exact: true }).fill(email)
  await page.getByLabel(vi.auth.password, { exact: true }).fill(demoPassword)
  await page.getByLabel(vi.auth.confirmPassword, { exact: true }).fill(demoPassword)
  await page.getByRole('button', { name: vi.auth.register, exact: true }).click()
  await expect(page).toHaveURL(/\/login$/)
  await login(page, email)
  return email
}
export async function setFlow(page) {
  await page.goto('/admin/system')
  await expect(page.getByText(/Mọi bài nộp đều đi qua hai bước/)).toBeVisible()
  await expect(page.getByRole('radio')).toHaveCount(0)
}
export async function approve(page, sid) {
  for (let attempt = 0; attempt < 120; attempt++) {
    const review = await api(page, `/admin/grading-reviews/${sid}`)
    if (review.release_status === 'pending_review') {
      await api(page, `/admin/grading-reviews/${sid}/publish`, 'POST', {
        revision: review.revision,
      })
      return
    }
    if (['published', 'reviewed'].includes(review.release_status)) return
    await page.waitForTimeout(1000)
  }
  throw new Error(`Session ${sid} did not reach admin review within 120s`)
}
export async function start(page, source = 'bank', count = 3, selection = {}) {
  await page.goto('/assessments')
  if (selection.concept_ids) {
    const options = await api(page, '/practice/options')
    for (const c of options.concepts)
      if (selection.concept_ids.includes(c.concept_id))
        await page.getByRole('button', { name: c.concept_name, exact: true }).click()
  } else await page.getByRole('button', { name: 'Chọn tất cả khái niệm' }).click()
  if (selection.difficulties) {
    for (const [key, label] of [
      ['EASY', 'Dễ'],
      ['MEDIUM', 'Vừa'],
      ['HARD', 'Khó'],
    ])
      if (!selection.difficulties.includes(key))
        await page.getByRole('button', { name: new RegExp(label) }).click()
  }
  await page
    .getByRole('radio', {
      name: source === 'bank' ? 'Từ ngân hàng câu hỏi' : 'AI tạo câu hỏi',
      exact: true,
    })
    .check()
  await page.getByLabel('Số câu (1–20)').fill(String(count))
  // Two bounded 10-second provider attempts plus validation/cleanup can exceed
  // the ordinary 20-second action deadline; the API client allows 60 seconds.
  const response = page.waitForResponse(
    (r) =>
      new URL(r.url()).pathname === '/api/v1/practice/start' && r.request().method() === 'POST',
    { timeout: 45_000 },
  )
  await page.getByRole('button', { name: 'Bắt đầu', exact: true }).click()
  const r = await response
  expect(r.ok(), await r.text()).toBe(true)
  await expect(page).toHaveURL(/\/exam\/\d+$/)
  const state = await r.json()
  if (state.current_question)
    await expect(page.getByText(state.current_question.prompt, { exact: true })).toBeVisible()
  return { ...state, _startRequest: r.request().postDataJSON() }
}
export async function take(page, state, { refresh = false, sandbox = false, answerFor } = {}) {
  const sid = state.session_id
  const kinds = []
  const seen = new Set()
  while (state.current_question) {
    const q = state.current_question
    expect(seen.has(q.question_id)).toBe(false)
    seen.add(q.question_id)
    kinds.push(q.question_type)
    const answer = answerFor ? await answerFor(q) : null
    const text =
      q.question_type === 'sql'
        ? answer?.reference_answer || 'SELECT 1'
        : answer?.reference_answer ||
          'Chuẩn hóa giúp giảm lặp dữ liệu và tránh bất thường cập nhật. Cần xét khóa, phụ thuộc hàm và phép phân rã không mất mát.'
    await expect(
      page.getByRole('heading', { name: new RegExp(`^${vi.exam.questionOf.split('{{')[0]}`) }),
    ).toBeVisible()
    if (refresh && q.question_type !== 'mcq')
      await page
        .getByRole('textbox', {
          name: q.question_type === 'sql' ? vi.sql.query : vi.essay.answer,
        })
        .fill('Initial editable draft')
    if (q.question_type === 'mcq') {
      const option = answer?.options.find((o) => o.is_correct)
      if (option) await page.locator(`input[value="${option.option_id}"]`).check()
      else await page.getByRole('radio').first().check()
    } else if (q.question_type === 'sql') {
      await page.getByRole('textbox', { name: vi.sql.query, exact: true }).fill(text)
      if (sandbox) {
        await page.getByRole('button', { name: vi.sql.run, exact: true }).click()
        await expect(page.getByRole('region', { name: vi.sql.resultTable })).toBeVisible()
      }
    } else await page.getByRole('textbox', { name: vi.essay.answer }).fill(text)
    if (refresh) {
      await page.getByRole('button', { name: vi.exam.saveDraft, exact: true }).click()
      await expect(page.getByText(vi.exam.draftSaved, { exact: true })).toBeVisible()
      await page.reload()
      if (q.question_type === 'mcq') await expect(page.getByRole('radio').first()).toBeChecked()
      else
        await expect(
          page.getByRole('textbox', {
            name: q.question_type === 'sql' ? vi.sql.query : vi.essay.answer,
          }),
        ).toHaveValue(text)
      const restored = await api(page, `/sessions/${sid}`)
      expect(restored.expires_at).toBe(state.expires_at)
      expect(restored.current_question.question_id).toBe(q.question_id)
    }
    const submitted = page.waitForResponse(
      (r) =>
        new URL(r.url()).pathname === `/api/v1/sessions/${sid}/submit` &&
        r.request().method() === 'POST',
    )
    await page.getByRole('button', { name: vi.exam.submit, exact: true }).click()
    const response = await submitted
    expect(response.ok(), await response.text()).toBe(true)
    const body = await response.json()
    expect(body.answer.score).toBeNull()
    expect(body.answer.is_correct).toBeNull()
    state = body.state
  }
  await page.getByRole('button', { name: vi.exam.finish, exact: true }).last().click()
  const dialog = page.getByRole('dialog')
  await dialog.getByRole('button', { name: vi.exam.confirmFinish, exact: true }).click()
  await expect(page).toHaveURL(new RegExp(`/evaluations/${sid}$`))
  return { sid, kinds }
}
export async function checkArithmetic(page, sid) {
  const evidence = await api(page, `/sessions/${sid}/evidence`)
  const possible = evidence.items.reduce((sum, item) => sum + Number(item.points), 0)
  const earned = evidence.items.reduce((sum, item) => sum + Number(item.score), 0)
  const history = await api(page, '/sessions')
  const row = history.find((item) => item.session_id === sid)
  expect(Number(row.overall_result_pct)).toBeCloseTo((earned / possible) * 100, 2)
  const stats = await api(page, '/sessions/statistics')
  expect(stats.published_formal_sessions).toBeGreaterThan(0)
  return { earned, possible, percentage: Number(row.overall_result_pct) }
}
export async function checkViewport(page) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(
    true,
  )
  await expect(page.getByRole('alert')).toHaveCount(0)
}
