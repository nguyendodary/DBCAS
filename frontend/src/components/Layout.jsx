import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

const linkCls = ({ isActive }) =>
  `rounded-md px-2 py-1 ${
    isActive ? 'font-medium text-blue-700' : 'text-gray-600 hover:text-gray-900'
  }`

// App frame: role-aware navigation + client-side logout (UC03).
export default function Layout({ children }) {
  const { account, hasRole, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <Link to="/" className="flex items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-md bg-blue-600 text-xs font-bold text-white">
              DB
            </span>
            <span className="text-lg font-semibold text-gray-900">DBCAS</span>
          </Link>
          <nav aria-label="Primary" className="flex flex-wrap items-center justify-end gap-x-3 gap-y-1 text-sm">
            {hasRole('Learner') && (
              <>
                <NavLink to="/dashboard" className={linkCls}>
                  My Competency
                </NavLink>
                <NavLink to="/assessments" className={linkCls}>
                  Assessments
                </NavLink>
                <NavLink to="/history" className={linkCls}>
                  History
                </NavLink>
              </>
            )}
            {hasRole('Administrator') && (
              <NavLink to="/admin" className={linkCls}>
                Admin
              </NavLink>
            )}
            {account && (
              <>
                <span className="hidden text-gray-500 sm:inline">
                  {account.full_name || account.email}
                </span>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="rounded-md border border-gray-300 px-3 py-1 text-gray-700 hover:bg-gray-100"
                >
                  Log out
                </button>
              </>
            )}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-6">{children}</main>
    </div>
  )
}
