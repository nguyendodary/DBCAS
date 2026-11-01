import { test } from 'node:test'
import assert from 'node:assert/strict'
import { mkdtempSync, readFileSync, writeFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'
import { databaseUrl, ensureEnvironment, readEnvironment } from './local.mjs'

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
