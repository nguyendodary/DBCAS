import { randomBytes } from 'node:crypto'
import { existsSync, readFileSync, writeFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { spawnSync } from 'node:child_process'

export function readEnvironment(text) {
  return Object.fromEntries(text.split(/\r?\n/).flatMap(line => {
    const match = /^\s*([A-Z][A-Z0-9_]*)\s*=\s*(.*?)\s*$/.exec(line)
    if (!match) return []
    const value = match[2]
    return [[match[1], /^(['"]).*\1$/.test(value) ? value.slice(1, -1) : value.split(/\s+#/)[0]]]
  }))
}

export function ensureEnvironment(root) {
  const file = path.join(root, '.env')
  const original = existsSync(file) ? readFileSync(file, 'utf8') : ''
  const values = readEnvironment(original)
  const defaults = {
    POSTGRES_USER: 'dbcas', POSTGRES_DB: 'dbcas',
    POSTGRES_PASSWORD: randomBytes(24).toString('hex'),
    JWT_SECRET: randomBytes(48).toString('hex'),
    LLM_API_KEY: '', LLM_BASE_URL: '', LLM_MODEL: '',
  }
  const additions = Object.entries(defaults).filter(([key]) => !(key in values))
  if (additions.length) {
    const text = original + (original && !original.endsWith('\n') ? '\n' : '')
      + additions.map(([key, value]) => `${key}=${value}\n`).join('')
    writeFileSync(file, text, { mode: 0o600, flag: existsSync(file) ? 'w' : 'wx' })
    Object.assign(values, Object.fromEntries(additions))
  }
  for (const key of ['POSTGRES_USER', 'POSTGRES_DB', 'POSTGRES_PASSWORD', 'JWT_SECRET']) {
    if (!values[key]?.trim()) throw new Error(`Điền ${key} trong .env rồi chạy lại.`)
  }
  return values
}

export function databaseUrl(env) {
  return `postgresql://${encodeURIComponent(env.POSTGRES_USER)}:${encodeURIComponent(env.POSTGRES_PASSWORD)}@db:5432/${encodeURIComponent(env.POSTGRES_DB)}`
}

export function main(action = 'start', root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')) {
  if (!['start', 'stop', 'reset'].includes(action)) throw new Error('Dùng npm start, npm run stop hoặc npm run reset.')
  const env = { ...ensureEnvironment(root), ...process.env }
  const project = env.DBCAS_LOCAL_PROJECT || 'dbcas-local'
  if (!/^[a-z][a-z0-9-]{0,48}$/.test(project)) throw new Error('DBCAS_LOCAL_PROJECT không hợp lệ.')
  let executable = process.platform === 'win32' ? 'docker.exe' : 'docker'
  let prefix = []
  if (process.platform === 'win32') {
    const resolved = spawnSync('where.exe', ['docker'], { encoding: 'utf8', windowsHide: true }).stdout?.split(/\r?\n/)[0] || ''
    if (resolved && !resolved.toLowerCase().endsWith('.exe')) {
      executable = 'wsl.exe'
      prefix = ['-e', 'docker']
    }
  }
  function docker(args, { capture = false, allowFailure = false } = {}) {
    // The WSL fallback needs explicit propagation of computed Compose values.
    const forwarded = Object.keys(env).filter(key => /^(LOCAL_|POSTGRES_|LLM_|GOOGLE_|GITHUB_|OAUTH_|PROMPT_BUILDER_|EVALUATION_FAKE_|JWT_SECRET$)/.test(key))
    env.WSLENV = [...new Set([...(env.WSLENV || '').split(':').filter(Boolean), ...forwarded])].join(':')
    let result = spawnSync(executable, [...prefix, ...args], {
      cwd: root, env, encoding: 'utf8', stdio: capture ? 'pipe' : 'inherit', windowsHide: true,
    })
    if (result.error?.code === 'ENOENT' && process.platform === 'win32' && executable === 'docker.exe') {
      executable = 'wsl.exe'
      prefix = ['-e', 'docker']
      result = spawnSync(executable, [...prefix, ...args], {
        cwd: root, env, encoding: 'utf8', stdio: capture ? 'pipe' : 'inherit', windowsHide: true,
      })
    }
    if ((result.error || result.status !== 0) && !allowFailure) {
      throw new Error(`Docker chưa hoàn tất bước ${args[0]}. Mở Docker Desktop (Linux containers), kiểm tra log phía trên rồi chạy lại.`)
    }
    return result
  }
  const probe = ['info', '--format', '{{.ServerVersion}}']
  let info = docker(probe, { capture: true, allowFailure: true })
  if ((info.status !== 0 || !/^\d+\./.test(info.stdout?.trim())) && process.platform === 'win32') {
    executable = 'wsl.exe'
    prefix = ['-e', 'docker']
    info = docker(probe, { capture: true, allowFailure: true })
  }
  if (info.status !== 0 || !/^\d+\./.test(info.stdout?.trim())) {
    throw new Error('Docker chưa sẵn sàng. Mở Docker Desktop (Linux containers) rồi chạy lại npm start.')
  }
  const compose = ['compose', '--project-name', project, '-f', 'docker-compose.local.yml']
  if (env.PROMPT_BUILDER_MODEL_PATH?.trim()) compose.push('-f', 'docker-compose.ai.yml')
  env.LOCAL_DATABASE_URL = databaseUrl(env)
  if (action === 'stop') {
    docker([...compose, 'stop'])
    return
  }
  if (action === 'reset') docker([...compose, 'down', '--volumes', '--remove-orphans'])
  if (!env.LOCAL_DOCKER_GID) {
    if (docker(['image', 'inspect', 'postgres:17'], { capture: true, allowFailure: true }).status !== 0) {
      docker(['pull', 'postgres:17'])
    }
    const group = docker(['run', '--rm', '--network', 'none', '--entrypoint', 'stat',
      '-v', '/var/run/docker.sock:/var/run/docker.sock', 'postgres:17', '-c', '%g', '/var/run/docker.sock'], { capture: true }).stdout.trim()
    if (!/^\d+$/.test(group)) throw new Error('Không đọc được group Docker socket; đặt LOCAL_DOCKER_GID trong .env.')
    env.LOCAL_DOCKER_GID = group
  }
  console.log('Đang dựng DBCAS, khởi tạo dữ liệu demo và chờ dịch vụ sẵn sàng…')
  docker([...compose, 'up', '--build', '--detach', '--wait', '--wait-timeout', '600'])
  const ready = spawnSync(process.execPath, [path.join(root, 'scripts/readiness.mjs'), `http://127.0.0.1:${env.LOCAL_WEB_PORT || 18080}/readiness`], {
    cwd: root, env, stdio: 'inherit', windowsHide: true, timeout: 50000,
  })
  if (ready.error || ready.status !== 0) throw new Error('Ứng dụng chưa sẵn sàng qua proxy. Kiểm tra Docker rồi chạy lại npm start.')
  console.log(`DBCAS: http://localhost:${env.LOCAL_WEB_PORT || 18080}`)
  console.log(`API: http://localhost:${env.LOCAL_API_PORT || 18000}/docs`)
  console.log(`Hộp thư demo: http://localhost:${env.LOCAL_MAIL_PORT || 18025}`)
  console.log('Demo: admin@dbcas.local / Demo12345! · learner@dbcas.local / Demo12345!')
  console.log('Dừng: npm run stop · Xóa dữ liệu demo và tạo lại: npm run reset')
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try { main(process.argv[2]) }
  catch (error) { console.error(error.message); process.exitCode = 1 }
}
