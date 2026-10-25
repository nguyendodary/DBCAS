import { Link } from 'react-router-dom'
import { t, useLocale } from '../i18n'
import { ActionSpinner } from './States'
import { Icon } from './SharedComponents'

const COPY = {
  submitting: ['submittingTitle', 'submittingBody'],
  auto_grading: ['gradingTitle', 'gradingBody'],
  pending_review: ['reviewTitle', 'reviewBody'],
  reviewed: ['reviewedTitle', 'reviewedBody'],
  grading_failed: ['failedTitle', 'failedBody'],
}

export default function GradingStatusPanel({
  status = 'auto_grading',
  timedOut = false,
  refreshError = false,
  refreshing = false,
  onRefresh,
}) {
  useLocale()
  const effectiveStatus = timedOut && status === 'auto_grading' ? 'takingLonger' : status
  const [title, body] = COPY[status] || COPY.auto_grading
  const isWorking = status === 'submitting' || status === 'auto_grading'
  const copyTitle = effectiveStatus === 'takingLonger' ? 'takingLongerTitle' : title
  const copyBody = effectiveStatus === 'takingLonger' ? 'takingLongerBody' : body

  return (
    <div className="mx-auto flex min-h-[55vh] w-full max-w-3xl items-center justify-center px-4 py-10 sm:px-6">
      <section className="surface-card w-full max-w-xl rounded-2xl border border-edge bg-panel p-6 text-center shadow-xl sm:p-10">
        <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-full bg-cyan-400/10 text-cyan-300 ring-1 ring-inset ring-cyan-400/20">
          {isWorking
            ? <ActionSpinner className="h-9 w-9" />
            : <Icon name={status === 'grading_failed' ? 'alert' : status === 'reviewed' ? 'check' : 'file'} className="h-8 w-8" />}
        </div>
        <div role="status" aria-live="polite" aria-busy={isWorking}>
          <h1 className="text-xl font-bold text-ink sm:text-2xl">{t(`gradingWait.${copyTitle}`)}</h1>
          <p className="mx-auto mt-3 max-w-lg text-sm leading-6 text-sub">{t(`gradingWait.${copyBody}`)}</p>
          {status === 'auto_grading' && <p className="mt-3 text-sm text-mute">{t('gradingWait.timingNote')}</p>}
        </div>
        {refreshError && <p role="alert" className="mt-4 text-sm text-amber-300">{t('gradingWait.refreshError')}</p>}
        {effectiveStatus === 'takingLonger' && <p className="mt-4 text-sm text-amber-300">{t('gradingWait.takingLongerHint')}</p>}
        {status !== 'submitting' && (
          <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
            {onRefresh && <button type="button" className="action-button" onClick={onRefresh} disabled={refreshing}>
              {refreshing && <ActionSpinner />}{refreshing ? t('gradingWait.refreshing') : t('gradingWait.refresh')}
            </button>}
            <Link to="/history" className="text-sm font-medium text-cyan-300 underline-offset-4 hover:underline">{t('gradingWait.history')}</Link>
          </div>
        )}
      </section>
    </div>
  )
}
