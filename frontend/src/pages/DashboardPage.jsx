import { t, useLocale, message, number, percent, dateTime, time, dateOnly, intlLocale } from '../i18n'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api, { apiMessage } from '../api'
import { CompetencyBar, CompetencyConceptBars, CompetencyRadar } from '../components/CompetencyCharts'
import { EmptyState, ErrorState, Loading } from '../components/States'
import { Badge, Card, CardTitle, HeroBand, Icon, ScoreBar, SkillTrack, StatTile, TagPill, TintCard } from '../components/ui'

const FINAL_STATES = new Set(['completed', 'timed_out'])

// Dark hero band — the learner prototype's greeting band. Carries the page's
// single h1 ("My competency") plus the session picker on the right.
function DashboardHero({ children }) {
  useLocale()
  return (
    <HeroBand
      eyebrow={t('dashboard.heroEyebrow')}
      title={t('dashboard.title')}
      subtitle={t('dashboard.subtitle')}
      aside={children}
    />
  )
}

function DashboardState({ children }) {
  useLocale()
  return <div className="space-y-6"><DashboardHero />{children}</div>
}

function fmt(dt) {
  return dt ? dateTime(dt) : ''
}

function guidanceReason(item) {
  if (item.reason_code !== 'below_benchmark' || !item.reason_params) return t('guidance.reason.unavailable')
  const reason = t('guidance.reason.belowBenchmark', {
    shortfall: number(item.reason_params.shortfall, { minimumFractionDigits: 2 }),
    target: percent(item.reason_params.target, { minimumFractionDigits: 2 }),
  })
  const blockers = item.prerequisites.filter(p => p.status === 'below_target')
  const unassessed = item.prerequisites.filter(p => p.status === 'unassessed')
  // Preserve the backend's readiness semantics: blockers take precedence.
  const preparation = blockers.length
    ? t('guidance.reason.preparation', { concepts: blockers.map(p => p.concept_name).join(', ') })
    : unassessed.length
      ? t('guidance.reason.unassessed', { concepts: unassessed.map(p => p.concept_name).join(', ') })
      : ''
  return [reason, preparation].filter(Boolean).join(' ')
}

// UC16/FR-13 + DBCAS-24 — the learner's visual competency profile:
// radar + bar charts of backend-computed concept competency, then the
// "What to study next" list (UC17/FR-14). Nothing is recalculated client-side.
// Visual layout follows the learner prototype's dashboard: hero band, KPI
// strip, framed charts, analysis cards, a concept score table, then
// prioritized guidance cards.
export default function DashboardPage() {
  useLocale()
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

  if (listError) return <DashboardState><ErrorState message={listError} onRetry={() => setRetry((r) => r + 1)} /></DashboardState>
  if (!sessions) return <DashboardState><Loading label={t('dashboard.loadingSessions')} /></DashboardState>

  const finalized = sessions.filter((s) => FINAL_STATES.has(s.status))
  if (!finalized.length) {
    return (
      <DashboardState><EmptyState title={t('dashboard.empty')}>{t('dashboard.emptyBody')}<Link to="/assessments" className="mt-3 block font-medium text-cyan-300 hover:underline">{t('dashboard.browse')}</Link>
      </EmptyState></DashboardState>
    )
  }

  const concepts = profile?.concepts || []
  const study = guidance?.guidance || []
  const summary = profile?.summary || {}
  const largestGap = study[0]
  const nextConcept = study[0]
  const selectedSession = finalized.find((s) => s.session_id === sessionId)
  const strengths = concepts.filter((c) => c.target_pct != null && !c.below_target)
  const gaps = concepts.filter((c) => c.below_target)

  return (
    <div className="space-y-6">
      <DashboardHero>
        <label className="block min-w-0 w-full text-sm text-slate-300 sm:w-auto">{t('dashboard.session')}{' '}
          <select
            aria-label={t('dashboard.selectSession')}
            value={sessionId ?? ''}
            onChange={(e) => setSessionId(Number(e.target.value))}
            className="mt-1 block w-full max-w-full rounded-lg border border-slate-500/40 bg-slate-900/80 px-3 py-2 text-sm text-slate-100 focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/20 sm:w-auto"
          >
            {finalized.map((s) => (
              <option key={s.session_id} value={s.session_id}>
                {s.assessment_title || t('assessment.number', { id: s.assessment_id })} —{' '}
                {fmt(s.submitted_at || s.started_at)}
              </option>
            ))}
          </select>
        </label>
        <button type="button" onClick={() => setRetry((r) => r + 1)} disabled={profileState === 'loading'} className="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-500/40 bg-slate-900/60 px-3.5 py-2 text-sm font-medium text-slate-200 hover:bg-slate-800 disabled:opacity-50">{t('dashboard.refresh')}</button>
      </DashboardHero>

      {selectedSession?.pending_grading_count > 0 && <p role="status" className="text-sm text-sub">{t('dashboard.pending')}</p>}
      {selectedSession?.failed_grading_count > 0 && <p role="status" className="text-sm text-amber-300">{t('dashboard.failed')}</p>}

      {profileState === 'loading' && <Loading label={t('dashboard.loadingProfile')} />}
      {profileState === 'error' && <ErrorState message={profileError} onRetry={() => setRetry((r) => r + 1)} />}

      {profileState === 'ready' && !concepts.length && (
        <EmptyState title={t('dashboard.noData')} />
      )}

      {profileState === 'ready' && concepts.length > 0 && (
        <>
          <section
            aria-label={t('dashboard.summary')}
            className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4"
          >
            <StatTile label={t('dashboard.meetingTarget')} value={`${number(summary.meeting_target)} / ${number(summary.benchmarked_concepts)}`} icon="check" tone="green" hint={t('dashboard.withoutBenchmark', { count: summary.unbenchmarked_concepts ?? 0 })} />
            <StatTile label={t('dashboard.completed')} value={number(summary.finalized_assessments)} icon="list" hint={fmt(selectedSession?.submitted_at || selectedSession?.started_at)} />
            <InsightCard label={t('dashboard.largestGap')} value={largestGap?.concept_name || t('dashboard.none')} hint={largestGap ? t('guidance.shortfall', { value: number(largestGap.shortfall) }) : t('dashboard.noGap')} icon="flag" tone="rose" />
            <InsightCard label={t('dashboard.next')} value={nextConcept?.concept_name || t('dashboard.onTrack')} hint={nextConcept ? t('guidance.priority', { value: number(nextConcept.priority) }) : t('dashboard.keepPracticing')} icon="target" tone="violet" />
          </section>

          <section
            aria-label={t('dashboard.charts')}
            className="grid min-w-0 gap-4 lg:grid-cols-2"
          >
            <Card className="min-w-0 p-4">
              <figure className="min-w-0">
                <figcaption className="mb-2 flex items-center justify-between gap-2 text-sm font-medium text-sub">
                  <span>{t('dashboard.masteryTarget')}</span>
                  <TagPill accent>{t('dashboard.conceptScores')}</TagPill>
                </figcaption>
                <div className="relative h-72 min-w-0 w-full">
                  {concepts.length < 3 ? <CompetencyConceptBars concepts={concepts} /> : <CompetencyRadar concepts={concepts} />}
                </div>
              </figure>
            </Card>
            <Card className="min-w-0 p-4">
              <figure className="min-w-0">
                <figcaption className="mb-2 text-sm font-medium text-sub">{t('dashboard.byArea')}</figcaption>
                <div className="relative h-72 min-w-0 w-full">
                  <CompetencyBar categories={profile.categories} />
                </div>
                <p className="mt-2 text-xs text-mute">{t('dashboard.displayAverage')}</p>
              </figure>
            </Card>
          </section>

          {/* Strength / gap analysis cards — the learner prototype's
              AI-analysis row, fed by backend below_target flags. */}
          <section aria-label={t('dashboard.analysisEyebrow')}>
            <p className="eyebrow mb-3">{t('dashboard.analysisEyebrow')}</p>
            <div className="grid gap-4 lg:grid-cols-2">
              <TintCard tone="green" icon="check" title={t('dashboard.strengths')} meta={t('dashboard.strengthsMeta')}>
                {!strengths.length ? (
                  <p className="relative mt-4 text-sm text-mute">{t('dashboard.noStrengths')}</p>
                ) : (
                  <ul className="relative mt-4 space-y-3">
                    {strengths.slice(0, 4).map((c) => (
                      <li key={c.concept_id}>
                        <div className="mb-1.5 flex items-center justify-between gap-3 text-sm">
                          <span className="min-w-0 truncate font-medium text-ink">{c.concept_name}</span>
                          <span className="shrink-0 font-mono text-xs font-semibold text-emerald-300">{percent(c.competency_pct, { maximumFractionDigits: 0 })}</span>
                        </div>
                        <SkillTrack value={Number(c.competency_pct)} target={c.target_pct == null ? null : Number(c.target_pct)} tone="success" />
                      </li>
                    ))}
                  </ul>
                )}
              </TintCard>
              <TintCard tone="rose" icon="alert" title={t('dashboard.gapsTitle')} meta={t('dashboard.gapsMeta')}>
                {!gaps.length ? (
                  <p className="relative mt-4 text-sm text-mute">{t('dashboard.noGapsShort')}</p>
                ) : (
                  <ul className="relative mt-4 space-y-3">
                    {gaps.slice(0, 4).map((c) => (
                      <li key={c.concept_id}>
                        <div className="mb-1.5 flex items-center justify-between gap-3 text-sm">
                          <span className="min-w-0 truncate font-medium text-ink">{c.concept_name}</span>
                          <span className="shrink-0 font-mono text-xs font-semibold text-rose-300">{percent(c.competency_pct, { maximumFractionDigits: 0 })}</span>
                        </div>
                        <SkillTrack value={Number(c.competency_pct)} target={c.target_pct == null ? null : Number(c.target_pct)} tone="danger" />
                      </li>
                    ))}
                  </ul>
                )}
              </TintCard>
            </div>
          </section>

          <section aria-label={t('dashboard.conceptScores')}>
            <Card className="overflow-hidden">
              <CardTitle title={t('dashboard.conceptScores')} />
              <p className="px-4 pt-2 text-xs text-mute sm:hidden">{t('common.swipeTable')}</p>
              <div className="overflow-x-auto" role="region" aria-label={t('dashboard.conceptTable')} tabIndex={0}>
                <table className="data-table min-w-[760px]">
                  <thead>
                    <tr>
                      <th className="px-4 py-2">{t('common.concept')}</th>
                      <th className="px-4 py-2">{t('common.subjectArea')}</th>
                      <th className="px-4 py-2">{t('dashboard.mastery')}</th>
                      <th className="px-4 py-2 text-right">{t('competency.label')}</th>
                      <th className="px-4 py-2 text-right">{t('competency.target')}</th>
                      <th className="px-4 py-2">{t('common.status')}</th>
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
                        <td className="px-4 py-2 text-right">{percent(c.competency_pct, { minimumFractionDigits: 2 })}</td>
                        <td className="px-4 py-2 text-right">
                          {percent(c.target_pct)}
                        </td>
                        <td className="px-4 py-2">
                          {c.target_pct == null ? <Badge>{t('common.noBenchmark')}</Badge> : c.below_target ? (
                            <Badge tone="red">{t('common.belowTarget')}</Badge>
                          ) : (
                            <Badge tone="green">{t('common.onTarget')}</Badge>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </section>

          <section aria-label={t('guidance.title')}>
            <h2 className="mb-2 text-lg font-semibold text-ink">{t('guidance.title')}</h2>
            {!study.length ? (
              <EmptyState title={t('guidance.noGaps')} />
            ) : (
              <ol className="space-y-3">
                {study.map((g) => (
                  <li key={g.concept_id}>
                    <Card className="p-4">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <p className="flex items-center gap-3 font-medium text-ink">
                          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-cyan-400/10 font-mono text-xs font-bold text-cyan-300 ring-1 ring-inset ring-cyan-400/25">
                            {g.priority}
                          </span>
                          {g.priority}. {g.concept_name}
                        </p>
                        <div className="flex items-center gap-2 text-xs">
                          <Badge tone="amber">{t('guidance.shortfall', { value: number(g.shortfall) })}</Badge>
                          {!g.ready && <Badge>{t('guidance.prerequisites')}</Badge>}
                        </div>
                      </div>
                      <p className="mt-2 text-sm leading-relaxed text-sub">{guidanceReason(g)}</p>
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

          <section aria-label={t('dashboard.activity')}>
            <Card className="overflow-hidden">
              <CardTitle title={t('dashboard.activity')}><Link to="/history" className="text-xs font-medium text-cyan-300 hover:underline">{t('dashboard.history')}</Link></CardTitle>
              <ul className="divide-y divide-edge/70">
                {finalized.slice(0, 3).map((session) => <li key={session.session_id} className="flex flex-wrap items-center justify-between gap-2 px-5 py-3 text-sm">
                  <div><p className="font-medium text-ink">{session.assessment_title}</p><p className="mt-0.5 text-xs text-mute">{fmt(session.submitted_at || session.started_at)} · {t('history.answered', { answered: number(session.answered_count), served: number(session.served_count) })}</p></div>
                  <Link to={`/history/${session.session_id}`} className="font-medium text-cyan-300 hover:underline">{t('dashboard.evidence')}</Link>
                </li>)}
              </ul>
            </Card>
          </section>
        </>
      )}
    </div>
  )
}

// The label's parent element must contain the value — dashboard tests assert
// on that relationship — so the icon lives inside the label row itself.
function InsightCard({ label, value, hint, icon, tone = '' }) {
  const iconCls = { rose: 'bg-rose-400/10 text-rose-300', violet: 'bg-violet-400/10 text-violet-300', cyan: 'bg-cyan-400/10 text-cyan-300' }[tone] || 'bg-cyan-400/10 text-cyan-300'
  return (
    <div className="stat-tile surface-card">
      <p className="flex items-center justify-between gap-2 text-xs font-medium uppercase tracking-wide text-mute">
        {label}
        {icon && <span className={`flex h-8 w-8 items-center justify-center rounded-lg ${iconCls}`}><Icon name={icon} className="h-4 w-4" /></span>}
      </p>
      <p className="mt-2 truncate text-base font-semibold text-ink" title={value}>{value}</p>
      <p className="mt-1 text-xs text-mute">{hint}</p>
    </div>
  )
}
