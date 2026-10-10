import { useEffect, useState } from 'react'
import api, { apiMessage } from '../api'
import { CompetencyBar, CompetencyRadar } from '../components/CompetencyCharts'
import { EmptyState, ErrorState, Loading } from '../components/States'
import { Badge, Card, CardTitle, Icon, PageHeader, ScoreBar, StatCard } from '../components/ui'

const FINAL_STATES = new Set(['completed', 'timed_out'])

function fmt(dt) {
  return dt ? new Date(dt).toLocaleString() : ''
}

// UC16/FR-13 + DBCAS-24 — the learner's visual competency profile:
// radar + bar charts of backend-computed concept competency, then the
// "What to study next" list (UC17/FR-14). Nothing is recalculated client-side.
// Visual layout follows the learner prototype's dashboard: KPI strip,
// framed charts, a concept score table, then prioritized guidance cards.
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
  const onTarget = concepts.filter((c) => !c.below_target).length

  return (
    <div className="space-y-6">
      <PageHeader
        title="My Competency Profile"
        subtitle="Deterministic per-concept results — points earned ÷ points possible."
      >
        <label className="text-sm text-gray-700">
          Assessment session{' '}
          <select
            aria-label="Select assessment session"
            value={sessionId ?? ''}
            onChange={(e) => setSessionId(Number(e.target.value))}
            className="rounded-md border border-gray-300 px-2 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
          >
            {finalized.map((s) => (
              <option key={s.session_id} value={s.session_id}>
                {s.assessment_title || `Assessment ${s.assessment_id}`} —{' '}
                {fmt(s.submitted_at || s.started_at)}
              </option>
            ))}
          </select>
        </label>
      </PageHeader>

      {profileState === 'loading' && <Loading label="Loading competency profile…" />}
      {profileState === 'error' && <ErrorState message={profileError} />}

      {profileState === 'ready' && !concepts.length && (
        <EmptyState title="No competency data for this session" />
      )}

      {profileState === 'ready' && concepts.length > 0 && (
        <>
          <section
            aria-label="Session summary"
            className="grid gap-4 sm:grid-cols-3"
          >
            <StatCard label="Concepts assessed" value={concepts.length} icon="book" />
            <StatCard label="Meeting target" value={onTarget} icon="check" />
            <StatCard
              label="Gaps to close"
              value={concepts.length - onTarget}
              icon="target"
              hint={study.length ? `${study.length} study recommendation(s) below` : undefined}
            />
          </section>

          <section
            aria-label="Competency charts"
            className="grid gap-6 md:grid-cols-2"
          >
            <Card className="p-4">
              <figure>
                <figcaption className="mb-2 text-sm font-medium text-gray-700">
                  Concept mastery vs target
                </figcaption>
                <div className="h-72">
                  <CompetencyRadar concepts={concepts} />
                </div>
              </figure>
            </Card>
            <Card className="p-4">
              <figure>
                <figcaption className="mb-2 text-sm font-medium text-gray-700">
                  By subject area
                </figcaption>
                <div className="h-72">
                  <CompetencyBar concepts={concepts} />
                </div>
              </figure>
            </Card>
          </section>

          <section aria-label="Concept scores">
            <Card className="overflow-hidden">
              <CardTitle title="Concept scores" />
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="border-b bg-gray-50 text-xs uppercase text-gray-500">
                    <tr>
                      <th className="px-4 py-2">Concept</th>
                      <th className="px-4 py-2">Subject area</th>
                      <th className="px-4 py-2">Mastery</th>
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
                        <td className="px-4 py-2">
                          <ScoreBar
                            value={Number(c.competency_pct)}
                            target={c.target_pct == null ? null : Number(c.target_pct)}
                          />
                        </td>
                        <td className="px-4 py-2 text-right">{c.competency_pct}%</td>
                        <td className="px-4 py-2 text-right">
                          {c.target_pct == null ? '—' : `${c.target_pct}%`}
                        </td>
                        <td className="px-4 py-2">
                          {c.below_target ? (
                            <Badge tone="red">Below target</Badge>
                          ) : (
                            <Badge tone="green">On target</Badge>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
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
                  <li key={g.concept_id}>
                    <Card className="p-4">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <p className="font-medium text-gray-900">
                          {g.priority}. {g.concept_name}
                        </p>
                        <div className="flex items-center gap-2 text-xs">
                          <Badge tone="amber">{g.shortfall} pts below target</Badge>
                          {!g.ready && <Badge>Study prerequisite first</Badge>}
                        </div>
                      </div>
                      <p className="mt-2 text-sm text-gray-600">{g.reason}</p>
                      {g.description && (
                        <p className="mt-1 text-sm text-gray-500">{g.description}</p>
                      )}
                      {g.llm_explanation && (
                        <p className="mt-2 flex gap-2 rounded-lg border-l-4 border-blue-300 bg-blue-50/60 p-3 text-sm text-gray-700">
                          <Icon name="spark" className="mt-0.5 h-4 w-4 shrink-0 text-blue-500" />
                          <span>{g.llm_explanation}</span>
                        </p>
                      )}
                    </Card>
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
