import { useCallback, useEffect, useState } from 'react'
import api, { apiMessage } from '../../api'
import AdminNav from '../../components/AdminNav'
import { EmptyState, ErrorState, Loading } from '../../components/States'
import { Badge, Card, CardTitle, Notice, PageHeader, StatusBadge, inputCls } from '../../components/ui'

const EMPTY = {
  title: '',
  description: '',
  max_questions: 13,
  duration_min: 60,
  target_mcq: 10,
  target_sql: 2,
  target_essay: 1,
  concepts: [{ concept_id: '', min_difficulty: 1, max_difficulty: 5, target_pct: '60.00' }],
}

const numCls =
  'w-16 rounded-md border border-gray-300 px-1.5 py-1.5 text-sm focus:border-blue-500 focus:outline-none'

// UC09 — adaptive assessment configuration (draft → active → closed).
export default function AdminAssessmentsPage() {
  const [items, setItems] = useState(null)
  const [concepts, setConcepts] = useState([])
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [form, setForm] = useState(EMPTY)
  const [editing, setEditing] = useState(null)
  const [busy, setBusy] = useState(false)

  const load = useCallback(() => {
    setError('')
    Promise.all([
      api.get('/admin/assessments'),
      api.get('/admin/concepts'),
    ])
      .then(([a, c]) => {
        setItems(a.data)
        setConcepts(c.data)
      })
      .catch((e) => {
        setError(apiMessage(e))
        setItems([])
      })
  }, [])

  useEffect(load, [load])

  async function run(fn, okMsg) {
    setError('')
    setNotice('')
    try {
      await fn()
      if (okMsg) setNotice(okMsg)
      load()
    } catch (e) {
      setError(apiMessage(e))
    }
  }

  function setConceptRow(i, key, value) {
    setForm((f) => {
      const concepts = f.concepts.map((c, j) => (j === i ? { ...c, [key]: value } : c))
      return { ...f, concepts }
    })
  }

  async function save(e) {
    e.preventDefault()
    setBusy(true)
    try {
      const payload = {
        title: form.title,
        description: form.description || null,
        max_questions: Number(form.max_questions),
        duration_min: Number(form.duration_min),
        target_mcq: Number(form.target_mcq),
        target_sql: Number(form.target_sql),
        target_essay: Number(form.target_essay),
        concepts: form.concepts.map((c) => ({
          concept_id: Number(c.concept_id),
          min_difficulty: Number(c.min_difficulty),
          max_difficulty: Number(c.max_difficulty),
          target_pct: String(c.target_pct),
        })),
      }
      if (editing) {
        await run(() => api.put(`/admin/assessments/${editing}`, payload), 'Assessment updated.')
      } else {
        await run(() => api.post('/admin/assessments', payload), 'Assessment created (draft).')
      }
      setEditing(null)
      setForm(EMPTY)
    } finally {
      setBusy(false)
    }
  }

  function startEdit(a) {
    api.get(`/admin/assessments/${a.assessment_id}`).then((r) => {
      const d = r.data
      setEditing(a.assessment_id)
      setForm({
        title: d.title,
        description: d.description || '',
        max_questions: d.max_questions,
        duration_min: d.duration_min,
        target_mcq: d.target_mcq,
        target_sql: d.target_sql,
        target_essay: d.target_essay,
        concepts: d.concepts.map((c) => ({
          concept_id: c.concept_id,
          min_difficulty: c.min_difficulty,
          max_difficulty: c.max_difficulty,
          target_pct: c.target_pct,
        })),
      })
      window.scrollTo({ top: 0, behavior: 'smooth' })
    })
  }

  return (
    <div className="space-y-4">
      <AdminNav />
      <PageHeader
        title="Adaptive assessments"
        subtitle="Configurations pick target concepts and difficulty ranges — never fixed question sets. Items are chosen adaptively at runtime."
      />

      <Card className="overflow-hidden">
        <CardTitle title={editing ? `Edit assessment #${editing}` : 'New assessment'} />
        <form onSubmit={save} className="grid gap-3 p-4 text-sm">
          <div className="grid gap-2 sm:grid-cols-2">
            <input required placeholder="Title" value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className={inputCls} />
            <input placeholder="Description" value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className={inputCls} />
          </div>
          <div className="grid gap-2 sm:grid-cols-5 text-gray-600">
            <label className="flex items-center gap-1.5">max q
              <input type="number" min="1" max="13" value={form.max_questions}
                onChange={(e) => setForm({ ...form, max_questions: e.target.value })}
                className={numCls} /></label>
            <label className="flex items-center gap-1.5">minutes
              <input type="number" min="5" value={form.duration_min}
                onChange={(e) => setForm({ ...form, duration_min: e.target.value })}
                className={numCls} /></label>
            <label className="flex items-center gap-1.5">mcq
              <input type="number" min="0" value={form.target_mcq}
                onChange={(e) => setForm({ ...form, target_mcq: e.target.value })}
                className={numCls} /></label>
            <label className="flex items-center gap-1.5">sql
              <input type="number" min="0" value={form.target_sql}
                onChange={(e) => setForm({ ...form, target_sql: e.target.value })}
                className={numCls} /></label>
            <label className="flex items-center gap-1.5">essay
              <input type="number" min="0" value={form.target_essay}
                onChange={(e) => setForm({ ...form, target_essay: e.target.value })}
                className={numCls} /></label>
          </div>

          <p className="mt-1 text-xs font-medium uppercase tracking-wide text-gray-500">Target concepts</p>
          {form.concepts.map((c, i) => (
            <div key={i} className="flex flex-wrap items-center gap-2">
              <select required value={c.concept_id}
                onChange={(e) => setConceptRow(i, 'concept_id', e.target.value)}
                className="rounded-md border border-gray-300 px-2 py-1.5 text-sm focus:border-blue-500 focus:outline-none">
                <option value="">— concept —</option>
                {concepts.map((k) => (
                  <option key={k.concept_id} value={k.concept_id}>{k.concept_code}</option>
                ))}
              </select>
              <label className="text-xs text-gray-600">difficulty
                <input type="number" min="1" max="5" value={c.min_difficulty}
                  onChange={(e) => setConceptRow(i, 'min_difficulty', e.target.value)}
                  className="ml-1 w-12 rounded-md border border-gray-300 px-1.5 py-1 focus:border-blue-500 focus:outline-none" />
                {' '}–{' '}
                <input type="number" min="1" max="5" value={c.max_difficulty}
                  onChange={(e) => setConceptRow(i, 'max_difficulty', e.target.value)}
                  className="w-12 rounded-md border border-gray-300 px-1.5 py-1 focus:border-blue-500 focus:outline-none" />
              </label>
              <label className="text-xs text-gray-600">benchmark %
                <input value={c.target_pct}
                  onChange={(e) => setConceptRow(i, 'target_pct', e.target.value)}
                  className="ml-1 w-16 rounded-md border border-gray-300 px-1.5 py-1 focus:border-blue-500 focus:outline-none" />
              </label>
              <button type="button"
                onClick={() => setForm((f) => ({ ...f, concepts: f.concepts.filter((_, j) => j !== i) }))}
                disabled={form.concepts.length <= 1}
                className="text-xs font-medium text-red-600 hover:underline disabled:opacity-40">
                remove
              </button>
            </div>
          ))}
          <button type="button"
            onClick={() => setForm((f) => ({
              ...f,
              concepts: [...f.concepts, { concept_id: '', min_difficulty: 1, max_difficulty: 5, target_pct: '60.00' }],
            }))}
            className="w-fit text-xs font-medium text-blue-600 hover:underline">
            + add concept
          </button>
          <div className="flex gap-2">
            <button type="submit" disabled={busy}
              className="rounded-md bg-blue-600 px-3 py-1.5 font-medium text-white hover:bg-blue-700 disabled:opacity-50">
              {busy ? 'Saving…' : editing ? 'Save changes' : 'Create draft'}
            </button>
            {editing && (
              <button type="button" onClick={() => { setEditing(null); setForm(EMPTY) }}
                className="rounded-md border border-gray-300 px-3 py-1.5 text-gray-700 hover:bg-gray-50">Cancel</button>
            )}
          </div>
        </form>
      </Card>

      {notice && <Notice>{notice}</Notice>}
      {error && <ErrorState message={error} />}

      {items === null ? (
        <Loading />
      ) : items.length === 0 ? (
        <EmptyState title="No assessments configured" />
      ) : (
        <Card className="overflow-hidden">
          <ul className="divide-y text-sm">
            {items.map((a) => (
              <li key={a.assessment_id} className="p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium text-gray-900">{a.title}</span>
                  <StatusBadge status={a.status} />
                  <Badge>
                    {a.max_questions}q · {a.duration_min}min · {a.target_count} concept
                    {a.target_count === 1 ? '' : 's'} · {a.session_count} session
                    {a.session_count === 1 ? '' : 's'}
                  </Badge>
                  <span className="ml-auto flex gap-3 text-xs">
                    {a.status === 'draft' && (
                      <>
                        <button type="button" onClick={() => startEdit(a)} className="font-medium text-blue-600 hover:underline">Edit</button>
                        <button type="button"
                          onClick={() => run(() => api.patch(`/admin/assessments/${a.assessment_id}`, { status: 'active' }), 'Activated.')}
                          className="font-medium text-green-600 hover:underline">Activate</button>
                        <button type="button"
                          onClick={() => run(() => api.delete(`/admin/assessments/${a.assessment_id}`), 'Deleted.')}
                          className="font-medium text-red-600 hover:underline">Delete</button>
                      </>
                    )}
                    {a.status === 'active' && (
                      <button type="button"
                        onClick={() => run(() => api.patch(`/admin/assessments/${a.assessment_id}`, { status: 'closed' }), 'Closed.')}
                        className="font-medium text-amber-600 hover:underline">Close</button>
                    )}
                    {a.status === 'closed' && (
                      <button type="button"
                        onClick={() => run(() => api.patch(`/admin/assessments/${a.assessment_id}`, { status: 'draft' }), 'Back to draft.')}
                        className="font-medium text-blue-600 hover:underline">Re-draft</button>
                    )}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  )
}
