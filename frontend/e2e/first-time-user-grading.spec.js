import { test, expect } from './browser-fixture.js'
import AxeBuilder from '@axe-core/playwright'
import {
  api,
  vi,
  register,
  login,
  start,
  take,
  setFlow,
  checkArithmetic,
  checkViewport,
} from './practice-harness.js'

async function accessible(page) {
  await checkViewport(page)
  expect(
    (await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze()).violations,
  ).toEqual([])
  expect(await page.getByRole('main').count()).toBe(1)
}

test('practice: learner source selection, resume, help, bilingual draft and sandbox safety', async ({
  page,
  context,
  browserDiagnostics,
}) => {
  test.setTimeout(240000)
  await register(page, 'new-practice')
  const state = await start(page, 'bank', 3)
  await page.getByRole('radio').first().check()
  const option = await page.getByRole('radio').first().inputValue()
  await page.getByRole('button', { name: vi.exam.saveDraft, exact: true }).click()
  await expect(page.getByText(vi.exam.draftSaved, { exact: true })).toBeVisible()
  await page.getByRole('button', { name: vi.help.label, exact: true }).click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await expect(page.locator('#root')).toHaveAttribute('inert', '')
  await page.keyboard.press('Escape')
  for (const language of ['English', 'Tiếng Việt']) {
    await page.getByRole('button', { name: /^(Language|Ngôn ngữ)$/ }).click()
    await page.getByRole('menuitemradio', { name: language, exact: true }).click()
    await expect(page.locator(`input[type="radio"][value="${option}"]`)).toBeChecked()
  }
  await page.reload()
  await expect(page.locator(`input[type="radio"][value="${option}"]`)).toBeChecked()
  const tab = await context.newPage()
  await tab.goto('/assessments')
  await expect(tab.getByRole('link', { name: 'Tiếp tục bài làm' })).toHaveAttribute(
    'href',
    `/exam/${state.session_id}`,
  )
  await tab.close()
  const submitted = page.waitForResponse(
    (r) =>
      r.url().endsWith(`/sessions/${state.session_id}/submit`) && r.request().method() === 'POST',
  )
  await page.getByRole('button', { name: vi.exam.submit, exact: true }).click()
  const response = await submitted
  const next = (await response.json()).state
  expect(next.current_question.question_type).toBe('sql')
  await page.getByRole('textbox', { name: vi.sql.query, exact: true }).fill('DELETE FROM students')
  await page.getByRole('button', { name: vi.sql.run, exact: true }).click()
  await expect(page.getByRole('alert')).toBeVisible()
  const sqlError = await api(page, `/sessions/${state.session_id}`)
  expect(sqlError.answered_count).toBe(1)
  const { sid, kinds } = await take(page, next, { sandbox: true, refresh: true })
  expect(kinds).toContain('sql')
  expect(kinds).toContain('essay')
  await expect(page.getByRole('heading', { name: 'Nhận xét từng câu' })).toBeVisible({
    timeout: 45000,
  })
  await checkArithmetic(page, sid)
  expect((await api(page, '/sessions/competency/cumulative')).summary.finalized_assessments).toBe(1)
  await accessible(page)
  expect(browserDiagnostics.records.pageErrors).toEqual([])
})

test('easy and hard learner practice completions become released cumulative evidence', async ({
  page,
}) => {
  test.setTimeout(180000)
  await register(page, 'difficulty')
  for (const band of ['EASY', 'HARD']) {
    const state = await start(page, 'ai', 3, { difficulties: [band] })
    expect(state.current_question.difficulty_level).toBeGreaterThanOrEqual(band === 'EASY' ? 1 : 4)
    expect(state.current_question.difficulty_level).toBeLessThanOrEqual(band === 'EASY' ? 2 : 5)
    const { sid } = await take(page, state, { refresh: true })
    await expect(page.getByRole('heading', { name: 'Nhận xét từng câu' })).toBeVisible({
      timeout: 45000,
    })
    const evidence = await api(page, `/sessions/${sid}/evidence`)
    expect(evidence.items).toHaveLength(3)
    for (const item of evidence.items) {
      expect(item.difficulty_level).toBeGreaterThanOrEqual(band === 'EASY' ? 1 : 4)
      expect(item.difficulty_level).toBeLessThanOrEqual(band === 'EASY' ? 2 : 5)
      expect(Number(item.score)).toBeGreaterThanOrEqual(0)
      expect(Number(item.score)).toBeLessThanOrEqual(Number(item.points))
    }
    await checkArithmetic(page, sid)
  }
  const cumulative = await api(page, '/sessions/competency/cumulative')
  expect(cumulative.summary.finalized_assessments).toBe(2)
  expect(cumulative.concepts.length).toBeGreaterThan(0)
  await page.goto('/competency')
  await expect(page.getByRole('heading', { name: 'Xu hướng qua các bài' })).toBeVisible({
    timeout: 45000,
  })
  await accessible(page)
})

test('automatic result: full submission, persisted answers, duplicate replay and evidence', async ({
  page,
  browserDiagnostics,
}) => {
  test.setTimeout(240000)
  await register(page, 'automatic')
  const state = await start(page, 'bank', 13)
  let firstPayload, firstAttempt
  page.on('response', async (response) => {
    if (
      !firstPayload &&
      response.url().endsWith(`/sessions/${state.session_id}/submit`) &&
      response.request().method() === 'POST' &&
      response.ok()
    ) {
      firstPayload = response.request().postDataJSON()
      firstAttempt = (await response.json()).answer.attempt_id
    }
  })
  const { sid, kinds } = await take(page, state, { refresh: true, sandbox: true })
  expect(kinds).toHaveLength(13)
  expect(new Set(kinds)).toEqual(new Set(['mcq', 'sql', 'essay']))
  await expect(page.getByRole('heading', { name: 'Nhận xét từng câu' })).toBeVisible({
    timeout: 45000,
  })
  const replay = await api(page, `/sessions/${sid}/submit`, 'POST', firstPayload)
  expect(replay.answer.attempt_id).toBe(firstAttempt)
  expect(replay.state.answered_count).toBe(13)
  const before = await api(page, `/sessions/${sid}`)
  const finished = await api(page, `/sessions/${sid}/finish`, 'POST')
  expect(finished.submitted_at).toBe(before.submitted_at)
  await checkArithmetic(page, sid)
  await page.goto('/history')
  await expect(page.getByRole('link', { name: 'Xem đánh giá', exact: true })).toHaveAttribute(
    'href',
    `/evaluations/${sid}`,
  )
  await page.getByRole('link', { name: 'Xem đánh giá', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Điểm bài làm' })).toBeVisible()
  expect(browserDiagnostics.records.pageErrors).toEqual([])
})

test('human verification: waiting, retry, unauthorized access, adjusted review and approval', async ({
  page,
  browser,
  browserDiagnostics,
}) => {
  test.setTimeout(240000)
  const adminContext = await browser.newContext({ baseURL: test.info().project.use.baseURL })
  browserDiagnostics.observe(adminContext)
  const admin = await adminContext.newPage()
  await login(admin, 'release-admin@test.dev', 'ReleaseTest123!')
  try {
    await setFlow(admin, 'HUMAN_VERIFIED')
    await register(page, 'verified')
    const state = await start(page, 'bank', 3)
    const { sid } = await take(page, state, { approveAfter: false })
    await expect(page.getByRole('heading', { name: 'Đang chờ giảng viên duyệt' })).toBeVisible()
    const token = await page.evaluate(() => localStorage.getItem('dbcas_token'))
    expect(
      (
        await page.request.get(`/api/v1/sessions/${sid}/evidence`, {
          headers: { Authorization: `Bearer ${token}` },
        })
      ).status(),
    ).toBe(409)
    expect((await api(page, `/evaluations/attempts/${sid}/retry`, 'POST')).status).toBe(
      'awaiting_approval',
    )
    expect((await api(page, '/sessions/statistics')).published_formal_sessions).toBe(0)
    await admin.goto(`/admin/grading/${sid}`)
    await expect(admin.getByRole('button', { name: 'Duyệt', exact: true })).toBeEnabled({
      timeout: 45000,
    })
    await admin.getByRole('button', { name: 'Chạy SQL kiểm tra', exact: true }).click()
    await expect(admin.getByText(/Thành công · 1 dòng/)).toBeVisible()
    const form = admin.locator('form').first()
    await form.getByRole('spinbutton').fill('0.25')
    expect(await form.evaluate((element) => element.checkValidity())).toBe(false)
    await form.getByLabel('Lý do điều chỉnh').fill('Đối chiếu theo rubric và kết quả sandbox.')
    await form.getByRole('button', { name: 'Lưu điểm điều chỉnh' }).click()
    await expect(admin.getByRole('heading', { name: 'Lịch sử điều chỉnh điểm' })).toBeVisible()
    await expect(admin.getByRole('button', { name: 'Duyệt', exact: true })).toBeEnabled({
      timeout: 45000,
    })
    await admin.getByRole('button', { name: 'Duyệt', exact: true }).click()
    await expect(page.getByText(/Đã được giảng viên duyệt/)).toBeVisible({ timeout: 45000 })
    await expect(page.getByText('Điểm đã được điều chỉnh', { exact: true })).toBeVisible()
    const result = await api(admin, `/admin/grading-reviews/${sid}`)
    expect(result.score_edits).toHaveLength(1)
    expect(result.score_edits[0].new_score).toBe(0.25)
    expect(result.events.at(-1).reviewer_id).toBeTruthy()
    await checkArithmetic(page, sid)
    await accessible(page)
    expect(browserDiagnostics.records.pageErrors).toEqual([])
  } finally {
    await setFlow(admin, 'IMMEDIATE')
    await adminContext.close()
  }
})
