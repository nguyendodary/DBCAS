import axios from 'axios'

// Shared API client. Vite proxies /api to http://localhost:8000 (vite.config.js),
// so the SPA talks to the backend same-origin in development.
const api = axios.create({ baseURL: '/api/v1' })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('dbcas_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// An expired or invalid token can only be fixed by logging in again —
// send the user there instead of leaving every page on an error state.
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
