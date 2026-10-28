import { t, useLocale, resolveMessage } from '../i18n'
import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import api, { apiMessage } from '../api'
import AuthShell from '../components/AuthShell'
import PasswordInput from '../components/PasswordInput'
import { ActionSpinner } from '../components/States'

// Redeems the single-use token from the emailed link. Missing, expired,
// reused and invalid tokens all render the same "request a new link" state.
export default function ResetPasswordPage() {
  useLocale()
  const [params] = useSearchParams()
  const token = params.get('token') || ''
  const [form, setForm] = useState({ password: '', password_confirm: '' })
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(false)
  const [invalid, setInvalid] = useState(!token)
  const [error, setError] = useState('')

  function set(field) {
    return (e) => setForm({ ...form, [field]: e.target.value })
  }

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    if (form.password.length < 8) {
      setError(t('auth.passwordTooShort'))
      return
    }
    if (form.password !== form.password_confirm) {
      setError(t('auth.passwordMismatch'))
      return
    }
    setBusy(true)
    try {
      await api.post('/auth/password-reset/confirm', { token, ...form })
      setDone(true)
    } catch (err) {
      if (err?.response?.data?.error?.code === 'invalid_reset_token') setInvalid(true)
      else setError(apiMessage(err))
    } finally {
      setBusy(false)
    }
  }

  if (invalid) {
    return (
      <AuthShell title={t('auth.resetLinkInvalidTitle')} subtitle={t('auth.resetLinkInvalidBody')}>
        <div className="flex w-full flex-col gap-3.5">
          <Link to="/forgot-password" className="auth-submit mt-1 text-center">
            {t('auth.requestNewLink')}
          </Link>
          <p className="flex w-full justify-center gap-1.5 border-t border-edge pt-4 text-xs text-sub">
            <Link to="/login" className="font-semibold text-accent hover:underline">
              {t('auth.backToSignIn')}
            </Link>
          </p>
        </div>
      </AuthShell>
    )
  }

  if (done) {
    return (
      <AuthShell title={t('auth.resetSuccessTitle')} subtitle={t('auth.resetSuccessBody')}>
        <div className="flex w-full flex-col gap-3.5" role="status">
          <Link to="/login" className="auth-submit mt-1 text-center">
            {t('auth.backToSignIn')}
          </Link>
        </div>
      </AuthShell>
    )
  }

  return (
    <AuthShell title={t('auth.resetTitle')} subtitle={t('auth.resetSubtitle')}>
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
          <label className="auth-label" htmlFor="password">{t('auth.newPassword')}</label>
          <PasswordInput
            id="password"
            autoComplete="new-password"
            placeholder={t('auth.passwordPlaceholder')}
            value={form.password}
            onChange={set('password')}
          />
          <p className="mt-1 text-xs text-sub">{t('auth.resetPasswordHint')}</p>
        </div>

        <div>
          <label className="auth-label" htmlFor="password_confirm">{t('auth.confirmPassword')}</label>
          <PasswordInput
            id="password_confirm"
            autoComplete="new-password"
            placeholder={t('auth.confirmPlaceholder')}
            value={form.password_confirm}
            onChange={set('password_confirm')}
          />
        </div>

        <button type="submit" disabled={busy} className="auth-submit mt-1">
          {busy && <ActionSpinner />}
          {busy ? t('auth.resettingPassword') : t('auth.resetPassword')}
        </button>

        <p className="flex w-full justify-center gap-1.5 border-t border-edge pt-4 text-xs text-sub">
          <Link to="/login" className="font-semibold text-accent hover:underline">
            {t('auth.backToSignIn')}
          </Link>
        </p>
      </form>
    </AuthShell>
  )
}
