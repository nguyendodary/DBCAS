import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api, { apiMessage } from '../api'
import { CompetencyBar, CompetencyConceptBars, CompetencyRadar } from '../components/CompetencyCharts'
import { EmptyState, ErrorState, Loading } from '../components/States'
import { Badge, Card, CardTitle, Icon, PageHeader, ScoreBar, StatCard, selectCls, btnGhost } from '../components/ui'

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
  const [retry, setRetry] = useState(0)

  useEffect(() => {
    let cancelled = false
    setListError('')
    api
      .get('/sessions')
      .then((r) => {
        if (cancelled) return
        const list = r.data || []
        setSessions(list)
        const latestFinal = list.find((s) => FINAL_STATES.has(s.status))
        if (latestFinal) setSessionId((current) => current && list.some((s) => s.session_id === current) ? current : latestFinal.session_id)
      })
      .catch((err) => !cancelled && setListError(apiMessage(err)))
    return () => {
      cancelled = true
    }
  }, [retry])

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
  }, [sessionId, retry])

  if (listError) return <ErrorState message={listError} onRetry={() => setRetry((r) => r + 1)} />
  if (!sessions) return <Loading label="Loading your sessions…" />

  const finalized = sessions.filter((s) => FINAL_STATES.has(s.status))
  if (!finalized.length) {
    return (
      <EmptyState title="No completed assessments yet">
        Your competency profile appears here after you finish an assessment.
        <Link to="/assessments" className="mt-3 block font-medium text-cyan-300 hover:underline">Browse assessments</Link>
      </EmptyState>
    )
  }

  const concepts = profile?.concepts || []
  const study = guidance?.guidance || []
  const summary = profile?.summary || {}
  const largestGap = study[0]
  const nextConcept = study[0]
  const selectedSession = finalized.find((s) => s.session_id === sessionId)

  return (
    <div className="space-y-6">
      <PageHeader
        title="My competency"
        subtitle="Your assessed skills, benchmarks, and next study priorities."
      >
        <label className="block min-w-0 w-full text-sm text-sub sm:w-auto">
          Assessment session{' '}
          <select
            aria-label="Select assessment session"
            value={sessionId ?? ''}
            onChange={(e) => setSessionId(Number(e.target.value))}
            className={`mt-1 block w-full max-w-full sm:w-auto ${selectCls}`}
          >
            {finalized.map((s) => (
              <option key={s.session_id} value={s.session_id}>
                {s.assessment_title || `Assessment ${s.assessment_id}`} —{' '}
                {fmt(s.submitted_at || s.started_at)}
              </option>
            ))}
          </select>
        </label>
        <button type="button" onClick={() => setRetry((r) => r + 1)} disabled={profileState === 'loading'} className={btnGhost}>Refresh results</button>
      </PageHeader>

      {selectedSession?.pending_grading_count > 0 && <p role="status" className="text-sm text-sub">Some submitted answers are awaiting grading. This profile shows graded evidence only. Refresh results after grading completes.</p>}
      {selectedSession?.failed_grading_count > 0 && <p role="status" className="text-sm text-amber-300">Some answers need a grading retry. Contact your administrator. Those answers are excluded until grading succeeds.</p>}

      {profileState === 'loading' && <Loading label="Loading competency profile…" />}
      {profileState === 'error' && <ErrorState message={profileError} onRetry={() => setRetry((r) => r + 1)} />}

      {profileState === 'ready' && !concepts.length && (
        <EmptyState title="No competency data for this session" />
      )}

      {profileState === 'ready' && concepts.length > 0 && (
        <>
          <section
            aria-label="Session summary"
            className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4"
          >
            <StatCard label="Meeting target" value={`${summary.meeting_target ?? '—'} / ${summary.benchmarked_concepts ?? '—'}`} icon="check" hint={`${summary.unbenchmarked_concepts ?? 0} assessed without a benchmark`} />
            <StatCard label="Assessments completed" value={summary.finalized_assessments ?? '—'} icon="list" />
            <InsightCard label="Largest skill gap" value={largestGap?.concept_name || 'None'} hint={largestGap ? `${largestGap.shortfall} pts below target` : 'No assessed concept is below its configured target'} />
            <InsightCard label="Next to study" value={nextConcept?.concept_name || 'On track'} hint={nextConcept ? `Priority ${nextConcept.priority}` : 'Keep practicing'} />
          </section>

          <section
            aria-label="Competency charts"
            className="grid min-w-0 gap-4 lg:grid-cols-2"
          >
            <Card className="min-w-0 p-4">
              <figure className="min-w-0">
                <figcaption className="mb-2 text-sm font-medium text-sub">
                  Concept mastery vs target
                </figcaption>
                <div className="relative h-72 min-w-0 w-full">
                  {concepts.length < 3 ? <CompetencyConceptBars concepts={concepts} /> : <CompetencyRadar concepts={concepts} />}
                </div>
              </figure>
            </Card>
            <Card className="min-w-0 p-4">
              <figure className="min-w-0">
                <figcaption className="mb-2 text-sm font-medium text-sub">
                  By subject area
                </figcaption>
                <div className="relative h-72 min-w-0 w-full">
                  <CompetencyBar categories={profile.categories} />
                </div>
                <p className="mt-2 text-xs text-mute">Display average of assessed concept percentages. Official competency and benchmarks remain per concept.</p>
              </figure>
            </Card>
          </section>

          <section aria-label="Concept scores">
            <Card className="overflow-hidden">
              <CardTitle title="Concept scores" />
              <p className="px-4 pt-2 text-xs text-mute sm:hidden">Swipe the table to see all columns.</p>
              <div className="overflow-x-auto" role="region" aria-label="Concept scores table" tabIndex={0}>
                <table className="data-table min-w-[760px]">
                  <thead>
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
                      <tr key={c.concept_id}>
                        <td className="px-4 py-2 font-medium text-ink">
                          {c.concept_name}
                        </td>
                        <td className="px-4 py-2 text-sub">{c.subject_area}</td>
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
                          {c.target_pct == null ? <Badge>No benchmark</Badge> : c.below_target ? (
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
            <h2 className="mb-2 text-lg font-semibold text-ink">
              What to study next
            </h2>
            {!study.length ? (
              <EmptyState title="No assessed concepts below a configured benchmark" />
            ) : (
              <ol className="space-y-3">
                {study.map((g) => (
                  <li key={g.concept_id}>
                    <Card className="p-4">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <p className="font-medium text-ink">
                          {g.priority}. {g.concept_name}
                        </p>
                        <div className="flex items-center gap-2 text-xs">
                          <Badge tone="amber">{g.shortfall} pts below target</Badge>
                          {!g.ready && <Badge>Prerequisite preparation needed</Badge>}
                        </div>
                      </div>
                      <p className="mt-2 text-sm leading-relaxed text-sub">{g.reason}</p>
                      {g.description && (
                        <p className="mt-1 text-sm text-mute">{g.description}</p>
                      )}
                      {g.llm_explanation && (
                        <p className="mt-2 flex gap-2 rounded-lg border-l-4 border-cyan-400/50 bg-cyan-400/10 p-3 text-sm text-sub">
                          <Icon name="spark" className="mt-0.5 h-4 w-4 shrink-0 text-cyan-300" />
                          <span>{g.llm_explanation}</span>
                        </p>
                      )}
                    </Card>
                  </li>
                ))}
              </ol>
            )}
          </section>

          <section aria-label="Recent activity">
            <Card className="overflow-hidden">
              <CardTitle title="Recent activity"><Link to="/history" className="text-xs font-medium text-cyan-300 hover:underline">View history</Link></CardTitle>
              <ul className="divide-y divide-edge/70">
                {finalized.slice(0, 3).map((session) => <li key={session.session_id} className="flex flex-wrap items-center justify-between gap-2 px-5 py-3 text-sm">
                  <div><p className="font-medium text-ink">{session.assessment_title}</p><p className="mt-0.5 text-xs text-mute">{fmt(session.submitted_at || session.started_at)} · {session.answered_count}/{session.served_count} answered</p></div>
                  <Link to={`/history/${session.session_id}`} className="font-medium text-cyan-300 hover:underline">View evidence</Link>
                </li>)}
              </ul>
            </Card>
          </section>
        </>
      )}
    </div>
  )
}

function InsightCard({ label, value, hint }) {
  return <Card className="min-w-0 p-5">
    <p className="text-xs font-medium uppercase tracking-wide text-mute">{label}</p>
    <p className="mt-2 truncate text-base font-semibold text-ink" title={value}>{value}</p>
    <p className="mt-1 text-xs text-mute">{hint}</p>
  </Card>
}
