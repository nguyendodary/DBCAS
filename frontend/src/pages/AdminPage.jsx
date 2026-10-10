import { useEffect, useState } from 'react'
import api, { apiMessage } from '../api'
import AdminNav from '../components/AdminNav'
import { CompetencyRadar } from '../components/CompetencyCharts'
import { EmptyState, ErrorState, Loading } from '../components/States'
import { Badge, Card, CardTitle, PageHeader, StatCard } from '../components/ui'

// UC20 / Admin story 9 — cohort-wide gap analytics plus a per-learner
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

  useEffect(() => {
    let cancelled = false
    Promise.all([api.get('/admin/analytics/cohort'), api.get('/admin/learners')])
      .then(([c, l]) => {
        if (cancelled) return
        setCohort(c.data)
        setLearners(l.data)
      })
      .catch((err) => !cancelled && setError(apiMessage(err)))
    return () => {
      cancelled = true
    }
  }, [])

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
        const latestFinal = (r.data.sessions || []).find(
          (s) => s.status === 'completed' || s.status === 'timed_out'
        )
        if (latestFinal) setSessionId(latestFinal.session_id)
      })
      .catch((err) => !cancelled && setDetailError(apiMessage(err)))
    return () => {
      cancelled = true
    }
  }, [selected])

  useEffect(() => {
    if (!sessionId) return
    let cancelled = false
    api
      .get(`/admin/sessions/${sessionId}/competency`)
      .then((r) => !cancelled && setProfile(r.data))
      .catch((err) => !cancelled && setDetailError(apiMessage(err)))
    return () => {
      cancelled = true
    }
  }, [sessionId])

  if (error) return <ErrorState message={error} />
  if (!cohort || !learners) return <Loading label="Loading cohort analytics…" />

  return (
    <div className="space-y-6">
      <AdminNav />
      <PageHeader
        title="Cohort Overview"
        subtitle="Class-wide competency and below-benchmark prevalence."
      />

      <section
        aria-label="Cohort summary"
        className="grid gap-4 sm:grid-cols-3"
      >
        <StatCard label="Learners assessed" value={cohort.learner_count} icon="users" />
        <StatCard label="Finalized sessions" value={cohort.finalized_sessions} icon="check" />
        <StatCard label="Concepts assessed" value={cohort.concepts.length} icon="book" />
      </section>

      <section aria-label="Cohort gap analytics">
        <Card className="overflow-hidden">
          <CardTitle title="Concepts where learners fall below the benchmark" />
          {!cohort.concepts.length ? (
            <div className="p-4">
              <EmptyState title="No assessed concepts yet" />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b bg-gray-50 text-xs uppercase text-gray-500">
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
                    <tr key={c.concept_id} className="border-b last:border-0">
                      <td className="px-4 py-2 font-medium text-gray-800">
                        {c.concept_name}
                      </td>
                      <td className="px-4 py-2 text-gray-600">{c.subject_area}</td>
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
            </div>
          )}
        </Card>
      </section>

      <section aria-label="Learner drill-down" className="grid gap-6 lg:grid-cols-2">
        <Card className="overflow-hidden">
          <CardTitle title="Learners" />
          {!learners.length ? (
            <div className="p-4">
              <EmptyState title="No learners registered yet" />
            </div>
          ) : (
            <ul className="divide-y">
              {learners.map((l) => (
                <li key={l.account_id}>
                  <button
                    type="button"
                    onClick={() => setSelected(l.account_id)}
                    className={`w-full px-4 py-2.5 text-left text-sm transition-colors hover:bg-blue-50 ${
                      selected === l.account_id ? 'bg-blue-50' : ''
                    }`}
                  >
                    <span className="font-medium text-gray-800">
                      {l.full_name || l.email}
                    </span>
                    <span className="ml-2 text-gray-500">{l.email}</span>
                    <span className="float-right text-gray-500">
                      {l.sessions_completed} completed
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card className="p-4">
          <h2 className="mb-3 text-sm font-semibold text-gray-800">
            Individual learner profile
          </h2>
          {!selected && (
            <EmptyState title="Select a learner to view their competency profile" />
          )}
          {detailError && <ErrorState message={detailError} />}
          {selected && !learnerDetail && !detailError && (
            <Loading label="Loading learner…" />
          )}
          {learnerDetail && (
            <>
              <label className="mb-3 block text-sm text-gray-700">
                Assessment session{' '}
                <select
                  aria-label="Select learner session"
                  value={sessionId ?? ''}
                  onChange={(e) => setSessionId(Number(e.target.value))}
                  className="rounded-md border border-gray-300 px-2 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
                >
                  {learnerDetail.sessions
                    .filter(
                      (s) => s.status === 'completed' || s.status === 'timed_out'
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
              {!learnerDetail.sessions.length && (
                <EmptyState title="This learner has no sessions yet" />
              )}
              {profile?.concepts?.length ? (
                <div className="h-72">
                  <CompetencyRadar concepts={profile.concepts} />
                </div>
              ) : learnerDetail.sessions.length && sessionId ? (
                <Loading label="Loading competency…" />
              ) : null}
            </>
          )}
        </Card>
      </section>
    </div>
  )
}
