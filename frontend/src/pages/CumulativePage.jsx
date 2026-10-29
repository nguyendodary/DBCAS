import { Fragment, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api, { apiMessage } from '../api'
import { t, useLocale, number, percent } from '../i18n'
import { Badge, Card, HeroBand, Icon, btnGhost, inputCls } from '../components/ui'
import { Loading, EmptyState, ErrorState } from '../components/States'
import { CompetencyConceptBars } from '../components/CompetencyCharts'
import heroPoster from '../assets/brand/nen1.jpg'
import heroVideo from '../assets/brand/video1.mp4'

const normalize = (value) => String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/\u0111/g, 'd').toLowerCase()
const clampPct = (value) => Math.max(0, Math.min(100, Number(value) || 0))

function conceptState(concept) {
  if (concept.target_pct == null) return 'neutral'
  return concept.below_target ? 'improve' : 'met'
}

export default function CumulativePage() {
  useLocale()
  const { learnerId } = useParams()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState('all')
  const [expandedId, setExpandedId] = useState(null)
  const requestSequence = useRef(0)
  const load = useCallback(() => {
    const sequence = ++requestSequence.current
    setError(null)
    setData(null)
    api.get(learnerId ? `/admin/learners/${learnerId}/competency/cumulative` : '/sessions/competency/cumulative')
      .then(r => { if (sequence === requestSequence.current) setData(r.data) })
      .catch(e => { if (sequence === requestSequence.current) setError(apiMessage(e)) })
  }, [learnerId])
  useEffect(() => {
    setQuery('')
    setFilter('all')
    setExpandedId(null)
    load()
    return () => { requestSequence.current += 1 }
  }, [load])

  const concepts = data?.concepts || []
  const counts = useMemo(() => ({
    all: concepts.length,
    improve: concepts.filter(c => conceptState(c) === 'improve').length,
    met: concepts.filter(c => conceptState(c) === 'met').length,
    neutral: concepts.filter(c => conceptState(c) === 'neutral').length,
  }), [concepts])
  const needle = normalize(query.trim())
  const visible = concepts.filter(c => (filter === 'all' || conceptState(c) === filter)
    && normalize(`${c.concept_name} ${c.concept_code || ''} ${c.subject_area || ''}`).includes(needle))

  return <>
    {!learnerId && <HeroBand
      className="hero-band-wide"
      eyebrow={t('nav.history')}
      title={t('supervisor.cumulative')}
      subtitle={t('supervisor.cumulativeHelp')}
      videoSrc={heroVideo}
      videoPoster={heroPoster}
    />}
    <div className="content-wrap space-y-5 py-6">
    <div className="flex flex-wrap items-center justify-between gap-3">
      {learnerId && <h1 className="text-2xl font-bold text-ink">{t('supervisor.cumulative')}</h1>}
      <button className={btnGhost} onClick={load}>{t('dashboard.refresh')}</button>
    </div>
    {learnerId && <p className="text-sm text-sub">{t('supervisor.cumulativeHelp')}</p>}
    {error ? <ErrorState message={error} onRetry={load} /> : !data ? <Loading /> : <>
      <p className="text-sm text-sub">{t('supervisor.publishedCount', { count: data.summary.finalized_assessments })}</p>
      {!concepts.length ? <EmptyState title={t('supervisor.noEvidence')} /> : <>
        <div className="grid gap-4 sm:grid-cols-3">
          <Card className="p-5"><p className="text-sm text-sub">{t('supervisor.assessedSkills')}</p><p className="mt-2 text-2xl font-bold text-ink">{number(concepts.length)}</p></Card>
          <Card className="p-5"><p className="text-sm text-sub">{t('supervisor.strongSkills')}</p><p className="mt-2 text-2xl font-bold text-ink">{number(counts.met)}</p></Card>
          <Card className="p-5"><p className="text-sm text-sub">{t('supervisor.skillsToImprove')}</p><p className="mt-2 text-2xl font-bold text-ink">{number(data.gaps.length)}</p></Card>
        </div>
        <Card className="p-5"><h2 className="font-semibold text-ink">{t('supervisor.strongSkills')}</h2>
          <ul className="mt-3 flex flex-wrap gap-2">{concepts.filter(c => conceptState(c) === 'met').map(c => <li key={c.concept_id}><Badge tone="green">{c.concept_name}</Badge></li>)}</ul>
          {!counts.met && <p className="text-sm text-sub">{t('supervisor.buildingStrengths')}</p>}
        </Card>
        <Card className="p-5"><h2 className="font-semibold text-ink">{t('guidance.title')}</h2>
          {!data.gaps.length ? <p className="mt-3 text-sm text-sub">{t('guidance.noGaps')}</p> : <ol className="mt-3 space-y-3">{data.gaps.map((g, i) => <li key={g.concept_id} className="text-sm text-sub">
            <strong>{i + 1}. {g.concept_name}</strong><p className="mt-1">{t('supervisor.practiceRecommendation', { skill: g.concept_name })}</p>
          </li>)}</ol>}
          {!learnerId && <Link className={`${btnGhost} mt-4 inline-flex`} to="/assessments">{t('supervisor.start')}</Link>}
        </Card>
        <details className="rounded-xl border border-edge p-4">
          <summary className="cursor-pointer font-semibold text-ink">{t('supervisor.competencyEvidence')}</summary>
          <div className="mt-4 space-y-4">
            <Card className="p-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <h2 className="font-semibold text-ink">{t('cumulativeView.skillsHeading')}</h2>
                  <p className="mt-1 text-xs leading-relaxed text-mute">{t('cumulativeView.detailsHint')}</p>
                </div>
                <p role="status" className="text-xs text-mute">{t('cumulativeView.showing', { count: visible.length, total: concepts.length })}</p>
              </div>
              <div className="mt-3 flex flex-col gap-2 lg:flex-row lg:items-center">
                <label className="relative min-w-0 flex-1 lg:max-w-sm">
                  <span className="sr-only">{t('cumulativeView.search')}</span>
                  <Icon name="search" className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-mute" />
                  <input
                    type="search"
                    value={query}
                    onChange={e => setQuery(e.target.value)}
                    aria-label={t('cumulativeView.search')}
                    placeholder={t('cumulativeView.searchPlaceholder')}
                    className={`${inputCls} !py-2 pl-9`}
                  />
                </label>
                <div role="group" aria-label={t('cumulativeView.filter')} className="flex flex-wrap gap-1 rounded-lg border border-edge bg-panel p-1">
                  {['all', 'improve', 'met', 'neutral'].map(key => <button
                    key={key}
                    type="button"
                    aria-pressed={filter === key}
                    onClick={() => setFilter(key)}
                    className={`rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-cyan-400 ${
                      filter === key ? 'bg-cyan-400/15 text-cyan-200' : 'text-sub hover:bg-surface-hover hover:text-ink'
                    }`}
                  >{t(`cumulativeView.${key}`)} <span className="text-[10px]">{number(counts[key])}</span></button>)}
                </div>
              </div>
            </Card>
            {!visible.length ? <Card className="p-5"><EmptyState title={t('cumulativeView.noMatches')} /></Card> : <>
              <Card className="min-w-0 overflow-hidden p-5"><div className="relative h-80 min-w-0 max-w-full overflow-hidden"><CompetencyConceptBars concepts={visible} /></div></Card>
              <Card className="overflow-hidden">
                <p className="px-4 pt-3 text-xs text-mute sm:hidden">{t('common.swipeTable')}</p>
                <div className="overflow-x-auto" tabIndex={0} role="region" aria-label={t('cumulativeView.skillsHeading')}>
                  <table className="data-table min-w-[820px]">
                    <thead><tr><th>{t('common.concept')}</th><th>{t('competency.label')}</th><th>{t('competency.target')}</th><th>{t('supervisor.evidence')}</th><th>{t('supervisor.recurring')}</th></tr></thead>
                    <tbody>{visible.map(c => {
                      const state = conceptState(c)
                      const hasTarget = c.target_pct != null
                      const open = expandedId === c.concept_id
                      const detailId = `cumulative-detail-${c.concept_id}`
                      const gap = hasTarget ? Math.max(0, Number(c.target_pct) - Number(c.competency_pct)) : null
                      const sessions = c.contributing_sessions || []
                      return <Fragment key={c.concept_id}>
                        <tr>
                          <td>
                            <button
                              type="button"
                              aria-expanded={open}
                              aria-controls={detailId}
                              onClick={() => setExpandedId(open ? null : c.concept_id)}
                              className="group flex w-full items-start gap-2 text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-400"
                            >
                              <span className="min-w-0">
                                <span className="block font-medium text-ink group-hover:text-cyan-300">{c.concept_name}</span>
                                <span className="block text-xs text-mute">{c.concept_code}{c.subject_area ? ` · ${c.subject_area}` : ''}</span>
                              </span>
                              <Icon name="chevronDown" className={`ml-auto mt-0.5 h-4 w-4 shrink-0 text-mute transition-transform ${open ? 'rotate-180' : ''}`} />
                            </button>
                          </td>
                          <td>
                            {percent(c.competency_pct)}
                            <span className="block text-xs text-mute">{number(c.points_earned)} / {number(c.points_possible)}</span>
                            <div aria-hidden="true" className="relative mt-1.5 h-1.5 w-32 max-w-full overflow-hidden rounded-full bg-elev">
                              <span className={`block h-full rounded-full ${state === 'met' ? 'bg-emerald-400' : state === 'improve' ? 'bg-rose-400' : 'bg-cyan-400/70'}`} style={{ width: `${clampPct(c.competency_pct)}%` }} />
                              {hasTarget && <i className="absolute top-0 h-full w-px bg-ink/70" style={{ left: `${clampPct(c.target_pct)}%` }} />}
                            </div>
                          </td>
                          <td>{hasTarget ? percent(c.target_pct) : t('common.noBenchmark')}</td>
                          <td>{t('supervisor.evidenceCount', { questions: (c.contributing_attempts || []).length, assessments: sessions.length })}</td>
                          <td>
                            <Badge tone={hasTarget ? (c.below_target ? 'red' : 'green') : 'gray'}>{!hasTarget ? t('common.noBenchmark') : c.below_target ? t('common.belowTarget') : t('common.onTarget')}</Badge>
                            {hasTarget && <><p className="mt-1 text-xs text-mute">{t('supervisor.recurringCount', { count: c.below_target_assessments })}</p><p className="text-xs text-mute">{t('supervisor.recurringStrengthCount', { count: c.meeting_target_assessments || 0 })}</p></>}
                          </td>
                        </tr>
                        {open && <tr id={detailId} className="bg-elev/30">
                          <td colSpan={5}>
                            <div className="grid gap-4 lg:grid-cols-[1.2fr_1fr]">
                              <section aria-label={t('cumulativeView.interpretation')}>
                                <h4 className="text-xs font-semibold uppercase tracking-wide text-mute">{t('cumulativeView.interpretation')}</h4>
                                <p className="mt-1.5 text-sm leading-relaxed text-sub">{!hasTarget
                                  ? t('cumulativeView.noTargetHelp')
                                  : c.below_target ? t('cumulativeView.gap', { value: number(gap, { maximumFractionDigits: 2 }) }) : t('cumulativeView.metHelp')}</p>
                                {hasTarget && <p className="mt-1.5 text-xs text-mute">{t('supervisor.recurringCount', { count: c.below_target_assessments })} · {t('supervisor.recurringStrengthCount', { count: c.meeting_target_assessments || 0 })}</p>}
                              </section>
                              <section aria-label={t('cumulativeView.nextStep')} className="rounded-lg border border-edge bg-panel p-3">
                                <h4 className="text-xs font-semibold uppercase tracking-wide text-mute">{t('cumulativeView.nextStep')}</h4>
                                <p className="mt-1.5 flex gap-2 text-sm leading-relaxed text-sub"><Icon name="book" className="mt-0.5 h-4 w-4 shrink-0" /><span>{t(c.below_target ? 'cumulativeView.nextImprove' : hasTarget ? 'cumulativeView.nextMaintain' : 'cumulativeView.nextUnbenchmarked', { name: c.concept_name })}</span></p>
                                {sessions.length === 1 && <p className="mt-2 text-xs text-mute">{t('cumulativeView.limitedSkill')}</p>}
                              </section>
                            </div>
                          </td>
                        </tr>}
                      </Fragment>
                    })}</tbody>
                  </table>
                </div>
              </Card>
            </>}
          </div>
        </details>
        {data.summary.finalized_assessments < 2 && <p role="status" className="text-sm text-sub">{t('supervisor.limitedEvidence')}</p>}
      </>}
    </>}
    <Link className="text-sm text-cyan-300 underline" to={learnerId ? '/admin' : '/history'}>{t(learnerId ? 'nav.cohort' : 'nav.history')}</Link>
    </div>
  </>
}
