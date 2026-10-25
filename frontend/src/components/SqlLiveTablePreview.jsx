import { t, useLocale } from '../i18n'

export default function SqlLiveTablePreview({ tables }) {
  useLocale()
  if (!tables.length) return null
  return <aside className="sql-live-table-preview rounded-xl border border-edge bg-elev p-4" aria-label={t('admin.questions.sqlLivePreview')}>
    <h4 className="text-sm font-semibold text-ink">{t('admin.questions.sqlLivePreview')}</h4>
    <p className="mb-3 mt-1 text-xs text-sub">{t('admin.questions.sqlLivePreviewHelp')}</p>
    <div className="space-y-4">{tables.map((table, ti) => <section className="min-w-0" key={ti}>
      <p className="mb-2 text-sm font-semibold text-accent">{table.name || t('admin.questions.sqlUnnamedTable')}</p>
      <div className="overflow-x-auto rounded-lg border border-edge bg-panel"><table className="data-table sql-live-data"><thead><tr>{table.columns.map((column, ci) => <th key={ci}>{column.name || t('admin.questions.sqlUnnamedColumn')}</th>)}</tr></thead><tbody>{table.rows.map((row, ri) => <tr key={ri}>{table.columns.map((_, ci) => <td key={ci}>{row[ci] === '' || row[ci] == null ? <span className="text-mute">NULL</span> : row[ci]}</td>)}</tr>)}</tbody></table>{!table.rows.length && <p className="p-3 text-xs text-mute">{t('admin.questions.sqlLiveNoRows')}</p>}</div>
    </section>)}</div>
  </aside>
}
