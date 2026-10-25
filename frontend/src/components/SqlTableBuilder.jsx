import { useEffect, useRef, useState } from 'react'
import { t, useLocale } from '../i18n'
import SqlEditor from './SqlEditor'
import SqlLiveTablePreview from './SqlLiveTablePreview'
import { btnGhost, inputCls } from './SharedComponents'
import { buildSetup, sampleTables, TABLE_TYPES } from './sqlTableData'

function knownSample(value) {
  for (const empty of [false, true]) {
    const tables = sampleTables(empty)
    if (buildSetup(tables) === value) return tables
  }
  return []
}

export default function SqlTableBuilder({ value, onChange, index }) {
  useLocale()
  const [tables, setTables] = useState(() => knownSample(value))
  const [mode, setMode] = useState(() => !value.trim() || knownSample(value).length ? 'builder' : 'sql')
  const [error, setError] = useState('')
  const lastValue = useRef(value)
  useEffect(() => {
    if (value !== lastValue.current) {
      lastValue.current = value
      const sample = knownSample(value)
      setTables(sample)
      setError('')
      setMode(!value.trim() || sample.length ? 'builder' : 'sql')
    }
  }, [value])
  function commit(sql) { lastValue.current = sql; onChange(sql) }
  function change(next) {
    setTables(next)
    try { commit(buildSetup(next)); setError('') }
    catch (err) { setError(err.message); commit('') }
  }
  const tableChange = (i, patch) => change(tables.map((table, ti) => ti === i ? { ...table, ...patch } : table))
  function emptyTable() {
    const used = new Set(tables.map(table => table.name.toLowerCase()))
    let number = 1
    while (used.has(`table_${number}`)) number += 1
    change([...tables, { name: `table_${number}`, columns: [{ name: 'id', type: 'INTEGER' }], rows: [] }])
  }
  return <div className="sql-table-builder space-y-3">
    <div className="flex flex-wrap items-center justify-between gap-2">
      <p className="text-xs leading-relaxed text-sub">{t('admin.questions.sqlBuilderHelp')}</p>
      <button type="button" className={btnGhost} onClick={() => setMode(mode === 'sql' ? 'builder' : 'sql')}>{t(mode === 'sql' ? 'admin.questions.sqlBuilderSwitch' : 'admin.questions.sqlManualSwitch')}</button>
    </div>
    {mode === 'sql' ? <div className="sql-admin-editor"><div className="sql-admin-toolbar"><span>setup.sql</span><span>PostgreSQL</span></div><SqlEditor compact rows={6} maxLength={65536} label={t('admin.questions.sqlSetupLabel', { index })} value={value} onChange={sql => { setTables([]); setError(''); onChange(sql) }} /></div> : <>
      {!tables.length && <div className="rounded-lg border border-dashed border-edge2 bg-elev p-4">
        <p className="mb-3 text-xs text-sub">{t(value.trim() ? 'admin.questions.sqlBuilderReplace' : 'admin.questions.sqlBuilderStart')}</p>
        <button type="button" className={btnGhost} onClick={emptyTable}>{t('admin.questions.sqlCreateEmptyTable')}</button>
      </div>}
      {tables.map((table, ti) => <div className="rounded-lg border border-edge bg-panel p-3" key={ti}>
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <label className="flex min-w-0 flex-wrap items-center gap-2 text-xs font-semibold text-sub">{t('admin.questions.sqlTableName')}<input required value={table.name} aria-label={t('admin.questions.sqlTableLabel', { index: ti + 1 })} onChange={e => tableChange(ti, { name: e.target.value })} className={`${inputCls} min-w-0`} /></label>
          <button type="button" className={`${btnGhost} text-danger`} onClick={() => change(tables.filter((_, i) => i !== ti))}>{t('admin.questions.sqlRemoveTable')}</button>
        </div>
        <div className="overflow-x-auto rounded-lg border border-edge"><table className="data-table sql-builder-table"><thead><tr>{table.columns.map((column, ci) => <th key={ci}><div className="grid gap-2">
          <div className="flex items-center gap-1"><input required value={column.name} aria-label={t('admin.questions.sqlColumnName', { index: ci + 1 })} className={`${inputCls} min-w-0 w-full`} onChange={e => tableChange(ti, { columns: table.columns.map((c, i) => i === ci ? { ...c, name: e.target.value } : c) })} /><button type="button" disabled={table.columns.length === 1} aria-label={t('admin.questions.sqlRemoveColumn', { index: ci + 1 })} className="p-1 text-mute disabled:opacity-30" onClick={() => tableChange(ti, { columns: table.columns.filter((_, i) => i !== ci), rows: table.rows.map(row => row.filter((_, i) => i !== ci)) })}>&times;</button></div>
          <select aria-label={t('admin.questions.sqlColumnType', { index: ci + 1 })} className={inputCls} value={column.type} onChange={e => tableChange(ti, { columns: table.columns.map((c, i) => i === ci ? { ...c, type: e.target.value } : c) })}>{TABLE_TYPES.map(type => <option value={type} key={type}>{t(`admin.questions.sqlDataType${type}`)}</option>)}</select>
        </div></th>)}<th /></tr></thead><tbody>{table.rows.map((row, ri) => <tr key={ri}>{table.columns.map((column, ci) => <td key={ci}>{column.type === 'BOOLEAN' ? <select className={inputCls} aria-label={t('admin.questions.sqlCell', { row: ri + 1, column: ci + 1 })} value={row[ci]} onChange={e => tableChange(ti, { rows: table.rows.map((r, i) => i === ri ? r.map((cell, j) => j === ci ? e.target.value : cell) : r) })}><option value="">NULL</option><option value="true">TRUE</option><option value="false">FALSE</option></select> : <input aria-label={t('admin.questions.sqlCell', { row: ri + 1, column: ci + 1 })} placeholder="NULL" type={column.type === 'DATE' ? 'date' : 'text'} inputMode={['INTEGER', 'NUMERIC'].includes(column.type) ? 'decimal' : undefined} value={row[ci]} className={`${inputCls} w-full min-w-0`} onChange={e => tableChange(ti, { rows: table.rows.map((r, i) => i === ri ? r.map((cell, j) => j === ci ? e.target.value : cell) : r) })} />}</td>)}<td><button type="button" aria-label={t('admin.questions.sqlRemoveRow', { index: ri + 1 })} className="p-2 text-mute" onClick={() => tableChange(ti, { rows: table.rows.filter((_, i) => i !== ri) })}>&times;</button></td></tr>)}</tbody></table></div>
        {!table.rows.length && <p className="mt-2 text-xs text-mute">{t('admin.questions.sqlNoInputRows')}</p>}
        <div className="mt-3 flex flex-wrap gap-2"><button type="button" className={btnGhost} onClick={() => tableChange(ti, { rows: [...table.rows, table.columns.map(() => '')] })}>{t('admin.questions.sqlAddRow')}</button><button type="button" className={btnGhost} onClick={() => tableChange(ti, { columns: [...table.columns, { name: `column_${table.columns.length + 1}`, type: 'TEXT' }], rows: table.rows.map(row => [...row, '']) })}>{t('admin.questions.sqlAddColumn')}</button></div>
      </div>)}
      {!!tables.length && <button type="button" className={btnGhost} onClick={emptyTable}>{t('admin.questions.sqlAddTable')}</button>}
      <SqlLiveTablePreview tables={tables} />
      {error && <p role="alert" className="text-xs text-danger">{t(`admin.questions.${error}`)}</p>}
      {!!tables.length && !error && <p className="text-xs text-sub">{t('admin.questions.sqlBuilderAuto')}</p>}
      {!!tables.length && <details className="rounded-lg border border-edge p-3"><summary className="cursor-pointer text-xs text-sub">{t('admin.questions.sqlViewGenerated')}</summary><pre className="mt-3 max-h-64 overflow-auto whitespace-pre text-xs text-ink">{value}</pre></details>}
    </>}
  </div>
}
