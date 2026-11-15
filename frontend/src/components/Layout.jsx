import { t, useLocale } from '../i18n'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { Icon } from './ui'
import LanguageSelector from './LanguageSelector'
import ThemeSelector from './ThemeSelector'
import { HelpButton } from './HelpGuide'
import BrandLogo, { BrandWordmark } from './BrandLogo'
import adminBg from '../assets/brand/SQL.jpg'

const LEARNER_LINKS = [
  { to: '/dashboard', label: 'nav.dashboard', icon: 'home' },
  { to: '/assessments', label: 'nav.assessments', icon: 'list' },
  { to: '/history', label: 'nav.history', icon: 'chart' },
  { to: '/competency', label: 'supervisor.cumulative', icon: 'chart' },
  { to: '/settings', label: 'nav.settings', icon: 'settings' },
]

const ADMIN_LINKS = [
  { to: '/admin', label: 'nav.cohort', icon: 'home', end: true },
  { to: '/admin/grading', label: 'supervisor.reviewTitle', icon: 'check' },
  { to: '/admin/accounts', label: 'nav.accounts', icon: 'users' },
  { to: '/admin/questions', label: 'nav.bank', icon: 'book' },
  { to: '/admin/system', label: 'nav.system', icon: 'settings' },
  { to: '/admin/chi-phi', label: 'Chi phí', icon: 'chart' },
]

function getLinkLabel(link, locale) {
  if (link.to === '/admin/chi-phi') {
    return locale === 'en' ? 'Costs' : 'Chi phí'
  }

  return t(link.label)
}

const sideLinkCls = ({ isActive }) =>
  `group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm ${
    isActive
      ? 'bg-cyan-400/[0.09] font-semibold text-cyan-200 shadow-[inset_3px_0_0_0_var(--primary)]'
      : 'text-mute hover:bg-surface-hover hover:text-ink'
  }`

const topLinkCls = ({ isActive }) => `nav-pill ${isActive ? 'active' : ''}`

function AccountMenu({ account, onLogout }) {
  const { locale } = useLocale()
  return (
    <div className="group relative">
      <button
        type="button"
        aria-label={account.full_name || account.email}
        title={account.full_name || account.email}
        className="flex h-9 w-9 cursor-pointer items-center justify-center rounded-full bg-cyan-400/10 text-xs font-bold text-cyan-300 ring-1 ring-inset ring-cyan-400/25 transition duration-150 hover:bg-cyan-300/30 hover:text-cyan-100 hover:ring-cyan-200/70 hover:shadow-[0_0_14px_rgba(34,211,238,0.45)] focus-visible:bg-cyan-300/30 focus-visible:text-cyan-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-300"
      >
        {(account.full_name || account.email || '?').slice(0, 1).toUpperCase()}
      </button>

      <div className="invisible absolute right-0 top-full z-50 mt-2 w-[min(19rem,calc(100vw-2rem))] translate-y-1 rounded-2xl border border-slate-200/90 bg-white p-3 text-slate-900 opacity-0 shadow-[0_18px_50px_rgba(15,23,42,0.2)] ring-1 ring-black/[0.03] transition duration-150 group-hover:visible group-hover:translate-y-0 group-hover:opacity-100 group-focus-within:visible group-focus-within:translate-y-0 group-focus-within:opacity-100">
        <div className="flex min-w-0 items-center gap-3 px-1 py-1.5">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-cyan-100 to-sky-200 text-sm font-bold text-sky-800 ring-1 ring-inset ring-sky-300/60">
            {(account.full_name || account.email || '?').slice(0, 1).toUpperCase()}
          </span>

          <div className="min-w-0 flex-1">
            <p
              className="truncate text-sm font-semibold"
              title={account.full_name || account.email}
            >
              {account.full_name || account.email}
            </p>
            {account.full_name && (
              <p className="mt-0.5 truncate text-xs text-slate-500" title={account.email}>
                {account.email}
              </p>
            )}
          </div>
        </div>

        <div className="my-2 h-px bg-slate-100" />

        <Link
          to="/upgrade"
          className="flex w-full items-center rounded-xl border border-cyan-100 bg-cyan-50 px-3 py-2.5 text-left text-sm font-medium text-cyan-700 transition-colors hover:border-cyan-200 hover:bg-cyan-100"
        >
          {locale === 'en' ? 'Upgrade' : 'Nâng cấp'}
        </Link>

        <div className="my-2 h-px bg-slate-100" />

        <button
          type="button"
          onClick={onLogout}
          className="flex w-full items-center gap-2.5 rounded-xl border border-rose-100 bg-rose-50 px-3 py-2.5 text-left text-sm font-medium text-rose-700 transition-colors hover:border-rose-200 hover:bg-rose-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-rose-400"
        >
          <Icon name="logout" className="h-4 w-4" />
          {t('nav.logout')}
        </button>
      </div>
    </div>
  )
}

function LearnerTopbar({ onLogout }) {
  useLocale()
  const { account } = useAuth()

  return (
    <header className="chrome-dark sticky top-0 z-40 border-b">
      <div className="mx-auto flex h-16 max-w-[1480px] items-center gap-4 px-4 sm:px-6">
        <BrandLogo variant="header" taglineClassName="brand-logo-tagline--responsive" />

        <nav
          aria-label={t('nav.primary')}
          className="nav-group mx-auto hidden flex-1 items-center justify-center xl:flex"
        >
          {LEARNER_LINKS.map((link) => (
            <NavLink key={link.to} to={link.to} className={topLinkCls}>
              <Icon name={link.icon} className="h-4 w-4" />
              {t(link.label)}
            </NavLink>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-2 lg:ml-0">
          <HelpButton />
          <LanguageSelector />
          <ThemeSelector />
          {account && <AccountMenu account={account} onLogout={onLogout} />}
        </div>
      </div>

      <nav
        aria-label={t('nav.primary')}
        className="flex gap-1 overflow-x-auto border-t border-edge px-3 py-2 xl:hidden"
      >
        {LEARNER_LINKS.map((link) => (
          <NavLink key={link.to} to={link.to} className={topLinkCls}>
            <Icon name={link.icon} className="h-4 w-4" />
            {t(link.label)}
          </NavLink>
        ))}
      </nav>
    </header>
  )
}

function AdminSidebar({ onLogout, isLearner }) {
  const { locale } = useLocale()
  const { account } = useAuth()

  return (
    <aside className="app-sidebar fixed inset-y-0 left-0 z-40 hidden w-60 flex-col border-r border-edge md:flex">
      <div className="px-5 pb-5 pt-6">
        <BrandLogo variant="admin" />
      </div>

      <div className="px-4">
        <Link
          to="/admin/grading"
          className="flex w-full items-center justify-center gap-2 rounded-lg border border-edge2 px-4 py-2.5 text-sm font-medium text-sub transition-colors hover:bg-surface-hover hover:text-ink"
        >
          <Icon name="plus" className="h-4 w-4" />
          {t('supervisor.reviewTitle')}
        </Link>
      </div>

      <nav
        aria-label={t('nav.primary')}
        className="mt-4 flex-1 space-y-1 overflow-y-auto px-4 py-2"
      >
        {isLearner && (
          <>
            <p className="px-3 pb-2 pt-1 text-2xs font-semibold uppercase tracking-[.14em] text-mute">
              {t('nav.learnerWorkspace')}
            </p>

            {LEARNER_LINKS.map((link) => (
              <NavLink key={link.to} to={link.to} className={sideLinkCls}>
                <Icon name={link.icon} className="h-4 w-4 shrink-0" />
                {t(link.label)}
              </NavLink>
            ))}

            <p className="px-3 pb-2 pt-2 text-2xs font-semibold uppercase tracking-[.14em] text-mute">
              {t('nav.administration')}
            </p>
          </>
        )}

        {ADMIN_LINKS.map((link) => (
          <NavLink key={link.to} to={link.to} end={link.end} className={sideLinkCls}>
            <Icon name={link.icon} className="h-4 w-4 shrink-0" />
            {getLinkLabel(link, locale)}
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
  const { locale } = useLocale()
  const { account } = useAuth()

  return (
    <header className="chrome-dark sticky top-0 z-40 border-b md:hidden">
      <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-3">
        <BrandLogo variant="header" taglineClassName="brand-logo-tagline--responsive" />

        <div className="ml-auto flex items-center gap-2">
          <HelpButton />
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
              <Icon name="logout" className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">{t('nav.logout')}</span>
            </button>
          )}
        </div>
      </div>

      <nav aria-label={t('nav.primary')} className="flex gap-1 overflow-x-auto px-3 pb-2.5">
        {links.map((link) => (
          <NavLink key={link.to} to={link.to} end={link.end} className={topLinkCls}>
            {getLinkLabel(link, locale)}
          </NavLink>
        ))}
      </nav>
    </header>
  )
}

function ChromeFooter({ className = '' }) {
  useLocale()

  return (
    <footer className={`chrome-footer ${className}`}>
      <div className="mx-auto flex min-h-12 max-w-[1480px] flex-wrap items-center justify-between gap-3 px-4 py-2 sm:px-6">
        <p className="chrome-footer-brand">
          <BrandWordmark as="strong" className="text-cyan-300" />
          <span aria-hidden="true" className="mx-2 text-mute">
            •
          </span>
          <span className="chrome-footer-brand-tagline">{t('nav.footerTagline')}</span>
        </p>

        <p className="chrome-footer-copyright text-mute">
          {t('nav.copyright', { year: new Date().getFullYear() })}
        </p>
      </div>
    </footer>
  )
}

export default function Layout({ children }) {
  const { locale } = useLocale()
  const { account, hasRole, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const isLearner = hasRole('Learner')
  const isAdmin = hasRole('Administrator')
  const isExam = location.pathname.startsWith('/exam/')

  const allLinks = [
    ...(isLearner ? LEARNER_LINKS : []),
    ...(isAdmin ? ADMIN_LINKS : []),
  ]

  const currentLink = allLinks.find((link) => link.to === location.pathname)

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen bg-abyss text-ink">
      <a href="#main-content" className="skip-link">
        {t('nav.skipContent')}
      </a>

      {!isExam && isAdmin ? (
        <>
          <AdminSidebar onLogout={handleLogout} isLearner={isLearner} />

          <header className="chrome-dark hidden min-h-14 items-center justify-between gap-4 border-b px-6 md:ml-60 md:flex">
            <p className="flex min-w-0 flex-1 items-center whitespace-nowrap text-sm text-mute">
              <BrandWordmark className="shrink-0 text-sub" />

              {currentLink && (
                <>
                  <span aria-hidden="true" className="mx-3 shrink-0 text-mute">
                    ›
                  </span>
                  <span className="truncate">{getLinkLabel(currentLink, locale)}</span>
                </>
              )}
            </p>

            <div className="flex shrink-0 items-center gap-3">
              <HelpButton />
              <LanguageSelector />
              <ThemeSelector />

              {account && (
                <div className="flex items-center gap-2.5 border-l border-edge pl-3">
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-cyan-400/10 text-xs font-bold text-cyan-300 ring-1 ring-inset ring-cyan-400/25">
                    {(account.full_name || account.email || '?').slice(0, 1).toUpperCase()}
                  </span>

                  <div className="hidden min-w-0 max-w-[240px] lg:block">
                    <p
                      className="truncate text-sm font-medium leading-tight"
                      title={account.full_name || account.email}
                    >
                      {account.full_name || account.email}
                    </p>
                    <p className="truncate text-xs leading-tight text-mute" title={account.email}>
                      {account.email}
                    </p>
                  </div>
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