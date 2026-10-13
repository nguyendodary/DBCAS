import { t, useLocale } from '../i18n'
import { useState } from 'react'
import { Icon } from './ui'

// Password field with a show/hide toggle, styled as the auth surface's icon
// input (lock glyph left, eye toggle right — the source Dang_nhap pattern).
export default function PasswordInput({
  id,
  autoComplete,
  value,
  onChange,
  className = '',
  placeholder,
}) {
  useLocale()
  const [show, setShow] = useState(false)
  return (
    <div className={`auth-field has-right ${className}`}>
      <Icon name="lock" className="auth-field-icon" />
      <input
        id={id}
        type={show ? 'text' : 'password'}
        required
        autoComplete={autoComplete}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
      />
      <button
        type="button"
        onClick={() => setShow((s) => !s)}
        aria-label={show ? t('auth.hidePassword') : t('auth.showPassword')}
        aria-pressed={show}
        className="auth-pw-toggle"
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
