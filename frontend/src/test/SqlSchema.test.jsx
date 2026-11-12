import { describe, expect, it } from 'vitest'
import { parseSqlSchema } from '../components/SqlSchema'

const SCHEMA = `CREATE TABLE cases(id integer PRIMARY KEY,grp text,n numeric,b numeric,txt text,flag boolean,doc jsonb,arr integer[],day date); INSERT INTO cases VALUES (1,'A',30,2,'beta',true,'{"score": 30, "nullable": true}','{2,1}','2026-11-01'),(2,'A',10,0,'alpha',false,'{"nullable": false}','{3,2}','2026-03-29'),(3,'B',30,NULL,'beta',true,'{"score": null}','{}','2026-11-01');`

describe('parseSqlSchema', () => {
  it('parses a bank table and its sample rows once', () => {
    const tables = parseSqlSchema(SCHEMA)
    expect(tables).toHaveLength(1)
    expect(tables[0].name).toBe('cases')
    expect(tables[0].columns).toHaveLength(9)
    expect(tables[0].columns[0]).toEqual({ name: 'id', type: 'integer' })
    expect(tables[0].columns[6]).toEqual({ name: 'doc', type: 'jsonb' })
    expect(tables[0].rows).toHaveLength(3)
    expect(tables[0].rows[2]).toEqual([
      '3',
      'B',
      '30',
      'NULL',
      'beta',
      'true',
      '{"score": null}',
      '{}',
      '2026-11-01',
    ])
  })

  it('keeps commas inside types and quoted values', () => {
    const tables = parseSqlSchema(
      "CREATE TABLE t(id numeric(5,2), note text, tags text[]); INSERT INTO t VALUES (1.5, 'a,b', '{x,y}');",
    )
    expect(tables[0].columns[0]).toEqual({ name: 'id', type: 'numeric(5,2)' })
    expect(tables[0].rows[0]).toEqual(['1.5', 'a,b', '{x,y}'])
  })

  it('returns no tables for a DDL variant it cannot structure', () => {
    expect(parseSqlSchema('ALTER TABLE cases ADD COLUMN ok boolean;')).toEqual([])
  })
})
