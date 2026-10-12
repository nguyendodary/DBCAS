import { t, useLocale, message, number, percent, dateTime, time, dateOnly, intlLocale } from '../i18n'
import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api, { apiMessage } from '../api'
import { ActionSpinner, EmptyState, ErrorState, Loading } from '../components/States'
import { Badge, Card, Icon, PageHeader, btnGhost, btnPrimary } from '../components/ui'

// UC12 — pick an active assessment and start (or resume) an adaptive session.
export default function AssessmentsPage() {
  useLocale()
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
        setError(apiMessage(e, message('assessment.loadError')))
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
      setError(apiMessage(e, message('assessment.startError')))
      setBusyId(null)
    }
  }

  if (error && !items?.length) return <ErrorState message={error} onRetry={load} />
  if (items === null) return <Loading label={t('assessment.loading')} />

  return (
    <div className="space-y-5">
      <PageHeader
        title={t('nav.assessments')}
        subtitle={t('assessment.intro')}
      />
      {error && <ErrorState message={error} onRetry={load} />}

      {items.length === 0 ? (
        <EmptyState title={t('assessment.empty')}>{t('assessment.emptyBody')}</EmptyState>
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
              <li key={a.assessment_id} className="border-l-2 border-l-transparent p-4 transition-colors hover:border-l-cyan-400/50 hover:bg-elev/40 sm:px-5 sm:py-5">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2.5">
                      <h2 className="text-base font-semibold tracking-tight text-ink">{a.title}</h2>
                      {live ? <Badge tone="blue">{t('assessment.inProgress')}</Badge> : completed ? <Badge tone="green">{t('assessment.completedBefore')}</Badge> : <Badge>{t('assessment.ready')}</Badge>}
                    </div>
                    {a.description && <p className="mt-1 text-sm leading-relaxed text-mute">{a.description}</p>}
                    <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-sub">
                      <span className="inline-flex items-center gap-1.5"><Icon name="clock" className="h-3.5 w-3.5 text-mute" />{t('assessment.duration', { value: number(a.duration_min) })}</span>
                      <span className="inline-flex items-center gap-1.5"><Icon name="list" className="h-3.5 w-3.5 text-mute" />{t('assessment.maxQuestions', { value: number(a.max_questions) })}</span>
                      <span className="inline-flex items-center gap-1.5"><Icon name="target" className="h-3.5 w-3.5 text-mute" />{t('assessment.conceptCount', { count: a.concept_count })}</span>
                    </div>
                    {live && <div className="mt-3 max-w-sm">
                      <div className="flex justify-between text-xs text-mute"><span>{t('assessment.progress')}</span><span>{t('assessment.answeredProgress', { answered: number(live.answered_count), max: number(a.max_questions) })}</span></div>
                      <div className="mt-1 h-1.5 rounded-full bg-elev" role="progressbar" aria-label={t('assessment.progressLabel', { title: a.title })} aria-valuemin={0} aria-valuemax={a.max_questions} aria-valuenow={live.answered_count}>
                        <div className="h-full rounded-full bg-cyan-400" style={{ width: `${progress}%` }} />
                      </div>
                    </div>}
                  </div>
                  <div className="flex flex-wrap gap-2 lg:justify-end">
                    {completed && !live && <Link to={`/history/${completed.session_id}`} className={btnGhost}>{t('assessment.viewResult')}</Link>}
                    <button
                      type="button"
                      onClick={() => (live ? navigate(`/exam/${live.session_id}`) : start(a.assessment_id))}
                      disabled={busyId === a.assessment_id}
                      className={completed && !live ? btnGhost : btnPrimary}
                    >
                      {busyId === a.assessment_id ? <ActionSpinner /> : <Icon name="play" className="h-3.5 w-3.5" />}
                      {live ? t('assessment.resume') : busyId === a.assessment_id ? t('assessment.starting') : completed ? t('assessment.startAgain') : t('assessment.start')}
                    </button>
                  </div>
                </div>
              </li>
            )
          })}
          </ul>
        </Card>
      )}

      <p className="text-sm text-mute">{t('assessment.pastSessions')}{' '}
        <Link to="/history" className="text-cyan-300 hover:underline">{t('assessment.historyLink')}</Link>
        .
      </p>
    </div>
  )
}
