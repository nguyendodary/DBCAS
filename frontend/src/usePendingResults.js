import { useEffect, useRef } from 'react'

// Refresh only while automatic grading is outstanding. Stop after five minutes
// or on unmount; human review remains an explicit, manually refreshable wait.
export default function usePendingResults(active, refresh) {
  const latest = useRef(refresh)
  useEffect(() => { latest.current = refresh }, [refresh])
  useEffect(() => {
    if (!active) return
    let count = 0
    const timer = setInterval(() => {
      latest.current()
      if (++count >= 60) clearInterval(timer)
    }, 5000)
    return () => clearInterval(timer)
  }, [active])
}
