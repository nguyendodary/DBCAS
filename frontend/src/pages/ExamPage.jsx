import LanguageSelector from '../components/LanguageSelector'
import ThemeSelector from '../components/ThemeSelector'
import { t, useLocale, message, resolveMessage, number, resources } from '../i18n'
import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import api, { apiMessage } from '../api'
import { ActionSpinner, EmptyState, ErrorState, Loading } from '../components/States'
import GradingStatusPanel from '../components/GradingStatusPanel'
import { ConfirmDialog, Icon, btnGhost, focusDialogTrigger } from '../components/ui'
import { useAnswerDraft } from '../useAnswerDraft'
import SqlEditor from '../components/SqlEditor'

function fmtClock(sec) {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

// The adaptive engine owns question order: the grid marks answered/served
// cells but — unlike the static prototype — cannot navigate backwards.
const SECTION_TYPES = [
  { type: 'mcq', icon: 'list', label: 'exam.mcqSection' },
  { type: 'sql', icon: 'code', label: 'exam.sqlSection' },
  { type: 'essay', icon: 'edit', label: 'exam.essaySection' },
]

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
  const [releaseChoice, setReleaseChoice] = useState('IMMEDIATE')
  const finishedRef = useRef(false)
  const autoFinishRef = useRef(false)
  const clock = useRef(null)
  const [warning, setWarning] = useState(null)
  const [selectedId, setSelectedId] = useState(null)
  const navigating = useRef(false)
  const free = state?.navigation_mode === 'FREE'
  const q = (free && state.questions?.find(item => item.question_id === selectedId)) || state?.current_question
  const currentNumber = q?.seq_no || state?.served_count
  const lastQuestion = currentNumber === state?.max_questions
  const answerLocked = free && Boolean(q?.submitted_at)
  const { draft, setDraft, flushDraft, saveStatus, saveError, saveConflict, reloadSavedDraft } = useAnswerDraft(sessionId, q)
  const hasAnswer = value => Object.values(value || {}).some(v => typeof v === 'string' ? v.trim() : Array.isArray(v) ? v.length : v)
  const answeredCount = free ? state.questions.filter(item => item.question_id === q?.question_id
    ? Boolean(draft.option || draft.options?.length || draft.sql.trim() || draft.essay.trim())
    : hasAnswer(item.draft)).length : state?.answered_count

  const acceptState = useCallback((next) => {
    const remainingMs = next.server_now && next.expires_at
      ? Math.max(0, Date.parse(next.expires_at) - Date.parse(next.server_now)) : next.remaining_seconds * 1000
    clock.current = { at: performance.now(), remainingMs }
    setState(next)
    setSecondsLeft(Math.max(0, Math.ceil(remainingMs / 1000)))
  }, [])

  const finish = useCallback(async (policy) => {
    if (finishedRef.current) return
    finishedRef.current = true
    setFinishing(true)
    setError(null)
    try {
      if (clock.current && clock.current.remainingMs - (performance.now() - clock.current.at) > 0) await flushDraft()
      if (policy) await api.post(`/sessions/${sessionId}/finish`, { result_release_policy: policy })
      else await api.post(`/sessions/${sessionId}/finish`)
      navigate(`/history/${sessionId}`, { replace: true })
    } catch (e) {
      // A connection can fail after the server commits the finish request.
      // Recover from the authoritative session state before offering a retry.
      try {
        const recovered = await api.get(`/sessions/${sessionId}`)
        acceptState(recovered.data)
        if (recovered.data.status !== 'in_progress') {
          navigate(`/history/${sessionId}`, { replace: true })
          return
        }
      } catch { /* keep the original failure visible; refresh can recover later */ }
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
      .then(async (r) => {
        if (r.data.status === 'in_progress' && r.data.navigation_mode === 'SEQUENTIAL') {
          r = await api.post(`/sessions/${sessionId}/navigation`)
        }
        acceptState(r.data)
        if (r.data.status !== 'in_progress') navigate(`/history/${sessionId}`, { replace: true })
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

  async function goToQuestion(id) {
    if (!free || !id || id === q?.question_id || navigating.current || finishedRef.current || running) return
    navigating.current = true
    setSubmitting(true)
    setError(null)
    try {
      await flushDraft()
      const result = await api.get(`/sessions/${sessionId}`)
      acceptState(result.data)
      setSelectedId(id)
      setRunResult(null)
    } catch (e) {
      setError(apiMessage(e, message('exam.submitError')))
    } finally {
      navigating.current = false
      setSubmitting(false)
    }
  }

  async function submit() {
    if (free) {
      const next = state.questions.find(item => item.seq_no === q.seq_no + 1)
      if (next) await goToQuestion(next.question_id)
      else setConfirmFinish(true)
      return
    }
    if (!q) return
    setSubmitting(true)
    setError(null)
    const payload = { question_id: q.question_id }
    if (q.question_type === 'mcq') {
      if (q.multiple_answers) payload.selected_option_ids = draft.options || []
      else payload.selected_option_id = draft.option
    }
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

  function resetDraft() {
    setDraft({ option: null, sql: '', essay: '' })
  }

  if (error && !state) return <div className="exam-shell"><div className="p-8"><ErrorState message={error} onRetry={load} /></div></div>
  if (!state) return <div className="exam-shell"><Loading label={t('exam.loading')} /></div>
  if (finishing) return <div className="exam-shell"><GradingStatusPanel status="submitting" /></div>

  const lowTime = secondsLeft !== null && secondsLeft <= 600
  const ended = secondsLeft !== null && secondsLeft <= 0
  const totalSec = state.started_at && state.expires_at
    ? Math.max(0, Math.round((Date.parse(state.expires_at) - Date.parse(state.started_at)) / 1000))
    : (secondsLeft ?? 0)
  const wordCount = draft.essay.trim() ? draft.essay.trim().split(/\s+/).length : 0
  const cells = Array.from({ length: state.max_questions || 0 }, (_, i) => i)
  const completion = state.max_questions ? Math.min(100, Math.round(answeredCount / state.max_questions * 100)) : 0

  return (
    <div className="exam-shell exam-modern">
      <header className="exam-header">
        <div className="header-inner">
          <div className="exam-identity">
            <button type="button" className="back-button" onClick={() => navigate('/assessments')}>
              <Icon name="arrowLeft" className="icon" />
              <span>{t('exam.back')}</span>
            </button>
            <span className="header-divider" aria-hidden="true" />
            <div className="exam-heading">
              <h1>{state.assessment_title}</h1>
              <p>{t('exam.progress', { current: number(currentNumber), max: number(state.max_questions), answered: number(answeredCount) })}</p>
            </div>
          </div>
          <div className="exam-controls">
            <LanguageSelector />
            <ThemeSelector />
            <div className={`timer-box${ended ? ' ended' : lowTime ? ' time-warning' : ''}`} aria-label={t('exam.timeRemaining')}>
              <Icon name="clock" className="icon timer-icon" />
              <div>
                <span className="timer-label">{ended ? t('exam.ended') : t('exam.timeRemaining')}</span>
                <div className="timer-value">
                  <strong>{secondsLeft === null ? '--:--' : fmtClock(Math.max(0, secondsLeft))}</strong>
                  {totalSec > 0 && <span>/ {fmtClock(totalSec)}</span>}
                </div>
              </div>
            </div>
            <button
              type="button"
              className="submit-button"
              disabled={finishing || submitting || ended}
              onClick={(event) => { focusDialogTrigger(event); setConfirmFinish(true) }}
            >
              {finishing ? <ActionSpinner /> : <Icon name="upload" className="icon" />}
              <span>{ended ? t('exam.ended') : t('exam.finish')}</span>
            </button>
          </div>
        </div>
      </header>

      <main className="exam-layout">
        <aside className="ex-sidebar">
          <section className="question-navigation" aria-label={t('exam.questionList')}>
            <div className="exam-progress-summary">
              <div className="exam-progress-ring" aria-hidden="true">
                <svg viewBox="0 0 80 80"><circle className="ring-track" cx="40" cy="40" r="33" /><circle className="ring-value" cx="40" cy="40" r="33" pathLength="100" strokeDasharray={`${completion} 100`} /></svg>
                <strong>{completion}%</strong>
              </div>
              <div><h2>{t('exam.progressTitle')}</h2><p>{t('exam.answeredOf', { answered: number(answeredCount), max: number(state.max_questions) })}</p></div>
            </div>
            <div className="navigation-heading">
              <span>{t('exam.questionList')}</span>
              <strong>{t('exam.answeredOf', { answered: number(answeredCount), max: number(state.max_questions) })}</strong>
            </div>
            <div className="ex-question-grid" role="list" aria-label={t('exam.questionList')}>
              {cells.map((i) => {
                const isActive = q && i === currentNumber - 1
                const item = state.questions?.[i]
                const isAnswered = free ? (isActive ? Boolean(draft.option || draft.options?.length || draft.sql.trim() || draft.essay.trim()) : Object.values(item?.draft || {}).some(value => typeof value === 'string' ? value.trim() : Array.isArray(value) ? value.length : value)) : i < state.answered_count
                return (
                  <div
                    key={i}
                    role="listitem"
                  >
                  <button type="button"
                    disabled={!free || submitting || finishing || running || ended}
                    onClick={() => goToQuestion(item?.question_id)}
                    aria-label={t('exam.goToQuestion', { number: i + 1 })}
                    className={`question-cell${isAnswered ? ' answered' : ''}${isActive ? ' active' : ''}`}
                    aria-current={isActive ? 'true' : undefined}
                  >
                    <span>{String(i + 1).padStart(2, '0')}</span>
                    <small aria-hidden="true">{isActive ? '●' : isAnswered ? '✓' : '–'}</small>
                  </button></div>
                )
              })}
            </div>
            <div className="exam-navigation-legend">
              <span><i className="answered" />{t('exam.legendAnswered')}</span>
              <span><i className="active" />{t('exam.legendCurrent')}</span>
              <span><i />{t('exam.legendUpcoming')}</span>
            </div>
          </section>

          {SECTION_TYPES.map(({ type, icon, label }) => (
            <button type="button" key={type} aria-label={t(label)} className={`section-link${q?.question_type === type ? ' live' : ''}`} aria-current={q?.question_type === type ? 'true' : undefined}
              disabled={!free || !state.questions?.some(item => item.question_type === type) || submitting || finishing || running || ended}
              onClick={() => goToQuestion(state.questions.find(item => item.question_type === type)?.question_id)}>
              <span className="section-name">
                <Icon name={icon} className="icon" />
                {t(label)}
              </span>
              <strong className="section-points">{t(`exam.type_${type}`)}</strong>
            </button>
          ))}

          <p className="sidebar-note">{t('exam.sectionNote')}</p>
        </aside>

        <section className={`question-panel question-panel--${q?.question_type || 'complete'}`} aria-labelledby="question-number">
          {warning && secondsLeft > 0 && (
            <p role="alert" className={`ex-banner mb-4${warning === 10 ? ' info' : ''}`} style={{ width: '100%', margin: '0 0 16px' }}>
              <Icon name="alert" className="icon" />
              {warning === 5 ? t('exam.warning5') : t('exam.warning10')}
            </p>
          )}
          {feedback && (
            <div role="status" className="ex-banner info" style={{ width: '100%', margin: '0 0 16px' }}>
              <Icon name={feedback.is_correct ? 'check' : 'info'} className="icon" />
              <span>{feedback.grading_status === 'pending' ? t('exam.pendingGrade') : feedback.grading_status === 'recovered' ? t('exam.recovered') : feedback.score == null && feedback.is_correct == null ? t('supervisor.answerSaved') : t('exam.feedback', { outcome: feedback.is_correct ? t('exam.correct') : t('exam.incorrect'), score: number(feedback.score, { minimumFractionDigits: 2 }), points: number(feedback.points_possible, { minimumFractionDigits: 2 }) })}</span>
            </div>
          )}
          {error && <ErrorState message={error} />}
          {saveError && <ErrorState message={saveError} onRetry={() => flushDraft().catch(() => {})} />}
          {saveConflict && <button type="button" className={btnGhost} onClick={() => reloadSavedDraft().catch(() => {})}>{t('exam.newerDraft')}</button>}

          {!q ? (
            <div className="all-served">
              <EmptyState title={t('exam.allServed')}>{t('exam.allServedBody')}</EmptyState>
              <button type="button" className="submit-button" onClick={(event) => { focusDialogTrigger(event); setConfirmFinish(true) }} disabled={finishing}>
                {finishing && <ActionSpinner />}{t('exam.finish')}
              </button>
            </div>
          ) : (
            <>
              <div className="question-top">
                <span className="question-type-icon" aria-hidden="true"><Icon name={q.question_type === 'sql' ? 'code' : q.question_type === 'essay' ? 'edit' : 'list'} className="icon" /></span>
                <h2 id="question-number">{t('exam.questionOf', { number: number(currentNumber), max: number(state.max_questions) })}</h2>
                <span className="question-score">{t('exam.points', { value: number(q.points) })}</span>
                <span className="question-score">{t('exam.difficulty', { value: number(q.difficulty_level) })}</span>
                <span className="question-score question-kind">{t(SECTION_TYPES.find(s => s.type === q.question_type)?.label || 'exam.mcqSection')}</span>
              </div>

              <div className="question-content">
                <h3 className="exam-content-label">{t('exam.promptHeading')}</h3>
                <p lang={q.content_locale || 'en'}>{q.prompt}</p>
                {q.question_type === 'sql' && q.schema_sql && (
                  <section className="exam-schema exam-dataset" aria-label={t('sql.providedData')}>
                    <h3 className="exam-dataset-title"><Icon name="database" className="icon" />{t('sql.providedData')}</h3>
                    <p className="exam-data-help">{t('sql.providedDataHelp')}</p>
                    {q.data_tables?.length > 0 && <div className="exam-data-tables">{q.data_tables.map(table => <section className="exam-data-table" key={table.name}>
                      <h4><Icon name="database" className="icon" />{table.name}<span>{t('sql.dataRows', { count: table.row_count })}</span></h4>
                      <div className="exam-data-scroll" tabIndex={0} role="region" aria-label={table.name}>
                        <table className="data-table"><thead><tr>{table.columns.map(column => <th key={column.name}>{column.name}<small>{column.type}</small></th>)}</tr></thead>
                          <tbody>{table.rows.map((row, i) => <tr key={i}>{row.map((cell, j) => <td key={j}>{cell === null ? <span className="text-mute">NULL</span> : String(cell)}</td>)}</tr>)}</tbody>
                        </table>
                        {!table.row_count && <p className="exam-data-help">{t('sql.emptyDataTable')}</p>}
                      </div>
                      {table.row_count > table.rows.length && <p className="exam-data-help">{t('sql.previewRows', { count: table.rows.length })}</p>}
                    </section>)}</div>}
                    <details className="exam-data-source" open={!q.data_tables?.length}>
                      <summary>{t('sql.viewSetup')}</summary>
                      <pre tabIndex={0} role="region" aria-label={t('sql.schema')}>{q.schema_sql}</pre>
                    </details>
                  </section>
                )}
                {q.concepts?.length > 0 && (
                  <div className="concept-row" aria-label={t('common.concepts')}>
                    {q.concepts.map((concept) => <span key={concept} className="concept-chip">{concept}</span>)}
                  </div>
                )}
              </div>

              {q.question_type === 'mcq' && (
                <fieldset lang={q.content_locale || 'en'} className="answers-fieldset" disabled={submitting || finishing || answerLocked}>
                  <legend>{t(q.multiple_answers ? 'exam.chooseMultipleLegend' : 'exam.chooseLegend')}</legend>
                  <div className="answer-list">
                    {q.options.map((option) => (
                      <label key={option.option_id} className="answer-option">
                        <input
                          type={q.multiple_answers ? 'checkbox' : 'radio'}
                          name={`answer-${q.question_id}`}
                          value={option.option_id}
                          checked={q.multiple_answers ? (draft.options || []).includes(option.option_id) : draft.option === option.option_id}
                          aria-label={`${option.option_label}: ${option.option_text}`}
                          onChange={() => setDraft(d => q.multiple_answers ? { ...d, options: (d.options || []).includes(option.option_id) ? d.options.filter(id => id !== option.option_id) : [...(d.options || []), option.option_id].sort((a, b) => a - b) } : { ...d, option: option.option_id })}
                        />
                        <span className="answer-body">
                          <span className="answer-heading">
                            <span className="answer-letter">{option.option_label}</span>
                            <span lang={q.content_locale || 'en'} className="answer-text">{option.option_text}</span>
                            <span className="selected-tag">{t('exam.selectedTag')}</span>
                          </span>
                        </span>
                      </label>
                    ))}
                  </div>
                </fieldset>
              )}

              {q.question_type === 'sql' && (
                <div className="sql-workspace">
                  <div className="ex-editor">
                    <div className="ex-editor-bar">
                      <span><Icon name="code" className="icon" />{t('essay.answer')} · SQL</span>
                    </div>
                    <SqlEditor value={draft.sql} onChange={(sql) => setDraft((d) => ({ ...d, sql }))} disabled={submitting || finishing || answerLocked} />
                  </div>
                  <div className="exam-run-actions">
                    <button type="button" className="action-button" onClick={runSql} disabled={running || submitting || finishing || ended || !draft.sql.trim()}>
                      {running ? <ActionSpinner /> : <Icon name="play" className="icon" />}
                      {running ? t('sql.running') : t('sql.run')}
                    </button>
                  </div>
                  <div className="ex-results" aria-live="polite">
                    <div className="ex-results-head">
                      <span>{t('sql.results')}</span>
                      {runResult?.success && <span>{t('sql.rowSummary', { count: runResult.row_count, time: number(runResult.execution_time_ms) })}</span>}
                    </div>
                    <div className="ex-results-body">
                      {running ? <p role="status" className="flex items-center gap-2"><ActionSpinner />{t('sql.runningQuery')}</p>
                        : runResult?.success ? <div tabIndex={0} role="region" aria-label={t('sql.resultTable')} className="max-h-72 overflow-auto">
                          {runResult.columns.length > 0 ? <table className="data-table"><thead><tr>{runResult.columns.map((column) => <th key={column}>{column}</th>)}</tr></thead><tbody>{runResult.rows.map((row, i) => <tr key={i}>{row.map((value, j) => <td key={j}>{String(value ?? 'NULL')}</td>)}</tr>)}</tbody></table> : <p>{t('sql.noColumns')}</p>}
                        </div>
                          : runResult ? <p role="alert" className="break-words leading-6 text-rose-200"><Icon name="alert" className="icon mr-1 inline-block align-middle" />{runResult.error_message?.translationKey ? resolveMessage(runResult.error_message) : t(Object.hasOwn(resources.en.translation.sql.errors, runResult.error_type || '') ? `sql.errors.${runResult.error_type}` : 'sql.executionError')}{['syntax_error', 'schema_error'].includes(runResult.error_type) && <code className="mt-2 block whitespace-pre-wrap text-xs">{runResult.error_message}</code>}</p>
                            : <p>{t('sql.runHint')}</p>}
                    </div>
                  </div>
                </div>
              )}

              {q.question_type === 'essay' && (
                <fieldset className="answers-fieldset essay-workspace" disabled={submitting || finishing || answerLocked}>
                  <div className="essay-toolbar">
                    <label htmlFor="essay-answer"><Icon name="edit" className="icon" />{t('essay.answer')}</label>
                    <span className="word-count">{t('essay.words', { count: wordCount })}</span>
                  </div>
                  <textarea id="essay-answer" className="ex-essay" value={draft.essay} onChange={(e) => setDraft((d) => ({ ...d, essay: e.target.value }))} maxLength={30000} rows={13} placeholder={t('essay.placeholder')} />
                </fieldset>
              )}

              {answerLocked && <p className="save-status">{t('exam.previouslySubmitted')}</p>}
              <p className="save-status" role="status" aria-live="polite">
                {saveStatus === 'saving' ? t('exam.draftSaving') : saveStatus === 'unsaved' ? t('exam.unsaved') : saveStatus === 'error' ? t('exam.draftFailed') : saveStatus === 'saved' ? t('exam.draftSaved') : '\u00A0'}
              </p>

              <div className="question-actions">
                <div className="right-actions">
                  {q.question_type !== 'mcq' && !answerLocked && <button type="button" className="action-button reset-button" disabled={submitting || finishing} onClick={resetDraft}>
                    <Icon name="reset" className="icon" />
                    {t('exam.resetAnswer')}
                  </button>}
                  {lastQuestion && !answerLocked && <button type="button" className="action-button" disabled={saveStatus === 'saving' || submitting || finishing} onClick={() => flushDraft().catch(() => {})}>
                    <Icon name="save" className="icon" />
                    {t('exam.saveDraft')}
                  </button>}
                  <button type="button" className="action-button next-button" disabled={submitting || finishing} onClick={submit}>
                    {submitting && <ActionSpinner />}
                    <span>{submitting ? t('exam.submitting') : free && lastQuestion ? t('exam.finish') : t('exam.nextQuestion')}</span>
                    <Icon name="arrowRight" className="icon" />
                  </button>
                </div>
              </div>
            </>
          )}
        </section>
      </main>

      <footer className="ex-footer">
        <div className="ex-footer-inner">
          <p>
            <strong>DBCAS</strong>
            <span>•</span>
            <span>{t('nav.footerTagline')}</span>
          </p>
          <p>{t('nav.copyright', { year: new Date().getFullYear() })}</p>
        </div>
      </footer>

      <ConfirmDialog open={confirmFinish} title={t('exam.finishTitle')} confirmLabel={finishing ? t('exam.finishing') : t('exam.confirmFinish')} onConfirm={() => finish(releaseChoice)} onCancel={() => setConfirmFinish(false)}>
        <p>{t('exam.finishBody', { count: answeredCount })}</p>
        <fieldset className="mt-4 space-y-3">
          <legend className="mb-2 text-sm font-semibold text-ink">{t('exam.releaseChoiceTitle')}</legend>
          {['IMMEDIATE', 'HUMAN_VERIFIED'].map(policy => <label key={policy} className={`flex cursor-pointer items-start gap-3 rounded-xl border p-3 ${releaseChoice === policy ? 'border-accent/40 bg-accent/5' : 'border-edge bg-panel'}`}>
            <input type="radio" name="result-release" value={policy} checked={releaseChoice === policy} onChange={() => setReleaseChoice(policy)} className="mt-1 h-4 w-4 shrink-0 accent-[var(--primary)]" />
            <span><span className="block text-sm font-medium text-ink">{t(`exam.release${policy}`)}</span><span className="mt-1 block text-xs leading-relaxed text-sub">{t(`exam.release${policy}Help`)}</span></span>
          </label>)}
        </fieldset>
        <p className="mt-3 text-xs text-sub">{t('exam.releaseTimeoutHelp')}</p>
      </ConfirmDialog>
    </div>
  )
}
