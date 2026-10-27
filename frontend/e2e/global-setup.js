import { execFileSync } from 'node:child_process'
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const reviewRoot = path.resolve(here, '../../../_review/remediation')
const manifestPath = process.env.DBCAS_TEST_MANIFEST
  ?? path.join(reviewRoot, 'release-containers.json')
const apiBase = 'http://127.0.0.1:8100/api/v1'

function dockerInspect(name) {
  return JSON.parse(execFileSync('docker', ['inspect', name], { encoding: 'utf8' }))[0]
}

function psqlScalar(container, user, database, sql) {
  // Docker Desktop can return exit 0 with empty exec output or an empty
  // redirected file on Windows. Query PostgreSQL natively, always read-only;
  // retain every ownership, version and persistent-probe assertion below.
  const backend = path.resolve(here, '../../backend')
  const python = process.env.DBCAS_TEST_PYTHON ?? path.join(backend,
    process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python')
  const result = JSON.parse(execFileSync(python,
    ['tests/query_release_scalar.py', container, user, database, sql], { cwd: backend, encoding: 'utf8' }))
  if (typeof result.scalar !== 'string' || !result.scalar.trim()) throw new Error('Isolation query returned no scalar')
  return result.scalar.trim()
}

async function api(pathname, { method = 'GET', body, token } = {}) {
  const response = await fetch(`${apiBase}${pathname}`, {
    method,
    headers: {
      'content-type': 'application/json',
      ...(token ? { authorization: `Bearer ${token}` } : {}),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  const text = await response.text()
  if (!response.ok) throw new Error(`${method} ${pathname} returned ${response.status}: ${text.slice(0, 300)}`)
  return text ? JSON.parse(text) : null
}

export default async function globalSetup() {
  const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'))
  if (!/^[0-9a-f]{32}$/.test(manifest.run_id || '')) {
    throw new Error(`Disposable database manifest has no valid run identity: ${manifestPath}`)
  }
  if (!Array.isArray(manifest.containers) || manifest.containers.length !== 2) {
    throw new Error(`Expected exactly two owned test containers, found ${manifest.containers?.length ?? 0}`)
  }

  const rows = manifest.containers.map(dockerInspect)
  for (const row of rows) {
    const name = row.Name?.replace(/^\//, '')
    if (row.Config?.Labels?.['dbcas.test-run'] !== manifest.run_id) {
      throw new Error(`Ownership label mismatch for ${name}; refusing to run mutating E2E`)
    }
    if (!row.State?.Running) throw new Error(`Owned test container ${name} is not running`)
    if (!String(row.HostConfig?.Tmpfs?.['/var/lib/postgresql/data'] ?? '').includes('rw')) {
      throw new Error(`Owned test container ${name} does not use tmpfs for PostgreSQL data`)
    }
    if ((row.Mounts || []).some((mount) => ['volume', 'bind'].includes(mount.Type))) {
      throw new Error(`Owned test container ${name} has an unexpected persistent mount`)
    }
  }

  const database = rows.find((row) => row.Config?.Image === 'postgres:17')
  const sandbox = rows.find((row) => row.Config?.Image === 'dbcas-sandbox-test')
  if (!database || !sandbox) throw new Error('The manifest does not identify the PostgreSQL and sandbox test containers')
  if (!(database.Config.Env || []).includes('POSTGRES_DB=dbcas_test')) {
    throw new Error('The disposable PostgreSQL container does not use the expected test database')
  }
  const databaseName = database.Name.replace(/^\//, '')

  const persistent = dockerInspect('dbcas-db')
  if (persistent.Config?.Labels?.['dbcas.test-run'] === manifest.run_id) {
    throw new Error('Persistent database container carries the disposable run identity')
  }
  if (!(persistent.Mounts || []).some((mount) => mount.Type === 'volume')) {
    throw new Error('The persistent development database was not found as a mounted, separate container')
  }

  const email = `isolation-${manifest.run_id}@test.dev`
  const password = 'IsolationProof123!'
  await api('/auth/register', {
    method: 'POST',
    body: { name: 'Disposable database proof', email, password, password_confirm: password },
  })
  const session = await api('/auth/login', { method: 'POST', body: { email, password } })
  const account = await api('/auth/me', { token: session.access_token })
  if (account.email !== email) throw new Error('The live API did not resolve the isolation probe account')

  const quoted = email.replaceAll("'", "''")
  const seededAdmin = Number(psqlScalar(databaseName, 'postgres', 'dbcas_test',
    "SELECT count(*) FROM account WHERE email = 'release-admin@test.dev'"))
  const probeInTest = Number(psqlScalar(databaseName, 'postgres', 'dbcas_test',
    `SELECT count(*) FROM account WHERE email = '${quoted}'`))
  const probeInPersistent = Number(psqlScalar('dbcas-db', 'dbcas', 'dbcas',
    `SELECT count(*) FROM account WHERE email = '${quoted}'`))
  const serverVersionRaw = psqlScalar(databaseName, 'postgres', 'dbcas_test',
    "SELECT current_setting('server_version_num')")
  const serverVersion = Number(serverVersionRaw)
  const apiConnections = Number(psqlScalar(databaseName, 'postgres', 'dbcas_test',
    "SELECT count(*) FROM pg_stat_activity WHERE datname = 'dbcas_test' AND pid <> pg_backend_pid()"))

  if (!(serverVersion >= 170000)) {
    throw new Error(`Disposable database ${databaseName} did not report PostgreSQL 17 (raw: ${JSON.stringify(serverVersionRaw)})`)
  }
  if (seededAdmin !== 1) throw new Error('The live API seed was not found inside the disposable database')
  if (probeInTest !== 1) throw new Error('The API probe account was not written to the disposable database')
  if (probeInPersistent !== 0) throw new Error('The API probe account leaked into the persistent development database')
  if (apiConnections < 1) throw new Error('No live API connection was observed on the disposable database')

  const proof = {
    verified_at: new Date().toISOString(),
    backend: 'http://127.0.0.1:8100',
    manifest: manifestPath,
    run_id: manifest.run_id,
    containers: {
      database: {
        name: databaseName,
        image: database.Config.Image,
        label: database.Config.Labels['dbcas.test-run'],
        tmpfs: database.HostConfig.Tmpfs,
        persistent_mounts: database.Mounts,
        postgres_version_num: serverVersion,
        api_connections: apiConnections,
      },
      sandbox: {
        name: sandbox.Name.replace(/^\//, ''),
        image: sandbox.Config.Image,
        label: sandbox.Config.Labels['dbcas.test-run'],
        tmpfs: sandbox.HostConfig.Tmpfs,
        persistent_mounts: sandbox.Mounts,
      },
    },
    checks: {
      seeded_admin_rows_in_disposable: seededAdmin,
      probe_email: email,
      probe_rows_in_disposable: probeInTest,
      probe_rows_in_persistent: probeInPersistent,
      persistent_container: persistent.Name.replace(/^\//, ''),
      persistent_is_separate: persistent.Config?.Labels?.['dbcas.test-run'] !== manifest.run_id,
    },
  }
  mkdirSync(reviewRoot, { recursive: true })
  const browser = process.env.DBCAS_BROWSER ?? 'chromium'
  writeFileSync(path.join(reviewRoot, `db-isolation-proof-${browser}.json`), `${JSON.stringify(proof, null, 2)}\n`)
  console.log(`Disposable database verified before mutating E2E (${databaseName}, run ${manifest.run_id}).`)
}
