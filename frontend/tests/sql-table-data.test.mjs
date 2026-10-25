import { test } from 'node:test'
import assert from 'node:assert/strict'
import { buildSetup, sampleTables } from '../src/components/sqlTableData.js'

test('sample tables generate executable PostgreSQL with separate data scenarios', () => {
  const normal = buildSetup(sampleTables())
  assert.match(normal, /CREATE TABLE "students"/)
  assert.match(normal, /\('An', 9\)/)
  assert.doesNotMatch(buildSetup(sampleTables(true)), /'An'/)
})

test('string values escape apostrophes and cannot introduce statements', () => {
  const tables = sampleTables()
  tables[0].rows[0][0] = "O'Brien'; DROP TABLE account; --"
  assert.match(buildSetup(tables), /'O''Brien''; DROP TABLE account; --'/)
})

test('zero, FALSE, NULL and decimal values retain their SQL types', () => {
  assert.match(buildSetup([{ name: 'demo', columns: [
    { name: 'n', type: 'INTEGER' }, { name: 'flag', type: 'BOOLEAN' },
    { name: 'note', type: 'TEXT' }, { name: 'price', type: 'NUMERIC' },
  ], rows: [['0', 'false', '', '-2.5']] }]), /\(0, FALSE, NULL, -2.5\)/)
})

test('identifiers, numeric values and types cannot inject SQL', () => {
  for (const change of [
    t => { t[0].name = 'students; DROP TABLE account' },
    t => { t[0].columns[0].name = 'name;DROP' },
    t => { t[0].columns[0].type = 'TEXT); DROP TABLE account' },
    t => { t[0].rows[0][1] = '1); DROP TABLE account' },
    t => { t[0].name = 'pg_authid' },
  ]) {
    const tables = sampleTables()
    change(tables)
    assert.throws(() => buildSetup(tables))
  }
})

test('duplicate columns, duplicate tables and invalid dates are rejected', () => {
  assert.throws(() => buildSetup([...sampleTables(), ...sampleTables()]), /Duplicate/)
  const tables = sampleTables()
  tables[0].columns[1].name = 'NAME'
  assert.throws(() => buildSetup(tables), /Duplicate/)
  assert.throws(() => buildSetup([{ name: 'dates', columns: [{ name: 'day', type: 'DATE' }], rows: [['2026-02-30']] }]), /Date/)
})

test('empty tables keep their schema and UTF-8 setup size is bounded', () => {
  const tables = sampleTables()
  tables[0].rows = []
  assert.match(buildSetup(tables), /CREATE TABLE/)
  assert.doesNotMatch(buildSetup(tables), /INSERT/)
  tables[0].rows = [['a'.repeat(66000), '1']]
  assert.throws(() => buildSetup(tables), /Size/)
})
