import { t, useLocale } from '../i18n'
import { useEffect, useRef, useState } from 'react'
import { Icon, btnGhost } from './ui'

// Shared admin chrome — one header, one filter pattern, one row-action
// menu, one segmented control — so every admin page presents the same
// hierarchy: title → context → primary action → filters → content.

export function AdminPageHeader({ title, subtitle, children }) {
  return (
    <header className="flex flex-wrap items-end justify-between gap-x-6 gap-y-3">
      <div className="min-w-0 max-w-3xl">
        <h1 className="text-2xl font-semibold tracking-tight text-ink">{title}</h1>
        {subtitle && <p className="mt-1 text-sm leading-relaxed text-mute">{subtitle}</p>}
      </div>
      {children && <div className="flex flex-wrap items-center gap-2">{children}</div>}
    </header>
  )
}

// Search-first filter row. Common controls stay visible as children; rare
// ones render inside `more` behind a toggle. The clear action only appears
// while filters are active.
export function FilterBar({ children, more, activeCount = 0, onClear }) {
  useLocale()
  const [expanded, setExpanded] = useState(false)
  return (
    <div className="rounded-xl border border-edge bg-panel p-3">
      <div className="flex flex-wrap items-center gap-2">
        {children}
        {more && (
          <button
            type="button"
            aria-expanded={expanded}
            onClick={() => setExpanded((open) => !open)}
            className={`${btnGhost} px-3 py-1.5 text-xs`}
          >
            {t('common.moreFilters')}
            {activeCount > 0 && (
              <span className="rounded-full bg-cyan-400/15 px-1.5 py-0.5 text-[10px] font-semibold text-cyan-300">
                {activeCount}
              </span>
            )}
          </button>
        )}
        {activeCount > 0 && onClear && (
          <button type="button" onClick={onClear} className="text-xs font-medium text-cyan-300 hover:underline">
            {t('common.clearFilters')}
          </button>
        )}
      </div>
      {more && expanded && (
        <div className="mt-2 flex flex-wrap items-center gap-2 border-t border-edge/70 pt-3">
          {more}
        </div>
      )}
    </div>
  )
}

export function MenuItem({ onSelect, danger = false, disabled = false, children }) {
  return (
    <button
      type="button"
      role="menuitem"
      onClick={onSelect}
      disabled={disabled}
      className={`flex w-full items-center px-3 py-2 text-left text-sm transition-colors enabled:hover:bg-surface-hover disabled:opacity-50 ${
        danger ? 'text-rose-300' : 'text-ink'
      }`}
    >
      {children}
    </button>
  )
}

// Overflow menu for row actions. Primary action stays visible; secondary
// and destructive actions collect here, with danger items separated.
export function RowMenu({ children, label }) {
  useLocale()
  const [open, setOpen] = useState(false)
  const rootRef = useRef(null)
  const triggerRef = useRef(null)
  const menuRef = useRef(null)

  useEffect(() => {
    if (!open) return
    const items = () => [...(menuRef.current?.querySelectorAll('[role="menuitem"]') || [])]
    items()[0]?.focus()
    const onPointer = (e) => { if (!rootRef.current?.contains(e.target)) setOpen(false) }
    const onKey = (e) => {
      if (e.key === 'Escape') {
        setOpen(false)
        triggerRef.current?.focus()
        return
      }
      if (!['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(e.key)) return
      const list = items()
      if (!list.length) return
      e.preventDefault()
      const index = list.indexOf(document.activeElement)
      const next = e.key === 'Home' ? 0
        : e.key === 'End' ? list.length - 1
        : e.key === 'ArrowDown' ? (index + 1) % list.length
        : (index - 1 + list.length) % list.length
      list[next].focus()
    }
    document.addEventListener('mousedown', onPointer)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onPointer)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  return (
    <span ref={rootRef} className="relative inline-block">
      <button
        ref={triggerRef}
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={label || t('common.actions')}
        onClick={() => setOpen((value) => !value)}
        onKeyDown={(e) => { if (e.key === 'ArrowDown' && !open) { e.preventDefault(); setOpen(true) } }}
        className="rounded-md p-1.5 text-mute transition-colors hover:bg-surface-hover hover:text-ink"
      >
        <Icon name="more" className="h-4 w-4" />
      </button>
      {open && (
        <div
          ref={menuRef}
          role="menu"
          aria-label={label || t('common.actions')}
          onClick={() => setOpen(false)}
          className="absolute right-0 z-30 mt-1 min-w-44 overflow-hidden rounded-lg border border-edge2 bg-panel shadow-lg shadow-black/30"
        >
          {children}
        </div>
      )}
    </span>
  )
}

// Segmented filter control (e.g. lifecycle tabs). Uses toggle semantics so
// it does not imply a tabpanel contract.
export function SegmentedFilter({ options, value, onChange, ariaLabel }) {
  useLocale()
  return (
    <div role="group" aria-label={ariaLabel} className="flex w-fit max-w-full flex-wrap gap-1 rounded-lg border border-edge bg-panel p-1">
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          aria-pressed={value === option.value}
          onClick={() => onChange(option.value)}
          className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
            value === option.value
              ? 'bg-cyan-400/15 text-cyan-200'
              : 'text-sub hover:bg-surface-hover hover:text-ink'
          }`}
        >
          {option.label}
          {option.count != null && <span className="ml-1.5 text-xs text-mute">({option.count})</span>}
        </button>
      ))}
    </div>
  )
}

// Consistent section heading inside editor cards.
export function FormSection({ title, children, className = '' }) {
  return (
    <fieldset className={`min-w-0 border-t border-edge/70 pt-3 ${className}`}>
      <legend className="pr-2 text-xs font-semibold uppercase tracking-wide text-mute">{title}</legend>
      <div className="grid gap-3">{children}</div>
    </fieldset>
  )
}
