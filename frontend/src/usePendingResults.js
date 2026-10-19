import { useEffect, useRef, useState } from 'react'

// Refresh only while automatic grading is outstanding. Stop after five minutes
// or on unmount; human review remains an explicit, manually refreshable wait.
export default function usePendingResults(active, refresh) {
  const latest = useRef(refresh)
  const [timedOut, setTimedOut] = useState(false)
  useEffect(() => { latest.current = refresh }, [refresh])
  useEffect(() => {
    if (!active) {
      setTimedOut(false)
      return
    }
    setTimedOut(false)
    let count = 0
    const timer = setInterval(() => {
      latest.current()
      if (++count >= 60) {
        clearInterval(timer)
        setTimedOut(true)
      }
    }, 5000)
    return () => clearInterval(timer)
  }, [active])
  return timedOut
}
