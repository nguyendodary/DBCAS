import { createContext, useCallback, useContext, useEffect, useId, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { useLocation } from 'react-router-dom'
import { useAuth } from '../auth'
import { t, useLocale } from '../i18n'
import { Icon } from './ui'

const HelpContext = createContext({ openHelp: () => {} })

const SECTIONS = [
  'overview',
  'start',
  'modes',
  'types',
  'sql',
  'essay',
  'results',
  'language',
  'accessibility',
  'troubleshooting',
]

const CONTEXT_ROUTES = [
  ['/admin/grading', 'adminGrading'],
  ['/admin/questions', 'adminQuestions'],
  ['/admin/curriculum', 'adminCurriculum'],
  ['/admin/candidates', 'adminCandidates'],
  ['/admin/assessments', 'adminAssessments'],
  ['/admin/accounts', 'adminAccounts'],
  ['/admin', 'admin'],
  ['/exam/', 'exam'],
  ['/history/', 'evidence'],
  ['/history', 'history'],
  ['/competency', 'competency'],
  ['/assessments', 'assessments'],
  ['/dashboard', 'dashboard'],
  ['/settings', 'settings'],
]

function contextKey(pathname) {
  return CONTEXT_ROUTES.find(([prefix]) => pathname.startsWith(prefix))?.[1] || 'generic'
}

export function HelpProvider({ children }) {
  const [open, setOpen] = useState(false)
  const openHelp = useCallback(() => setOpen(true), [])
  const closeHelp = useCallback(() => setOpen(false), [])
  return (
    <HelpContext.Provider value={{ openHelp }}>
      {children}
      <HelpGuide open={open} onClose={closeHelp} />
    </HelpContext.Provider>
  )
}

export function HelpButton({ className = '' }) {
  useLocale()
  const { openHelp } = useContext(HelpContext)
  const label = t('help.label')
  return (
    <button
      type="button"
      className={`header-icon-button help-trigger ${className}`}
      aria-label={label}
      title={t('help.triggerTitle')}
      aria-haspopup="dialog"
      onClick={(event) => {
        // Pointer activation does not focus buttons in every browser.
        // Record the invoker before the drawer takes keyboard focus.
        event.currentTarget.focus({ preventScroll: true })
        openHelp()
      }}
    >
      <Icon name="circleHelp" className="h-5 w-5" />
      <span className="help-trigger-label">{label}</span>
    </button>
  )
}

function GuideSection({ id, title, children }) {
  return (
    <section className="help-section" aria-labelledby={`help-section-${id}`}>
      <h3 id={`help-section-${id}`} tabIndex={-1} className="help-section-title">{title}</h3>
      {children}
    </section>
  )
}

function BulletList({ items }) {
  return <ul className="help-list">{items.map((item) => <li key={item}>{item}</li>)}</ul>
}

function RoleGuide({ role, heading, items }) {
  return (
    <div className="help-role-card">
      <p className="help-role-label">{role}</p>
      <h4>{heading}</h4>
      <BulletList items={items} />
    </div>
  )
}

export function HelpGuide({ open, onClose }) {
  const { locale } = useLocale()
  const location = useLocation()
  const auth = useAuth()
  const titleId = useId()
  const descriptionId = useId()
  const panelRef = useRef(null)
  const backdropRef = useRef(null)
  const closeRef = useRef(null)
  const contentRef = useRef(null)
  const closeHandler = useRef(onClose)
  closeHandler.current = onClose

  const roles = auth?.account?.roles || []
  const showLearner = roles.length === 0 || roles.includes('Learner')
  const showAdmin = roles.length === 0 || roles.includes('Administrator')
  const key = useMemo(() => contextKey(location.pathname), [location.pathname])

  useEffect(() => {
    if (!open) return
    const previous = document.activeElement
    const background = [...document.body.children].filter((element) => element !== backdropRef.current)
      .map((element) => ({
        element,
        inert: element.getAttribute('inert'),
        hidden: element.getAttribute('aria-hidden'),
      }))
    const overflow = document.body.style.overflow
    const padding = document.body.style.paddingRight
    const width = document.documentElement.clientWidth
    const scrollbar = width > 0 ? Math.max(0, window.innerWidth - width) : 0
    document.body.style.overflow = 'hidden'
    if (scrollbar) document.body.style.paddingRight = `${parseFloat(getComputedStyle(document.body).paddingRight) + scrollbar}px`
    for (const { element } of background) {
      element.setAttribute('inert', '')
      element.setAttribute('aria-hidden', 'true')
    }

    const focusable = () => [...panelRef.current.querySelectorAll('button, a[href], input:not([type="hidden"]), select, textarea, [tabindex]:not([tabindex="-1"])')]
      .filter((element) => !element.matches(':disabled') && !element.closest('[hidden]')
        && getComputedStyle(element).display !== 'none' && getComputedStyle(element).visibility !== 'hidden')
    closeRef.current?.focus()

    const onKeyDown = (event) => {
      if (event.key === 'Escape') {
        event.preventDefault()
        closeHandler.current()
        return
      }
      if (event.key !== 'Tab') return
      const controls = focusable()
      if (!controls.length) {
        event.preventDefault()
        panelRef.current?.focus()
        return
      }
      const first = controls[0]
      const last = controls.at(-1)
      if (event.shiftKey && (document.activeElement === first || !panelRef.current.contains(document.activeElement))) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && (document.activeElement === last || !panelRef.current.contains(document.activeElement))) {
        event.preventDefault()
        first.focus()
      }
    }
    const keepFocus = (event) => {
      if (!panelRef.current?.contains(event.target)) closeRef.current?.focus()
    }
    document.addEventListener('keydown', onKeyDown)
    document.addEventListener('focusin', keepFocus)
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.removeEventListener('focusin', keepFocus)
      document.body.style.overflow = overflow
      document.body.style.paddingRight = padding
      for (const { element, inert, hidden } of background) {
        if (inert == null) element.removeAttribute('inert')
        else element.setAttribute('inert', inert)
        if (hidden == null) element.removeAttribute('aria-hidden')
        else element.setAttribute('aria-hidden', hidden)
      }
      if (previous?.isConnected) previous.focus?.()
    }
  }, [open])

  function jump(section) {
    const heading = contentRef.current?.querySelector(`#help-section-${section}`)
    heading?.scrollIntoView({ block: 'start' })
    heading?.focus()
  }

  if (!open) return null

  const learnerItems = [1, 2, 3, 4].map((number) => t(`help.learner.item${number}`))
  const adminItems = [1, 2, 3, 4, 5, 6].map((number) => t(`help.admin.item${number}`))
  const troubleshooting = [1, 2, 3, 4, 5, 6].map((number) => t(`help.troubleshooting.item${number}`))
  const accessibility = [1, 2, 3, 4].map((number) => t(`help.accessibility.item${number}`))

  return createPortal(
    <div
      ref={backdropRef}
      className="help-backdrop"
      role="presentation"
      onMouseDown={(event) => { if (event.target === event.currentTarget) closeHandler.current() }}
    >
      <aside
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descriptionId}
        tabIndex={-1}
        className="help-drawer"
      >
        <header className="help-drawer-header">
          <div className="min-w-0">
            <p className="eyebrow">{t('help.eyebrow')}</p>
            <h2 id={titleId} className="help-title">{t('help.title')}</h2>
            <p id={descriptionId} className="help-subtitle">{t('help.subtitle')}</p>
          </div>
          <button
            ref={closeRef}
            type="button"
            className="header-icon-button help-close"
            aria-label={t('help.close')}
            title={t('help.close')}
            onClick={() => closeHandler.current()}
          >
            <Icon name="x" className="h-5 w-5" />
          </button>
        </header>

        <div ref={contentRef} className="help-drawer-body" lang={locale}>
          <div className="help-context" role="note">
            <span className="help-context-icon" aria-hidden="true"><Icon name="info" className="h-4 w-4" /></span>
            <div>
              <p className="help-context-label">{t('help.contextLabel')}</p>
              <strong>{t(`help.context.${key}.title`)}</strong>
              <p>{t(`help.context.${key}.body`)}</p>
            </div>
          </div>

          <nav className="help-index" aria-label={t('help.contents')}>
            {SECTIONS.map((section) => (
              <button key={section} type="button" onClick={() => jump(section)}>
                {t(`help.section.${section}`)}
              </button>
            ))}
            {showLearner && <button type="button" onClick={() => jump('learner')}>{t('help.section.learner')}</button>}
            {showAdmin && <button type="button" onClick={() => jump('admin')}>{t('help.section.admin')}</button>}
          </nav>

          <GuideSection id="overview" title={t('help.section.overview')}>
            <p>{t('help.overview.body')}</p>
            <p className="help-note">{t('help.overview.note')}</p>
          </GuideSection>

          <GuideSection id="start" title={t('help.section.start')}>
            <ol className="help-steps">
              {[1, 2, 3].map((number) => (
                <li key={number}>
                  <strong>{t(`help.start.step${number}Title`)}</strong>
                  <p>{t(`help.start.step${number}Body`)}</p>
                </li>
              ))}
            </ol>
          </GuideSection>

          <GuideSection id="modes" title={t('help.section.modes')}>
            <div className="help-two-up">
              <div className="help-mini-card">
                <h4>{t('help.modes.practiceTitle')}</h4>
                <p>{t('help.modes.practiceBody')}</p>
              </div>
              <div className="help-mini-card">
                <h4>{t('help.modes.formalTitle')}</h4>
                <p>{t('help.modes.formalBody')}</p>
              </div>
            </div>
            <div className="help-mini-card">
              <h4>{t('help.modes.adaptiveTitle')}</h4>
              <p>{t('help.modes.adaptiveBody')}</p>
            </div>
            <p className="help-note">{t('help.modes.note')}</p>
          </GuideSection>

          <GuideSection id="types" title={t('help.section.types')}>
            <dl className="help-definition-list">
              {['mcq', 'sql', 'essay'].map((type) => (
                <div key={type}>
                  <dt>{t(`help.types.${type}Title`)}</dt>
                  <dd>{t(`help.types.${type}Body`)}</dd>
                </div>
              ))}
            </dl>
          </GuideSection>

          <GuideSection id="sql" title={t('help.section.sql')}>
            <p>{t('help.sql.body')}</p>
            <BulletList items={[t('help.sql.restrictions'), t('help.sql.limits'), t('help.sql.errors')]} />
          </GuideSection>

          <GuideSection id="essay" title={t('help.section.essay')}>
            <p>{t('help.essay.body')}</p>
            <BulletList items={[t('help.essay.pending'), t('help.essay.review')]} />
          </GuideSection>

          <GuideSection id="results" title={t('help.section.results')}>
            <p>{t('help.results.body')}</p>
            <dl className="help-definition-list">
              {['immediate', 'human', 'pending', 'timedOut'].map((state) => (
                <div key={state}>
                  <dt>{t(`help.results.${state}Title`)}</dt>
                  <dd>{t(`help.results.${state}Body`)}</dd>
                </div>
              ))}
            </dl>
          </GuideSection>

          <GuideSection id="language" title={t('help.section.language')}>
            <BulletList items={[t('help.language.interface'), t('help.language.content'), t('help.language.theme')]} />
          </GuideSection>

          {showLearner && (
            <GuideSection id="learner" title={t('help.section.learner')}>
              <RoleGuide role={t('help.roles.learner')} heading={t('help.learner.heading')} items={learnerItems} />
            </GuideSection>
          )}

          {showAdmin && (
            <GuideSection id="admin" title={t('help.section.admin')}>
              <RoleGuide role={t('help.roles.admin')} heading={t('help.admin.heading')} items={adminItems} />
            </GuideSection>
          )}

          <GuideSection id="accessibility" title={t('help.section.accessibility')}>
            <BulletList items={accessibility} />
          </GuideSection>

          <GuideSection id="troubleshooting" title={t('help.section.troubleshooting')}>
            <BulletList items={troubleshooting} />
          </GuideSection>

          <p className="help-disclaimer">{t('help.disclaimer')}</p>
        </div>
      </aside>
    </div>,
    document.body,
  )
}
