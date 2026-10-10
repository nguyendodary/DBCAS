import { useCallback, useEffect, useState } from 'react'
import api, { apiMessage } from '../../api'
import AdminNav from '../../components/AdminNav'
import { EmptyState, ErrorState, Loading } from '../../components/States'
import { Badge, Card, CardTitle, Notice, PageHeader, StatusBadge, TypeBadge, inputCls } from '../../components/ui'

const EMPTY_FORM = {
  question_type: 'mcq',
  prompt: '',
  reference_answer: '',
  difficulty_level: 1,
  points: '1.0',
  concept_ids: '',
  required_concept_ids: '',
  options: [
    { option_label: 'A', option_text: 'Option A', is_correct: false },
    { option_label: 'B', option_text: 'Option B', is_correct: true },
  ],
  datasets: '[]',
  rubrics: '[]',
}

function nextLabel(options) {
  return String.fromCharCode(65 + options.length)
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
      .map((o, i) => ({
        option_label: (o.option_label || '').trim() || String.fromCharCode(65 + i),
        option_text: (o.option_text || '').trim(),
        is_correct: !!o.is_correct,
      }))
      .filter((o) => o.option_text)
  }
  if (f.question_type === 'sql') payload.datasets = JSON.parse(f.datasets || '[]')
  if (f.question_type === 'essay') payload.rubrics = JSON.parse(f.rubrics || '[]')
  return payload
}

// Lettered option rows with inline correct-answer selection — adapted
// from the prototype question editors, producing the same payload shape
// the API already accepts.
function OptionsEditor({ options, onChange }) {
  const set = (i, patch) =>
    onChange(options.map((o, j) => (j === i ? { ...o, ...patch } : o)))
  return (
    <fieldset className="rounded-lg border border-gray-200 p-3">
      <legend className="px-1 text-xs font-medium text-gray-600">
        Options — check the correct answer(s)
      </legend>
      <ul className="space-y-2">
        {options.map((o, i) => (
          <li key={i} className="flex items-center gap-2">
            <input
              value={o.option_label}
              onChange={(e) => set(i, { option_label: e.target.value })}
              aria-label={`Option ${i + 1} label`}
              className="w-11 rounded-md border border-gray-300 px-2 py-1.5 text-center font-mono text-sm focus:border-blue-500 focus:outline-none"
            />
            <input
              required
              value={o.option_text}
              onChange={(e) => set(i, { option_text: e.target.value })}
              placeholder={`Option ${o.option_label || i + 1} text`}
              aria-label={`Option ${i + 1} text`}
              className={inputCls}
            />
            <label className="flex shrink-0 items-center gap-1 text-xs text-gray-600">
              <input
                type="checkbox"
                checked={!!o.is_correct}
                onChange={(e) => set(i, { is_correct: e.target.checked })}
                className="h-4 w-4 accent-blue-600"
              />
              correct
            </label>
            <button
              type="button"
              onClick={() => onChange(options.filter((_, j) => j !== i))}
              disabled={options.length <= 2}
              aria-label={`Remove option ${o.option_label || i + 1}`}
              className="text-xs font-medium text-red-600 hover:underline disabled:opacity-40"
            >
              remove
            </button>
          </li>
        ))}
      </ul>
      <button
        type="button"
        onClick={() =>
          onChange([
            ...options,
            { option_label: nextLabel(options), option_text: '', is_correct: false },
          ])
        }
        className="mt-2 text-xs font-medium text-blue-600 hover:underline"
      >
        + add option
      </button>
    </fieldset>
  )
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
      options: (d.options || []).length
        ? (d.options || []).map((o) => ({
            option_label: o.option_label,
            option_text: o.option_text,
            is_correct: !!o.is_correct,
          }))
        : EMPTY_FORM.options,
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

  const selCls =
    'rounded-md border border-gray-300 px-2 py-1.5 text-sm focus:border-blue-500 focus:outline-none'

  return (
    <div className="space-y-4">
      <AdminNav />
      <PageHeader
        title="Question bank"
        subtitle="Draft → validated → (rejected) lifecycle, with optional AI concept-tag suggestions."
      />

      {/* ---------- filters ---------- */}
      <Card className="flex flex-wrap gap-2 p-3 text-sm">
        <select value={filters.question_type} aria-label="Filter by type"
          onChange={(e) => setFilters({ ...filters, question_type: e.target.value })}
          className={selCls}>
          <option value="">all types</option>
          <option value="mcq">mcq</option>
          <option value="sql">sql</option>
          <option value="essay">essay</option>
        </select>
        <select value={filters.status} aria-label="Filter by status"
          onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          className={selCls}>
          <option value="">all statuses</option>
          <option value="draft">draft</option>
          <option value="validated">validated</option>
          <option value="rejected">rejected</option>
        </select>
        <select value={filters.difficulty} aria-label="Filter by difficulty"
          onChange={(e) => setFilters({ ...filters, difficulty: e.target.value })}
          className={selCls}>
          <option value="">all difficulties</option>
          {[1, 2, 3, 4, 5].map((d) => <option key={d} value={d}>d{d}</option>)}
        </select>
        <input
          placeholder="search prompt…"
          aria-label="Search prompt"
          value={filters.q}
          onChange={(e) => setFilters({ ...filters, q: e.target.value })}
          className={`min-w-48 ${inputCls}`}
        />
      </Card>

      {notice && <Notice>{notice}</Notice>}
      {error && <ErrorState message={error} />}
      {suggestion && (
        <div className="rounded-lg border border-purple-200 bg-purple-50 p-3 text-sm text-purple-900">
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
      <Card className="overflow-hidden">
        <CardTitle title={editing ? `Edit question #${editing}` : 'New question'} />
        <form onSubmit={save} className="grid gap-3 p-4 text-sm">
          <div className="grid gap-2 sm:grid-cols-4">
            <select value={form.question_type} aria-label="Question type"
              onChange={(e) => setForm({ ...form, question_type: e.target.value })}
              className={selCls}>
              <option value="mcq">mcq</option>
              <option value="sql">sql</option>
              <option value="essay">essay</option>
            </select>
            <label className="flex items-center gap-2 text-gray-600">
              difficulty
              <input type="number" min="1" max="5" value={form.difficulty_level}
                onChange={(e) => setForm({ ...form, difficulty_level: e.target.value })}
                className="w-16 rounded-md border border-gray-300 px-2 py-1.5 focus:border-blue-500 focus:outline-none" />
            </label>
            <label className="flex items-center gap-2 text-gray-600">
              points
              <input value={form.points}
                onChange={(e) => setForm({ ...form, points: e.target.value })}
                className="w-20 rounded-md border border-gray-300 px-2 py-1.5 focus:border-blue-500 focus:outline-none" />
            </label>
          </div>
          <textarea required placeholder="Prompt" value={form.prompt} rows={2}
            onChange={(e) => setForm({ ...form, prompt: e.target.value })}
            className={inputCls} />
          <input placeholder="Reference answer (sql/essay)" value={form.reference_answer}
            onChange={(e) => setForm({ ...form, reference_answer: e.target.value })}
            className={inputCls} />
          <div className="grid gap-2 sm:grid-cols-2">
            <input placeholder="concept ids, e.g. 1,2" value={form.concept_ids}
              onChange={(e) => setForm({ ...form, concept_ids: e.target.value })}
              className={inputCls} />
            <input placeholder="required concept ids (subset)" value={form.required_concept_ids}
              onChange={(e) => setForm({ ...form, required_concept_ids: e.target.value })}
              className={inputCls} />
          </div>
          {form.question_type === 'mcq' && (
            <OptionsEditor
              options={form.options}
              onChange={(options) => setForm({ ...form, options })}
            />
          )}
          {form.question_type === 'sql' && (
            <label className="text-xs text-gray-600">
              datasets (JSON array)
              <textarea value={form.datasets} rows={4}
                onChange={(e) => setForm({ ...form, datasets: e.target.value })}
                className="mt-1 w-full rounded-md border border-gray-300 px-2 py-1.5 font-mono text-xs focus:border-blue-500 focus:outline-none" />
            </label>
          )}
          {form.question_type === 'essay' && (
            <label className="text-xs text-gray-600">
              rubrics (JSON array)
              <textarea value={form.rubrics} rows={4}
                onChange={(e) => setForm({ ...form, rubrics: e.target.value })}
                className="mt-1 w-full rounded-md border border-gray-300 px-2 py-1.5 font-mono text-xs focus:border-blue-500 focus:outline-none" />
            </label>
          )}
          <div className="flex gap-2">
            <button type="submit" disabled={busy}
              className="rounded-md bg-blue-600 px-3 py-1.5 font-medium text-white hover:bg-blue-700 disabled:opacity-50">
              {busy ? 'Saving…' : editing ? 'Save changes' : 'Create'}
            </button>
            {editing && (
              <button type="button" onClick={() => { setEditing(null); setForm(EMPTY_FORM) }}
                className="rounded-md border border-gray-300 px-3 py-1.5 text-gray-700 hover:bg-gray-50">
                Cancel
              </button>
            )}
          </div>
        </form>
      </Card>

      {/* ---------- list ---------- */}
      {items === null ? (
        <Loading />
      ) : items.length === 0 ? (
        <EmptyState title="No questions match" />
      ) : (
        <Card className="overflow-hidden">
          <ul className="divide-y text-sm">
            {items.map((q) => (
              <li key={q.question_id} className="p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-xs text-gray-400">#{q.question_id}</span>
                  <TypeBadge type={q.question_type} />
                  <Badge>d{q.difficulty_level}</Badge>
                  <StatusBadge status={q.status} />
                  <Badge>{q.source}</Badge>
                  <span className="ml-auto flex gap-3 text-xs">
                    <button type="button" onClick={() => aiTags(q)} disabled={suggesting === q.question_id}
                      className="font-medium text-purple-600 hover:underline disabled:opacity-50">
                      {suggesting === q.question_id ? 'suggesting…' : 'AI tags'}
                    </button>
                    <button type="button" onClick={() => edit(q)} className="font-medium text-blue-600 hover:underline">Edit</button>
                    {q.status !== 'validated' && (
                      <button type="button"
                        onClick={() => run(() => api.patch(`/admin/questions/${q.question_id}`, { status: 'validated' }), 'Validated.')}
                        className="font-medium text-green-600 hover:underline">Validate</button>
                    )}
                    {q.status === 'validated' && (
                      <button type="button"
                        onClick={() => run(() => api.patch(`/admin/questions/${q.question_id}`, { status: 'rejected' }), 'Rejected.')}
                        className="font-medium text-red-600 hover:underline">Reject</button>
                    )}
                    <button type="button"
                      onClick={() => run(() => api.delete(`/admin/questions/${q.question_id}`), 'Deleted.')}
                      className="font-medium text-red-600 hover:underline">Delete</button>
                  </span>
                </div>
                <p className="mt-1.5 text-gray-800">{q.prompt}</p>
                {q.concepts?.length > 0 && (
                  <div className="mt-1.5 flex flex-wrap gap-1 text-xs">
                    {q.concepts.map((t) => (
                      <span key={t.concept_id}
                        className={`rounded-full px-2 py-0.5 ${
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
        </Card>
      )}
    </div>
  )
}
