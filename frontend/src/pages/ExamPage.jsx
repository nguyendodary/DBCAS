import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import api, { apiMessage } from '../api'
import { EmptyState, ErrorState, Loading } from '../components/States'

function fmtClock(sec) {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

// UC12-15 — the adaptive exam room: countdown, one question at a time,
// immediate per-question grading feedback, then the engine's next pick.
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
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border bg-white p-3">
        <div>
          <p className="text-xs uppercase tracking-wide text-gray-500">
            {state.assessment_title}
          </p>
          <p className="text-sm text-gray-600">
            Question {state.served_count} of up to {state.max_questions} ·{' '}
            {state.answered_count} answered
          </p>
        </div>
        <div
          aria-label="Time remaining"
          className={`rounded px-3 py-1 font-mono text-lg ${
            lowTime ? 'bg-red-50 text-red-700' : 'bg-gray-100 text-gray-800'
          }`}
        >
          {secondsLeft === null ? '--:--' : fmtClock(Math.max(0, secondsLeft))}
        </div>
      </div>
      {lowTime && secondsLeft !== null && secondsLeft > 0 && (
        <p role="alert" className="text-sm text-red-600">
          {secondsLeft <= 300
            ? 'Less than 5 minutes left — answers submit automatically at 00:00.'
            : 'Less than 10 minutes left.'}
        </p>
      )}

      <div className="h-1.5 w-full rounded bg-gray-200" aria-hidden="true">
        <div className="h-1.5 rounded bg-blue-600" style={{ width: `${answeredPct}%` }} />
      </div>

      {feedback && (
        <div
          role="status"
          className={`rounded-md border p-3 text-sm ${
            feedback.is_correct
              ? 'border-green-200 bg-green-50 text-green-800'
              : 'border-amber-200 bg-amber-50 text-amber-800'
          }`}
        >
          {feedback.is_correct ? 'Correct' : 'Not quite'} — scored{' '}
          {feedback.score} / {feedback.points_possible} pts on the previous
          question.
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
        <section className="rounded-md border bg-white p-5">
          <div className="mb-3 flex flex-wrap items-center gap-2 text-xs text-gray-500">
            <span className="rounded bg-gray-100 px-2 py-0.5 uppercase">
              {q.question_type}
            </span>
            <span className="rounded bg-gray-100 px-2 py-0.5">
              difficulty {q.difficulty_level}
            </span>
            <span className="rounded bg-gray-100 px-2 py-0.5">
              {q.points} pts
            </span>
            {q.concepts.map((c) => (
              <span key={c} className="rounded bg-blue-50 px-2 py-0.5 text-blue-700">
                {c}
              </span>
            ))}
          </div>
          <p className="whitespace-pre-wrap text-gray-900">{q.prompt}</p>

          {q.question_type === 'mcq' && (
            <fieldset className="mt-4 space-y-2">
              <legend className="sr-only">Choose one answer</legend>
              {q.options.map((o) => (
                <label
                  key={o.option_id}
                  className="flex cursor-pointer items-start gap-2 rounded border p-2 hover:bg-gray-50"
                >
                  <input
                    type="radio"
                    name="mcq"
                    value={o.option_id}
                    checked={draft.option === o.option_id}
                    onChange={() => setDraft((d) => ({ ...d, option: o.option_id }))}
                    className="mt-1"
                  />
                  <span>
                    <span className="mr-1 font-medium">{o.option_label}.</span>
                    {o.option_text}
                  </span>
                </label>
              ))}
            </fieldset>
          )}

          {q.question_type === 'sql' && (
            <div className="mt-4 space-y-3">
              {q.schema_sql && (
                <details className="rounded border bg-gray-50 p-3 text-xs">
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
                <textarea
                  value={draft.sql}
                  onChange={(e) => setDraft((d) => ({ ...d, sql: e.target.value }))}
                  rows={6}
                  spellCheck={false}
                  className="mt-1 w-full rounded border border-gray-300 p-2 font-mono text-sm"
                  placeholder="SELECT ..."
                />
              </label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={runSql}
                  disabled={running || !draft.sql.trim()}
                  className="rounded border border-gray-300 px-3 py-1 text-sm text-gray-700 hover:bg-gray-100 disabled:opacity-50"
                >
                  {running ? 'Running…' : 'Run in sandbox'}
                </button>
              </div>
              {runResult && (
                <div className="rounded border bg-gray-50 p-3 text-sm">
                  {runResult.success ? (
                    <>
                      <p className="text-xs text-gray-500">
                        {runResult.row_count} row(s) · {runResult.execution_time_ms} ms
                      </p>
                      <table className="mt-2 w-full border-collapse text-xs">
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
                className="mt-1 w-full rounded border border-gray-300 p-2 text-sm"
                placeholder="Explain the concept clearly…"
              />
            </label>
          )}

          <div className="mt-5 flex items-center justify-between">
            <button
              type="button"
              onClick={submit}
              disabled={submitting}
              className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {submitting ? 'Submitting…' : 'Submit answer'}
            </button>
            <p className="text-xs text-gray-400">
              Empty answers count as unanswered (0 pts).
            </p>
          </div>
        </section>
      )}

      <div className="flex justify-end">
        {confirmFinish ? (
          <span className="flex items-center gap-2">
            <span className="text-sm text-gray-600">Submit the whole assessment?</span>
            <button
              type="button"
              onClick={() => finish()}
              className="rounded bg-red-600 px-3 py-1 text-sm text-white hover:bg-red-700"
            >
              Yes, finish
            </button>
            <button
              type="button"
              onClick={() => setConfirmFinish(false)}
              className="rounded border border-gray-300 px-3 py-1 text-sm text-gray-700"
            >
              Keep going
            </button>
          </span>
        ) : (
          <button
            type="button"
            onClick={() => setConfirmFinish(true)}
            className="rounded border border-red-300 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-50"
          >
            Finish assessment
          </button>
        )}
      </div>
    </div>
  )
}
