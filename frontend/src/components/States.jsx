import { Icon } from './ui'

// Shared async-state primitives: every data view renders one of these
// instead of leaving the learner staring at a blank area.
export function Loading({ label = 'Loading…' }) {
  return (
    <p role="status" className="flex items-center justify-center gap-2 py-8 text-sm text-gray-500">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600" aria-hidden="true" />
      {label}
    </p>
  )
}

export function ErrorState({ message, onRetry }) {
  return (
    <div role="alert" className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
      <Icon name="alert" className="mt-0.5 h-4 w-4 shrink-0" />
      <div>
        <p>{message}</p>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="mt-2 rounded-md bg-red-600 px-3 py-1 text-white hover:bg-red-700"
          >
            Retry
          </button>
        )}
      </div>
    </div>
  )
}

export function EmptyState({ title, children }) {
  return (
    <div className="rounded-xl border border-dashed border-gray-300 p-8 text-center">
      <span className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-gray-100 text-gray-400">
        <Icon name="inbox" className="h-5 w-5" />
      </span>
      <p className="font-medium text-gray-700">{title}</p>
      {children && <div className="mt-1 text-sm text-gray-500">{children}</div>}
    </div>
  )
}
