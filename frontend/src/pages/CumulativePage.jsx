import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api, { apiMessage } from '../api'
import { t, useLocale, number, percent } from '../i18n'
import { Card, Badge, btnGhost } from '../components/ui'
import { Loading, EmptyState, ErrorState } from '../components/States'
import { CompetencyConceptBars } from '../components/CompetencyCharts'

export default function CumulativePage() {
  useLocale()
  const { learnerId } = useParams()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
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
    load()
    return () => { requestSequence.current += 1 }
  }, [load])
  return <div className="content-wrap space-y-5 py-6">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <h1 className="text-2xl font-bold text-ink">{t('supervisor.cumulative')}</h1>
      <button className={btnGhost} onClick={load}>{t('dashboard.refresh')}</button>
    </div>
    <p className="text-sm text-sub">{t('supervisor.cumulativeHelp')}</p>
    {error ? <ErrorState message={error} onRetry={load} /> : !data ? <Loading /> : <>
      <p className="text-sm text-sub">{t('supervisor.publishedCount', { count: data.summary.finalized_assessments })}</p>
      {!data.concepts.length ? <EmptyState title={t('supervisor.noEvidence')} /> : <>
        <div className="grid gap-4 sm:grid-cols-3">
          <Card className="p-5"><p className="text-sm text-sub">{t('supervisor.assessedSkills')}</p><p className="mt-2 text-2xl font-bold text-ink">{number(data.concepts.length)}</p></Card>
          <Card className="p-5"><p className="text-sm text-sub">{t('supervisor.strongSkills')}</p><p className="mt-2 text-2xl font-bold text-ink">{number(data.concepts.filter(c => c.target_pct != null && !c.below_target).length)}</p></Card>
          <Card className="p-5"><p className="text-sm text-sub">{t('supervisor.skillsToImprove')}</p><p className="mt-2 text-2xl font-bold text-ink">{number(data.gaps.length)}</p></Card>
        </div>
        <Card className="p-5"><h2 className="font-semibold text-ink">{t('supervisor.strongSkills')}</h2>
          <ul className="mt-3 flex flex-wrap gap-2">{data.concepts.filter(c => c.target_pct != null && !c.below_target).map(c => <li key={c.concept_id}><Badge tone="green">{c.concept_name}</Badge></li>)}</ul>
          {!data.concepts.some(c => c.target_pct != null && !c.below_target) && <p className="text-sm text-sub">{t('supervisor.buildingStrengths')}</p>}
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
        <Card className="min-w-0 overflow-hidden p-5"><div className="relative h-80 min-w-0 max-w-full overflow-hidden"><CompetencyConceptBars concepts={data.concepts} /></div></Card>
        <Card className="overflow-hidden">
          <div className="overflow-x-auto" tabIndex={0} role="region" aria-label={t('supervisor.cumulative')}>
            <table className="data-table min-w-[700px]">
              <thead><tr><th>{t('common.concept')}</th><th>{t('competency.label')}</th><th>{t('competency.target')}</th><th>{t('supervisor.evidence')}</th><th>{t('supervisor.recurring')}</th></tr></thead>
              <tbody>{data.concepts.map(c => <tr key={c.concept_id}>
                <td>{c.concept_name}<span className="block text-xs text-mute">{c.concept_code}</span></td>
                <td>{percent(c.competency_pct)}<span className="block text-xs text-mute">{number(c.points_earned)} / {number(c.points_possible)}</span></td>
                <td>{c.target_pct == null ? t('common.noBenchmark') : percent(c.target_pct)}</td>
                <td>{t('supervisor.evidenceCount', { questions: c.contributing_attempts.length, assessments: c.contributing_sessions.length })}</td>
                <td><Badge tone={c.below_target ? 'red' : 'green'}>{c.target_pct == null ? t('common.noBenchmark') : c.below_target ? t('common.belowTarget') : t('common.onTarget')}</Badge>{c.target_pct != null && <><p className="mt-1 text-xs text-mute">{t('supervisor.recurringCount', { count: c.below_target_assessments })}</p><p className="text-xs text-mute">{t('supervisor.recurringStrengthCount', { count: c.meeting_target_assessments || 0 })}</p></>}</td>
              </tr>)}</tbody>
            </table>
          </div>
        </Card>
          </div>
        </details>
        {data.summary.finalized_assessments < 2 && <p role="status" className="text-sm text-sub">{t('supervisor.limitedEvidence')}</p>}
      </>}
    </>}
    <Link className="text-sm text-cyan-300 underline" to={learnerId ? '/admin' : '/history'}>{t(learnerId ? 'nav.cohort' : 'nav.history')}</Link>
  </div>
}
