import { t, useLocale } from '../i18n'
import SqlTableBuilder from './SqlTableBuilder'
import { btnGhost, inputCls } from './ui'

export default function SqlDatasetsEditor({ value, onChange }) {
  useLocale()
  let datasets
  try {
    datasets = JSON.parse(value || '[]')
    if (!Array.isArray(datasets)) throw new Error('invalid fixtures')
  } catch {
    return <label className="grid gap-2 text-sm text-danger">{t('admin.questions.sqlInvalidDatasets')}<textarea aria-label={t('admin.questions.datasets')} value={value} onChange={e => onChange(e.target.value)} className={inputCls} /></label>
  }
  const update = (index, patch) => onChange(JSON.stringify(datasets.map((item, i) => i === index ? { ...item, ...patch } : item)))
  return <div className="sql-fixtures-editor space-y-4">
    <p className="text-sm leading-relaxed text-sub">{t('admin.questions.sqlInputHelp')}</p>
    {datasets.map((dataset, index) => {
      const columns = dataset.expected_result?.columns || []
      const rows = dataset.expected_result?.rows
      const hasAnswer = Array.isArray(rows)
      return <section key={index} className="sql-fixture-panel rounded-xl border border-edge bg-panel p-4">
        <div className="mb-4 flex flex-wrap items-center justify-end gap-3">
          {datasets.length > 1 && <span className="mr-auto text-sm font-medium text-sub">{t('admin.questions.sqlDatasetName', { index: index + 1 })}</span>}
          <button type="button" className={`${btnGhost} text-danger`} onClick={() => onChange(JSON.stringify(datasets.filter((_, i) => i !== index)))}>{t('common.delete')}</button>
        </div>
        <SqlTableBuilder index={index + 1} value={dataset.setup_sql || ''} onChange={setup_sql => {
          if (setup_sql === dataset.setup_sql) return
          const { columns: oldColumns, rows: oldRows, ...options } = dataset.expected_result || {}
          update(index, { setup_sql, expected_result: options })
        }} />
        <p className={`mt-4 text-xs ${hasAnswer ? 'text-success' : 'text-sub'}`}>{t(hasAnswer ? 'admin.questions.sqlBaselineReady' : 'admin.questions.sqlBaselineMissing')}</p>
        <details className="mt-3 rounded-lg border border-edge p-3">
          <summary className="cursor-pointer text-xs font-semibold text-sub">{t('admin.questions.sqlBaselineDetails')}</summary>
          <p className="my-3 text-xs leading-relaxed text-sub">{t('admin.questions.sqlBaselineHelp')}</p>
          {hasAnswer && <div className="overflow-x-auto rounded-lg border border-edge"><table className="data-table"><thead><tr>{columns.map((column, c) => <th key={c} className="px-3 py-2">{column}</th>)}</tr></thead><tbody>{rows.map((row, r) => <tr key={r}>{row.map((cell, c) => <td key={c} className="px-3 py-2">{cell === null ? 'NULL' : String(cell)}</td>)}</tr>)}</tbody></table>{!rows.length && <p className="p-3 text-xs text-mute">{t('admin.questions.sqlPreviewEmpty')}</p>}</div>}

        </details>
      </section>
    })}
    <button type="button" className={btnGhost} onClick={() => {
      let suffix = datasets.length + 1
      while (datasets.some(dataset => dataset.dataset_name === `dataset_${suffix}`)) suffix++
      onChange(JSON.stringify([...datasets, { dataset_name: `dataset_${suffix}`, setup_sql: '', expected_result: {}, is_edge_case: false }]))
    }}>{t('admin.questions.sqlAddDataset')}</button>
  </div>
}
