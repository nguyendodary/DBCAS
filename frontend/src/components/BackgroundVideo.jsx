import { useEffect, useState } from 'react'

const REDUCE_QUERY = '(prefers-reduced-motion: reduce)'

export function usePrefersReducedMotion() {
  const [reduce, setReduce] = useState(() =>
    typeof window !== 'undefined' && typeof window.matchMedia === 'function'
      ? window.matchMedia(REDUCE_QUERY).matches
      : false,
  )
  useEffect(() => {
    if (typeof window.matchMedia !== 'function') return undefined
    const mql = window.matchMedia(REDUCE_QUERY)
    const onChange = () => setReduce(mql.matches)
    onChange()
    if (typeof mql.addEventListener === 'function') {
      mql.addEventListener('change', onChange)
      return () => mql.removeEventListener('change', onChange)
    }
    return undefined
  }, [])
  return reduce
}

// Decorative looping background video — the frontend prototype's animated
// hero/landing surfaces. Always muted + playsInline; honors reduced motion by
// mounting the same element without autoplay so the poster frame shows instead.
// `poster` keeps a static fallback for failed/unsupported playback.
export default function BackgroundVideo({ src, poster, className = '' }) {
  const reduce = usePrefersReducedMotion()
  return (
    <video
      className={className}
      autoPlay={!reduce}
      muted
      loop
      playsInline
      preload={reduce ? 'none' : 'auto'}
      poster={poster}
      aria-hidden="true"
      tabIndex={-1}
    >
      <source src={src} type="video/mp4" />
    </video>
  )
}
