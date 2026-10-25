import { t, useLocale, message, number, percent, dateTime, statusLabel, typeLabel, validationError, resources } from '../../i18n'
import { resolveMessage } from '../../i18n'
import { useCallback, useEffect, useRef, useState } from 'react'
import api, { apiMessage } from '../../api'
import { ActionSpinner, EmptyState, ErrorState, Loading } from '../../components/States'
import { Badge, Card, CardTitle, ConfirmDialog, Icon, Notice, Pagination, StatusBadge, TypeBadge, btnGhost, btnPrimary, inputCls } from '../../components/ui'
import SqlEditor from '../../components/SqlEditor'
import SqlAnswerPreview from '../../components/SqlAnswerPreview'
import SqlDatasetsEditor from '../../components/SqlDatasetsEditor'
import EssayRubricEditor, { rubricRows } from '../../components/EssayRubricEditor'
import { AdminPageHeader, FilterBar, FormSection, MenuItem, RowMenu } from '../../components/admin'

const EMPTY_FORM = {
  question_type: 'mcq',
  prompt: '',
  reference_answer: '',
  explanation: '',
  tags: [],
  source_refs: [],
  difficulty_level: 1,
  points: '1.0',
  concept_ids: '',
  options: [
    { option_label: 'A', option_text: '', is_correct: false },
    { option_label: 'B', option_text: '', is_correct: false },
    { option_label: 'C', option_text: '', is_correct: false },
    { option_label: 'D', option_text: '', is_correct: false },
  ],
  datasets: '[]',
  rubrics: '[]',
}

function previewDatasets(value) {
  try {
    const datasets = JSON.parse(value || '[]')
    return Array.isArray(datasets) ? datasets : []
  } catch { return [] }
}

function createQuestionForm() {
  return { ...EMPTY_FORM, options: EMPTY_FORM.options.map(option => ({ ...option })) }
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
    explanation: f.explanation?.trim() || null,
    tags: f.tags,
    source_refs: f.source_refs,
    difficulty_level: Number(f.difficulty_level),
    points: f.points,
    concept_ids: ids(f.concept_ids),
    required_concept_ids: [],
  }
  if (f.question_type === 'mcq') {
    payload.options = f.options
      .map((o, i) => ({
        option_label: (o.option_label || '').trim() || String.fromCharCode(65 + i),
        option_text: (o.option_text || '').trim(),
        is_correct: !!o.is_correct,
      }))
      .filter((o) => o.option_text)
    if (!payload.options.some(option => option.is_correct)) throw validationError('validation.mcqCorrectRequired')
  }
  if (f.question_type === 'sql') {
    const names = new Set()
    payload.datasets = JSON.parse(f.datasets || '[]').map((dataset, index) => {
      const base = dataset.dataset_name?.trim() || `dataset_${index + 1}`
      let name = base
      let suffix = 2
      while (names.has(name)) name = `${base}_${suffix++}`
      names.add(name)
      return { ...dataset, dataset_name: name, expected_result: { ...dataset.expected_result, ordered: false, check_columns: false } }
    })
  }
  if (f.question_type === 'essay') {
    const points = Number(f.points)
    if (!Number.isFinite(points) || points < 0.03 || Math.abs(points * 100 - Math.round(points * 100)) > 0.000001)
      throw validationError('admin.questions.rubricPointsError')
    payload.rubrics = rubricRows(f.rubrics, f.points)
    if (payload.rubrics.some(row => !row.criteria.trim())) throw validationError('admin.questions.rubricCriteriaRequired')
  }
  // Both display locales use the one piece of content entered by the admin.
  payload.translations = [{
    locale: 'vi', prompt: f.prompt,
    explanation: f.explanation?.trim() || null,
    option_texts: Object.fromEntries((payload.options || []).map(o => [o.option_label, o.option_text])),
    rubrics: Object.fromEntries((payload.rubrics || []).map(r => [r.level_name, { label: r.level_name, criteria: r.criteria }])),
  }]
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
            <input required value={o.option_text}
              onChange={(e) => set(i, { option_text: e.target.value })}
              placeholder={t('admin.questions.optionText', { number: o.option_label || i + 1 })}
              aria-label={t('admin.questions.optionText', { number: i + 1 })}
              className={`${inputCls} min-w-0 flex-[1_1_12rem]`} />
            <label className="flex shrink-0 items-center gap-1 text-xs text-sub">
              <input
                type="checkbox"
                aria-label={t('admin.questions.correctOption', { label: o.option_label || i + 1 })}
                checked={!!o.is_correct}
                onChange={event => set(i, { is_correct: event.target.checked })}
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
  const [previewIndex, setPreviewIndex] = useState(null)
  const [editing, setEditing] = useState(null) // question_id being replaced
  const [suggesting, setSuggesting] = useState(null)
  const [suggestion, setSuggestion] = useState(null) // TagSuggestionResult
  const [busy, setBusy] = useState(false)
  const [editorOpen, setEditorOpen] = useState(false)
  const [conceptCatalog, setConceptCatalog] = useState(null)
  const [conceptError, setConceptError] = useState('')
  const [page, setPage] = useState(1)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [deleting, setDeleting] = useState(false)
  const [expandedId, setExpandedId] = useState(null)

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
  useEffect(() => {
    if (!editorOpen) return
    let cancelled = false
    setConceptCatalog(null)
    setConceptError('')
    api.get('/admin/concepts').then(response => {
      if (!cancelled) setConceptCatalog(response.data)
    }).catch(err => { if (!cancelled) setConceptError(apiMessage(err)) })
    return () => { cancelled = true }
  }, [editorOpen])

  function toggleConcept(id, checked) {
    setForm(current => {
      const selected = new Set(current.concept_ids.split(',').filter(Boolean).map(Number))
      if (checked) selected.add(id)
      else selected.delete(id)
      return { ...current, concept_ids: [...selected].join(',') }
    })
  }

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
      explanation: d.explanation || '',
      tags: d.tags || [],
      source_refs: d.source_refs || [],
      difficulty_level: d.difficulty_level,
      points: d.points,
      concept_ids: d.concepts.filter((c) => c.confirmed).map((c) => c.concept_id).join(','),
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
    'rounded-md border border-edge2 bg-panel px-2 py-1.5 text-sm text-ink focus:border-cyan-400/60 focus:outline-none'
  const pageCount = Math.ceil((items?.length || 0) / 12)
  const currentPage = Math.min(page, pageCount || 1)
  const activeFilterCount = Object.values(filters).filter(Boolean).length
  const sqlDatasets = previewDatasets(form.datasets)
  const activePreviewIndex = previewIndex !== null && sqlDatasets[previewIndex] ? previewIndex : Math.max(0, sqlDatasets.findIndex(dataset => !dataset.is_edge_case))
  function updateQuestionText(field, value) {
    setForm(current => ({ ...current, [field]: value, ...(current.question_type === 'sql' ? {
      datasets: JSON.stringify(previewDatasets(current.datasets).map(dataset => {
        const { columns, rows, ...options } = dataset.expected_result || {}
        return { ...dataset, expected_result: options }
      }))
    } : {}) }))
  }
  function useActualAnswer(output) {
    setForm(current => {
      const datasets = previewDatasets(current.datasets)
      return { ...current, datasets: JSON.stringify(datasets.map((dataset, i) => i === activePreviewIndex ? { ...dataset, expected_result: { ...dataset.expected_result, ...output, ordered: false, check_columns: false } } : dataset)) }
    })
  }

  return (
    <div data-admin-view="questions" className="space-y-4">
      <AdminPageHeader icon="edit"
        title={t('admin.questions.title')}
        subtitle={t('admin.questions.subtitle')}
      >
        <button type="button" onClick={() => { setEditing(null); setForm(createQuestionForm()); setEditorOpen((open) => !open) }} className={editorOpen ? btnGhost : btnPrimary}>
          {editorOpen ? t('admin.closeEditor') : t('admin.questions.new')}
        </button>
      </AdminPageHeader>

      {/* ---------- filters ---------- */}
      <FilterBar className="question-filter-bar"
        activeCount={activeFilterCount}
        onClear={() => setFilters({ question_type: '', status: '', difficulty: '', concept_id: '', q: '' })}

      >
        <label className="question-search-label">{t('admin.questions.search')}
        <input
          placeholder={t('admin.questions.searchPlaceholder')}
          aria-label={t('admin.questions.search')}
          value={filters.q}
          onChange={(e) => setFilters({ ...filters, q: e.target.value })}
          className={`${inputCls} !py-1.5 min-w-[10rem] flex-1`}
        />
        </label>
        <label className="question-filter-label">{t('admin.questions.filterType')}<select value={filters.question_type} aria-label={t('admin.questions.filterType')}
          onChange={(e) => setFilters({ ...filters, question_type: e.target.value })}
          className={selCls}>
          <option value="">{t('admin.questions.allTypes')}</option>
          <option value="mcq">{typeLabel('mcq')}</option>
          <option value="sql">{typeLabel('sql')}</option>
          <option value="essay">{typeLabel('essay')}</option>
        </select></label>
        <label className="question-filter-label">{t('admin.questions.filterStatus')}<select value={filters.status} aria-label={t('admin.questions.filterStatus')}
          onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          className={selCls}>
          <option value="">{t('admin.questions.allStatuses')}</option>
          <option value="draft">{statusLabel('draft')}</option>
          <option value="validated">{statusLabel('validated')}</option>
          <option value="retired">{statusLabel('retired')}</option>
        </select></label>


          <label className="question-filter-label">{t('admin.questions.filterDifficulty')}<select value={filters.difficulty} aria-label={t('admin.questions.filterDifficulty')}
            onChange={(e) => setFilters({ ...filters, difficulty: e.target.value })}
            className={selCls}>
            <option value="">{t('admin.questions.allDifficulties')}</option>
            {[1, 2, 3, 4, 5].map((d) => <option key={d} value={d}>{t('exam.difficulty', { value: number(d) })}</option>)}
          </select></label>
          <label className="question-filter-label">{t('admin.questions.filterConcept')}<select value={filters.concept_id} aria-label={t('admin.questions.filterConcept')} onChange={(e) => setFilters({ ...filters, concept_id: e.target.value })} className={selCls}>
            <option value="">{t('admin.questions.allConcepts')}</option>
            {conceptOptions.map((c) => <option key={c.concept_id} value={c.concept_id}>{c.concept_code}</option>)}
          </select></label>

      </FilterBar>

      {items !== null && <div className="question-bank-summary" aria-label={t('admin.questions.filteredSummary')}>
        <span className="text-xs text-mute">{t('admin.questions.filteredSummary')}</span>
        {['mcq', 'sql', 'essay'].map(type => <span key={type} className="question-summary-item"><strong>{number(items.filter(question => question.question_type === type).length)}</strong>{typeLabel(type)}</span>)}
      </div>}

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
      {editorOpen && <Card className="question-bank-editor overflow-hidden">
        <CardTitle title={editing ? t('admin.questions.edit', { id: editing }) : t('admin.questions.new')} />
        <form onSubmit={save} className="question-editor-form grid gap-4 p-4 text-sm sm:p-5">
          <FormSection title={t('admin.questions.sectionBasics')}>
            <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
              <select value={form.question_type} aria-label={t('admin.questions.type')}
                onChange={e => setForm(current => ({ ...current, question_type: e.target.value, ...(e.target.value === 'sql' && !previewDatasets(current.datasets).length ? { datasets: JSON.stringify([{ dataset_name: 'dataset_1', setup_sql: '', expected_result: {}, is_edge_case: false }]) } : {}) }))}
                className={`${selCls} w-full sm:w-56`}>
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
                  onChange={(e) => setForm({ ...form, points: e.target.value, rubrics: JSON.stringify(rubricRows(form.rubrics, e.target.value, true)) })}
                  className="w-20 rounded-md border border-edge2 px-2 py-1.5 focus:border-cyan-400/60 focus:outline-none" />
              </label>
            </div>
          </FormSection>
          <FormSection title={t('admin.questions.sectionPrompt')}>
            <textarea required aria-label={t('admin.questions.prompt')} placeholder={t('admin.questions.promptPlaceholder')} value={form.prompt} rows={4}
              onChange={(e) => updateQuestionText('prompt', e.target.value)}
              className={inputCls} />
          </FormSection>
          {form.question_type === 'sql' && <FormSection title={t('admin.questions.sqlInputSection')}>
            <div className="sql-grading-config"><SqlDatasetsEditor value={form.datasets} onChange={datasets => setForm({ ...form, datasets })} /></div>
          </FormSection>}
          <FormSection title={t('admin.questions.sectionAnswer')}>
            {form.question_type === 'sql' ? <div>
              <p className="mb-2 text-xs font-semibold text-sub">{t('admin.questions.reference')}</p>
              <div className="sql-admin-editor"><div className="sql-admin-toolbar"><span>answer.sql</span><span>PostgreSQL</span></div>
                <SqlEditor compact rows={7} label={t('admin.questions.reference')} value={form.reference_answer} onChange={reference_answer => updateQuestionText('reference_answer', reference_answer)} />
              </div>
              <SqlAnswerPreview key={activePreviewIndex} promptText={form.prompt} sql={form.reference_answer} setupSql={sqlDatasets[activePreviewIndex]?.setup_sql || ''} onUseResult={useActualAnswer} datasetControl={sqlDatasets.length > 1 ? <label className="flex flex-wrap items-center gap-2 text-xs text-sub">{t('admin.questions.sqlRunScenario')}<select aria-label={t('admin.questions.sqlRunScenario')} className={selCls} value={activePreviewIndex} onChange={e => setPreviewIndex(Number(e.target.value))}>{sqlDatasets.map((dataset, i) => <option key={i} value={i}>{dataset.dataset_name || t('admin.questions.sqlDatasetName', { index: i + 1 })}</option>)}</select></label> : null} />
            </div> : form.question_type === 'essay' ? <label className="grid gap-2 text-xs font-medium text-sub">{t('admin.questions.reference')}
              <textarea rows={6} aria-label={t('admin.questions.reference')} placeholder={t('admin.questions.referenceHint')} value={form.reference_answer}
                onChange={(e) => setForm({ ...form, reference_answer: e.target.value })} className={`${inputCls} w-full min-h-40 resize-y !text-sm`} />
            </label> : null}
            {form.question_type === 'mcq' && (
              <OptionsEditor
                options={form.options}
                onChange={(options) => setForm({ ...form, options })}
              />
            )}
            {form.question_type === 'essay' && (
              <EssayRubricEditor value={form.rubrics} points={form.points} onChange={rubrics => setForm({ ...form, rubrics })} />
            )}
          </FormSection>

          <FormSection title={t('admin.questions.sectionConcepts')}>
            <p className="text-sm text-sub">{t('admin.questions.curriculumConceptHelp')}</p>
            {conceptError ? <ErrorState message={conceptError} /> : conceptCatalog === null ? <Loading /> : !conceptCatalog.length ? <p className="text-sm text-sub">{t('admin.questions.noCurriculumConcepts')} <a href="/admin/curriculum" className="underline underline-offset-4">{t('nav.curriculum')}</a></p> :
              <div className="grid gap-3 sm:grid-cols-2">
                {conceptCatalog.map(concept => {
                  const selected = form.concept_ids.split(',').map(Number).includes(concept.concept_id)
                  return <div key={concept.concept_id} className={`rounded-lg border p-3 ${selected ? 'border-edge2 bg-elev' : 'border-edge'}`}>
                    <label className="flex cursor-pointer items-start gap-3 text-sm text-ink">
                      <input type="checkbox" className="mt-1 h-4 w-4 shrink-0" checked={selected} onChange={event => toggleConcept(concept.concept_id, event.target.checked)} />
                      <span><span className="font-medium">{concept.concept_name}</span><span className="mt-1 block text-xs text-mute">{concept.concept_code} · {concept.subject_area}</span></span>
                    </label>

                  </div>
                })}
              </div>}
          </FormSection>
          <details open={!!editing} className="rounded-lg border border-edge/70 px-3 py-2.5">
            <summary className="cursor-pointer text-xs font-semibold uppercase tracking-wide text-mute focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-400/60">
              {t('admin.questions.sectionSource')}
            </summary>
            <div className="mt-2 space-y-2 text-xs text-sub">
              <p>{t('admin.questions.tags', { ids: form.tags.join(', ') || '—' })}</p>
              {form.source_refs?.length ? (
                <ul className="space-y-1">
                  {form.source_refs.map((s, i) => (
                    <li key={i}>
                      <a href={s.url} target="_blank" rel="noreferrer"
                        className="text-cyan-300/80 underline decoration-dotted underline-offset-2 hover:text-cyan-200">
                        {t('admin.questions.sourceRef', { title: s.title || s.section || s.url, version: s.version || '?' })}
                      </a>
                    </li>
                  ))}
                </ul>
              ) : (
                <p>{t('admin.questions.noSources')}</p>
              )}
            </div>
          </details>
          <div className="question-editor-actions flex flex-wrap gap-2">
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
        <Card className="question-bank-list overflow-hidden">
          <CardTitle title={t('admin.questions.count', { count: items.length })} />
          <ul className="question-bank-rows text-sm">
            {items.slice((currentPage - 1) * 12, currentPage * 12).map((q) => (
              <li key={q.question_id} className="question-bank-item">
                <div className="question-item-header flex flex-wrap items-center gap-2">
                  <span className="font-mono text-xs text-faint">#{q.question_id}</span>
                  <TypeBadge type={q.question_type} />
                  <StatusBadge status={q.status} />
                  {q.legacy_rubric && <Badge title={t('admin.questions.legacyRubricHint')} className="whitespace-nowrap">{t('admin.questions.legacyRubric')}</Badge>}
                  <span className="ml-auto flex items-center gap-1">
                    <button type="button" onClick={() => edit(q)} className="px-1.5 py-1 text-xs font-medium text-cyan-300 hover:underline">{t('common.edit')}</button>
                    <button type="button"
                      aria-expanded={expandedId === q.question_id}
                      aria-label={t('common.details')}
                      onClick={() => setExpandedId(expandedId === q.question_id ? null : q.question_id)}
                      className="rounded-md p-1.5 text-mute transition-colors hover:bg-surface-hover hover:text-ink">
                      <Icon name="chevronDown" className={`h-4 w-4 transition-transform ${expandedId === q.question_id ? 'rotate-180' : ''}`} />
                    </button>
                    <RowMenu>
                      <MenuItem onSelect={() => aiTags(q)} disabled={suggesting === q.question_id}>
                        {suggesting === q.question_id ? t('admin.questions.suggesting') : t('admin.questions.aiTags')}
                      </MenuItem>
                      {q.status !== 'validated' && !q.legacy_rubric && (
                        <MenuItem onSelect={() => run(() => api.patch(`/admin/questions/${q.question_id}`, { status: 'validated' }), message('admin.questions.validated'))}>
                          {t('admin.validate')}
                        </MenuItem>
                      )}
                      {q.status === 'validated' && (
                        <MenuItem onSelect={() => run(() => api.patch(`/admin/questions/${q.question_id}`, { status: 'retired' }), message('admin.questions.retired'))}>
                          {t('admin.questions.retire')}
                        </MenuItem>
                      )}
                      <div className="my-1 border-t border-edge/70" aria-hidden="true" />
                      <MenuItem danger onSelect={() => setDeleteTarget(q)}>{t('common.delete')}</MenuItem>
                    </RowMenu>
                  </span>
                </div>
                <p className="question-item-prompt">{q.prompt}</p>
                <p className="question-item-meta">{t('exam.difficulty', { value: number(q.difficulty_level) })}<span aria-hidden="true"> &middot; </span>{t('admin.questions.linkedCount', { count: (q.concepts || []).filter(concept => concept.confirmed).length })}</p>
                {expandedId === q.question_id && (
                  <div className="mt-2.5 space-y-2 border-t border-edge/60 pt-2.5">
                    <div className="flex flex-wrap items-center gap-2 text-xs">
                      <Badge>{t('exam.difficulty', { value: number(q.difficulty_level) })}</Badge>
                      <Badge>{statusLabel(q.source)}</Badge>
                    </div>
                    {q.concepts?.length > 0 && (
                      <div className="flex flex-wrap gap-1 text-xs">
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
                    {q.source_refs?.length > 0 && (
                      <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs">
                        {q.source_refs.map((s, i) => (
                          <a key={i} href={s.url} target="_blank" rel="noreferrer"
                            className="text-cyan-300/80 underline decoration-dotted underline-offset-2 hover:text-cyan-200"
                            title={s.url}>
                            {t('admin.questions.sourceRef', { title: s.title || s.section || s.url, version: s.version || '?' })}
                          </a>
                        ))}
                      </div>
                    )}
                    {q.ai_review && <div className="rounded-lg border border-edge bg-elev/50 p-3 text-xs text-sub">
                      <p className="font-medium">{t('admin.questions.aiReview', { status: statusLabel(q.ai_review.status) })}</p>
                      <p className="mt-1">{t('admin.questions.suggestedDifficulty', { value: number(q.ai_review.difficulty_level) })}</p>
                      <p className="mt-1">{q.ai_review.evaluation_criteria}</p>
                      {q.ai_review.status === 'pending' && <div className="mt-2 flex flex-wrap gap-3">
                        <button type="button" onClick={() => run(() => api.post(`/admin/questions/${q.question_id}/ai-review`, { decision: 'confirmed', apply_difficulty: true }), message('admin.questions.approvedSuggestion'))} className="font-medium text-emerald-300 underline">{t('admin.questions.approveCriteria')}</button>
                        <button type="button" onClick={() => run(() => api.post(`/admin/questions/${q.question_id}/ai-review`, { decision: 'rejected' }), message('admin.rejectedSuggestion'))} className="font-medium text-rose-300 underline">{t('admin.questions.rejectSuggestion')}</button>
                      </div>}
                    </div>}
                  </div>
                )}
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
