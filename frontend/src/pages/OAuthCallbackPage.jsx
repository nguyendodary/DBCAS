import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { Loading } from '../components/States'

// OAuth landing route — the backend callback 302s here with a one-time
// HttpOnly handoff cookie; we exchange it for the real JWT, then land on
// the role-appropriate home. Failures go back to /login with an error.
export default function OAuthCallbackPage() {
  const { completeOAuth } = useAuth()
  const navigate = useNavigate()
  const ran = useRef(false) // StrictMode double-invokes effects in dev

  useEffect(() => {
    if (ran.current) return
    ran.current = true
    completeOAuth()
      .then((account) =>
        navigate(account.roles.includes('Administrator') ? '/admin' : '/dashboard', {
          replace: true,
        })
      )
      .catch(() => navigate('/login?oauth_error=complete', { replace: true }))
  }, [completeOAuth, navigate])

  return (
    <div className="flex min-h-screen items-center justify-center bg-abyss">
      <Loading label="Completing sign-in…" />
    </div>
  )
}
