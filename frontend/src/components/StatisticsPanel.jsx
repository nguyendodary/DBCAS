import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api, { apiMessage } from '../api'
import { t, useLocale, number, percent, dateTime } from '../i18n'
import { Card, btnGhost } from './ui'
import { EmptyState, ErrorState, Loading } from './States'

export function statisticsCsv(data, names = {}) {
  const escape = value => `"${String(value ?? '').replace(/^[=+@\-\t\r]/, "'$&").replaceAll('"', '""')}"`
  const rows = [[t('analytics.dimension'), t('analytics.label'), t('analytics.score'), t('analytics.evidence')]]
  rows.push([t('analytics.score'), t('analytics.scope'), data.dimensions.overall.competency_pct, data.dimensions.overall.evidence_count])
  for (const key of ['clos', 'topics', 'difficulties']) {
    for (const item of data.dimensions[key]) rows.push([t(`analytics.${key}`), item.label, item.competency_pct, item.evidence_count])
  }
  rows.push([], [t('analytics.ranking'), t('analytics.learner'), t('analytics.score')])
  for (const row of data.ranking) rows.push([row.rank, names[row.learner_id] || `#${row.learner_id}`, row.competency_pct])
  rows.push([], [t('analytics.distribution'), t('analytics.sessions')])
  for (const bucket of data.score_distribution) rows.push([`${bucket.lower_bound}–${bucket.upper_bound}%`, bucket.count])
  return '\uFEFF' + rows.map(row => row.map(escape).join(',')).join('\r\n')
}

export default function StatisticsPanel({ admin = false, assessmentId = '', learners = [] }) {
  useLocale()
  const { learnerId } = useParams()
  const [data, setData] = useState(null)
  const [rank, setRank] = useState(null)
  const [error, setError] = useState(null)
  const [offset, setOffset] = useState(0)
  const [retry, setRetry] = useState(0)
  const sequence = useRef(0)
  const names = Object.fromEntries(learners.map(learner => [learner.account_id, learner.full_name || learner.email]))
  useEffect(() => { setOffset(0) }, [assessmentId, learnerId])
  const load = useCallback(() => {
    const request = ++sequence.current
    const controller = new AbortController()
    setError(null)
    setData(null)
    const params = { limit: 10, offset, ...(assessmentId ? { assessment_id: Number(assessmentId) } : {}),
      ...(admin && learnerId ? { learner_id: Number(learnerId) } : {}) }
    Promise.all([
      api.get(admin ? '/admin/analytics/statistics' : '/sessions/statistics', { params, signal: controller.signal }),
      admin ? Promise.resolve(null) : api.get('/sessions/ranking', { params: assessmentId ? { assessment_id: Number(assessmentId) } : {}, signal: controller.signal }),
    ]).then(([statistics, position]) => {
      if (request !== sequence.current) return
      if (!statistics.data?.dimensions) throw new Error('Invalid statistics response')
      setData(statistics.data)
      setRank(position?.data || null)
    }).catch(err => { if (request === sequence.current) setError(apiMessage(err)) })
    return () => { sequence.current += 1; controller.abort() }
  }, [admin, learnerId, assessmentId, offset])
  useEffect(load, [load, retry])

  function download() {
    const url = URL.createObjectURL(new Blob([statisticsCsv(data, names)], { type: 'text/csv;charset=utf-8' }))
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = 'dbcas-report.csv'
    anchor.click()
    setTimeout(() => URL.revokeObjectURL(url), 0)
  }

  return <section aria-label={t('analytics.title')} className="space-y-4">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div><h2 className="text-lg font-bold text-ink">{t('analytics.title')}</h2><p className="mt-1 text-xs text-mute">{t('analytics.scope')}</p></div>
      {admin && data && <button className={btnGhost} onClick={download}>{t('analytics.export')}</button>}
    </div>
    {error ? <ErrorState message={error} onRetry={() => setRetry(value => value + 1)} /> : !data ? <Loading /> : <>
      <div className="grid gap-4 sm:grid-cols-3">
        <Card className="p-4"><p className="text-sm text-sub">{t('analytics.score')}</p><p className="mt-2 text-2xl font-bold text-ink">{percent(data.dimensions.overall.competency_pct)}</p></Card>
        <Card className="p-4"><p className="text-sm text-sub">{t('analytics.sessions')}</p><p className="mt-2 text-2xl font-bold text-ink">{number(data.published_formal_sessions)}</p></Card>
        {!admin && <Card className="p-4"><p className="text-sm text-sub">{t('analytics.ownRank')}</p><p className="mt-2 text-2xl font-bold text-ink">{rank?.rank == null ? '—' : `${number(rank.rank)} / ${number(rank.participants)}`}</p><p className="mt-1 text-xs text-mute">{t('analytics.rankHelp')}</p></Card>}
      </div>
      {!data.graded_sessions ? <EmptyState title={t('analytics.empty')}><Link className="text-cyan-300 underline" to={admin ? '/admin/assessments' : '/assessments'}>{t('nav.assessments')}</Link></EmptyState> : <details className="rounded-xl border border-edge p-4">
        <summary className="cursor-pointer font-semibold text-ink">{t('analytics.details')}</summary>
        <div className="mt-4 space-y-4">
        <div className="grid gap-4 lg:grid-cols-3">
          {['clos', 'topics', 'difficulties'].map(key => <Card key={key} className="p-4">
            <h3 className="font-semibold text-ink">{t(`analytics.${key}`)}</h3>
            <ul className="mt-3 space-y-3">{data.dimensions[key].map(row => <li key={row.key} className="text-sm">
              <div className="flex justify-between gap-3 text-sub"><span>{key === 'difficulties' ? t('analytics.level', { level: row.label }) : row.label}</span><strong className="shrink-0 text-ink">{percent(row.competency_pct)}</strong></div>
              <progress aria-label={`${row.label}: ${percent(row.competency_pct)}`} max="100" value={Number(row.competency_pct || 0)} className="mt-1 h-2 w-full accent-cyan-400" />
            </li>)}</ul>
            {!data.dimensions[key].length && <p className="mt-3 text-sm text-mute">{t('analytics.noEvidence')}</p>}
          </Card>)}
        </div>
        {data.dimensions.clo_mapping_unknown_attempts > 0 && <p className="text-xs text-mute">{t('analytics.unknownClo', { count: data.dimensions.clo_mapping_unknown_attempts })}</p>}
        <div className="grid gap-4 lg:grid-cols-2">
          <Card className="p-4"><h3 className="font-semibold text-ink">{t('analytics.distribution')}</h3><ul className="mt-3 space-y-2">
            {data.score_distribution.map(bucket => <li key={bucket.lower_bound} className="flex justify-between text-sm text-sub"><span>{bucket.lower_bound}–{bucket.upper_bound}%</span><strong>{number(bucket.count)}</strong></li>)}
          </ul></Card>
          <Card className="p-4"><h3 className="font-semibold text-ink">{t('analytics.progress')}</h3><ul className="mt-3 space-y-2">
            {data.progress.map(point => <li key={point.session_id} className="flex flex-wrap justify-between gap-2 text-sm text-sub"><Link className="text-cyan-300 underline" to={admin ? `/admin/grading/${point.session_id}` : `/history/${point.session_id}`}>{dateTime(point.completed_at)}</Link><strong>{percent(point.competency_pct)}</strong></li>)}
          </ul>
          {data.progress_total > 10 && <nav aria-label={t('analytics.progress')} className="mt-4 flex gap-3"><button className={btnGhost} disabled={offset === 0} onClick={() => setOffset(value => Math.max(0, value - 10))}>{t('assessment.prevPage')}</button><button className={btnGhost} disabled={offset + 10 >= data.progress_total} onClick={() => setOffset(value => value + 10)}>{t('assessment.nextPage')}</button></nav>}
          </Card>
        </div>
        {admin && !learnerId && <Card className="p-4"><h3 className="font-semibold text-ink">{t('analytics.ranking')}</h3><p className="mt-1 text-xs text-mute">{t('analytics.rankHelp')}</p><ol className="mt-3 divide-y divide-edge">{data.ranking.map(row => <li key={row.learner_id} className="flex justify-between gap-3 py-3 text-sm"><Link className="text-cyan-300 underline" to={`/admin/learners/${row.learner_id}/competency`}>{number(row.rank)}. {names[row.learner_id] || `#${row.learner_id}`}</Link><strong>{percent(row.competency_pct)}</strong></li>)}</ol></Card>}
        </div>
      </details>}
    </>}
  </section>
}
