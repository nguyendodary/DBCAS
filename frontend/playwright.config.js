import { defineConfig } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const python = path.resolve(here, '../backend', process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python')
const selectedBrowser = process.env.DBCAS_BROWSER ?? 'chromium'
const reviewRoot = process.env.DBCAS_E2E_OUTPUT ?? '../../_review/remediation'
if (!['chromium', 'firefox', 'webkit', 'msedge'].includes(selectedBrowser)) throw new Error('Unsupported release browser')
export default defineConfig({
  testDir: './e2e', fullyParallel: false, workers: 1, timeout: 120_000,
  globalTeardown: './e2e/teardown.js',
  expect: { timeout: 15_000 }, retries: 0,
  outputDir: path.join(reviewRoot, 'browser-results'),
  reporter: [['list'], ['json', { outputFile: path.join(reviewRoot, `browser-results-${selectedBrowser}.json`) }]],
  use: { baseURL: 'http://127.0.0.1:5174', viewport: { width: 1440, height: 1000 },
    browserName: selectedBrowser === 'msedge' ? 'chromium' : selectedBrowser,
    channel: selectedBrowser === 'msedge' ? 'msedge' : undefined,
    trace: 'off', screenshot: 'only-on-failure', actionTimeout: 15_000, navigationTimeout: 30_000 },
  webServer: [
    { command: `"${python}" tests/release_server.py --workers ${process.platform === 'win32' ? 1 : 2}`, cwd: path.join(here, '../backend'),
      url: 'http://127.0.0.1:8100/health', timeout: 240_000, reuseExistingServer: false },
    { command: 'npm run dev -- --config vite.e2e.config.js', cwd: here,
      url: 'http://127.0.0.1:5174/login', timeout: 60_000, reuseExistingServer: false },
  ],
})
