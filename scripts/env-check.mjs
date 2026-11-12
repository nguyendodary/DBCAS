// Name-only environment check. Never prints values or reads a second .env.
import { existsSync, readFileSync, statSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { maskSecret, readEnvironment } from './local.mjs'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const file = path.join(root, '.env')
const required = ['LLM_API_KEY', 'LLM_BASE_URL', 'LLM_MODEL']
const problems = []

function linkedWorktree() {
  try { return statSync(path.join(root, '.git')).isFile() } catch { return false }
}

console.log(`env:check: ${file}`)
if (!existsSync(file)) {
  if (linkedWorktree()) {
    console.error('env:check: FAIL - linked worktree has no .env; create it from .env.example and run again.')
    process.exit(1)
  }
  console.log('env:check: no .env - OK for a fresh clone; npm start will create demo defaults (AI uses template fallback).')
  process.exit(0)
}

const values = readEnvironment(readFileSync(file, 'utf8'))
const present = required.filter(name => Object.hasOwn(values, name))
const missing = required.filter(name => !Object.hasOwn(values, name))
const empty = required.filter(name => Object.hasOwn(values, name) && !values[name]?.trim())
console.log(`env:check: AI names present: ${present.join(', ') || 'none'}`)
if (missing.length) console.log(`env:check: missing names: ${missing.join(', ')}`)
if (empty.length) console.log(`env:check: empty names: ${empty.join(', ')}`)

const key = values.LLM_API_KEY?.trim() || ''
const base = values.LLM_BASE_URL?.trim() || ''
const model = values.LLM_MODEL?.trim() || ''
const configured = Boolean(key || base || model)
if (!configured) {
  console.log('env:check: AI not configured - OK for demo/template mode.')
  process.exit(0)
}

if (!key) problems.push('LLM_API_KEY is empty')
else {
  const masked = maskSecret(key)
  const syntax = key.length >= 20 && !/\s/.test(key) && /^[A-Za-z0-9._-]+$/.test(key)
  console.log(`env:check: LLM_API_KEY ${syntax ? 'looks syntactically valid' : 'does not look syntactically valid'} (${masked})`)
  if (!syntax) problems.push('LLM_API_KEY format')
}
if (!base) problems.push('LLM_BASE_URL is empty')
else {
  let valid = false
  try { const url = new URL(base); valid = url.protocol === 'https:' && Boolean(url.host) } catch {}
  console.log(`env:check: LLM_BASE_URL ${valid ? 'is a valid HTTPS URL' : 'is not a valid HTTPS URL'}`)
  if (!valid) problems.push('LLM_BASE_URL format')
}
if (!model) problems.push('LLM_MODEL is empty')
else console.log(`env:check: LLM_MODEL ${model ? 'set' : 'not set'}`)

if (problems.length) {
  console.error(`env:check: FAIL - ${problems.join('; ')}`)
  process.exit(1)
}
console.log('env:check: PASS - AI variables are present and syntactically valid.')
