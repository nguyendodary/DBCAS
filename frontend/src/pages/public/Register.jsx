import { t, useLocale, resolveMessage } from '../../i18n'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../auth'
import { apiMessage } from '../../api'
import AuthShell from '../../components/AuthShell'
import OAuthButtons from '../../components/OAuthButtons'
import PasswordInput from '../../components/PasswordInput'
import { ActionSpinner } from '../../components/States'
import { Icon } from '../../components/SharedComponents'

// UC01 — learner self-registration (always the Learner role server-side;
// this screen cannot create administrators).
export default function Register() {
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
  const [fieldErrors, setFieldErrors] = useState({})
  const [submitted, setSubmitted] = useState(false)

  function validate(values) {
    const errors = {}
    if (!values.name.trim()) errors.name = 'validation.required'
    else if (values.name.trim().length > 100) errors.name = 'auth.registerNameLong'
    if (!values.email.trim()) errors.email = 'validation.required'
    else if (values.email.trim().length > 255 || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(values.email.trim())) errors.email = 'validation.email'
    if (!values.password) errors.password = 'validation.required'
    else if ([...values.password].length < 8) errors.password = 'auth.registerPasswordShort'
    else if (new TextEncoder().encode(values.password).length > 72) errors.password = 'auth.registerPasswordLong'
    if (!values.password_confirm) errors.password_confirm = 'validation.required'
    else if (values.password_confirm !== values.password) errors.password_confirm = 'auth.registerPasswordMismatch'
    return errors
  }

  function set(field) {
    return (e) => {
      const next = { ...form, [field]: e.target.value }
      setForm(next)
      setError('')
      if (submitted) setFieldErrors(validate(next))
    }
  }

  function fieldProps(field) {
    return {
      'aria-invalid': Boolean(fieldErrors[field]),
      'aria-describedby': fieldErrors[field] ? `${field}-error` : field === 'password' ? 'password-hint' : undefined,
    }
  }

  function fieldError(field) {
    return fieldErrors[field] ? <p id={`${field}-error`} className="mt-1.5 text-xs text-danger" role="alert">{t(fieldErrors[field])}</p> : null
  }

  function showFieldErrors(errors) {
    setFieldErrors(errors)
    document.getElementById(Object.keys(errors)[0])?.focus()
  }

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    setSubmitted(true)
    const errors = validate(form)
    if (Object.keys(errors).length) {
      showFieldErrors(errors)
      return
    }
    setFieldErrors({})
    setBusy(true)
    try {
      await register(form.name.trim(), form.email.trim(), form.password, form.password_confirm)
      navigate('/login', { replace: true })
    } catch (err) {
      const code = err?.response?.data?.error?.code
      if (['email_exists', 'email_taken'].includes(code)) {
        showFieldErrors({ email: 'errors.email_exists' })
      } else if (code === 'validation_error') {
        const errors = {}
        for (const detail of err.response.data.error.details || []) {
          const field = detail.loc?.[detail.loc.length - 1]
          if (Object.hasOwn(form, field)) errors[field] = 'validation.format'
        }
        if (Object.keys(errors).length) showFieldErrors(errors)
        else setError(apiMessage(err))
      } else setError(apiMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthShell className="auth-register-compact" headingClassName="auth-login-heading auth-register-heading" title={<>{t('auth.registerTitle')} <span className="auth-login-brand">DBCAS</span></>} subtitle={t('auth.registerSubtitle')}>
      <form noValidate onSubmit={onSubmit} aria-busy={busy} className="flex w-full flex-col gap-3.5">
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
              {...fieldProps('name')}
              required
              autoComplete="name"
              placeholder={t('auth.namePlaceholder')}
              value={form.name}
              onChange={set('name')}
            />
          </div>
          {fieldError('name')}
        </div>

        <div>
          <label className="auth-label" htmlFor="email">{t('auth.emailLabel')}</label>
          <div className="auth-field">
            <Icon name="mail" className="auth-field-icon" />
            <input
              id="email"
              {...fieldProps('email')}
              type="email"
              required
              autoComplete="email"
              placeholder={t('auth.emailPlaceholder')}
              value={form.email}
              onChange={set('email')}
            />
          </div>
          {fieldError('email')}
        </div>

        <div>
          <label className="auth-label" htmlFor="password">{t('auth.password')}</label>
          <PasswordInput
            id="password"
              {...fieldProps('password')}
            autoComplete="new-password"
            placeholder={t('auth.passwordPlaceholder')}
            value={form.password}
            onChange={set('password')}
          />
          <p id="password-hint" className="mt-1.5 text-xs text-mute">{t('auth.registerPasswordHint')}</p>
          {fieldError('password')}
        </div>

        <div>
          <label className="auth-label" htmlFor="password_confirm">{t('auth.confirmPassword')}</label>
          <PasswordInput
            id="password_confirm"
              {...fieldProps('password_confirm')}
            autoComplete="new-password"
            placeholder={t('auth.confirmPlaceholder')}
            value={form.password_confirm}
            onChange={set('password_confirm')}
          />
          {fieldError('password_confirm')}
        </div>

        <button type="submit" disabled={busy} className="auth-submit mt-1">
          {busy && <ActionSpinner />}
          {busy ? t('auth.creating') : t('auth.register')}
        </button>
      </form>

      <OAuthButtons divider={t('auth.signupDivider')} />

      <p className="flex w-full justify-center gap-1.5 border-t border-edge pt-4 text-xs text-sub">
        {t('auth.alreadyRegistered')}
        <Link to="/login" className="font-semibold text-accent hover:underline">{t('auth.signIn')}</Link>
      </p>
    </AuthShell>
  )
}
