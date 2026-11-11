import { defineConfig } from '@playwright/test'

const label = process.env.DBCAS_QA_RUN || 'manual'
if (!/^[a-z0-9-]+$/.test(label)) throw new Error('Invalid QA run label')
export default defineConfig({
  testDir: './e2e',
  testMatch: 'browser-qa.spec.js',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 300000,
  expect: { timeout: 25000 },
  outputDir: `../_review/qa/browser/${label}`,
  reporter: [['list'], ['json', { outputFile: `../_review/qa/${label}.json` }]],
  use: {
    baseURL: process.env.DBCAS_LOCAL_URL || 'http://localhost:18080',
    browserName: 'chromium',
    viewport: { width: 1440, height: 1000 },
    trace: 'off',
    screenshot: 'only-on-failure',
    actionTimeout: 20000,
  },
})
