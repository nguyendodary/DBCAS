import { resolveMessage } from '../../i18n'
import { useCallback, useEffect, useState } from 'react'
import api, { apiMessage } from '../../api'
import { ActionSpinner, EmptyState, ErrorState, Loading } from '../../components/States'
import { Badge, Card, CardTitle, Notice, PageHeader, StatusBadge, TypeBadge, btnGhost, btnPrimary, inputCls } from '../../components/ui'

// UC10 — AI question candidates: generation, deterministic check results,
// and the approve-into-bank / reject review actions.
export default function AdminCandidatesPage() {
  const [items, setItems] = useState(null)
  const [detail, setDetail] = useState(null) // expanded candidate
  const [concepts, setConcepts] = useState([])
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [status, setStatus] = useState('')
  const [gen, setGen] = useState({ concept_id: '', question_type: 'mcq', count: 1 })
  const [busy, setBusy] = useState(false)

  const load = useCallback(() => {
    setError('')
    Promise.all([
      api.get('/admin/question-candidates', { params: status ? { status } : {} }),
      api.get('/admin/concepts'),
    ])
      .then(([c, k]) => {
        setItems(c.data)
        setConcepts(k.data)
      })
      .catch((e) => {
        setError(apiMessage(e))
        setItems([])
      })
  }, [status])

  useEffect(load, [load])

  async function run(fn, okMsg) {
    setError('')
    setNotice('')
    try {
      const r = await fn()
      if (okMsg) setNotice(okMsg)
      load()
      return r
    } catch (e) {
      setError(apiMessage(e))
      return null
    }
  }

  async function generate(e) {
    e.preventDefault()
    setBusy(true)
    const r = await run(
      () => api.post('/admin/question-candidates/generate', {
        concept_id: Number(gen.concept_id),
        question_type: gen.question_type,
        count: Number(gen.count),
      }),
      'Candidates generated and checked.'
    )
    if (r?.data?.[0]) setDetail(r.data[0])
    setBusy(false)
  }

  async function open(id) {
    const r = await api.get(`/admin/question-candidates/${id}`).catch((e) => {
      setError(apiMessage(e, 'Could not open the candidate'))
      return null
    })
    if (r) setDetail(r.data)
  }

  function CheckBadge({ check }) {
    return (
      <span
        className={`rounded-full px-2 py-0.5 text-xs font-medium ${
          check.ok ? 'bg-emerald-500/10 text-emerald-300' : 'bg-rose-500/10 text-rose-300'
        }`}
        title={JSON.stringify(check, null, 1)}
      >
        {check.check}: {check.ok ? 'ok' : 'fail'}
      </span>
    )
  }

  const selCls = inputCls

  return (
    <div className="space-y-4">
      <PageHeader
        title="AI question candidates"
        subtitle="Generate, validate, and review drafts before they enter the question bank."
      />

      <Card className="p-4 sm:p-5">
        <h2 className="mb-3 text-sm font-semibold text-ink">Generate candidates</h2>
        <form onSubmit={generate} className="grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)_6rem_auto] lg:items-end">
          <label className="grid gap-1.5 text-xs font-medium text-sub">Concept
            <select required value={gen.concept_id}
              onChange={(e) => setGen({ ...gen, concept_id: e.target.value })}
              className={selCls}>
              <option value="">Select concept</option>
              {concepts.map((c) => (
                <option key={c.concept_id} value={c.concept_id}>{c.concept_code}</option>
              ))}
            </select>
          </label>
          <label className="grid gap-1.5 text-xs font-medium text-sub">Type
            <select value={gen.question_type}
              onChange={(e) => setGen({ ...gen, question_type: e.target.value })}
              className={selCls}>
              <option value="mcq">mcq</option>
              <option value="sql">sql</option>
              <option value="essay">essay</option>
            </select>
          </label>
          <label className="grid gap-1.5 text-xs font-medium text-sub">Count
            <input type="number" min="1" max="3" value={gen.count}
              onChange={(e) => setGen({ ...gen, count: e.target.value })}
              className={selCls} />
          </label>
          <button type="submit" disabled={busy}
            className={btnPrimary}>
            {busy && <ActionSpinner />}
            {busy ? 'Generating…' : 'Generate'}
          </button>
        </form>
      </Card>

      {notice && <Notice>{notice}</Notice>}
      {error && <ErrorState message={resolveMessage(error)} />}

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.05fr)]">
        <div>
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-sm font-semibold text-ink">Review queue {items && <span className="ml-1 text-mute">({items.length})</span>}</h2>
            <select value={status} onChange={(e) => setStatus(e.target.value)}
              aria-label="Filter queue by status" className={`${selCls} w-auto`}>
              <option value="">Active queue</option>
              <option value="pending">Pending</option>
              <option value="validated">Validated</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
          {items === null ? (
            <Loading />
          ) : items.length === 0 ? (
            <EmptyState title="Queue is empty">Generate candidates above or choose another status to review.</EmptyState>
          ) : (
            <Card className="overflow-hidden">
              <ul className="divide-y divide-edge text-sm">
                {items.map((c) => (
                  <li key={c.candidate_id} className={`flex items-center justify-between gap-3 px-4 py-3 transition-colors hover:bg-white/[0.035] ${detail?.candidate_id === c.candidate_id ? 'bg-cyan-400/[0.055]' : ''}`}>
                    <span className="flex flex-wrap items-center gap-1.5">
                      <span className="font-mono text-xs text-faint">#{c.candidate_id}</span>
                      <TypeBadge type={c.question_type} />
                      <Badge>{c.concept_code}</Badge>
                      <StatusBadge status={c.validation_status} />
                      {c.promoted_question_id && <Badge tone="green">Added to bank</Badge>}
                    </span>
                    <button type="button" onClick={() => open(c.candidate_id)}
                      className="shrink-0 text-xs font-medium text-cyan-300 hover:underline">
                      Review
                    </button>
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </div>

        {detail && (
          <Card className="self-start overflow-hidden">
            <CardTitle title={`Candidate #${detail.candidate_id}`}>
              <button type="button" onClick={() => setDetail(null)}
                className="text-xs font-medium text-mute hover:underline">Close</button>
            </CardTitle>
            <div className="p-4 text-sm">
              <p className="whitespace-pre-wrap rounded-lg bg-elev p-3 text-xs">
                {detail.payload?.prompt}
              </p>
              <pre tabIndex={0} role="region" aria-label="Candidate question content" className="mt-2 max-h-56 overflow-auto rounded-lg bg-elev p-3 text-xs text-sub">
                {JSON.stringify(detail.payload, null, 1)}
              </pre>
              {detail.validation_detail?.checks && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {detail.validation_detail.checks.map((c, i) => (
                    <CheckBadge key={i} check={c} />
                  ))}
                </div>
              )}
              {detail.promoted_question_id && (
                <p className="mt-2 text-xs text-mute">
                  promoted → question #{detail.promoted_question_id}
                </p>
              )}
              <div className="mt-4 flex flex-wrap gap-2 text-xs">
                <button type="button"
                  onClick={() => run(() => api.post(`/admin/question-candidates/${detail.candidate_id}/validate`), 'Re-checked.').then((r) => r && setDetail(r.data))}
                  className={btnGhost}>
                  Re-run checks
                </button>
                {detail.validation_status === 'validated' && !detail.promoted_question_id && (
                  <button type="button"
                    onClick={() => run(() => api.post(`/admin/question-candidates/${detail.candidate_id}/approve`), 'Promoted into the bank.').then((r) => r && setDetail(r.data))}
                    className={btnPrimary}>
                    Approve into bank
                  </button>
                )}
                {['pending', 'validated'].includes(detail.validation_status) && !detail.promoted_question_id && (
                  <button type="button"
                    onClick={() => run(() => api.post(`/admin/question-candidates/${detail.candidate_id}/reject`), 'Rejected.').then((r) => r && setDetail(r.data))}
                    className="rounded-md border border-rose-400/25 bg-rose-400/10 px-3 py-2 font-medium text-rose-200 transition-colors hover:bg-rose-400/15">
                    Reject
                  </button>
                )}
              </div>
            </div>
          </Card>
        )}
      </div>
    </div>
  )
}
