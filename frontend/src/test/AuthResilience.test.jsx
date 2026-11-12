import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthProvider, useAuth } from '../auth'
import api from '../api'

vi.mock('../api', () => ({ default: { get: vi.fn(), post: vi.fn() } }))

function Probe() {
  const auth = useAuth()
  return (
    <>
      <p>{auth.ready ? 'ready' : 'checking'}</p>
      <p>{auth.account?.email || 'no account'}</p>
      {auth.error && (
        <div role="alert">
          {auth.error}
          <button onClick={auth.retry}>Retry</button>
        </div>
      )}
      <button onClick={() => auth.login('learner@test.dev', 'Secret123!')}>Fixture login</button>
      <button onClick={auth.logout}>Fixture logout</button>
    </>
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
})
afterEach(() => {
  localStorage.clear()
})

describe('Session validation resilience', () => {
  it('stores the refresh session on login and revokes it through the logout API', async () => {
    api.post
      .mockResolvedValueOnce({
        data: {
          access_token: 'access',
          refresh_token: 'refresh',
          account: { email: 'learner@test.dev', roles: ['Learner'] },
        },
      })
      .mockResolvedValueOnce({ status: 204 })
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    )
    await userEvent.click(screen.getByRole('button', { name: 'Fixture login' }))
    expect(localStorage.getItem('dbcas_refresh_token')).toBe('refresh')
    await userEvent.click(screen.getByRole('button', { name: 'Fixture logout' }))
    expect(api.post).toHaveBeenLastCalledWith('/auth/logout', { refresh_token: 'refresh' })
    expect(localStorage.getItem('dbcas_token')).toBeNull()
    expect(localStorage.getItem('dbcas_refresh_token')).toBeNull()
  })
  it.each([undefined, 500, 503])(
    'preserves the token on a temporary failure (%s) and permits retry',
    async (status) => {
      localStorage.setItem('dbcas_token', 'existing-token')
      api.get
        .mockRejectedValueOnce({ response: status ? { status } : undefined })
        .mockResolvedValueOnce({ data: { email: 'learner@test.dev', roles: ['Learner'] } })
      render(
        <AuthProvider>
          <Probe />
        </AuthProvider>,
      )
      expect(await screen.findByRole('alert')).toHaveTextContent('Retry')
      expect(localStorage.getItem('dbcas_token')).toBe('existing-token')
      await userEvent.click(screen.getByRole('button', { name: 'Retry' }))
      expect(await screen.findByText('learner@test.dev')).toBeInTheDocument()
      expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    },
  )

  it.each([401, 403])('clears invalid credentials (%s)', async (status) => {
    localStorage.setItem('dbcas_token', 'invalid-token')
    api.get.mockRejectedValueOnce({ response: { status } })
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    )
    await waitFor(() => expect(screen.getByText('ready')).toBeInTheDocument())
    expect(localStorage.getItem('dbcas_token')).toBeNull()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('updates account state after an access renewal', async () => {
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    )
    act(() =>
      window.dispatchEvent(
        new CustomEvent('dbcas:auth-renewed', {
          detail: { email: 'renewed@test.dev', roles: ['Learner'] },
        }),
      ),
    )
    expect(screen.getByText('renewed@test.dev')).toBeInTheDocument()
  })

  it('starts the session check before a short-lived token expires', async () => {
    vi.useFakeTimers()
    const now = Math.floor(Date.now() / 1000)
    localStorage.setItem(
      'dbcas_token',
      `header.${btoa(JSON.stringify({ iat: now, exp: now + 60 }))}.signature`,
    )
    api.get.mockResolvedValue({ data: { email: 'learner@test.dev', roles: ['Learner'] } })
    const { unmount } = render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    )
    try {
      await act(async () => {})
      expect(api.get).toHaveBeenCalledTimes(1)
      await act(async () => {
        vi.advanceTimersByTime(50_000)
      })
      expect(api.get).toHaveBeenCalledTimes(2)
    } finally {
      unmount()
      vi.useRealTimers()
    }
  })
})
