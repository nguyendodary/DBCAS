import { useCallback, useEffect, useState } from 'react'
import api, { apiMessage } from '../../api'
import AdminNav from '../../components/AdminNav'
import { EmptyState, ErrorState, Loading } from '../../components/States'

const EMPTY_FORM = {
  question_type: 'mcq',
  prompt: '',
  reference_answer: '',
  difficulty_level: 1,
  points: '1.0',
  concept_ids: '',
  required_concept_ids: '',
  options: 'A\tOption A\tfalse\nB\tOption B\ttrue',
  datasets: '[]',
  rubrics: '[]',
}

function formToPayload(f) {
  const ids = (s) =>
    s.split(',').map((x) => Number(x.trim())).filter((n) => Number.isInteger(n) && n > 0)
  const payload = {
    question_type: f.question_type,
    prompt: f.prompt,
    reference_answer: f.reference_answer || null,
    difficulty_level: Number(f.difficulty_level),
    points: f.points,
    concept_ids: ids(f.concept_ids),
    required_concept_ids: ids(f.required_concept_ids),
  }
  if (f.question_type === 'mcq') {
    payload.options = f.options
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const [option_label, option_text, flag] = line.split('\t')
        return {
          option_label: (option_label || '').trim(),
          option_text: (option_text || '').trim(),
          is_correct: String(flag).trim().toLowerCase() === 'true',
        }
      })
  }
  if (f.question_type === 'sql') payload.datasets = JSON.parse(f.datasets || '[]')
  if (f.question_type === 'essay') payload.rubrics = JSON.parse(f.rubrics || '[]')
  return payload
}

// UC07 + UC08 — the question bank plus AI tag review.
export default function AdminQuestionsPage() {
  const [items, setItems] = useState(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [filters, setFilters] = useState({ question_type: '', status: '', difficulty: '', q: '' })
  const [form, setForm] = useState(EMPTY_FORM)
  const [editing, setEditing] = useState(null) // question_id being replaced
  const [suggesting, setSuggesting] = useState(null)
  const [suggestion, setSuggestion] = useState(null) // TagSuggestionResult
  const [busy, setBusy] = useState(false)

  const load = useCallback(() => {
    setError('')
    const params = Object.fromEntries(
      Object.entries(filters).filter(([, v]) => v !== '' && v !== null)
    )
    api
      .get('/admin/questions', { params })
      .then((r) => setItems(r.data))
      .catch((e) => {
        setError(apiMessage(e))
        setItems([])
      })
  }, [filters])

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

  async function save(e) {
    e.preventDefault()
    setBusy(true)
    try {
      const payload = formToPayload(form)
      if (editing) {
        await run(
          () => api.put(`/admin/questions/${editing}`, payload),
          'Question updated (demoted to draft for re-validation).'
        )
      } else {
        await run(() => api.post('/admin/questions', payload), 'Question created.')
      }
      setEditing(null)
      setForm(EMPTY_FORM)
    } catch (e2) {
      setError(e2 instanceof SyntaxError ? 'Children JSON is malformed' : apiMessage(e2))
    } finally {
      setBusy(false)
    }
  }

  async function edit(q) {
    const r = await api.get(`/admin/questions/${q.question_id}`).catch(() => null)
    if (!r) return
    const d = r.data
    setEditing(q.question_id)
    setForm({
      question_type: d.question_type,
      prompt: d.prompt,
      reference_answer: d.reference_answer || '',
      difficulty_level: d.difficulty_level,
      points: d.points,
      concept_ids: d.concepts.map((c) => c.concept_id).join(','),
      required_concept_ids: d.concepts.filter((c) => c.is_required).map((c) => c.concept_id).join(','),
      options: (d.options || [])
        .map((o) => `${o.option_label}\t${o.option_text}\t${o.is_correct}`)
        .join('\n'),
      datasets: JSON.stringify(d.datasets || [], null, 2),
      rubrics: JSON.stringify(d.rubrics || [], null, 2),
    })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  async function aiTags(q) {
    setSuggesting(q.question_id)
    setSuggestion(null)
    const r = await run(
      () => api.post(`/admin/questions/${q.question_id}/ai-tags`),
      'AI suggestions stored as pending tags.'
    )
    if (r) setSuggestion(r.data)
    setSuggesting(null)
  }

  return (
    <div>
      <AdminNav />
      <h1 className="text-xl font-semibold text-gray-900">Question bank</h1>

      {/* ---------- filters ---------- */}
      <div className="mt-4 flex flex-wrap gap-2 text-sm">
        <select value={filters.question_type}
          onChange={(e) => setFilters({ ...filters, question_type: e.target.value })}
          className="rounded border border-gray-300 px-2 py-1">
          <option value="">all types</option>
          <option value="mcq">mcq</option>
          <option value="sql">sql</option>
          <option value="essay">essay</option>
        </select>
        <select value={filters.status}
          onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          className="rounded border border-gray-300 px-2 py-1">
          <option value="">all statuses</option>
          <option value="draft">draft</option>
          <option value="validated">validated</option>
          <option value="rejected">rejected</option>
        </select>
        <select value={filters.difficulty}
          onChange={(e) => setFilters({ ...filters, difficulty: e.target.value })}
          className="rounded border border-gray-300 px-2 py-1">
          <option value="">all difficulties</option>
          {[1, 2, 3, 4, 5].map((d) => <option key={d} value={d}>d{d}</option>)}
        </select>
        <input
          placeholder="search prompt…"
          value={filters.q}
          onChange={(e) => setFilters({ ...filters, q: e.target.value })}
          className="min-w-48 rounded border border-gray-300 px-2 py-1"
        />
      </div>

      {notice && <p role="status" className="mt-3 rounded bg-green-50 p-2 text-sm text-green-700">{notice}</p>}
      {error && <div className="mt-3"><ErrorState message={error} /></div>}
      {suggestion && (
        <div className="mt-3 rounded border border-purple-200 bg-purple-50 p-3 text-sm text-purple-900">
          <p className="font-medium">AI suggestion for question #{suggestion.question_id}</p>
          <p className="mt-1">
            tags: {suggestion.suggested_concept_ids.join(', ') || '—'}
            {suggestion.suggested_difficulty && ` · difficulty ${suggestion.suggested_difficulty}`}
          </p>
          {suggestion.evaluation_criteria && (
            <p className="mt-1 text-xs">criteria: {suggestion.evaluation_criteria}</p>
          )}
          <p className="mt-1 text-xs">Stored as pending tags — confirm them below.</p>
        </div>
      )}

      {/* ---------- editor ---------- */}
      <form onSubmit={save} className="mt-4 grid gap-2 rounded-md border bg-white p-4 text-sm">
        <p className="font-medium text-gray-900">
          {editing ? `Edit question #${editing}` : 'New question'}
        </p>
        <div className="grid gap-2 sm:grid-cols-4">
          <select value={form.question_type}
            onChange={(e) => setForm({ ...form, question_type: e.target.value })}
            className="rounded border border-gray-300 px-2 py-1">
            <option value="mcq">mcq</option>
            <option value="sql">sql</option>
            <option value="essay">essay</option>
          </select>
          <label className="flex items-center gap-2 text-gray-600">
            difficulty
            <input type="number" min="1" max="5" value={form.difficulty_level}
              onChange={(e) => setForm({ ...form, difficulty_level: e.target.value })}
              className="w-16 rounded border border-gray-300 px-2 py-1" />
          </label>
          <label className="flex items-center gap-2 text-gray-600">
            points
            <input value={form.points}
              onChange={(e) => setForm({ ...form, points: e.target.value })}
              className="w-20 rounded border border-gray-300 px-2 py-1" />
          </label>
        </div>
        <textarea required placeholder="Prompt" value={form.prompt} rows={2}
          onChange={(e) => setForm({ ...form, prompt: e.target.value })}
          className="rounded border border-gray-300 px-2 py-1" />
        <input placeholder="Reference answer (sql/essay)" value={form.reference_answer}
          onChange={(e) => setForm({ ...form, reference_answer: e.target.value })}
          className="rounded border border-gray-300 px-2 py-1" />
        <div className="grid gap-2 sm:grid-cols-2">
          <input placeholder="concept ids, e.g. 1,2" value={form.concept_ids}
            onChange={(e) => setForm({ ...form, concept_ids: e.target.value })}
            className="rounded border border-gray-300 px-2 py-1" />
          <input placeholder="required concept ids (subset)" value={form.required_concept_ids}
            onChange={(e) => setForm({ ...form, required_concept_ids: e.target.value })}
            className="rounded border border-gray-300 px-2 py-1" />
        </div>
        {form.question_type === 'mcq' && (
          <label className="text-xs text-gray-600">
            options — one per line, tab-separated: label / text / true|false
            <textarea value={form.options} rows={4}
              onChange={(e) => setForm({ ...form, options: e.target.value })}
              className="mt-1 w-full rounded border border-gray-300 px-2 py-1 font-mono text-xs" />
          </label>
        )}
        {form.question_type === 'sql' && (
          <label className="text-xs text-gray-600">
            datasets (JSON array)
            <textarea value={form.datasets} rows={4}
              onChange={(e) => setForm({ ...form, datasets: e.target.value })}
              className="mt-1 w-full rounded border border-gray-300 px-2 py-1 font-mono text-xs" />
          </label>
        )}
        {form.question_type === 'essay' && (
          <label className="text-xs text-gray-600">
            rubrics (JSON array)
            <textarea value={form.rubrics} rows={4}
              onChange={(e) => setForm({ ...form, rubrics: e.target.value })}
              className="mt-1 w-full rounded border border-gray-300 px-2 py-1 font-mono text-xs" />
          </label>
        )}
        <div className="flex gap-2">
          <button type="submit" disabled={busy}
            className="rounded bg-blue-600 px-3 py-1 font-medium text-white hover:bg-blue-700 disabled:opacity-50">
            {busy ? 'Saving…' : editing ? 'Save changes' : 'Create'}
          </button>
          {editing && (
            <button type="button" onClick={() => { setEditing(null); setForm(EMPTY_FORM) }}
              className="rounded border border-gray-300 px-3 py-1 text-gray-700">
              Cancel
            </button>
          )}
        </div>
      </form>

      {/* ---------- list ---------- */}
      {items === null ? (
        <Loading />
      ) : items.length === 0 ? (
        <div className="mt-4"><EmptyState title="No questions match" /></div>
      ) : (
        <ul className="mt-4 divide-y rounded-md border bg-white text-sm">
          {items.map((q) => (
            <li key={q.question_id} className="p-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-mono text-xs text-gray-400">#{q.question_id}</span>
                <span className="rounded bg-gray-100 px-2 py-0.5 text-xs uppercase">{q.question_type}</span>
                <span className="rounded bg-gray-100 px-2 py-0.5 text-xs">d{q.difficulty_level}</span>
                <span className={`rounded px-2 py-0.5 text-xs font-medium ${
                  q.status === 'validated' ? 'bg-green-50 text-green-700'
                  : q.status === 'rejected' ? 'bg-red-50 text-red-700'
                  : 'bg-amber-50 text-amber-700'
                }`}>{q.status}</span>
                <span className="rounded bg-gray-50 px-2 py-0.5 text-xs text-gray-500">{q.source}</span>
                <span className="ml-auto flex gap-3 text-xs">
                  <button type="button" onClick={() => aiTags(q)} disabled={suggesting === q.question_id}
                    className="text-purple-600 hover:underline disabled:opacity-50">
                    {suggesting === q.question_id ? 'suggesting…' : 'AI tags'}
                  </button>
                  <button type="button" onClick={() => edit(q)} className="text-blue-600 hover:underline">Edit</button>
                  {q.status !== 'validated' && (
                    <button type="button"
                      onClick={() => run(() => api.patch(`/admin/questions/${q.question_id}`, { status: 'validated' }), 'Validated.')}
                      className="text-green-600 hover:underline">Validate</button>
                  )}
                  {q.status === 'validated' && (
                    <button type="button"
                      onClick={() => run(() => api.patch(`/admin/questions/${q.question_id}`, { status: 'rejected' }), 'Rejected.')}
                      className="text-red-600 hover:underline">Reject</button>
                  )}
                  <button type="button"
                    onClick={() => run(() => api.delete(`/admin/questions/${q.question_id}`), 'Deleted.')}
                    className="text-red-600 hover:underline">Delete</button>
                </span>
              </div>
              <p className="mt-1 text-gray-800">{q.prompt}</p>
              {q.concepts?.length > 0 && (
                <div className="mt-1 flex flex-wrap gap-1 text-xs">
                  {q.concepts.map((t) => (
                    <span key={t.concept_id}
                      className={`rounded px-1.5 py-0.5 ${
                        t.confirmed ? 'bg-blue-50 text-blue-700' : 'bg-amber-50 text-amber-700'
                      }`}>
                      {t.concept_code}{t.is_required && '*'}{!t.confirmed && ' (pending)'}
                      {!t.confirmed && (
                        <>
                          {' '}
                          <button type="button"
                            onClick={() => run(() => api.post(`/admin/questions/${q.question_id}/tags/${t.concept_id}/confirm`), 'Tag confirmed.')}
                            className="text-green-700 underline">confirm</button>
                          {' / '}
                          <button type="button"
                            onClick={() => run(() => api.delete(`/admin/questions/${q.question_id}/tags/${t.concept_id}`), 'Tag rejected.')}
                            className="text-red-700 underline">reject</button>
                        </>
                      )}
                    </span>
                  ))}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
