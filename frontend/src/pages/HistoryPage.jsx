import { t, useLocale, message, number, percent, dateTime, time, dateOnly, intlLocale } from '../i18n'
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api, { apiMessage } from '../api'
import { EmptyState, ErrorState, Loading } from '../components/States'
import { Card, PageHeader, StatusBadge } from '../components/ui'

// UC18 — the learner's assessment history.
export default function HistoryPage() {
  useLocale()
  const [items, setItems] = useState(null)
  const [error, setError] = useState(null)

  const load = useCallback(() => {
    setError(null)
    api
      .get('/sessions')
      .then((r) => setItems(r.data))
      .catch((e) => {
        setError(apiMessage(e, message('history.loadError')))
        setItems([])
      })
  }, [])

  useEffect(load, [load])

  if (error) return <ErrorState message={error} onRetry={load} />
  if (items === null) return <Loading label={t('history.loading')} />

  return (
    <div className="space-y-4">
      <PageHeader title={t('history.title')} />
      {items.length === 0 ? (
        <EmptyState title={t('history.empty')}>{t('history.emptyBody')}</EmptyState>
      ) : (
        <Card className="overflow-hidden">
          <ul className="divide-y divide-edge">
          {items.map((s) => (
            <li key={s.session_id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-4 transition-colors hover:bg-surface-hover">
              <div className="min-w-0">
                <p className="font-medium text-ink">{s.assessment_title}</p>
                <p className="mt-0.5 text-xs text-mute">
                  {dateTime(s.submitted_at || s.started_at)} ·{' '}
                  {t('history.answered', { answered: number(s.answered_count), served: number(s.served_count) })}
                </p>
                {s.status !== 'in_progress' && <>
                  <p className="mt-2 text-sm text-sub">{s.pending_grading_count ? t('history.pending') : s.failed_grading_count ? t('history.retryGrade') : s.overall_result_pct != null ? t('history.result', { value: percent(s.overall_result_pct) }) : t('history.noGraded')}</p>
                  <ul aria-label={t('history.perConcept')} className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-mute">
                    {(s.concepts || []).map((c) => <li key={c.concept_id}>{c.concept_name}: {percent(c.competency_pct, { minimumFractionDigits: 2 })}{c.target_pct == null ? t('history.unbenchmarked') : c.below_target ? t('history.below') : t('history.meets')}</li>)}
                  </ul>
                </>}
              </div>
              <div className="flex items-center gap-3">
                <StatusBadge status={s.status} />
                {s.status === 'in_progress' ? (
                  <Link
                    to={`/exam/${s.session_id}`}
                    className="text-sm font-medium text-cyan-300 hover:underline"
                  >{t('assessment.resume')}</Link>
                ) : (
                  <Link
                    to={`/history/${s.session_id}`}
                    className="text-sm font-medium text-cyan-300 hover:underline"
                  >{t('history.evidence')}</Link>
                )}
              </div>
            </li>
          ))}
          </ul>
        </Card>
      )}
    </div>
  )
}
