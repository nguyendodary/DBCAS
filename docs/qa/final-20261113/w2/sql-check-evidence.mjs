// Focused evidence capture for the read-only admin SQL check (W2).
// Read-only: runs the submitted SELECT in the existing pending review.
import { chromium } from '../../../../frontend/node_modules/playwright/index.mjs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const BASE = 'http://localhost:18080'
const API = 'http://localhost:18000'
const OUT = path.dirname(fileURLToPath(import.meta.url))
const SHOTS = path.join(OUT, 'screenshots')
const login = await fetch(`${API}/api/v1/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'admin@dbcas.local', password: 'Demo12345!' }),
})
if (!login.ok) throw new Error(`admin login ${login.status}`)
const token = (await login.json()).access_token
const sessionId = 28
const detail = await (
  await fetch(`${API}/api/v1/admin/grading-reviews/${sessionId}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
).json()

const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1280, height: 900 }, baseURL: BASE })
try {
  await page.goto('/login')
  await page.getByLabel('Email', { exact: true }).fill('admin@dbcas.local')
  await page.getByLabel('Mật khẩu', { exact: true }).fill('Demo12345!')
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click()
  await page.waitForURL(/\/admin$/)
  await page.goto(`/admin/grading/${sessionId}`)
  await page.getByRole('heading', { name: new RegExp(detail.learner_name) }).waitFor({ timeout: 30000 })
  if ((await page.locator('html').getAttribute('data-theme')) === 'dark')
    await page.locator('.theme-selector').first().click()
  const card = page.locator('.surface-card').filter({ hasText: 'SQL kiểm tra (chỉ SELECT)' }).first()
  await card.waitFor({ state: 'visible', timeout: 30000 })
  await card.getByRole('button', { name: 'Chạy SQL kiểm tra', exact: true }).click()
  await card.getByRole('status').filter({ hasText: 'Thành công' }).waitFor({ timeout: 90000 })
  await card.scrollIntoViewIfNeeded()
  await page.evaluate(() => window.scrollBy(0, -120))
  await page.waitForTimeout(400)
  const bytes = await page.screenshot({
    path: path.join(SHOTS, 'sql-check-result-vi-light-1280.png'),
    scale: 'css',
    animations: 'disabled',
  })
  console.log(`captured ${bytes.length} bytes: ${await card.getByRole('status').innerText()}`)
} finally {
  await browser.close()
}
