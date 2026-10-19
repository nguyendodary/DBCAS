import { test as base } from '@playwright/test'
import fs from 'node:fs/promises'

// Capture paths/statuses only; never save auth headers, bodies or cookies here.
export const test = base.extend({
  browserDiagnostics: [async ({ context }, use, testInfo) => {
    const records = { test: testInfo.title, pageErrors: [], consoleErrors: [], responses: [], failedRequests: [] }
    const watched = new WeakSet()
    function observePage(page) {
      if (watched.has(page)) return
      watched.add(page)
      const pathname = url => { try { return new URL(url).pathname } catch { return '(non-http)' } }
      page.on('pageerror', e => records.pageErrors.push(e.message))
      page.on('console', e => { if (e.type() === 'error') records.consoleErrors.push({ text: e.text(), path: pathname(e.location().url) }) })
      page.on('response', r => { if (r.url().includes('/api/')) records.responses.push({ method: r.request().method(), path: pathname(r.url()), status: r.status() }) })
      page.on('requestfailed', r => records.failedRequests.push({ method: r.method(), path: pathname(r.url()), error: r.failure()?.errorText }))
    }
    function observe(ctx) { ctx.pages().forEach(observePage); ctx.on('page', observePage) }
    observe(context)
    await use({ observe, records })
    const output = testInfo.outputPath('browser-diagnostics.json')
    await fs.writeFile(output, JSON.stringify(records, null, 2))
    await testInfo.attach('browser-diagnostics', { path: output, contentType: 'application/json' })
  }, { auto: true }],
})
export { expect, request } from '@playwright/test'
