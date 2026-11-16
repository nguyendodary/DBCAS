import { t, useLocale, resolveMessage } from '../i18n'
import { useEffect, useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import api, { apiMessage } from '../api'
import AuthShell from '../components/AuthShell'
import { ActionSpinner } from '../components/States'

// Mirrors PASSWORD_RESET_OTP_RESEND_COOLDOWN_SECONDS; the server enforces it.
const RESEND_SECONDS = 60
const OTP_LENGTH = 6

// Step 2 of recovery: exchange the emailed code for a short-lived reset
// token, which travels to the next page in router state (never in the URL).
// The server burns a code after too many wrong guesses; that answer (429)
// sends the user back to sign-in to start over.
export default function VerifyOtpPage() {
  useLocale()
  const navigate = useNavigate()
  const email = useLocation().state?.email
  const [otp, setOtp] = useState('')
  const [busy, setBusy] = useState(false)
  const [resending, setResending] = useState(false)
  const [error, setError] = useState('')
  const [resent, setResent] = useState(false)
  const [cooldown, setCooldown] = useState(RESEND_SECONDS)

  useEffect(() => {
    if (cooldown <= 0) return undefined
    const timer = setTimeout(() => setCooldown((s) => s - 1), 1000)
    return () => clearTimeout(timer)
  }, [cooldown])

  // Reloading drops router state; without an address there is nothing to verify.
  if (!email) return <Navigate to="/forgot-password" replace />

  function startOver(err) {
    if (err?.response?.data?.error?.code !== 'password_reset_rate_limited') return false
    navigate('/login', { replace: true, state: { notice: 'auth.otpTooManyAttempts' } })
    return true
  }

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    setResent(false)
    setBusy(true)
    try {
      const { data } = await api.post('/auth/password-reset/verify', { email, otp })
      navigate('/reset-password', { replace: true, state: { token: data.reset_token } })
    } catch (err) {
      if (!startOver(err)) {
        setError(apiMessage(err))
        setOtp('')
        setBusy(false)
      }
    }
  }

  async function onResend() {
    setError('')
    setResent(false)
    setResending(true)
    try {
      await api.post('/auth/password-reset/request', { email })
      setResent(true)
      setOtp('')
      setCooldown(RESEND_SECONDS)
    } catch (err) {
      setError(apiMessage(err))
    } finally {
      setResending(false)
    }
  }

  return (
    <AuthShell title={t('auth.otpTitle')} subtitle={t('auth.otpSubtitle', { email })}>
      <form onSubmit={onSubmit} aria-busy={busy} className="flex w-full flex-col gap-3.5">
        {resent && (
          <p
            role="status"
            className="rounded-md border border-emerald-500/30 bg-emerald-500/10 p-2.5 text-sm text-emerald-200"
          >
            {t('auth.otpResent')}
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
          <label className="auth-label" htmlFor="otp">
            {t('auth.otpLabel')}
          </label>
          <div className="auth-field">
            <input
              id="otp"
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              autoComplete="one-time-code"
              maxLength={OTP_LENGTH}
              required
              placeholder={t('auth.otpPlaceholder')}
              className="text-center tracking-[0.5em]"
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, OTP_LENGTH))}
            />
          </div>
          <p className="mt-1 text-xs text-sub">{t('auth.otpHint')}</p>
        </div>

        <button
          type="submit"
          disabled={busy || otp.length !== OTP_LENGTH}
          className="auth-submit mt-1"
        >
          {busy && <ActionSpinner />}
          {busy ? t('auth.verifyingOtp') : t('auth.verifyOtp')}
        </button>

        <button
          type="button"
          onClick={onResend}
          disabled={cooldown > 0 || resending || busy}
          className="text-center text-sm font-semibold text-accent hover:underline disabled:cursor-not-allowed disabled:opacity-60 disabled:no-underline"
        >
          {cooldown > 0 ? t('auth.resendOtpIn', { seconds: cooldown }) : t('auth.resendOtp')}
        </button>

        {import.meta.env.VITE_LOCAL_MAILBOX_URL && (
          <a
            className="text-center text-sm font-semibold text-cyan-300 underline"
            href={import.meta.env.VITE_LOCAL_MAILBOX_URL}
            target="_blank"
            rel="noreferrer"
          >
            {t('local.mailbox')}
          </a>
        )}

        <p className="flex w-full justify-center gap-3 border-t border-edge pt-4 text-xs text-sub">
          <Link to="/forgot-password" className="font-semibold text-accent hover:underline">
            {t('auth.changeEmail')}
          </Link>
          <Link to="/login" className="font-semibold text-accent hover:underline">
            {t('auth.backToSignIn')}
          </Link>
        </p>
      </form>
    </AuthShell>
  )
}
