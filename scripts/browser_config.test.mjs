import { test } from 'node:test'
import assert from 'node:assert/strict'
import standard from '../frontend/playwright.config.js'
import application from '../frontend/playwright.application.config.js'

test('production browser profile boots the real API and web app', () => {
  const api = application.webServer.find(server => server.url === 'http://127.0.0.1:8100/health')
  assert.ok(api, 'The application profile must start the API, not the fake OAuth process')
  assert.match(api.command, /release_server\.py .*--application$/)
  assert.ok(application.webServer.some(server => server.url === 'http://127.0.0.1:5174/login'))
  assert.ok(!application.webServer.some(server => server.command.includes('fake-oauth-server')))
})

test('default browser profile starts the loopback OAuth fixture', () => {
  assert.ok(standard.webServer.some(server => server.url === 'http://127.0.0.1:8101/health' && server.command.includes('fake-oauth-server')))
})
