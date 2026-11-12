import { useCallback, useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import api, { apiMessage } from '../../api'
import { t, useLocale, number, dateTime } from '../../i18n'
import { Card, Badge, TypeBadge, btnPrimary, btnGhost, inputCls } from '../../components/ui'
import { Loading, EmptyState, ErrorState } from '../../components/States'
import { AdminPageHeader } from '../../components/admin'

export default function AdminGradingPage() {
  useLocale()
  const { reviewSessionId } = useParams()
  const [queue, setQueue] = useState(null)
  const [detail, setDetail] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [opening, setOpening] = useState(false)
  const [offset, setOffset] = useState(0)
  const [showMcq, setShowMcq] = useState(false)
  const guard = useRef(false)
  const detailSequence = useRef(0)
  const requestedReview = useRef(null)
  const load = useCallback(() => {
    setError(null)
    return api
      .get('/admin/grading-reviews', { params: { offset, limit: 100 } })
      .then((r) => setQueue(r.data))
      .catch((e) => setError(apiMessage(e)))
  }, [offset])
  useEffect(() => {
    load()
  }, [load])
  const open = useCallback(async (id) => {
    requestedReview.current = String(id)
    const sequence = ++detailSequence.current
    setError(null)
    setDetail(null)
    setOpening(true)
    try {
      const response = await api.get(`/admin/grading-reviews/${id}`)
      if (sequence === detailSequence.current) setDetail(response.data)
    } catch (e) {
      if (sequence === detailSequence.current) setError(apiMessage(e))
    } finally {
      if (sequence === detailSequence.current) setOpening(false)
    }
  }, [])
  function refresh() {
    load()
    if (requestedReview.current) open(requestedReview.current)
  }
  useEffect(() => {
    if (reviewSessionId) open(reviewSessionId)
  }, [reviewSessionId, open])
  useEffect(() => {
    if (!detail || detail.release_status !== 'auto_grading') return
    const id = detail.session_id
    let canceled = false,
      rounds = 0
    const timer = setInterval(async () => {
      if (++rounds > 30) {
        clearInterval(timer)
        return
      }
      try {
        const r = await api.get(`/admin/grading-reviews/${id}`)
        if (!canceled && requestedReview.current === String(id)) setDetail(r.data)
      } catch {
        clearInterval(timer)
      }
    }, 2000)
    return () => {
      canceled = true
      clearInterval(timer)
    }
  }, [detail?.session_id, detail?.release_status])
  async function mutate(path, payload) {
    if (guard.current) return
    guard.current = true
    setBusy(true)
    setError(null)
    try {
      const result = await api.post(path, payload)
      setDetail(result.data)
      await load()
    } catch (e) {
      setError(apiMessage(e))
    } finally {
      guard.current = false
      setBusy(false)
    }
  }
  function renderReviewItem(item) {
    return (
      <ReviewItem
        key={`${item.attempt_id}-${item.revision}-${item.grading_status}`}
        item={item}
        busy={busy}
        published={detail.release_status === 'published'}
        practice={detail.learner_defined}
        sessionId={detail.session_id}
        reviewAllowed={
          detail.result_release_policy === 'HUMAN_VERIFIED' || detail.manual_review_required
        }
        approve={(payload) =>
          mutate(`/admin/grading-reviews/${detail.session_id}/attempts/${item.attempt_id}`, payload)
        }
      />
    )
  }
  return (
    <div className="space-y-5">
      <AdminPageHeader title={t('supervisor.reviewTitle')} subtitle={t('supervisor.reviewHelp')}>
        <button type="button" className={btnGhost} disabled={busy || opening} onClick={refresh}>
          {t('dashboard.refresh')}
        </button>
      </AdminPageHeader>
      {error && <ErrorState message={error} onRetry={refresh} />}
      {!queue ? (
        !error && <Loading />
      ) : !queue.length ? (
        <EmptyState title={t('supervisor.queueEmpty')} />
      ) : (
        <Card className="divide-y divide-edge">
          {queue.map((s) => (
            <button
              key={s.session_id}
              type="button"
              disabled={busy || opening}
              className="flex w-full flex-wrap justify-between gap-2 p-4 text-left text-sm hover:bg-surface-hover"
              onClick={() => open(s.session_id)}
            >
              <span className="font-semibold text-ink">
                {s.learner_name} · {s.assessment_title} · #{s.session_id}
              </span>
              <Badge>
                {t(
                  `supervisor.${String(detail?.session_id) === String(s.session_id) ? detail.release_status : s.release_status}`,
                )}
              </Badge>
            </button>
          ))}
        </Card>
      )}
      {(offset > 0 || queue?.length === 100) && (
        <nav className="flex gap-3" aria-label={t('supervisor.reviewPages')}>
          <button
            className={btnGhost}
            disabled={busy || offset === 0}
            onClick={() => setOffset(Math.max(0, offset - 100))}
          >
            {t('assessment.prevPage')}
          </button>
          <button
            className={btnGhost}
            disabled={busy || queue?.length !== 100}
            onClick={() => setOffset(offset + 100)}
          >
            {t('assessment.nextPage')}
          </button>
        </nav>
      )}
      {opening && <Loading />}
      {detail && (
        <section className="space-y-4" aria-label={t('supervisor.reviewDetails')}>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="font-bold text-ink">
                {detail.learner_name} · {detail.assessment_title} · #{detail.session_id}
              </h2>
              <p role="status" className="mt-1 text-sm text-sub">
                {t(`supervisor.${detail.release_status}`)}
              </p>
            </div>
            <button
              type="button"
              className={btnPrimary}
              disabled={
                busy ||
                (detail.learner_defined
                  ? !detail.evaluation ||
                    !['provisional_ai', 'pending_review'].includes(detail.release_status)
                  : detail.release_status !== 'reviewed')
              }
              onClick={() =>
                mutate(`/admin/grading-reviews/${detail.session_id}/publish`, {
                  revision: detail.revision,
                })
              }
            >
              {detail.learner_defined ? 'Duyệt' : t('supervisor.publish')}
            </button>
            {detail.release_status === 'grading_failed' && (
              <button
                type="button"
                className={btnGhost}
                disabled={busy}
                onClick={() =>
                  mutate(`/admin/grading-reviews/${detail.session_id}/retry`, {
                    revision: detail.revision,
                  })
                }
              >
                {t('supervisor.retryGrading')}
              </button>
            )}
          </div>
          {detail.learner_defined && (
            <Card className="space-y-3 p-5">
              <h3 className="font-semibold">Đánh giá AI</h3>
              {detail.evaluation ? (
                <>
                  <p className="text-sub">{detail.evaluation.evaluation.summary}</p>
                  {detail.evaluation.evaluator_fallback && (
                    <p className="text-sm text-sub">Đánh giá dự phòng theo quy tắc.</p>
                  )}
                  <ul className="list-disc space-y-2 pl-5 text-sub">
                    {detail.evaluation.evaluation.question_comments.map((item, index) => (
                      <li key={item.attempt_id}>
                        Câu {index + 1}: {item.comment}
                      </li>
                    ))}
                  </ul>
                </>
              ) : (
                <p role="status">Đang chờ AI đánh giá...</p>
              )}
            </Card>
          )}
          {detail.learner_defined && detail.final_result && (
            <Card className="space-y-2 p-5">
              <h3 className="font-semibold">Kết quả cuối cùng đã duyệt</h3>
              <p className="text-sub">{detail.final_result.final_evaluation?.summary}</p>
              <p className="text-sm text-sub">
                Nguồn: {detail.final_result.source === 'legacy' ? 'bản cũ đã duyệt' : 'giảng viên duyệt'}
              </p>
            </Card>
          )}
          {detail.items.filter((item) => item.question_type !== 'mcq').map(renderReviewItem)}
          {detail.items.some((item) => item.question_type === 'mcq') && (
            <details
              onToggle={(event) => setShowMcq(event.currentTarget.open)}
              className="rounded-xl border border-edge p-4"
            >
              <summary className="cursor-pointer font-semibold text-ink">
                {t('local.autoMcq')}
              </summary>
              {showMcq && (
                <div className="mt-4 space-y-4">
                  {detail.items
                    .filter((item) => item.question_type === 'mcq')
                    .map(renderReviewItem)}
                </div>
              )}
            </details>
          )}
          {detail.learner_defined &&
            detail.evaluation &&
            detail.release_status !== 'published' && (
              <FinalFeedbackEditor
                key={`${detail.session_id}-${detail.revision}`}
                detail={detail}
                busy={busy}
                onPublish={(feedback) =>
                  mutate(`/admin/grading-reviews/${detail.session_id}/publish`, {
                    revision: detail.revision,
                    final_feedback: feedback,
                  })
                }
              />
            )}
          <Card className="p-4">
            <h3 className="font-semibold text-ink">{t('supervisor.audit')}</h3>
            <ul className="mt-2 space-y-2 text-xs text-sub">
              {detail.events.map((event, i) => (
                <li key={i}>
                  {dateTime(event.created_at)} · {t(`supervisor.${event.previous_status}`)} →{' '}
                  {t(`supervisor.${event.new_status}`)}
                  {event.reviewer_id ? ` · #${event.reviewer_id}` : ''}
                </li>
              ))}
            </ul>
          </Card>
          {detail.score_edits?.length > 0 && (
            <Card className="p-4">
              <h3 className="font-semibold">Lịch sử điều chỉnh điểm</h3>
              <ul className="mt-3 space-y-3 text-sm text-sub">
                {detail.score_edits.map((edit, i) => (
                  <li key={i}>
                    {dateTime(edit.created_at)} · Giảng viên #{edit.reviewer_id} ·{' '}
                    {edit.old_score ?? 'Chưa chấm'} → {edit.new_score} điểm<p>{edit.reason}</p>
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </section>
      )}
    </div>
  )
}

function lines(value) {
  return value
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean)
}

function FinalFeedbackEditor({ detail, busy, onPublish }) {
  const draft = detail.final_result?.final_evaluation || detail.evaluation?.evaluation || {}
  const notes = Object.fromEntries(
    (draft.concepts || []).map((item) => [item.concept_id, item]),
  )
  const [summary, setSummary] = useState(draft.summary || '')
  const [strengths, setStrengths] = useState((draft.strengths || []).join('\n'))
  const [weaknesses, setWeaknesses] = useState((draft.weaknesses || []).join('\n'))
  const [suggestions, setSuggestions] = useState((draft.suggestions || []).join('\n'))
  const [learningPath, setLearningPath] = useState((draft.learning_path || []).join('\n'))
  const [concepts, setConcepts] = useState(
    (detail.concept_results || []).map((item) => ({
      concept_id: item.concept_id,
      concept_name: item.concept_name,
      strength: notes[item.concept_id]?.strength || '',
      weakness: notes[item.concept_id]?.weakness || '',
      recommendation: notes[item.concept_id]?.recommendation || '',
    })),
  )
  function updateConcept(conceptId, field, value) {
    setConcepts((items) =>
      items.map((item) => (item.concept_id === conceptId ? { ...item, [field]: value } : item)),
    )
  }
  return (
    <Card className="space-y-3 p-5">
      <div>
        <h3 className="font-semibold">Kết quả cuối cùng do giảng viên duyệt</h3>
        <p className="mt-1 text-sm text-sub">
          Nội dung AI bên dưới là bản nháp. Chỉnh sửa nếu cần; bản đã duyệt sẽ thay thế hoàn toàn
          kết quả tạm thời của người học.
        </p>
      </div>
      <form
        className="space-y-3"
        onSubmit={(event) => {
          event.preventDefault()
          onPublish({
            summary,
            strengths: lines(strengths),
            weaknesses: lines(weaknesses),
            suggestions: lines(suggestions),
            learning_path: lines(learningPath),
            concepts: concepts
              .map((item) => ({
                concept_id: item.concept_id,
                strength: item.strength.trim() || null,
                weakness: item.weakness.trim() || null,
                recommendation: item.recommendation.trim() || null,
              }))
              .filter((item) => item.strength || item.weakness || item.recommendation),
          })
        }}
      >
        <label className="block text-sm text-sub">
          Tóm tắt
          <textarea
            className={`${inputCls} mt-1 block min-h-24 w-full`}
            value={summary}
            onChange={(event) => setSummary(event.target.value)}
            required
          />
        </label>
        {[
          ['Điểm mạnh', strengths, setStrengths],
          ['Điểm cần cải thiện', weaknesses, setWeaknesses],
          ['Gợi ý luyện tập', suggestions, setSuggestions],
          ['Lộ trình học', learningPath, setLearningPath],
        ].map(([label, value, setter]) => (
          <label className="block text-sm text-sub" key={label}>
            {label} (mỗi dòng một mục)
            <textarea
              className={`${inputCls} mt-1 block min-h-20 w-full`}
              value={value}
              onChange={(event) => setter(event.target.value)}
              required
            />
          </label>
        ))}
        {concepts.length > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-semibold">Ghi chú theo khái niệm</p>
            {concepts.map((item) => (
              <div className="grid gap-2 rounded-lg border border-edge p-3 md:grid-cols-3" key={item.concept_id}>
                <p className="text-sm font-medium md:col-span-3">
                  {item.concept_name || `Khái niệm #${item.concept_id}`}
                </p>
                <input
                  className={inputCls}
                  placeholder="Điểm mạnh"
                  value={item.strength}
                  onChange={(event) => updateConcept(item.concept_id, 'strength', event.target.value)}
                />
                <input
                  className={inputCls}
                  placeholder="Cần cải thiện"
                  value={item.weakness}
                  onChange={(event) => updateConcept(item.concept_id, 'weakness', event.target.value)}
                />
                <input
                  className={inputCls}
                  placeholder="Gợi ý"
                  value={item.recommendation}
                  onChange={(event) =>
                    updateConcept(item.concept_id, 'recommendation', event.target.value)
                  }
                />
              </div>
            ))}
          </div>
        )}
        <button type="submit" className={btnPrimary} disabled={busy}>
          Lưu và duyệt
        </button>
      </form>
    </Card>
  )
}

function ReviewItem({
  item,
  busy,
  published,
  reviewAllowed,
  approve,
  practice = false,
  sessionId,
}) {
  const [score, setScore] = useState(item.automated_score ?? '')
  const [comments, setComments] = useState('')
  return (
    <Card className="space-y-3 p-4">
      <div className="flex flex-wrap items-center gap-2">
        <TypeBadge type={item.question_type} />
        <Badge>
          {item.review
            ? t('supervisor.approved')
            : item.question_type === 'mcq'
              ? t('supervisor.optionalReview')
              : t('supervisor.requiredReview')}
        </Badge>
      </div>
      <h3 className="whitespace-pre-wrap font-semibold text-ink">{item.prompt}</h3>
      <p className="text-sm text-sub">{t('supervisor.response')}</p>
      <pre
        className={`overflow-x-auto whitespace-pre-wrap break-words rounded bg-elev p-3 text-sm text-ink ${item.question_type === 'sql' ? 'font-mono' : 'font-sans'}`}
      >
        {item.sql_answer ??
          item.essay_answer ??
          item.options.find((o) => o.option_id === item.selected_option_id)?.option_text ??
          '—'}
      </pre>
      {item.reference_answer && (
        <details>
          <summary className="cursor-pointer text-sm text-cyan-300">
            {t('supervisor.expected')}
          </summary>
          <pre
            className={`mt-2 whitespace-pre-wrap break-words text-sm text-sub ${item.question_type === 'sql' ? 'font-mono' : 'font-sans'}`}
          >
            {item.reference_answer}
          </pre>
        </details>
      )}
      {item.rubrics.length > 0 && (
        <details>
          <summary className="cursor-pointer text-sm text-cyan-300">
            {t('supervisor.rubric')}
          </summary>
          <ul className="mt-2 space-y-2 text-sm text-sub">
            {item.rubrics.map((r) => (
              <li key={r.level_name}>
                {r.level_name} ({number(r.min_score)}–{number(r.max_score)}): {r.criteria}
              </li>
            ))}
          </ul>
        </details>
      )}
      <p className="text-sm text-sub">
        {practice ? 'Điểm hiện tại' : t('supervisor.suggested')}:{' '}
        {item.automated_score == null ? t('evidence.notGraded') : number(item.automated_score)} /{' '}
        {number(item.points)}
      </p>
      {item.automated_detail?.awaiting_instructor && !item.review && (
        <p role="status" className="text-sm text-amber-300">
          {t('local.essayManual')}
        </p>
      )}
      {item.automated_detail && (
        <details>
          <summary className="cursor-pointer text-sm text-cyan-300">
            {t('supervisor.automatedEvidence')}
          </summary>
          <AutomaticFeedback detail={item.automated_detail} />
        </details>
      )}
      {practice && item.question_type === 'sql' && (
        <SqlVerification sessionId={sessionId} item={item} />
      )}
      {item.review ? (
        <p className="text-sm text-sub">
          {t('supervisor.approved')}: {number(item.final_score)} / {number(item.points)} · #
          {item.review.reviewer_id} · {dateTime(item.review.reviewed_at)}
          <span className="block whitespace-pre-wrap">{item.review.comments}</span>
        </p>
      ) : (
        item.submitted_at &&
        !published &&
        reviewAllowed && (
          <form
            onSubmit={(e) => {
              e.preventDefault()
              approve({ score, comments: comments || null, revision: item.revision })
            }}
          >
            <fieldset
              disabled={busy || !['graded', 'failed', 'pending'].includes(item.grading_status)}
              className="flex flex-wrap items-end gap-3"
            >
              <label className="text-sm text-sub">
                {t('supervisor.finalScore')}
                <input
                  type="number"
                  min="0"
                  max={item.points}
                  step="0.01"
                  required
                  value={score}
                  onChange={(e) => setScore(e.target.value)}
                  className={`${inputCls} mt-1 block w-32`}
                />
              </label>
              <label className="grow text-sm text-sub">
                {practice ? 'Lý do điều chỉnh' : t('supervisor.comments')}
                <textarea
                  minLength={practice ? 3 : undefined}
                  maxLength={practice ? 1000 : 4000}
                  required={practice || ['failed', 'pending'].includes(item.grading_status)}
                  value={comments}
                  onChange={(e) => setComments(e.target.value)}
                  className={`${inputCls} mt-1 block w-full`}
                />
              </label>
              <button type="submit" className={practice ? btnGhost : btnPrimary}>
                {practice ? 'Lưu điểm điều chỉnh' : t('supervisor.approve')}
              </button>
            </fieldset>
          </form>
        )
      )}
    </Card>
  )
}

function SqlVerification({ sessionId, item }) {
  const [sql, setSql] = useState(item.sql_answer || '')
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  async function run() {
    if (busy) return
    setBusy(true)
    setResult(null)
    try {
      const r = await api.post(`/admin/grading-reviews/${sessionId}/run-sql`, {
        question_id: item.question_id,
        sql,
      })
      setResult(r.data)
    } catch {
      setResult({ success: false, error_message: 'Sandbox chưa sẵn sàng. Hãy thử lại.' })
    } finally {
      setBusy(false)
    }
  }
  return (
    <div className="space-y-3 rounded-xl border border-edge p-4">
      <label className="block text-sm text-sub">
        SQL kiểm tra (chỉ SELECT)
        <textarea
          className={`${inputCls} mt-2 block min-h-24 w-full font-mono`}
          value={sql}
          onChange={(e) => setSql(e.target.value)}
        />
      </label>
      <button type="button" className={btnGhost} disabled={busy || !sql.trim()} onClick={run}>
        {busy ? 'Đang chạy...' : 'Chạy SQL kiểm tra'}
      </button>
      {result && (
        <div role="status" className="space-y-2 text-sm text-sub">
          <p>
            {result.success
              ? `Thành công · ${result.row_count} dòng · ${result.execution_time_ms} ms`
              : 'Không chạy được truy vấn. Chỉ dùng SELECT hợp lệ trên schema của câu hỏi.'}
          </p>
          {result.success && (
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    {result.columns.map((name, i) => (
                      <th className="p-2" key={i}>
                        {name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.rows.map((row, i) => (
                    <tr key={i}>
                      {row.map((value, j) => (
                        <td className="p-2" key={j}>
                          {String(value ?? 'NULL')}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function AutomaticFeedback({ detail }) {
  return (
    <div className="mt-2 space-y-2 whitespace-pre-wrap break-words text-sm text-sub">
      {detail.feedback && <p>{detail.feedback}</p>}
      {detail.explanation && detail.explanation !== detail.feedback && <p>{detail.explanation}</p>}
      {detail.datasets_total != null && (
        <p>
          {t('evidence.passedChecks', {
            passed: number(detail.datasets_passed || 0),
            total: number(detail.datasets_total),
          })}
        </p>
      )}
      {detail.matched_criteria?.length > 0 && (
        <p>
          <strong>{t('evidence.criteria')}: </strong>
          {detail.matched_criteria.join(' · ')}
        </p>
      )}
      {detail.missing_concepts?.length > 0 && (
        <p>
          <strong>{t('evidence.missingConcepts')}: </strong>
          {detail.missing_concepts.join(' · ')}
        </p>
      )}
      {detail.evidence?.length > 0 && (
        <blockquote className="border-l-2 border-cyan-400/40 pl-3">
          {detail.evidence.join('\n')}
        </blockquote>
      )}
      {detail.missing_required_concepts?.length > 0 && (
        <p>
          <strong>{t('evidence.missingSql')}: </strong>
          {detail.missing_required_concepts.join(' · ')}
        </p>
      )}
    </div>
  )
}
