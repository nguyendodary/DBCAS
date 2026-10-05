// Shared async-state primitives: every data view renders one of these
// instead of leaving the learner staring at a blank area.
export function Loading({ label = 'Loading…' }) {
  return (
    <p role="status" className="py-8 text-center text-sm text-gray-500">
      {label}
    </p>
  )
}

export function ErrorState({ message, onRetry }) {
  return (
    <div role="alert" className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
      <p>{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-2 rounded bg-red-600 px-3 py-1 text-white hover:bg-red-700"
        >
          Retry
        </button>
      )}
    </div>
  )
}

export function EmptyState({ title, children }) {
  return (
    <div className="rounded-md border border-dashed border-gray-300 p-8 text-center">
      <p className="font-medium text-gray-700">{title}</p>
      {children && <div className="mt-1 text-sm text-gray-500">{children}</div>}
    </div>
  )
}
