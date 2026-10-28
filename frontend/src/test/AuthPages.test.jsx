import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { vi } from 'vitest'
import { AuthProvider } from '../auth'
import ForgotPasswordPage from '../pages/ForgotPasswordPage'
import LoginPage from '../pages/LoginPage'
import OAuthCallbackPage from '../pages/OAuthCallbackPage'
import RegisterPage from '../pages/RegisterPage'
import ResetPasswordPage from '../pages/ResetPasswordPage'
import api from '../api'

vi.mock('../api', () => ({
  default: { get: vi.fn(), post: vi.fn() },
  apiMessage: (e, fb) => e?.response?.data?.error?.message || e?.message || fb,
}))

// Minimal app shell: real AuthProvider (real login/register/completeOAuth
// implementations) over a tiny route table with page markers.
function renderApp(entry = '/login') {
  return render(
    <MemoryRouter initialEntries={[entry]}>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route path="/auth/callback" element={<OAuthCallbackPage />} />
          <Route path="/dashboard" element={<div>learner dashboard</div>} />
          <Route path="/admin" element={<div>admin home</div>} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>
  )
}

const LEARNER = { account_id: 1, name: 'Lia', email: 'lia@x.dev', roles: ['Learner'] }
const ADMIN = { account_id: 2, name: 'Ann', email: 'ann@x.dev', roles: ['Administrator'] }

beforeEach(() => {
  vi.restoreAllMocks()
  api.post.mockReset()
  api.get.mockReset()
  localStorage.clear()
  api.get.mockImplementation((url) => {
    if (url === '/auth/oauth/providers')
      return Promise.resolve({
        data: {
          providers: [
            { name: 'google', configured: true },
            { name: 'github', configured: true },
          ],
        },
      })
    return Promise.reject(new Error('unexpected GET ' + url))
  })
})

describe('LoginPage', () => {
  it('signs in with email/password, stores the token, and lands a learner on /dashboard', async () => {
    api.post.mockResolvedValueOnce({
      data: { access_token: 'jwt-1', account: LEARNER },
    })
    renderApp('/login')
    const user = userEvent.setup()

    await user.type(screen.getByLabelText(/email/i), 'lia@x.dev')
    await user.type(screen.getByLabelText(/password/i, { selector: 'input' }), 's3cret!')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() =>
      expect(screen.getByText('learner dashboard')).toBeInTheDocument()
    )
    expect(api.post).toHaveBeenCalledWith('/auth/login', {
      email: 'lia@x.dev',
      password: 's3cret!',
    })
    expect(localStorage.getItem('dbcas_token')).toBe('jwt-1')
  })

  it('lands an administrator on /admin', async () => {
    api.post.mockResolvedValueOnce({
      data: { access_token: 'jwt-2', account: ADMIN },
    })
    renderApp('/login')
    const user = userEvent.setup()

    await user.type(screen.getByLabelText(/email/i), 'ann@x.dev')
    await user.type(screen.getByLabelText(/password/i, { selector: 'input' }), 's3cret!')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => expect(screen.getByText('admin home')).toBeInTheDocument())
  })

  it('shows the API error on a bad login and stays on the page', async () => {
    api.post.mockRejectedValueOnce({
      response: { data: { error: { message: 'Invalid credentials' } } },
    })
    renderApp('/login')
    const user = userEvent.setup()

    await user.type(screen.getByLabelText(/email/i), 'lia@x.dev')
    await user.type(screen.getByLabelText(/password/i, { selector: 'input' }), 'wrong')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    expect(await screen.findByText('Invalid credentials')).toBeInTheDocument()
    expect(screen.queryByText('learner dashboard')).not.toBeInTheDocument()
  })

  it('offers the password-recovery link and navigates to the request form', async () => {
    renderApp('/login')
    const user = userEvent.setup()
    const link = await screen.findByRole('link', { name: /forgot password/i })
    expect(link).toHaveAttribute('href', '/forgot-password')

    await user.click(link)
    expect(
      await screen.findByRole('heading', { name: /reset your password/i })
    ).toBeInTheDocument()
  })

  it('renders real Google and GitHub provider links to the backend start routes', async () => {
    renderApp('/login')
    expect(await screen.findByRole('link', { name: /continue with google/i }))
      .toHaveAttribute('href', '/api/v1/auth/oauth/google/start')
    expect(screen.getByRole('link', { name: /continue with github/i }))
      .toHaveAttribute('href', '/api/v1/auth/oauth/github/start')
  })

  it('disables a provider button when the server reports it unconfigured', async () => {
    api.get.mockImplementation((url) => {
      if (url === '/auth/oauth/providers')
        return Promise.resolve({
          data: {
            providers: [
              { name: 'google', configured: false },
              { name: 'github', configured: true },
            ],
          },
        })
      return Promise.reject(new Error('unexpected GET ' + url))
    })
    renderApp('/login')

    const google = await screen.findByRole('link', { name: /continue with google/i })
    await waitFor(() => expect(google).not.toHaveAttribute('href'))
    expect(google).toHaveAttribute('aria-disabled', 'true')
    expect(screen.getByRole('link', { name: /continue with github/i }))
      .toHaveAttribute('href', '/api/v1/auth/oauth/github/start')
    expect(screen.queryByText(/Unavailable sign-in methods are disabled/i)).not.toBeInTheDocument()
  })

  it('surfaces a friendly message when the provider redirects back with oauth_error', async () => {
    renderApp('/login?oauth_error=not_configured')
    await screen.findByRole('link', { name: /continue with google/i })
    expect(
      screen.getByText('That sign-in method is not configured on this server.')
    ).toBeInTheDocument()
  })
})

describe('RegisterPage', () => {
  it('registers a learner then routes to /login', async () => {
    api.post.mockResolvedValueOnce({ data: { account_id: 9 } })
    renderApp('/register')
    const user = userEvent.setup()

    await user.type(screen.getByLabelText(/full name/i), 'New Learner')
    await user.type(screen.getByLabelText(/email/i), 'new@x.dev')
    await user.type(screen.getByLabelText(/^password$/i, { selector: 'input' }), 'S3cret-ok')
    await user.type(screen.getByLabelText(/confirm password/i, { selector: 'input' }), 'S3cret-ok')
    await user.click(screen.getByRole('button', { name: /register/i }))

    await waitFor(() =>
      expect(screen.getByRole('heading', { name: /sign in to dbcas/i }))
        .toBeInTheDocument()
    )
    expect(api.post).toHaveBeenCalledWith('/auth/register', {
      name: 'New Learner',
      email: 'new@x.dev',
      password: 'S3cret-ok',
      password_confirm: 'S3cret-ok',
    })
  })

  it('shows the API error when registration fails', async () => {
    api.post.mockRejectedValueOnce({
      response: { data: { error: { message: 'Email already registered' } } },
    })
    renderApp('/register')
    const user = userEvent.setup()

    await user.type(screen.getByLabelText(/full name/i), 'New Learner')
    await user.type(screen.getByLabelText(/email/i), 'dupe@x.dev')
    await user.type(screen.getByLabelText(/^password$/i, { selector: 'input' }), 'S3cret-ok')
    await user.type(screen.getByLabelText(/confirm password/i, { selector: 'input' }), 'S3cret-ok')
    await user.click(screen.getByRole('button', { name: /register/i }))

    expect(await screen.findByText('Email already registered')).toBeInTheDocument()
  })

  it('offers the same real OAuth providers as signup', async () => {
    renderApp('/register')
    expect(await screen.findByRole('link', { name: /continue with google/i }))
      .toHaveAttribute('href', '/api/v1/auth/oauth/google/start')
  })
})

describe('ForgotPasswordPage', () => {
  it('requests a reset link and shows a neutral confirmation for any address', async () => {
    api.post.mockResolvedValueOnce({ data: { status: 'accepted' } })
    renderApp('/forgot-password')
    const user = userEvent.setup()

    await user.type(screen.getByLabelText(/^email$/i), 'nobody@x.dev')
    await user.click(screen.getByRole('button', { name: /send reset link/i }))

    expect(await screen.findByText('Check your email')).toBeInTheDocument()
    expect(
      screen.getByText(/if an account exists for that email/i)
    ).toBeInTheDocument()
    expect(screen.queryByLabelText(/^email$/i)).not.toBeInTheDocument()
    expect(api.post).toHaveBeenCalledWith('/auth/password-reset/request', {
      email: 'nobody@x.dev',
    })
  })

  it('shows the API error and keeps the form when the request fails', async () => {
    api.post.mockRejectedValueOnce({
      response: {
        data: {
          error: {
            code: 'password_reset_unavailable',
            message: 'Password reset email is not available on this server.',
          },
        },
      },
    })
    renderApp('/forgot-password')
    const user = userEvent.setup()

    await user.type(screen.getByLabelText(/^email$/i), 'lia@x.dev')
    await user.click(screen.getByRole('button', { name: /send reset link/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Password reset email is not available on this server.'
    )
    expect(screen.getByLabelText(/^email$/i)).toHaveValue('lia@x.dev')
    expect(screen.queryByText('Check your email')).not.toBeInTheDocument()
  })
})

describe('ResetPasswordPage', () => {
  const TOKEN = 'A'.repeat(43)

  it('submits the token with the new password and confirms success', async () => {
    api.post.mockResolvedValueOnce({ data: { status: 'reset' } })
    renderApp(`/reset-password?token=${TOKEN}`)
    const user = userEvent.setup()

    await user.type(screen.getByLabelText(/new password/i, { selector: 'input' }), 'S3cret-ok')
    await user.type(screen.getByLabelText(/confirm password/i, { selector: 'input' }), 'S3cret-ok')
    await user.click(screen.getByRole('button', { name: /set new password/i }))

    expect(await screen.findByText('Password updated')).toBeInTheDocument()
    expect(api.post).toHaveBeenCalledWith('/auth/password-reset/confirm', {
      token: TOKEN,
      password: 'S3cret-ok',
      password_confirm: 'S3cret-ok',
    })
    expect(screen.getByRole('link', { name: 'Back to sign in' })).toHaveAttribute(
      'href',
      '/login'
    )
  })

  it('rejects a mismatched confirmation without calling the API', async () => {
    renderApp(`/reset-password?token=${TOKEN}`)
    const user = userEvent.setup()

    await user.type(screen.getByLabelText(/new password/i, { selector: 'input' }), 'S3cret-ok')
    await user.type(screen.getByLabelText(/confirm password/i, { selector: 'input' }), 'S3cret-no')
    await user.click(screen.getByRole('button', { name: /set new password/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Passwords do not match.')
    expect(api.post).not.toHaveBeenCalled()
  })

  it('rejects a password shorter than the minimum without calling the API', async () => {
    renderApp(`/reset-password?token=${TOKEN}`)
    const user = userEvent.setup()

    await user.type(screen.getByLabelText(/new password/i, { selector: 'input' }), 'short')
    await user.type(screen.getByLabelText(/confirm password/i, { selector: 'input' }), 'short')
    await user.click(screen.getByRole('button', { name: /set new password/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Password must be at least 8 characters.'
    )
    expect(api.post).not.toHaveBeenCalled()
  })

  it('renders the invalid-link state when the URL has no token', async () => {
    renderApp('/reset-password')

    expect(
      screen.getByRole('heading', { name: 'This link is not valid' })
    ).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Request a new link' })).toHaveAttribute(
      'href',
      '/forgot-password'
    )
    expect(screen.queryByLabelText(/new password/i, { selector: 'input' })).not.toBeInTheDocument()
  })

  it('renders the invalid-link state when the server rejects the token', async () => {
    api.post.mockRejectedValueOnce({
      response: {
        data: {
          error: { code: 'invalid_reset_token', message: 'This reset link is invalid.' },
        },
      },
    })
    renderApp(`/reset-password?token=${TOKEN}`)
    const user = userEvent.setup()

    await user.type(screen.getByLabelText(/new password/i, { selector: 'input' }), 'S3cret-ok')
    await user.type(screen.getByLabelText(/confirm password/i, { selector: 'input' }), 'S3cret-ok')
    await user.click(screen.getByRole('button', { name: /set new password/i }))

    expect(
      await screen.findByRole('heading', { name: 'This link is not valid' })
    ).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Request a new link' })).toBeInTheDocument()
  })

  it('keeps the form and shows the API error for other failures', async () => {
    api.post.mockRejectedValueOnce({
      response: {
        data: {
          error: {
            code: 'password_reset_rate_limited',
            message: 'Too many password reset attempts. Please wait and try again.',
          },
        },
      },
    })
    renderApp(`/reset-password?token=${TOKEN}`)
    const user = userEvent.setup()

    await user.type(screen.getByLabelText(/new password/i, { selector: 'input' }), 'S3cret-ok')
    await user.type(screen.getByLabelText(/confirm password/i, { selector: 'input' }), 'S3cret-ok')
    await user.click(screen.getByRole('button', { name: /set new password/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Too many password reset attempts. Please wait and try again.'
    )
    expect(screen.getByRole('button', { name: /set new password/i })).toBeInTheDocument()
  })

  it('exposes accessible new-password fields with show/hide toggles', async () => {
    renderApp(`/reset-password?token=${TOKEN}`)

    const password = screen.getByLabelText(/new password/i, { selector: 'input' })
    expect(password).toHaveAttribute('type', 'password')
    expect(password).toHaveAttribute('autocomplete', 'new-password')
    expect(
      screen.getAllByRole('button', { name: /show password/i })
    ).toHaveLength(2)
  })
})

describe('OAuthCallbackPage', () => {
  it('exchanges the handoff cookie for a JWT and lands the learner on /dashboard', async () => {
    api.post.mockResolvedValueOnce({
      data: { access_token: 'jwt-oauth', account: LEARNER },
    })
    renderApp('/auth/callback')

    await waitFor(() =>
      expect(screen.getByText('learner dashboard')).toBeInTheDocument()
    )
    expect(api.post).toHaveBeenCalledWith('/auth/oauth/complete', null, {
      withCredentials: true,
    })
    expect(localStorage.getItem('dbcas_token')).toBe('jwt-oauth')
  })

  it('lands an administrator completing OAuth on /admin', async () => {
    api.post.mockResolvedValueOnce({
      data: { access_token: 'jwt-oauth', account: ADMIN },
    })
    renderApp('/auth/callback')
    await waitFor(() => expect(screen.getByText('admin home')).toBeInTheDocument())
  })

  it('sends the user back to /login with an error when the handoff fails', async () => {
    api.post.mockRejectedValueOnce({ response: { status: 401 } })
    renderApp('/auth/callback')

    await waitFor(() =>
      expect(
        screen.getByText('Sign-in could not be finished. Please try again.')
      ).toBeInTheDocument()
    )
    expect(localStorage.getItem('dbcas_token')).toBeNull()
  })
})
