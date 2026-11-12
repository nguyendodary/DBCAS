import { t, useLocale } from './i18n'
import { useLocalizedValidation } from './i18n/validation'
import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth'
import Layout from './components/Layout'
import { HelpProvider } from './components/HelpGuide'
import { Loading, ErrorState } from './components/States'
import WorkspaceLoading from './components/WorkspaceLoading'
import AssessmentsPage from './pages/AssessmentsPage'
import ForgotPasswordPage from './pages/ForgotPasswordPage'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import OAuthCallbackPage from './pages/OAuthCallbackPage'
import RegisterPage from './pages/RegisterPage'
import ResetPasswordPage from './pages/ResetPasswordPage'

// Heavy chart and assessment workspaces load only when their route is opened.
const DashboardPage = lazy(() => import('./pages/DashboardPage'))
const EvidencePage = lazy(() => import('./pages/EvidencePage'))
const ExamPage = lazy(() => import('./pages/ExamPage'))
const HistoryPage = lazy(() => import('./pages/HistoryPage'))
const AdminPage = lazy(() => import('./pages/AdminPage'))
const AdminAccountsPage = lazy(() => import('./pages/admin/AdminAccountsPage'))
const AdminSystemPage = lazy(() => import('./pages/admin/AdminSystemPage'))
const AdminBankPage = lazy(() => import('./pages/admin/AdminBankPage'))
const EvaluationPage = lazy(() => import('./pages/EvaluationPage'))
const SettingsPage = lazy(() => import('./pages/SettingsPage'))
const CumulativePage = lazy(() => import('./pages/CumulativePage'))
const AdminGradingPage = lazy(() => import('./pages/admin/AdminGradingPage'))

function RequireAuth({ children }) {
  useLocale()
  const { account, ready, error, retry } = useAuth()
  if (!ready) return <Loading label={t('common.loading')} />
  if (error) return <ErrorState message={error} onRetry={retry} />
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
    <RequireRole role="Learner">
      <Suspense fallback={<WorkspaceLoading label={t('common.workspaceLoading')} />}>{el}</Suspense>
    </RequireRole>
  </RequireAuth>
)

const admin = (el) => (
  <RequireAuth>
    <RequireRole role="Administrator">
      <Suspense fallback={<WorkspaceLoading label={t('common.loading')} />}>{el}</Suspense>
    </RequireRole>
  </RequireAuth>
)

// Shared authenticated route — any signed-in role may open it.
const authed = (el) => (
  <RequireAuth>
    <Suspense fallback={<WorkspaceLoading label={t('common.loading')} />}>{el}</Suspense>
  </RequireAuth>
)

// Role-aware landing (UC02): the public marketing page for signed-out
// visitors; admins go to their portal, learners to theirs.
function Home() {
  useLocale()
  const { account, ready, hasRole, error, retry } = useAuth()
  if (!ready) return <Loading label={t('common.loading')} />
  if (error) return <ErrorState message={error} onRetry={retry} />
  if (!account) return <LandingPage />
  return <Navigate to={hasRole('Administrator') ? '/admin' : '/dashboard'} replace />
}

export default function App() {
  useLocale()
  useLocalizedValidation()
  return (
    <AuthProvider>
      <HelpProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route path="/auth/callback" element={<OAuthCallbackPage />} />
          <Route path="/" element={<Home />} />

          {/* learner */}
          <Route path="/dashboard" element={learner(<DashboardPage />)} />
          <Route path="/competency" element={learner(<EvaluationPage overall />)} />
          <Route path="/evaluations/:sessionId" element={learner(<EvaluationPage />)} />
          <Route path="/assessments" element={learner(<AssessmentsPage />)} />
          <Route path="/exam/:sessionId" element={learner(<ExamPage />)} />
          <Route path="/history" element={learner(<HistoryPage />)} />
          <Route path="/history/:sessionId" element={learner(<EvidencePage />)} />

          {/* shared authenticated */}
          <Route path="/settings" element={authed(<SettingsPage />)} />

          {/* admin */}
          <Route path="/admin" element={admin(<AdminPage />)} />
          <Route
            path="/admin/curriculum"
            element={admin(<Navigate to="/admin/questions?tab=concepts" replace />)}
          />
          <Route path="/admin/questions" element={admin(<AdminBankPage />)} />
          <Route path="/admin/system" element={admin(<AdminSystemPage />)} />
          <Route path="/admin/accounts" element={admin(<AdminAccountsPage />)} />
          <Route path="/admin/grading" element={admin(<AdminGradingPage />)} />
          <Route path="/admin/grading/:reviewSessionId" element={admin(<AdminGradingPage />)} />
          <Route path="/admin/learners/:learnerId/competency" element={admin(<CumulativePage />)} />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </HelpProvider>
    </AuthProvider>
  )
}
