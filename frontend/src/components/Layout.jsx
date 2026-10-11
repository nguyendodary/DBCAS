import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { Icon } from './ui'

const LEARNER_LINKS = [
  { to: '/dashboard', label: 'My Competency', icon: 'chart' },
  { to: '/assessments', label: 'Assessments', icon: 'play' },
  { to: '/history', label: 'History', icon: 'clock' },
]

const ADMIN_LINKS = [
  { to: '/admin', label: 'Cohort', icon: 'users', end: true },
  { to: '/admin/curriculum', label: 'Curriculum', icon: 'book' },
  { to: '/admin/questions', label: 'Question Bank', icon: 'edit' },
  { to: '/admin/candidates', label: 'AI Candidates', icon: 'spark' },
  { to: '/admin/assessments', label: 'Assessments', icon: 'target' },
  { to: '/admin/accounts', label: 'Accounts', icon: 'shield' },
]

const sideLinkCls = ({ isActive }) =>
  `flex items-center gap-3 rounded-r-lg border-l-2 px-3 py-2.5 text-sm ${
    isActive
      ? 'border-cyan-400 bg-cyan-400/[0.08] font-semibold text-cyan-200'
      : 'border-transparent text-sub hover:bg-white/[0.035] hover:text-ink'
  }`

const topLinkCls = ({ isActive }) =>
  `whitespace-nowrap rounded-lg px-3 py-2 text-sm ${
    isActive ? 'bg-cyan-400/10 font-semibold text-cyan-200' : 'text-sub hover:bg-white/5 hover:text-ink'
  }`

function Brand() {
  return (
    <Link to="/" className="flex items-center gap-2.5">
      <span className="flex h-8 w-8 items-center justify-center rounded-lg border border-cyan-400/20 bg-cyan-400/[0.08] text-cyan-300">
        <Icon name="database" className="h-4.5 w-4.5" />
      </span>
      <span className="text-base font-bold tracking-tight text-ink">DBCAS</span>
    </Link>
  )
}

function SideNav({ isLearner, isAdmin }) {
  return (
    <nav aria-label="Primary" className="flex-1 space-y-1 overflow-y-auto px-3 py-5">
      {isLearner && <p className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-[.14em] text-mute">Learner workspace</p>}
      {isLearner &&
        LEARNER_LINKS.map((l) => (
          <NavLink key={l.to} to={l.to} className={sideLinkCls}>
            <Icon name={l.icon} className="h-4 w-4 shrink-0" />
            {l.label}
          </NavLink>
        ))}
      {isAdmin && (
        <>
          <p className="px-3 pb-2 pt-2 text-[11px] font-semibold uppercase tracking-[.14em] text-mute">
            Administration
          </p>
          {ADMIN_LINKS.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.end} className={sideLinkCls}>
              <Icon name={l.icon} className="h-4 w-4 shrink-0" />
              {l.label}
            </NavLink>
          ))}
        </>
      )}
    </nav>
  )
}

// App frame: prototype-style dark sidebar on desktop, a compact top bar
// with a scrollable nav on small screens. Role-aware links + client-side
// logout (UC03).
export default function Layout({ children }) {
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

  return (
    <div className="min-h-screen bg-abyss text-ink">
      {/* desktop sidebar */}
      {!isExam && <aside className="fixed inset-y-0 left-0 z-40 hidden w-58 flex-col border-r border-edge bg-panel md:flex">
        <div className="border-b border-edge/70 px-5 py-5">
          <Brand />
        </div>
        <SideNav isLearner={isLearner} isAdmin={isAdmin} />
        {account && (
          <div className="border-t border-edge/70 p-3">
            <div className="flex items-center gap-2.5 rounded-lg px-2 py-1.5">
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-elev text-xs font-bold text-cyan-300">
                {(account.full_name || account.email || '?').slice(0, 1).toUpperCase()}
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-ink">
                  {account.full_name || account.email}
                </p>
                <p className="truncate text-xs text-mute">{account.email}</p>
              </div>
              <button
                type="button"
                onClick={handleLogout}
                aria-label="Log out"
                title="Log out"
                className="rounded-md p-1.5 text-mute transition-colors hover:bg-white/5 hover:text-rose-300"
              >
                <Icon name="logout" className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </aside>}

      {/* mobile top bar */}
      {!isExam && <header className="sticky top-0 z-40 border-b border-edge bg-panel/95 backdrop-blur md:hidden">
        <div className="flex items-center justify-between px-4 py-3">
          <Brand />
          {account && (
            <button
              type="button"
              onClick={handleLogout}
              className="flex items-center gap-1.5 rounded-md border border-edge2 px-2.5 py-1.5 text-xs text-sub hover:bg-white/5"
            >
              <Icon name="logout" className="h-3.5 w-3.5" />
              Log out
            </button>
          )}
        </div>
        <nav
          aria-label="Primary"
          className="flex gap-1 overflow-x-auto px-3 pb-2.5"
        >
          {allLinks.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.end} className={topLinkCls}>
              {l.label}
            </NavLink>
          ))}
        </nav>
      </header>}

      <main className={`px-4 py-6 sm:px-6 lg:py-8 ${isExam ? 'lg:px-8' : 'md:pl-[calc(14.5rem+1.5rem)] lg:pr-8'}`}>
        <div key={location.pathname} className={`page-enter mx-auto w-full ${isExam ? 'max-w-[1440px]' : 'max-w-7xl'}`}>{children}</div>
      </main>
    </div>
  )
}
