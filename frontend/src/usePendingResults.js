import { useEffect, useRef, useState } from 'react'

// Check both automatic grading and instructor publication. Poll for at most
// five minutes, back off, and never overlap requests. Returning to a tab checks
// once even after the polling budget expires; a manual retry starts a new budget.
export default function usePendingResults(active, refresh, restartKey = 0) {
  const latest = useRef(refresh)
  const [timedOut, setTimedOut] = useState(false)
  useEffect(() => { latest.current = refresh }, [refresh])
  useEffect(() => {
    setTimedOut(false)
    if (!active) return
    let disposed = false
    let expired = false
    let busy = false
    let delay = 5000
    let timer
    const maxDelay = active === 'pending_review' || active === 'reviewed' ? 30000 : 15000
    const deadline = setTimeout(() => {
      expired = true
      clearTimeout(timer)
      setTimedOut(true)
    }, 300000)
    async function check() {
      if (disposed || busy || document.visibilityState === 'hidden') return
      busy = true
      try { await latest.current() } catch { /* The caller renders recoverable errors. */ }
      finally { busy = false }
    }
    function schedule() {
      if (disposed || expired) return
      timer = setTimeout(async () => {
        await check()
        delay = Math.min(maxDelay, delay + 5000)
        schedule()
      }, delay)
    }
    const onReturn = () => { check() }
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
