import { t, useLocale } from './i18n'
import { useLocalizedValidation } from './i18n/validation'
import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth'
import Layout from './components/Layout'
import { Loading, ErrorState } from './components/States'
import AssessmentListPage from './pages/AssessmentListPage'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import ForgotPasswordPage from './pages/ForgotPasswordPage'
import OAuthCallbackPage from './pages/OAuthCallbackPage'
import RegisterPage from './pages/RegisterPage'

// Heavy chart and assessment workspaces load only when their route is opened.
const LearnerDashboardPage = lazy(() => import('./pages/LearnerDashboardPage'))
const LearnerLeaderboardPage = lazy(() => import('./pages/LearnerLeaderboardPage'))
const AssessmentReviewPage = lazy(() => import('./pages/AssessmentReviewPage'))
const AssessmentAttemptPage = lazy(() => import('./pages/AssessmentAttemptPage'))
const AssessmentHistoryPage = lazy(() => import('./pages/AssessmentHistoryPage'))
const AdminDashboardPage = lazy(() => import('./pages/AdminDashboardPage'))
const AdminAccountsPage = lazy(() => import('./pages/admin/AdminAccountsPage'))
const AdminAssessmentsPage = lazy(() => import('./pages/admin/AdminAssessmentsPage'))
const AdminQuestionSuggestionsPage = lazy(() => import('./pages/admin/AdminQuestionSuggestionsPage'))
const AdminCurriculumPage = lazy(() => import('./pages/admin/AdminCurriculumPage'))
const AdminQuestionsPage = lazy(() => import('./pages/admin/AdminQuestionsPage'))
const AccountSettingsPage = lazy(() => import('./pages/AccountSettingsPage'))
const CumulativeCompetencyPage = lazy(() => import('./pages/CumulativeCompetencyPage'))
const AdminEssayReviewPage = lazy(() => import('./pages/admin/AdminEssayReviewPage'))
const AdminLeaderboardPage = lazy(() => import('./pages/admin/AdminLeaderboardPage'))

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
      <Suspense fallback={<Loading label={t('common.workspaceLoading')} />}>{el}</Suspense>
    </RequireRole>
  </RequireAuth>
)

const admin = (el) => (
  <RequireAuth>
    <RequireRole role="Administrator">
      <Suspense fallback={<Loading label={t('common.loading')} />}>{el}</Suspense>
    </RequireRole>
  </RequireAuth>
)

// Shared authenticated route — any signed-in role may open it.
const authed = (el) => (
  <RequireAuth>
    <Suspense fallback={<Loading label={t('common.loading')} />}>{el}</Suspense>
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
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/auth/callback" element={<OAuthCallbackPage />} />
        <Route path="/" element={<Home />} />

        {/* learner */}
        <Route path="/dashboard" element={learner(<LearnerDashboardPage />)} />
        <Route path="/leaderboard" element={learner(<LearnerLeaderboardPage />)} />
        <Route path="/competency" element={learner(<CumulativeCompetencyPage />)} />
        <Route path="/assessments" element={learner(<AssessmentListPage />)} />
        <Route path="/exam/:sessionId" element={learner(<AssessmentAttemptPage />)} />
        <Route path="/history" element={learner(<AssessmentHistoryPage />)} />
        <Route path="/history/:sessionId" element={learner(<AssessmentReviewPage />)} />

        {/* shared authenticated */}
        <Route path="/settings" element={authed(<AccountSettingsPage />)} />

        {/* admin */}
        <Route path="/admin" element={admin(<AdminDashboardPage />)} />
        <Route path="/admin/leaderboard" element={admin(<AdminLeaderboardPage />)} />
        <Route path="/admin/curriculum" element={admin(<AdminCurriculumPage />)} />
        <Route path="/admin/questions" element={admin(<AdminQuestionsPage />)} />
        <Route path="/admin/candidates" element={admin(<AdminQuestionSuggestionsPage />)} />
        <Route path="/admin/assessments" element={admin(<AdminAssessmentsPage />)} />
        <Route path="/admin/accounts" element={admin(<AdminAccountsPage />)} />
        <Route path="/admin/grading" element={admin(<AdminEssayReviewPage />)} />
        <Route path="/admin/grading/:reviewSessionId" element={admin(<AdminEssayReviewPage />)} />
        <Route path="/admin/learners/:learnerId/competency" element={admin(<CumulativeCompetencyPage />)} />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  )
}
