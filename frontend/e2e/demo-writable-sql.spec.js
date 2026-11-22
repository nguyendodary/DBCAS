import { test, expect } from './browser-fixture.js'
import { api, register, start, vi } from './practice-harness.js'

// Runs only with the opt-in demo profile:
//   DBCAS_DEMO_WRITABLE=1 DBCAS_DEMO_PROFILE=writable npm start
test('demo writable SQL: CREATE, INSERT and SELECT in one rolled-back run', async ({ page }) => {
  test.skip(process.env.DBCAS_DEMO_WRITABLE !== '1', 'requires DBCAS_DEMO_PROFILE=writable')
  test.setTimeout(180_000)
  await register(page, 'demo-writable')
  const state = await start(page, 'bank', 3, { difficulties: ['EASY'] })
  const grid = page.locator('.ex-question-grid button')

  let sqlSeq = null
  for (let seq = 1; seq <= state.max_questions && sqlSeq === null; seq += 1) {
    if (seq > 1) await grid.nth(seq - 1).click()
    const served = await api(page, `/sessions/${state.session_id}/questions`)
    if (served.find((item) => item.seq_no === seq)?.question_type === 'sql') sqlSeq = seq
  }
  expect(sqlSeq, 'practice plan must contain one SQL question').not.toBeNull()

  await page
    .getByRole('textbox', { name: vi.sql.query, exact: true })
    .fill(
      'CREATE TABLE demo_item(id INT PRIMARY KEY, name TEXT); ' +
        "INSERT INTO demo_item VALUES (1, 'alpha'), (2, 'beta'); " +
        'SELECT id, name FROM demo_item ORDER BY id;',
    )
  await page.getByRole('button', { name: vi.sql.run, exact: true }).click()
  const result = page.getByRole('region', { name: vi.sql.resultTable })
  await expect(result).toBeVisible()
  await expect(result).toContainText('alpha')
  await expect(result).toContainText('beta')
})
