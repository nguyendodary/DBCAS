import { defineConfig } from '@playwright/test'
import base from './playwright.config.js'

// Real production application entrypoint with isolated PostgreSQL/sandbox data.
// AI credentials remain blank: failures and human takeover use actual services.
const apiServer = base.webServer.find((server) => server.url === 'http://127.0.0.1:8100/health')
const frontendServer = base.webServer.find((server) => server.url === 'http://127.0.0.1:5174/login')
if (!apiServer || !frontendServer)
  throw new Error('Application browser profile requires API and web servers')

export default defineConfig({
  ...base,
  testDir: './e2e-application',
  webServer: [{ ...apiServer, command: `${apiServer.command} --application` }, frontendServer],
})
