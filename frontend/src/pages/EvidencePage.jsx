import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api, { apiMessage } from '../api'
import { EmptyState, ErrorState, Loading } from '../components/States'

function AnswerBlock({ item }) {
  if (item.question_type === 'mcq') {
    const chosen = item.options.find((o) => o.option_id === item.selected_option_id)
    return (
      <div className="mt-2 space-y-1 text-sm">
        {item.options.map((o) => (
          <p
            key={o.option_id}
            className={
              o.option_id === item.selected_option_id
                ? o.is_correct
                  ? 'font-medium text-green-700'
                  : 'font-medium text-red-700'
                : o.is_correct
                  ? 'text-green-700'
                  : 'text-gray-500'
            }
          >
            {o.option_label}. {o.option_text}
            {o.option_id === item.selected_option_id && ' (your answer)'}
            {o.is_correct && ' ✓'}
          </p>
        ))}
        {!chosen && <p className="text-gray-500">No answer submitted.</p>}
      </div>
    )
  }
  if (item.question_type === 'sql') {
    return (
      <pre className="mt-2 overflow-x-auto rounded bg-gray-50 p-2 text-xs text-gray-700">
        {item.sql_answer || '— no answer submitted —'}
      </pre>
    )
  }
  return (
    <p className="mt-2 whitespace-pre-wrap rounded bg-gray-50 p-2 text-sm text-gray-700">
      {item.essay_answer || '— no answer submitted —'}
    </p>
  )
}

// UC18 — the evidence record of one finalized session.
export default function EvidencePage() {
  const { sessionId } = useParams()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  const load = useCallback(() => {
    setError(null)
    api
      .get(`/sessions/${sessionId}/evidence`)
      .then((r) => setData(r.data))
      .catch((e) => setError(apiMessage(e, 'Could not load the evidence record')))
  }, [sessionId])

  useEffect(load, [load])

  if (error) return <ErrorState message={error} onRetry={load} />
  if (!data) return <Loading label="Loading evidence…" />

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">
          Evidence — session #{data.session_id}
        </h1>
        <span className="rounded bg-gray-100 px-2 py-1 text-xs font-medium text-gray-600">
          {data.status.replace('_', ' ')}
        </span>
      </div>
      {data.items.length === 0 ? (
        <EmptyState title="No questions were served in this session" />
      ) : (
        <ol className="space-y-4">
          {data.items.map((item) => (
            <li key={item.attempt_id} className="rounded-md border bg-white p-4">
              <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500">
                <span className="font-medium text-gray-700">Q{item.seq_no}</span>
                <span className="rounded bg-gray-100 px-2 py-0.5 uppercase">
                  {item.question_type}
                </span>
                <span className="rounded bg-gray-100 px-2 py-0.5">
                  difficulty {item.difficulty_level}
                </span>
                {item.concepts.map((c) => (
                  <span
                    key={c.concept_id}
                    className="rounded bg-blue-50 px-2 py-0.5 text-blue-700"
                  >
                    {c.concept_name}
                  </span>
                ))}
                <span className="ml-auto font-medium">
                  {item.score === null ? 'not graded' : `${item.score} / ${item.points} pts`}
                </span>
              </div>
              <p className="mt-2 text-sm text-gray-900">{item.prompt}</p>
              <AnswerBlock item={item} />
              {item.grading_detail?.feedback && (
                <p className="mt-2 text-sm text-gray-600">
                  <span className="font-medium">Feedback: </span>
                  {item.grading_detail.feedback}
                </p>
              )}
              <p className="mt-2 text-xs text-gray-400">
                served {new Date(item.served_at).toLocaleTimeString()}
                {item.submitted_at &&
                  ` · answered ${new Date(item.submitted_at).toLocaleTimeString()}`}
              </p>
            </li>
          ))}
        </ol>
      )}
      <p className="text-sm">
        <Link to="/history" className="text-blue-600 hover:underline">
          ← Back to history
        </Link>
      </p>
    </div>
  )
}
