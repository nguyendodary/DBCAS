import { t, useLocale, resolveMessage } from '../i18n'
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
  denied: 'auth.oauthDenied',
  state: 'auth.oauthState',
  exchange: 'auth.oauthExchange',
  profile: 'auth.oauthProfile',
  email_unverified:
    'auth.oauthEmail',
  account_disabled: 'auth.accountDisabled',
  not_configured: 'auth.oauthNotConfigured',
  complete: 'auth.oauthComplete',
}

// UC02 — email + password → JWT; admins land on /admin, learners /dashboard.
// Social sign-in goes through the real backend OAuth flow (no mocks).
export default function LoginPage() {
  useLocale()
  const { login } = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const oauthError = params.get('oauth_error')
  const oauthMessage = oauthError
    ? t(Object.hasOwn(OAUTH_ERRORS, oauthError) ? OAUTH_ERRORS[oauthError] : 'auth.oauthFailed')
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
      setError(apiMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthShell>
      <form onSubmit={onSubmit} aria-busy={busy}>
        <p className="mb-2 text-xs font-semibold uppercase tracking-[.16em] text-cyan-300">{t('auth.welcome')}</p>
        <h1 className="text-2xl font-semibold tracking-tight text-ink">{t('auth.loginTitle')}</h1>
        <p className="mb-7 mt-2 text-sm text-mute">{t('auth.loginSubtitle')}</p>

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
            {resolveMessage(error)}
          </p>
        )}

        <Field label={t('common.email')} htmlFor="email" className="mb-4">
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

        <Field label={t('auth.password')} htmlFor="password" className="mb-6">
          <PasswordInput
            id="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </Field>

        <button type="submit" disabled={busy} className={`w-full ${btnPrimary}`}>
          {busy && <ActionSpinner />}
          {busy ? t('auth.signingIn') : t('auth.signIn')}
        </button>
      </form>

      <OAuthButtons />

      <p className="mt-5 text-center text-sm text-mute">{t('auth.noAccount')}{' '}
        <Link to="/register" className="text-cyan-300 underline underline-offset-4 hover:text-cyan-200">{t('auth.registerLearner')}</Link>
      </p>
    </AuthShell>
  )
}
