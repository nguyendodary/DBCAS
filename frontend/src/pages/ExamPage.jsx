import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import api, { apiMessage } from '../api'
import { EmptyState, ErrorState, Loading } from '../components/States'
import { Badge, Card, ConfirmDialog, Icon, TypeBadge } from '../components/ui'

function fmtClock(sec) {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

// UC12-15 — the adaptive exam room: countdown, one question at a time,
// immediate per-question grading feedback, then the engine's next pick.
// Layout follows the static-pages exam-room mockups: sticky header with
// a clock pill, lettered option rows, and a framed SQL editor. The
// prototypes' fixed-question navigator is intentionally absent — the
// adaptive engine serves questions one at a time.
export default function ExamPage() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const [state, setState] = useState(null)
  const [error, setError] = useState(null)
  const [secondsLeft, setSecondsLeft] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [feedback, setFeedback] = useState(null) // AttemptResult just graded
  const [draft, setDraft] = useState({ option: null, sql: '', essay: '' })
  const [runResult, setRunResult] = useState(null)
  const [running, setRunning] = useState(false)
  const [confirmFinish, setConfirmFinish] = useState(false)
  const finishedRef = useRef(false)

  const finish = useCallback(
    async (navigateAfter = true) => {
      if (finishedRef.current) return
      finishedRef.current = true
      try {
        await api.post(`/sessions/${sessionId}/finish`)
      } catch {
        // best effort — the server flips expired sessions on read anyway
      }
      if (navigateAfter) navigate('/dashboard', { replace: true })
    },
    [sessionId, navigate]
  )

  const load = useCallback(() => {
    setError(null)
    api
      .get(`/sessions/${sessionId}`)
      .then((r) => {
        setState(r.data)
        setSecondsLeft((prev) => (prev === null ? r.data.remaining_seconds : prev))
        if (r.data.status !== 'in_progress') {
          navigate('/dashboard', { replace: true })
        }
      })
      .catch((e) => {
        setError(apiMessage(e, 'Could not load the session'))
      })
  }, [sessionId, navigate])

  useEffect(load, [load])

  // countdown — auto-submit at 00:00 (documented timer rule)
  useEffect(() => {
    if (secondsLeft === null) return
    if (secondsLeft <= 0) {
      finish()
      return
    }
    const t = setTimeout(() => setSecondsLeft((s) => (s ?? 0) - 1), 1000)
    return () => clearTimeout(t)
  }, [secondsLeft, finish])

  const q = state?.current_question

  async function submit() {
    if (!q) return
    setSubmitting(true)
    setError(null)
    const payload = { question_id: q.question_id }
    if (q.question_type === 'mcq') payload.selected_option_id = draft.option
    if (q.question_type === 'sql') payload.sql_answer = draft.sql
    if (q.question_type === 'essay') payload.essay_answer = draft.essay
    try {
      const r = await api.post(`/sessions/${sessionId}/answers`, payload)
      setFeedback(r.data)
      // pull the engine's next pick
      const nxt = await api.post(`/sessions/${sessionId}/serve-next`)
      const s = await api.get(`/sessions/${sessionId}`)
      setState(s.data)
      setDraft({ option: null, sql: '', essay: '' })
      setRunResult(null)
      if (nxt.data.done) {
        // nothing left to serve — keep UI on a finish prompt
        setFeedback((f) => f)
      }
    } catch (e) {
      setError(apiMessage(e, 'Could not submit the answer'))
    } finally {
      setSubmitting(false)
    }
  }

  async function runSql() {
    if (!q || q.question_type !== 'sql' || !draft.sql.trim()) return
    setRunning(true)
    setRunResult(null)
    try {
      const r = await api.post(`/sessions/${sessionId}/sql-run`, {
        question_id: q.question_id,
        sql: draft.sql,
      })
      setRunResult(r.data)
    } catch (e) {
      setRunResult({ success: false, error_message: apiMessage(e) })
    } finally {
      setRunning(false)
    }
  }

  if (error && !state) return <ErrorState message={error} onRetry={load} />
  if (!state) return <Loading label="Loading session…" />

  const answeredPct =
    state.max_questions > 0
      ? Math.round((state.answered_count / state.max_questions) * 100)
      : 0
  const lowTime = secondsLeft !== null && secondsLeft <= 600

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      {/* persistent countdown + progress (story 3) */}
      <Card className="flex flex-wrap items-center justify-between gap-3 p-4">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-gray-500">
            {state.assessment_title}
          </p>
          <p className="text-sm text-gray-600">
            Question {state.served_count} of up to {state.max_questions} ·{' '}
            {state.answered_count} answered
          </p>
        </div>
        <div
          aria-label="Time remaining"
          className={`flex items-center gap-2 rounded-lg px-3 py-1.5 font-mono text-lg font-semibold ${
            lowTime ? 'bg-red-50 text-red-700' : 'bg-gray-900 text-white'
          }`}
        >
          <Icon name="clock" className="h-4 w-4" />
          {secondsLeft === null ? '--:--' : fmtClock(Math.max(0, secondsLeft))}
        </div>
      </Card>
      {lowTime && secondsLeft !== null && secondsLeft > 0 && (
        <p role="alert" className="text-sm text-red-600">
          {secondsLeft <= 300
            ? 'Less than 5 minutes left — answers submit automatically at 00:00.'
            : 'Less than 10 minutes left.'}
        </p>
      )}

      <div className="h-1.5 w-full rounded-full bg-gray-200" aria-hidden="true">
        <div
          className="h-1.5 rounded-full bg-blue-600 transition-all"
          style={{ width: `${answeredPct}%` }}
        />
      </div>

      {feedback && (
        <div
          role="status"
          className={`flex items-center gap-2 rounded-lg border p-3 text-sm ${
            feedback.is_correct
              ? 'border-green-200 bg-green-50 text-green-800'
              : 'border-amber-200 bg-amber-50 text-amber-800'
          }`}
        >
          <Icon name={feedback.is_correct ? 'check' : 'info'} className="h-4 w-4 shrink-0" />
          <span>
            {feedback.is_correct ? 'Correct' : 'Not quite'} — scored{' '}
            {feedback.score} / {feedback.points_possible} pts on the previous
            question.
          </span>
        </div>
      )}
      {error && <ErrorState message={error} />}

      {!q ? (
        <EmptyState title="All questions served">
          {state.done
            ? 'You reached the end of this adaptive session.'
            : 'No further questions are available.'}{' '}
          Submit the assessment to see your results.
        </EmptyState>
      ) : (
        <Card className="p-5">
          <div className="mb-3 flex flex-wrap items-center gap-2 text-xs">
            <TypeBadge type={q.question_type} />
            <Badge>difficulty {q.difficulty_level}</Badge>
            <Badge>{q.points} pts</Badge>
            {q.concepts.map((c) => (
              <Badge key={c} tone="blue">
                {c}
              </Badge>
            ))}
          </div>
          <p className="whitespace-pre-wrap font-medium text-gray-900">{q.prompt}</p>

          {q.question_type === 'mcq' && (
            <fieldset className="mt-4 space-y-2">
              <legend className="sr-only">Choose one answer</legend>
              {q.options.map((o) => {
                const selected = draft.option === o.option_id
                return (
                  <label
                    key={o.option_id}
                    className={`flex cursor-pointer items-center gap-3 rounded-lg border p-3 transition-colors ${
                      selected
                        ? 'border-blue-500 bg-blue-50 ring-1 ring-blue-500'
                        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    <input
                      type="radio"
                      name="mcq"
                      value={o.option_id}
                      checked={selected}
                      onChange={() => setDraft((d) => ({ ...d, option: o.option_id }))}
                      className="sr-only"
                    />
                    <span
                      className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-xs font-bold ${
                        selected ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600'
                      }`}
                    >
                      {o.option_label}
                    </span>
                    <span className="text-sm text-gray-800">{o.option_text}</span>
                  </label>
                )
              })}
            </fieldset>
          )}

          {q.question_type === 'sql' && (
            <div className="mt-4 space-y-3">
              {q.schema_sql && (
                <details className="rounded-lg border bg-gray-50 p-3 text-xs">
                  <summary className="cursor-pointer font-medium text-gray-700">
                    Test-table schema
                  </summary>
                  <pre className="mt-2 overflow-x-auto whitespace-pre-wrap text-gray-600">
                    {q.schema_sql}
                  </pre>
                </details>
              )}
              <label className="block text-sm font-medium text-gray-700">
                Your query
                <span className="mt-1 block overflow-hidden rounded-lg border border-gray-300 focus-within:border-blue-500">
                  <span className="flex items-center gap-1.5 border-b bg-gray-800 px-3 py-1.5 text-xs text-gray-300">
                    <Icon name="code" className="h-3.5 w-3.5" />
                    SQL editor
                  </span>
                  <textarea
                    value={draft.sql}
                    onChange={(e) => setDraft((d) => ({ ...d, sql: e.target.value }))}
                    rows={6}
                    spellCheck={false}
                    className="block w-full bg-gray-950 p-3 font-mono text-sm text-gray-100 placeholder-gray-500 focus:outline-none"
                    placeholder="SELECT ..."
                  />
                </span>
              </label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={runSql}
                  disabled={running || !draft.sql.trim()}
                  className="flex items-center gap-1.5 rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-100 disabled:opacity-50"
                >
                  <Icon name="play" className="h-3.5 w-3.5" />
                  {running ? 'Running…' : 'Run in sandbox'}
                </button>
              </div>
              {runResult && (
                <div className="rounded-lg border bg-gray-50 p-3 text-sm">
                  {runResult.success ? (
                    <>
                      <p className="text-xs text-gray-500">
                        {runResult.row_count} row(s) · {runResult.execution_time_ms} ms
                      </p>
                      <div className="mt-2 overflow-x-auto">
                        <table className="w-full border-collapse text-xs">
                          <thead>
                            <tr>
                              {runResult.columns.map((c) => (
                                <th key={c} className="border bg-gray-100 px-2 py-1 text-left">
                                  {c}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {runResult.rows.map((row, i) => (
                              <tr key={i}>
                                {row.map((v, j) => (
                                  <td key={j} className="border px-2 py-1">
                                    {String(v)}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </>
                  ) : (
                    <p className="text-red-700">
                      {runResult.error_type && (
                        <span className="mr-2 font-medium">{runResult.error_type}</span>
                      )}
                      {runResult.error_message}
                    </p>
                  )}
                </div>
              )}
            </div>
          )}

          {q.question_type === 'essay' && (
            <label className="mt-4 block text-sm font-medium text-gray-700">
              Your answer
              <textarea
                value={draft.essay}
                onChange={(e) => setDraft((d) => ({ ...d, essay: e.target.value }))}
                rows={7}
                className="mt-1 w-full rounded-lg border border-gray-300 p-3 text-sm focus:border-blue-500 focus:outline-none"
                placeholder="Explain the concept clearly…"
              />
            </label>
          )}

          <div className="mt-5 flex items-center justify-between">
            <button
              type="button"
              onClick={submit}
              disabled={submitting}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {submitting ? 'Submitting…' : 'Submit answer'}
            </button>
            <p className="text-xs text-gray-400">
              Empty answers count as unanswered (0 pts).
            </p>
          </div>
        </Card>
      )}

      <div className="flex justify-end">
        <button
          type="button"
          onClick={() => setConfirmFinish(true)}
          className="rounded-md border border-red-300 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-50"
        >
          Finish assessment
        </button>
      </div>
      <ConfirmDialog
        open={confirmFinish}
        title="Submit the whole assessment?"
        confirmLabel="Yes, finish"
        onConfirm={() => finish()}
        onCancel={() => setConfirmFinish(false)}
      >
        Answers are final once submitted. You can still keep working until the
        timer ends — the session auto-submits at 00:00.
      </ConfirmDialog>
    </div>
  )
}
