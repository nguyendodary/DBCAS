import { defineConfig } from '@playwright/test'
export default defineConfig({
  testDir: './e2e', testMatch: process.env.DBCAS_QA_PROVIDER_URL ? ['practice-flows.spec.js', 'browser-qa.spec.js'] : 'practice-flows.spec.js', workers: 1, fullyParallel: false,
  retries: 0, timeout: 180000, expect: { timeout: 20000 },
  metadata: { demo: true },
  outputDir: '../_review/practice-browser',
  reporter: [['list'], ['json', { outputFile: '../_review/practice-browser-results.json' }]],
  use: { baseURL: process.env.DBCAS_LOCAL_URL || 'http://localhost:18080', browserName: 'chromium',
    viewport: { width: 1440, height: 1000 }, actionTimeout: 20000, screenshot: 'only-on-failure', trace: 'retain-on-failure' },
})
