import { spawnSync } from 'node:child_process'
import { mkdirSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { main, ensureEnvironment, databaseUrl } from './local.mjs'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const count = Number(process.argv[2] || 3)
if (!Number.isInteger(count) || count < 1 || count > 3) throw new Error('Use 1, 2 or 3 QA runs')
const env = { ...ensureEnvironment(root), ...process.env }
if (env.LLM_API_KEY?.trim()) throw new Error('QA reset requires a local environment without a real LLM key')
env.LOCAL_DATABASE_URL = databaseUrl(env)
env.DBCAS_LOCAL_URL ||= `http://localhost:${env.LOCAL_WEB_PORT || 18080}`
env.DBCAS_QA_PROVIDER_URL ||= `http://localhost:${env.LOCAL_QA_PROVIDER_PORT || 18099}`
let docker = process.platform === 'win32' ? 'docker.exe' : 'docker', prefix = []
if (process.platform === 'win32') {
  const resolved = spawnSync('where.exe', ['docker'], { encoding: 'utf8', windowsHide: true }).stdout?.split(/\r?\n/)[0] || ''
  if (!resolved.toLowerCase().endsWith('.exe')) { docker = 'wsl.exe'; prefix = ['-e', 'docker'] }
}
function run(executable, args, options = {}) {
  const result = spawnSync(executable, args, { cwd: root, env, stdio: 'inherit', windowsHide: true, ...options })
  if (result.error || result.status !== 0) throw new Error(`QA command failed: ${path.basename(executable)} (exit ${result.status})`)
  return result
}
function dc(args) {
  return run(docker, [...prefix, 'compose', '-p', env.DBCAS_LOCAL_PROJECT || 'dbcas-local', '-f', 'docker-compose.local.yml', ...args])
}
const gid = run(docker, [...prefix, 'run', '--rm', '--network', 'none', '--entrypoint', 'stat', '-v', '/var/run/docker.sock:/var/run/docker.sock', 'postgres:17', '-c', '%g', '/var/run/docker.sock'], { encoding: 'utf8', stdio: 'pipe' }).stdout.trim()
if (!/^\d+$/.test(gid)) throw new Error('Cannot determine the local Docker socket group')
env.LOCAL_DOCKER_GID = gid
env.WSLENV = [...new Set([...(env.WSLENV || '').split(':').filter(Boolean), ...Object.keys(env).filter(k => /^(LOCAL_|POSTGRES_|LLM_|JWT_SECRET$)/.test(k))])].join(':')
mkdirSync(path.join(root, '_review/qa'), { recursive: true })
async function waitWeb() {
  const url = `http://localhost:${env.LOCAL_WEB_PORT || 18080}/readiness`
  for (let attempt = 0; attempt < 30; attempt++) {
    try { if ((await fetch(url, { signal: AbortSignal.timeout(3000) })).ok) return } catch { /* Allow bounded DNS/container recovery. */ }
    await new Promise(resolve => setTimeout(resolve, 1000))
  }
  throw new Error('The UI proxy did not become ready')
}
async function browser(mode, iteration) {
  await waitWeb()
  run(process.execPath, ['frontend/node_modules/@playwright/test/cli.js', 'test', '--config', 'frontend/playwright.qa.config.js',
    ...(mode === 'manual' ? ['--grep', 'journey'] : [])], { env: { ...env, DBCAS_QA_MODE: mode, DBCAS_QA_RUN: `run-${iteration}-${mode}` } })
}
try {
  for (let iteration = 1; iteration <= count; iteration++) {
    console.log(`QA ${iteration}/${count}: clean reset, no-key journey, delayed AI journey and recovery`)
    main('reset', root)
    await browser('manual', iteration)
    dc(['-f', 'docker-compose.qa.yml', 'up', '-d', '--wait', '--wait-timeout', '120', 'qa-ai', 'app', 'frontend'])
    await browser('ai', iteration)
  }
} finally {
  dc(['up', '-d', '--no-deps', '--force-recreate', '--wait', '--wait-timeout', '120', 'app'])
  dc(['-f', 'docker-compose.qa.yml', 'rm', '--stop', '--force', 'qa-ai'])
  await waitWeb()
}
