import { useState } from 'react'
import { Link } from 'react-router-dom'
import { t, useLocale } from '../i18n'
import AuthShell from '../components/AuthShell'
import { Icon } from '../components/ui'

export default function ForgotPasswordPage() {
  useLocale()
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)
  return <AuthShell className="auth-refined" headingClassName="auth-login-heading" title={t('auth.recoveryTitle')} subtitle={t('auth.recoverySubtitle')}>
    <form className="flex flex-col gap-4" onSubmit={event => { event.preventDefault(); setSubmitted(true) }}>
      <div>
        <label className="auth-label" htmlFor="recovery-email">{t('auth.emailLabel')}</label>
        <div className="auth-field">
          <Icon name="mail" className="auth-field-icon" />
          <input id="recovery-email" type="email" required autoComplete="email" placeholder={t('auth.emailPlaceholder')} value={email} onChange={event => { setEmail(event.target.value); setSubmitted(false) }} />
        </div>
      </div>
      {submitted && <p role="status" className="auth-recovery-status">{t('auth.recoveryUnavailable')}</p>}
      <button type="submit" className="auth-submit">{t('auth.recoveryContinue')}<Icon name="arrowRight" className="h-4 w-4" /></button>
    </form>
    <Link className="auth-return-link" to="/login"><Icon name="arrowLeft" className="h-4 w-4" />{t('auth.recoveryBack')}</Link>
  </AuthShell>
}
