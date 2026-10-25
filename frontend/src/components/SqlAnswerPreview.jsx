import { useEffect, useRef, useState } from 'react'
import api, { apiMessage } from '../api'
import { t, useLocale, resolveMessage, resources } from '../i18n'
import { ActionSpinner } from './States'
import { btnPrimary, Icon } from './ui'

export default function SqlAnswerPreview({ sql, setupSql, onUseResult, datasetControl, promptText = '' }) {
  useLocale()
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [applied, setApplied] = useState(false)
  const sequence = useRef(0)
  const running = useRef(false)
  useEffect(() => {
    sequence.current += 1
    running.current = false
    setResult(null)
    setError(null)
    setBusy(false)
    setApplied(false)
    return () => { sequence.current += 1 }
  }, [sql, setupSql, promptText])

  async function run() {
    if (running.current || !sql.trim() || !setupSql.trim() || !promptText.trim()) return
    running.current = true
    const request = ++sequence.current
    setBusy(true)
    setResult(null)
    setError(null)
    setApplied(false)
    try {
      const response = await api.post('/admin/sql/preview', { sql, setup_sql: setupSql })
      if (sequence.current === request) {
        setResult(response.data)
        if (response.data.success && onUseResult) {
          onUseResult({ columns: response.data.columns, rows: response.data.rows })
          setApplied(true)
        }
      }
    } catch (err) {
      if (sequence.current === request) setError(apiMessage(err))
    } finally {
      if (sequence.current === request) { running.current = false; setBusy(false) }
    }
  }

  const failure = result?.error_type
  const errorKey = Object.hasOwn(resources.en.translation.sql.errors, failure || '') ? `sql.errors.${failure}` : 'sql.executionError'
  return <div className="sql-answer-preview mt-3">
    {promptText && <div className="mb-3 rounded-lg border border-edge bg-elev p-3"><p className="mb-1 text-xs font-semibold text-sub">{t('admin.questions.sqlPromptContext')}</p><p className="whitespace-pre-wrap text-sm text-ink">{promptText}</p></div>}
    <div className="flex flex-wrap items-center justify-between gap-3">
      {datasetControl}
      <button type="button" onClick={run} disabled={busy || !sql.trim() || !setupSql.trim() || !promptText.trim()} className={btnPrimary}>
        {busy ? <ActionSpinner /> : <Icon name="play" className="h-4 w-4" />}{busy ? t('admin.questions.sqlPreviewRunning') : t('admin.questions.sqlPreviewRun')}
      </button>
    </div>
    {(!sql.trim() || !setupSql.trim() || !promptText.trim()) && <p className="mt-2 text-xs text-mute">{t('admin.questions.sqlPreviewRequired')}</p>}
    <div aria-live="polite" aria-busy={busy}>
      {error && <p role="alert" className="mt-3 text-sm text-danger">{resolveMessage(error)}</p>}
      {result && !result.success && <div role="alert" className="mt-3 rounded-lg border border-danger/30 bg-danger/5 p-3 text-sm text-danger"><p>{t(errorKey)}</p>{['syntax_error', 'schema_error'].includes(failure) && <pre className="mt-2 whitespace-pre-wrap break-words text-xs">{result.error_message}</pre>}</div>}
      {result?.success && <div className="mt-4">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2"><p className="text-xs font-semibold text-success">{t('admin.questions.sqlPreviewDone', { count: result.row_count, time: result.execution_time_ms })}</p>{applied && <span className="text-xs font-medium text-success">{t('admin.questions.sqlExpectedAuto')}</span>}</div>
        <div className="overflow-x-auto rounded-lg border border-edge bg-panel"><table className="data-table"><thead><tr>{result.columns.map((column, i) => <th key={i} className="px-3 py-2">{column}</th>)}</tr></thead><tbody>{result.rows.map((row, r) => <tr key={r}>{row.map((cell, c) => <td key={c} className="whitespace-pre-wrap break-words px-3 py-2">{cell === null ? <span className="text-mute">NULL</span> : typeof cell === 'object' ? JSON.stringify(cell) : String(cell)}</td>)}</tr>)}</tbody></table>{!result.rows.length && <p className="p-4 text-xs text-sub">{t('admin.questions.sqlPreviewEmpty')}</p>}</div>
      </div>}
    </div>
  </div>
}
