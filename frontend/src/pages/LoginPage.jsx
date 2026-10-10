import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { apiMessage } from '../api'
import AuthShell from '../components/AuthShell'
import PasswordInput from '../components/PasswordInput'
import { inputCls } from '../components/ui'

// UC02 — email + password → JWT; admins land on /admin, learners /dashboard.
export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

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
      setError(apiMessage(err, 'Login failed'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthShell>
      <form onSubmit={onSubmit}>
        <h1 className="mb-1 text-xl font-semibold text-gray-900">Sign in to DBCAS</h1>
        <p className="mb-5 text-sm text-gray-500">Database Competency Assessment</p>

        {error && (
          <p role="alert" className="mb-3 rounded-md bg-red-50 p-2 text-sm text-red-700">
            {error}
          </p>
        )}

        <label htmlFor="email" className="mb-1 block text-sm font-medium text-gray-700">
          Email
        </label>
        <input
          id="email"
          type="email"
          required
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className={`${inputCls} mb-3`}
        />

        <label htmlFor="password" className="mb-1 block text-sm font-medium text-gray-700">
          Password
        </label>
        <PasswordInput
          id="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="mb-4"
        />

        <button
          type="submit"
          disabled={busy}
          className="w-full rounded-md bg-blue-600 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {busy ? 'Signing in…' : 'Sign in'}
        </button>

        <p className="mt-4 text-center text-sm text-gray-500">
          No account?{' '}
          <Link to="/register" className="text-blue-600 hover:underline">
            Register as a learner
          </Link>
        </p>
      </form>
    </AuthShell>
  )
}
