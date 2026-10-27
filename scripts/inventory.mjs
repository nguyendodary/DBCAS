#!/usr/bin/env node
// Generated interface inventories: docs/inventory/api-routes.json and
// docs/inventory/frontend-routes.json.
//
//   node scripts/inventory.mjs check     fail when a committed inventory no longer matches its sources
//   node scripts/inventory.mjs write     regenerate both inventories//
// The generator is static analysis only: no application import, no database, no network.
import { execFile } from 'node:child_process'
import { promisify } from 'node:util'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { pythonCommand, scriptArgs } from './python.mjs'

const run = promisify(execFile)
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const GENERATOR = path.join(ROOT, 'scripts', 'generate_route_inventory.py')
const FLAG = { check: '--verify', write: '--write' }
const mode = process.argv[2]

if (!['check', 'write'].includes(mode)) {
  console.error('usage: node scripts/inventory.mjs <check|write>')
  process.exit(2)
}

const python = await pythonCommand()
if (!python) {
  console.error('FAIL: no Python interpreter found for scripts/generate_route_inventory.py (set DBCAS_TEST_PYTHON)')
  process.exit(1)
}

const lines = (text) => text.trim().split(/\r?\n/).filter(Boolean)
try {
  const output = await run(python, scriptArgs(python, GENERATOR).concat([FLAG[mode]]), { cwd: ROOT })
  for (const line of lines(output.stdout)) console.log(line)
} catch (error) {
  for (const line of lines(`${error.stderr || ''}${error.stdout || ''}`)) console.error(line)
  console.error(`FAIL: inventory ${mode} reported drift`)
  process.exit(1)
}
