import { useEffect, useState } from 'react'
import api, { apiMessage } from '../api'
import { CompetencyBar, CompetencyConceptBars, CompetencyRadar, ResultTrend } from '../components/CompetencyCharts'
import { EmptyState, ErrorState, Loading } from '../components/States'
import { Badge, Card, CardTitle, PageHeader, StatCard, selectCls } from '../components/ui'

// UC11 / Admin story 9 — cohort-wide gap analytics plus a per-learner
// drill-down that reuses the same deterministic competency profile the
// learner sees. All aggregation happens server-side.
export default function AdminPage() {
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
  if (!cohort || !learners) return <Loading label="Loading cohort analytics…" />

  return (
    <div className="space-y-6">
      <PageHeader
        title="Cohort Overview"
        subtitle="Class-wide competency and below-benchmark prevalence."
      >
        <label className="block text-sm text-sub">Assessment
          <select aria-label="Analytics assessment" value={assessmentId} onChange={(e) => setAssessmentId(e.target.value)} className={`mt-1 block w-full sm:w-auto ${selectCls}`}>
            <option value="">All assessments</option>
            {assessments.map((a) => <option key={a.assessment_id} value={a.assessment_id}>{a.title} · v{a.version_no || 1}</option>)}
          </select>
        </label>
      </PageHeader>
      <p className="text-xs text-mute">Cohort means all learners assessed in the selected assessment. Select a learner below for individual results.</p>

      <section
        aria-label="Cohort summary"
        className="grid gap-4 sm:grid-cols-3"
      >
        <StatCard label="Learners assessed" value={cohort.learner_count} icon="users" />
        <StatCard label="Finalized sessions" value={cohort.finalized_sessions} icon="check" />
        <StatCard label="Concepts assessed" value={cohort.concepts.length} icon="book" />
      </section>

      <Card className="min-w-0 p-4">
        <h2 className="text-sm font-semibold text-ink">Result trend</h2>
        <p className="mt-1 text-xs text-mute">Daily mean of fully graded answer results; pending sessions are excluded from the mean.</p>
        {cohort.trend?.length ? <div className="relative mt-4 h-64 min-w-0"><ResultTrend points={cohort.trend} /></div> : <EmptyState title="No finalized results for this selection" />}
      </Card>

      <section aria-label="Cohort gap analytics">
        <Card className="overflow-hidden">
          <CardTitle title="Concept performance across the cohort" />
          {!cohort.concepts.length ? (
            <div className="p-4">
              <EmptyState title="No assessed concepts yet" />
            </div>
          ) : (
            <><p className="px-4 pt-3 text-xs text-mute sm:hidden">Swipe the table to see all columns.</p>
            <div className="overflow-x-auto" role="region" aria-label="Cohort gap table" tabIndex={0}>
              <table className="data-table min-w-[760px]">
                <thead>
                  <tr>
                    <th className="px-4 py-2">Concept</th>
                    <th className="px-4 py-2">Subject area</th>
                    <th className="px-4 py-2 text-right">Learners</th>
                    <th className="px-4 py-2 text-right">Avg competency</th>
                    <th className="px-4 py-2 text-right">Below benchmark</th>
                    <th className="px-4 py-2 text-right">Gap rate</th>
                  </tr>
                </thead>
                <tbody>
                  {cohort.concepts.map((c) => (
                    <tr key={c.concept_id}>
                      <td className="px-4 py-2 font-medium text-ink">
                        {c.concept_name}
                      </td>
                      <td className="px-4 py-2 text-sub">{c.subject_area}</td>
                      <td className="px-4 py-2 text-right">{c.learners_assessed}</td>
                      <td className="px-4 py-2 text-right">{c.avg_competency_pct}%</td>
                      <td className="px-4 py-2 text-right">{c.below_target_count}</td>
                      <td className="px-4 py-2 text-right">
                        <Badge tone={c.below_target_count > 0 ? 'red' : 'green'}>
                          {c.gap_rate_pct}%
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

      <section aria-label="Learner drill-down" className="grid min-w-0 gap-6 lg:grid-cols-2">
        <Card className="overflow-hidden">
          <CardTitle title="Learners" />
          {!learners.length ? (
            <div className="p-4">
              <EmptyState title="No learners registered yet" />
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
                      {l.sessions_completed} finalized · {l.status || 'active'}
                      {l.last_activity && <span className="block">Last activity {new Date(l.last_activity).toLocaleString()}</span>}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card className="min-w-0 p-4">
          <h2 className="mb-3 text-sm font-semibold text-ink">
            Individual learner profile
          </h2>
          {!selected && (
            <EmptyState title="Select a learner to view their competency profile" />
          )}
          {detailError && <ErrorState message={detailError} onRetry={() => setRetry((r) => r + 1)} />}
          {selected && !learnerDetail && !detailError && (
            <Loading label="Loading learner…" />
          )}
          {learnerDetail && (
            <>
              <label className="mb-3 block text-sm text-sub">
                Assessment session{' '}
                <select
                  aria-label="Select learner session"
                  value={sessionId ?? ''}
                  onChange={(e) => setSessionId(Number(e.target.value))}
                  className="block max-w-full rounded-md border border-edge2 px-2 py-1.5 text-sm focus:border-cyan-400/60 focus:outline-none"
                >
                  {learnerDetail.sessions
                    .filter(
                      (s) => (s.status === 'completed' || s.status === 'timed_out') && (!assessmentId || s.assessment_id === Number(assessmentId))
                    )
                    .map((s) => (
                      <option key={s.session_id} value={s.session_id}>
                        {s.assessment_title || `Assessment ${s.assessment_id}`} —{' '}
                        {new Date(
                          s.submitted_at || s.started_at
                        ).toLocaleString()}
                      </option>
                    ))}
                </select>
              </label>
              {!sessionId && (
                <EmptyState title="No finalized learner sessions for this selection" />
              )}
              {profile?.concepts?.length ? (
                <div className="relative h-72 min-w-0 w-full">
                  {profile.concepts.length < 3 ? <CompetencyConceptBars concepts={profile.concepts} /> : <CompetencyRadar concepts={profile.concepts} />}
                </div>
              ) : profile && !detailError ? <EmptyState title="No graded concept evidence for this session" /> : sessionId && !detailError ? (
                <Loading label="Loading competency…" />
              ) : null}
              {profile?.categories?.length > 0 && <><p className="mt-5 text-xs text-mute">Subject-area display average of assessed concept percentages.</p><div className="relative mt-2 h-64 min-w-0"><CompetencyBar categories={profile.categories} /></div></>}
              {sessionId && learnerDetail.sessions.find((s) => s.session_id === sessionId)?.concepts?.length > 0 && <ul aria-label="Learner session results" className="mt-4 space-y-1 text-sm text-sub">
                {learnerDetail.sessions.find((s) => s.session_id === sessionId).concepts.map((c) => <li key={c.concept_id}>{c.concept_name}: {c.competency_pct}%</li>)}
              </ul>}
            </>
          )}
        </Card>
      </section>
    </div>
  )
}
