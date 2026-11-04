import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  testMatch: 'local-smoke.spec.js',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 240_000,
  expect: { timeout: 20_000 },
  outputDir: '../_review/local-smoke',
  reporter: [['list'], ['json', { outputFile: '../_review/local-smoke-results.json' }]],
  use: {
    baseURL: process.env.DBCAS_LOCAL_URL || 'http://localhost:18080',
    browserName: 'chromium',
    viewport: { width: 1440, height: 1000 },
    screenshot: 'only-on-failure',
    trace: 'off',
    actionTimeout: 20_000,
  },
})
