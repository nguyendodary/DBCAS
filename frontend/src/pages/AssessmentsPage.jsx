import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api, { apiMessage } from '../api'
import { ActionSpinner, EmptyState, ErrorState, Loading } from '../components/States'
import { Badge, Card, Icon, PageHeader, btnGhost, btnPrimary } from '../components/ui'

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

  if (error && !items?.length) return <ErrorState message={error} onRetry={load} />
  if (items === null) return <Loading label="Loading assessments…" />

  return (
    <div className="space-y-5">
      <PageHeader
        title="Assessments"
        subtitle="Choose an assessment to begin. Questions adapt as you progress, with one question served at a time."
      />
      {error && <ErrorState message={error} onRetry={load} />}

      {items.length === 0 ? (
        <EmptyState title="No assessments available">
          Check back later — your administrator has not activated an
          assessment yet.
        </EmptyState>
      ) : (
        <Card className="overflow-hidden">
          <ul className="divide-y divide-edge/70">
          {items.map((a) => {
            const related = sessions.filter((s) => s.assessment_id === a.assessment_id)
              .sort((left, right) => new Date(right.started_at) - new Date(left.started_at))
            const live = related.find((s) => s.status === 'in_progress')
            const completed = related.find((s) => s.status === 'completed' || s.status === 'timed_out')
            const progress = live && a.max_questions ? Math.min(100, Math.round((live.answered_count / a.max_questions) * 100)) : 0
            return (
              <li key={a.assessment_id} className="p-4 transition-colors hover:bg-white/[0.025] sm:px-5 sm:py-5">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2.5">
                      <h2 className="text-base font-semibold tracking-tight text-ink">{a.title}</h2>
                      {live ? <Badge tone="blue">In progress</Badge> : completed ? <Badge tone="green">Completed before</Badge> : <Badge>Ready to start</Badge>}
                    </div>
                    {a.description && <p className="mt-1 text-sm leading-relaxed text-mute">{a.description}</p>}
                    <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-sub">
                      <span className="inline-flex items-center gap-1.5"><Icon name="clock" className="h-3.5 w-3.5 text-mute" />{a.duration_min} min</span>
                      <span className="inline-flex items-center gap-1.5"><Icon name="list" className="h-3.5 w-3.5 text-mute" />Up to {a.max_questions} questions</span>
                      <span className="inline-flex items-center gap-1.5"><Icon name="target" className="h-3.5 w-3.5 text-mute" />{a.concept_count} concept{a.concept_count === 1 ? '' : 's'}</span>
                    </div>
                    {live && <div className="mt-3 max-w-sm">
                      <div className="flex justify-between text-xs text-mute"><span>Progress</span><span>{live.answered_count} of up to {a.max_questions} answered</span></div>
                      <div className="mt-1 h-1.5 rounded-full bg-elev" role="progressbar" aria-label={`${a.title} progress`} aria-valuemin={0} aria-valuemax={a.max_questions} aria-valuenow={live.answered_count}>
                        <div className="h-full rounded-full bg-cyan-400" style={{ width: `${progress}%` }} />
                      </div>
                    </div>}
                  </div>
                  <div className="flex flex-wrap gap-2 lg:justify-end">
                    {completed && !live && <Link to={`/history/${completed.session_id}`} className={btnGhost}>View result</Link>}
                    <button
                      type="button"
                      onClick={() => (live ? navigate(`/exam/${live.session_id}`) : start(a.assessment_id))}
                      disabled={busyId === a.assessment_id}
                      className={completed && !live ? btnGhost : btnPrimary}
                    >
                      {busyId === a.assessment_id ? <ActionSpinner /> : <Icon name="play" className="h-3.5 w-3.5" />}
                      {live ? 'Resume' : busyId === a.assessment_id ? 'Starting…' : completed ? 'Start again' : 'Start'}
                    </button>
                  </div>
                </div>
              </li>
            )
          })}
          </ul>
        </Card>
      )}

      <p className="text-sm text-mute">
        Past sessions are on the{' '}
        <Link to="/history" className="text-cyan-300 hover:underline">
          history page
        </Link>
        .
      </p>
    </div>
  )
}
