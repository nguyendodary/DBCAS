import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import api from '../api'

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } },
    })),
  },
}))

let location
const reject = api.interceptors.response.use.mock.calls[0][1]

beforeEach(() => {
  localStorage.clear()
  location = { pathname: '/auth/callback', assign: vi.fn() }
  vi.stubGlobal('window', { location })
})

afterEach(() => {
  vi.unstubAllGlobals()
  localStorage.clear()
})

it('lets the OAuth callback retain its failure explanation and existing credentials', async () => {
  localStorage.setItem('dbcas_token', 'existing-token')
  localStorage.setItem('dbcas_refresh_token', 'existing-refresh')
  const error = {
    response: { status: 401 },
    config: { url: '/auth/oauth/complete', headers: {} },
  }
  await expect(reject(error)).rejects.toBe(error)
  expect(location.assign).not.toHaveBeenCalled()
  expect(localStorage.getItem('dbcas_token')).toBe('existing-token')
  expect(localStorage.getItem('dbcas_refresh_token')).toBe('existing-refresh')
})

it('still clears expired credentials and redirects a protected request', async () => {
  location.pathname = '/dashboard'
  localStorage.setItem('dbcas_token', 'expired-token')
  localStorage.setItem('dbcas_refresh_token', 'expired-refresh')
  const error = {
    response: { status: 401 },
    config: { url: '/sessions', headers: { Authorization: 'Bearer expired-token' } },
  }
  await expect(reject(error)).rejects.toBe(error)
  expect(location.assign).toHaveBeenCalledExactlyOnceWith('/login')
  expect(localStorage.getItem('dbcas_token')).toBeNull()
  expect(localStorage.getItem('dbcas_refresh_token')).toBeNull()
})

it('does not clear a new sign-in when an older request returns unauthorized', async () => {
  location.pathname = '/dashboard'
  localStorage.setItem('dbcas_token', 'new-token')
  const error = {
    response: { status: 401 },
    config: { url: '/sessions', headers: { Authorization: 'Bearer old-token' } },
  }
  await expect(reject(error)).rejects.toBe(error)
  expect(location.assign).not.toHaveBeenCalled()
  expect(localStorage.getItem('dbcas_token')).toBe('new-token')
})
