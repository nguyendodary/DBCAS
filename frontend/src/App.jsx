import { Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth'
import Layout from './components/Layout'
import { Loading } from './components/States'
import DashboardPage from './pages/DashboardPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'

function RequireAuth({ children }) {
  const { account, ready } = useAuth()
  if (!ready) return <Loading label="Loading…" />
  if (!account) return <Navigate to="/login" replace />
  return <Layout>{children}</Layout>
}

function RequireRole({ role, children }) {
  const { hasRole } = useAuth()
  if (!hasRole(role)) return <Navigate to="/" replace />
  return children
}

// Role-aware landing (UC02): admins go to their portal, learners to theirs.
function Home() {
  const { account, ready, hasRole } = useAuth()
  if (!ready) return <Loading label="Loading…" />
  if (!account) return <Navigate to="/login" replace />
  return <Navigate to={hasRole('Administrator') ? '/admin' : '/dashboard'} replace />
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/" element={<Home />} />
        <Route
          path="/dashboard"
          element={
            <RequireAuth>
              <RequireRole role="Learner">
                <DashboardPage />
              </RequireRole>
            </RequireAuth>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  )
}
