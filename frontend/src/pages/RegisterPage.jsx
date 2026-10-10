import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { apiMessage } from '../api'
import AuthShell from '../components/AuthShell'
import PasswordInput from '../components/PasswordInput'
import { inputCls } from '../components/ui'

// UC01 — learner self-registration (always the Learner role server-side).
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
      <form onSubmit={onSubmit}>
        <h1 className="mb-1 text-xl font-semibold text-gray-900">Create your account</h1>
        <p className="mb-5 text-sm text-gray-500">Learner registration</p>

        {error && (
          <p role="alert" className="mb-3 rounded-md bg-red-50 p-2 text-sm text-red-700">
            {error}
          </p>
        )}

        <label htmlFor="name" className="mb-1 block text-sm font-medium text-gray-700">
          Full name
        </label>
        <input id="name" required value={form.name} onChange={set('name')} className={`${inputCls} mb-3`} />

        <label htmlFor="email" className="mb-1 block text-sm font-medium text-gray-700">
          Email
        </label>
        <input
          id="email"
          type="email"
          required
          autoComplete="email"
          value={form.email}
          onChange={set('email')}
          className={`${inputCls} mb-3`}
        />

        <label htmlFor="password" className="mb-1 block text-sm font-medium text-gray-700">
          Password
        </label>
        <PasswordInput
          id="password"
          autoComplete="new-password"
          value={form.password}
          onChange={set('password')}
          className="mb-3"
        />

        <label htmlFor="password_confirm" className="mb-1 block text-sm font-medium text-gray-700">
          Confirm password
        </label>
        <PasswordInput
          id="password_confirm"
          autoComplete="new-password"
          value={form.password_confirm}
          onChange={set('password_confirm')}
          className="mb-4"
        />

        <button
          type="submit"
          disabled={busy}
          className="w-full rounded-md bg-blue-600 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {busy ? 'Creating…' : 'Register'}
        </button>

        <p className="mt-4 text-center text-sm text-gray-500">
          Already registered?{' '}
          <Link to="/login" className="text-blue-600 hover:underline">
            Sign in
          </Link>
        </p>
      </form>
    </AuthShell>
  )
}
