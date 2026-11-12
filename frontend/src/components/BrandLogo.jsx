import { Link } from 'react-router-dom'
import { t, useLocale } from '../i18n'

// One product name, one mark, one tagline key. Every visible DBCAS lockup in
// the application renders through this module so the brand cannot drift into a
// second inline SVG or a hand-typed wordmark.
export const PRODUCT_NAME = 'DBCAS'
export const BRAND_TAGLINE_KEY = 'nav.engineTagFull'

export function BrandMark({ className = '' }) {
  return <span className={`brand-mark ${className}`.trim()} aria-hidden="true" />
}

export function BrandWordmark({ as: Tag = 'span', className = '' }) {
  return <Tag className={`brand-wordmark ${className}`.trim()}>{PRODUCT_NAME}</Tag>
}

export default function BrandLogo({
  to = '/',
  variant = 'header',
  showTagline = true,
  taglineKey = BRAND_TAGLINE_KEY,
  taglineClassName = '',
  className = '',
}) {
  useLocale()
  const body = (
    <>
      <span className="brand-logo-row">
        <BrandMark />
        <BrandWordmark />
      </span>
      {showTagline && (
        <span className={`brand-logo-tagline ${taglineClassName}`.trim()}>{t(taglineKey)}</span>
      )}
    </>
  )
  const classes = `brand-logo brand-logo--${variant} ${className}`.trim()
  if (!to) return <span className={classes}>{body}</span>
  return (
    <Link to={to} className={classes} aria-label={PRODUCT_NAME}>
      {body}
    </Link>
  )
}
