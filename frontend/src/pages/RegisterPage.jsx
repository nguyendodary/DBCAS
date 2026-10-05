import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { apiMessage } from '../api'

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

  const field =
    'mb-3 w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none'

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <form
        onSubmit={onSubmit}
        className="w-full max-w-sm rounded-lg border bg-white p-6 shadow-sm"
      >
        <h1 className="mb-1 text-xl font-semibold text-gray-900">Create your account</h1>
        <p className="mb-5 text-sm text-gray-500">Learner registration</p>

        {error && (
          <p role="alert" className="mb-3 rounded bg-red-50 p-2 text-sm text-red-700">
            {error}
          </p>
        )}

        <label htmlFor="name" className="mb-1 block text-sm font-medium text-gray-700">
          Full name
        </label>
        <input id="name" required value={form.name} onChange={set('name')} className={field} />

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
          className={field}
        />

        <label htmlFor="password" className="mb-1 block text-sm font-medium text-gray-700">
          Password
        </label>
        <input
          id="password"
          type="password"
          required
          autoComplete="new-password"
          value={form.password}
          onChange={set('password')}
          className={field}
        />

        <label htmlFor="password_confirm" className="mb-1 block text-sm font-medium text-gray-700">
          Confirm password
        </label>
        <input
          id="password_confirm"
          type="password"
          required
          autoComplete="new-password"
          value={form.password_confirm}
          onChange={set('password_confirm')}
          className="mb-4 w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        />

        <button
          type="submit"
          disabled={busy}
          className="w-full rounded bg-blue-600 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
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
    </div>
  )
}
