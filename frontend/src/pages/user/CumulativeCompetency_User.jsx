import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api, { apiMessage } from '../../api'
import { t, useLocale, number, percent } from '../../i18n'
import { Card, Icon, Badge } from '../../components/SharedComponents'
import { Loading, EmptyState, ErrorState } from '../../components/States'
import CompetencyPieChart from '../../components/CompetencyPieChart'

const normalize = value => String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/\u0111/g, 'd').toLowerCase()

export default function CumulativeCompetency_User() {
  useLocale()
  const { learnerId } = useParams()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [refreshing, setRefreshing] = useState(false)
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState('all')
  const [focusedConcept, setFocusedConcept] = useState(null)
  const requestSequence = useRef(0)
  const load = useCallback(() => {
    const sequence = ++requestSequence.current
    setError(null)
    setRefreshing(true)
    api.get(learnerId ? `/admin/learners/${learnerId}/competency/cumulative` : '/sessions/competency/cumulative')
      .then(r => { if (sequence === requestSequence.current) setData(r.data) })
      .catch(e => { if (sequence === requestSequence.current) setError(apiMessage(e)) })
      .finally(() => { if (sequence === requestSequence.current) setRefreshing(false) })
  }, [learnerId])
  useEffect(() => {
    setData(null)
    setQuery('')
    setFilter('all')
    load()
    return () => { requestSequence.current += 1 }
  }, [load])
  useEffect(() => {
    if (focusedConcept == null) return
    const row = document.getElementById(`cumulative-skill-${focusedConcept}`)
    if (row) {
      row.open = true
      row.querySelector('summary')?.focus({ preventScroll: true })
      row.scrollIntoView?.({ block: 'center', behavior: window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' })
    }
    setFocusedConcept(null)
  }, [focusedConcept, filter, query])
  const concepts = data?.concepts || []
  const counts = {
    all: concepts.length,
    improve: concepts.filter(c => c.target_pct != null && c.below_target).length,
    met: concepts.filter(c => c.target_pct != null && !c.below_target).length,
    neutral: concepts.filter(c => c.target_pct == null).length,
  }
  const visible = concepts.filter(c => {
    const state = c.target_pct == null ? 'neutral' : c.below_target ? 'improve' : 'met'
    return (filter === 'all' || filter === state) && normalize(`${c.concept_name} ${c.concept_code} ${c.subject_area || ''}`).includes(normalize(query.trim()))
  })
  return <div className="content-wrap cumulative-page py-6">
    <header className="cumulative-header">
      <div><h1>{t('supervisor.cumulative')}</h1><p>{t('cumulativeView.intro')}</p></div>
      <button type="button" className="cumulative-refresh" onClick={load} disabled={refreshing}><Icon name="reset" className={`h-3.5 w-3.5${refreshing ? ' animate-spin' : ''}`} />{t('dashboard.refresh')}</button>
    </header>
    {error && <ErrorState message={error} onRetry={load} />}
    {!data ? !error && <Loading /> : <>
      {concepts.length > 0 && <Card className="cumulative-comparison">
        <div className="cumulative-section-heading"><h2>{t('cumulativeView.chartTitle')}</h2><p>{t('cumulativeView.chartHelp')}</p></div>
        <CompetencyPieChart key={learnerId || 'learner'} concepts={concepts} />
      </Card>}
      {!concepts.length ? <EmptyState title={t('supervisor.noEvidence')} /> : <>
        {(data.gaps || []).length > 0 && <section className="cumulative-priorities" aria-label={t('cumulativeView.priorities')}>
          <h2>{t('cumulativeView.priorities')}</h2><p>{t('cumulativeView.priorityHelp')}</p>
          <ol>{data.gaps.slice(0, 3).map((c, i) => <li key={c.concept_id}><span className="cumulative-priority-number">{i + 1}</span><button type="button" className="cumulative-priority-link" onClick={() => { setQuery(''); setFilter('all'); setFocusedConcept(c.concept_id) }}>{c.concept_name}<Icon name="arrowRight" className="h-3 w-3" /></button><span>{t('cumulativeView.gap', { value: number(Math.max(0, Number(c.target_pct) - Number(c.competency_pct)), { maximumFractionDigits: 2 }) })}</span></li>)}</ol>
        </section>}
        <Card className="cumulative-skills">
          <div className="cumulative-section-heading"><h2>{t('cumulativeView.skillsHeading')}</h2><p>{t('cumulativeView.detailsHint')}</p></div>
          <div className="cumulative-controls">
            <input type="search" aria-label={t('cumulativeView.search')} placeholder={t('cumulativeView.search')} value={query} onChange={e => setQuery(e.target.value)} />
            <div className="cumulative-filters" role="group" aria-label={t('cumulativeView.filter')}>
              {['all', 'improve', 'met', 'neutral'].map(key => <button key={key} type="button" aria-pressed={filter === key} onClick={() => setFilter(key)}>{t(`cumulativeView.${key}`)} <span>{number(counts[key])}</span></button>)}
            </div>
          </div>
          <p className="cumulative-result-count" role="status">{t('cumulativeView.showing', { count: visible.length, total: concepts.length })}</p>
          {visible.length ? visible.map(c => <CumulativeConceptDetails key={c.concept_id} concept={c} />) : <div className="p-5"><EmptyState title={t('cumulativeView.noMatches')} /></div>}
        </Card>
        {data.summary.finalized_assessments < 2 && <p role="status" className="cumulative-footnote">{t('supervisor.limitedEvidence')}</p>}
      </>}
    </>}
    <Link className="cumulative-back" to={learnerId ? '/admin' : '/history'}><Icon name="arrowLeft" className="h-3.5 w-3.5" />{t(learnerId ? 'nav.cohort' : 'nav.history')}</Link>
  </div>
}

export function CumulativeConceptDetails({ concept: c }) {
  const hasTarget = c.target_pct != null
  const state = !hasTarget ? 'neutral' : c.below_target ? 'improve' : 'met'
  const status = !hasTarget ? 'common.noBenchmark' : c.below_target ? 'common.belowTarget' : 'common.onTarget'
  const gap = hasTarget ? Math.max(0, Number(c.target_pct) - Number(c.competency_pct)) : null
  const sessions = c.contributing_sessions || []
  return <details id={`cumulative-skill-${c.concept_id}`} className={`cumulative-skill ${state}`}>
    <summary>
      <div className="cumulative-skill-name"><h3>{c.concept_name}</h3>{c.subject_area && <span>{c.subject_area}</span>}</div>
      <div className="cumulative-skill-measure">
        <div><strong>{percent(c.competency_pct)}</strong><span>{hasTarget ? t('cumulativeView.target', { value: percent(c.target_pct) }) : t('common.noBenchmark')}</span></div>
        <div className="cumulative-track" aria-hidden="true"><span style={{ width: `${Math.max(0, Math.min(100, Number(c.competency_pct)))}%` }} />{hasTarget && <i style={{ left: `${Math.max(0, Math.min(100, Number(c.target_pct)))}%` }} />}</div>
      </div>
      <Badge tone={state === 'met' ? 'green' : state === 'improve' ? 'amber' : undefined}>{t(status)}</Badge>
      <Icon name="chevronDown" className="cumulative-detail-chevron h-4 w-4" />
    </summary>
    <div className="cumulative-skill-detail">
      <div className="cumulative-detail-grid cumulative-student-detail">
        <section><h4>{t('cumulativeView.interpretation')}</h4>
          <p>{!hasTarget ? t('cumulativeView.noTargetHelp') : c.below_target ? t('cumulativeView.gap', { value: number(gap, { maximumFractionDigits: 2 }) }) : t('cumulativeView.metHelp')}</p>
          {hasTarget && <><p>{t('supervisor.recurringCount', { count: c.below_target_assessments || 0 })}</p><p>{t('supervisor.recurringStrengthCount', { count: c.meeting_target_assessments || 0 })}</p></>}
        </section>
      </div>
      <div className="cumulative-next-step"><Icon name="book" className="h-4 w-4 shrink-0" /><p>{t(c.below_target ? 'cumulativeView.nextImprove' : hasTarget ? 'cumulativeView.nextMaintain' : 'cumulativeView.nextUnbenchmarked', { name: c.concept_name })}</p></div>
      {sessions.length === 1 && <p className="cumulative-limited">{t('cumulativeView.limitedSkill')}</p>}
    </div>
  </details>
}
