import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import api from './api'

const TOKEN_KEY = 'dbcas_token'
const AuthContext = createContext(null)

// Stateless JWT auth (UC02/UC03): the token lives in localStorage and is
// attached by the axios interceptor; logout is purely client-side — the
// issued JWT stays valid until expiry by design.
export function AuthProvider({ children }) {
  const [account, setAccount] = useState(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    if (!localStorage.getItem(TOKEN_KEY)) {
      setReady(true)
      return
    }
    api
      .get('/auth/me')
      .then((r) => setAccount(r.data))
      .catch(() => localStorage.removeItem(TOKEN_KEY))
      .finally(() => setReady(true))
  }, [])

  const value = useMemo(
    () => ({
      account,
      ready,
      hasRole: (role) => Boolean(account?.roles?.includes(role)),
      async login(email, password) {
        const r = await api.post('/auth/login', { email, password })
        localStorage.setItem(TOKEN_KEY, r.data.access_token)
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
      logout() {
        localStorage.removeItem(TOKEN_KEY)
        setAccount(null)
      },
    }),
    [account, ready]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}
