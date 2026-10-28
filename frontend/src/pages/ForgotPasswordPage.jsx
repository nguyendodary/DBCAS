import { t, useLocale, resolveMessage } from '../i18n'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import api, { apiMessage } from '../api'
import AuthShell from '../components/AuthShell'
import { ActionSpinner } from '../components/States'
import { Icon } from '../components/ui'

// Requests a recovery link. The backend answers 202 for every syntactically
// valid address, so the confirmation never reveals whether an account exists.
export default function ForgotPasswordPage() {
  useLocale()
  const [email, setEmail] = useState('')
  const [busy, setBusy] = useState(false)
  const [sent, setSent] = useState(false)
  const [error, setError] = useState('')

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      await api.post('/auth/password-reset/request', { email })
      setSent(true)
    } catch (err) {
      setError(apiMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthShell title={t('auth.forgotTitle')} subtitle={t('auth.forgotSubtitle')}>
      {sent ? (
        <div className="flex w-full flex-col gap-3.5" role="status">
          <p className="rounded-md border border-emerald-500/30 bg-emerald-500/10 p-3 text-sm text-emerald-200">
            <strong className="mb-1 block">{t('auth.resetRequestedTitle')}</strong>
            {t('auth.resetRequested')}
          </p>
          <Link to="/login" className="auth-submit mt-1 text-center">
            {t('auth.backToSignIn')}
          </Link>
        </div>
      ) : (
        <form onSubmit={onSubmit} aria-busy={busy} className="flex w-full flex-col gap-3.5">
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

          <button type="submit" disabled={busy} className="auth-submit mt-1">
            {busy && <ActionSpinner />}
            {busy ? t('auth.sendingResetLink') : t('auth.sendResetLink')}
          </button>

          <p className="flex w-full justify-center gap-1.5 border-t border-edge pt-4 text-xs text-sub">
            <Link to="/login" className="font-semibold text-accent hover:underline">
              {t('auth.backToSignIn')}
            </Link>
          </p>
        </form>
      )}
    </AuthShell>
  )
}
