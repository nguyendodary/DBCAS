import { useEffect, useId, useRef, useState } from 'react'
import { useLocale } from '../i18n'
import { Icon } from './ui'

const LANGUAGES = [{ code: 'vi', name: 'Tiếng Việt' }, { code: 'en', name: 'English' }]

export default function LanguageSelector({ className = '' }) {
  const id = useId()
  const { locale, setLocale, t } = useLocale()
  const [open, setOpen] = useState(false)
  const region = useRef(null)
  const trigger = useRef(null)
  const items = useRef([])
  const timer = useRef(null)
  const returningFocus = useRef(false)
  const cancelClose = () => clearTimeout(timer.current)
  const show = () => { cancelClose(); setOpen(true) }
  const close = (restoreFocus = false) => {
    cancelClose()
    setOpen(false)
    if (restoreFocus) {
      returningFocus.current = true
      trigger.current?.focus()
      returningFocus.current = false
    }
  }
  useEffect(() => {
    const outside = (event) => { if (!region.current?.contains(event.target)) setOpen(false) }
    document.addEventListener('pointerdown', outside)
    return () => { clearTimeout(timer.current); document.removeEventListener('pointerdown', outside) }
  }, [])
  const focusItem = (index) => {
    show()
    // Let the popup mount before moving keyboard focus into it.
    requestAnimationFrame(() => items.current[index]?.focus())
  }
  const onKeyDown = (event) => {
    const index = items.current.indexOf(document.activeElement)
    if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); close(true) }
    else if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault()
      focusItem(index < 0 ? (event.key === 'ArrowDown' ? 0 : 1) : (index + 1) % 2)
    } else if (event.key === 'Home' || event.key === 'End') {
      event.preventDefault(); focusItem(event.key === 'Home' ? 0 : 1)
    } else if (index < 0 && (event.key === 'Enter' || event.key === ' ')) {
      event.preventDefault(); focusItem(LANGUAGES.findIndex(language => language.code === locale))
    }
  }
  return <div ref={region} className={`language-selector ${className}`} onKeyDown={onKeyDown}
    onPointerEnter={(event) => { if (event.pointerType !== 'touch') show() }}
    onPointerLeave={(event) => {
      if (event.pointerType !== 'touch') timer.current = setTimeout(() => setOpen(false), 120)
    }}
    onBlur={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) close() }}>
    <button ref={trigger} type="button" className="header-icon-button" aria-label={t('common.language')}
      title={t('common.language')} aria-haspopup="menu" aria-expanded={open} aria-controls={open ? id : undefined}
      onFocus={() => { if (!returningFocus.current) show() }} onClick={show}>
      <Icon name="globe" className="h-5 w-5" />
    </button>
    {open && <div className="language-menu-bridge">
      <div id={id} role="menu" aria-label={t('common.language')} className="language-menu">
        {LANGUAGES.map((language, index) => <button key={language.code} ref={element => { items.current[index] = element }}
          type="button" role="menuitemradio" aria-checked={locale === language.code} lang={language.code} tabIndex={-1}
          onClick={() => { setLocale(language.code); close(true) }}>
          <span>{language.name}</span>{locale === language.code && <Icon name="check" />}
        </button>)}
      </div>
    </div>}
  </div>
}
