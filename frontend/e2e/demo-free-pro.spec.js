import { test, expect } from './browser-fixture.js'
import { login, register } from './practice-harness.js'

// Runs only when the frontend is built with VITE_DEMO_FREE_PRO=true.
test('demo Free/Pro badge, fake upgrade and admin-only static costs', async ({ page, browser }) => {
  test.skip(process.env.DBCAS_DEMO_FREE_PRO !== '1', 'requires DBCAS_DEMO_PROFILE=free-pro')
  test.setTimeout(120_000)
  await register(page, 'demo-free-pro')
  await expect(page.getByTestId('demo-plan-panel')).toBeVisible()
  await expect(page.getByText(/Free · 3 sessions per month/)).toBeVisible()
  await expect(page.getByText('DEMO')).toBeVisible()
  await page.getByRole('button', { name: 'Upgrade to Pro (Demo)' }).click()
  await expect(page.getByText(/Pro \(Demo\) · 99,000 VND \/ 30 days/)).toBeVisible()

  const adminContext = await browser.newContext({ baseURL: test.info().project.use.baseURL })
  const admin = await adminContext.newPage()
  try {
    await login(admin, 'admin@dbcas.local')
    await expect(admin.getByTestId('demo-costs-panel')).toBeVisible()
    await expect(admin.getByText(/Sample data only/)).toBeVisible()
  } finally {
    await adminContext.close()
  }
})
