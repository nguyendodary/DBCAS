// Locate a Python interpreter that can run the repository scripts, without
// assuming anything about the caller's PATH. Windows-first: the backend venv,
// then the `py` launcher, then python3/python. Override with DBCAS_TEST_PYTHON.
import { execFile } from 'node:child_process'
import { promisify } from 'node:util'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const run = promisify(execFile)
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')

export async function pythonCommand() {
  const venv = path.join(ROOT, 'backend',
    process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python')
  const ordered = [process.env.DBCAS_TEST_PYTHON, venv,
    process.platform === 'win32' ? 'py' : 'python3', 'python'].filter(Boolean)
  for (const candidate of ordered) {
    try {
      await run(candidate, candidate === 'py' ? ['-3', '-c', 'import sys'] : ['-c', 'import sys'])
      return candidate
    } catch { /* try the next candidate */ }
  }
  return null
}

export const scriptArgs = (command, script) =>
  [...(command === 'py' ? ['-3'] : []), script]
