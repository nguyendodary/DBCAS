import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../auth'
import { apiMessage } from '../api'
import AuthShell from '../components/AuthShell'
import OAuthButtons from '../components/OAuthButtons'
import PasswordInput from '../components/PasswordInput'
import { ActionSpinner } from '../components/States'
import { btnPrimary, Field, Icon, inputCls } from '../components/ui'

// Backend callback error codes → friendly text (services/oauth.py).
const OAUTH_ERRORS = {
  denied: 'Sign-in was cancelled or denied by the provider.',
  state: 'That sign-in attempt expired — please try again.',
  exchange: 'The provider could not complete sign-in. Please try again.',
  profile: 'Your provider profile could not be read. Please try again.',
  email_unverified:
    'The provider did not return a verified email address, so the sign-in cannot be linked safely.',
  account_disabled: 'This account is disabled. Contact an administrator.',
  not_configured: 'That sign-in method is not configured on this server.',
  complete: 'Sign-in could not be finished. Please try again.',
}

// UC02 — email + password → JWT; admins land on /admin, learners /dashboard.
// Social sign-in goes through the real backend OAuth flow (no mocks).
export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const oauthError = params.get('oauth_error')
  const oauthMessage = oauthError
    ? OAUTH_ERRORS[oauthError] || 'Social sign-in failed. Please try again.'
    : null

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      const account = await login(email, password)
      navigate(account.roles.includes('Administrator') ? '/admin' : '/dashboard', {
        replace: true,
      })
    } catch (err) {
      setError(apiMessage(err, 'Login failed'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthShell>
      <form onSubmit={onSubmit} aria-busy={busy}>
        <p className="mb-2 text-xs font-semibold uppercase tracking-[.16em] text-cyan-300">Welcome back</p>
        <h1 className="text-2xl font-semibold tracking-tight text-ink">Sign in to DBCAS</h1>
        <p className="mb-7 mt-2 text-sm text-mute">Continue to your assessment workspace.</p>

        {oauthMessage && (
          <p
            role="alert"
            className="mb-3 flex items-start gap-2 rounded-md border border-amber-400/30 bg-amber-400/10 p-2.5 text-sm text-amber-300"
          >
            <Icon name="alert" className="mt-0.5 h-4 w-4 shrink-0" />
            {oauthMessage}
          </p>
        )}
        {error && (
          <p
            role="alert"
            className="mb-3 rounded-md border border-rose-500/30 bg-rose-500/10 p-2.5 text-sm text-rose-300"
          >
            {error}
          </p>
        )}

        <Field label="Email" htmlFor="email" className="mb-4">
          <input
            id="email"
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={inputCls}
          />
        </Field>

        <Field label="Password" htmlFor="password" className="mb-6">
          <PasswordInput
            id="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </Field>

        <button type="submit" disabled={busy} className={`w-full ${btnPrimary}`}>
          {busy && <ActionSpinner />}
          {busy ? 'Signing in…' : 'Sign in'}
        </button>
      </form>

      <OAuthButtons />

      <p className="mt-5 text-center text-sm text-mute">
        No account?{' '}
        <Link to="/register" className="text-cyan-300 hover:underline">
          Register as a learner
        </Link>
      </p>
    </AuthShell>
  )
}
