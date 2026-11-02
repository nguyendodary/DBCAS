import axios from 'axios'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'

const originalAdapter = axios.defaults.adapter
const token = (expires) => `header.${btoa(JSON.stringify({ exp: expires }))}.signature`
let api
let calls
let nextToken

beforeEach(async () => {
  vi.resetModules()
  localStorage.clear()
  calls = []
  nextToken = token(Date.now() / 1000 + 3600)
  axios.defaults.adapter = async (config) => {
    calls.push(config)
    return { data: config.url === '/auth/renew' ? { access_token: nextToken, account: { roles: ['Learner'] } } : { ok: true }, status: 200, statusText: 'OK', headers: {}, config }
  }
  api = (await import('../api')).default
})

afterEach(() => { axios.defaults.adapter = originalAdapter; localStorage.clear(); vi.unstubAllGlobals() })

it('renews once for simultaneous requests near expiry and sends the new token', async () => {
  localStorage.setItem('dbcas_token', token(Date.now() / 1000 + 100))
  await Promise.all([api.get('/sessions/1'), api.get('/sessions/2')])
  expect(calls.filter((r) => r.url === '/auth/renew')).toHaveLength(1)
  expect(calls.filter((r) => r.url !== '/auth/renew').every((r) => r.headers.Authorization === `Bearer ${nextToken}`)).toBe(true)
})

it('renews before starting an assessment even with a longer remaining token lifetime', async () => {
  localStorage.setItem('dbcas_token', token(Date.now() / 1000 + 1800))
  await api.post('/assessments/12/sessions')
  expect(calls.map((r) => r.url)).toEqual(['/auth/renew', '/assessments/12/sessions'])
})

it('keeps a valid token available when renewal encounters an infrastructure failure', async () => {
  const oldToken = token(Date.now() / 1000 + 100)
  localStorage.setItem('dbcas_token', oldToken)
  const adapter = axios.defaults.adapter
  // Both clients inherit defaults at construction, so reload with this adapter.
  axios.defaults.adapter = (config) => config.url === '/auth/renew' ? Promise.reject({ response: { status: 503 } }) : adapter(config)
  vi.resetModules()
  api = (await import('../api')).default
  await api.get('/sessions/1')
  expect(localStorage.getItem('dbcas_token')).toBe(oldToken)
  expect(calls[0].headers.Authorization).toBe(`Bearer ${oldToken}`)
})

it('does not restore a token after logout during an in-flight renewal', async () => {
  let resolve
  axios.defaults.adapter = (config) => config.url === '/auth/renew'
    ? new Promise((done) => { resolve = () => done({ data: { access_token: nextToken, account: {} }, status: 200, headers: {}, config }) })
    : Promise.resolve({ data: {}, status: 200, headers: {}, config })
  vi.resetModules()
  api = (await import('../api')).default
  localStorage.setItem('dbcas_token', token(Date.now() / 1000 + 100))
  const request = api.get('/sessions/1')
  await vi.waitFor(() => expect(resolve).toBeTypeOf('function'))
  localStorage.removeItem('dbcas_token')
  resolve()
  await request
  expect(localStorage.getItem('dbcas_token')).toBeNull()
})

it('rotates a stored refresh token once for concurrent requests', async () => {
  axios.defaults.adapter = async config => {
    calls.push(config)
    return { data: config.url === '/auth/refresh' ? { access_token: nextToken, refresh_token: 'rotated-refresh', account: { roles: ['Learner'] } } : {},
      status: 200, headers: {}, config }
  }
  vi.resetModules()
  api = (await import('../api')).default
  localStorage.setItem('dbcas_token', token(Date.now() / 1000 + 100))
  localStorage.setItem('dbcas_refresh_token', 'original-refresh')
  await Promise.all([api.get('/sessions/1'), api.get('/sessions/2')])
  expect(calls.filter(request => request.url === '/auth/refresh')).toHaveLength(1)
  expect(JSON.parse(calls[0].data)).toEqual({ refresh_token: 'original-refresh' })
  expect(calls.some(request => request.url === '/auth/renew')).toBe(false)
  expect(localStorage.getItem('dbcas_refresh_token')).toBe('rotated-refresh')
  expect(calls.slice(1).every(request => request.headers.Authorization === `Bearer ${nextToken}`)).toBe(true)
})

it('does not restore either token after logout during refresh rotation', async () => {
  let complete
  axios.defaults.adapter = config => config.url === '/auth/refresh'
    ? new Promise(resolve => { complete = () => resolve({ data: { access_token: nextToken, refresh_token: 'rotated-refresh', account: {} }, status: 200, headers: {}, config }) })
    : Promise.resolve({ data: {}, status: 200, headers: {}, config })
  vi.resetModules()
  api = (await import('../api')).default
  localStorage.setItem('dbcas_token', token(Date.now() / 1000 + 100))
  localStorage.setItem('dbcas_refresh_token', 'original-refresh')
  const request = api.get('/sessions/1')
  await vi.waitFor(() => expect(complete).toBeTypeOf('function'))
  localStorage.removeItem('dbcas_token')
  localStorage.removeItem('dbcas_refresh_token')
  complete()
  await request
  expect(localStorage.getItem('dbcas_token')).toBeNull()
  expect(localStorage.getItem('dbcas_refresh_token')).toBeNull()
})

it('uses a renewal from another tab that completed while waiting for the browser lock', async () => {
  const original = token(Date.now() / 1000 + 100)
  localStorage.setItem('dbcas_token', original)
  localStorage.setItem('dbcas_refresh_token', 'original-refresh')
  const request = vi.fn(async (_name, action) => {
    localStorage.setItem('dbcas_token', nextToken)
    localStorage.setItem('dbcas_refresh_token', 'other-tab-refresh')
    return action()
  })
  vi.stubGlobal('navigator', { locks: { request } })
  await api.get('/sessions/1')
  expect(request).toHaveBeenCalledOnce()
  expect(calls.map(call => call.url)).toEqual(['/sessions/1'])
  expect(calls[0].headers.Authorization).toBe(`Bearer ${nextToken}`)
  expect(localStorage.getItem('dbcas_refresh_token')).toBe('other-tab-refresh')
})

it('does not continuously renew a freshly issued short-lived token', async () => {
  const now = Math.floor(Date.now() / 1000)
  const short = `header.${btoa(JSON.stringify({ exp: now + 60, iat: now }))}.signature`
  localStorage.setItem('dbcas_token', short)
  await api.get('/sessions/1')
  expect(calls.map(call => call.url)).toEqual(['/sessions/1'])
  expect(calls[0].headers.Authorization).toBe(`Bearer ${short}`)
})

it('does not clear a new login after a late unauthorized response from an older session', async () => {
  const original = token(Date.now() / 1000 + 1800)
  localStorage.setItem('dbcas_token', original)
  axios.defaults.adapter = async config => {
    localStorage.setItem('dbcas_token', nextToken)
    localStorage.setItem('dbcas_refresh_token', 'new-login-refresh')
    throw { response: { status: 401 }, config }
  }
  vi.resetModules()
  api = (await import('../api')).default
  await expect(api.get('/sessions/1')).rejects.toMatchObject({ response: { status: 401 } })
  expect(localStorage.getItem('dbcas_token')).toBe(nextToken)
  expect(localStorage.getItem('dbcas_refresh_token')).toBe('new-login-refresh')
})
