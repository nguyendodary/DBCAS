import { test, expect } from '@playwright/test'
import {
  api,
  vi,
  login,
  register,
  setFlow,
  approve,
  start,
  take,
  checkArithmetic,
  checkViewport,
} from './practice-harness.js'

test.describe.configure({ mode: 'serial' })
test('bank practice: 0/1/3 attempts, saved drafts, loading, evidence and cumulative trend', async ({
  browser,
}, info) => {
  const adminContext = await browser.newContext({ baseURL: info.project.use.baseURL })
  const learnerContext = await browser.newContext({ baseURL: info.project.use.baseURL })
  const admin = await adminContext.newPage(),
    learner = await learnerContext.newPage()
  const errors = []
  for (const page of [admin, learner]) page.on('pageerror', (error) => errors.push(error.message))
  try {
    await login(admin, 'admin@dbcas.local')
    await setFlow(admin, 'IMMEDIATE')
    await register(learner)
    await learner.goto('/competency')
    await expect(learner.getByRole('heading', { name: 'Bắt đầu hành trình của bạn' })).toBeVisible()
    await expect(
      learner.getByRole('link', { name: 'Bắt đầu luyện tập', exact: true }),
    ).toBeVisible()
    await learner.screenshot({ path: info.outputPath('overall-0.png'), fullPage: true })
    const sessions = []
    for (let i = 0; i < 3; i++) {
      const state = await start(learner)
      const { sid, kinds } = await take(learner, state, {
        refresh: i === 0,
        sandbox: i === 0,
        approveAfter: false,
      })
      expect(new Set(kinds)).toEqual(new Set(['mcq', 'sql', 'essay']))
      await expect(learner.getByText('Đang chờ giảng viên duyệt', { exact: true })).toBeVisible()
      await approve(admin, sid)
      if (i === 0) await learner.reload()
      await expect(
        learner.getByRole('heading', { name: 'Nhận xét từng câu', exact: true }),
      ).toBeVisible({ timeout: 45000 })
      sessions.push(await checkArithmetic(learner, sid))
      await checkViewport(learner)
      await learner.screenshot({ path: info.outputPath(`attempt-${i + 1}.png`), fullPage: true })
      await learner.goto('/competency')
      await expect(learner.getByRole('heading', { name: 'Nhận xét', exact: true })).toBeVisible({
        timeout: 45000,
      })
      if (!i) {
        await expect(
          learner.getByText('Làm thêm bài để xem xu hướng', { exact: true }),
        ).toBeVisible()
        await expect(learner.getByRole('heading', { name: 'Xu hướng qua các bài' })).toHaveCount(0)
      } else
        await expect(
          learner.getByRole('heading', { name: 'Xu hướng qua các bài', exact: true }),
        ).toBeVisible()
      const evaluation = await api(learner, '/evaluations/overall')
      expect(evaluation.attempt_count).toBe(i + 1)
      expect(evaluation.history).toHaveLength(i + 1)
      const cached = await api(learner, '/evaluations/overall')
      expect(cached.input_hash).toBe(evaluation.input_hash)
      await learner.screenshot({ path: info.outputPath(`overall-${i + 1}.png`), fullPage: true })
    }
    const rank = await api(learner, '/sessions/ranking')
    expect(JSON.stringify(rank)).not.toContain('admin@')
    await info.attach('arithmetic', {
      body: JSON.stringify(sessions),
      contentType: 'application/json',
    })
    expect(errors).toEqual([])
  } finally {
    await learnerContext.close()
    await adminContext.close()
  }
})

test('AI-generated source stays inside chosen concepts and hard difficulty', async ({
  page,
}, info) => {
  await register(page, 'generated')
  await page.goto('/assessments')
  const options = await api(page, '/practice/options')
  const chosen = options.concepts[0]
  await page.getByRole('button', { name: chosen.concept_name, exact: true }).click()
  await page.getByRole('button', { name: /Dễ/ }).click()
  await page.getByRole('button', { name: /Vừa/ }).click()
  await page.getByRole('radio', { name: 'AI tạo câu hỏi', exact: true }).check()
  await page.getByLabel('Số câu (1–13)').fill('3')
  const started = page.waitForResponse(
    (r) =>
      new URL(r.url()).pathname === '/api/v1/practice/start' && r.request().method() === 'POST',
  )
  await page.getByRole('button', { name: 'Bắt đầu', exact: true }).click()
  const response = await started
  expect(response.ok()).toBe(true)
  const state = await response.json()
  expect(state.selected_concept_ids).toEqual([chosen.concept_id])
  expect(state.question_source).toBe('ai')
  if (process.env.DBCAS_QA_PROVIDER_URL) {
    expect(state.generation_fallback).toBe(true)
    expect(state.bank_mixed).toBe(true)
    expect(state.template_fallback).toBe(false)
    expect(state.ai_generated_count).toBe(2)
  }
  await expect(page).toHaveURL(/\/exam\/\d+$/)
  expect(state.current_question.difficulty_level).toBeGreaterThanOrEqual(4)
  await expect(page.getByText(state.current_question.prompt, { exact: true })).toBeVisible()
  await page.screenshot({ path: info.outputPath('generated-source.png'), fullPage: true })
  const { sid } = await take(page, state)
  const adminContext = await page
    .context()
    .browser()
    .newContext({ baseURL: info.project.use.baseURL })
  try {
    const admin = await adminContext.newPage()
    await login(admin, 'admin@dbcas.local')
    await approve(admin, sid)
  } finally {
    await adminContext.close()
  }
  await expect(page.getByRole('heading', { name: 'Nhận xét từng câu' })).toBeVisible({
    timeout: 45000,
  })
  const evidence = await api(page, `/sessions/${sid}/evidence`)
  expect(evidence.items).toHaveLength(3)
  expect(new Set(evidence.items.map((item) => item.question_type))).toEqual(
    new Set(['mcq', 'sql', 'essay']),
  )
  for (const item of evidence.items) {
    expect(item.difficulty_level).toBeGreaterThanOrEqual(4)
    expect(item.concepts.map((c) => c.concept_id)).toEqual([chosen.concept_id])
    if (item.question_type === 'mcq')
      expect(item.options.filter((o) => o.is_correct)).toHaveLength(1)
    else if (item.question_type === 'essay') expect(item.rubrics).toHaveLength(4)
    else expect(item.sql_answer).toBeTruthy()
  }
})

test('Flow 2: admin verifies SQL, adjusts with a reason and approves the hidden result', async ({
  browser,
}, info) => {
  const adminContext = await browser.newContext({ baseURL: info.project.use.baseURL })
  const learnerContext = await browser.newContext({ baseURL: info.project.use.baseURL })
  const admin = await adminContext.newPage(),
    learner = await learnerContext.newPage()
  try {
    await login(admin, 'admin@dbcas.local')
    await setFlow(admin, 'HUMAN_VERIFIED')
    const cohortBefore = await api(admin, '/admin/analytics/cohort')
    await register(learner, 'review')
    const state = await start(learner)
    const { sid } = await take(learner, state, { approveAfter: false })
    await expect(
      learner.getByRole('heading', { name: 'Đang chờ giảng viên duyệt', exact: true }),
    ).toBeVisible()
    await expect(learner.getByRole('heading', { name: 'Nhận xét từng câu' })).toHaveCount(0)
    expect((await api(learner, '/sessions/statistics')).published_formal_sessions).toBe(0)
    const cohortPending = await api(admin, '/admin/analytics/cohort')
    expect(cohortPending).toEqual(cohortBefore)
    await learner.screenshot({ path: info.outputPath('waiting-approval.png'), fullPage: true })
    // Exercise manual refresh while approval is withheld, then leave the
    // original long-wait check to prove late publication arrives automatically.
    await learner.getByRole('button', { name: 'Kiểm tra cập nhật', exact: true }).click()
    await expect(
      learner.getByRole('heading', { name: 'Đang chờ giảng viên duyệt', exact: true }),
    ).toBeVisible()
    // Instructor review may outlast the AI polling budget; approval still arrives automatically.
    await learner.waitForTimeout(46000)
    await admin.goto(`/admin/grading/${sid}`)
    await expect(admin.getByRole('button', { name: 'Duyệt', exact: true })).toBeEnabled({
      timeout: 45000,
    })
    await admin.getByRole('button', { name: 'Chạy SQL kiểm tra', exact: true }).click()
    await expect(admin.getByText(/Thành công · 1 dòng/)).toBeVisible()
    const sql = admin.getByLabel('SQL kiểm tra (chỉ SELECT)')
    await sql.fill('DELETE FROM students')
    await admin.getByRole('button', { name: 'Chạy SQL kiểm tra', exact: true }).click()
    await expect(admin.getByText(/Không chạy được truy vấn/)).toBeVisible()
    const form = admin.locator('form').first()
    await form.getByRole('spinbutton').fill('0.25')
    await expect(form.getByLabel('Lý do điều chỉnh')).toHaveAttribute('required', '')
    await form.getByLabel('Lý do điều chỉnh').fill('Điều chỉnh theo rubric sau khi kiểm tra SQL.')
    await form.getByRole('button', { name: 'Lưu điểm điều chỉnh' }).click()
    await expect(admin.getByRole('heading', { name: 'Lịch sử điều chỉnh điểm' })).toBeVisible()
    await expect(admin.getByRole('button', { name: 'Duyệt', exact: true })).toBeEnabled({
      timeout: 45000,
    })
    await expect(admin.getByRole('button', { name: new RegExp(`#${sid}\\b`) })).toContainText(
      vi.supervisor.pending_review,
    )
    await expect(admin.getByText(/^Điểm hiện tại:/).first()).toContainText('0,25')
    await admin.screenshot({ path: info.outputPath('admin-review.png'), fullPage: true })
    await admin.getByRole('button', { name: 'Duyệt', exact: true }).click()
    await expect(learner.getByText(/Đã được giảng viên duyệt/)).toBeVisible({ timeout: 45000 })
    await expect(learner.getByText('Điểm đã được điều chỉnh', { exact: true })).toBeVisible()
    const review = await api(admin, `/admin/grading-reviews/${sid}`)
    expect(review.score_edits).toHaveLength(1)
    expect(review.score_edits[0].reason).toContain('rubric')
    expect(review.events.at(-1).reviewer_id).toBeTruthy()
    expect((await api(admin, '/admin/analytics/cohort')).finalized_sessions).toBe(
      cohortBefore.finalized_sessions + 1,
    )
    await checkArithmetic(learner, sid)
    await learner.screenshot({ path: info.outputPath('approved-result.png'), fullPage: true })
  } finally {
    await setFlow(admin, 'IMMEDIATE')
    await learnerContext.close()
    await adminContext.close()
  }
})

test('Admin navigation has five focused screens and no exam creation surface', async ({
  page,
}, info) => {
  await login(page, 'admin@dbcas.local')
  const menu = page.locator('.app-sidebar nav')
  expect(await menu.getByRole('link').count()).toBe(5)
  expect(
    await menu
      .getByRole('link')
      .evaluateAll((nodes) => nodes.map((node) => node.getAttribute('href'))),
  ).toEqual(['/admin', '/admin/grading', '/admin/accounts', '/admin/questions', '/admin/system'])
  for (const route of ['/admin/grading', '/admin/accounts', '/admin/questions', '/admin/system']) {
    await page.goto(route)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
    await checkViewport(page)
  }
  const token = await page.evaluate(() => localStorage.getItem('dbcas_token'))
  expect(
    (
      await page.request.post('/api/v1/admin/assessments', {
        data: {},
        headers: { Authorization: `Bearer ${token}` },
      })
    ).status(),
  ).toBe(404)
  await page.screenshot({ path: info.outputPath('admin-system.png'), fullPage: true })
})

test('390px mobile learner setup, attempt and evaluation fit the viewport', async ({
  page,
}, info) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await register(page, 'mobile')
  const state = await start(page, 'ai', 3)
  await checkViewport(page)
  await page.screenshot({ path: info.outputPath('mobile-attempt.png'), fullPage: true })
  const { sid } = await take(page, state)
  const adminContext = await page
    .context()
    .browser()
    .newContext({ baseURL: info.project.use.baseURL })
  try {
    const admin = await adminContext.newPage()
    await login(admin, 'admin@dbcas.local')
    await approve(admin, sid)
  } finally {
    await adminContext.close()
  }
  await expect(page.getByRole('heading', { name: 'Nhận xét từng câu' })).toBeVisible({
    timeout: 45000,
  })
  await checkViewport(page)
  await page.screenshot({ path: info.outputPath('mobile-evaluation.png'), fullPage: true })
  await page.goto('/assessments')
  await expect(page.getByRole('button', { name: 'Bắt đầu', exact: true })).toBeVisible()
  await checkViewport(page)
  await page.screenshot({ path: info.outputPath('mobile-setup.png'), fullPage: true })
})

test('provider outage uses a bounded fallback and caches the unchanged evaluation', async ({
  page,
}, info) => {
  const provider = process.env.DBCAS_QA_PROVIDER_URL
  if (provider)
    expect(
      (
        await page.request.post(`${provider}/control`, {
          data: { delay_seconds: 1, failure: true },
        })
      ).ok(),
    ).toBe(true)
  try {
    await register(page, 'outage')
    const state = await start(page, 'bank', 3)
    const { sid } = await take(page, state, { approveAfter: false })
    await expect(page.getByText('Đang chờ AI đánh giá...', { exact: true })).toBeVisible()
    await page.reload()
    const adminContext = await page
      .context()
      .browser()
      .newContext({ baseURL: info.project.use.baseURL })
    try {
      const admin = await adminContext.newPage()
      await login(admin, 'admin@dbcas.local')
      await approve(admin, sid)
    } finally {
      await adminContext.close()
    }
    await page.reload()
    await expect(page.getByRole('heading', { name: 'Nhận xét từng câu' })).toBeVisible({
      timeout: 45000,
    })
    await expect(page.getByText(/Đánh giá dự phòng theo quy tắc/).first()).toBeVisible()
    const first = await api(page, `/evaluations/attempts/${sid}`)
    const second = await api(page, `/evaluations/attempts/${sid}`)
    expect(first.result.evaluator_fallback).toBe(true)
    expect(second.input_hash).toBe(first.input_hash)
    await page.screenshot({ path: info.outputPath('provider-fallback.png'), fullPage: true })
  } finally {
    if (provider)
      await page.request.post(`${provider}/control`, { data: { delay_seconds: 1, failure: false } })
  }
})

test('AI provider failure fills the exact count from the validated bank', async ({
  page,
}, info) => {
  const provider = process.env.DBCAS_QA_PROVIDER_URL
  test.skip(!provider, 'Requires the deterministic local provider')
  await register(page, 'generation-fallback')
  const options = await api(page, '/practice/options')
  const concept = options.concepts.find((c) => c.concept_name === 'ER modeling')
  expect(concept).toBeTruthy()
  await page.request.post(`${provider}/control`, {
    data: { delay_seconds: 1, failure: true, hold: false },
  })
  try {
    const state = await start(page, 'ai', 5, { concept_ids: [concept.concept_id] })
    expect(state.max_questions).toBe(5)
    expect(state.generation_fallback).toBe(true)
    expect(state.bank_mixed).toBe(true)
    expect(state.template_fallback).toBe(false)
    expect(state.ai_generated_count).toBe(0)
    await expect(page.getByText(state.selection_notice, { exact: true })).toBeVisible()
    await page.screenshot({ path: info.outputPath('generation-bank-fallback.png'), fullPage: true })
    const result = await take(page, state)
    expect(result.kinds).toHaveLength(5)
  } finally {
    await page.request.post(`${provider}/control`, {
      data: { delay_seconds: 1, failure: false, hold: false },
    })
  }
})

test('AI generation timeout falls back within the request deadline at exact count', async ({
  page,
}, info) => {
  const provider = process.env.DBCAS_QA_PROVIDER_URL
  test.skip(!provider, 'Requires the deterministic local provider')
  await register(page, 'generation-timeout')
  await page.request.post(`${provider}/control`, {
    data: { delay_seconds: 60, failure: false, hold: false },
  })
  const began = Date.now()
  try {
    const state = await start(page, 'ai', 3, {}, 70_000)
    expect(Date.now() - began).toBeLessThan(70_000)
    expect(state.max_questions).toBe(3)
    expect(state.generation_fallback).toBe(true)
    expect(state.bank_mixed).toBe(true)
    expect(state.template_fallback).toBe(false)
    expect(state.ai_generated_count).toBe(0)
    await expect(page.getByText(state.selection_notice, { exact: true })).toBeVisible()
    await page.screenshot({
      path: info.outputPath('generation-timeout-fallback.png'),
      fullPage: true,
    })
  } finally {
    await page.request.post(`${provider}/control`, {
      data: { delay_seconds: 1, failure: false, hold: false },
    })
  }
})

test('transport failure offers one-click retry with unchanged setup and request id', async ({
  page,
}, info) => {
  const provider = process.env.DBCAS_QA_PROVIDER_URL
  test.skip(!provider, 'Requires the deterministic local provider')
  await register(page, 'generation-retry')
  await page.goto('/assessments')
  await page.getByRole('button', { name: 'ER modeling', exact: true }).click()
  await page.getByRole('radio', { name: 'AI tạo câu hỏi', exact: true }).check()
  await expect(page.getByRole('button', { name: 'Bắt đầu', exact: true })).toBeEnabled()
  await page.request.post(`${provider}/control`, {
    data: { delay_seconds: 1, failure: false, hold: false },
  })
  const unavailable = (route) =>
    route.fulfill({
      status: 503,
      contentType: 'application/json',
      body: JSON.stringify({
        error: { code: 'service_unavailable', message: 'Dịch vụ tạm bận. Hãy thử lại.' },
      }),
    })
  await page.route('**/api/v1/practice/start', unavailable)
  try {
    const failed = page.waitForResponse(
      (r) =>
        new URL(r.url()).pathname === '/api/v1/practice/start' && r.request().method() === 'POST',
    )
    await page.getByRole('button', { name: 'Bắt đầu', exact: true }).click()
    const failure = await failed
    expect(failure.status()).toBe(503)
    expect((await failure.json()).error.code).toBe('service_unavailable')
    await expect(page.getByRole('alert')).toHaveText(vi.errors.unknown)
    await expect(page.getByRole('button', { name: 'Thử lại', exact: true })).toBeEnabled()
    await page.screenshot({ path: info.outputPath('generation-unavailable.png'), fullPage: true })
    await page.unroute('**/api/v1/practice/start', unavailable)
    const recovered = page.waitForResponse(
      (r) =>
        new URL(r.url()).pathname === '/api/v1/practice/start' && r.request().method() === 'POST',
    )
    await page.getByRole('button', { name: 'Thử lại', exact: true }).click()
    const response = await recovered
    expect(response.ok()).toBe(true)
    expect(response.request().postDataJSON()).toEqual(failure.request().postDataJSON())
    const state = await response.json()
    expect(state.generation_fallback).toBe(true)
    expect(state.bank_mixed).toBe(true)
    expect(state.template_fallback).toBe(false)
    // Count 5 is two MCQ + two bank SQL + one essay, so the AI batch is three.
    expect(state.ai_generated_count).toBe(3)
    await expect(page).toHaveURL(/\/exam\/\d+$/, { timeout: 45000 })
    await expect(page.getByText(state.current_question.prompt, { exact: true })).toBeVisible()
    await page.screenshot({ path: info.outputPath('generation-recovered.png'), fullPage: true })
  } finally {
    await page.request.post(`${provider}/control`, {
      data: { delay_seconds: 1, failure: false, hold: false },
    })
  }
})
