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

afterEach(() => { axios.defaults.adapter = originalAdapter; localStorage.clear() })

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
