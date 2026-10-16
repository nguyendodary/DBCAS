import { t, useLocale, resolveMessage, percent, number, statusLabel, typeLabel } from '../i18n'
import { useEffect, useId, useRef } from 'react'
import { createPortal } from 'react-dom'
import BackgroundVideo from './BackgroundVideo'

// Shared design-system primitives. Visual ideas adapted from the
// origin/frontend static-pages prototypes — stat cards, tinted status
// badges, lettered option rows, outcome-tinted panels — rebuilt for the
// real React app on the dark token set in index.css. No prototype assets
// or data are used.

const PATHS = {
  globe: 'M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0ZM3 12h18M12 3c5 5 5 13 0 18-5-5-5-13 0-18Z',
  clock: 'M12 8v4l3 2M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z',
  check: 'm4 12.5 5 5L20 6.5',
  x: 'M6 6l12 12M18 6 6 18',
  alert: 'M12 3 2 20h20L12 3Zm0 7v4m0 3.5v.5',
  info: 'M12 8h.01M12 11v5m9-4a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z',
  inbox: 'M3 13h5l2 3h4l2-3h5M5 5h14a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H5a2 2 0 0 1 2-2Z',
  book: 'M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2V5Zm0 16a2 2 0 0 1 2-2h13',
  chart: 'M4 20V10m6 10V4m6 16v-8m4 8H2',
  spark: 'M12 3l1.9 5.6L19.5 10l-5.6 1.9L12 17.5l-1.9-5.6L4.5 10l5.6-1.4L12 3Z',
  code: 'm8 6-6 6 6 6m8-12 6 6-6 6',
  edit: 'M14 4l6 6L9 21H3v-6L14 4Z',
  target: 'M12 21a9 9 0 1 1 0-18 9 9 0 0 1 0 18Zm0-5a4 4 0 1 1 0-8 4 4 0 0 1 0 8Z',
  users: 'M16 19a4 4 0 0 0-8 0m8-10a4 4 0 1 1-8 0 4 4 0 0 1 8 0Zm6 10a5.5 5.5 0 0 0-3.3-5M17 4.6a4 4 0 0 1 0 7.8',
  flag: 'M5 21V4c4-2 8 2 12 0v10c-4 2-8-2-12 0',
  play: 'M6 4.5v15l13-7.5-13-7.5Z',
  list: 'M8 6h13M8 12h13M8 18h13M4 6h.01M4 12h.01M4 18h.01',
  home: 'm3 11 9-8 9 8M5 9.5V21h14V9.5',
  logout: 'M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4m7 14 5-5-5-5m5 5H9',
  database:
    'M12 8c4.4 0 8-1.3 8-3s-3.6-3-8-3-8 1.3-8 3 3.6 3 8 3Zm8 2V5M4 10V5m16 7c0 1.7-3.6 3-8 3s-8-1.3-8-3m16 7v-5M4 19v-5m16 5c0 1.7-3.6 3-8 3s-8-1.3-8-3',
  shield: 'M12 3l7 3v5c0 4.5-3 8.5-7 10-4-1.5-7-5.5-7-10V6l7-3Z',
  key: 'M14 10a4 4 0 1 0-4 4c.5 0 1-.1 1.4-.3L12 14v2h2v2h2v2h4v-4l-4.6-4.6c.2-.4.4-.9.4-1.4Z',
  sun: 'M12 3v2m0 14v2m9-9h-2M5 12H3m15.4-6.4-1.4 1.4M7 17l-1.4 1.4m12.8 0L17 17M7 7 5.6 5.6M16 12a4 4 0 1 1-8 0 4 4 0 0 1 8 0Z',
  moon: 'M20.9 13A8.5 8.5 0 0 1 11 3.1 8.5 8.5 0 1 0 20.9 13Z',
  monitor: 'M4 5h16a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-6v2h3m-10 0h7m-4-2v2M6 8h12v7H6V8Z',
  search: 'M21 21l-4.8-4.8M10.5 18a7.5 7.5 0 1 1 0-15 7.5 7.5 0 0 1 0 15Z',
  file: 'M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9l-6-6Zm0 0v6h6M9 13h6M9 17h4',
  layers: 'm12 3 9 5-9 5-9-5 9-5Zm-9 9 9 5 9-5m-18 4 9 5 9-5',
  trend: 'm3 17 6-6 4 4 8-8m0 0h-5m5 0v5',
  settings: 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Zm8-3a8 8 0 0 0-.2-1.8l2-1.5-2-3.5-2.4 1a8 8 0 0 0-3.1-1.8L13.9 2h-3.8l-.4 2.4a8 8 0 0 0-3.1 1.8l-2.4-1-2 3.5 2 1.5A8 8 0 0 0 4 12c0 .6.1 1.2.2 1.8l-2 1.5 2 3.5 2.4-1a8 8 0 0 0 3.1 1.8l.4 2.4h3.8l.4-2.4a8 8 0 0 0 3.1-1.8l2.4 1 2-3.5-2-1.5c.1-.6.2-1.2.2-1.8Z',
  arrowLeft: 'M19 12H5m0 0 6-6m-6 6 6 6',
  mail: 'M4 4h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Zm18 2-10 7L2 6',
  lock: 'M3 11h18v11H3V11Zm4 0V7a5 5 0 0 1 10 0v4',
  user: 'M19 21a7 7 0 0 0-14 0m14-13a7 7 0 1 1-14 0 7 7 0 0 1 14 0Z',
  arrowRight: 'M5 12h14m0 0-6-6m6 6-6 6',
  plus: 'M12 5v14m-7-7h14',
  reset: 'M3 12a9 9 0 1 0 3-6.7M3 4v5h5',
  grad: 'm2 9 10-5 10 5-10 5L2 9Zm4 2.5V16c0 1.7 2.7 3 6 3s6-1.3 6-3v-4.5M22 9v5',
  save: 'M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2Zm-2-16v4H7V5',
  upload: 'M12 3v12m0-12-4 4m4-4 4 4M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2',
  more: 'M5 12h.01M12 12h.01M19 12h.01',
  chevronDown: 'm6 9 6 6 6-6',
}

export function Icon({ name, className = 'h-4 w-4' }) {
  return (
    <svg
      data-icon={name}
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

// Dark-mode tones: translucent tint + matching ring so badges read on
// deep surfaces instead of pastel fills on white.
const TONES = {
  gray: 'bg-slate-400/10 text-slate-300 ring-1 ring-inset ring-slate-400/20',
  blue: 'bg-sky-400/10 text-sky-300 ring-1 ring-inset ring-sky-400/25',
  teal: 'bg-cyan-400/10 text-cyan-300 ring-1 ring-inset ring-cyan-400/25',
  violet: 'bg-violet-400/10 text-violet-300 ring-1 ring-inset ring-violet-400/25',
  green: 'bg-emerald-400/10 text-emerald-300 ring-1 ring-inset ring-emerald-400/25',
  amber: 'bg-amber-400/10 text-amber-300 ring-1 ring-inset ring-amber-400/25',
  red: 'bg-rose-400/10 text-rose-300 ring-1 ring-inset ring-rose-400/25',
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

export function TypeBadge({ type }) {
  useLocale()
  return <Badge tone={TYPE_TONES[type] || 'gray'}>{typeLabel(type)}</Badge>
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
  published: 'green',
  retired: 'gray',
  confirmed: 'green',
  disabled: 'amber',
}

export function StatusBadge({ status }) {
  useLocale()
  return <Badge tone={STATUS_TONES[status] || 'gray'}>{statusLabel(status)}</Badge>
}

// Elevated dark surface — subtle border + restrained shadow, per the
// prototypes' panel treatment.
export function Card({ className = '', children }) {
  return (
    <div
      className={`surface-card rounded-xl border border-edge bg-panel ${className}`}
    >
      {children}
    </div>
  )
}

// Banded card header — title row separated from the body, like the
// prototypes' section panels.
export function CardTitle({ title, children }) {
  return (
    <div className="section-heading flex flex-wrap items-center justify-between gap-2 border-b border-edge/70 px-5 py-3.5">
      <h2 className="text-sm font-semibold tracking-tight text-ink">{title}</h2>
      {children}
    </div>
  )
}

export function PageHeader({ title, subtitle, eyebrow, children }) {
  return (
    <div className="page-heading flex flex-wrap items-center justify-between gap-4 rounded-xl border border-edge bg-panel p-5 sm:p-6">
      <div className="min-w-0 max-w-3xl">
        {eyebrow && <p className="eyebrow mb-2">{eyebrow}</p>}
        <h1 className="text-2xl font-semibold tracking-tight text-ink">{title}</h1>
        {subtitle && <p className="mt-1.5 text-sm leading-relaxed text-mute">{subtitle}</p>}
      </div>
      {children}
    </div>
  )
}

export function StatCard({ label, value, icon, hint }) {
  return (
    <Card className="p-5">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-2xl font-semibold tracking-tight text-ink">{value}</p>
          <p className="mt-1 text-sm text-sub">{label}</p>
          {hint && <p className="mt-1 text-xs text-mute">{hint}</p>}
        </div>
        {icon && (
          <span className="rounded-lg bg-cyan-400/[0.07] p-2 text-cyan-300">
            <Icon name={icon} className="h-4 w-4" />
          </span>
        )}
      </div>
    </Card>
  )
}

// Competency bar with a benchmark tick — from the learner prototype's
// per-concept score list. Value/target are 0–100 numbers or null.
export function ScoreBar({ value, target }) {
  useLocale()
  const pct = value == null ? 0 : Math.max(0, Math.min(100, Number(value)))
  const targetPct = target == null ? null : Math.max(0, Math.min(100, Number(target)))
  const met = targetPct != null && pct >= targetPct
  return (
    <div className="flex items-center gap-2">
      <div className="relative h-2 w-full max-w-40 rounded-full bg-elev">
        <div
          className={`h-2 w-full origin-left rounded-full transition-transform duration-300 ${targetPct == null ? 'bg-cyan-400' : met ? 'bg-emerald-400' : 'bg-rose-400'}`}
          style={{ transform: `scaleX(${pct / 100})` }}
        />
        {targetPct != null && (
          <span
            className="absolute -top-0.5 h-3 w-0.5 bg-mute"
            style={{ left: `${targetPct}%` }}
            title={t('common.targetPercent', { value: percent(target) })}
          />
        )}
      </div>
      <span className="w-12 shrink-0 text-right text-xs tabular-nums text-sub">
        {percent(value, { maximumFractionDigits: 0 })}
      </span>
    </div>
  )
}

// Consistent labelled form control — the prototypes label every field.
export function Field({ label, htmlFor, children, className = '' }) {
  return (
    <div className={className}>
      <label htmlFor={htmlFor} className="mb-1 block text-sm font-medium text-sub">
        {label}
      </label>
      {children}
    </div>
  )
}

export const inputCls =
  'w-full rounded-lg border border-edge2 bg-abyss/60 px-3.5 py-2.5 text-sm text-ink placeholder-faint focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/20'

export const selectCls =
  'rounded-lg border border-edge2 bg-panel px-3 py-2 text-sm text-ink focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/20'

export const btnPrimary =
  'inline-flex items-center justify-center gap-2 rounded-lg bg-cyan-400 px-4 py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary-hover motion-safe:active:scale-[.985] disabled:opacity-50'

export const btnGhost =
  'btn-ghost inline-flex items-center justify-center gap-2 rounded-lg border border-edge2 bg-transparent px-3.5 py-2 text-sm font-medium text-sub hover:bg-surface-hover hover:text-ink motion-safe:active:scale-[.985]'

export const btnDanger =
  'inline-flex items-center justify-center gap-2 rounded-lg bg-rose-600 px-4 py-2 text-sm font-semibold text-white hover:bg-danger-hover disabled:opacity-50'

export const btnLink = 'font-medium text-cyan-300 hover:text-cyan-200 hover:underline'

export const thCls =
  'border-b border-edge bg-elev/70 text-left text-xs font-semibold uppercase tracking-wide text-mute'

export function TableShell({ children }) {
  useLocale()
  return (
    <div tabIndex={0} role="region" aria-label={t('common.scrollTable')} className="overflow-x-auto overscroll-x-contain">
      <table className="data-table">{children}</table>
    </div>
  )
}

export function Pagination({ page, pageCount, onPageChange }) {
  useLocale()
  if (pageCount <= 1) return null
  return <nav aria-label={t('common.pagination')} className="flex items-center justify-between gap-3 border-t border-edge/70 px-4 py-3 text-xs text-mute">
    <span>{t('common.pageOf', { page: number(page), pages: number(pageCount) })}</span>
    <div className="flex gap-2">
      <button type="button" onClick={() => onPageChange(page - 1)} disabled={page <= 1} className={btnGhost}>{t('common.previous')}</button>
      <button type="button" onClick={() => onPageChange(page + 1)} disabled={page >= pageCount} className={btnGhost}>{t('common.next')}</button>
    </div>
  </nav>
}

// WebKit does not focus buttons on pointer activation. Establish the opener
// before rendering a modal so dismissal restores focus consistently.
export function focusDialogTrigger(event) {
  event.currentTarget.focus()
}

// Accessible, viewport-level confirmation dialog.
export function ConfirmDialog({ open, title, children, confirmLabel, cancelLabel = t('common.keepGoing'), busy = false, onConfirm, onCancel }) {
  useLocale()
  const dialogRef = useRef(null)
  const backdropRef = useRef(null)
  const titleId = useId()
  const descriptionId = useId()
  const cancelRef = useRef(onCancel)
  cancelRef.current = busy ? () => {} : onCancel
  useEffect(() => {
    if (!open) return
    const previous = document.activeElement
    const background = [...document.body.children].filter((el) => el !== backdropRef.current)
      .map((el) => ({ el, inert: el.getAttribute('inert'), hidden: el.getAttribute('aria-hidden') }))
    const overflow = document.body.style.overflow
    const padding = document.body.style.paddingRight
    const width = document.documentElement.clientWidth
    const scrollbar = width > 0 ? Math.max(0, window.innerWidth - width) : 0
    document.body.style.overflow = 'hidden'
    if (scrollbar) document.body.style.paddingRight = `${parseFloat(getComputedStyle(document.body).paddingRight) + scrollbar}px`
    for (const { el } of background) { el.setAttribute('inert', ''); el.setAttribute('aria-hidden', 'true') }
    const focusable = () => [...dialogRef.current.querySelectorAll('button, a[href], input:not([type="hidden"]), select, textarea, [tabindex]:not([tabindex="-1"])')]
      .filter((element) => !element.matches(':disabled') && !element.closest('[hidden]') && getComputedStyle(element).display !== 'none' && getComputedStyle(element).visibility !== 'hidden')
    const moveFocus = () => (focusable()[0] || dialogRef.current).focus()
    moveFocus()
    const onKey = (e) => {
      if (e.key === 'Escape') { e.preventDefault(); cancelRef.current() }
      if (e.key !== 'Tab') return
      const controls = focusable()
      if (!controls.length) { e.preventDefault(); dialogRef.current.focus(); return }
      const first = controls[0]
      const last = controls.at(-1)
      if (e.shiftKey && (document.activeElement === first || !dialogRef.current.contains(document.activeElement))) { e.preventDefault(); last.focus() }
      if (!e.shiftKey && (document.activeElement === last || !dialogRef.current.contains(document.activeElement))) { e.preventDefault(); first.focus() }
    }
    const keepFocus = (e) => { if (!dialogRef.current.contains(e.target)) moveFocus() }
    document.addEventListener('keydown', onKey)
    document.addEventListener('focusin', keepFocus)
    return () => {
      document.removeEventListener('keydown', onKey)
      document.removeEventListener('focusin', keepFocus)
      document.body.style.overflow = overflow
      document.body.style.paddingRight = padding
      for (const { el, inert, hidden } of background) {
        if (inert == null) el.removeAttribute('inert'); else el.setAttribute('inert', inert)
        if (hidden == null) el.removeAttribute('aria-hidden'); else el.setAttribute('aria-hidden', hidden)
      }
      if (previous?.isConnected) previous.focus?.()
    }
  }, [open])
  if (!open) return null
  return createPortal(
    <div
      ref={backdropRef}
      className="dialog-backdrop fixed inset-0 z-50 flex items-center justify-center p-4"
      role="presentation"
      onClick={busy ? undefined : onCancel}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descriptionId}
        tabIndex={-1}
        className="dialog-enter max-h-[calc(100dvh-2rem)] w-full max-w-sm overflow-y-auto rounded-xl border border-edge2 bg-panel p-6 focus:outline-none"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id={titleId} className="text-base font-semibold text-ink">{title}</h2>
        <div id={descriptionId} className="mt-2 text-sm text-sub">{children}</div>
        <div className="mt-4 flex justify-end gap-2">
          <button type="button" onClick={onCancel} disabled={busy} className={btnGhost}>
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={busy}
            aria-busy={busy}
            className={btnDanger}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>, document.body
  )
}

// ---------- frontend-branch port primitives ----------
// Composition patterns from origin/frontend (eyebrow labels, tag pills,
// stat tiles, tinted insight cards, hero bands) bound to the theme tokens.

export function Eyebrow({ children, className = '' }) {
  return <p className={`eyebrow ${className}`}>{children}</p>
}

export function TagPill({ children, accent = false, className = '' }) {
  return <span className={`tag ${accent ? 'tag-accent' : ''} ${className}`}>{children}</span>
}

export function IconChip({ name, large = false, className = '' }) {
  return (
    <span className={`icon-chip ${large ? 'icon-chip-lg' : ''} ${className}`} aria-hidden="true">
      <Icon name={name} className={large ? 'h-5 w-5' : 'h-4 w-4'} />
    </span>
  )
}

// Mock-style stat tile: mono value with optional unit, caps heading, icon chip.
// `hint`/`tag` form the foot row like the prototypes' change chips.
export function StatTile({ label, value, unit, icon, tone = '', hint, tag, className = '' }) {
  return (
    <div className={`stat-tile surface-card ${tone ? `stat-${tone}` : ''} ${className}`}>
      <div className="stat-tile-head">
        <h3>{label}</h3>
        {icon && <IconChip name={icon} />}
      </div>
      <p className="stat-tile-value">
        {value}
        {unit ? <small> {unit}</small> : null}
      </p>
      {(hint || tag) && (
        <div className="stat-tile-foot">
          {hint ? <span className="min-w-0 truncate" title={hint}>{hint}</span> : <span />}
          {tag}
        </div>
      )}
    </div>
  )
}

// Tinted insight card — the learner prototype's strength/weakness/gap blocks.
export function TintCard({ tone = 'cyan', icon, title, meta, className = '', children }) {
  return (
    <div className={`tint-card tint-${tone} ${className}`}>
      {(icon || title) && (
        <div className="relative flex items-start justify-between gap-3">
          <div className="min-w-0">
            {title && <h3 className="text-sm font-semibold text-ink">{title}</h3>}
            {meta && <p className="mt-1 text-xs text-mute">{meta}</p>}
          </div>
          {icon && <IconChip name={icon} />}
        </div>
      )}
      {children}
    </div>
  )
}

// Thin progress track with an optional benchmark tick (0-100 numbers or null).
export function SkillTrack({ value, target, tone, className = '' }) {
  const pct = value == null ? 0 : Math.max(0, Math.min(100, Number(value)))
  const targetPct = target == null ? null : Math.max(0, Math.min(100, Number(target)))
  return (
    <div className={`skill-track relative ${className}`} role="presentation">
      <span
        className="skill-fill"
        style={{ transform: `scaleX(${pct / 100})`, width: '100%', '--fill': tone ? `var(--${tone})` : undefined }}
      />
      {targetPct != null && (
        <span
          className="absolute -top-[3px] h-[11px] w-[2px] bg-mute"
          style={{ left: `${targetPct}%` }}
          title={percent(targetPct, { maximumFractionDigits: 0 })}
        />
      )}
    </div>
  )
}

// Dark hero band — the learner prototype's greeting band with stats.
// Always dark: it is a brand surface, like the auth side panel.
export function HeroBand({ eyebrow, title, subtitle, aside, headingLevel = 1, className = '', videoSrc, videoPoster, children }) {
  const Heading = `h${headingLevel}`
  return (
    <section className={`hero-band p-6 sm:p-8 ${className}`}>
      {videoSrc && <BackgroundVideo className="hero-band-video" src={videoSrc} poster={videoPoster} />}
      {videoSrc && <div className="hero-band-video-overlay" aria-hidden="true" />}
      <div className="relative flex flex-wrap items-end justify-between gap-6">
        <div className="min-w-0 max-w-2xl">
          {eyebrow && <p className="eyebrow">{eyebrow}</p>}
          <Heading className="mt-3 text-2xl font-bold tracking-tight sm:text-[28px]">{title}</Heading>
          {subtitle && <p className="hero-sub mt-2 max-w-xl text-sm leading-relaxed">{subtitle}</p>}
          {children}
        </div>
        {aside && <div className="flex flex-wrap items-center gap-6 sm:gap-8">{aside}</div>}
      </div>
    </section>
  )
}

export function Notice({ children }) {
  useLocale()
  return (
    <p
      role="status"
      className="mt-3 flex items-center gap-2 rounded-md border border-emerald-400/30 bg-emerald-400/10 p-2.5 text-sm text-emerald-300"
    >
      <Icon name="check" className="h-4 w-4 shrink-0" />
      <span>{resolveMessage(children)}</span>
    </p>
  )
}
