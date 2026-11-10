import axios from 'axios'
import { i18n, message, resources } from './i18n'

// Shared API client. Vite proxies /api to http://localhost:8000 (vite.config.js),
// so the SPA talks to the backend same-origin in development.
const api = axios.create({ baseURL: '/api/v1', timeout: 60_000 })
const renewal = axios.create({ baseURL: '/api/v1', timeout: 15_000 })
let renewing = null

api.interceptors.request.use(async (config) => {
  config.headers['Accept-Language'] = i18n.language || 'en'
  let token = localStorage.getItem('dbcas_token')
  if (token && config.url !== '/auth/renew') {
    let expires = 0
    let advance = 300000
    try {
      const claims = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')))
      expires = claims.exp * 1000
      if (claims.iat && claims.exp > claims.iat)
        advance = Math.min(advance, (claims.exp - claims.iat) * 200)
    } catch {
      /* server validates malformed tokens */
    }
    const startsAssessment =
      config.method === 'post' && /^\/assessments\/\d+\/sessions$/.test(config.url)
    if (expires && (expires - Date.now() < advance || startsAssessment)) {
      if (!renewing) {
        const original = token
        const rotate = async () => {
          // Another tab may have renewed while this tab waited for the lock.
          if (localStorage.getItem('dbcas_token') !== original) return
          const refresh = localStorage.getItem('dbcas_refresh_token')
          const r = await (refresh
            ? renewal.post('/auth/refresh', { refresh_token: refresh })
            : renewal.post('/auth/renew', null, {
                headers: { Authorization: `Bearer ${original}` },
              }))
          // A logout or another sign-in during renewal takes precedence.
          if (localStorage.getItem('dbcas_token') === original) {
            localStorage.setItem('dbcas_token', r.data.access_token)
            if (r.data.refresh_token)
              localStorage.setItem('dbcas_refresh_token', r.data.refresh_token)
            window.dispatchEvent(new CustomEvent('dbcas:auth-renewed', { detail: r.data.account }))
          }
        }
        renewing = (
          navigator.locks?.request ? navigator.locks.request('dbcas:auth-renew', rotate) : rotate()
        ).finally(() => {
          renewing = null
        })
      }
      try {
        await renewing
      } catch (err) {
        if (err?.response?.status === 401) {
          if (localStorage.getItem('dbcas_token') === token) {
            localStorage.removeItem('dbcas_token')
            localStorage.removeItem('dbcas_refresh_token')
            if (!window.location.pathname.startsWith('/login')) window.location.assign('/login')
            throw err
          }
        }
        // A transient renewal failure leaves the valid token available.
      }
      token = localStorage.getItem('dbcas_token')
    }
  }
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Authentication failures require a new sign-in. Infrastructure failures
// preserve the token and remain visible/retryable in the current page.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (
      error?.response?.status === 401 &&
      // The OAuth callback owns its failure route and localized explanation.
      error.config?.url !== '/auth/oauth/complete' &&
      (!error.config?.headers?.Authorization ||
        error.config.headers.Authorization === `Bearer ${localStorage.getItem('dbcas_token')}`) &&
      !window.location.pathname.startsWith('/login')
    ) {
      localStorage.removeItem('dbcas_token')
      localStorage.removeItem('dbcas_refresh_token')
      window.location.assign('/login')
    }
    return Promise.reject(error)
  },
)

// The API always answers { error: { code, message } } on failure.
export function apiMessage(err, fallback) {
  if (err?.uiMessage) return err.uiMessage
  const code = err?.response?.data?.error?.code
  if (typeof code === 'string' && Object.hasOwn(resources.en.translation.errors, code))
    return message(`errors.${code}`)
  if (!err?.response && (err?.isAxiosError || err?.code === 'ERR_NETWORK'))
    return message('errors.network')
  // Never echo arbitrary provider/proxy/server exception text to the UI.
  return fallback?.translationKey ? fallback : message('errors.unknown')
}

export default api
