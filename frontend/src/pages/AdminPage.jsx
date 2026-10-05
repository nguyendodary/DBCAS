import { useEffect, useState } from 'react'
import api, { apiMessage } from '../api'
import { CompetencyRadar } from '../components/CompetencyCharts'
import { EmptyState, ErrorState, Loading } from '../components/States'

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
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Cohort Overview</h1>
        <p className="text-sm text-gray-500">
          Class-wide competency and below-benchmark prevalence.
        </p>
      </div>

      <section
        aria-label="Cohort summary"
        className="grid gap-4 sm:grid-cols-3"
      >
        <StatCard label="Learners assessed" value={cohort.learner_count} />
        <StatCard label="Finalized sessions" value={cohort.finalized_sessions} />
        <StatCard label="Concepts assessed" value={cohort.concepts.length} />
      </section>

      <section aria-label="Cohort gap analytics" className="rounded-lg border bg-white">
        <h2 className="border-b px-4 py-3 text-sm font-semibold text-gray-800">
          Concepts where learners fall below the benchmark
        </h2>
        {!cohort.concepts.length ? (
          <div className="p-4">
            <EmptyState title="No assessed concepts yet" />
          </div>
        ) : (
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
                    <span
                      className={
                        c.below_target_count > 0
                          ? 'rounded bg-red-50 px-2 py-0.5 text-xs text-red-700'
                          : 'rounded bg-green-50 px-2 py-0.5 text-xs text-green-700'
                      }
                    >
                      {c.gap_rate_pct}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section aria-label="Learner drill-down" className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-lg border bg-white">
          <h2 className="border-b px-4 py-3 text-sm font-semibold text-gray-800">
            Learners
          </h2>
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
                    className={`w-full px-4 py-2 text-left text-sm hover:bg-blue-50 ${
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
        </div>

        <div className="rounded-lg border bg-white p-4">
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
                  className="rounded border border-gray-300 px-2 py-1 text-sm"
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
        </div>
      </section>
    </div>
  )
}

function StatCard({ label, value }) {
  return (
    <div className="rounded-lg border bg-white p-4">
      <p className="text-2xl font-semibold text-gray-900">{value}</p>
      <p className="text-sm text-gray-500">{label}</p>
    </div>
  )
}
