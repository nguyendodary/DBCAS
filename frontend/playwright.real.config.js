import { defineConfig } from '@playwright/test'
import { existsSync, readFileSync } from 'node:fs'
import { readEnvironment } from '../scripts/local.mjs'

const file = new URL('../.env', import.meta.url)
const local = existsSync(file) ? readEnvironment(readFileSync(file, 'utf8')) : {}
const hasKey = Boolean((process.env.LLM_API_KEY || local.LLM_API_KEY || '').trim())
export default defineConfig({
  testDir: './e2e', testMatch: 'real-provider.spec.js', workers: 1,
  fullyParallel: false, retries: 0, maxFailures: 1, repeatEach: 3, timeout: 360000,
  expect: { timeout: 30000 },
  metadata: { live: hasKey && process.env.DBCAS_RUN_REAL_PROVIDER === '1' },
  outputDir: '../_review/real-provider-browser',
  reporter: [['list'], ['json', { outputFile: '../_review/real-provider-browser-results.json' }]],
  use: { baseURL: process.env.DBCAS_LOCAL_URL || 'http://localhost:18580',
    browserName: 'chromium', viewport: { width: 1440, height: 1000 },
    actionTimeout: 30000, screenshot: 'only-on-failure', trace: 'off' },
})
