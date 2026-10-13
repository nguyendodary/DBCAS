import LanguageSelector from '../components/LanguageSelector'
import ThemeSelector from '../components/ThemeSelector'
import { t, useLocale, message, resolveMessage, number, resources } from '../i18n'
import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import api, { apiMessage } from '../api'
import { ActionSpinner, EmptyState, ErrorState, Loading } from '../components/States'
import { Badge, Card, ConfirmDialog, Icon, TypeBadge, btnGhost, btnPrimary, focusDialogTrigger } from '../components/ui'
import { useAnswerDraft } from '../useAnswerDraft'
import SqlEditor from '../components/SqlEditor'

function fmtClock(sec) {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

// The adaptive engine owns question order. Only the currently served question
// is visible; there is no fixed question navigator.
export default function ExamPage() {
  const { sessionId } = useParams()
  return <ExamWorkspace key={sessionId} sessionId={sessionId} />
}

function ExamWorkspace({ sessionId }) {
  useLocale()
  const navigate = useNavigate()
  const [state, setState] = useState(null)
  const [error, setError] = useState(null)
  const [secondsLeft, setSecondsLeft] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [finishing, setFinishing] = useState(false)
  const [feedback, setFeedback] = useState(null)
  const [runResult, setRunResult] = useState(null)
  const [running, setRunning] = useState(false)
  const [confirmFinish, setConfirmFinish] = useState(false)
  const finishedRef = useRef(false)
  const autoFinishRef = useRef(false)
  const clock = useRef(null)
  const [warning, setWarning] = useState(null)
  const q = state?.current_question
  const { draft, setDraft, flushDraft, saveStatus, saveError, saveConflict, reloadSavedDraft } = useAnswerDraft(sessionId, q)

  const acceptState = useCallback((next) => {
    const remainingMs = next.server_now && next.expires_at
      ? Math.max(0, Date.parse(next.expires_at) - Date.parse(next.server_now)) : next.remaining_seconds * 1000
    clock.current = { at: performance.now(), remainingMs }
    setState(next)
    setSecondsLeft(Math.max(0, Math.ceil(remainingMs / 1000)))
  }, [])

  const finish = useCallback(async () => {
    if (finishedRef.current) return
    finishedRef.current = true
    setFinishing(true)
    setError(null)
    try {
      if (clock.current && clock.current.remainingMs - (performance.now() - clock.current.at) > 0) await flushDraft()
      await api.post(`/sessions/${sessionId}/finish`)
      navigate('/dashboard', { replace: true })
    } catch (e) {
      finishedRef.current = false
      setConfirmFinish(false)
      setError(apiMessage(e, message('exam.finishError')))
    } finally {
      setFinishing(false)
    }
  }, [sessionId, navigate, flushDraft])

  const load = useCallback(() => {
    setError(null)
    api.get(`/sessions/${sessionId}`)
      .then((r) => {
        acceptState(r.data)
        if (r.data.status !== 'in_progress') navigate('/dashboard', { replace: true })
      })
      .catch((e) => setError(apiMessage(e, message('exam.loadError'))))
  }, [sessionId, navigate, acceptState])

  useEffect(load, [load])

  useEffect(() => {
    const tick = () => {
      if (!clock.current || state?.status !== 'in_progress') return
      const remaining = Math.max(0, clock.current.remainingMs - (performance.now() - clock.current.at))
      const seconds = Math.ceil(remaining / 1000)
      setSecondsLeft(seconds)
      const threshold = seconds > 0 && seconds <= 300 ? 5 : seconds > 0 && seconds <= 600 ? 10 : null
      if (threshold && !sessionStorage.getItem(`dbcas-time-warning:${sessionId}:${threshold}`)) {
        sessionStorage.setItem(`dbcas-time-warning:${sessionId}:${threshold}`, 'shown')
        setWarning(threshold)
      }
      if (remaining <= 0 && !autoFinishRef.current) { autoFinishRef.current = true; finish() }
    }
    const timer = setInterval(tick, 500)
    const onVisible = () => { if (document.visibilityState === 'visible') load() }
    document.addEventListener('visibilitychange', onVisible)
    return () => { clearInterval(timer); document.removeEventListener('visibilitychange', onVisible) }
  }, [state?.status, sessionId, finish, load])

  async function submit() {
    if (!q) return
    setSubmitting(true)
    setError(null)
    const payload = { question_id: q.question_id }
    if (q.question_type === 'mcq') payload.selected_option_id = draft.option
    if (q.question_type === 'sql') payload.sql_answer = draft.sql
    if (q.question_type === 'essay') payload.essay_answer = draft.essay
    try {
      await flushDraft()
      const result = await api.post(`/sessions/${sessionId}/submit`, payload)
      setFeedback(result.data.answer)
      acceptState(result.data.state)
      setRunResult(null)
    } catch (e) {
      setError(apiMessage(e, message('exam.submitError')))
      try {
        const recovered = await api.get(`/sessions/${sessionId}`)
        acceptState(recovered.data)
        if (recovered.data.answered_count > state.answered_count) {
          setError(null)
          setFeedback({ grading_status: 'recovered' })
        }
      } catch { /* the visible retry retains the durable server draft */ }
    } finally {
      setSubmitting(false)
    }
  }

  async function runSql() {
    if (!q || q.question_type !== 'sql' || !draft.sql.trim()) return
    setRunning(true)
    setRunResult(null)
    try {
      const result = await api.post(`/sessions/${sessionId}/sql-run`, {
        question_id: q.question_id,
        sql: draft.sql,
      })
      setRunResult(result.data)
    } catch (e) {
      setRunResult({ success: false, error_message: apiMessage(e) })
    } finally {
      setRunning(false)
    }
  }

  if (error && !state) return <ErrorState message={error} onRetry={load} />
  if (!state) return <Loading label={t('exam.loading')} />

  const answeredPct = state.max_questions > 0
    ? Math.min(100, Math.round((state.answered_count / state.max_questions) * 100)) : 0
  const lowTime = secondsLeft !== null && secondsLeft <= 600
  const criticalTime = secondsLeft !== null && secondsLeft <= 300
  const wordCount = draft.essay.trim() ? draft.essay.trim().split(/\s+/).length : 0

  return (
    <div className="space-y-5">
      <header className="exam-header sticky top-0 z-20 overflow-hidden rounded-xl border border-edge2 bg-panel">
        <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3.5 sm:px-6">
          <div className="min-w-0">
            <div className="flex items-center gap-2.5">
              <Icon name="database" className="hidden h-4 w-4 text-cyan-300 sm:block" />
              <h1 className="truncate text-sm font-semibold text-ink sm:text-base">{state.assessment_title}</h1>
              <Badge tone="blue">{t('exam.adaptive')}</Badge>
            </div>
            <p className="mt-1 text-xs text-mute">{t('exam.progress', { current: number(state.served_count), max: number(state.max_questions), answered: number(state.answered_count) })}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2 sm:gap-3"><LanguageSelector /><ThemeSelector />
            <div aria-label={t('exam.timeRemaining')} className={`flex items-center gap-2.5 rounded-lg border px-3 py-1.5 sm:px-3.5 ${lowTime ? 'border-rose-400/40 bg-rose-400/10' : 'border-edge2 bg-elev'}`}>
              <Icon name="clock" className={`h-4 w-4 ${lowTime ? 'text-rose-300' : 'text-cyan-300'}`} />
              <div>
                <span className={`block text-[9px] font-bold uppercase tracking-[.14em] ${lowTime ? 'text-rose-300' : 'text-mute'}`}>{t('exam.timeRemaining')}</span>
                <span className={`block font-mono text-sm font-bold tabular-nums leading-tight sm:text-base ${lowTime ? 'text-rose-200' : 'text-cyan-200'}`}>
                  {secondsLeft === null ? '--:--' : fmtClock(Math.max(0, secondsLeft))}
                </span>
              </div>
            </div>
            <button type="button" onClick={(event) => { focusDialogTrigger(event); setConfirmFinish(true) }} disabled={finishing || submitting} className={`${btnPrimary} whitespace-nowrap text-xs sm:text-sm`}>
              {finishing && <ActionSpinner />}{t('exam.finish')}</button>
          </div>
        </div>
        <div className="h-1 w-full bg-elev" role="progressbar" aria-label={t('exam.answered')} aria-valuemin={0} aria-valuemax={state.max_questions} aria-valuenow={state.answered_count}>
          <div className="h-full w-full origin-left bg-cyan-400 transition-transform duration-300" style={{ transform: `scaleX(${answeredPct / 100})` }} />
        </div>
      </header>

      {warning && secondsLeft > 0 && <p role="alert" className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-sm ${criticalTime ? 'border-rose-400/40 bg-rose-400/10 text-rose-200' : 'border-amber-400/30 bg-amber-400/10 text-amber-200'}`}>
        <Icon name="alert" className="h-4 w-4 shrink-0" />
        {warning === 5 ? t('exam.warning5') : t('exam.warning10')}
      </p>}
      {feedback && <div role="status" className={`flex items-center gap-2 rounded-lg border px-4 py-3 text-sm ${feedback.is_correct ? 'border-emerald-400/30 bg-emerald-400/10 text-emerald-200' : 'border-amber-400/30 bg-amber-400/10 text-amber-200'}`}>
        <Icon name={feedback.is_correct ? 'check' : 'info'} className="h-4 w-4 shrink-0" />
        <span>{feedback.grading_status === 'pending' ? t('exam.pendingGrade') : feedback.grading_status === 'recovered' ? t('exam.recovered') : t('exam.feedback', { outcome: feedback.is_correct ? t('exam.correct') : t('exam.incorrect'), score: number(feedback.score, { minimumFractionDigits: 2 }), points: number(feedback.points_possible, { minimumFractionDigits: 2 }) })}</span>
      </div>}
      {error && <ErrorState message={error} />}
      {saveError && <ErrorState message={saveError} onRetry={() => flushDraft().catch(() => {})} />}
      {saveConflict && <button type="button" className={btnGhost} onClick={() => reloadSavedDraft().catch(() => {})}>{t('exam.newerDraft')}</button>}

      {!q ? (
        <Card className="mx-auto max-w-2xl p-6 text-center sm:p-10">
          <EmptyState title={t('exam.allServed')}>{t('exam.allServedBody')}</EmptyState>
          <button type="button" onClick={(event) => { focusDialogTrigger(event); setConfirmFinish(true) }} disabled={finishing} className={`mt-5 ${btnPrimary}`}>
            {finishing && <ActionSpinner />}{t('exam.finish')}</button>
        </Card>
      ) : (
        <div className="grid min-w-0 items-start gap-5 lg:grid-cols-[minmax(0,.88fr)_minmax(0,1.12fr)]">
          <section tabIndex={0} aria-label={t('exam.question')} className="min-w-0 rounded-xl border border-edge bg-panel p-5 sm:p-6 lg:sticky lg:top-28 lg:max-h-[calc(100vh-8rem)] lg:overflow-y-auto">
            <p className="text-xs font-semibold uppercase tracking-[.14em] text-mute">{t('exam.questionNumber', { number: number(state.served_count) })}</p>
            <div className="mt-3 flex flex-wrap gap-2"><TypeBadge type={q.question_type} /><Badge>{t('exam.difficulty', { value: number(q.difficulty_level) })}</Badge><Badge>{t('exam.points', { value: number(q.points) })}</Badge></div>
            <p className="mt-6 whitespace-pre-wrap text-base font-medium leading-7 text-ink sm:text-lg">{q.prompt}</p>
            {q.concepts?.length > 0 && <div className="mt-6 border-t border-edge/70 pt-4">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-mute">{t('common.concepts')}</p>
              <div className="flex flex-wrap gap-1.5">{q.concepts.map((concept) => <Badge key={concept} tone="blue">{concept}</Badge>)}</div>
            </div>}
            {q.question_type === 'sql' && q.schema_sql && <div className="mt-6 border-t border-edge/70 pt-4">
              <h2 className="text-xs font-semibold uppercase tracking-wide text-mute">{t('sql.schema')}</h2>
              <pre tabIndex={0} role="region" aria-label={t('sql.schema')} className="mt-2 max-h-72 overflow-auto rounded-lg border border-edge bg-abyss/70 p-4 font-mono text-xs leading-5 text-sub">{q.schema_sql}</pre>
            </div>}
          </section>

          <section aria-label={t('exam.workspace')} className="min-w-0 overflow-hidden rounded-xl border border-edge bg-panel">
            <div className="flex items-center justify-between border-b border-edge/70 px-5 py-3.5 sm:px-6">
              <h2 className="text-sm font-semibold text-ink">{q.question_type === 'sql' ? t('sql.workspace') : q.question_type === 'essay' ? t('essay.workspace') : t('exam.choose')}</h2>
              {q.question_type === 'sql' && <span className="font-mono text-xs text-mute">PostgreSQL</span>}
            </div>

            {q.question_type === 'mcq' && <fieldset disabled={submitting || finishing} className="space-y-2.5 p-5 sm:p-6">
              <legend className="sr-only">{t('exam.choose')}</legend>
              {q.options.map((option) => {
                const selected = draft.option === option.option_id
                return <label key={option.option_id} className={`flex min-h-14 cursor-pointer items-center gap-3 rounded-lg border p-3.5 focus-within:outline focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-cyan-400 ${selected ? 'border-cyan-400/70 bg-cyan-400/10' : 'border-edge2 bg-abyss/35 hover:border-cyan-400/40 hover:bg-elev/60'}`}>
                  <input type="radio" name="mcq" aria-label={`${option.option_label}: ${option.option_text}`} value={option.option_id} checked={selected} onChange={() => setDraft((d) => ({ ...d, option: option.option_id }))} className="sr-only" />
                  <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-md font-mono text-xs font-semibold ${selected ? 'bg-cyan-400 text-primary-foreground' : 'border border-edge2 bg-elev text-sub'}`}>{option.option_label}</span>
                  <span className="flex-1 text-sm leading-relaxed text-ink">{option.option_text}</span>
                  {selected && <span className="ml-2 shrink-0 rounded bg-cyan-400/15 px-2 py-0.5 font-mono text-[10px] font-bold tracking-wider text-cyan-300">{t('exam.selectedTag')}</span>}
                </label>
              })}
            </fieldset>}

            {q.question_type === 'sql' && <div className="p-4 sm:p-5">
              <div className="overflow-hidden rounded-lg border border-editor-border bg-editor-bg focus-within:border-cyan-400/70 focus-within:ring-2 focus-within:ring-cyan-400/15">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-edge bg-elev/70 px-3 py-2">
                  <span className="flex items-center gap-2 font-mono text-xs text-sub"><Icon name="code" className="h-4 w-4 text-cyan-300" /> query.sql</span>
                  <button type="button" onClick={runSql} disabled={running || submitting || !draft.sql.trim()} className={`${btnGhost} py-1 text-xs`}>
                    {running ? <ActionSpinner /> : <Icon name="play" className="h-3.5 w-3.5" />}
                    {running ? t('sql.running') : t('sql.run')}
                  </button>
                </div>
                <SqlEditor value={draft.sql} onChange={(sql) => setDraft((d) => ({ ...d, sql }))} disabled={submitting || finishing} />
              </div>
              <div className="mt-4 overflow-hidden rounded-lg border border-edge bg-abyss/50" aria-live="polite">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-edge px-3 py-2"><h3 className="text-xs font-semibold uppercase tracking-wide text-sub">{t('sql.results')}</h3>{runResult?.success && <span className="text-xs tabular-nums text-mute">{t('sql.rowSummary', { count: runResult.row_count, time: number(runResult.execution_time_ms) })}</span>}</div>
                {running ? <p role="status" className="flex items-center gap-2 p-4 text-sm text-sub"><ActionSpinner />{t('sql.runningQuery')}</p>
                  : runResult?.success ? <div tabIndex={0} role="region" aria-label={t('sql.resultTable')} className="max-h-72 overflow-auto">
                    {runResult.columns.length > 0 ? <table className="data-table font-mono text-xs"><thead><tr>{runResult.columns.map((column) => <th key={column}>{column}</th>)}</tr></thead><tbody>{runResult.rows.map((row, i) => <tr key={i}>{row.map((value, j) => <td key={j}>{String(value ?? 'NULL')}</td>)}</tr>)}</tbody></table> : <p className="p-4 text-sm text-sub">{t('sql.noColumns')}</p>}
                  </div> : runResult ? <p role="alert" className="flex items-start gap-2 break-words p-4 text-sm leading-5 text-rose-200"><Icon name="alert" className="mt-0.5 h-4 w-4 shrink-0" /><span>{runResult.error_message?.translationKey ? resolveMessage(runResult.error_message) : t(Object.hasOwn(resources.en.translation.sql.errors, runResult.error_type || '') ? `sql.errors.${runResult.error_type}` : 'sql.executionError')}{['syntax_error', 'schema_error'].includes(runResult.error_type) && <code className="mt-2 block whitespace-pre-wrap text-xs">{runResult.error_message}</code>}</span></p>
                    : <p className="p-4 text-sm text-mute">{t('sql.runHint')}</p>}
              </div>
            </div>}

            {q.question_type === 'essay' && <div className="p-5 sm:p-6">
              <label htmlFor="essay-answer" className="mb-2 block text-sm font-medium text-sub">{t('essay.answer')}</label>
              <textarea id="essay-answer" value={draft.essay} onChange={(e) => setDraft((d) => ({ ...d, essay: e.target.value }))} disabled={submitting || finishing} maxLength={30000} rows={13} className="min-h-72 w-full resize-y rounded-lg border border-edge2 bg-abyss/60 p-4 text-sm leading-6 text-ink placeholder-faint focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/20" placeholder={t('essay.placeholder')} />
              <p className="mt-1 text-right text-xs tabular-nums text-mute">{t('essay.words', { count: wordCount })}</p>
            </div>}

            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-edge/70 bg-elev/20 px-5 py-4 sm:px-6">
              <div className="flex items-center gap-3"><p role="status" className="text-xs text-mute">{saveStatus === 'saving' ? t('exam.draftSaving') : saveStatus === 'unsaved' ? t('exam.unsaved') : saveStatus === 'error' ? t('exam.draftFailed') : t('exam.draftSaved')}</p><button type="button" className={btnGhost} onClick={() => flushDraft().catch(() => {})} disabled={saveStatus === 'saving' || submitting}>{t('exam.saveDraft')}</button></div>
              <button type="button" onClick={submit} disabled={submitting || finishing} className={btnPrimary}>
                {submitting && <ActionSpinner />}
                {submitting ? t('exam.submitting') : t('exam.submit')}
              </button>
            </div>
          </section>
        </div>
      )}

      <ConfirmDialog open={confirmFinish} title={t('exam.finishTitle')} confirmLabel={finishing ? t('exam.finishing') : t('exam.confirmFinish')} onConfirm={finish} onCancel={() => setConfirmFinish(false)}>
        {t('exam.finishBody', { count: state.answered_count })}
      </ConfirmDialog>
    </div>
  )
}
