import { t, useLocale } from './i18n'
import { useLocalizedValidation } from './i18n/validation'
import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth'
import Layout from './components/Layout'
import { Loading, ErrorState } from './components/States'
import Assessments_User from './pages/user/Assessments_User'
import Home from './pages/public/Home'
import Login from './pages/public/Login'
import ForgotPassword from './pages/public/ForgotPassword'
import OAuthCallback from './pages/public/OAuthCallback'
import Register from './pages/public/Register'

// Heavy chart and assessment workspaces load only when their route is opened.
const Dashboard_User = lazy(() => import('./pages/user/Dashboard_User'))
const Leaderboard_User = lazy(() => import('./pages/user/Leaderboard_User'))
const AssessmentReview_User = lazy(() => import('./pages/user/AssessmentReview_User'))
const AssessmentAttempt_User = lazy(() => import('./pages/user/AssessmentAttempt_User'))
const History_User = lazy(() => import('./pages/user/History_User'))
const Dashboard_Admin = lazy(() => import('./pages/admin/Dashboard_Admin'))
const Accounts_Admin = lazy(() => import('./pages/admin/Accounts_Admin'))
const Assessments_Admin = lazy(() => import('./pages/admin/Assessments_Admin'))
const QuestionSuggestions_Admin = lazy(() => import('./pages/admin/QuestionSuggestions_Admin'))
const Curriculum_Admin = lazy(() => import('./pages/admin/Curriculum_Admin'))
const Questions_Admin = lazy(() => import('./pages/admin/Questions_Admin'))
const Settings_User = lazy(() => import('./pages/user/Settings_User'))
const CumulativeCompetency_User = lazy(() => import('./pages/user/CumulativeCompetency_User'))
const EssayReview_Admin = lazy(() => import('./pages/admin/EssayReview_Admin'))
const Leaderboard_Admin = lazy(() => import('./pages/admin/Leaderboard_Admin'))

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
function RoleAwareHome() {
  useLocale()
  const { account, ready, hasRole, error, retry } = useAuth()
  if (!ready) return <Loading label={t('common.loading')} />
  if (error) return <ErrorState message={error} onRetry={retry} />
  if (!account) return <Home />
  return <Navigate to={hasRole('Administrator') ? '/admin' : '/dashboard'} replace />
}

export default function App() {
  useLocale()
  useLocalizedValidation()
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/register" element={<Register />} />
        <Route path="/auth/callback" element={<OAuthCallback />} />
        <Route path="/" element={<RoleAwareHome />} />

        {/* learner */}
        <Route path="/dashboard" element={learner(<Dashboard_User />)} />
        <Route path="/leaderboard" element={learner(<Leaderboard_User />)} />
        <Route path="/competency" element={learner(<CumulativeCompetency_User />)} />
        <Route path="/assessments" element={learner(<Assessments_User />)} />
        <Route path="/exam/:sessionId" element={learner(<AssessmentAttempt_User />)} />
        <Route path="/history" element={learner(<History_User />)} />
        <Route path="/history/:sessionId" element={learner(<AssessmentReview_User />)} />

        {/* shared authenticated */}
        <Route path="/settings" element={authed(<Settings_User />)} />

        {/* admin */}
        <Route path="/admin" element={admin(<Dashboard_Admin />)} />
        <Route path="/admin/leaderboard" element={admin(<Leaderboard_Admin />)} />
        <Route path="/admin/curriculum" element={admin(<Curriculum_Admin />)} />
        <Route path="/admin/questions" element={admin(<Questions_Admin />)} />
        <Route path="/admin/candidates" element={admin(<QuestionSuggestions_Admin />)} />
        <Route path="/admin/assessments" element={admin(<Assessments_Admin />)} />
        <Route path="/admin/accounts" element={admin(<Accounts_Admin />)} />
        <Route path="/admin/grading" element={admin(<EssayReview_Admin />)} />
        <Route path="/admin/grading/:reviewSessionId" element={admin(<EssayReview_Admin />)} />
        <Route path="/admin/learners/:learnerId/competency" element={admin(<CumulativeCompetency_User />)} />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  )
}
