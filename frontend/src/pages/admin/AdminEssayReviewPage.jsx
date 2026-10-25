import { useCallback, useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import api, { apiMessage } from '../../api'
import { t, useLocale, number, dateTime } from '../../i18n'
import { Card, Badge, btnPrimary, btnGhost, inputCls } from '../../components/ui'
import { Loading, EmptyState, ErrorState } from '../../components/States'
import { AdminPageHeader } from '../../components/admin'

export default function AdminEssayReviewPage() {
  useLocale()
  const { reviewSessionId } = useParams()
  const [queue, setQueue] = useState(null)
  const [detail, setDetail] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [opening, setOpening] = useState(false)
  const [offset, setOffset] = useState(0)
  const guard = useRef(false)
  const detailSequence = useRef(0)
  const load = useCallback(() => {
    setError(null)
    return api.get('/admin/grading-reviews', { params: { offset, limit: 100 } })
      .then(r => setQueue(r.data)).catch(e => setError(apiMessage(e)))
  }, [offset])
  useEffect(() => { load() }, [load])
  useEffect(() => {
    const timer = setInterval(() => {
      if (!guard.current && !document.hidden) load()
    }, 15000)
    return () => clearInterval(timer)
  }, [load])
  const open = useCallback(async (id) => {
    const sequence = ++detailSequence.current
    setError(null)
    setDetail(null)
    setOpening(true)
    try {
      const response = await api.get(`/admin/grading-reviews/${id}`)
      if (sequence === detailSequence.current) setDetail(response.data)
    } catch (e) { if (sequence === detailSequence.current) setError(apiMessage(e)) }
    finally { if (sequence === detailSequence.current) setOpening(false) }
  }, [])
  useEffect(() => { if (reviewSessionId) open(reviewSessionId) }, [reviewSessionId, open])
  async function mutate(path, payload) {
    if (guard.current) return
    guard.current = true
    setBusy(true)
    setError(null)
    try {
      const result = await api.post(path, payload)
      setDetail(result.data)
      await load()
    } catch (e) { setError(apiMessage(e)) }
    finally { guard.current = false; setBusy(false) }
  }
  return <div data-admin-view="grading" className="space-y-5">
    <AdminPageHeader icon="check" title={t('supervisor.reviewTitle')} subtitle={t('supervisor.reviewHelp')}>
      <button type="button" className={btnGhost} disabled={busy || opening} onClick={() => detail ? open(detail.session_id) : load()}>{t('dashboard.refresh')}</button>
    </AdminPageHeader>
    {error && <ErrorState message={error} onRetry={() => detail ? open(detail.session_id) : load()} />}
    {!queue ? <Loading /> : !queue.length ? <EmptyState title={t('supervisor.queueEmpty')} /> : <Card className="divide-y divide-edge">
      {queue.map(s => <button key={s.session_id} type="button" disabled={busy || opening} className="flex w-full flex-wrap justify-between gap-2 p-4 text-left text-sm hover:bg-surface-hover" onClick={() => open(s.session_id)}>
        <span className="font-semibold text-ink">{s.learner_name} · {s.assessment_title} · #{s.session_id}</span>
        <Badge>{t(`supervisor.${s.release_status}`)}</Badge>
      </button>)}
    </Card>}
    <nav className="flex gap-3" aria-label={t('supervisor.reviewPages')}>
      <button className={btnGhost} disabled={busy || offset === 0} onClick={() => setOffset(Math.max(0, offset - 100))}>{t('assessment.prevPage')}</button>
      <button className={btnGhost} disabled={busy || queue?.length !== 100} onClick={() => setOffset(offset + 100)}>{t('assessment.nextPage')}</button>
    </nav>
    {opening && <Loading />}
    {detail && <section className="space-y-4" aria-label={t('supervisor.reviewDetails')}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div><h2 className="font-bold text-ink">{detail.learner_name} · {detail.assessment_title} · #{detail.session_id}</h2><p role="status" className="mt-1 text-sm text-sub">{t(`supervisor.${detail.release_status}`)}</p></div>
        <button type="button" className={btnPrimary} disabled={busy || detail.release_status !== 'reviewed'} onClick={() => mutate(`/admin/grading-reviews/${detail.session_id}/publish`, { revision: detail.revision })}>{t('supervisor.publish')}</button>
        {detail.release_status === 'grading_failed' && <button type="button" className={btnGhost} disabled={busy} onClick={() => mutate(`/admin/grading-reviews/${detail.session_id}/retry`, { revision: detail.revision })}>{t('supervisor.retryGrading')}</button>}
      </div>
      {detail.items.filter(item => item.question_type === 'essay').map(item => <ReviewItem key={`${item.attempt_id}-${item.revision}-${item.grading_status}`} item={item} busy={busy} reviewAllowed={detail.result_release_policy === 'HUMAN_VERIFIED' ? detail.release_status !== 'published' : true} approve={payload => mutate(`/admin/grading-reviews/${detail.session_id}/attempts/${item.attempt_id}`, payload)} />)}
      <Card className="p-4"><h3 className="font-semibold text-ink">{t('supervisor.audit')}</h3><ul className="mt-2 space-y-2 text-xs text-sub">{detail.events.map((event, i) => <li key={i}>{dateTime(event.created_at)} · {t(`supervisor.${event.previous_status}`)} → {t(`supervisor.${event.new_status}`)}{event.reviewer_id ? ` · #${event.reviewer_id}` : ''}</li>)}</ul></Card>
    </section>}
  </div>
}

function ReviewItem({ item, busy, reviewAllowed, approve }) {
  const [score, setScore] = useState(item.automated_score ?? '')
  const [comments, setComments] = useState('')
  return <Card className="space-y-3 p-4">
    <div className="flex flex-wrap items-center gap-2"><Badge>{item.question_type.toUpperCase()}</Badge><Badge>{item.review ? t('supervisor.approved') : item.review_required ? t('supervisor.requiredReview') : t('supervisor.optionalReview')}</Badge></div>
    <h3 className="whitespace-pre-wrap font-semibold text-ink">{item.prompt}</h3>
    <p className="text-sm text-sub">{t('supervisor.response')}</p>
    <pre className="overflow-x-auto whitespace-pre-wrap break-words rounded bg-elev p-3 text-sm text-ink">{item.sql_answer ?? item.essay_answer ?? (item.options.filter(o => (item.selected_option_ids ?? [item.selected_option_id]).includes(o.option_id)).map(o => o.option_text).join('\n') || '—')}</pre>
    {item.reference_answer && <details><summary className="cursor-pointer text-sm text-cyan-300">{t('supervisor.expected')}</summary><pre className="mt-2 whitespace-pre-wrap break-words text-sm text-sub">{item.reference_answer}</pre></details>}
    {item.rubrics.length > 0 && <details><summary className="cursor-pointer text-sm text-cyan-300">{t('supervisor.rubric')}</summary><ul className="mt-2 space-y-2 text-sm text-sub">{item.rubrics.map(r => <li key={r.level_name}>{r.level_name} ({number(r.min_score)}–{number(r.max_score)}): {r.criteria}</li>)}</ul></details>}
    <p className="text-sm text-sub">{t('supervisor.suggested')}: {item.automated_score == null ? t('evidence.notGraded') : number(item.automated_score)} / {number(item.points)}</p>
    {item.automated_detail && <details><summary className="cursor-pointer text-sm text-cyan-300">{t('supervisor.automatedEvidence')}</summary><pre className="mt-2 max-h-80 overflow-auto whitespace-pre-wrap break-words text-xs text-sub">{JSON.stringify(item.automated_detail, null, 2)}</pre></details>}
    {item.review ? <p className="text-sm text-sub">{t('supervisor.approved')}: {number(item.final_score)} / {number(item.points)} · #{item.review.reviewer_id} · {dateTime(item.review.reviewed_at)}<span className="block whitespace-pre-wrap">{item.review.comments}</span></p> : item.submitted_at && reviewAllowed && <form onSubmit={e => { e.preventDefault(); approve({ score, comments: comments || null, revision: item.revision }) }}>
      <fieldset disabled={busy || !['graded', 'failed', 'pending'].includes(item.grading_status)} className="flex flex-wrap items-end gap-3">
        <label className="text-sm text-sub">{t('supervisor.finalScore')}<input type="number" min="0" max={item.points} step="0.01" required value={score} onChange={e => setScore(e.target.value)} className={`${inputCls} mt-1 block w-32`} /></label>
        <label className="grow text-sm text-sub">{t('supervisor.comments')}<textarea maxLength={4000} required={['failed', 'pending'].includes(item.grading_status)} value={comments} onChange={e => setComments(e.target.value)} className={`${inputCls} mt-1 block w-full`} /></label>
        <button type="submit" className={btnPrimary}>{t('supervisor.approve')}</button>
      </fieldset>
    </form>}
  </Card>
}
