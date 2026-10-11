import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { apiMessage } from '../api'
import AuthShell from '../components/AuthShell'
import OAuthButtons from '../components/OAuthButtons'
import PasswordInput from '../components/PasswordInput'
import { ActionSpinner } from '../components/States'
import { btnPrimary, Field, inputCls } from '../components/ui'

// UC01 — learner self-registration (always the Learner role server-side;
// this screen cannot create administrators).
export default function RegisterPage() {
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
      setError(apiMessage(err, 'Registration failed'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthShell>
      <form onSubmit={onSubmit} aria-busy={busy}>
        <p className="mb-2 text-xs font-semibold uppercase tracking-[.16em] text-cyan-300">Learner access</p>
        <h1 className="text-2xl font-semibold tracking-tight text-ink">Create your account</h1>
        <p className="mb-7 mt-2 text-sm text-mute">Start assessing your database skills.</p>

        {error && (
          <p
            role="alert"
            className="mb-3 rounded-md border border-rose-500/30 bg-rose-500/10 p-2.5 text-sm text-rose-300"
          >
            {error}
          </p>
        )}

        <Field label="Full name" htmlFor="name" className="mb-4">
          <input
            id="name"
            required
            autoComplete="name"
            value={form.name}
            onChange={set('name')}
            className={inputCls}
          />
        </Field>

        <Field label="Email" htmlFor="email" className="mb-4">
          <input
            id="email"
            type="email"
            required
            autoComplete="email"
            value={form.email}
            onChange={set('email')}
            className={inputCls}
          />
        </Field>

        <Field label="Password" htmlFor="password" className="mb-4">
          <PasswordInput
            id="password"
            autoComplete="new-password"
            value={form.password}
            onChange={set('password')}
          />
        </Field>

        <Field label="Confirm password" htmlFor="password_confirm" className="mb-6">
          <PasswordInput
            id="password_confirm"
            autoComplete="new-password"
            value={form.password_confirm}
            onChange={set('password_confirm')}
          />
        </Field>

        <button type="submit" disabled={busy} className={`w-full ${btnPrimary}`}>
          {busy && <ActionSpinner />}
          {busy ? 'Creating…' : 'Register'}
        </button>
      </form>

      <OAuthButtons divider="or sign up with" />

      <p className="mt-5 text-center text-sm text-mute">
        Already registered?{' '}
        <Link to="/login" className="text-cyan-300 hover:underline">
          Sign in
        </Link>
      </p>
    </AuthShell>
  )
}
