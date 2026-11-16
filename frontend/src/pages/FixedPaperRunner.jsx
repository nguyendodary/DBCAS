import LanguageSelector from '../components/LanguageSelector'
import ThemeSelector from '../components/ThemeSelector'
import { t, useLocale, message, number } from '../i18n'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api, { apiMessage } from '../api'
import { ActionSpinner, ErrorState, Loading } from '../components/States'
import GradingStatusPanel from '../components/GradingStatusPanel'
import { ConfirmDialog, Icon, btnGhost, focusDialogTrigger } from '../components/ui'
import { HelpButton } from '../components/HelpGuide'
import { BrandWordmark } from '../components/BrandLogo'
import { usePaperDraft } from '../usePaperDraft'
import QuestionPalette from '../components/QuestionPalette'
import SqlEditor from '../components/SqlEditor'
import SqlSchema from '../components/SqlSchema'

function fmtClock(sec) {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

function cleanPrompt(prompt) {
  return (prompt || '')
    .trim()
    .replace(
      /^(?:Nội dung câu hỏi|Question content):[^.]+\.\s*(?:Hiển thị bản dịch[^.]*\.|Shows the approved translation[^.]*\.)\s*/i,
      '',
    )
    .replace(/\s+/g, ' ')
    .trim()
}

function stripDataset(prompt, schema) {
  let text = cleanPrompt(prompt)
  if (schema) {
    const index = text.indexOf(schema)
    if (index >= 0) text = `${text.slice(0, index)} ${text.slice(index + schema.length)}`
  }
  return text
    .replace(/(?:Dữ liệu PostgreSQL cố định|Fixed PostgreSQL data)[^:]{0,160}:\s*/i, ' ')
    .replace(/\bCREATE\s+TABLE\b[\s\S]*?;\s*/gi, ' ')
    .replace(/\bINSERT\s+INTO\b[\s\S]*?;\s*/gi, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

function splitParagraphs(text, maxLength = 280) {
  const sentences = text.split(/(?<=[.!?])\s+(?=[A-ZÀ-Ỹ0-9"“(])/u).filter(Boolean)
  const paragraphs = []
  let current = ''
  for (const sentence of sentences) {
    const next = current ? `${current} ${sentence}` : sentence
    if (current && (next.length > maxLength || current.split(/(?<=[.!?])/).length >= 2)) {
      paragraphs.push(current)
      current = sentence
    } else current = next
  }
  if (current) paragraphs.push(current)
  return paragraphs.length ? paragraphs : [text]
}

const codeOf = (error) => error?.response?.data?.error?.code
const isExpired = (error) => codeOf(error) === 'session_expired'

export default function FixedPaperRunner({ sessionId, initialState }) {
  useLocale()
  const navigate = useNavigate()
  const [paper, setPaper] = useState(null)
  const [question, setQuestion] = useState(null)
  const [currentSeq, setCurrentSeq] = useState(null)
  const [secondsLeft, setSecondsLeft] = useState(null)
  const [warning, setWarning] = useState(null)
  const [error, setError] = useState(null)
  const [flagState, setFlagState] = useState({ flagged: false, revision: 0 })
  const [flagSaving, setFlagSaving] = useState(false)
  const [flagError, setFlagError] = useState(null)
  const [flagNotice, setFlagNotice] = useState(null)
  const [confirmFinish, setConfirmFinish] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState(null)
  const [runResult, setRunResult] = useState(null)
  const [running, setRunning] = useState(false)
  const [retry, setRetry] = useState(0)

  const clock = useRef(null)
  const expired = useRef(false)
  const submittingRef = useRef(false)
  const navigationToken = useRef(0)
  const currentSeqRef = useRef(null)

  const resultPath = useCallback(
    (next) =>
      typeof next === 'string' && next.startsWith('/') ? next : `/evaluations/${sessionId}`,
    [sessionId],
  )

  const acceptClock = useCallback((data) => {
    const now = Date.parse(data.server_now)
    const end = data.expires_at
      ? Date.parse(data.expires_at)
      : now + (data.remaining_seconds ?? 0) * 1000
    const remainingMs = Math.max(0, end - now)
    clock.current = { at: performance.now(), remainingMs }
    setSecondsLeft(Math.ceil(remainingMs / 1000))
  }, [])

  const patchQuestion = useCallback((seq, patch) => {
    setPaper((previous) =>
      previous
        ? {
            ...previous,
            questions: previous.questions.map((item) =>
              item.seq_no === seq ? { ...item, ...patch } : item,
            ),
          }
        : previous,
    )
  }, [])

  const {
    draft,
    setDraft,
    hydrate,
    flushDraft,
    flushAll,
    saveStatus,
    saveError,
    saveConflict,
    reloadSavedDraft,
  } = usePaperDraft(sessionId, patchQuestion)

  const leaveOnExpiry = useCallback(async () => {
    expired.current = true
    try {
      const { data } = await api.post(`/sessions/${sessionId}/paper/submit`, {})
      navigate(resultPath(data.next), { replace: true })
    } catch {
      navigate(resultPath(), { replace: true })
    }
  }, [sessionId, navigate, resultPath])

  const openSeq = useCallback(
    async (seq, { skipFlush = false } = {}) => {
      if (currentSeqRef.current === seq) return
      const token = ++navigationToken.current
      if (!skipFlush) {
        try {
          await flushDraft()
        } catch {
          // Save errors are already visible; keep the user on this question.
          return
        }
      }
      try {
        if (token !== navigationToken.current) return
        const { data } = await api.get(`/sessions/${sessionId}/paper/${seq}`)
        if (token !== navigationToken.current) return
        currentSeqRef.current = seq
        setCurrentSeq(seq)
        setQuestion(data)
        hydrate(data)
        setFlagState({ flagged: data.flagged, revision: data.flag_revision ?? 0 })
        setFlagError(null)
        setFlagNotice(null)
        setRunResult(null)
        patchQuestion(seq, {
          opened: true,
          flagged: data.flagged,
          answered: data.answered,
          draft_revision: data.draft_revision,
        })
        acceptClock(data)
        setError(null)
      } catch (cause) {
        if (token !== navigationToken.current) return
        if (isExpired(cause)) return leaveOnExpiry()
        setError(apiMessage(cause, message('paper.loadError')))
      }
    },
    [sessionId, flushDraft, hydrate, patchQuestion, acceptClock, leaveOnExpiry],
  )

  // Resume: paper metadata supplies last_opened_seq and the authoritative
  // server clock; opening that seq restores its saved draft and flag state.
  useEffect(() => {
    if (initialState?.status && initialState.status !== 'in_progress') {
      navigate(resultPath(), { replace: true })
      return undefined
    }
    let active = true
    api
      .get(`/sessions/${sessionId}/paper`)
      .then(({ data }) => {
        if (!active) return
        setPaper(data)
        acceptClock(data)
        const seq = data.last_opened_seq ?? data.questions?.[0]?.seq_no
        if (seq) openSeq(seq, { skipFlush: true })
      })
      .catch((cause) => {
        if (!active) return
        if (isExpired(cause)) leaveOnExpiry()
        else setError(apiMessage(cause, message('paper.loadError')))
      })
    return () => {
      active = false
    }
  }, [
    sessionId,
    initialState?.status,
    openSeq,
    acceptClock,
    leaveOnExpiry,
    navigate,
    resultPath,
    retry,
  ])

  // A draft can lose the race against the server deadline; the authoritative
  // expiry then routes to the finalized paper instead of a misleading retry.
  useEffect(() => {
    if (saveError?.translationKey === 'errors.session_expired') leaveOnExpiry()
  }, [saveError, leaveOnExpiry])

  useEffect(() => {
    const onVisible = () => {
      if (document.visibilityState !== 'visible' || expired.current) return
      api
        .get(`/sessions/${sessionId}/paper`)
        .then(({ data }) => {
          setPaper(data)
          acceptClock(data)
        })
        .catch(() => {})
    }
    document.addEventListener('visibilitychange', onVisible)
    return () => document.removeEventListener('visibilitychange', onVisible)
  }, [sessionId, acceptClock])

  const doSubmit = useCallback(
    async ({ auto = false } = {}) => {
      if (submittingRef.current) return
      submittingRef.current = true
      setSubmitting(true)
      setSubmitError(null)
      setConfirmFinish(false)
      try {
        if (!auto) await flushAll()
        const { data } = await api.post(`/sessions/${sessionId}/paper/submit`, {
          request_id: crypto.randomUUID(),
        })
        navigate(resultPath(data.next), { replace: true })
      } catch (cause) {
        if (isExpired(cause) || codeOf(cause) === 'session_not_active') {
          try {
            const { data } = await api.post(`/sessions/${sessionId}/paper/submit`, {})
            navigate(resultPath(data.next), { replace: true })
          } catch {
            navigate(resultPath(), { replace: true })
          }
          return
        }
        setSubmitError(apiMessage(cause, message('paper.submitError')))
        submittingRef.current = false
      } finally {
        setSubmitting(false)
      }
    },
    [sessionId, navigate, resultPath, flushAll],
  )

  useEffect(() => {
    const tick = () => {
      if (!clock.current || paper?.status !== 'in_progress' || expired.current) return
      const remaining = Math.max(
        0,
        clock.current.remainingMs - (performance.now() - clock.current.at),
      )
      const seconds = Math.ceil(remaining / 1000)
      setSecondsLeft(seconds)
      const threshold =
        seconds > 0 && seconds <= 60
          ? 1
          : seconds > 0 && seconds <= 300
            ? 5
            : seconds > 0 && seconds <= 600
              ? 10
              : null
      if (threshold && !sessionStorage.getItem(`dbcas-paper-warning:${sessionId}:${threshold}`)) {
        sessionStorage.setItem(`dbcas-paper-warning:${sessionId}:${threshold}`, 'shown')
        setWarning(threshold)
      }
      if (remaining <= 0) {
        expired.current = true
        doSubmit({ auto: true })
      }
    }
    tick()
    const timer = setInterval(tick, 500)
    return () => clearInterval(timer)
  }, [paper?.status, sessionId, doSubmit])

  async function toggleFlag() {
    if (!question || flagSaving) return
    const seq = question.seq_no
    const desired = !flagState.flagged
    setFlagSaving(true)
    setFlagError(null)
    setFlagNotice(null)
    try {
      const { data } = await api.put(`/sessions/${sessionId}/paper/${seq}/flag`, {
        flagged: desired,
        revision: flagState.revision,
      })
      setFlagState({ flagged: data.flagged, revision: data.revision })
      setQuestion((previous) =>
        previous?.seq_no === seq
          ? { ...previous, flagged: data.flagged, flag_revision: data.revision }
          : previous,
      )
      patchQuestion(seq, { flagged: data.flagged })
    } catch (cause) {
      if (isExpired(cause)) return leaveOnExpiry()
      if (codeOf(cause) === 'flag_revision_conflict') {
        try {
          const { data } = await api.get(`/sessions/${sessionId}/paper/${seq}`)
          setFlagState({ flagged: data.flagged, revision: data.flag_revision ?? 0 })
          patchQuestion(seq, { flagged: data.flagged })
          setFlagNotice(t('paper.flagConflict'))
        } catch {
          setFlagError(apiMessage(cause, message('paper.flagError')))
        }
      } else {
        setFlagError(apiMessage(cause, message('paper.flagError')))
      }
    } finally {
      setFlagSaving(false)
    }
  }

  async function reloadDraft() {
    try {
      const data = await reloadSavedDraft()
      if (!data) return
      setQuestion(data)
      setFlagState({ flagged: data.flagged, revision: data.flag_revision ?? 0 })
      patchQuestion(data.seq_no, { answered: data.answered, flagged: data.flagged })
    } catch (cause) {
      if (isExpired(cause)) leaveOnExpiry()
      else setError(apiMessage(cause, message('paper.loadError')))
    }
  }

  async function requestFinish(event) {
    focusDialogTrigger(event)
    setSubmitError(null)
    try {
      await flushAll()
      const { data } = await api.get(`/sessions/${sessionId}/paper`)
      setPaper(data)
      setConfirmFinish(true)
    } catch (cause) {
      if (isExpired(cause)) leaveOnExpiry()
      else setError(apiMessage(cause, message('paper.finishError')))
    }
  }

  async function runSql() {
    if (!question || question.question_type !== 'sql' || !draft?.sql?.trim()) return
    setRunning(true)
    setRunResult(null)
    try {
      const { data } = await api.post(`/sessions/${sessionId}/sql-run`, {
        question_id: question.question_id,
        sql: draft.sql,
      })
      setRunResult(data)
    } catch (cause) {
      if (isExpired(cause)) leaveOnExpiry()
      else setRunResult({ success: false, error_message: apiMessage(cause) })
    } finally {
      setRunning(false)
    }
  }

  const questions = paper?.questions ?? []
  const index = questions.findIndex((item) => item.seq_no === currentSeq)
  const sqlParagraphs = useMemo(
    () =>
      question?.question_type === 'sql'
        ? splitParagraphs(stripDataset(question.prompt, question.schema_sql))
        : [],
    [question?.question_type, question?.prompt, question?.schema_sql],
  )
  const wordCount = draft?.essay?.trim() ? draft.essay.trim().split(/\s+/).length : 0
  const ended = secondsLeft !== null && secondsLeft <= 0
  const lowTime = secondsLeft !== null && secondsLeft <= 600
  const totalSec =
    paper?.started_at && paper?.expires_at
      ? Math.max(
          0,
          Math.round((Date.parse(paper.expires_at) - Date.parse(paper.started_at)) / 1000),
        )
      : (secondsLeft ?? 0)

  if (error && !paper)
    return (
      <div className="exam-shell">
        <div className="p-8">
          <ErrorState message={error} onRetry={() => setRetry((value) => value + 1)} />
        </div>
      </div>
    )
  if (!paper || !question)
    return (
      <div className="exam-shell">
        <Loading label={t('paper.loading')} />
      </div>
    )
  if (submitting)
    return (
      <div className="exam-shell">
        <GradingStatusPanel status="submitting" />
      </div>
    )

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
              <h1>{paper.assessment_title}</h1>
              <p>
                {t('paper.progress', {
                  current: number(currentSeq),
                  max: number(questions.length),
                  answered: questions.filter((item) => item.answered).length,
                  flagged: questions.filter((item) => item.flagged).length,
                })}
              </p>
            </div>
          </div>
          <div className="exam-controls">
            <HelpButton />
            <LanguageSelector />
            <ThemeSelector />
            <div
              className={`timer-box${ended ? ' ended' : lowTime ? ' time-warning' : ''}`}
              aria-label={t('exam.timeRemaining')}
            >
              <Icon name="clock" className="icon timer-icon" />
              <div>
                <span className="timer-label">
                  {ended ? t('exam.ended') : t('exam.timeRemaining')}
                </span>
                <div className="timer-value">
                  <strong>
                    {secondsLeft === null ? '--:--' : fmtClock(Math.max(0, secondsLeft))}
                  </strong>
                  {totalSec > 0 && <span>/ {fmtClock(totalSec)}</span>}
                </div>
              </div>
            </div>
            <button
              type="button"
              className="finish-button"
              disabled={submitting || ended}
              onClick={requestFinish}
            >
              <Icon name="upload" className="icon" />
              <span>{ended ? t('exam.ended') : t('paper.finish')}</span>
            </button>
          </div>
        </div>
      </header>

      <div className="exam-layout">
        <aside className="ex-sidebar">
          <QuestionPalette
            questions={questions}
            currentSeq={currentSeq}
            onJump={openSeq}
            disabled={submitting}
          />
          <p className="sidebar-note">{t('exam.sectionNote')}</p>
        </aside>

        <section className="question-panel" aria-labelledby="paper-question-number">
          {warning && secondsLeft > 0 && (
            <p
              role="alert"
              className="ex-banner mb-4"
              style={{ width: '100%', margin: '0 0 16px' }}
            >
              <Icon name="alert" className="icon" />
              {warning === 1
                ? t('paper.warning1')
                : warning === 5
                  ? t('paper.warning5')
                  : t('paper.warning10')}
            </p>
          )}
          {error && <ErrorState message={error} onRetry={() => setRetry((value) => value + 1)} />}
          {submitError && <ErrorState message={submitError} onRetry={() => doSubmit()} />}
          {saveError && (
            <ErrorState message={saveError} onRetry={() => flushDraft().catch(() => {})} />
          )}
          {saveConflict && (
            <button type="button" className={btnGhost} onClick={reloadDraft}>
              {t('paper.reloadDraft')}
            </button>
          )}
          {flagError && <ErrorState message={flagError} onRetry={toggleFlag} />}
          {flagNotice && (
            <p
              role="status"
              className="ex-banner info"
              style={{ width: '100%', margin: '0 0 16px' }}
            >
              <Icon name="info" className="icon" />
              {flagNotice}
            </p>
          )}

          <div className="question-top">
            <h2 id="paper-question-number">
              {t('paper.questionOf', {
                number: number(currentSeq),
                max: number(questions.length),
              })}
            </h2>
            <button
              type="button"
              className={btnGhost}
              onClick={toggleFlag}
              disabled={flagSaving}
              aria-pressed={flagState.flagged}
              aria-busy={flagSaving}
            >
              <Icon name="flag" className="icon" />
              {flagSaving
                ? t('paper.flagSaving')
                : flagState.flagged
                  ? t('paper.unflag')
                  : t('paper.flag')}
            </button>
          </div>

          <div
            className={`question-content${question.question_type === 'sql' ? ' sql-brief' : ''}`}
          >
            {question.question_type === 'sql' ? (
              <div className="sql-prompt">
                {sqlParagraphs.map((paragraph, i) => (
                  <p key={i} lang={question.content_locale || 'en'}>
                    {paragraph}
                  </p>
                ))}
              </div>
            ) : (
              <p lang={question.content_locale || 'en'}>{cleanPrompt(question.prompt)}</p>
            )}
          </div>
          {question.question_type === 'sql' && <SqlSchema schema={question.schema_sql} />}

          {question.question_type === 'mcq' && (
            <fieldset lang={question.content_locale || 'en'} className="answers-fieldset">
              <legend>{t('exam.chooseLegend')}</legend>
              <div className="answer-list">
                {(question.options ?? []).map((option) => (
                  <label key={option.option_id} className="answer-option">
                    <input
                      type="radio"
                      name={`paper-answer-${question.question_id}`}
                      value={option.option_id}
                      checked={draft?.option === option.option_id}
                      aria-label={`${option.option_label}: ${option.option_text}`}
                      onChange={() =>
                        setDraft((values) => ({ ...values, option: option.option_id }))
                      }
                    />
                    <span className="answer-body">
                      <span className="answer-heading">
                        <span className="answer-letter">{option.option_label}</span>
                        <span lang={question.content_locale || 'en'} className="answer-text">
                          {option.option_text}
                        </span>
                        <span className="selected-tag">{t('exam.selectedTag')}</span>
                      </span>
                    </span>
                  </label>
                ))}
              </div>
            </fieldset>
          )}

          {question.question_type === 'sql' && (
            <>
              <div className="ex-editor sql-editor-pane">
                <div className="ex-editor-bar">
                  <span>
                    <Icon name="code" className="icon" /> query.sql — PostgreSQL
                  </span>
                  <div className="sql-editor-actions">
                    <button
                      type="button"
                      className="action-button next-button"
                      onClick={runSql}
                      disabled={running || !draft?.sql?.trim()}
                    >
                      {running ? <ActionSpinner /> : <Icon name="play" className="icon" />}
                      {running ? t('sql.running') : t('sql.run')}
                    </button>
                  </div>
                </div>
                <SqlEditor
                  value={draft?.sql ?? ''}
                  onChange={(sql) => setDraft((values) => ({ ...values, sql }))}
                />
              </div>
              <div className="ex-results sql-result-pane" aria-live="polite">
                <div className="ex-results-head">
                  <span>{t('sql.results')}</span>
                  {runResult?.success && (
                    <span>
                      {t('sql.rowSummary', {
                        count: runResult.row_count,
                        time: number(runResult.execution_time_ms),
                      })}
                    </span>
                  )}
                </div>
                <div className="ex-results-body">
                  {running ? (
                    <p role="status" className="flex items-center gap-2">
                      <ActionSpinner />
                      {t('sql.runningQuery')}
                    </p>
                  ) : runResult?.success ? (
                    <div
                      tabIndex={0}
                      role="region"
                      aria-label={t('sql.resultTable')}
                      className="sql-result-scroll"
                    >
                      <table className="data-table">
                        <thead>
                          <tr>
                            {(runResult.columns ?? []).map((column) => (
                              <th key={column} title={column}>
                                {column}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {(runResult.rows ?? []).map((row, i) => (
                            <tr key={i}>
                              {row.map((value, j) => (
                                <td key={j} title={String(value ?? 'NULL')}>
                                  {String(value ?? 'NULL')}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : runResult ? (
                    <div role="alert" className="sql-error">
                      <p>
                        <Icon name="alert" className="icon" />
                        {typeof runResult.error_message === 'string'
                          ? runResult.error_message
                          : t('sql.executionError')}
                      </p>
                    </div>
                  ) : (
                    <p>{t('sql.runHint')}</p>
                  )}
                </div>
              </div>
            </>
          )}

          {question.question_type === 'essay' && (
            <fieldset className="answers-fieldset">
              <label
                htmlFor="paper-essay"
                className="mb-2 block text-2xs font-semibold tracking-[.5px] text-sub"
              >
                {t('essay.answer')}
              </label>
              <textarea
                id="paper-essay"
                className="ex-essay"
                value={draft?.essay ?? ''}
                onChange={(event) =>
                  setDraft((values) => ({ ...values, essay: event.target.value }))
                }
                maxLength={30000}
                rows={13}
                placeholder={t('essay.placeholder')}
              />
              <p className="word-count">{t('essay.words', { count: wordCount })}</p>
            </fieldset>
          )}

          <p className="save-status" role="status" aria-live="polite">
            {saveStatus === 'saving'
              ? t('paper.draftSaving')
              : saveStatus === 'unsaved'
                ? t('paper.unsaved')
                : saveStatus === 'error'
                  ? t('exam.draftFailed')
                  : saveStatus === 'saved'
                    ? t('paper.draftSaved')
                    : '\u00A0'}
          </p>

          <div className="question-actions">
            <div className="right-actions">
              <button
                type="button"
                className="action-button"
                disabled={index <= 0 || submitting}
                onClick={() => openSeq(questions[index - 1]?.seq_no)}
              >
                <Icon name="arrowLeft" className="icon" />
                {t('paper.previous')}
              </button>
              <button
                type="button"
                className="action-button"
                disabled={saveStatus === 'saving' || submitting}
                onClick={() => flushDraft().catch(() => {})}
              >
                <Icon name="save" className="icon" />
                {t('exam.saveDraft')}
              </button>
              <button
                type="button"
                className="action-button next-button"
                disabled={index < 0 || index >= questions.length - 1 || submitting}
                onClick={() => openSeq(questions[index + 1]?.seq_no)}
              >
                <span>{t('paper.next')}</span>
                <Icon name="arrowRight" className="icon" />
              </button>
            </div>
          </div>
        </section>
      </div>

      <footer className="ex-footer">
        <div className="ex-footer-inner">
          <p>
            <BrandWordmark as="strong" />
            <span>•</span>
            <span>{t('nav.footerTagline')}</span>
          </p>
          <p>{t('nav.copyright', { year: new Date().getFullYear() })}</p>
        </div>
      </footer>

      <ConfirmDialog
        open={confirmFinish}
        title={t('paper.finishTitle')}
        confirmLabel={t('paper.confirm')}
        cancelLabel={t('common.keepGoing')}
        onConfirm={() => doSubmit()}
        onCancel={() => setConfirmFinish(false)}
      >
        {t('paper.finishBody_other', {
          answered: questions.filter((item) => item.answered).length,
          unanswered: questions.filter((item) => !item.answered).length,
          flagged: questions.filter((item) => item.flagged).length,
          max: questions.length,
        })}
      </ConfirmDialog>
    </div>
  )
}
