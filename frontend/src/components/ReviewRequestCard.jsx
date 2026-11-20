import { useCallback, useEffect, useRef, useState } from 'react'
import api, { apiMessage } from '../api'
import { i18n, t, useLocale } from '../i18n'
import { Card, btnGhost, btnPrimary } from './ui'

const reviewLabels = {
  REQUESTED: 'pending',
  IN_REVIEW: 'inReview',
  REJECTED: 'rejected',
  EXPIRED: 'expired',
}

function reviewMessage(error) {
  const status = error.response?.status
  if (status === 403) return t('reviewRequest.forbidden')
  if (status === 404) return t('reviewRequest.unavailable')
  return apiMessage(error)
}

export default function ReviewRequestCard({ session, resultVersion, onOfficial }) {
  useLocale()
  const url = `/sessions/${session.session_id}/review-request`
  const [review, setReview] = useState()
  const [reason, setReason] = useState('')
  const [blocked, setBlocked] = useState(false)
  const [message, setMessage] = useState(null)
  const [busy, setBusy] = useState(false)
  const [ambiguous, setAmbiguous] = useState(false)
  const controller = useRef(null)
  const submitting = useRef(false)
  const intent = useRef(null)

  const readReview = useCallback(
    async (signal) => {
      if (signal.aborted) return
      setBusy(true)
      setMessage(null)
      try {
        const { data } = await api.get(url, { signal })
        if (signal.aborted) return
        if (data.v2_state === 'OFFICIAL') await onOfficial(signal)
        if (!signal.aborted) {
          setReview(data)
          setBlocked(false)
        }
      } catch (error) {
        if (signal.aborted) return
        const { status, data } = error.response ?? {}
        if (status === 404 && data?.error?.code === 'review_not_found') {
          setReview(null)
        } else {
          if (status === 403 || status === 404) setBlocked(true)
          setMessage(reviewMessage(error))
        }
      } finally {
        if (!signal.aborted) setBusy(false)
      }
    },
    [url, onOfficial],
  )

  useEffect(() => {
    const abort = new AbortController()
    controller.current = abort
    readReview(abort.signal)
    return () => abort.abort()
  }, [readReview])

  const canRequest =
    review === null &&
    session.review_status === 'OFFICIAL' &&
    session.can_request_review === true &&
    Boolean(session.review_window_expires_at) &&
    !blocked
  const trimmed = reason.trim()
  const reasonLength = [...trimmed].length

  async function submit(event) {
    event.preventDefault()
    const signal = controller.current.signal
    if (!canRequest || busy || submitting.current || reasonLength < 10 || reasonLength > 2000)
      return
    submitting.current = true
    setBusy(true)
    setMessage(null)
    intent.current ??= { key: crypto.randomUUID(), reason: trimmed }
    try {
      const { data } = await api.post(
        url,
        { reason: intent.current.reason },
        {
          signal,
          headers: { 'Idempotency-Key': intent.current.key },
        },
      )
      if (signal.aborted) return
      if (data.v2_state === 'OFFICIAL') await onOfficial(signal)
      if (!signal.aborted) setReview(data)
    } catch (error) {
      if (signal.aborted) return
      const { status, data } = error.response ?? {}
      const code = data?.error?.code
      if (status === 409 && code === 'review_exists') {
        setBlocked(true)
        await readReview(signal)
      } else if (status === 409 && ['review_window_closed', 'review_not_eligible'].includes(code)) {
        setBlocked(true)
        setMessage(t('reviewRequest.closed'))
      } else {
        if (status === 403 || status === 404) setBlocked(true)
        const failedBeforeAcceptance = status === 422
        if (failedBeforeAcceptance) intent.current = null
        setAmbiguous(!failedBeforeAcceptance && status !== 403 && status !== 404)
        setMessage(reviewMessage(error))
      }
    } finally {
      submitting.current = false
      if (!signal.aborted) setBusy(false)
    }
  }

  const v2 = review?.v2_state
  const label = v2 === 'OFFICIAL' ? 'v2Official' : reviewLabels[review?.status]
  const checkStatus =
    !blocked &&
    !canRequest &&
    (Boolean(message) || ['REQUESTED', 'IN_REVIEW'].includes(review?.status))
  if (!canRequest && !review && !message) return null

  return (
    <Card className="space-y-3 p-5">
      {review && (
        <div role="status" className="space-y-1">
          {label && <p className="font-semibold">{t(`reviewRequest.${label}`)}</p>}
          {v2 !== 'OFFICIAL' && resultVersion === 1 && <p>{t('reviewRequest.v1Official')}</p>}
          {v2 === 'ANALYSIS_PENDING' && <p>{t('reviewRequest.analysisPending')}</p>}
          {v2 === 'ANALYSIS_FAILED_V1_KEPT' && <p>{t('reviewRequest.analysisFailed')}</p>}
        </div>
      )}
      {message && (
        <p role="alert">{typeof message === 'string' ? message : t(message.translationKey)}</p>
      )}
      {checkStatus && (
        <button
          type="button"
          className={btnGhost}
          disabled={busy}
          onClick={() => readReview(controller.current.signal)}
        >
          {t('reviewRequest.checkStatus')}
        </button>
      )}
      {canRequest && (
        <form className="space-y-3" onSubmit={submit}>
          <p className="text-sm text-sub">
            {t('reviewRequest.deadline', {
              date: new Date(session.review_window_expires_at).toLocaleString(i18n.language),
            })}
          </p>
          <label className="block">
            {t('reviewRequest.reason')}
            <textarea
              className="mt-1 block w-full rounded-lg border border-edge bg-surface p-2"
              required
              maxLength={2000}
              disabled={busy}
              readOnly={ambiguous}
              value={reason}
              onChange={(event) => setReason(event.target.value)}
            />
          </label>
          <button
            type="submit"
            className={btnPrimary}
            disabled={busy || reasonLength < 10 || reasonLength > 2000}
          >
            {t('reviewRequest.request')}
          </button>
        </form>
      )}
    </Card>
  )
}
