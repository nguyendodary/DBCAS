import { spawnSync } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { main, ensureEnvironment, databaseUrl } from './local.mjs'
import { waitForFrontend } from './readiness.mjs'

const root = fileURLToPath(new URL('..', import.meta.url))
const count = Number(process.argv[2] || 3)
if (![1, 2, 3].includes(count)) throw new Error('Use 1, 2 or 3 consecutive runs')
const env = { ...ensureEnvironment(root), ...process.env }
if (env.LLM_API_KEY?.trim()) throw new Error('Clear the real LLM key before running the fake-provider gate')
env.LOCAL_DATABASE_URL = databaseUrl(env)
env.DBCAS_LOCAL_URL ||= `http://127.0.0.1:${env.LOCAL_WEB_PORT || 18080}`
env.DBCAS_QA_PROVIDER_URL ||= `http://127.0.0.1:${env.LOCAL_QA_PROVIDER_PORT || 18099}`
let executable = 'docker', prefix = []
if (process.platform === 'win32') {
  const resolved = spawnSync('where.exe', ['docker'], { encoding: 'utf8', windowsHide: true }).stdout?.split(/\r?\n/)[0] || ''
  if (resolved.toLowerCase().endsWith('.exe')) executable = resolved
  else { executable = 'wsl.exe'; prefix = ['-e', 'docker'] }
}
function run(command, args, options = {}) {
  const r = spawnSync(command, args, { cwd: root, env, stdio: 'inherit', windowsHide: true, ...options })
  if (r.error || r.status !== 0) throw new Error(`QA command failed: ${path.basename(command)} (${r.status})`)
  return r
}
const gid = run(executable, [...prefix, 'run', '--rm', '--network', 'none', '--entrypoint', 'stat', '-v', '/var/run/docker.sock:/var/run/docker.sock', 'postgres:17', '-c', '%g', '/var/run/docker.sock'], { encoding: 'utf8', stdio: 'pipe' }).stdout.trim()
if (!/^\d+$/.test(gid)) throw new Error('Cannot identify Docker socket group')
env.LOCAL_DOCKER_GID = gid
env.WSLENV = [...new Set([...(env.WSLENV || '').split(':').filter(Boolean), ...Object.keys(env).filter(key => /^(LOCAL_|POSTGRES_|LLM_|JWT_SECRET$)/.test(key))])].join(':')
const compose = ['compose', '-p', env.DBCAS_LOCAL_PROJECT || 'dbcas-local', '-f', 'docker-compose.local.yml']
function dc(args, fake = false) { return run(executable, [...prefix, ...compose, ...(fake ? ['-f', 'docker-compose.qa.yml'] : []), ...args]) }
main('start', root)
try {
  dc(['up', '-d', '--wait', '--wait-timeout', '180', 'qa-ai', 'app'], true)
  await waitForFrontend(`${env.DBCAS_LOCAL_URL}/readiness`)
  const response = await fetch(`${env.DBCAS_QA_PROVIDER_URL}/control`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ delay_seconds: 1, failure: false, hold: false }) })
  if (!response.ok) throw new Error('Fake provider control is unavailable')
  run(process.execPath, [path.join(root, 'frontend/node_modules/@playwright/test/cli.js'), 'test', '--config', 'playwright.practice.config.js', `--repeat-each=${count}`], { cwd: path.join(root, 'frontend') })
} finally {
  try {
    dc(['up', '-d', '--wait', '--force-recreate', 'app'])
    await waitForFrontend(`${env.DBCAS_LOCAL_URL}/readiness`)
  } finally { dc(['rm', '-s', '-f', 'qa-ai'], true) }
}
