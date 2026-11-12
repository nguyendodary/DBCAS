// Post-rebuild check for the English header overflow reported as D1.
// Creates a fresh long-email learner, switches to EN and measures 1280/390.
import { chromium } from '../../../../frontend/node_modules/playwright/index.mjs'
import { mkdir, stat, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const BASE = 'http://localhost:18080'
const API = 'http://localhost:18000'
const OUT = path.dirname(fileURLToPath(import.meta.url))
const email = `w1-header-recheck-${Date.now()}@dbcas.local`
const password = 'W1Demo12345!'
const response = await fetch(`${API}/api/v1/auth/register`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ name: 'W1 Header Recheck', email, password, password_confirm: password }),
})
if (!response.ok) throw new Error(`register ${response.status} ${await response.text()}`)

const browser = await chromium.launch()
const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, baseURL: BASE })
const page = await context.newPage()
const results = []
try {
  await page.goto('/login')
  await page.getByLabel('Email', { exact: true }).fill(email)
  await page.getByLabel('Mật khẩu', { exact: true }).fill(password)
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click()
  await page.waitForURL(/\/dashboard$/)
  await page.evaluate(() => localStorage.setItem('dbcas_locale', 'en'))
  await page.reload()
  await page.getByRole('heading', { name: 'My competency', exact: true }).waitFor()
  await page.waitForTimeout(800)
  for (const width of [1280, 390]) {
    await page.setViewportSize({ width, height: 900 })
    for (const route of ['/dashboard', '/assessments']) {
      await page.goto(route)
      await page.waitForTimeout(700)
      const info = await page.evaluate(() => ({
        scrollWidth: document.documentElement.scrollWidth,
        innerWidth: innerWidth,
      }))
      const file = path.join(OUT, 'screenshots', `header-recheck-${route.slice(1)}-en-${width}.png`)
      await page.screenshot({ path: file, fullPage: true, scale: 'css', animations: 'disabled' })
      results.push({
        route,
        width,
        ...info,
        overflow: info.scrollWidth > info.innerWidth + 1,
        bytes: (await stat(file)).size,
        screenshot: path.basename(file),
      })
    }
  }
} finally {
  await browser.close()
}
await writeFile(
  path.join(OUT, 'header-recheck.json'),
  `${JSON.stringify({ checked_at: new Date().toISOString(), email, results }, null, 2)}\n`,
)
console.log(JSON.stringify(results, null, 2))
