import { t, useLocale, message, number, percent, dateTime, statusLabel, typeLabel, validationError, resources } from '../../i18n'
import { resolveMessage } from '../../i18n'
import { useCallback, useEffect, useRef, useState } from 'react'
import api, { apiMessage } from '../../api'
import { ActionSpinner, EmptyState, ErrorState, Loading } from '../../components/States'
import { Badge, Card, CardTitle, ConfirmDialog, Notice, PageHeader, Pagination, StatusBadge, TypeBadge, btnGhost, btnPrimary, inputCls, focusDialogTrigger } from '../../components/ui'

const EMPTY_FORM = {
  question_type: 'mcq',
  prompt: '',
  reference_answer: '',
  difficulty_level: 1,
  points: '1.0',
  concept_ids: '',
  required_concept_ids: '',
  options: [
    { option_label: 'A', option_text: '', is_correct: false },
    { option_label: 'B', option_text: '', is_correct: true },
  ],
  datasets: '[]',
  rubrics: '[]',
}

function createQuestionForm() {
  return { ...EMPTY_FORM, options: EMPTY_FORM.options.map(option => ({ ...option, option_text: t('admin.questions.defaultOption', { label: option.option_label }) })) }
}

function nextLabel(options) {
  return String.fromCharCode(65 + options.length)
}

function formToPayload(f) {
  const ids = (s) => {
    if (!s.trim()) return []
    const values = s.split(',').map((x) => Number(x.trim()))
    if (values.some((n) => !Number.isInteger(n) || n <= 0) || new Set(values).size !== values.length)
      throw validationError('validation.questionConceptIds')
    return values
  }
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
  useLocale()
  const set = (i, patch) =>
    onChange(options.map((o, j) => (j === i ? { ...o, ...patch } : o)))
  return (
    <fieldset className="min-w-0 rounded-lg border border-edge p-3">
      <legend className="px-1 text-xs font-medium text-sub">{t('admin.questions.options')}</legend>
      <ul className="space-y-2">
        {options.map((o, i) => (
          <li key={i} className="flex flex-wrap items-center gap-2">
            <input
              value={o.option_label}
              onChange={(e) => set(i, { option_label: e.target.value })}
              aria-label={t('admin.questions.optionLabel', { number: i + 1 })}
              className="w-11 rounded-md border border-edge2 px-2 py-1.5 text-center font-mono text-sm focus:border-cyan-400/60 focus:outline-none"
            />
            <input
              required
              value={o.option_text}
              onChange={(e) => set(i, { option_text: e.target.value })}
              placeholder={t('admin.questions.optionText', { number: o.option_label || i + 1 })}
              aria-label={t('admin.questions.optionText', { number: i + 1 })}
              className={`${inputCls} min-w-0 flex-[1_1_12rem]`}
            />
            <label className="flex shrink-0 items-center gap-1 text-xs text-sub">
              <input
                type="checkbox"
                checked={!!o.is_correct}
                onChange={(e) => set(i, { is_correct: e.target.checked })}
                className="h-4 w-4 accent-cyan-400"
              />
              {t('admin.questions.correct')}
            </label>
            <button
              type="button"
              onClick={() => onChange(options.filter((_, j) => j !== i))}
              disabled={options.length <= 2}
              aria-label={t('admin.questions.removeOption', { number: o.option_label || i + 1 })}
              className="text-xs font-medium text-rose-300 hover:underline disabled:opacity-40"
            >{t('admin.remove')}
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
        className="mt-2 text-xs font-medium text-cyan-300 hover:underline"
      >{t('admin.questions.addOption')}</button>
    </fieldset>
  )
}

// UC07 + UC08 — the question bank plus AI tag review.
export default function AdminQuestionsPage() {
  useLocale()
  const [items, setItems] = useState(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [filters, setFilters] = useState({ question_type: '', status: '', difficulty: '', concept_id: '', q: '' })
  const [conceptOptions, setConceptOptions] = useState([])
  const [query, setQuery] = useState('')
  const requestRef = useRef(null)
  const [form, setForm] = useState(createQuestionForm)
  const [editing, setEditing] = useState(null) // question_id being replaced
  const [suggesting, setSuggesting] = useState(null)
  const [suggestion, setSuggestion] = useState(null) // TagSuggestionResult
  const [busy, setBusy] = useState(false)
  const [editorOpen, setEditorOpen] = useState(false)
  const [page, setPage] = useState(1)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [deleting, setDeleting] = useState(false)

  const load = useCallback(() => {
    requestRef.current?.abort()
    const controller = new AbortController()
    requestRef.current = controller
    setError('')
    const params = Object.fromEntries(
      Object.entries({ question_type: filters.question_type, status: filters.status,
        difficulty: filters.difficulty, concept_id: filters.concept_id, q: query }).filter(([, v]) => v !== '' && v !== null)
    )
    api
      .get('/admin/questions', { params, signal: controller.signal })
      .then((r) => {
        if (controller.signal.aborted) return
        setItems(r.data)
        setConceptOptions((existing) => {
          const byId = new Map(existing.map((c) => [c.concept_id, c]))
          r.data.forEach((q) => q.concepts?.forEach((c) => byId.set(c.concept_id, c)))
          return [...byId.values()].sort((a, b) => a.concept_code.localeCompare(b.concept_code))
        })
      })
      .catch((e) => {
        if (controller.signal.aborted || e.code === 'ERR_CANCELED') return
        setError(apiMessage(e))
        setItems([])
      })
  }, [filters.question_type, filters.status, filters.difficulty, filters.concept_id, query])

  useEffect(() => { load(); return () => requestRef.current?.abort() }, [load])
  useEffect(() => {
    const timer = setTimeout(() => setQuery(filters.q), 250)
    return () => clearTimeout(timer)
  }, [filters.q])
  useEffect(() => setPage(1), [filters])

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
      const saved = editing
        ? await run(
          () => api.put(`/admin/questions/${editing}`, payload),
          message('admin.questions.updated')
        )
        : await run(() => api.post('/admin/questions', payload), message('admin.questions.created'))
      if (saved) {
        setEditing(null)
        setForm(createQuestionForm())
        setEditorOpen(false)
      }
    } catch (e2) {
      setError(e2 instanceof SyntaxError ? message('validation.json') : apiMessage(e2))
    } finally {
      setBusy(false)
    }
  }

  async function edit(q) {
    const r = await api.get(`/admin/questions/${q.question_id}`).catch((e) => {
      setError(apiMessage(e, message('admin.questions.openError')))
      return null
    })
    if (!r) return
    const d = r.data
    setEditing(q.question_id)
    setEditorOpen(true)
    setForm({
      question_type: d.question_type,
      prompt: d.prompt,
      reference_answer: d.reference_answer || '',
      difficulty_level: d.difficulty_level,
      points: d.points,
      concept_ids: d.concepts.filter((c) => c.confirmed).map((c) => c.concept_id).join(','),
      required_concept_ids: d.concepts.filter((c) => c.confirmed && c.is_required).map((c) => c.concept_id).join(','),
      options: (d.options || []).length
        ? (d.options || []).map((o) => ({
            option_label: o.option_label,
            option_text: o.option_text,
            is_correct: !!o.is_correct,
          }))
        : createQuestionForm().options,
      datasets: JSON.stringify(d.datasets || [], null, 2),
      rubrics: JSON.stringify(d.rubrics || [], null, 2),
    })
    window.scrollTo({ top: 0, behavior: window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' })
  }

  async function aiTags(q) {
    setSuggesting(q.question_id)
    setSuggestion(null)
    const r = await run(
      () => api.post(`/admin/questions/${q.question_id}/ai-tags`),
      message('admin.questions.pendingTags')
    )
    if (r) setSuggestion(r.data)
    setSuggesting(null)
  }

  async function deleteQuestion() {
    if (!deleteTarget || deleting) return
    setDeleting(true)
    const deleted = await run(() => api.delete(`/admin/questions/${deleteTarget.question_id}`), message('admin.questions.deleted'))
    setDeleting(false)
    if (deleted) setDeleteTarget(null)
  }

  const selCls =
    'rounded-md border border-edge2 px-2 py-1.5 text-sm focus:border-cyan-400/60 focus:outline-none'
  const pageCount = Math.ceil((items?.length || 0) / 12)
  const currentPage = Math.min(page, pageCount || 1)

  return (
    <div className="space-y-4">
      <PageHeader
        eyebrow={t('admin.questions.eyebrow')}
        title={t('admin.questions.title')}
        subtitle={t('admin.questions.subtitle')}
      >
        <button type="button" onClick={() => { setEditing(null); setForm(createQuestionForm()); setEditorOpen((open) => !open) }} className={editorOpen ? btnGhost : btnPrimary}>
          {editorOpen ? t('admin.closeEditor') : t('admin.questions.new')}
        </button>
      </PageHeader>

      {/* ---------- filters ---------- */}
      <Card className="grid grid-cols-2 gap-2 p-3 text-sm md:flex md:flex-wrap md:items-center">
        <select value={filters.concept_id} aria-label={t('admin.questions.filterConcept')} onChange={(e) => setFilters({ ...filters, concept_id: e.target.value })} className={`${selCls} w-full md:w-auto`}>
          <option value="">{t('admin.questions.allConcepts')}</option>
          {conceptOptions.map((c) => <option key={c.concept_id} value={c.concept_id}>{c.concept_code}</option>)}
        </select>
        <select value={filters.question_type} aria-label={t('admin.questions.filterType')}
          onChange={(e) => setFilters({ ...filters, question_type: e.target.value })}
          className={`${selCls} w-full md:w-auto`}>
          <option value="">{t('admin.questions.allTypes')}</option>
          <option value="mcq">{typeLabel('mcq')}</option>
          <option value="sql">{typeLabel('sql')}</option>
          <option value="essay">{typeLabel('essay')}</option>
        </select>
        <select value={filters.status} aria-label={t('admin.questions.filterStatus')}
          onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          className={`${selCls} w-full md:w-auto`}>
          <option value="">{t('admin.questions.allStatuses')}</option>
          <option value="draft">{statusLabel('draft')}</option>
          <option value="validated">{statusLabel('validated')}</option>
          <option value="retired">{statusLabel('retired')}</option>
        </select>
        <select value={filters.difficulty} aria-label={t('admin.questions.filterDifficulty')}
          onChange={(e) => setFilters({ ...filters, difficulty: e.target.value })}
          className={`${selCls} w-full md:w-auto`}>
          <option value="">{t('admin.questions.allDifficulties')}</option>
          {[1, 2, 3, 4, 5].map((d) => <option key={d} value={d}>{t('exam.difficulty', { value: number(d) })}</option>)}
        </select>
        <input
          placeholder={t('admin.questions.searchPlaceholder')}
          aria-label={t('admin.questions.search')}
          value={filters.q}
          onChange={(e) => setFilters({ ...filters, q: e.target.value })}
          className={`col-span-2 md:min-w-56 md:flex-1 md:!w-auto ${inputCls}`}
        />
      </Card>

      {notice && <Notice>{notice}</Notice>}
      {error && <ErrorState message={resolveMessage(error)} />}
      {suggestion && (
        <div className="rounded-lg border border-violet-500/30 bg-violet-500/10 p-3 text-sm text-violet-200">
          <p className="font-medium">{t('admin.questions.suggestion', { id: suggestion.question_id })}</p>
          <p className="mt-1">
            {t('admin.questions.tags', { ids: suggestion.suggested_concept_ids.join(', ') || '—' })}
            {suggestion.suggested_difficulty && ` · ${t('exam.difficulty', { value: number(suggestion.suggested_difficulty) })}`}
          </p>
          {suggestion.evaluation_criteria && (
            <p className="mt-1 text-xs">{t('admin.questions.criteria', { value: suggestion.evaluation_criteria })}</p>
          )}
          <p className="mt-1 text-xs">{t('admin.questions.pendingHint')}</p>
        </div>
      )}

      {/* ---------- editor ---------- */}
      {editorOpen && <Card className="overflow-hidden">
        <CardTitle title={editing ? t('admin.questions.edit', { id: editing }) : t('admin.questions.new')} />
        <form onSubmit={save} className="grid gap-3 p-4 text-sm">
          <div className="grid gap-2 sm:grid-cols-4">
            <select value={form.question_type} aria-label={t('admin.questions.type')}
              onChange={(e) => setForm({ ...form, question_type: e.target.value })}
              className={selCls}>
              <option value="mcq">{typeLabel('mcq')}</option>
              <option value="sql">{typeLabel('sql')}</option>
              <option value="essay">{typeLabel('essay')}</option>
            </select>
            <label className="flex items-center gap-2 text-sub">
              {t('common.difficulty')}
              <input type="number" min="1" max="5" value={form.difficulty_level}
                onChange={(e) => setForm({ ...form, difficulty_level: e.target.value })}
                className="w-16 rounded-md border border-edge2 px-2 py-1.5 focus:border-cyan-400/60 focus:outline-none" />
            </label>
            <label className="flex items-center gap-2 text-sub">{t('common.points')}<input value={form.points}
                onChange={(e) => setForm({ ...form, points: e.target.value })}
                className="w-20 rounded-md border border-edge2 px-2 py-1.5 focus:border-cyan-400/60 focus:outline-none" />
            </label>
          </div>
          <textarea required aria-label={t('admin.questions.prompt')} placeholder={t('admin.questions.promptPlaceholder')} value={form.prompt} rows={3}
            onChange={(e) => setForm({ ...form, prompt: e.target.value })}
            className={inputCls} />
          <input aria-label={t('admin.questions.reference')} placeholder={t('admin.questions.referenceHint')} value={form.reference_answer}
            onChange={(e) => setForm({ ...form, reference_answer: e.target.value })}
            className={inputCls} />
          <div className="grid gap-2 sm:grid-cols-2">
            <input aria-label={t('admin.questions.ids')} placeholder={t('admin.questions.idsHint')} value={form.concept_ids}
              onChange={(e) => setForm({ ...form, concept_ids: e.target.value })}
              className={inputCls} />
            <input aria-label={t('admin.questions.requiredIds')} placeholder={t('admin.questions.requiredHint')} value={form.required_concept_ids}
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
            <label className="text-xs text-sub">{t('admin.questions.datasets')}<textarea value={form.datasets} rows={4}
                onChange={(e) => setForm({ ...form, datasets: e.target.value })}
                className="mt-1 w-full rounded-md border border-edge2 px-2 py-1.5 font-mono text-xs focus:border-cyan-400/60 focus:outline-none" />
            </label>
          )}
          {form.question_type === 'essay' && (
            <label className="text-xs text-sub">{t('admin.questions.rubrics')}<textarea value={form.rubrics} rows={4}
                onChange={(e) => setForm({ ...form, rubrics: e.target.value })}
                className="mt-1 w-full rounded-md border border-edge2 px-2 py-1.5 font-mono text-xs focus:border-cyan-400/60 focus:outline-none" />
            </label>
          )}
          <div className="flex gap-2">
            <button type="submit" disabled={busy}
              className={btnPrimary}>
              {busy && <ActionSpinner />}
              {busy ? t('common.saving') : editing ? t('common.saveChanges') : t('common.create')}
            </button>
            <button type="button" onClick={() => { setEditing(null); setForm(createQuestionForm()); setEditorOpen(false) }}
              className={btnGhost}>{t('common.cancel')}</button>
          </div>
        </form>
      </Card>}

      {/* ---------- list ---------- */}
      {items === null ? (
        <Loading />
      ) : items.length === 0 ? (
        <EmptyState title={t('admin.questions.empty')} />
      ) : (
        <Card className="overflow-hidden">
          <CardTitle title={t('admin.questions.count', { count: items.length })} />
          <ul className="divide-y divide-edge text-sm">
            {items.slice((currentPage - 1) * 12, currentPage * 12).map((q) => (
              <li key={q.question_id} className="px-4 py-3.5 transition-colors hover:bg-surface-hover sm:px-5">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-xs text-faint">#{q.question_id}</span>
                  <TypeBadge type={q.question_type} />
                  <Badge>{t('exam.difficulty', { value: number(q.difficulty_level) })}</Badge>
                  <StatusBadge status={q.status} />
                  <Badge>{statusLabel(q.source)}</Badge>
                  <span className="ml-auto flex flex-wrap gap-x-3 gap-y-1.5 text-xs">
                    <button type="button" onClick={() => aiTags(q)} disabled={suggesting === q.question_id}
                      className="font-medium text-violet-300 hover:underline disabled:opacity-50">
                      {suggesting === q.question_id ? t('admin.questions.suggesting') : t('admin.questions.aiTags')}
                    </button>
                    <button type="button" onClick={() => edit(q)} className="font-medium text-cyan-300 hover:underline">{t('common.edit')}</button>
                    {q.status !== 'validated' && (
                      <button type="button"
                        onClick={() => run(() => api.patch(`/admin/questions/${q.question_id}`, { status: 'validated' }), message('admin.questions.validated'))}
                        className="font-medium text-emerald-300 hover:underline">{t('admin.validate')}</button>
                    )}
                    {q.status === 'validated' && (
                      <button type="button"
                        onClick={() => run(() => api.patch(`/admin/questions/${q.question_id}`, { status: 'retired' }), message('admin.questions.retired'))}
                        className="font-medium text-rose-300 hover:underline">{t('admin.questions.retire')}</button>
                    )}
                    <button type="button"
                      onClick={(event) => { focusDialogTrigger(event); setDeleteTarget(q) }}
                      className="font-medium text-rose-300 hover:underline">{t('common.delete')}</button>
                  </span>
                </div>
                <p className="mt-2 line-clamp-2 text-ink">{q.prompt}</p>
                {q.concepts?.length > 0 && (
                  <div className="mt-1.5 flex flex-wrap gap-1 text-xs">
                    {q.concepts.map((tag) => (
                      <span key={tag.concept_id}
                        className={`rounded-full px-2 py-0.5 ${
                          tag.confirmed ? 'bg-cyan-400/10 text-cyan-300' : 'bg-amber-500/10 text-amber-300'
                        }`}>
                        {tag.concept_code}{tag.is_required && '*'}{!tag.confirmed && ` (${statusLabel(tag.review_status || 'pending')})`}
                        {!tag.confirmed && tag.review_status !== 'rejected' && (
                          <>
                            {' '}
                            <button type="button"
                              onClick={() => run(() => api.post(`/admin/questions/${q.question_id}/tags/${tag.concept_id}/confirm`), message('admin.questions.confirmedTag'))}
                              className="text-emerald-300 underline">{t('common.confirm')}</button>
                            {' / '}
                            <button type="button"
                              onClick={() => run(() => api.delete(`/admin/questions/${q.question_id}/tags/${tag.concept_id}`), message('admin.questions.rejectedTag'))}
                              className="text-rose-300 underline">{t('common.reject')}</button>
                          </>
                        )}
                      </span>
                    ))}
                  </div>
                )}
                {q.ai_review && <div className="mt-3 rounded-lg border border-edge bg-elev/50 p-3 text-xs text-sub">
                  <p className="font-medium">{t('admin.questions.aiReview', { status: statusLabel(q.ai_review.status) })}</p>
                  <p className="mt-1">{t('admin.questions.suggestedDifficulty', { value: number(q.ai_review.difficulty_level) })}</p>
                  <p className="mt-1">{q.ai_review.evaluation_criteria}</p>
                  {q.ai_review.status === 'pending' && <div className="mt-2 flex flex-wrap gap-3">
                    <button type="button" onClick={() => run(() => api.post(`/admin/questions/${q.question_id}/ai-review`, { decision: 'confirmed', apply_difficulty: true }), message('admin.questions.approvedSuggestion'))} className="font-medium text-emerald-300 underline">{t('admin.questions.approveCriteria')}</button>
                    <button type="button" onClick={() => run(() => api.post(`/admin/questions/${q.question_id}/ai-review`, { decision: 'rejected' }), message('admin.rejectedSuggestion'))} className="font-medium text-rose-300 underline">{t('admin.questions.rejectSuggestion')}</button>
                  </div>}
                </div>}
              </li>
            ))}
          </ul>
          <Pagination page={currentPage} pageCount={pageCount} onPageChange={setPage} />
        </Card>
      )}
      <ConfirmDialog open={!!deleteTarget} title={t('admin.questions.deleteTitle')} confirmLabel={deleting ? t('common.deleting') : t('admin.questions.delete')} cancelLabel={t('common.cancel')} busy={deleting} onConfirm={deleteQuestion} onCancel={() => setDeleteTarget(null)}>
        {t('admin.questions.deleteBody', { id: deleteTarget?.question_id || '' })}
        {error && <p role="alert" className="mt-2 text-rose-300">{resolveMessage(error)}</p>}
      </ConfirmDialog>
    </div>
  )
}
