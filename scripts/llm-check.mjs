// Check the configured OpenAI-compatible LLM provider without printing secrets.
// Reads .env, then lets process.env override individual values for temporary
// trials; never writes to .env and never changes a configuration value.
import { existsSync, readFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { readEnvironment } from './local.mjs'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const file = path.join(root, '.env')
const fromFile = existsSync(file) ? readEnvironment(readFileSync(file, 'utf8')) : {}
const get = (name) => String(process.env[name] ?? fromFile[name] ?? '').trim()

const rawProvider = get('LLM_PROVIDER') || 'openai_compatible'
const canonical = rawProvider.toLowerCase() === 'openai_compatible' ||
  rawProvider.toLowerCase() === 'compatible'
const recognized = canonical ? 'openai_compatible' : 'openai_compatible (unknown value, warning)'
const key = get('LLM_API_KEY')
const base = get('LLM_BASE_URL').replace(/\/+$/, '')
const model = get('LLM_MODEL')

function redact(text) {
  let out = String(text ?? '')
  if (key) out = out.split(key).join('***')
  return out.replace(/Bearer\s+[A-Za-z0-9._-]+/gi, 'Bearer ***')
}

function endpoint(suffix) {
  if (base.endsWith(suffix)) return base
  return `${base}/${suffix}`
}

console.log('llm:check (values from .env unless overridden by environment)')
console.log(`provider: ${recognized}`)
console.log(`base URL: ${redact(base) || '(empty)'}`)
console.log(`model: ${model || '(empty)'}`)

if (!key || !base || !model) {
  console.log('result: AI chưa cấu hình (LLM_API_KEY / LLM_BASE_URL / LLM_MODEL chưa đủ) - fallback ngân hàng vẫn dùng được.')
  process.exit(0)
}

const headers = { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' }

let modelStatus = 0
let ids = []
let modelsMs = 0
try {
  const started = Date.now()
  const response = await fetch(endpoint('models'), { headers, signal: AbortSignal.timeout(15000) })
  modelsMs = Date.now() - started
  modelStatus = response.status
  const payload = await response.json()
  ids = (payload?.data ?? []).map((item) => item?.id).filter(Boolean)
} catch (error) {
  console.log(`GET /models: ERROR ${redact(error.message)}`)
  console.log('result: FAIL - không gọi được endpoint models; kiểm tra LLM_BASE_URL và mạng.')
  process.exit(1)
}

console.log(`GET /models: HTTP ${modelStatus} in ${modelsMs} ms; ${ids.length} model(s)`)
if (modelStatus >= 400 || !ids.includes(model)) {
  console.log(`result: FAIL - model "${model}" không có trong danh sách khả dụng (không tự đổi LLM_MODEL).`)
  console.log('available ids:')
  for (const id of ids) console.log(`  - ${id}`)
  process.exit(1)
}

let chatStatus = 0
let chatMs = 0
let jsonValid = false
let detail = ''
try {
  const started = Date.now()
  const response = await fetch(endpoint('chat/completions'), {
    method: 'POST', headers,
    body: JSON.stringify({
      model,
      messages: [{ role: 'user', content: 'Trả về JSON: {"ok":true}' }],
      response_format: { type: 'json_object' },
      temperature: 0,
    }),
    signal: AbortSignal.timeout(60000),
  })
  chatMs = Date.now() - started
  chatStatus = response.status
  const payload = await response.json()
  const content = payload?.choices?.[0]?.message?.content
  if (chatStatus < 400 && typeof content === 'string') {
    try { JSON.parse(content); jsonValid = true } catch { jsonValid = false }
  } else {
    detail = redact(JSON.stringify(payload?.error ?? payload ?? '')).slice(0, 300)
  }
} catch (error) {
  detail = redact(error.message)
}

console.log(`POST /chat/completions: HTTP ${chatStatus} in ${chatMs} ms; JSON hợp lệ: ${jsonValid ? 'có' : 'không'}`)
if (detail) console.log(`detail (đã che key): ${detail}`)
console.log(`result: ${jsonValid ? 'PASS' : 'FAIL'}`)
process.exit(jsonValid ? 0 : 1)
