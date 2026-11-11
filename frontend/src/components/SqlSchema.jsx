import { useMemo } from 'react'
import { t, useLocale } from '../i18n'

// The bank stores one self-contained PostgreSQL dataset per SQL question.
// Render it as scannable table cards instead of a wrapped DDL blob.
function splitTopLevel(text, separator = ',') {
  const parts = []
  let current = ''
  let depth = 0
  let quote = null
  for (let i = 0; i < text.length; i += 1) {
    const char = text[i]
    if (quote) {
      current += char
      if (char === quote) {
        if (text[i + 1] === quote) {
          current += text[i + 1]
          i += 1
        } else quote = null
      }
      continue
    }
    if (char === "'" || char === '"') {
      quote = char
      current += char
      continue
    }
    if (char === '(') depth += 1
    if (char === ')') depth -= 1
    if (char === separator && depth === 0) {
      parts.push(current.trim())
      current = ''
      continue
    }
    current += char
  }
  if (current.trim()) parts.push(current.trim())
  return parts
}

function splitStatements(sql) {
  const statements = []
  let current = ''
  let quote = null
  for (let i = 0; i < sql.length; i += 1) {
    const char = sql[i]
    current += char
    if (quote) {
      if (char === quote) {
        if (sql[i + 1] === quote) {
          current += sql[i + 1]
          i += 1
        } else quote = null
      }
      continue
    }
    if (char === "'" || char === '"') {
      quote = char
      continue
    }
    if (char === ';') {
      if (current.trim()) statements.push(current.trim().replace(/;$/, ''))
      current = ''
    }
  }
  if (current.trim()) statements.push(current.trim().replace(/;$/, ''))
  return statements
}

function parseColumn(definition) {
  const match = /^\s*"?([\w$]+)"?\s+([\s\S]+)$/.exec(definition)
  if (!match) return null
  const type = match[2]
    .split(
      /\s+(?:PRIMARY\s+KEY|NOT\s+NULL|NULL|UNIQUE|DEFAULT|REFERENCES|CHECK|GENERATED|COLLATE)\b/i,
    )[0]
    .trim()
  return { name: match[1], type: type || 'text' }
}

function unquote(value) {
  const trimmed = value.trim()
  if (/^'(?:''|[^'])*'$/.test(trimmed)) return trimmed.slice(1, -1).replaceAll("''", "'")
  if (trimmed === 'NULL') return 'NULL'
  return trimmed
}

export function parseSqlSchema(schema) {
  const tables = new Map()
  for (const statement of splitStatements(schema || '')) {
    const create = /^CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?"?([\w$]+)"?\s*\(([\s\S]*)\)$/i.exec(
      statement,
    )
    if (create) {
      const columns = splitTopLevel(create[2]).map(parseColumn).filter(Boolean)
      tables.set(create[1], { name: create[1], columns, rows: [] })
      continue
    }
    const insert = /^INSERT\s+INTO\s+"?([\w$]+)"?\s+VALUES\s+([\s\S]+)$/i.exec(statement)
    if (!insert) continue
    const table = tables.get(insert[1])
    if (!table) continue
    for (const tuple of splitTopLevel(insert[2])) {
      if (!tuple.startsWith('(') || !tuple.endsWith(')')) continue
      const values = splitTopLevel(tuple.slice(1, -1)).map(unquote)
      if (values.length) table.rows.push(values)
    }
  }
  return [...tables.values()]
}

function SchemaTable({ table }) {
  const preview = table.rows.slice(0, 4)
  return (
    <details className="sql-schema-table" open>
      <summary title={table.name}>
        <code className="sql-schema-name">{table.name}</code>
        <span className="sql-schema-meta">
          {t('sql.tableSummary', { columns: table.columns.length, rows: table.rows.length })}
        </span>
      </summary>
      <div className="sql-schema-body">
        <div className="sql-schema-columns" role="table" aria-label={table.name}>
          <div className="sql-schema-columns-head" role="row">
            <span role="columnheader">{t('common.name')}</span>
            <span role="columnheader">{t('common.type')}</span>
          </div>
          {table.columns.map((column) => (
            <div className="sql-schema-column" role="row" key={column.name}>
              <code role="cell" title={column.name}>
                {column.name}
              </code>
              <span role="cell" title={column.type}>
                {column.type}
              </span>
            </div>
          ))}
        </div>
        {preview.length > 0 && (
          <div
            className="sql-schema-rows"
            tabIndex={0}
            role="region"
            aria-label={t('sql.sampleRows')}
          >
            <table className="data-table">
              <thead>
                <tr>
                  {table.columns.map((column) => (
                    <th key={column.name} title={column.name}>
                      {column.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.map((row, index) => (
                  <tr key={index}>
                    {table.columns.map((column, columnIndex) => {
                      const value = row[columnIndex]
                      return (
                        <td key={column.name} title={value ?? ''}>
                          {value === undefined || value === '' ? 'NULL' : value}
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </details>
  )
}

export default function SqlSchema({ schema }) {
  useLocale()
  const tables = useMemo(() => parseSqlSchema(schema), [schema])
  if (!schema) return null
  return (
    <section className="sql-schema" aria-label={t('sql.schema')}>
      <div className="sql-schema-heading">
        <h3>{t('sql.schema')}</h3>
        <span>{t('sql.schemaHint')}</span>
      </div>
      {tables.length > 0 ? (
        tables.map((table) => <SchemaTable key={table.name} table={table} />)
      ) : (
        <pre className="sql-schema-raw" tabIndex={0} role="region" aria-label={t('sql.schema')}>
          {schema}
        </pre>
      )}
    </section>
  )
}
