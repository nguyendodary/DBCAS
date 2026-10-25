import { t, useLocale, resolveMessage } from '../../i18n'
import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../../auth'
import { apiMessage } from '../../api'
import AuthShell from '../../components/AuthShell'
import OAuthButtons from '../../components/OAuthButtons'
import PasswordInput from '../../components/PasswordInput'
import { ActionSpinner } from '../../components/States'
import { Icon } from '../../components/SharedComponents'

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
export default function Login() {
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
    <AuthShell className="auth-refined auth-login-compact" title={<>{t('auth.loginTitle').replace('DBCAS', '').trim()} <span className="auth-login-brand">DBCAS</span></>} subtitle={t('auth.loginSubtitle')} headingClassName="auth-login-heading">
      <form onSubmit={onSubmit} aria-busy={busy} className="flex w-full flex-col gap-3.5">
        {oauthMessage && (
          <p
            role="alert"
            className="flex items-start gap-2 rounded-md border border-amber-400/30 bg-amber-400/10 p-2.5 text-sm text-amber-300"
          >
            <Icon name="alert" className="mt-0.5 h-4 w-4 shrink-0" />
            {oauthMessage}
          </p>
        )}
        {error && (
          <p
            role="alert"
            className="rounded-md border border-rose-500/30 bg-rose-500/10 p-2.5 text-sm text-rose-300"
          >
            {resolveMessage(error)}
          </p>
        )}

        <div>
          <label className="auth-label" htmlFor="email">{t('auth.emailLabel')}</label>
          <div className="auth-field">
            <Icon name="mail" className="auth-field-icon" />
            <input
              id="email"
              type="email"
              required
              autoComplete="email"
              placeholder={t('auth.emailPlaceholder')}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
        </div>

        <div>
          <label className="auth-label" htmlFor="password">{t('auth.password')}</label>
          <PasswordInput
            id="password"
            autoComplete="current-password"
            placeholder={t('auth.passwordPlaceholder')}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <div className="mt-2 flex justify-end">
            <Link className="auth-forgot-link" to="/forgot-password">{t('auth.forgotPassword')}</Link>
          </div>
        </div>

        <button type="submit" disabled={busy} className="auth-submit mt-1">
          {busy && <ActionSpinner />}
          {busy ? t('auth.signingIn') : t('auth.signIn')}
        </button>
      </form>

      <OAuthButtons />

      <p className="flex w-full justify-center gap-1.5 border-t border-edge pt-4 text-xs text-sub">
        {t('auth.noAccount')}
        <Link to="/register" className="font-semibold text-accent hover:underline">{t('auth.registerLearner')}</Link>
      </p>
    </AuthShell>
  )
}
