import { useEffect } from 'react'

// Shared design-system primitives. Visual ideas adapted from the
// origin/frontend static-pages prototypes — stat cards, tinted status
// badges, lettered option rows, outcome-tinted panels — rebuilt for the
// real React app. No prototype assets or data are used.

const PATHS = {
  clock: 'M12 8v4l3 2M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z',
  check: 'm4 12.5 5 5L20 6.5',
  x: 'M6 6l12 12M18 6 6 18',
  alert: 'M12 3 2 20h20L12 3Zm0 7v4m0 3.5v.5',
  info: 'M12 8h.01M12 11v5m9-4a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z',
  inbox: 'M3 13h5l2 3h4l2-3h5M5 5h14a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Z',
  book: 'M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2V5Zm0 16a2 2 0 0 1 2-2h13',
  chart: 'M4 20V10m6 10V4m6 16v-8m4 8H2',
  spark: 'M12 3l1.9 5.6L19.5 10l-5.6 1.9L12 17.5l-1.9-5.6L4.5 10l5.6-1.4L12 3Z',
  code: 'm8 6-6 6 6 6m8-12 6 6-6 6',
  edit: 'M14 4l6 6L9 21H3v-6L14 4Z',
  target: 'M12 21a9 9 0 1 1 0-18 9 9 0 0 1 0 18Zm0-5a4 4 0 1 1 0-8 4 4 0 0 1 0 8Z',
  users: 'M16 19a4 4 0 0 0-8 0m8-10a4 4 0 1 1-8 0 4 4 0 0 1 8 0Zm6 10a5.5 5.5 0 0 0-3.3-5M17 4.6a4 4 0 0 1 0 7.8',
  flag: 'M5 21V4c4-2 8 2 12 0v10c-4 2-8-2-12 0',
  play: 'M6 4.5v15l13-7.5-13-7.5Z',
}

export function Icon({ name, className = 'h-4 w-4' }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d={PATHS[name]} />
    </svg>
  )
}

const TONES = {
  gray: 'bg-gray-100 text-gray-700',
  blue: 'bg-blue-50 text-blue-700',
  teal: 'bg-teal-50 text-teal-700',
  violet: 'bg-violet-50 text-violet-700',
  green: 'bg-green-50 text-green-700',
  amber: 'bg-amber-50 text-amber-700',
  red: 'bg-red-50 text-red-700',
}

export function Badge({ tone = 'gray', children, className = '' }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${TONES[tone]} ${className}`}
    >
      {children}
    </span>
  )
}

const TYPE_TONES = { mcq: 'blue', sql: 'teal', essay: 'violet' }
const TYPE_LABELS = { mcq: 'MCQ', sql: 'SQL', essay: 'Essay' }

export function TypeBadge({ type }) {
  return <Badge tone={TYPE_TONES[type] || 'gray'}>{TYPE_LABELS[type] || type}</Badge>
}

const STATUS_TONES = {
  in_progress: 'blue',
  completed: 'green',
  timed_out: 'amber',
  draft: 'gray',
  active: 'green',
  closed: 'gray',
  validated: 'green',
  rejected: 'red',
  pending: 'amber',
  approved: 'blue',
  confirmed: 'green',
  disabled: 'amber',
}

export function StatusBadge({ status }) {
  return <Badge tone={STATUS_TONES[status] || 'gray'}>{status.replaceAll('_', ' ')}</Badge>
}

export function Card({ className = '', children }) {
  return (
    <div className={`rounded-xl border border-gray-200 bg-white shadow-sm ${className}`}>
      {children}
    </div>
  )
}

// Banded card header — title row separated from the body, like the
// prototypes' section panels.
export function CardTitle({ title, children }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-gray-100 px-4 py-3">
      <h2 className="text-sm font-semibold text-gray-800">{title}</h2>
      {children}
    </div>
  )
}

export function PageHeader({ title, subtitle, children }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-gray-500">{subtitle}</p>}
      </div>
      {children}
    </div>
  )
}

export function StatCard({ label, value, icon, hint }) {
  return (
    <Card className="p-4">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-2xl font-semibold tracking-tight text-gray-900">{value}</p>
          <p className="mt-0.5 text-sm text-gray-500">{label}</p>
          {hint && <p className="mt-1 text-xs text-gray-400">{hint}</p>}
        </div>
        {icon && (
          <span className="rounded-lg bg-blue-50 p-2 text-blue-600">
            <Icon name={icon} className="h-5 w-5" />
          </span>
        )}
      </div>
    </Card>
  )
}

// Competency bar with a benchmark tick — from the learner prototype's
// per-concept score list. Value/target are 0–100 numbers or null.
export function ScoreBar({ value, target }) {
  const pct = value == null ? 0 : Math.max(0, Math.min(100, Number(value)))
  const targetPct = target == null ? null : Math.max(0, Math.min(100, Number(target)))
  const met = targetPct == null || pct >= targetPct
  return (
    <div className="flex items-center gap-2">
      <div className="relative h-2 w-full max-w-40 rounded-full bg-gray-100">
        <div
          className={`h-2 rounded-full ${met ? 'bg-emerald-500' : 'bg-red-400'}`}
          style={{ width: `${pct}%` }}
        />
        {targetPct != null && (
          <span
            className="absolute -top-0.5 h-3 w-0.5 bg-gray-500"
            style={{ left: `${targetPct}%` }}
            title={`target ${target}%`}
          />
        )}
      </div>
      <span className="w-12 shrink-0 text-right text-xs tabular-nums text-gray-600">
        {value == null ? '—' : `${Number(value).toFixed(0)}%`}
      </span>
    </div>
  )
}

// Consistent labelled form control — the prototypes label every field.
export function Field({ label, htmlFor, children, className = '' }) {
  return (
    <div className={className}>
      <label htmlFor={htmlFor} className="mb-1 block text-sm font-medium text-gray-700">
        {label}
      </label>
      {children}
    </div>
  )
}

export const inputCls =
  'w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100'

// Accessible modal confirmation — the prototypes use a small confirm
// dialog before submitting an assessment.
export function ConfirmDialog({ open, title, children, confirmLabel, onConfirm, onCancel }) {
  useEffect(() => {
    if (!open) return
    const onKey = (e) => e.key === 'Escape' && onCancel()
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open, onCancel])
  if (!open) return null
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/40 p-4"
      role="presentation"
      onClick={onCancel}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="w-full max-w-sm rounded-xl bg-white p-5 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-base font-semibold text-gray-900">{title}</h2>
        <div className="mt-2 text-sm text-gray-600">{children}</div>
        <div className="mt-4 flex justify-end gap-2">
          <button
            type="button"
            onClick={onCancel}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
          >
            Keep going
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className="rounded-md bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700"
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}

export function Notice({ children }) {
  return (
    <p
      role="status"
      className="mt-3 flex items-center gap-2 rounded-md border border-green-200 bg-green-50 p-2.5 text-sm text-green-800"
    >
      <Icon name="check" className="h-4 w-4 shrink-0" />
      <span>{children}</span>
    </p>
  )
}
