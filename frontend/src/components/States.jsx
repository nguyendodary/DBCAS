import { t, useLocale, resolveMessage } from '../i18n'
import { Icon } from './ui'

// Shared async-state primitives: every data view renders one of these
// instead of leaving the learner staring at a blank area.
export function Loading({ label = t('common.loading') }) {
  useLocale()
  return (
    <div role="status" className="space-y-3 py-5" aria-label={label}>
      <span className="sr-only">{label}</span>
      <div className="skeleton h-5 w-44" aria-hidden="true" />
      <div className="skeleton h-16 w-full" aria-hidden="true" />
      <div className="skeleton h-16 w-full opacity-60" aria-hidden="true" />
    </div>
  )
}

export function ActionSpinner() {
  return <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-r-transparent" aria-hidden="true" />
}

export function ErrorState({ message, onRetry }) {
  useLocale()
  return (
    <div role="alert" className="flex items-start gap-3 rounded-lg border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-200">
      <Icon name="alert" className="mt-0.5 h-4 w-4 shrink-0" />
      <div>
        <p>{resolveMessage(message)}</p>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="mt-3 rounded-md border border-rose-400/40 px-3 py-1.5 font-medium text-rose-100 hover:bg-rose-400/10"
          >{t('common.retry')}</button>
        )}
      </div>
    </div>
  )
}

export function EmptyState({ title, children }) {
  return (
    <div className="rounded-xl border border-dashed border-edge2 bg-panel/50 p-8 text-center sm:p-10">
      <span className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-elev text-mute">
        <Icon name="inbox" className="h-5 w-5" />
      </span>
      <p className="font-medium text-ink">{title}</p>
      {children && <div className="mt-1 text-sm text-mute">{children}</div>}
    </div>
  )
}
