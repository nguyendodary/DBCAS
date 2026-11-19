import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import api, { apiMessage } from '../../api'
import { useAuth } from '../../auth'
import { dateTime, number, t, typeLabel } from '../../i18n'
import { AdminPageHeader } from '../../components/admin'
import { EmptyState, ErrorState, Loading } from '../../components/States'
import { Badge, Card, btnGhost, btnPrimary, inputCls } from '../../components/ui'

const queuePath = '/admin/review-requests'
const statuses = ['REQUESTED', 'IN_REVIEW', 'REGRADED', 'REJECTED', 'EXPIRED']
const categories = ['WRONG_ANSWER', 'WRONG_QUESTION', 'AMBIGUOUS', 'TECHNICAL']
const limit = 100
const label = (key, values) => t(`adminReview.${key}`, values)

export default function AdminReviewQueue() {
  const [filter, setFilter] = useState('')
  const [offset, setOffset] = useState(0)
  const [refreshes, refresh] = useState(0)
  const [cases, setCases] = useState(null)
  const [caseId, setCaseId] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    const controller = new AbortController()
    api
      .get(queuePath, {
        params: { status: filter || undefined, offset, limit },
        signal: controller.signal,
      })
      .then(({ data }) => {
        if (!controller.signal.aborted) {
          setCases(data)
          setError(null)
        }
      })
      .catch((e) => {
        if (!controller.signal.aborted) setError(apiMessage(e))
      })
    return () => controller.abort()
  }, [filter, offset, refreshes])

  function refreshQueue() {
    refresh((value) => value + 1)
  }

  return (
    <div className="space-y-5">
      <AdminPageHeader title={label('title')}>
        <Link className={btnGhost} to="/admin/grading">
          {t('supervisor.reviewTitle')}
        </Link>
        <button type="button" className={btnGhost} onClick={refreshQueue}>
          {t('dashboard.refresh')}
        </button>
      </AdminPageHeader>
      <label className="flex flex-wrap items-center gap-2">
        {label('filter')}
        <select
          className={inputCls}
          value={filter}
          onChange={(event) => {
            setFilter(event.target.value)
            setOffset(0)
          }}
        >
          <option value="">{label('all')}</option>
          {statuses.map((status) => (
            <option key={status} value={status}>
              {label(status)}
            </option>
          ))}
        </select>
      </label>
      {error && <ErrorState message={error} onRetry={refreshQueue} />}
      {cases === null && !error && <Loading />}
      {cases?.length === 0 && <EmptyState title={label('empty')} />}
      {cases?.length > 0 && (
        <Card className="divide-y divide-edge">
          {cases.map((item) => (
            <button
              type="button"
              key={item.review_request_id}
              aria-pressed={item.review_request_id === caseId}
              className="flex w-full flex-wrap justify-between gap-2 p-4 text-left hover:bg-surface-hover"
              onClick={() => setCaseId(item.review_request_id)}
            >
              <span>
                {label('case', { id: item.review_request_id })} · {item.learner_name}
              </span>
              <Badge>{label(item.status)}</Badge>
            </button>
          ))}
        </Card>
      )}
      {(offset > 0 || cases?.length === limit) && (
        <nav className="flex gap-3" aria-label={t('supervisor.reviewPages')}>
          <button
            type="button"
            className={btnGhost}
            disabled={!offset}
            onClick={() => setOffset(offset - limit)}
          >
            {t('assessment.prevPage')}
          </button>
          <button
            type="button"
            className={btnGhost}
            disabled={cases?.length !== limit}
            onClick={() => setOffset(offset + limit)}
          >
            {t('assessment.nextPage')}
          </button>
        </nav>
      )}
      {caseId && (
        <ReviewCase key={caseId} id={caseId} refreshes={refreshes} onChange={refreshQueue} />
      )}
    </div>
  )
}

function ReviewCase({ id, refreshes, onChange }) {
  const { account } = useAuth()
  const [detail, setDetail] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [note, setNote] = useState('')
  const [confirmed, setConfirmed] = useState({})
  const guard = useRef(false)
  const path = queuePath + '/' + id

  useEffect(() => {
    const controller = new AbortController()
    api
      .get(path, { signal: controller.signal })
      .then(({ data }) => {
        if (!controller.signal.aborted) {
          setDetail(data)
          setError(null)
        }
      })
      .catch((e) => {
        if (!controller.signal.aborted) setError(apiMessage(e))
      })
    return () => controller.abort()
  }, [path, refreshes])

  async function mutate(endpoint, data, confirmationId) {
    if (guard.current) return
    guard.current = true
    setBusy(true)
    setError(null)
    try {
      const response = await api.post(endpoint, data)
      if (confirmationId) setConfirmed((state) => ({ ...state, [confirmationId]: true }))
      else setDetail(response.data)
      setNote('')
      onChange()
    } catch (e) {
      setError(apiMessage(e))
    } finally {
      guard.current = false
      setBusy(false)
    }
  }

  if (!detail) return error ? <ErrorState message={error} onRetry={onChange} /> : <Loading />
  const holder = detail.status === 'IN_REVIEW' && detail.claimed_by === account.account_id
  const editable = holder && !detail.regraded_result_version_id
  const validNote = [...note.trim()].length >= 10
  const decide = (outcome) =>
    mutate(path + '/decision', { outcome, note: note.trim(), expected_revision: detail.revision })

  return (
    <Card className="space-y-4 p-5">
      <h2 className="font-semibold">
        {label('case', { id })} · {detail.learner_name}
      </h2>
      <p role="status" className="text-sub">
        {label(detail.status)}
        {detail.analysis_status && ' · ' + label(detail.analysis_status)}
      </p>
      <p className="whitespace-pre-wrap break-words">{detail.reason}</p>
      {detail.claim_expires_at && (
        <p>{label('claimExpiry', { time: dateTime(detail.claim_expires_at) })}</p>
      )}
      {detail.resolution_note && (
        <p className="whitespace-pre-wrap break-words">{detail.resolution_note}</p>
      )}
      {error && <ErrorState message={error} onRetry={onChange} />}
      <div className="flex flex-wrap gap-2">
        <Link className={btnGhost} to={'/admin/grading/' + detail.session_id}>
          {label('openResult')}
        </Link>
        {detail.status === 'REQUESTED' && (
          <button
            type="button"
            className={btnPrimary}
            disabled={busy}
            onClick={() => mutate(path + '/claim', { expected_revision: detail.revision })}
          >
            {label('claim')}
          </button>
        )}
        {holder && detail.analysis_status === 'ANALYSIS_FAILED' && (
          <button
            type="button"
            className={btnPrimary}
            disabled={busy}
            onClick={() => mutate(path + '/analysis-retry')}
          >
            {label('retry')}
          </button>
        )}
      </div>
      {detail.question_reports.length > 0 && (
        <ul className="space-y-2">
          {detail.question_reports.map((report) => (
            <li key={report.question_report_id}>
              <p>
                {label(report.category)} · {label(report.status)}
              </p>
              <p className="whitespace-pre-wrap break-words">{report.details}</p>
              {editable && report.status === 'OPEN' && (
                <div className="flex flex-wrap gap-2">
                  {['ACCEPTED', 'REJECTED'].map((status) => (
                    <button
                      type="button"
                      key={status}
                      className={btnGhost}
                      disabled={busy || !validNote}
                      onClick={() =>
                        mutate(
                          '/admin/question-reports/' + report.question_report_id + '/resolve',
                          { status, note: note.trim() },
                        )
                      }
                    >
                      {label(status === 'ACCEPTED' ? 'acceptReport' : 'rejectReport')}
                    </button>
                  ))}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
      {detail.deviations.length > 0 && (
        <ul className="space-y-2">
          {detail.deviations.map((deviation) => (
            <li key={deviation.deviation_id}>
              <span>
                {label('deviation', {
                  before: number(deviation.ai_score),
                  after: number(deviation.reviewed_score),
                })}
              </span>
              {confirmed[deviation.deviation_id] && (
                <span role="status"> · {label('confirmed')}</span>
              )}
              {detail.status === 'IN_REVIEW' &&
                deviation.second_reviewer_id === account.account_id && (
                  <button
                    type="button"
                    className={btnGhost}
                    disabled={busy || confirmed[deviation.deviation_id]}
                    onClick={() =>
                      mutate(
                        path + '/deviations/' + deviation.deviation_id + '/confirm',
                        undefined,
                        deviation.deviation_id,
                      )
                    }
                  >
                    {label('confirm')}
                  </button>
                )}
            </li>
          ))}
        </ul>
      )}
      {editable && (
        <>
          <label className="block space-y-1">
            <span>{label('note')}</span>
            <textarea
              className={inputCls}
              value={note}
              maxLength={2000}
              disabled={busy}
              onChange={(event) => setNote(event.target.value)}
            />
          </label>
          <ReportForm
            detail={detail}
            path={path}
            busy={busy}
            validNote={validNote}
            note={note.trim()}
            mutate={mutate}
            adminId={account.account_id}
          />
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              className={btnGhost}
              disabled={busy || !validNote}
              onClick={() => decide('REJECT')}
            >
              {label('reject')}
            </button>
            <button
              type="button"
              className={btnPrimary}
              disabled={busy || !validNote}
              onClick={() => decide('APPROVE')}
            >
              {label('approve')}
            </button>
          </div>
        </>
      )}
    </Card>
  )
}

function ReportForm({ detail, path, busy, validNote, note, mutate, adminId }) {
  const [options, setOptions] = useState(null)
  const [attemptId, setAttemptId] = useState('')
  const [category, setCategory] = useState(categories[0])
  const [reviewer, setReviewer] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const selected = options?.items.find((item) => String(item.attempt_id) === attemptId)
  const accepted = detail.question_reports.some(
    (report) => report.attempt_id === selected?.attempt_id && report.status === 'ACCEPTED',
  )
  const changed = detail.deviations.some(
    (deviation) =>
      deviation.attempt_id === selected?.attempt_id && !deviation.criterion_snapshot_id,
  )
  const needsConfirmation =
    accepted &&
    selected.points > 0 &&
    (selected.final_score ?? selected.automated_score ?? 0) / selected.points > 0.3

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const [grading, accounts] = await Promise.all([
        api.get('/admin/grading-reviews/' + detail.session_id),
        api.get('/admin/accounts'),
      ])
      setOptions({
        items: grading.data.items.filter(({ question_type }) =>
          ['mcq', 'sql'].includes(question_type),
        ),
        admins: accounts.data.filter(
          (item) =>
            item.account_id !== adminId &&
            item.status === 'active' &&
            item.roles.includes('Administrator'),
        ),
      })
    } catch (e) {
      setError(apiMessage(e))
    } finally {
      setLoading(false)
    }
  }

  if (!options)
    return (
      <div>
        {error && <ErrorState message={error} />}
        <button type="button" className={btnGhost} disabled={loading} onClick={load}>
          {label('loadQuestions')}
        </button>
      </div>
    )
  return (
    <div className="space-y-2">
      <label className="block">
        {label('question')}
        <select
          className={inputCls}
          aria-label={label('question')}
          value={attemptId}
          disabled={busy}
          onChange={(event) => setAttemptId(event.target.value)}
        >
          <option value="">{label('chooseQuestion')}</option>
          {options.items.map((item, index) => (
            <option key={item.attempt_id} value={item.attempt_id}>
              #{index + 1} · {typeLabel(item.question_type)} · {item.prompt}
            </option>
          ))}
        </select>
      </label>
      {selected && !accepted && (
        <div className="flex flex-wrap items-end gap-2">
          <label>
            {label('category')}
            <select
              className={inputCls}
              value={category}
              onChange={(event) => setCategory(event.target.value)}
            >
              {categories.map((value) => (
                <option key={value} value={value}>
                  {label(value)}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            className={btnGhost}
            disabled={busy || !validNote}
            onClick={() =>
              mutate(path + '/question-reports', {
                attempt_id: selected.attempt_id,
                category,
                details: note,
              })
            }
          >
            {label('addReport')}
          </button>
        </div>
      )}
      {needsConfirmation && !changed && (
        <div className="flex flex-wrap items-end gap-2">
          {options.admins.length > 0 ? (
            <label>
              {label('secondAdmin')}
              <select
                className={inputCls}
                aria-label={label('secondAdmin')}
                value={reviewer}
                onChange={(event) => setReviewer(event.target.value)}
              >
                <option value="">{label('chooseAdmin')}</option>
                {options.admins.map((item) => (
                  <option key={item.account_id} value={item.account_id}>
                    {item.name || item.email}
                  </option>
                ))}
              </select>
            </label>
          ) : (
            <p>{label('longNote')}</p>
          )}
          <button
            type="button"
            className={btnGhost}
            disabled={
              busy || !validNote || (options.admins.length ? !reviewer : [...note].length < 120)
            }
            onClick={() =>
              mutate(path + '/deviations', {
                attempt_id: selected.attempt_id,
                reviewed_score: '0',
                reason: note,
                ...(reviewer ? { second_reviewer_id: Number(reviewer) } : {}),
              })
            }
          >
            {label('requestConfirmation')}
          </button>
        </div>
      )}
    </div>
  )
}
