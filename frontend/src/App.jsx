import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth'
import Layout from './components/Layout'
import { Loading } from './components/States'
import AssessmentsPage from './pages/AssessmentsPage'
import DashboardPage from './pages/DashboardPage'
import EvidencePage from './pages/EvidencePage'
import ExamPage from './pages/ExamPage'
import HistoryPage from './pages/HistoryPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'

// Admin screens are only ever loaded by admin sessions — split them out
// of the learner bundle (NFR performance).
const AdminPage = lazy(() => import('./pages/AdminPage'))
const AdminAccountsPage = lazy(() => import('./pages/admin/AdminAccountsPage'))
const AdminAssessmentsPage = lazy(() => import('./pages/admin/AdminAssessmentsPage'))
const AdminCandidatesPage = lazy(() => import('./pages/admin/AdminCandidatesPage'))
const AdminCurriculumPage = lazy(() => import('./pages/admin/AdminCurriculumPage'))
const AdminQuestionsPage = lazy(() => import('./pages/admin/AdminQuestionsPage'))

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

const learner = (el) => (
  <RequireAuth>
    <RequireRole role="Learner">{el}</RequireRole>
  </RequireAuth>
)

const admin = (el) => (
  <RequireAuth>
    <RequireRole role="Administrator">
      <Suspense fallback={<Loading label="Loading…" />}>{el}</Suspense>
    </RequireRole>
  </RequireAuth>
)

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

        {/* learner */}
        <Route path="/dashboard" element={learner(<DashboardPage />)} />
        <Route path="/assessments" element={learner(<AssessmentsPage />)} />
        <Route path="/exam/:sessionId" element={learner(<ExamPage />)} />
        <Route path="/history" element={learner(<HistoryPage />)} />
        <Route path="/history/:sessionId" element={learner(<EvidencePage />)} />

        {/* admin */}
        <Route path="/admin" element={admin(<AdminPage />)} />
        <Route path="/admin/curriculum" element={admin(<AdminCurriculumPage />)} />
        <Route path="/admin/questions" element={admin(<AdminQuestionsPage />)} />
        <Route path="/admin/candidates" element={admin(<AdminCandidatesPage />)} />
        <Route path="/admin/assessments" element={admin(<AdminAssessmentsPage />)} />
        <Route path="/admin/accounts" element={admin(<AdminAccountsPage />)} />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  )
}
