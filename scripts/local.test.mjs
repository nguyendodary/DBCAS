import { test } from 'node:test'
import assert from 'node:assert/strict'
import { mkdtempSync, readFileSync, writeFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'
import { databaseUrl, ensureEnvironment, readEnvironment } from './local.mjs'
import { createServer } from 'node:http'
import { waitForFrontend } from './readiness.mjs'

function removeTemporary(root) {
  assert.ok(path.resolve(root).startsWith(path.join(path.resolve(tmpdir()), 'dbcas-bootstrap-')))
  rmSync(root, { recursive: true })
}

test('creates distinct random secrets and preserves configuration on restart', () => {
  const root = mkdtempSync(path.join(tmpdir(), 'dbcas-bootstrap-'))
  try {
    const first = ensureEnvironment(root)
    assert.match(first.JWT_SECRET, /^[a-f0-9]{96}$/)
    assert.match(first.POSTGRES_PASSWORD, /^[a-f0-9]{48}$/)
    assert.notEqual(first.JWT_SECRET, first.POSTGRES_PASSWORD)
    const contents = readFileSync(path.join(root, '.env'), 'utf8')
    assert.deepEqual(ensureEnvironment(root), first)
    assert.equal(readFileSync(path.join(root, '.env'), 'utf8'), contents)
  } finally { removeTemporary(root) }
})

test('adds missing keys without changing an existing operator configuration', () => {
  const root = mkdtempSync(path.join(tmpdir(), 'dbcas-bootstrap-'))
  try {
    const original = '# retained\nJWT_SECRET="existing-secret"\nLLM_API_KEY=local-key\n'
    writeFileSync(path.join(root, '.env'), original)
    const env = ensureEnvironment(root)
    assert.equal(env.JWT_SECRET, 'existing-secret')
    assert.equal(env.LLM_API_KEY, 'local-key')
    assert.ok(readFileSync(path.join(root, '.env'), 'utf8').startsWith(original))
  } finally { removeTemporary(root) }
})

test('encodes credentials and parses quoted dotenv values without shell evaluation', () => {
  const env = readEnvironment('POSTGRES_USER=dbcas\nPOSTGRES_PASSWORD="p@ss:/# word"\nPOSTGRES_DB=demo\n')
  assert.equal(databaseUrl(env), 'postgresql://dbcas:p%40ss%3A%2F%23%20word@db:5432/demo')
})

async function withHealthServer(handler, check) {
  const server = createServer(handler)
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve))
  try { await check(`http://127.0.0.1:${server.address().port}/readiness`) }
  finally { server.closeAllConnections(); await new Promise(resolve => server.close(resolve)) }
}

test('waits for fresh proxied readiness after a stale Compose healthy flag', async () => {
  let calls = 0
  await withHealthServer((request, response) => {
    calls++
    response.writeHead(calls === 1 ? 503 : 200, { 'Content-Type': 'application/json' })
    response.end(JSON.stringify({ status: 'ready', dependencies: { database: true, sandbox: true } }))
  }, async url => {
    await waitForFrontend(url, { timeoutMs: 1500, pollMs: 5 })
    assert.equal(calls, 2)
  })
})

test('rejects a frontend HTML response and an API with an unhealthy dependency', async () => {
  let calls = 0
  await withHealthServer((request, response) => {
    calls++
    response.writeHead(200, { 'Content-Type': calls === 1 ? 'text/html' : 'application/json' })
    response.end(calls === 1 ? '<html>SPA fallback</html>' : JSON.stringify({ status: 'ready', dependencies: { database: calls > 2 } }))
  }, async url => {
    await waitForFrontend(url, { timeoutMs: 1500, pollMs: 5 })
    assert.equal(calls, 3)
  })
})

test('bounds a proxy that never becomes ready', async () => {
  await withHealthServer((request, response) => { response.writeHead(503); response.end() }, async url => {
    const started = performance.now()
    await assert.rejects(waitForFrontend(url, { timeoutMs: 250, requestTimeoutMs: 40, pollMs: 5 }), /chưa sẵn sàng qua proxy/)
    assert.ok(performance.now() - started < 1500)
  })
})

test('aborts a hanging readiness response within the startup budget', async () => {
  await withHealthServer(() => {}, async url => {
    const started = performance.now()
    await assert.rejects(waitForFrontend(url, { timeoutMs: 150, requestTimeoutMs: 40, pollMs: 5 }), /chưa sẵn sàng qua proxy/)
    assert.ok(performance.now() - started < 1500)
  })
})
