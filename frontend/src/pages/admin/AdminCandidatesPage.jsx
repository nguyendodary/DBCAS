import { useCallback, useEffect, useState } from 'react'
import api, { apiMessage } from '../../api'
import { EmptyState, ErrorState, Loading } from '../../components/States'
import { Badge, Card, CardTitle, Notice, PageHeader, StatusBadge, TypeBadge } from '../../components/ui'

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
    const r = await api.get(`/admin/question-candidates/${id}`).catch(() => null)
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

  const selCls =
    'ml-1 rounded-md border border-edge border-edge2 px-2 py-1.5 text-sm focus:border-cyan-400/60 focus:outline-none'

  return (
    <div className="space-y-4">
      <PageHeader
        title="AI question candidates"
        subtitle="Drafts stay outside the bank. The system checks completeness, duplicates, and (for SQL) executes the reference answer on the declared datasets before you review."
      />

      <Card className="p-4">
        <form onSubmit={generate} className="flex flex-wrap items-end gap-2 text-sm">
          <label className="text-sub">concept
            <select required value={gen.concept_id}
              onChange={(e) => setGen({ ...gen, concept_id: e.target.value })}
              className={selCls}>
              <option value="">—</option>
              {concepts.map((c) => (
                <option key={c.concept_id} value={c.concept_id}>{c.concept_code}</option>
              ))}
            </select>
          </label>
          <label className="text-sub">type
            <select value={gen.question_type}
              onChange={(e) => setGen({ ...gen, question_type: e.target.value })}
              className={selCls}>
              <option value="mcq">mcq</option>
              <option value="sql">sql</option>
              <option value="essay">essay</option>
            </select>
          </label>
          <label className="text-sub">count
            <input type="number" min="1" max="3" value={gen.count}
              onChange={(e) => setGen({ ...gen, count: e.target.value })}
              className="ml-1 w-14 rounded-md border border-edge border-edge2 px-2 py-1.5 text-sm focus:border-cyan-400/60 focus:outline-none" />
          </label>
          <button type="submit" disabled={busy}
            className="rounded-md bg-violet-600 px-3 py-1.5 font-medium text-white hover:bg-violet-500 disabled:opacity-50">
            {busy ? 'Generating…' : 'Generate'}
          </button>
          <select value={status} onChange={(e) => setStatus(e.target.value)}
            aria-label="Filter queue by status"
            className="ml-auto rounded-md border border-edge border-edge2 px-2 py-1.5 text-sm focus:border-cyan-400/60 focus:outline-none">
            <option value="">active queue</option>
            <option value="pending">pending</option>
            <option value="validated">validated</option>
            <option value="approved">approved</option>
            <option value="rejected">rejected</option>
          </select>
        </form>
      </Card>

      {notice && <Notice>{notice}</Notice>}
      {error && <ErrorState message={error} />}

      <div className="grid gap-4 lg:grid-cols-2">
        <div>
          {items === null ? (
            <Loading />
          ) : items.length === 0 ? (
            <EmptyState title="Queue is empty" />
          ) : (
            <Card className="overflow-hidden">
              <ul className="divide-y divide-edge text-sm">
                {items.map((c) => (
                  <li key={c.candidate_id} className="flex items-center justify-between gap-2 p-3">
                    <span className="flex flex-wrap items-center gap-1.5">
                      <span className="font-mono text-xs text-faint">#{c.candidate_id}</span>
                      <TypeBadge type={c.question_type} />
                      <Badge>{c.concept_code}</Badge>
                      <StatusBadge status={c.validation_status} />
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
                className="text-xs font-medium text-mute hover:underline">close</button>
            </CardTitle>
            <div className="p-4 text-sm">
              <p className="whitespace-pre-wrap rounded-lg bg-elev p-3 text-xs">
                {detail.payload?.prompt}
              </p>
              <pre className="mt-2 max-h-56 overflow-auto rounded-lg bg-elev p-3 text-xs text-sub">
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
              <div className="mt-3 flex gap-2 text-xs">
                <button type="button"
                  onClick={() => run(() => api.post(`/admin/question-candidates/${detail.candidate_id}/validate`), 'Re-checked.').then((r) => r && setDetail(r.data))}
                  className="rounded-md border border-edge border-edge2 px-2 py-1.5 text-sub hover:bg-white/5">
                  Re-run checks
                </button>
                {detail.validation_status === 'validated' && (
                  <button type="button"
                    onClick={() => run(() => api.post(`/admin/question-candidates/${detail.candidate_id}/approve`), 'Promoted into the bank.').then((r) => r && setDetail(r.data))}
                    className="rounded-md bg-emerald-600 px-2 py-1.5 font-medium text-white hover:bg-emerald-500">
                    Approve into bank
                  </button>
                )}
                {['pending', 'validated'].includes(detail.validation_status) && (
                  <button type="button"
                    onClick={() => run(() => api.post(`/admin/question-candidates/${detail.candidate_id}/reject`), 'Rejected.').then((r) => r && setDetail(r.data))}
                    className="rounded-md bg-rose-600 px-2 py-1.5 font-medium text-white hover:bg-rose-500">
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
