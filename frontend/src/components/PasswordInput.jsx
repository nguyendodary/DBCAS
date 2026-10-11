import { useState } from 'react'

// Password field with a show/hide toggle — adapted from the static-pages
// mockups' eye-icon button. No API surface; purely reduces credential typos.
export default function PasswordInput({
  id,
  autoComplete,
  value,
  onChange,
  className = '',
}) {
  const [show, setShow] = useState(false)
  return (
    <div className={`relative ${className}`}>
      <input
        id={id}
        type={show ? 'text' : 'password'}
        required
        autoComplete={autoComplete}
        value={value}
        onChange={onChange}
        className="w-full rounded-lg border border-edge2 bg-abyss/60 px-3.5 py-2.5 pr-12 text-sm text-ink placeholder-faint focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/20"
      />
      <button
        type="button"
        onClick={() => setShow((s) => !s)}
        aria-label={show ? 'Hide password' : 'Show password'}
        aria-pressed={show}
        className="absolute inset-y-0 right-0 flex items-center rounded-r-lg px-3.5 text-mute hover:text-ink"
      >
        {show ? (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-4 w-4" aria-hidden="true">
            <path d="M3 4l18 16" />
            <path d="M10.6 5.1A9.8 9.8 0 0 1 12 5c7 0 10 7 10 7a17 17 0 0 1-3.2 4M6.6 6.6A16 16 0 0 0 2 12s3 7 10 7a9.6 9.6 0 0 0 4.4-1" />
            <path d="M9.9 9.9a3 3 0 0 0 4.2 4.2" />
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-4 w-4" aria-hidden="true">
            <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
            <circle cx="12" cy="12" r="3" />
          </svg>
        )}
      </button>
    </div>
  )
}
