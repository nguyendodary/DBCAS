import { message, resolveMessage, useLocale } from './i18n'
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import api from './api'

const TOKEN_KEY = 'dbcas_token'
const REFRESH_KEY = 'dbcas_refresh_token'
const AuthContext = createContext(null)

function rememberTokens(data) {
  localStorage.setItem(TOKEN_KEY, data.access_token)
  if (data.refresh_token) localStorage.setItem(REFRESH_KEY, data.refresh_token)
  else localStorage.removeItem(REFRESH_KEY)
}

// The API rotates refresh sessions; the interceptor attaches access tokens.
export function AuthProvider({ children }) {
  useLocale()
  const [account, setAccount] = useState(null)
  const [ready, setReady] = useState(false)
  const [error, setError] = useState(null)

  const retry = useCallback(async () => {
    setReady(false)
    setError(null)
    if (!localStorage.getItem(TOKEN_KEY)) {
      setReady(true)
      return
    }
    try {
      const r = await api.get('/auth/me')
      setAccount(r.data)
    } catch (err) {
      if ([401, 403].includes(err?.response?.status)) {
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(REFRESH_KEY)
        setAccount(null)
      } else {
        setError(message('auth.sessionUnavailable'))
      }
    } finally {
      setReady(true)
    }
  }, [])

  useEffect(() => { retry() }, [retry])

  useEffect(() => {
    const renewed = (event) => setAccount(event.detail)
    window.addEventListener('dbcas:auth-renewed', renewed)
    // Any normal request may renew the token. The periodic check also keeps
    // a focused assessment alive while the learner is writing a long answer.
    const timer = setInterval(() => {
      if (localStorage.getItem(TOKEN_KEY)) api.get('/auth/me').catch(() => {})
    }, 60_000)
    return () => {
      clearInterval(timer)
      window.removeEventListener('dbcas:auth-renewed', renewed)
    }
  }, [])

  const displayError = resolveMessage(error)
  const value = useMemo(
    () => ({
      account,
      ready,
      error: displayError,
      retry,
      hasRole: (role) => Boolean(account?.roles?.includes(role)),
      async login(email, password) {
        const r = await api.post('/auth/login', { email, password })
        rememberTokens(r.data)
        setAccount(r.data.account)
        return r.data.account
      },
      async register(name, email, password, password_confirm) {
        await api.post('/auth/register', {
          name,
          email,
          password,
          password_confirm,
        })
      },
      // Social sign-in lands on /auth/callback with a one-time HttpOnly
      // handoff cookie; this exchanges it for the normal Bearer JWT.
      async completeOAuth() {
        const r = await api.post('/auth/oauth/complete', null, {
          withCredentials: true,
        })
        rememberTokens(r.data)
        setAccount(r.data.account)
        return r.data.account
      },
      logout() {
        const refresh = localStorage.getItem(REFRESH_KEY)
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(REFRESH_KEY)
        setAccount(null)
        setError(null)
        if (refresh) return api.post('/auth/logout', { refresh_token: refresh }).catch(() => {})
      },
    }),
    [account, ready, displayError, retry]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}
