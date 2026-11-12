import { useEffect, useRef, useState } from 'react'

// Check both automatic grading and instructor publication. Poll for at most
// five minutes for AI, back off, and never overlap requests. Instructor review
// has no spinner or deadline: publication can arrive while the learner waits.
// Returning to an expired AI tab checks once; retry starts a new polling budget.
export default function usePendingResults(active, refresh, restartKey = 0) {
  const latest = useRef(refresh)
  const [timedOut, setTimedOut] = useState(false)
  useEffect(() => {
    latest.current = refresh
  }, [refresh])
  useEffect(() => {
    setTimedOut(false)
    if (!active) return
    let disposed = false
    let expired = false
    let busy = false
    let delay = 5000
    let timer
    const human = ['provisional_ai', 'pending_review', 'reviewed', 'grading_failed'].includes(
      active,
    )
    const maxDelay = human ? 30000 : 15000
    const deadline = human
      ? null
      : setTimeout(() => {
          expired = true
          clearTimeout(timer)
          setTimedOut(true)
        }, 300000)
    async function check() {
      if (disposed || busy || document.visibilityState === 'hidden') return
      busy = true
      try {
        await latest.current()
      } catch {
        /* The caller renders recoverable errors. */
      } finally {
        busy = false
      }
    }
    function schedule() {
      if (disposed || expired) return
      timer = setTimeout(async () => {
        await check()
        delay = Math.min(maxDelay, delay + 5000)
        schedule()
      }, delay)
    }
    const onReturn = () => {
      check()
    }
    window.addEventListener('focus', onReturn)
    document.addEventListener('visibilitychange', onReturn)
    schedule()
    return () => {
      disposed = true
      clearTimeout(timer)
      clearTimeout(deadline)
      window.removeEventListener('focus', onReturn)
      document.removeEventListener('visibilitychange', onReturn)
    }
  }, [active, restartKey])
  return timedOut
}
