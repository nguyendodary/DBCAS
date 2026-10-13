import { t, useLocale, resolveMessage } from '../i18n'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { apiMessage } from '../api'
import AuthShell from '../components/AuthShell'
import OAuthButtons from '../components/OAuthButtons'
import PasswordInput from '../components/PasswordInput'
import { ActionSpinner } from '../components/States'
import { Icon } from '../components/ui'

// UC01 — learner self-registration (always the Learner role server-side;
// this screen cannot create administrators).
export default function RegisterPage() {
  useLocale()
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    password_confirm: '',
  })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  function set(field) {
    return (e) => setForm({ ...form, [field]: e.target.value })
  }

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      await register(form.name, form.email, form.password, form.password_confirm)
      navigate('/login', { replace: true })
    } catch (err) {
      setError(apiMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthShell title={t('auth.registerTitle')} subtitle={t('auth.registerSubtitle')}>
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
          <label className="auth-label" htmlFor="name">{t('common.fullName')}</label>
          <div className="auth-field">
            <Icon name="user" className="auth-field-icon" />
            <input
              id="name"
              required
              autoComplete="name"
              placeholder={t('auth.namePlaceholder')}
              value={form.name}
              onChange={set('name')}
            />
          </div>
        </div>

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
              value={form.email}
              onChange={set('email')}
            />
          </div>
        </div>

        <div>
          <label className="auth-label" htmlFor="password">{t('auth.password')}</label>
          <PasswordInput
            id="password"
            autoComplete="new-password"
            placeholder={t('auth.passwordPlaceholder')}
            value={form.password}
            onChange={set('password')}
          />
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
          {busy ? t('auth.creating') : t('auth.register')}
        </button>
      </form>

      <OAuthButtons divider={t('auth.signupDivider')} />

      <p className="flex w-full justify-center gap-1.5 border-t border-[#3d494c33] pt-4 text-xs text-[#bcc9cd]">
        {t('auth.alreadyRegistered')}
        <Link to="/login" className="font-semibold text-[#4cd7f6] hover:underline">{t('auth.signIn')}</Link>
      </p>
    </AuthShell>
  )
}
