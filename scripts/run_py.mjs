// Resolve a Python interpreter portably (Windows venv, DBCAS_TEST_PYTHON, python/python3)
// and run the given script. Used by npm scripts docs:check / docs:render.
// --prefer-tools puts tools/.venv first (for docs:verify-word); the default
// order keeps backend/.venv first because check_docs.py imports FastAPI.
import fs from 'node:fs'
import path from 'node:path'
import { spawnSync } from 'node:child_process'

const root = path.resolve(import.meta.dirname, '..')
const rawArgs = process.argv.slice(2)
const preferTools = rawArgs[0] === '--prefer-tools'
const args = preferTools ? rawArgs.slice(1) : rawArgs
const tools = [
  path.join(root, 'tools', '.venv', 'Scripts', 'python.exe'),
  path.join(root, 'tools', '.venv', 'bin', 'python'),
]
const backend = [
  path.join(root, 'backend', '.venv', 'Scripts', 'python.exe'),
  path.join(root, 'backend', '.venv', 'bin', 'python'),
]
const candidates = [
  process.env.DBCAS_TEST_PYTHON,
  ...(preferTools ? tools : backend),
  'python',
  'python3',
  ...(preferTools ? backend : tools),
].filter(Boolean)

let python = null
for (const c of candidates) {
  if (path.isAbsolute(c)) {
    if (fs.existsSync(c)) { python = c; break }
    continue
  }
  const r = spawnSync(c, ['-c', 'import sys; sys.exit(0)'], { stdio: 'ignore' })
  if (r.status === 0) { python = c; break }
}
if (!python) {
  console.error('No Python interpreter found (set DBCAS_TEST_PYTHON)')
  process.exit(2)
}
const result = spawnSync(python, args, { stdio: 'inherit', cwd: root })
process.exit(result.status ?? 1)
