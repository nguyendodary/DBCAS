import axios from 'axios'

// Shared API client. Vite proxies /api to http://localhost:8000 (vite.config.js),
// so the SPA talks to the backend same-origin in development.
const api = axios.create({ baseURL: '/api/v1' })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('dbcas_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export default api
