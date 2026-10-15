import { execFileSync } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

export default function teardown() {
  const backend = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../backend')
  const python = process.env.DBCAS_TEST_PYTHON ?? path.join(backend, process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python')
  execFileSync(python, ['tests/cleanup_release.py'], { cwd: backend, stdio: 'pipe' })
}
