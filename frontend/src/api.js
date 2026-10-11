import axios from 'axios'

// Shared API client. Vite proxies /api to http://localhost:8000 (vite.config.js),
// so the SPA talks to the backend same-origin in development.
const api = axios.create({ baseURL: '/api/v1' })
const renewal = axios.create({ baseURL: '/api/v1' })
let renewing = null

api.interceptors.request.use(async (config) => {
  let token = localStorage.getItem('dbcas_token')
  if (token && config.url !== '/auth/renew') {
    let expires = 0
    try { expires = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/'))).exp * 1000 } catch { /* server validates malformed tokens */ }
    const startsAssessment = config.method === 'post' && /^\/assessments\/\d+\/sessions$/.test(config.url)
    if (expires && (expires - Date.now() < 300_000 || startsAssessment)) {
      if (!renewing) {
        const original = token
        renewing = renewal.post('/auth/renew', null, { headers: { Authorization: `Bearer ${token}` } })
          .then((r) => {
            // A logout or another sign-in during renewal takes precedence.
            if (localStorage.getItem('dbcas_token') === original) {
              localStorage.setItem('dbcas_token', r.data.access_token)
              window.dispatchEvent(new CustomEvent('dbcas:auth-renewed', { detail: r.data.account }))
            }
          }).finally(() => { renewing = null })
      }
      try { await renewing } catch (err) {
        if (err?.response?.status === 401) {
          localStorage.removeItem('dbcas_token')
          if (!window.location.pathname.startsWith('/login')) window.location.assign('/login')
          throw err
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
      !window.location.pathname.startsWith('/login')
    ) {
      localStorage.removeItem('dbcas_token')
      window.location.assign('/login')
    }
    return Promise.reject(error)
  }
)

// The API always answers { error: { code, message } } on failure.
export function apiMessage(err, fallback = 'Something went wrong') {
  return err?.response?.data?.error?.message || err?.message || fallback
}

export default api
