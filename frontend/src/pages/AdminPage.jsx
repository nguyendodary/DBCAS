import { t, useLocale, message, number, percent, dateTime, statusLabel, typeLabel, validationError, resources } from '../i18n'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api, { apiMessage } from '../api'
import { CompetencyBar, CompetencyConceptBars, CompetencyRadar, ResultTrend } from '../components/CompetencyCharts'
import { EmptyState, ErrorState, Loading } from '../components/States'
import { Badge, Card, CardTitle, StatTile, selectCls } from '../components/ui'
import { AdminPageHeader } from '../components/admin'

// UC11 / Admin story 9 — cohort-wide gap analytics plus a per-learner
// drill-down that reuses the same deterministic competency profile the
// learner sees. All aggregation happens server-side.
export default function AdminPage() {
  useLocale()
  const [cohort, setCohort] = useState(null)
  const [learners, setLearners] = useState(null)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState(null) // learner account_id
  const [learnerDetail, setLearnerDetail] = useState(null)
  const [sessionId, setSessionId] = useState(null)
  const [profile, setProfile] = useState(null)
  const [detailError, setDetailError] = useState('')
  const [assessments, setAssessments] = useState([])
  const [assessmentId, setAssessmentId] = useState('')
  const [retry, setRetry] = useState(0)

  useEffect(() => {
    let cancelled = false
    setError('')
    setCohort(null)
    Promise.all([
      api.get('/admin/analytics/cohort', { params: assessmentId ? { assessment_id: Number(assessmentId) } : {} }),
      api.get('/admin/learners'), api.get('/admin/assessments'),
    ])
      .then(([c, l, a]) => {
        if (cancelled) return
        setCohort(c.data)
        setLearners(l.data)
        setAssessments(a.data)
      })
      .catch((err) => !cancelled && setError(apiMessage(err)))
    return () => {
      cancelled = true
    }
  }, [assessmentId, retry])

  useEffect(() => {
    if (!selected) return
    let cancelled = false
    setLearnerDetail(null)
    setProfile(null)
    setSessionId(null)
    setDetailError('')
    api
      .get(`/admin/learners/${selected}/sessions`)
      .then((r) => {
        if (cancelled) return
        setLearnerDetail(r.data)
        const latestFinal = (r.data.sessions || []).find((s) =>
          (s.status === 'completed' || s.status === 'timed_out') && (!assessmentId || s.assessment_id === Number(assessmentId)))
        if (latestFinal) setSessionId(latestFinal.session_id)
      })
      .catch((err) => !cancelled && setDetailError(apiMessage(err)))
    return () => {
      cancelled = true
    }
  }, [selected, assessmentId, retry])

  useEffect(() => {
    if (!sessionId) return
    let cancelled = false
    setProfile(null)
    setDetailError('')
    api
      .get(`/admin/sessions/${sessionId}/competency`)
      .then((r) => !cancelled && setProfile(r.data))
      .catch((err) => !cancelled && setDetailError(apiMessage(err)))
    return () => {
      cancelled = true
    }
  }, [sessionId, retry])

  if (error) return <ErrorState message={error} onRetry={() => setRetry((r) => r + 1)} />
  if (!cohort || !learners) return <Loading label={t('admin.analytics.loading')} />

  return (
    <div className="space-y-6">
      <AdminPageHeader
        title={t('admin.analytics.title')}
        subtitle={t('admin.analytics.subtitle')}
      >
        <label className="block min-w-0 max-w-full text-sm text-sub">{t('admin.analytics.assessment')}<select aria-label={t('admin.analytics.selector')} value={assessmentId} onChange={(e) => setAssessmentId(e.target.value)} className={`mt-1 block w-full max-w-full min-w-0 sm:max-w-[26rem] ${selectCls}`}>
            <option value="">{t('admin.analytics.all')}</option>
            {assessments.map((a) => <option key={a.assessment_id} value={a.assessment_id}>{t('admin.analytics.version', { title: a.title, version: a.version_no || 1 })}</option>)}
          </select>
        </label>
      </AdminPageHeader>
      <p className="text-xs text-mute">{t('admin.analytics.scope')}</p>

      <section
        aria-label={t('admin.analytics.summary')}
        className="grid gap-4 sm:grid-cols-3"
      >
        <StatTile label={t('admin.analytics.learnersAssessed')} value={number(cohort.learner_count)} icon="users" tone="cyan" />
        <StatTile label={t('admin.analytics.finalized')} value={number(cohort.finalized_sessions)} icon="check" tone="green" />
        <StatTile label={t('admin.analytics.conceptsAssessed')} value={number(cohort.concepts.length)} icon="book" tone="violet" />
      </section>

      <Card className="min-w-0 p-4">
        <h2 className="text-sm font-semibold text-ink">{t('admin.analytics.trend')}</h2>
        <p className="mt-1 text-xs text-mute">{t('admin.analytics.trendHelp')}</p>
        {cohort.trend?.length ? <div className="relative mt-4 h-64 min-w-0"><ResultTrend points={cohort.trend} /></div> : <EmptyState title={t('admin.analytics.noResults')} />}
      </Card>

      <section aria-label={t('admin.analytics.gaps')}>
        <Card className="overflow-hidden">
          <CardTitle title={t('admin.analytics.performance')} />
          {!cohort.concepts.length ? (
            <div className="p-4">
              <EmptyState title={t('admin.analytics.noConcepts')} />
            </div>
          ) : (
            <><p className="px-4 pt-3 text-xs text-mute sm:hidden">{t('common.swipeTable')}</p>
            <div className="overflow-x-auto" role="region" aria-label={t('admin.analytics.gapTable')} tabIndex={0}>
              <table className="data-table min-w-[760px]">
                <thead>
                  <tr>
                    <th className="px-4 py-2">{t('common.concept')}</th>
                    <th className="px-4 py-2">{t('common.subjectArea')}</th>
                    <th className="px-4 py-2 text-right">{t('admin.analytics.learners')}</th>
                    <th className="px-4 py-2 text-right">{t('admin.analytics.average')}</th>
                    <th className="px-4 py-2 text-right">{t('admin.analytics.below')}</th>
                    <th className="px-4 py-2 text-right">{t('admin.analytics.gapRate')}</th>
                  </tr>
                </thead>
                <tbody>
                  {cohort.concepts.map((c) => (
                    <tr key={c.concept_id}>
                      <td className="px-4 py-2 font-medium text-ink">
                        {c.concept_name}
                      </td>
                      <td className="px-4 py-2 text-sub">{c.subject_area}</td>
                      <td className="px-4 py-2 text-right">{number(c.learners_assessed)}</td>
                      <td className="px-4 py-2 text-right">{percent(c.avg_competency_pct, { minimumFractionDigits: 2 })}</td>
                      <td className="px-4 py-2 text-right">{number(c.below_target_count)}</td>
                      <td className="px-4 py-2 text-right">
                        <Badge tone={c.below_target_count > 0 ? 'red' : 'green'}>
                          {percent(c.gap_rate_pct, { minimumFractionDigits: 2 })}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div></>
          )}
        </Card>
      </section>

      <section aria-label={t('admin.analytics.drilldown')} className="grid min-w-0 gap-6 lg:grid-cols-2">
        <Card className="overflow-hidden">
          <CardTitle title={t('admin.analytics.learners')} />
          {!learners.length ? (
            <div className="p-4">
              <EmptyState title={t('admin.analytics.noLearners')} />
            </div>
          ) : (
            <ul className="divide-y divide-edge">
              {learners.map((l) => (
                <li key={l.account_id}>
                  <button
                    type="button"
                    onClick={() => setSelected(l.account_id)}
                    className={`flex w-full flex-wrap items-center justify-between gap-1 px-4 py-3 text-left text-sm hover:bg-cyan-400/[0.06] ${
                      selected === l.account_id ? 'bg-cyan-400/[0.08] border-l-2 border-cyan-400' : 'border-l-2 border-transparent'
                    }`}
                  >
                    <span className="min-w-0"><span className="block font-medium text-ink">{l.full_name || l.email}</span><span className="block truncate text-xs text-mute">{l.email}</span></span>
                    <span className="text-xs text-mute">
                      {t('admin.analytics.finalizedStatus', { count: l.sessions_completed, status: statusLabel(l.status || 'active') })}
                      {l.last_activity && <span className="block">{t('admin.analytics.lastActivity', { date: dateTime(l.last_activity) })}</span>}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card className="min-w-0 p-4">
          <h2 className="mb-3 text-sm font-semibold text-ink">{t('admin.analytics.individual')}</h2>
          {selected && <Link className="mb-3 block text-sm text-cyan-300 underline" to={`/admin/learners/${selected}/competency`}>{t('supervisor.cumulative')}</Link>}
          {sessionId && <Link className="mb-3 block text-sm text-cyan-300 underline" to={`/admin/grading/${sessionId}`}>{t('supervisor.reviewTitle')}</Link>}
          {!selected && (
            <EmptyState title={t('admin.analytics.selectLearner')} />
          )}
          {detailError && <ErrorState message={detailError} onRetry={() => setRetry((r) => r + 1)} />}
          {selected && !learnerDetail && !detailError && (
            <Loading label={t('admin.analytics.loadingLearner')} />
          )}
          {learnerDetail && (
            <>
              <label className="mb-3 block text-sm text-sub">
                {t('admin.analytics.selectSession')}{' '}
                <select
                  aria-label={t('admin.analytics.selectSession')}
                  value={sessionId ?? ''}
                  onChange={(e) => setSessionId(Number(e.target.value))}
                  className="block max-w-full rounded-md border border-edge2 bg-panel px-2 py-1.5 text-sm text-ink focus:border-cyan-400/60 focus:outline-none"
                >
                  {learnerDetail.sessions
                    .filter(
                      (s) => (s.status === 'completed' || s.status === 'timed_out') && (!assessmentId || s.assessment_id === Number(assessmentId))
                    )
                    .map((s) => (
                      <option key={s.session_id} value={s.session_id}>
                        {s.assessment_title || t('assessment.number', { id: s.assessment_id })} —{' '}
                        {dateTime(s.submitted_at || s.started_at)}
                      </option>
                    ))}
                </select>
              </label>
              {!sessionId && (
                <EmptyState title={t('admin.analytics.noSessions')} />
              )}
              {profile?.concepts?.length ? (
                <div className="relative h-72 min-w-0 w-full">
                  {profile.concepts.length < 3 ? <CompetencyConceptBars concepts={profile.concepts} /> : <CompetencyRadar concepts={profile.concepts} />}
                </div>
              ) : profile && !detailError ? <EmptyState title={t('admin.analytics.noEvidence')} /> : sessionId && !detailError ? (
                <Loading label={t('admin.analytics.loadingCompetency')} />
              ) : null}
              {profile?.categories?.length > 0 && <><p className="mt-5 text-xs text-mute">{t('admin.analytics.areaHelp')}</p><div className="relative mt-2 h-64 min-w-0"><CompetencyBar categories={profile.categories} /></div></>}
              {sessionId && learnerDetail.sessions.find((s) => s.session_id === sessionId)?.concepts?.length > 0 && <ul aria-label={t('admin.analytics.sessionResults')} className="mt-4 space-y-1 text-sm text-sub">
                {learnerDetail.sessions.find((s) => s.session_id === sessionId).concepts.map((c) => <li key={c.concept_id}>{c.concept_name}: {percent(c.competency_pct, { minimumFractionDigits: 2 })}</li>)}
              </ul>}
            </>
          )}
        </Card>
      </section>
    </div>
  )
}
