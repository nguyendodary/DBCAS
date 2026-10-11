import { useEffect, useState } from 'react'
import api from '../api'

// Official brand marks (SVG paths) — the same logos the prototype pages
// used; they render locally, no asset files needed.
function GoogleLogo({ className = 'h-4 w-4' }) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
      <path
        fill="#EA4335"
        d="M12 5c1.6 0 3 .6 4.1 1.6l3.1-3.1C17.3 1.8 14.8 1 12 1 7.4 1 3.5 3.6 1.6 7.4l3.7 2.9C6.2 7.1 8.9 5 12 5z"
      />
      <path
        fill="#4285F4"
        d="M23.5 12.3c0-.8-.1-1.6-.2-2.3H12v4.5h6.5c-.3 1.5-1.1 2.8-2.4 3.7l3.7 2.9c2.2-2 3.7-5 3.7-8.8z"
      />
      <path
        fill="#FBBC05"
        d="M5.3 14.7c-.2-.7-.4-1.5-.4-2.7s.2-2 .4-2.7L1.6 6.4C.6 8.4 0 10.6 0 13s.6 4.6 1.6 6.6l3.7-2.9z"
      />
      <path
        fill="#34A853"
        d="M12 23c3.2 0 6-1.1 8-3l-3.7-2.9c-1.1.7-2.5 1.2-4.3 1.2-3.1 0-5.8-2.1-6.7-5.3L1.6 15C3.5 18.8 7.4 23 12 23z"
      />
    </svg>
  )
}

function GitHubLogo({ className = 'h-4 w-4' }) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden="true">
      <path d="M12 .5C5.65.5.5 5.65.5 12c0 5.08 3.29 9.39 7.86 10.91.58.11.79-.25.79-.55v-2.15c-3.2.7-3.87-1.36-3.87-1.36-.53-1.33-1.28-1.69-1.28-1.69-1.05-.72.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.77 2.7 1.26 3.36.96.1-.75.4-1.26.73-1.55-2.55-.29-5.23-1.28-5.23-5.68 0-1.26.45-2.28 1.19-3.09-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.18 1.18a11 11 0 0 1 5.78 0c2.21-1.49 3.18-1.18 3.18-1.18.63 1.59.23 2.76.11 3.05.74.81 1.19 1.83 1.19 3.09 0 4.41-2.69 5.38-5.25 5.67.41.35.77 1.05.77 2.12v3.15c0 .3.21.66.8.55A11.51 11.51 0 0 0 23.5 12C23.5 5.65 18.35.5 12 .5z" />
    </svg>
  )
}

const PROVIDERS = [
  { name: 'google', label: 'Google', Logo: GoogleLogo },
  { name: 'github', label: 'GitHub', Logo: GitHubLogo },
]

// Real OAuth entry points — these are plain links that navigate the whole
// page to the backend start route, which 302s to the provider. Provider
// secrets never touch this bundle. When the server reports a provider as
// unconfigured the button is disabled with an explanation instead of
// sending the user into a dead flow.
export default function OAuthButtons({ divider = 'or continue with' }) {
  const [configured, setConfigured] = useState(null) // name -> bool | null while loading

  useEffect(() => {
    let cancelled = false
    api
      .get('/auth/oauth/providers')
      .then((r) => {
        if (cancelled) return
        const map = {}
        for (const p of r.data?.providers || []) map[p.name] = p.configured
        setConfigured(map)
      })
      .catch(() => {
        // Endpoint unreachable → leave buttons enabled; the backend start
        // route still reports oauth_not_configured with a clear error.
        if (!cancelled) setConfigured({})
      })
    return () => {
      cancelled = true
    }
  }, [])

  const anyDisabled =
    configured !== null && PROVIDERS.some((p) => configured[p.name] === false)

  return (
    <div className="mt-6">
      <div className="flex items-center gap-3" aria-hidden="true">
        <span className="h-px flex-1 bg-edge" />
        <span className="text-xs text-mute">{divider}</span>
        <span className="h-px flex-1 bg-edge" />
      </div>
      <div className="mt-4 grid gap-2 sm:grid-cols-2">
        {PROVIDERS.map(({ name, label, Logo }) => {
          const disabled = configured !== null && configured[name] === false
          return (
            <a
              key={name}
              href={disabled ? undefined : `/api/v1/auth/oauth/${name}/start`}
              aria-disabled={disabled}
              title={
                disabled
                  ? `${label} sign-in is not configured on this server`
                  : `Continue with ${label}`
              }
              className={`flex min-h-10 items-center justify-center gap-2.5 rounded-lg border px-3 py-2 text-sm font-medium ${
                disabled
                  ? 'cursor-not-allowed border-edge text-mute opacity-60'
                  : 'border-edge2 bg-elev/50 text-ink hover:border-cyan-400/50 hover:bg-cyan-400/[0.08]'
              }`}
            >
              <Logo />
              Continue with {label}
            </a>
          )
        })}
      </div>
      {anyDisabled && (
        <p className="mt-3 text-center text-xs text-mute">
          Unavailable sign-in methods are disabled on this server.
        </p>
      )}
    </div>
  )
}
