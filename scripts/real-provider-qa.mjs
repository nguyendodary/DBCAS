// Local opt-in acceptance; preserve .env and the ordinary suite's network guard.
import { spawnSync } from 'node:child_process'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { ensureEnvironment, databaseUrl, main } from './local.mjs'
import { waitForFrontend } from './readiness.mjs'

const root = fileURLToPath(new URL('..', import.meta.url))
const prior = process.env.DBCAS_REAL_PRIOR_CALLS
if (!/^(?:[0-7]?\d|80)$/.test(prior || '')) throw new Error('Set verified DBCAS_REAL_PRIOR_CALLS (0–80); cache rows are not request counts')
const env = { ...ensureEnvironment(root), ...process.env }
env.DBCAS_REAL_MAX_CALLS = '80'
env.DBCAS_REAL_LEDGER_DIR ||= './_review/real-provider-20261104'
if (!/^\.\/_review\/real-provider(?:-[a-z0-9-]+)?$/.test(env.DBCAS_REAL_LEDGER_DIR)) throw new Error('Use a dedicated ignored ledger directory')
if (!env.LLM_API_KEY?.trim() || !env.LLM_BASE_URL?.startsWith('https://') || !env.LLM_MODEL?.trim()) {
  throw new Error('A configured HTTPS real provider and model are required')
}
const project = env.DBCAS_LOCAL_PROJECT || 'dbcas-real-qa'
if (!/^dbcas-real-qa(?:-[a-z0-9-]+)?$/.test(project)) throw new Error('Use a dedicated dbcas-real-qa project')
Object.assign(env, { DBCAS_LOCAL_PROJECT: project, LOCAL_WEB_PORT: env.LOCAL_WEB_PORT || '18580',
  LOCAL_API_PORT: env.LOCAL_API_PORT || '18500', LOCAL_MAIL_PORT: env.LOCAL_MAIL_PORT || '18525',
  LOCAL_SMTP_PORT: env.LOCAL_SMTP_PORT || '11525' })
env.LOCAL_DATABASE_URL = databaseUrl(env)
env.DBCAS_LOCAL_URL = `http://127.0.0.1:${env.LOCAL_WEB_PORT}`
env.DBCAS_RUN_REAL_PROVIDER = '1'
const executable = process.platform === 'win32' ? 'wsl.exe' : 'docker'
const prefix = process.platform === 'win32' ? ['-e', 'docker'] : []
function run(command, args, options = {}) {
  const result = spawnSync(command, args, { cwd: root, env, stdio: 'inherit', windowsHide: true, ...options })
  if (result.error || result.status !== 0) throw new Error(`QA command failed: ${path.basename(command)} (${result.status})`)
  return result
}
const gid = run(executable, [...prefix, 'run', '--rm', '--network', 'none', '--entrypoint', 'stat',
  '-v', '/var/run/docker.sock:/var/run/docker.sock', 'postgres:17', '-c', '%g', '/var/run/docker.sock'],
  { encoding: 'utf8', stdio: 'pipe' }).stdout.trim()
if (!/^\d+$/.test(gid)) throw new Error('Cannot identify Docker socket group')
env.LOCAL_DOCKER_GID = gid
env.WSLENV = [...new Set([...(env.WSLENV || '').split(':').filter(Boolean), ...Object.keys(env)
  .filter(key => /^(LOCAL_|POSTGRES_|LLM_|JWT_SECRET$|DBCAS_REAL_)/.test(key))])].join(':')
const compose = [...prefix, 'compose', '-p', project, '-f', 'docker-compose.local.yml']
function dc(args, metered = false) {
  return run(executable, [...compose, ...(metered ? ['-f', 'docker-compose.real-qa.yml'] : []), ...args])
}
const disabled = { LLM_API_KEY: ' ', LLM_BASE_URL: 'http://127.0.0.1:1/v1', LLM_MODEL: 'disabled-qa' }
// Seed with the provider disabled. Install the meter before giving the app a key.
const saved = { ...process.env }
Object.assign(process.env, env, disabled)
try { main('start', root) } finally {
  for (const key of Object.keys(process.env)) if (!(key in saved)) delete process.env[key]
  Object.assign(process.env, saved)
}
try {
  dc(['up', '-d', '--no-deps', '--wait', 'app'], true)
  await waitForFrontend(`${env.DBCAS_LOCAL_URL}/readiness`)
  run(process.execPath, [path.join(root, 'frontend/node_modules/@playwright/test/cli.js'), 'test',
    '--config', path.join(root, 'frontend/playwright.real.config.js'),
    ...(env.DBCAS_REAL_GREP ? ['--grep', env.DBCAS_REAL_GREP] : [])])
} finally {
  Object.assign(env, disabled)
  dc(['up', '-d', '--no-deps', '--wait', 'app'])
  await waitForFrontend(`${env.DBCAS_LOCAL_URL}/readiness`)
  const ledger = JSON.parse(readFileSync(path.join(root, env.DBCAS_REAL_LEDGER_DIR, 'ledger.json'), 'utf8'))
  console.log(JSON.stringify({ previous: ledger.prior_calls, new_requests: ledger.calls.length,
    total: ledger.prior_calls + ledger.calls.length }))
}
