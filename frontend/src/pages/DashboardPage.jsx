import { useEffect, useState } from 'react'
import api, { apiMessage } from '../api'
import { CompetencyBar, CompetencyRadar } from '../components/CompetencyCharts'
import { EmptyState, ErrorState, Loading } from '../components/States'

const FINAL_STATES = new Set(['completed', 'timed_out'])

function fmt(dt) {
  return dt ? new Date(dt).toLocaleString() : ''
}

// UC16/FR-13 + DBCAS-24 — the learner's visual competency profile:
// radar + bar charts of backend-computed concept competency, then the
// "What to study next" list (UC17/FR-14). Nothing is recalculated client-side.
export default function DashboardPage() {
  const [sessions, setSessions] = useState(null)
  const [sessionId, setSessionId] = useState(null)
  const [listError, setListError] = useState('')
  const [profile, setProfile] = useState(null)
  const [guidance, setGuidance] = useState(null)
  const [profileState, setProfileState] = useState('idle') // idle|loading|error|ready
  const [profileError, setProfileError] = useState('')

  useEffect(() => {
    let cancelled = false
    api
      .get('/sessions')
      .then((r) => {
        if (cancelled) return
        const list = r.data || []
        setSessions(list)
        const latestFinal = list.find((s) => FINAL_STATES.has(s.status))
        if (latestFinal) setSessionId(latestFinal.session_id)
      })
      .catch((err) => !cancelled && setListError(apiMessage(err)))
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!sessionId) return
    let cancelled = false
    setProfileState('loading')
    setProfileError('')
    Promise.all([
      api.get(`/sessions/${sessionId}/competency`),
      api.get(`/sessions/${sessionId}/guidance`),
    ])
      .then(([comp, guide]) => {
        if (cancelled) return
        setProfile(comp.data)
        setGuidance(guide.data)
        setProfileState('ready')
      })
      .catch((err) => {
        if (cancelled) return
        setProfileError(apiMessage(err))
        setProfileState('error')
      })
    return () => {
      cancelled = true
    }
  }, [sessionId])

  if (listError) return <ErrorState message={listError} />
  if (!sessions) return <Loading label="Loading your sessions…" />

  const finalized = sessions.filter((s) => FINAL_STATES.has(s.status))
  if (!finalized.length) {
    return (
      <EmptyState title="No completed assessments yet">
        Your competency profile appears here after you finish an assessment.
      </EmptyState>
    )
  }

  const concepts = profile?.concepts || []
  const study = guidance?.guidance || []

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">My Competency Profile</h1>
          <p className="text-sm text-gray-500">
            Deterministic per-concept results — points earned ÷ points possible.
          </p>
        </div>
        <label className="text-sm text-gray-700">
          Assessment session{' '}
          <select
            aria-label="Select assessment session"
            value={sessionId ?? ''}
            onChange={(e) => setSessionId(Number(e.target.value))}
            className="rounded border border-gray-300 px-2 py-1 text-sm"
          >
            {finalized.map((s) => (
              <option key={s.session_id} value={s.session_id}>
                {s.assessment_title || `Assessment ${s.assessment_id}`} —{' '}
                {fmt(s.submitted_at || s.started_at)}
              </option>
            ))}
          </select>
        </label>
      </div>

      {profileState === 'loading' && <Loading label="Loading competency profile…" />}
      {profileState === 'error' && <ErrorState message={profileError} />}

      {profileState === 'ready' && !concepts.length && (
        <EmptyState title="No competency data for this session" />
      )}

      {profileState === 'ready' && concepts.length > 0 && (
        <>
          <section
            aria-label="Competency charts"
            className="grid gap-6 md:grid-cols-2"
          >
            <figure className="rounded-lg border bg-white p-4">
              <figcaption className="mb-2 text-sm font-medium text-gray-700">
                Concept mastery vs target
              </figcaption>
              <div className="h-72">
                <CompetencyRadar concepts={concepts} />
              </div>
            </figure>
            <figure className="rounded-lg border bg-white p-4">
              <figcaption className="mb-2 text-sm font-medium text-gray-700">
                By subject area
              </figcaption>
              <div className="h-72">
                <CompetencyBar concepts={concepts} />
              </div>
            </figure>
          </section>

          <section aria-label="Concept scores" className="rounded-lg border bg-white">
            <table className="w-full text-left text-sm">
              <thead className="border-b bg-gray-50 text-xs uppercase text-gray-500">
                <tr>
                  <th className="px-4 py-2">Concept</th>
                  <th className="px-4 py-2">Subject area</th>
                  <th className="px-4 py-2 text-right">Competency</th>
                  <th className="px-4 py-2 text-right">Target</th>
                  <th className="px-4 py-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {concepts.map((c) => (
                  <tr key={c.concept_id} className="border-b last:border-0">
                    <td className="px-4 py-2 font-medium text-gray-800">
                      {c.concept_name}
                    </td>
                    <td className="px-4 py-2 text-gray-600">{c.subject_area}</td>
                    <td className="px-4 py-2 text-right">{c.competency_pct}%</td>
                    <td className="px-4 py-2 text-right">
                      {c.target_pct == null ? '—' : `${c.target_pct}%`}
                    </td>
                    <td className="px-4 py-2">
                      {c.below_target ? (
                        <span className="rounded bg-red-50 px-2 py-0.5 text-xs text-red-700">
                          Below target
                        </span>
                      ) : (
                        <span className="rounded bg-green-50 px-2 py-0.5 text-xs text-green-700">
                          On target
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section aria-label="What to study next">
            <h2 className="mb-2 text-lg font-semibold text-gray-900">
              What to study next
            </h2>
            {!study.length ? (
              <EmptyState title="No gaps — every assessed concept meets its benchmark" />
            ) : (
              <ol className="space-y-3">
                {study.map((g) => (
                  <li
                    key={g.concept_id}
                    className="rounded-lg border bg-white p-4"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="font-medium text-gray-900">
                        {g.priority}. {g.concept_name}
                      </p>
                      <div className="flex items-center gap-2 text-xs">
                        <span className="rounded bg-amber-50 px-2 py-0.5 text-amber-700">
                          {g.shortfall} pts below target
                        </span>
                        {!g.ready && (
                          <span className="rounded bg-gray-100 px-2 py-0.5 text-gray-600">
                            Study prerequisite first
                          </span>
                        )}
                      </div>
                    </div>
                    <p className="mt-1 text-sm text-gray-600">{g.reason}</p>
                    {g.description && (
                      <p className="mt-1 text-sm text-gray-500">{g.description}</p>
                    )}
                    {g.llm_explanation && (
                      <p className="mt-2 border-l-2 border-blue-200 pl-3 text-sm text-gray-600">
                        {g.llm_explanation}
                      </p>
                    )}
                  </li>
                ))}
              </ol>
            )}
          </section>
        </>
      )}
    </div>
  )
}
