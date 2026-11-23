import { spawn, spawnSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { main, ensureEnvironment, databaseUrl, demoProfileFiles } from './local.mjs'
import { waitForFrontend, waitForProvider, postWithRetry } from './readiness.mjs'

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
for (const file of demoProfileFiles(env.DBCAS_DEMO_PROFILE)) compose.push('-f', file)
function dc(args, fake = false) { return run(executable, [...prefix, ...compose, ...(fake ? ['-f', 'docker-compose.qa.yml'] : []), ...args]) }
main('start', root)
let memorySampler = null
try {
  dc(['up', '-d', '--wait', '--wait-timeout', '180', 'qa-ai', 'app'], true)
  // Diagnostic-only: sample the provider's cgroup memory from here until the
  // launcher stops, uploaded as an artifact even on a passing shard.
  const memoryLog = path.join(root, '_review', 'qa-memory.log')
  fs.mkdirSync(path.dirname(memoryLog), { recursive: true })
  memorySampler = spawn(process.execPath, [
    path.join(root, 'scripts/qa-memory-sample.mjs'), memoryLog,
    env.DBCAS_LOCAL_PROJECT || 'dbcas-local', JSON.stringify({ executable, prefix }),
  ], { cwd: root, env, stdio: 'ignore', windowsHide: true })
  memorySampler.unref?.()
  await waitForFrontend(`${env.DBCAS_LOCAL_URL}/readiness`)
  // Compose's internal healthcheck can pass before the published provider port
  // is reachable from the host; verify that path, then issue the control POST
  // with bounded retries so a startup race cannot fail the whole QA shard.
  await waitForProvider(env.DBCAS_QA_PROVIDER_URL)
  await postWithRetry(`${env.DBCAS_QA_PROVIDER_URL}/control`, { delay_seconds: 1, failure: false, hold: false })
  // Diagnostic only: stream every Docker event from just before the suite starts.
  // The file is uploaded as a CI artifact even when the shard fails, so it does
  // not depend on a --since window computed after the fact.
  const eventsLog = path.join(root, '_review', 'qa-docker-events.log')
  fs.mkdirSync(path.dirname(eventsLog), { recursive: true })
  const eventsFd = fs.openSync(eventsLog, 'w')
  fs.writeSync(eventsFd, `# start ${new Date().toISOString()} project=${env.DBCAS_LOCAL_PROJECT || 'dbcas-local'}\n`)
  const eventsProcess = spawn(executable, [...prefix, 'events', '--format', '{{json .}}'], {
    cwd: root, env, stdio: ['ignore', eventsFd, eventsFd], windowsHide: true,
  })
  eventsProcess.unref?.()
  try {
    run(process.execPath, [path.join(root, 'frontend/node_modules/@playwright/test/cli.js'), 'test', '--config', 'playwright.practice.config.js', `--repeat-each=${count}`], { cwd: path.join(root, 'frontend') })
  } finally {
    try { eventsProcess.kill('SIGTERM') } catch { /* already exited */ }
    try { fs.writeSync(eventsFd, `# end ${new Date().toISOString()}\n`); fs.closeSync(eventsFd) } catch { /* best effort */ }
  }
  if (env.DBCAS_QA_LOAD === '1') {
    const python = env.DBCAS_TEST_PYTHON || path.join(root, 'backend', process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python')
    run(python, [path.join(root, 'backend/tests/practice_load.py'), '--base', env.DBCAS_LOCAL_URL,
      '--provider', env.DBCAS_QA_PROVIDER_URL, '--output', path.join(root, '_review/practice-load-results.json')],
    { env: { ...env, DBCAS_QA_LOAD_GUARD: 'fake-provider-only' } })
  }
} finally {
  try { memorySampler?.kill('SIGTERM') } catch { /* already exited */ }
  try {
    dc(['up', '-d', '--wait', '--force-recreate', 'app'])
    await waitForFrontend(`${env.DBCAS_LOCAL_URL}/readiness`)
  } finally { dc(['rm', '-s', '-f', 'qa-ai'], true) }
}
