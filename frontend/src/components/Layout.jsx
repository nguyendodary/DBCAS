import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

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
          <Link to="/" className="text-lg font-semibold text-gray-900">
            DBCAS
          </Link>
          <nav className="flex items-center gap-4 text-sm">
            {hasRole('Learner') && (
              <Link to="/dashboard" className="text-gray-700 hover:text-gray-900">
                My Competency
              </Link>
            )}
            {hasRole('Administrator') && (
              <Link to="/admin" className="text-gray-700 hover:text-gray-900">
                Admin
              </Link>
            )}
            {account && (
              <>
                <span className="hidden text-gray-500 sm:inline">
                  {account.full_name || account.email}
                </span>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="rounded border border-gray-300 px-3 py-1 text-gray-700 hover:bg-gray-100"
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
