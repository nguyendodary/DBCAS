import { spawnSync } from 'node:child_process'
import { existsSync, readFileSync, writeFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { readEnvironment } from './local.mjs'

// Build a synthetic-only data snapshot from the already-seeded demo database.
// The snapshot intentionally excludes schema_migration (owned by the migration
// ledger) and role (recreated by initialize_db), so it can be restored into a
// fresh schema without changing seed semantics or applied migrations.
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const env = { ...readEnvironment(readFileSync(path.join(root, '.env'), 'utf8')), ...process.env }
const project = env.DBCAS_LOCAL_PROJECT || 'dbcas-local'
const output = path.join(root, '.demo-seed.sql')
const compose = ['compose', '--project-name', project, '-f', 'docker-compose.local.yml']
const dump = spawnSync(
  process.platform === 'win32' ? 'docker.exe' : 'docker',
  [
    ...compose,
    'exec',
    '-T',
    'db',
    'pg_dump',
    '-U',
    env.POSTGRES_USER || 'dbcas',
    '-d',
    env.POSTGRES_DB || 'dbcas',
    '--data-only',
    '--inserts',
    '--no-owner',
    '--no-privileges',
    '--exclude-table=role',
    '--exclude-table=schema_migration',
  ],
  { cwd: root, env, encoding: 'utf8', maxBuffer: 256 * 1024 * 1024 },
)
if (dump.status !== 0) {
  console.error(dump.stderr || 'pg_dump failed')
  process.exit(1)
}
if (!dump.stdout.includes('INSERT INTO')) {
  console.error('Refusing to write a snapshot without demo data')
  process.exit(1)
}
writeFileSync(output, dump.stdout, { encoding: 'utf8' })
console.log(`Wrote ${output} (${Math.round(dump.stdout.length / 1024)} KiB)`)
if (!existsSync(path.join(root, 'docker-compose.demo-snapshot.yml'))) {
  console.error('Missing docker-compose.demo-snapshot.yml')
  process.exit(1)
}
