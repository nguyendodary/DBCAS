import { test, expect } from './browser-fixture.js'
import { api, register, start, vi } from './practice-harness.js'

function questionHeading(number, max) {
  return vi.exam.questionOf.replace('{{number}}', String(number)).replace('{{max}}', String(max))
}

test('practice opens a planned question out of order; formal sessions stay locked', async ({
  page,
}) => {
  test.setTimeout(240_000)
  await register(page, 'feature-navigation')
  const practice = await start(page, 'bank', 3, { difficulties: ['EASY'] })
  const sid = practice.session_id
  const grid = page.locator('.ex-question-grid button')
  await expect(grid).toHaveCount(practice.max_questions)

  // Question 3 was never served, but a planned practice slot can be opened.
  const third = grid.nth(2)
  await expect(third).toBeEnabled()
  await third.click()
  await expect(
    page.getByRole('heading', { name: questionHeading(3, practice.max_questions), exact: true }),
  ).toBeVisible()

  const before = await api(page, `/sessions/${sid}/questions`)
  const thirdAttempt = before.find((item) => item.seq_no === 3)
  expect(thirdAttempt).toBeTruthy()
  if (thirdAttempt.question_type === 'mcq') await page.getByRole('radio').first().check()
  else if (thirdAttempt.question_type === 'sql')
    await page.getByRole('textbox', { name: vi.sql.query, exact: true }).fill('SELECT 1;')
  else
    await page.getByRole('textbox', { name: vi.essay.answer }).fill('Test answer for navigation.')

  const submitted = page.waitForResponse(
    (response) =>
      new URL(response.url()).pathname === `/api/v1/sessions/${sid}/submit` &&
      response.request().method() === 'POST',
  )
  await page.getByRole('button', { name: vi.exam.submit, exact: true }).click()
  expect((await submitted).ok()).toBe(true)

  // Coming back to the answered question reuses the same attempt, not a new one.
  await grid.first().click()
  await expect(
    page.getByRole('heading', { name: questionHeading(1, practice.max_questions), exact: true }),
  ).toBeVisible()
  await grid.nth(2).click()
  await expect(page.getByText(vi.exam.savedAnswerReview, { exact: true })).toBeVisible()
  const after = await api(page, `/sessions/${sid}/questions`)
  expect(after.filter((item) => item.seq_no === 3)).toHaveLength(1)
  expect(after.find((item) => item.seq_no === 3).attempt_id).toBe(thirdAttempt.attempt_id)
  expect(new Set(after.map((item) => item.seq_no)).size).toBe(after.length)
  await api(page, `/sessions/${sid}/finish`, 'POST')

  // A formal assessment keeps every not-yet-served cell disabled, and the
  // practice-only selector is rejected even if called directly.
  const formal = await api(page, '/assessments/1/sessions', 'POST')
  expect(formal.runner_mode).not.toBe('fixed')
  await page.goto(`/exam/${formal.session_id}`)
  const formalGrid = page.locator('.ex-question-grid button')
  await expect(formalGrid).toHaveCount(formal.max_questions)
  await expect(formalGrid.nth(1)).toBeDisabled()

  const token = await page.evaluate(() => localStorage.getItem('dbcas_token'))
  const rejected = await page.request.post(
    `/api/v1/sessions/${formal.session_id}/serve-next?seq_no=2`,
    { headers: { Authorization: `Bearer ${token}` } },
  )
  expect(rejected.status()).toBe(409)
  expect((await rejected.json()).error.code).toBe('question_navigation_unavailable')
  await expect(formalGrid.nth(1)).toBeDisabled()
  await api(page, `/sessions/${formal.session_id}/finish`, 'POST')
})
