// Regression guard for the QA fixture control channel.
//
// The control POST must reach the provider's own loopback listener. Depending
// on Docker's embedded DNS to resolve the "qa-ai" alias from inside "app" is
// an indirect path that can fail with EAI_AGAIN while the provider stays
// Healthy (CI 44329132276, qa-3, both attempts).
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

const source = fileURLToPath(new URL('./provider-control.mjs', import.meta.url))
const src = readFileSync(source, 'utf8')

test('provider control POST does not resolve an embedded-DNS service alias', () => {
  assert.equal(
    src.includes('qa-ai:8080/control'),
    false,
    'current code resolves the qa-ai alias via embedded DNS from app',
  )
  assert.equal(
    src.includes('127.0.0.1:8080/control'),
    true,
    'the control POST must use the provider container loopback listener',
  )
  assert.match(
    src,
    /'exec',\s*'-T',\s*'qa-ai',/,
    'docker compose exec must target the qa-ai service directly',
  )
})
