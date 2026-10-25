import { t, useLocale, message, number, percent, dateTime, time, dateOnly, intlLocale } from '../i18n'
import { useEffect, useRef, useState } from 'react'
import usePendingResults from '../usePendingResults'
import { Link } from 'react-router-dom'
import api, { apiMessage } from '../api'
import { useAuth } from '../auth'
import CompetencyDonut from '../components/CompetencyDonut'
import StudentLeaderboard from '../components/StudentLeaderboard'
import { EmptyState, ErrorState, Loading } from '../components/States'
import { Badge, Card, CardTitle, Icon, ScoreBar } from '../components/ui'
import heroBg from '../assets/brand/nen1.jpg'
import heroVideo from '../assets/brand/video1.mp4'
import BackgroundVideo from '../components/BackgroundVideo'

const FINAL_STATES = new Set(['completed', 'timed_out'])

// Photo hero band — the learner prototype's greeting + glass stat grid over
// the fixed photographic background (nen1.jpg), exactly like Home_Learner.
function DashboardHero({ finalized, profile, study, profileState, onRefresh }) {
  useLocale()
  const account = useAuth()?.account
  const concepts = profile?.concepts || []
  const summary = profile?.summary || {}
  const avg = concepts.length
    ? concepts.reduce((sum, c) => sum + Number(c.competency_pct || 0), 0) / concepts.length
    : null
  const benchmarked = Number(summary.benchmarked_concepts || 0)
  const meeting = Number(summary.meeting_target || 0)
  const cloPct = benchmarked ? Math.round((meeting / benchmarked) * 100) : null
  const largestGap = study?.[0]

  return (
    <section className="hero-photo" style={{ '--hero-img': `url(${heroBg})` }}>
      <BackgroundVideo className="hero-video" src={heroVideo} poster={heroBg} />
      <div className="content-wrap hero-photo-inner">
        <div className="mb-7 flex flex-wrap items-center justify-between gap-6">
          <div>
            <h1 className="text-[23px] font-extrabold leading-snug tracking-[-1px] text-ink lg:text-[32px]">
              {t('dashboard.greeting', { name: account?.full_name || account?.email || '' })} <span aria-hidden="true">👋</span>
            </h1>
            <p className="mt-1.5 text-xs text-sub">{t('dashboard.subtitle')}</p>
          </div>
          <div className="flex flex-wrap items-center justify-end gap-2.5">
            <button type="button" onClick={onRefresh} disabled={profileState === 'loading'} className="hero-tag btn-ghost disabled:opacity-50">
              <Icon name="reset" className="hero-tag-icon" />
              <strong>{t('dashboard.refresh')}</strong>
            </button>
          </div>
        </div>

        <div className="hero-stat-grid" role="list">
          <article className="hero-stat" role="listitem">
            <div className="hero-stat-heading"><span>{t('dashboard.statAttempts')}</span><Icon name="check" className="h-[17px] w-[17px] text-cyan-300" /></div>
            <div className="hero-stat-bottom">
              <div className="hero-stat-value"><strong>{number(summary.finalized_assessments ?? finalized.length)}</strong><span>{t('dashboard.statAttemptsUnit')}</span></div>
              <span className="hero-tag-chip green">{t('dashboard.statAttemptsTag', { count: finalized.length })}</span>
            </div>
          </article>
          <article className="hero-stat" role="listitem">
            <div className="hero-stat-heading"><span>{t('dashboard.statScore')}</span><Icon name="chart" className="h-[17px] w-[17px] text-cyan-300" /></div>
            <div className="hero-stat-bottom">
              <div className="hero-stat-value"><strong className="cyan">{avg == null ? '—' : percent(avg, { maximumFractionDigits: 0 })}</strong><span>{t('dashboard.statScoreUnit')}</span></div>
              <span className="hero-tag-chip">{t('dashboard.statScoreTag')}</span>
            </div>
          </article>
          <article className="hero-stat" role="listitem">
            <div className="hero-stat-heading"><span>{t('dashboard.statFocus')}</span><Icon name="flag" className="h-[17px] w-[17px] text-cyan-300" /></div>
            <div className="hero-stat-bottom">
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-ink" title={largestGap?.concept_name || ''}>{largestGap?.concept_name || t('dashboard.onTrack')}</p>
              </div>
              {largestGap && <span className="hero-tag-chip">{t('guidance.shortfall', { value: number(largestGap.shortfall) })}</span>}
            </div>
          </article>
          <article className="hero-stat" role="listitem">
            <div className="hero-stat-heading"><span>{t('dashboard.statProgress')}</span><span className="mono">{benchmarked ? t('dashboard.statRemaining', { pct: 100 - (cloPct ?? 0) }) : ''}</span></div>
            <div className="hero-stat-bottom">
              <div className="hero-stat-value"><strong>{benchmarked ? `${number(meeting)} / ${number(benchmarked)}` : '—'}</strong><span>{t('dashboard.statProgressUnit')}</span></div>
              <span className="hero-stat-target">{t('dashboard.statProgressTarget')}</span>
            </div>
            <div className="hero-progress" role="progressbar" aria-label={t('dashboard.statProgress')} aria-valuemin="0" aria-valuemax="100" aria-valuenow={cloPct ?? 0}>
              <span style={{ width: `${cloPct ?? 0}%` }} />
            </div>
          </article>
        </div>
      </div>
    </section>
  )
}

function DashboardState({ children }) {
  useLocale()
  return (
    <>
      <section className="hero-photo" style={{ '--hero-img': `url(${heroBg})` }}>
        <BackgroundVideo className="hero-video" src={heroVideo} poster={heroBg} />
        <div className="content-wrap hero-photo-inner">
          <Link to="/competency" className="mb-3 inline-block text-sm text-cyan-300 underline">{t('supervisor.cumulative')}</Link>
          <h1 className="text-[23px] font-extrabold leading-snug tracking-[-1px] text-ink lg:text-[32px]">{t('dashboard.title')}</h1>
          <p className="mt-1.5 text-xs text-sub">{t('dashboard.subtitle')}</p>
        </div>
      </section>
      <div className="content-wrap py-8">{children}</div>
    </>
  )
}

function fmt(dt) {
  return dt ? dateTime(dt) : ''
}

// UC16/FR-13 + DBCAS-24 — the learner's visual competency profile rendered
// with the learner prototype's exact composition: photo hero with glass stat
// cards, competency panel (radar + per-area skill tracks), the AI analysis
// panel (strength/weakness findings + guidance roadmap), then the concept
// table and recent sessions.
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
  const [listRefresh, setListRefresh] = useState(0)
  const listInFlight = useRef(false)
  usePendingResults(sessions?.some(s => FINAL_STATES.has(s.status) && s.release_status === 'auto_grading'), () => {
    if (!listInFlight.current) setListRefresh(r => r + 1)
  })

  useEffect(() => {
    let cancelled = false
    listInFlight.current = true
    setListError('')
    api
      .get('/sessions')
      .then((r) => {
        if (cancelled) return
        const list = r.data || []
        setSessions(list)
        const latestFinal = list.find((s) => FINAL_STATES.has(s.status) && (!s.release_status || s.release_status === 'published'))
        if (latestFinal) setSessionId(latestFinal.session_id)
      })
      .catch((err) => { if (!cancelled && !sessions) setListError(apiMessage(err)) })
      .finally(() => { if (!cancelled) listInFlight.current = false })
    return () => {
      cancelled = true
    }
  }, [retry, listRefresh])

  useEffect(() => {
    if (!sessionId) return
    let cancelled = false
    setProfileState('loading')
    setProfileError('')
    Promise.all([
      api.get(`/sessions/${sessionId}/competency`),
      api.get('/sessions/competency/cumulative'),
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

  const finalized = sessions.filter((s) => FINAL_STATES.has(s.status) && (!s.release_status || s.release_status === 'published'))
  if (!finalized.length) {
    return (
      <DashboardState><EmptyState title={t('dashboard.empty')}>{sessions.some(s => FINAL_STATES.has(s.status)) ? t('supervisor.pendingHelp') : t('dashboard.emptyBody')}<Link to="/assessments" className="mt-3 block font-medium text-cyan-300 hover:underline">{t('dashboard.browse')}</Link>
      </EmptyState><button type="button" className="mt-4 text-sm text-cyan-300 underline" onClick={() => setRetry(r => r + 1)}>{t('dashboard.refresh')}</button><div className="mt-6"><StudentLeaderboard /></div></DashboardState>
    )
  }

  const concepts = profile?.concepts || []
  const study = (guidance?.gaps || []).map(g => ({ ...g, shortfall: Math.max(0, Number(g.target_pct) - Number(g.competency_pct)) }))
  const selectedSession = finalized.find((s) => s.session_id === sessionId)
  const strengths = (guidance?.concepts || []).filter((c) => c.target_pct != null && !c.below_target)
  const gaps = guidance?.gaps || []

  return (
    <>
      <DashboardHero
        finalized={finalized}
        profile={profile}
        study={study}
        profileState={profileState}
        onRefresh={() => setRetry((r) => r + 1)}
      />

      <div className="content-wrap flex flex-col gap-7 py-8">
        {selectedSession?.pending_grading_count > 0 && <p role="status" className="text-sm text-sub">{t('dashboard.pending')}</p>}
        {selectedSession?.failed_grading_count > 0 && <p role="status" className="text-sm text-amber-300">{t('dashboard.failed')}</p>}

        {profileState === 'loading' && <Loading label={t('dashboard.loadingProfile')} />}
        {profileState === 'error' && <ErrorState message={profileError} onRetry={() => setRetry((r) => r + 1)} />}

        {profileState === 'ready' && !concepts.length && (
          <EmptyState title={t('dashboard.noData')} />
        )}

        {profileState === 'ready' && concepts.length > 0 && (
          <>
            {/* Concept distribution against each configured target. */}
            <section className="lp-panel" aria-label={t('dashboard.charts')}>
              <div className="lp-panel-heading">
                <div>
                  <h2>{t('dashboard.competencyTitle')}</h2>
                  <p>{t('dashboard.competencySub')}</p>
                </div>
              </div>
              <CompetencyDonut concepts={concepts} />
            </section>

            {/* Analysis panel: strengths, weaknesses, then the guidance roadmap. */}
            <section className="lp-panel" aria-label={t('dashboard.analysisEyebrow')}>
              <div className="lp-analysis-heading">
                <span className="lp-analysis-icon"><Icon name="spark" className="h-6 w-6" /></span>
                <div>
                  <h2 className="text-xl font-extrabold tracking-[-0.5px] text-ink sm:text-2xl">{t('dashboard.analysisTitle')}</h2>
                  <p>{t('dashboard.analysisSub')}</p>
                </div>
              </div>
              <div className="grid gap-6 lg:grid-cols-2">
                <article className="lp-analysis-card strengths">
                  <div className="lp-analysis-card-heading">
                    <h3><Icon name="shield" className="h-4 w-4" />{t('dashboard.strengths')}</h3>
                    <span className="lp-badge green">{t('dashboard.strengthsMeta')}</span>
                  </div>
                  {!strengths.length ? (
                    <p className="text-xs text-sub">{t('dashboard.noStrengths')}</p>
                  ) : (
                    strengths.slice(0, 3).map((c) => (
                      <div className="lp-finding" key={c.concept_id}>
                        <div className="lp-finding-heading">
                          <h4>{c.concept_name}</h4>
                          <span>{percent(c.competency_pct, { maximumFractionDigits: 0 })}</span>
                        </div>
                        <p>{c.description || c.subject_area}</p>
                      </div>
                    ))
                  )}
                </article>
                <article className="lp-analysis-card weaknesses">
                  <div className="lp-analysis-card-heading">
                    <h3><Icon name="alert" className="h-4 w-4" />{t('dashboard.gapsTitle')}</h3>
                    <span className="lp-badge rose">{t('dashboard.gapsMeta')}</span>
                  </div>
                  {!gaps.length ? (
                    <p className="text-xs text-sub">{t('dashboard.noGapsShort')}</p>
                  ) : (
                    gaps.slice(0, 3).map((c) => (
                      <div className="lp-finding" key={c.concept_id}>
                        <div className="lp-finding-heading">
                          <h4>{c.concept_name}</h4>
                          <span>{percent(c.competency_pct, { maximumFractionDigits: 0 })}</span>
                        </div>
                        <p>{c.description || c.subject_area}</p>
                      </div>
                    ))
                  )}
                </article>
              </div>

              {/* Guidance roadmap — prioritized real recommendations. */}
              <section className="lp-roadmap" aria-label={t('guidance.title')}>
                <div className="lp-roadmap-heading">
                  <h3>{t('guidance.title')}</h3>
                  <p>{t('dashboard.roadmapSub')}</p>
                </div>
                {!study.length ? (
                  <EmptyState title={t('guidance.noGaps')} />
                ) : (
                  <ol className={`lp-roadmap-grid ${study.length >= 3 ? 'lp-roadmap-grid-three' : ''}`}>
                    {study.slice(0, 6).map((g, index) => (
                      <li key={g.concept_id}>
                        <article className="lp-roadmap-card">
                          <div className="lp-roadmap-label"><Icon name="target" className="h-4 w-4" />{index === 0 ? t('dashboard.next') : t('dashboard.roadmapLabel')}</div>
                          <h4>{index + 1}. {g.concept_name}</h4>
                          <span className="lp-badge rose">
                            {t('cumulativeView.gap', { value: number(Math.max(0, Number(g.target_pct) - Number(g.competency_pct)), { maximumFractionDigits: 2 }) })}
                          </span>
                          <p>{t('dashboard.cumulativeAdvice', { name: g.concept_name, score: percent(g.competency_pct), target: percent(g.target_pct) })}</p>
                          {g.llm_explanation && <p>{g.llm_explanation}</p>}
                          <div className="lp-roadmap-tags">
                            <span>{g.description || g.subject_area || ''}</span>
                            <strong>{t('guidance.priority', { value: number(index + 1) })}</strong>
                          </div>
                        </article>
                      </li>
                    ))}
                  </ol>
                )}
              </section>
              <div className="mt-7 flex flex-wrap items-center justify-between gap-4 border-t border-edge pt-5">
                <p className="flex items-center gap-2 text-xs text-sub">
                  <Icon name="spark" className="h-4 w-4 text-accent" />
                  {t('dashboard.analysisNote')}
                </p>
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
        <StudentLeaderboard />
      </div>
    </>
  )
}
