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

// The engine owns delivery order. Already delivered answers can be revisited
// read-only while the current draft and the authoritative clock stay mounted.
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
  const { locale } = useLocale()
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
  const [displayError, setDisplayError] = useState(false)
  const [displayRetry, setDisplayRetry] = useState(0)
  const [reviewSeq, setReviewSeq] = useState(null)
  const [reviewQuestion, setReviewQuestion] = useState(null)
  const [reviewError, setReviewError] = useState(null)
  const [reviewRetry, setReviewRetry] = useState(0)
  const browseSequence = useRef(0)
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
      .then((r) => {
        acceptState(r.data)
        if (r.data.status !== 'in_progress') navigate(`/history/${sessionId}`, { replace: true })
      })
      .catch((e) => setError(apiMessage(e, message('exam.loadError'))))
  }, [sessionId, navigate, acceptState])

  useEffect(load, [load])

  useEffect(() => {
    if (reviewSeq === null) return
    let active = true
    setReviewQuestion(null)
    setReviewError(null)
    api.get(`/sessions/${sessionId}/questions`, { params: { display_locale: locale } })
      .then(({ data }) => {
        if (active) {
          const question = data.find(item => item.seq_no === reviewSeq)
          if (!question) throw new Error(message('exam.loadError'))
          setReviewQuestion(question)
        }
      })
      .catch(error => { if (active) setReviewError(apiMessage(error, message('exam.loadError'))) })
    return () => { active = false }
  }, [sessionId, reviewSeq, locale, reviewRetry])

  async function browseQuestion(seq) {
    const sequence = ++browseSequence.current
    if (q?.seq_no === seq) { setReviewSeq(null); return }
    try {
      await flushDraft()
      if (sequence === browseSequence.current) setReviewSeq(seq)
    } catch { /* keep the editable answer visible until its draft is safe */ }
  }

  // Display only reviewed content captured when this question was served.
  // Do not reset the answer draft, clock, session locale or grading evidence.
  useEffect(() => {
    setDisplayError(false)
    if (!q?.question_id || locale === (q._displayLocale || state.locale || 'en')) return
    let active = true
    const questionId = q.question_id
    api.get(`/sessions/${sessionId}`, { params: { display_locale: locale } })
      .then(({ data }) => {
        if (!active || data.current_question?.question_id !== questionId) return
        setState(previous => previous?.current_question?.question_id === questionId
          ? { ...previous, current_question: { ...data.current_question, _displayLocale: locale } } : previous)
      })
      .catch(() => { if (active) setDisplayError(true) })
    return () => { active = false }
  }, [sessionId, q, locale, displayRetry])

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
    tick()
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

  return (
    <div className="exam-shell">
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
              <p>{t('exam.progress', { current: number(state.served_count), max: number(state.max_questions), answered: number(state.answered_count) })}</p>
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
            <div className="section-heading">
              <h2 className="section-title">
                <Icon name={q?.question_type === 'sql' ? 'code' : q?.question_type === 'essay' ? 'edit' : 'list'} className="icon" />
                {t(SECTION_TYPES.find((s) => s.type === q?.question_type)?.label ?? 'exam.mcqSection')}
              </h2>
              <span className="doing-badge">{ended ? t('exam.ended') : t('exam.doingBadge')}</span>
            </div>
            <div className="navigation-heading">
              <span>{t('exam.questionList')}</span>
              <strong>{t('exam.answeredOf', { answered: number(state.answered_count), max: number(state.max_questions) })}</strong>
            </div>
            <div className="ex-question-grid" role="list" aria-label={t('exam.questionList')}>
              {cells.map((i) => {
                const isActive = reviewSeq !== null ? i === reviewSeq - 1 : q && i === state.served_count - 1
                const isAnswered = i < state.answered_count
                return (
                  <div
                    key={i}
                    role="listitem"
                  >
                    <button type="button" className={`question-cell w-full${isAnswered ? ' answered' : ''}${isActive ? ' active' : ''}`} disabled={i >= state.served_count || submitting || finishing} onClick={() => browseQuestion(i + 1)} aria-label={t('exam.navigateQuestion', { number: i + 1 })} aria-current={isActive ? 'step' : undefined}>
                    <span>{String(i + 1).padStart(2, '0')}</span>
                    <small>{isActive ? t('exam.doingBadge') : isAnswered ? '✓' : '–'}</small>
                    </button>
                  </div>
                )
              })}
            </div>
            <p className="navigation-note">{t('exam.gridNote')}</p>
          </section>

          {SECTION_TYPES.map(({ type, icon, label }) => (
            <div key={type} className={`section-link${q?.question_type === type ? ' live' : ''}`} aria-current={q?.question_type === type ? 'true' : undefined}>
              <span className="section-name">
                <Icon name={icon} className="icon" />
                {t(label)}
              </span>
              {q?.question_type === type && <span className="saved-count">{t('exam.doingBadge')}</span>}
              <strong className="section-points">{t(`exam.type_${type}`)}</strong>
            </div>
          ))}

          <p className="sidebar-note">{t('exam.sectionNote')}</p>
        </aside>

        <section className="question-panel" aria-label={!q && reviewSeq === null ? t('exam.questionList') : undefined} aria-labelledby={reviewSeq !== null ? 'review-question-number' : q ? 'question-number' : undefined}>
          {reviewSeq !== null && <div>
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <h2 id="review-question-number" className="text-lg font-semibold text-ink">{t('exam.questionOf', { number: number(reviewSeq), max: number(state.max_questions) })}</h2>
              <button type="button" className={btnGhost} onClick={() => { browseSequence.current += 1; setReviewSeq(null) }}>{t('exam.returnCurrent')}</button>
            </div>
            <p className="mb-4 text-sm text-sub">{t('exam.savedAnswerReview')}</p>
            {reviewError ? <ErrorState message={reviewError} onRetry={() => setReviewRetry(value => value + 1)} /> : !reviewQuestion ? <Loading /> : <>
              <div className="question-content"><p lang={reviewQuestion.content_locale}>{reviewQuestion.prompt}</p></div>
              {reviewQuestion.question_type === 'mcq' ? <ul className="space-y-3" aria-label={t('exam.savedResponse')}>
                {reviewQuestion.options.map(option => <li key={option.option_id} className="rounded-lg border border-edge p-3 text-sm text-ink">
                  <span>{option.option_label}. {option.option_text}</span>
                  {option.option_id === reviewQuestion.selected_option_id && <strong className="ml-2 text-sm">{t('exam.yourSelection')}</strong>}
                </li>)}
              </ul> : <pre tabIndex={0} role="region" aria-label={t('exam.savedResponse')} className="whitespace-pre-wrap break-words rounded-lg border border-edge p-4 text-sm text-ink">{reviewQuestion.sql_answer || reviewQuestion.essay_answer || t('exam.noSavedResponse')}</pre>}
            </>}
          </div>}
          <div hidden={reviewSeq !== null}>
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
                <h2 id="question-number">{t('exam.questionOf', { number: number(state.served_count), max: number(state.max_questions) })}</h2>
                <span className="question-score">{t('exam.points', { value: number(q.points) })}</span>
                <span className="question-score">{t('exam.difficulty', { value: number(q.difficulty_level) })}</span>
                <span className="question-score">{t(`exam.type_${q.question_type}`)}</span>
              </div>

              <div className="question-content">
                <p className="text-xs text-mute">{t('authoring.contentLanguage', { language: t(`authoring.${q.content_locale === 'vi' ? 'vi' : 'en'}`) })}</p>
                {displayError && <p role="status" className="text-xs text-amber-300">{t('authoring.languageLoadError')} <button type="button" className="underline" onClick={() => setDisplayRetry(value => value + 1)}>{t('common.retry')}</button></p>}
                <p lang={q.content_locale || 'en'}>{q.prompt}</p>
                {q.question_type === 'sql' && q.schema_sql && (
                  <pre tabIndex={0} role="region" aria-label={t('sql.schema')}>{q.schema_sql}</pre>
                )}
                {q.concepts?.length > 0 && (
                  <div className="concept-row" aria-label={t('common.concepts')}>
                    {q.concepts.map((concept) => <span key={concept} className="concept-chip">{concept}</span>)}
                  </div>
                )}
              </div>

              {q.question_type === 'mcq' && (
                <fieldset lang={q.content_locale || 'en'} className="answers-fieldset" disabled={submitting || finishing}>
                  <legend>{t('exam.chooseLegend')}</legend>
                  <div className="answer-list">
                    {q.options.map((option) => (
                      <label key={option.option_id} className="answer-option">
                        <input
                          type="radio"
                          name={`answer-${q.question_id}`}
                          value={option.option_id}
                          checked={draft.option === option.option_id}
                          aria-label={`${option.option_label}: ${option.option_text}`}
                          onChange={() => setDraft((d) => ({ ...d, option: option.option_id }))}
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
                      <span><Icon name="code" className="icon" /> query.sql — PostgreSQL</span>
                      <button type="button" className="action-button" onClick={runSql} disabled={running || submitting || !draft.sql.trim()}>
                        {running ? <ActionSpinner /> : <Icon name="play" className="icon" />}
                        {running ? t('sql.running') : t('sql.run')}
                      </button>
                    </div>
                    <SqlEditor value={draft.sql} onChange={(sql) => setDraft((d) => ({ ...d, sql }))} disabled={submitting || finishing} />
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
                <fieldset className="answers-fieldset" disabled={submitting || finishing}>
                  <label htmlFor="essay-answer" className="mb-2 block font-mono text-[11px] font-semibold tracking-[.5px] text-sub">{t('essay.answer')}</label>
                  <textarea id="essay-answer" className="ex-essay" value={draft.essay} onChange={(e) => setDraft((d) => ({ ...d, essay: e.target.value }))} maxLength={30000} rows={13} placeholder={t('essay.placeholder')} />
                  <p className="word-count">{t('essay.words', { count: wordCount })}</p>
                </fieldset>
              )}

              <p className="save-status" role="status" aria-live="polite">
                {saveStatus === 'saving' ? t('exam.draftSaving') : saveStatus === 'unsaved' ? t('exam.unsaved') : saveStatus === 'error' ? t('exam.draftFailed') : saveStatus === 'saved' ? t('exam.draftSaved') : '\u00A0'}
              </p>

              <div className="question-actions">
                <div className="right-actions">
                  <button type="button" className="action-button reset-button" disabled={submitting || finishing} onClick={resetDraft}>
                    <Icon name="reset" className="icon" />
                    {t('exam.resetAnswer')}
                  </button>
                  <button type="button" className="action-button" disabled={saveStatus === 'saving' || submitting || finishing} onClick={() => flushDraft().catch(() => {})}>
                    <Icon name="save" className="icon" />
                    {t('exam.saveDraft')}
                  </button>
                  <button type="button" className="action-button next-button" disabled={submitting || finishing} onClick={submit}>
                    {submitting && <ActionSpinner />}
                    <span>{submitting ? t('exam.submitting') : t('exam.submit')}</span>
                    <Icon name="arrowRight" className="icon" />
                  </button>
                </div>
              </div>
            </>
          )}
          </div>
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

      <ConfirmDialog open={confirmFinish} title={t('exam.finishTitle')} confirmLabel={finishing ? t('exam.finishing') : t('exam.confirmFinish')} onConfirm={finish} onCancel={() => setConfirmFinish(false)}>
        {t('exam.finishBody', { count: state.answered_count })}
      </ConfirmDialog>
    </div>
  )
}
