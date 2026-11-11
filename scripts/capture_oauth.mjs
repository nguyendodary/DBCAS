// Reproduce exact CSS viewport dimensions independently of an interactive
// browser profile's zoom. Both origins are local; no credentials are read.
import { chromium } from '../frontend/node_modules/playwright/index.mjs'
import { mkdir, writeFile } from 'node:fs/promises'
import { strict as assert } from 'node:assert'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const output = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../docs/qa/oauth-20261112/screenshots')
await mkdir(output, { recursive: true })
const browser = await chromium.launch()
const results = []
try {
  for (const [phase, origin] of [['before', 'http://localhost:18080'], ['after', 'http://127.0.0.1:5175']]) {
    for (const theme of ['light', 'dark']) {
      for (const width of [1280, 390]) {
        const context = await browser.newContext({ viewport: { width, height: 900 }, deviceScaleFactor: 1 })
        await context.addInitScript((theme) => {
          localStorage.setItem('dbcas_theme', theme)
          localStorage.setItem('dbcas_locale', 'vi')
        }, theme)
        const page = await context.newPage()
        for (const screen of ['login', 'register']) {
          const read = page.waitForResponse(r => r.url().endsWith('/auth/oauth/providers'))
          await page.goto(`${origin}/${screen}`)
          const providers = await (await read).json()
          assert(providers.providers.every(p => p.configured === false))
          await page.getByRole('heading', { level: 1 }).waitFor()
          await page.evaluate(() => document.fonts.ready)
          const dimensions = await page.evaluate(() => ({ width: innerWidth, scrollWidth: document.documentElement.scrollWidth }))
          assert.equal(dimensions.width, width)
          assert(dimensions.scrollWidth <= width)
          const count = await page.locator('.auth-oauth').count()
          assert.equal(count, phase === 'before' ? 0 : 2)
          if (phase === 'after') await page.waitForFunction(() =>
            [...document.querySelectorAll('button.auth-oauth')].every(button => !button.disabled))
          const filename = `${phase}-${screen}-${theme}-${width}.png`
          await page.screenshot({ path: path.join(output, filename), fullPage: true, scale: 'css', animations: 'disabled' })
          results.push({ filename, phase, origin, screen, theme, cssWidth: width, providerControls: count, overflow: false })
          if (phase === 'after' && screen === 'login' && theme === 'light' && width === 390) {
            await page.getByRole('button', { name: 'Tiếp tục với Google' }).click()
            assert.equal(await page.getByRole('status').innerText(), 'Chưa cấu hình đăng nhập bằng Google. Vui lòng dùng email.')
            await page.screenshot({ path: path.join(output, 'after-notice-light-390.png'), fullPage: true, scale: 'css' })
          }
        }
        await context.close()
      }
    }
  }
} finally { await browser.close() }
await writeFile(path.join(output, 'verification.json'), `${JSON.stringify(results, null, 2)}\n`)
console.log(`${results.length} captures; exact 1280/390 CSS viewports; zero overflow; before 0/after 2 provider controls`)
