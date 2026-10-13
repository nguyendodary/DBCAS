import { t, useLocale } from '../i18n'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { Icon } from './ui'
import LanguageSelector from './LanguageSelector'
import ThemeSelector from './ThemeSelector'

const LEARNER_LINKS = [
  { to: '/dashboard', label: 'nav.dashboard', icon: 'chart' },
  { to: '/assessments', label: 'nav.assessments', icon: 'play' },
  { to: '/history', label: 'nav.history', icon: 'clock' },
  { to: '/settings', label: 'nav.settings', icon: 'settings' },
]

const ADMIN_LINKS = [
  { to: '/admin', label: 'nav.cohort', icon: 'users', end: true },
  { to: '/admin/curriculum', label: 'nav.curriculum', icon: 'book' },
  { to: '/admin/questions', label: 'nav.questions', icon: 'edit' },
  { to: '/admin/candidates', label: 'nav.candidates', icon: 'spark' },
  { to: '/admin/assessments', label: 'nav.assessments', icon: 'target' },
  { to: '/admin/accounts', label: 'nav.accounts', icon: 'shield' },
  { to: '/settings', label: 'nav.settings', icon: 'settings' },
]

const sideLinkCls = ({ isActive }) =>
  `group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm ${
    isActive
      ? 'bg-cyan-400/[0.09] font-semibold text-cyan-200 shadow-[inset_3px_0_0_0_var(--primary)]'
      : 'text-sub hover:bg-surface-hover hover:text-ink'
  }`

const topLinkCls = ({ isActive }) =>
  `nav-pill ${isActive ? 'active' : ''}`

function Brand({ compact = false }) {
  useLocale()
  return (
    <Link to="/" className="flex min-w-0 items-center gap-2.5">
      <span className="icon-chip icon-chip-lg" aria-hidden="true">
        <Icon name="database" className="h-5 w-5" />
      </span>
      <span className="min-w-0">
        <span className="block font-mono text-base font-bold leading-tight tracking-tight text-ink">DBCAS</span>
        {!compact && <span className="eyebrow eyebrow-no-dot block whitespace-nowrap text-[9px] leading-tight">{t('nav.engineTag')}</span>}
      </span>
    </Link>
  )
}

function AccountChip({ account, onLogout }) {
  useLocale()
  return (
    <div className="flex min-w-0 items-center gap-2.5">
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-cyan-400/10 text-xs font-bold text-cyan-300 ring-1 ring-inset ring-cyan-400/25">
        {(account.full_name || account.email || '?').slice(0, 1).toUpperCase()}
      </span>
      <div className="hidden min-w-0 xl:block">
        <p className="truncate text-sm font-medium leading-tight text-ink">
          {account.full_name || account.email}
        </p>
        <p className="truncate text-xs leading-tight text-mute">{account.email}</p>
      </div>
      <button
        type="button"
        onClick={onLogout}
        aria-label={t('nav.logout')}
        title={t('nav.logout')}
        className="rounded-md p-1.5 text-mute transition-colors hover:bg-surface-hover hover:text-rose-300"
      >
        <Icon name="logout" className="h-4 w-4" />
      </button>
    </div>
  )
}

// Learner chrome follows the learner prototype: a dark topbar with the
// centered pill navigation; mobile keeps the same links in a scrollable row.
function LearnerTopbar({ onLogout }) {
  useLocale()
  const { account } = useAuth()
  return (
    <header className="sticky top-0 z-40 border-b border-edge bg-panel/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-[1200px] items-center gap-4 px-4 sm:px-6">
        <Brand />
        <nav aria-label={t('nav.primary')} className="hidden flex-1 items-center justify-center gap-1 md:flex">
          {LEARNER_LINKS.map((l) => (
            <NavLink key={l.to} to={l.to} className={topLinkCls}>
              {t(l.label)}
            </NavLink>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-2 md:ml-0">
          <LanguageSelector />
          <ThemeSelector />
          {account && <AccountChip account={account} onLogout={onLogout} />}
        </div>
      </div>
      <nav aria-label={t('nav.primary')} className="flex gap-1 overflow-x-auto border-t border-edge/60 px-3 py-2 md:hidden">
        {LEARNER_LINKS.map((l) => (
          <NavLink key={l.to} to={l.to} className={topLinkCls}>
            {t(l.label)}
          </NavLink>
        ))}
      </nav>
    </header>
  )
}

// Admin chrome follows the admin prototype: fixed 240px dark sidebar with the
// brand block, the primary "new assessment" CTA, grouped navigation and a
// bottom account card. Mobile falls back to the top bar + scrollable nav.
function AdminSidebar({ onLogout, isLearner }) {
  useLocale()
  const { account } = useAuth()
  return (
    <aside className="app-sidebar fixed inset-y-0 left-0 z-40 hidden w-60 flex-col border-r border-edge md:flex">
      <div className="px-5 pb-5 pt-6">
        <Brand />
      </div>
      <div className="px-4">
        <Link
          to="/admin/assessments"
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-cyan-400 px-4 py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary-hover"
        >
          <Icon name="plus" className="h-4 w-4" />
          {t('nav.newAssessment')}
        </Link>
      </div>
      <nav aria-label={t('nav.primary')} className="mt-4 flex-1 space-y-1 overflow-y-auto px-4 py-2">
        {isLearner && (
          <>
            <p className="px-3 pb-2 pt-1 text-[11px] font-semibold uppercase tracking-[.14em] text-mute">{t('nav.learnerWorkspace')}</p>
            {LEARNER_LINKS.map((l) => (
              <NavLink key={l.to} to={l.to} className={sideLinkCls}>
                <Icon name={l.icon} className="h-4 w-4 shrink-0" />
                {t(l.label)}
              </NavLink>
            ))}
          </>
        )}
        <p className="px-3 pb-2 pt-2 text-[11px] font-semibold uppercase tracking-[.14em] text-mute">{t('nav.administration')}</p>
        {ADMIN_LINKS.map((l) => (
          <NavLink key={l.to} to={l.to} end={l.end} className={sideLinkCls}>
            <Icon name={l.icon} className="h-4 w-4 shrink-0" />
            {t(l.label)}
          </NavLink>
        ))}
      </nav>
      {account && (
        <div className="border-t border-edge/70 p-4">
          <div className="flex items-center gap-2.5 rounded-lg border border-edge bg-panel/60 px-3 py-2.5">
            <AccountChip account={account} onLogout={onLogout} />
          </div>
        </div>
      )}
    </aside>
  )
}

function MobileTopbar({ links, onLogout }) {
  useLocale()
  const { account } = useAuth()
  return (
    <header className="sticky top-0 z-40 border-b border-edge bg-panel/95 backdrop-blur md:hidden">
      <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-3">
        <Brand />
        <div className="ml-auto flex items-center gap-2">
          <LanguageSelector />
          <ThemeSelector />
          {account && (
            <button
              type="button"
              onClick={onLogout}
              aria-label={t('nav.logout')}
              title={t('nav.logout')}
              className="flex items-center gap-1.5 rounded-md border border-edge2 px-2.5 py-1.5 text-xs text-sub hover:bg-surface-hover"
            >
              <Icon name="logout" className="h-3.5 w-3.5" /><span className="hidden sm:inline">{t('nav.logout')}</span>
            </button>
          )}
        </div>
      </div>
      <nav
        aria-label={t('nav.primary')}
        className="flex gap-1 overflow-x-auto px-3 pb-2.5"
      >
        {links.map((l) => (
          <NavLink key={l.to} to={l.to} end={l.end} className={topLinkCls}>
            {t(l.label)}
          </NavLink>
        ))}
      </nav>
    </header>
  )
}

// App frame: role-aware chrome ported from the frontend branch — learner
// topbar, admin sidebar — with the real role guard and client-side logout.
export default function Layout({ children }) {
  useLocale()
  const { account, hasRole, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const isLearner = hasRole('Learner')
  const isAdmin = hasRole('Administrator')
  const isExam = location.pathname.startsWith('/exam/')

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  const allLinks = [
    ...(isLearner ? LEARNER_LINKS : []),
    ...(isAdmin ? ADMIN_LINKS : []),
  ]

  const pageLabel = allLinks.find((link) => link.to === location.pathname)?.label

  return (
    <div className="min-h-screen bg-abyss text-ink">
      <a href="#main-content" className="skip-link">{t('nav.skipContent')}</a>

      {!isExam && isAdmin ? (
        <>
          <AdminSidebar onLogout={handleLogout} isLearner={isLearner} />
          {/* desktop utility bar */}
          <header className="hidden min-h-14 items-center justify-between gap-4 border-b border-edge bg-panel px-6 md:ml-60 md:flex">
            <p className="text-sm text-mute">
              <span className="font-semibold text-sub">DBCAS</span>
              <span aria-hidden="true" className="mx-3 text-faint">/</span>
              {t(pageLabel || 'nav.administration')}
            </p>
            <div className="flex items-center gap-3">
              <LanguageSelector />
              <ThemeSelector />
            </div>
          </header>
          <MobileTopbar links={allLinks} onLogout={handleLogout} />
        </>
      ) : !isExam ? (
        <LearnerTopbar onLogout={handleLogout} />
      ) : null}

      <main
        id="main-content"
        tabIndex={-1}
        className={`min-w-0 px-4 py-6 sm:px-6 lg:py-8 ${
          isExam
            ? 'lg:px-8'
            : isAdmin
              ? 'md:pl-[calc(15rem+1.5rem)] lg:pr-8'
              : ''
        }`}
      >
        <div
          key={location.pathname}
          className={`page-enter mx-auto w-full ${
            isExam ? 'max-w-[1440px]' : isAdmin ? 'max-w-[1400px]' : 'max-w-[1180px]'
          }`}
        >
          {children}
        </div>
      </main>
    </div>
  )
}
