import { useCallback, useEffect, useState } from 'react'
import api, { apiMessage } from '../../api'
import AdminNav from '../../components/AdminNav'
import { EmptyState, ErrorState, Loading } from '../../components/States'

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
        className={`rounded px-2 py-0.5 text-xs font-medium ${
          check.ok ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
        }`}
        title={JSON.stringify(check, null, 1)}
      >
        {check.check}: {check.ok ? 'ok' : 'fail'}
      </span>
    )
  }

  return (
    <div>
      <AdminNav />
      <h1 className="text-xl font-semibold text-gray-900">AI question candidates</h1>
      <p className="mt-1 text-sm text-gray-500">
        Drafts stay outside the bank. The system checks completeness,
        duplicates, and (for SQL) executes the reference answer on the
        declared datasets before you review.
      </p>

      <form onSubmit={generate} className="mt-4 flex flex-wrap items-end gap-2 rounded-md border bg-white p-4 text-sm">
        <label className="text-gray-600">concept
          <select required value={gen.concept_id}
            onChange={(e) => setGen({ ...gen, concept_id: e.target.value })}
            className="ml-1 rounded border border-gray-300 px-2 py-1">
            <option value="">—</option>
            {concepts.map((c) => (
              <option key={c.concept_id} value={c.concept_id}>{c.concept_code}</option>
            ))}
          </select>
        </label>
        <label className="text-gray-600">type
          <select value={gen.question_type}
            onChange={(e) => setGen({ ...gen, question_type: e.target.value })}
            className="ml-1 rounded border border-gray-300 px-2 py-1">
            <option value="mcq">mcq</option>
            <option value="sql">sql</option>
            <option value="essay">essay</option>
          </select>
        </label>
        <label className="text-gray-600">count
          <input type="number" min="1" max="3" value={gen.count}
            onChange={(e) => setGen({ ...gen, count: e.target.value })}
            className="ml-1 w-14 rounded border border-gray-300 px-2 py-1" />
        </label>
        <button type="submit" disabled={busy}
          className="rounded bg-purple-600 px-3 py-1 font-medium text-white hover:bg-purple-700 disabled:opacity-50">
          {busy ? 'Generating…' : 'Generate'}
        </button>
        <select value={status} onChange={(e) => setStatus(e.target.value)}
          className="ml-auto rounded border border-gray-300 px-2 py-1">
          <option value="">active queue</option>
          <option value="pending">pending</option>
          <option value="validated">validated</option>
          <option value="approved">approved</option>
          <option value="rejected">rejected</option>
        </select>
      </form>

      {notice && <p role="status" className="mt-3 rounded bg-green-50 p-2 text-sm text-green-700">{notice}</p>}
      {error && <div className="mt-3"><ErrorState message={error} /></div>}

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <div>
          {items === null ? (
            <Loading />
          ) : items.length === 0 ? (
            <EmptyState title="Queue is empty" />
          ) : (
            <ul className="divide-y rounded-md border bg-white text-sm">
              {items.map((c) => (
                <li key={c.candidate_id} className="flex items-center justify-between p-3">
                  <span>
                    <span className="font-mono text-xs text-gray-400">#{c.candidate_id}</span>{' '}
                    <span className="rounded bg-gray-100 px-1.5 py-0.5 text-xs uppercase">{c.question_type}</span>{' '}
                    <span className="text-xs text-gray-600">{c.concept_code}</span>{' '}
                    <span className={`rounded px-1.5 py-0.5 text-xs font-medium ${
                      c.validation_status === 'validated' ? 'bg-green-50 text-green-700'
                      : c.validation_status === 'approved' ? 'bg-blue-50 text-blue-700'
                      : c.validation_status === 'rejected' ? 'bg-red-50 text-red-700'
                      : 'bg-amber-50 text-amber-700'
                    }`}>{c.validation_status}</span>
                  </span>
                  <button type="button" onClick={() => open(c.candidate_id)}
                    className="text-xs text-blue-600 hover:underline">
                    Review
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {detail && (
          <section className="rounded-md border bg-white p-4 text-sm">
            <div className="flex items-center justify-between">
              <p className="font-medium">Candidate #{detail.candidate_id}</p>
              <button type="button" onClick={() => setDetail(null)}
                className="text-xs text-gray-500">close</button>
            </div>
            <p className="mt-2 whitespace-pre-wrap rounded bg-gray-50 p-2 text-xs">
              {detail.payload?.prompt}
            </p>
            <pre className="mt-2 max-h-56 overflow-auto rounded bg-gray-50 p-2 text-xs text-gray-600">
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
              <p className="mt-2 text-xs text-gray-500">
                promoted → question #{detail.promoted_question_id}
              </p>
            )}
            <div className="mt-3 flex gap-2 text-xs">
              <button type="button"
                onClick={() => run(() => api.post(`/admin/question-candidates/${detail.candidate_id}/validate`), 'Re-checked.').then((r) => r && setDetail(r.data))}
                className="rounded border border-gray-300 px-2 py-1 text-gray-700">
                Re-run checks
              </button>
              {detail.validation_status === 'validated' && (
                <button type="button"
                  onClick={() => run(() => api.post(`/admin/question-candidates/${detail.candidate_id}/approve`), 'Promoted into the bank.').then((r) => r && setDetail(r.data))}
                  className="rounded bg-green-600 px-2 py-1 text-white hover:bg-green-700">
                  Approve into bank
                </button>
              )}
              {['pending', 'validated'].includes(detail.validation_status) && (
                <button type="button"
                  onClick={() => run(() => api.post(`/admin/question-candidates/${detail.candidate_id}/reject`), 'Rejected.').then((r) => r && setDetail(r.data))}
                  className="rounded bg-red-600 px-2 py-1 text-white hover:bg-red-700">
                  Reject
                </button>
              )}
            </div>
          </section>
        )}
      </div>
    </div>
  )
}
