import { useCallback, useEffect, useRef, useState } from 'react'
import api from './api'

// Coalesces the blur+visibilitychange pair that one tab switch produces.
// The server owns the real grace period; this timer only avoids duplicate
// reports and brief focus flicker.
export const TAB_LEAVE_DEBOUNCE_MS = 200

const pendingKey = (sessionId) => `dbcas-tab-leave:${sessionId}`

function readPending(sessionId) {
  try {
    return sessionStorage.getItem(pendingKey(sessionId))
  } catch {
    return null
  }
}

function writePending(sessionId, value) {
  try {
    if (value) sessionStorage.setItem(pendingKey(sessionId), value)
    else sessionStorage.removeItem(pendingKey(sessionId))
  } catch {
    /* restricted storage: the in-memory ref still deduplicates this page */
  }
}

function normalise(state) {
  if (!state) return null
  return {
    ...state,
    violation_count: Number(state.violation_count || 0),
    violation_limit: Number(state.violation_limit || 3),
    grace_seconds: Number(state.grace_seconds || 3),
    warning_level: Number(state.warning_level || 0),
    cancelled: Boolean(state.cancelled),
  }
}

/**
 * Reports FIXED-paper focus leaves to the server. The server measures the
 * away duration, decides whether it counts, and returns the authoritative
 * counter. A pending leave survives reload in sessionStorage so re-entry
 * reports the return instead of losing the violation.
 */
export function useTabLeaveGuard({ sessionId, enabled = true, initialState = null }) {
  const [state, setState] = useState(() => normalise(initialState))
  const stateRef = useRef(normalise(initialState))
  const enabledRef = useRef(enabled)
  const desiredRef = useRef(Boolean(readPending(sessionId)))
  const sentRef = useRef(Boolean(readPending(sessionId)))
  const timerRef = useRef(null)
  const inFlightRef = useRef(false)

  enabledRef.current = enabled

  useEffect(() => {
    const next = normalise(initialState)
    if (!next) return
    stateRef.current = next
    setState(next)
  }, [
    initialState?.violation_count,
    initialState?.violation_limit,
    initialState?.grace_seconds,
    initialState?.cancelled,
    initialState?.status,
  ])

  const report = useCallback(
    async (event, leaveId) => {
      if (!enabledRef.current || stateRef.current?.cancelled) return
      const eventId = crypto.randomUUID()
      try {
        const { data } = await api.post(`/sessions/${sessionId}/paper/tab-leave`, {
          event,
          event_id: eventId,
          ...(leaveId ? { leave_event_id: leaveId } : {}),
        })
        const next = normalise(data)
        stateRef.current = next
        setState(next)
        if (event === 'leave') writePending(sessionId, eventId)
        else writePending(sessionId, null)
      } catch {
        // A failed report must not block the exam UI. The next focus
        // transition retries with a fresh event id.
        if (event === 'leave') writePending(sessionId, null)
      }
    },
    [sessionId],
  )

  const commit = useCallback(async () => {
    if (!enabledRef.current || stateRef.current?.cancelled) return
    if (inFlightRef.current) return
    inFlightRef.current = true
    try {
      while (desiredRef.current !== sentRef.current) {
        if (desiredRef.current) {
          sentRef.current = true
          await report('leave')
        } else {
          sentRef.current = false
          await report('return', readPending(sessionId))
        }
        if (!enabledRef.current || stateRef.current?.cancelled) break
      }
    } finally {
      inFlightRef.current = false
    }
  }, [report, sessionId])

  const schedule = useCallback(
    (away) => {
      desiredRef.current = away
      if (timerRef.current) clearTimeout(timerRef.current)
      timerRef.current = setTimeout(() => {
        timerRef.current = null
        commit()
      }, TAB_LEAVE_DEBOUNCE_MS)
    },
    [commit],
  )

  useEffect(() => {
    if (!enabled) return undefined
    const hidden = () => {
      if (document.visibilityState === 'hidden') schedule(true)
      else schedule(false)
    }
    const blur = () => schedule(true)
    const focus = () => schedule(false)
    document.addEventListener('visibilitychange', hidden)
    window.addEventListener('blur', blur)
    window.addEventListener('focus', focus)
    if (readPending(sessionId)) schedule(false)
    return () => {
      document.removeEventListener('visibilitychange', hidden)
      window.removeEventListener('blur', blur)
      window.removeEventListener('focus', focus)
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [enabled, schedule, sessionId])

  return state
}

export default useTabLeaveGuard
