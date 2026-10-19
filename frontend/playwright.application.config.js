import { defineConfig } from '@playwright/test'
import base from './playwright.config.js'

// Real production application entrypoint with isolated PostgreSQL/sandbox data.
// AI credentials remain blank: failures and human takeover use actual services.
export default defineConfig({
  ...base,
  testDir: './e2e-application',
  webServer: [
    { ...base.webServer[0], command: `${base.webServer[0].command} --application` },
    base.webServer[1],
  ],
})
