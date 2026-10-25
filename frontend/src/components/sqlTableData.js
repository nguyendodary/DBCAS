export const TABLE_TYPES = ['TEXT', 'INTEGER', 'NUMERIC', 'BOOLEAN', 'DATE']
export const SAMPLE_SQL = 'SELECT name\nFROM students\nWHERE score >= 8;'

export function sampleTables(emptyResult = false) {
  return [{ name: 'students', columns: [{ name: 'name', type: 'TEXT' }, { name: 'score', type: 'INTEGER' }], rows: emptyResult ? [['Binh', '6']] : [['An', '9'], ['Binh', '6']] }]
}

function identifier(value) {
  const name = value.trim()
  if (!/^[A-Za-z_][A-Za-z0-9_]{0,62}$/.test(name) || /^(pg_|sql_)/i.test(name)) throw new Error('sqlBuilderIdentifier')
  return `"${name}"`
}

function literal(value, type) {
  if (value === '') return 'NULL'
  if (type === 'INTEGER' || type === 'NUMERIC') {
    const pattern = type === 'INTEGER' ? /^-?\d+$/ : /^-?\d+(?:\.\d+)?$/
    if (!pattern.test(value)) throw new Error('sqlBuilderNumber')
    return value
  }
  if (type === 'BOOLEAN') {
    if (!['true', 'false'].includes(value)) throw new Error('sqlBuilderBoolean')
    return value.toUpperCase()
  }
  if (type === 'DATE' && (!/^\d{4}-\d{2}-\d{2}$/.test(value) || !Number.isFinite(Date.parse(value)) || new Date(value).toISOString().slice(0, 10) !== value)) throw new Error('sqlBuilderDate')
  return `'${value.replace(/'/g, "''")}'`
}

export function buildSetup(tables) {
  if (!tables.length) return ''
  const names = new Set()
  const statements = []
  for (const table of tables) {
    const name = identifier(table.name)
    if (names.has(table.name.trim().toLowerCase()) || !table.columns.length) throw new Error('sqlBuilderDuplicate')
    names.add(table.name.trim().toLowerCase())
    const columnNames = new Set()
    const definitions = table.columns.map(column => {
      const columnName = identifier(column.name)
      if (columnNames.has(column.name.trim().toLowerCase())) throw new Error('sqlBuilderDuplicate')
      columnNames.add(column.name.trim().toLowerCase())
      if (!TABLE_TYPES.includes(column.type)) throw new Error('sqlBuilderType')
      return `  ${columnName} ${column.type}`
    })
    statements.push(`CREATE TABLE ${name} (\n${definitions.join(',\n')}\n);`)
    if (table.rows.length) {
      const values = table.rows.map(row => {
        if (row.length !== table.columns.length) throw new Error('sqlBuilderDuplicate')
        return `  (${row.map((cell, index) => literal(cell, table.columns[index].type)).join(', ')})`
      })
      statements.push(`INSERT INTO ${name} VALUES\n${values.join(',\n')};`)
    }
  }
  const sql = statements.join('\n\n')
  if (statements.length > 64 || new TextEncoder().encode(sql).length > 65536) throw new Error('sqlBuilderSize')
  return sql
}
