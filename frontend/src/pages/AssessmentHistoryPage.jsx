import { t, useLocale, message, number, percent, dateTime, time, dateOnly, intlLocale } from '../i18n'
import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import api, { apiMessage } from '../api'
import { EmptyState, ErrorState, Loading } from '../components/States'
import { Card, HeroBand, Icon, IconChip, StatusBadge } from '../components/ui'
import heroPoster from '../assets/brand/learner-background.jpg'
import heroVideo from '../assets/brand/learner-background.mp4'
import usePendingResults from '../usePendingResults'

// UC18 — the learner's assessment history. Row composition follows the
// learner prototype's result list: icon chip, title + meta, status pill and
// the evidence/resume action.
export default function AssessmentHistoryPage() {
  useLocale()
  const [items, setItems] = useState(null)
  const [error, setError] = useState(null)
  const requestSequence = useRef(0)

  const load = useCallback(() => {
    const sequence = ++requestSequence.current
    setError(null)
    api
      .get('/sessions')
      .then((r) => { if (sequence === requestSequence.current) setItems(r.data) })
      .catch((e) => {
        if (sequence !== requestSequence.current) return
        setError(apiMessage(e, message('history.loadError')))
        setItems([])
      })
  }, [])

  useEffect(() => {
    load()
    return () => { requestSequence.current += 1 }
  }, [load])
  usePendingResults(items?.some(s => s.status !== 'in_progress' && s.release_status === 'auto_grading'), load)

  if (error) return <ErrorState message={error} onRetry={load} />
  if (items === null) return <Loading label={t('history.loading')} />

  return (
    <div className="space-y-5">
      <HeroBand eyebrow={t('history.heroEyebrow')} title={t('history.title')} subtitle={t('history.heroSub')} videoSrc={heroVideo} videoPoster={heroPoster} />
      <div className="flex justify-end">
        <button type="button" className="inline-flex items-center gap-1.5 border-0 bg-transparent p-0 text-xs font-medium text-sub transition-colors hover:text-accent focus-visible:outline-1 focus-visible:outline-offset-4 focus-visible:outline-accent" onClick={load}>
          <Icon name="reset" className="h-3.5 w-3.5" />
          {t('dashboard.refresh')}
        </button>
      </div>
      {items.length === 0 ? (
        <EmptyState title={t('history.empty')}>{t('history.emptyBody')}</EmptyState>
      ) : (
        <Card className="overflow-hidden">
          <ul className="divide-y divide-edge">
          {items.map((s) => (
            <li key={s.session_id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-4 transition-colors hover:bg-surface-hover">
              <div className="flex min-w-0 items-start gap-4">
                <IconChip name={s.status === 'in_progress' ? 'play' : 'file'} large className="mt-0.5" />
                <div className="min-w-0">
                  <p className="font-medium text-ink">{s.assessment_title}</p>
                  {s.assembly_mode && <p className="text-xs text-mute">{t(`supervisor.${s.assembly_mode}`)} · {t(`supervisor.${s.difficulty}`)}</p>}
                  <p className="mt-0.5 text-xs text-mute">
                    {dateTime(s.submitted_at || s.started_at)} ·{' '}
                    {t('history.answered', { answered: number(s.answered_count), served: number(s.served_count) })}
                  </p>
                  {s.status !== 'in_progress' && <>
                    <p className="mt-2 text-sm text-sub">{s.release_status && s.release_status !== 'published' ? t(`supervisor.${s.release_status}`) : s.pending_grading_count ? t('history.pending') : s.failed_grading_count ? t('history.retryGrade') : s.overall_result_pct != null ? t('history.result', { value: percent(s.overall_result_pct) }) : t('history.noGraded')}</p>
                    <ul aria-label={t('history.perConcept')} className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-mute">
                      {(s.concepts || []).map((c) => <li key={c.concept_id}>{c.concept_name}: {percent(c.competency_pct, { minimumFractionDigits: 2 })}{c.target_pct == null ? t('history.unbenchmarked') : c.below_target ? t('history.below') : t('history.meets')}</li>)}
                    </ul>
                  </>}
                </div>
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
