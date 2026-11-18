// Reach the QA provider through the Compose network the app already uses.
// The provider's published host port can stop forwarding mid-suite while the
// container and its internal :8080 listener stay healthy; the control POST is
// fixture setup, so it must not depend on that host-side path.
import { spawnSync } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = fileURLToPath(new URL('..', import.meta.url))

function dockerCommand() {
  if (process.platform !== 'win32') return { executable: 'docker', prefix: [] }
  const resolved =
    spawnSync('where.exe', ['docker'], {
      encoding: 'utf8',
      windowsHide: true,
    }).stdout?.split(/\r?\n/)[0] || ''
  if (resolved.toLowerCase().endsWith('.exe')) return { executable: resolved, prefix: [] }
  return { executable: 'wsl.exe', prefix: ['-e', 'docker'] }
}

// Execute one POST inside the app container against qa-ai:8080. The payload is
// passed as a single argv element (no shell interpolation) and the provider's
// JSON response is returned to the caller.
export function postProviderControl(payload) {
  const project = process.env.DBCAS_LOCAL_PROJECT || 'dbcas-local'
  const { executable, prefix } = dockerCommand()
  const code = [
    'import json,sys,urllib.request',
    'req=urllib.request.Request("http://qa-ai:8080/control",',
    '  data=json.loads(sys.argv[1]).encode(), headers={"Content-Type":"application/json"})',
    'print(urllib.request.urlopen(req, timeout=15).read().decode())',
  ].join('\n')
  const args = [
    ...prefix,
    'compose',
    '-p',
    project,
    '-f',
    'docker-compose.local.yml',
    '-f',
    'docker-compose.qa.yml',
    'exec',
    '-T',
    'app',
    'python',
    '-c',
    code,
    JSON.stringify(payload),
  ]
  const result = spawnSync(executable, args, {
    cwd: root,
    env: process.env,
    encoding: 'utf8',
    windowsHide: true,
  })
  if (result.error || result.status !== 0) {
    throw new Error(
      `Provider control via Compose failed: ${result.error?.message || result.stderr?.trim() || result.status}`,
    )
  }
  return JSON.parse(result.stdout.trim())
}
