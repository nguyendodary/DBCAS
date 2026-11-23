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

function scheduleAfterLoad(callback) {
  let cancelled = false
  let handle = null
  const schedule = () => {
    if (cancelled) return
    if (typeof window.requestIdleCallback === 'function') {
      handle = { idle: window.requestIdleCallback(callback, { timeout: 1500 }) }
    } else {
      handle = { timeout: window.setTimeout(callback, 0) }
    }
  }
  if (document.readyState === 'complete') {
    schedule()
  } else {
    window.addEventListener('load', schedule, { once: true })
  }
  return () => {
    cancelled = true
    window.removeEventListener('load', schedule)
    if (!handle) return
    if ('idle' in handle) window.cancelIdleCallback?.(handle.idle)
    else window.clearTimeout(handle.timeout)
  }
}

// Decorative looping background video — the frontend prototype's animated
// hero/landing surfaces. Always muted + playsInline; honors reduced motion by
// mounting the same element without autoplay so the poster frame shows instead.
// `poster` keeps a static fallback for failed/unsupported playback. The media
// source is attached only after the page load event and an idle slot, so the
// poster and critical JS/CSS paint first without changing the page's visuals.
export default function BackgroundVideo({ src, poster, className = '' }) {
  const reduce = usePrefersReducedMotion()
  const [active, setActive] = useState(false)
  useEffect(() => {
    if (reduce) {
      setActive(false)
      return undefined
    }
    return scheduleAfterLoad(() => setActive(true))
  }, [reduce])
  return (
    <video
      className={className}
      autoPlay={!reduce}
      muted
      loop
      playsInline
      preload="none"
      poster={poster}
      aria-hidden="true"
      tabIndex={-1}
    >
      {active && !reduce && <source src={src} type="video/mp4" />}
    </video>
  )
}
