import { t, useLocale } from '../i18n'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { Icon } from './ui'
import LanguageSelector from './LanguageSelector'
import ThemeSelector from './ThemeSelector'
import ThemeProvider from './ThemeProvider'
import AccountAvatar from './AccountAvatar'
import adminBg from '../assets/brand/admin-background.jpg'

const LEARNER_LINKS = [
  { to: '/dashboard', label: 'nav.dashboard', icon: 'home' },
  { to: '/assessments', label: 'nav.assessments', icon: 'list' },
  { to: '/history', label: 'nav.history', icon: 'chart' },
  { to: '/competency', label: 'supervisor.cumulative', icon: 'chart' },
  { to: '/settings', label: 'nav.settings', icon: 'settings' },
]

const ADMIN_LINKS = [
  { to: '/admin', label: 'nav.cohort', icon: 'home', end: true },
  { to: '/admin/curriculum', label: 'nav.curriculum', icon: 'book' },
  { to: '/admin/questions', label: 'nav.questions', icon: 'edit' },
  { to: '/admin/candidates', label: 'nav.candidates', icon: 'spark' },
  { to: '/admin/assessments', label: 'nav.assessments', icon: 'file' },
  { to: '/admin/grading', label: 'supervisor.reviewTitle', icon: 'check' },
  { to: '/admin/accounts', label: 'nav.accounts', icon: 'users' },
  { to: '/settings', label: 'nav.settings', icon: 'settings' },
]

const sideLinkCls = ({ isActive }) =>
  `group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm ${
    isActive
      ? 'bg-cyan-400/[0.09] font-semibold text-cyan-200 shadow-[inset_3px_0_0_0_var(--primary)]'
      : 'text-mute hover:bg-surface-hover hover:text-ink'
  }`

const topLinkCls = ({ isActive }) =>
  `nav-pill ${isActive ? 'active' : ''}`

function BrandSymbol({ className }) {
  return <svg className={className} viewBox="2 2 36 40" fill="none" aria-hidden="true">
    <path d="M7 5h12c10 0 16 7 16 17s-6 17-16 17H7" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    <path d="M7 14v16" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    <path d="M4 19h13m-13 6h13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity=".55" />
    <path d="M22 14c4 1 6 4 6 8s-2 7-6 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" opacity=".4" />
  </svg>
}

// The same signature as the admin sidebar, scaled for the top navigation.
function Brand({ compact = false }) {
  useLocale()
  return (
    <Link to="/" className="dbcas-brand" aria-label="DBCAS">
      <span className="dbcas-brand-row">
        <BrandSymbol className="dbcas-brand-symbol" />
        <span className="dbcas-brand-wordmark">BCAS</span>
      </span>
      {!compact && <span className="dbcas-brand-caption hidden sm:block">{t('nav.engineTagFull')}</span>}
    </Link>
  )
}

function AccountChip({ account, onLogout }) {
  useLocale()
  return (
    <div className="flex min-w-0 items-center gap-2.5">
      <AccountAvatar account={account} className="h-8 w-8 text-xs" />
      <div className="hidden min-w-0 xl:block">
        <p className="truncate text-sm font-medium leading-tight">{account.full_name || account.email}</p>
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

// Learner chrome follows the learner prototype exactly: a theme-aware
// topbar with the bordered pill navigation group, and a
// scrollable second row below lg. Icons ride inside each pill like the source.
function LearnerTopbar({ onLogout }) {
  useLocale()
  const { account } = useAuth()
  return (
    <header className="chrome-dark sticky top-0 z-40 border-b">
      <div className="mx-auto flex h-16 max-w-[1480px] items-center gap-4 px-4 sm:px-6">
        <Brand />
        <nav aria-label={t('nav.primary')} className="nav-group mx-auto hidden flex-1 items-center justify-center lg:flex">
          {LEARNER_LINKS.map((l) => (
            <NavLink key={l.to} to={l.to} className={topLinkCls}>
              <Icon name={l.icon} className="h-4 w-4" />
              {t(l.label)}
            </NavLink>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-2 lg:ml-0">
          <LanguageSelector />
          <ThemeSelector />
          {account && <AccountChip account={account} onLogout={onLogout} />}
        </div>
      </div>
      <nav aria-label={t('nav.primary')} className="flex gap-1 overflow-x-auto border-t border-edge px-3 py-2 lg:hidden">
        {LEARNER_LINKS.map((l) => (
          <NavLink key={l.to} to={l.to} className={topLinkCls}>
            <Icon name={l.icon} className="h-4 w-4" />
            {t(l.label)}
          </NavLink>
        ))}
      </nav>
    </header>
  )
}

// Admin chrome follows the admin prototype: fixed 240px themed sidebar with the
// logo lockup, the primary "new assessment" CTA, flat navigation and a
// full-width logout button at the bottom.
function AdminSidebar({ onLogout, isLearner }) {
  useLocale()
  const { account } = useAuth()
  return (
    <aside className="app-sidebar fixed inset-y-0 left-0 z-40 hidden w-60 flex-col border-r border-edge md:flex">
      <div className="px-5 pb-5 pt-6">
        <Link to="/" className="admin-art-brand" aria-label="DBCAS">
          <span className="admin-signature-row">
            <BrandSymbol className="admin-signature-symbol" />
            <span className="admin-refined-wordmark">BCAS</span>
          </span>
          <span className="admin-art-caption">{t('nav.engineTagFull')}</span>
        </Link>
      </div>
      <div className="px-4">
        <Link
          to="/admin/assessments"
          className="admin-new-assessment flex w-full items-center justify-center gap-2 rounded-lg border border-edge2 px-4 py-2.5 text-sm font-medium text-sub transition-colors hover:bg-surface-hover hover:text-ink"
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
            <p className="px-3 pb-2 pt-2 text-[11px] font-semibold uppercase tracking-[.14em] text-mute">{t('nav.administration')}</p>
          </>
        )}
        {ADMIN_LINKS.map((l) => (
          <NavLink key={l.to} to={l.to} end={l.end} className={sideLinkCls}>
            <Icon name={l.icon} className="h-4 w-4 shrink-0" />
            {t(l.label)}
          </NavLink>
        ))}
      </nav>
      {account && (
        <div className="border-t border-edge/70 p-4">
          <button
            type="button"
            onClick={onLogout}
            className="flex w-full items-center justify-center gap-2 rounded-lg border border-edge2 px-3 py-2 text-sm font-medium text-sub hover:bg-surface-hover hover:text-ink"
          >
            <Icon name="logout" className="h-4 w-4" />
            {t('nav.logout')}
          </button>
        </div>
      )}
    </aside>
  )
}

function MobileTopbar({ links, onLogout }) {
  useLocale()
  const { account } = useAuth()
  return (
    <header className="chrome-dark sticky top-0 z-40 border-b md:hidden">
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

// The prototypes close every page with a slim themed footer: wordmark + product
// line on the left, copyright on the right.
function ChromeFooter({ className = '' }) {
  useLocale()
  return (
    <footer className={`chrome-footer ${className}`}>
      <div className="mx-auto flex min-h-16 max-w-[1480px] flex-wrap items-center justify-between gap-3 px-4 py-4 sm:px-6">
        <p>
          <strong className="font-mono font-bold text-cyan-300">DBCAS</strong>
          <span aria-hidden="true" className="mx-2 text-mute">•</span>
          {t('nav.footerTagline')}
        </p>
        <p className="text-mute">{t('nav.copyright', { year: new Date().getFullYear() })}</p>
      </div>
    </footer>
  )
}

// App frame: role-aware chrome ported from the frontend branch — learner
// topbar, admin sidebar — with the real role guard and client-side logout.
function LayoutContent({ children }) {
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
    <div className={`min-h-screen bg-abyss text-ink ${isAdmin && !isExam ? 'admin-workspace' : ''}`}>
      <a href="#main-content" className="skip-link">{t('nav.skipContent')}</a>

      {!isExam && isAdmin ? (
        <>
          <AdminSidebar onLogout={handleLogout} isLearner={isLearner} />
          {/* desktop utility bar */}
          <header className="chrome-dark hidden min-h-14 items-center justify-between gap-4 border-b px-6 md:ml-60 md:flex">
            <p className="text-sm text-mute">
              <span className="font-semibold text-sub">DBCAS</span>
              <span aria-hidden="true" className="mx-3 text-mute">›</span>
              {t(pageLabel || 'nav.administration')}
            </p>
            <div className="flex items-center gap-3">
              <LanguageSelector />
              <ThemeSelector />
              {account && (
                <div className="flex items-center gap-2.5 border-l border-edge pl-3">
                  <AccountChip account={account} onLogout={handleLogout} />
                </div>
              )}
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
        className={`min-w-0 ${
          isExam
            ? 'flex flex-col'
            : isAdmin
              ? 'page-photo px-4 py-6 sm:px-6 lg:py-8 md:pl-[calc(15rem+1.5rem)] lg:pr-8'
              : ''
        }`}
        style={isAdmin && !isExam ? { '--page-img': `url(${adminBg})` } : undefined}
      >
        <div
          key={location.pathname}
          className={`page-enter w-full ${
            isExam ? 'flex min-h-screen flex-col' : isAdmin ? 'mx-auto max-w-[1400px]' : ''
          }`}
        >
          {children}
        </div>
      </main>

      {!isExam && <ChromeFooter className={isAdmin ? 'md:ml-60' : undefined} />}
    </div>
  )
}

// Admin keeps a separate preference so its light default does not change learner/public pages.
export default function Layout({ children }) {
  const { hasRole } = useAuth()
  const location = useLocation()
  if (hasRole('Administrator') && !location.pathname.startsWith('/exam/')) {
    return <ThemeProvider storageKey="dbcas_admin_theme" defaultTheme="light" restoreOnUnmount><LayoutContent>{children}</LayoutContent></ThemeProvider>
  }
  return <LayoutContent>{children}</LayoutContent>
}
