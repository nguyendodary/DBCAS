import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api, { apiMessage } from '../api'
import { EmptyState, ErrorState, Loading } from '../components/States'

// UC12 — pick an active assessment and start (or resume) an adaptive session.
export default function AssessmentsPage() {
  const [items, setItems] = useState(null)
  const [sessions, setSessions] = useState([])
  const [error, setError] = useState(null)
  const [busyId, setBusyId] = useState(null)
  const navigate = useNavigate()

  const load = useCallback(() => {
    setError(null)
    Promise.all([api.get('/assessments'), api.get('/sessions')])
      .then(([a, s]) => {
        setItems(a.data)
        setSessions(s.data)
      })
      .catch((e) => {
        setError(apiMessage(e, 'Could not load assessments'))
        setItems([])
      })
  }, [])

  useEffect(load, [load])

  async function start(assessmentId) {
    setBusyId(assessmentId)
    try {
      const r = await api.post(`/assessments/${assessmentId}/sessions`)
      navigate(`/exam/${r.data.session_id}`)
    } catch (e) {
      setError(apiMessage(e, 'Could not start the assessment'))
      setBusyId(null)
    }
  }

  if (error) return <ErrorState message={error} onRetry={load} />
  if (items === null) return <Loading label="Loading assessments…" />

  const liveByAssessment = Object.fromEntries(
    sessions.filter((s) => s.status === 'in_progress').map((s) => [s.assessment_id, s])
  )

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Take an assessment</h1>
        <p className="mt-1 text-sm text-gray-500">
          Each session is adaptive: it opens with three basic questions, then
          adjusts difficulty and probes weak or uncovered concepts based on
          your answers. Up to 13 questions within the time limit.
        </p>
      </div>

      {items.length === 0 ? (
        <EmptyState title="No assessments available">
          Check back later — your administrator has not activated an
          assessment yet.
        </EmptyState>
      ) : (
        <ul className="space-y-3">
          {items.map((a) => {
            const live = liveByAssessment[a.assessment_id]
            return (
              <li
                key={a.assessment_id}
                className="flex items-center justify-between rounded-md border bg-white p-4"
              >
                <div>
                  <p className="font-medium text-gray-900">{a.title}</p>
                  {a.description && (
                    <p className="mt-0.5 text-sm text-gray-500">{a.description}</p>
                  )}
                  <p className="mt-1 text-xs text-gray-500">
                    Up to {a.max_questions} questions · {a.duration_min} minutes ·{' '}
                    {a.concept_count} concept{a.concept_count === 1 ? '' : 's'}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => (live ? navigate(`/exam/${live.session_id}`) : start(a.assessment_id))}
                  disabled={busyId === a.assessment_id}
                  className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  {live ? 'Resume' : busyId === a.assessment_id ? 'Starting…' : 'Start'}
                </button>
              </li>
            )
          })}
        </ul>
      )}

      <p className="text-sm text-gray-500">
        Past sessions are on the{' '}
        <Link to="/history" className="text-blue-600 hover:underline">
          history page
        </Link>
        .
      </p>
    </div>
  )
}
