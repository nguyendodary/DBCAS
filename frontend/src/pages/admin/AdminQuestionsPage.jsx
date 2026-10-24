import { t, useLocale, message, number, statusLabel, typeLabel } from '../../i18n'
import { resolveMessage } from '../../i18n'
import { useCallback, useEffect, useRef, useState } from 'react'
import api, { apiMessage } from '../../api'
import { ActionSpinner, EmptyState, ErrorState, Loading } from '../../components/States'
import { Badge, Card, CardTitle, ConfirmDialog, Icon, Notice, Pagination, StatusBadge, TypeBadge, btnGhost, btnPrimary, inputCls } from '../../components/ui'
import { AdminPageHeader, FilterBar, MenuItem, RowMenu } from '../../components/admin'

import { QuestionAuthoring, createQuestionForm, questionToForm, formToPayload } from '../../components/QuestionAuthoring'

const PG_TOPICS = ['queries', 'data-types', 'functions', 'ddl', 'dml', 'concurrency', 'performance', 'security', 'server-programming', 'admin']

// UC07 + UC08 — the question bank plus AI tag review.
export default function AdminQuestionsPage() {
  const { locale } = useLocale()
  const [items, setItems] = useState(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [filters, setFilters] = useState({ question_type: '', status: '', difficulty: '', concept_id: '', tag: '', q: '' })
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
  const [expandedId, setExpandedId] = useState(null)

  const load = useCallback(() => {
    requestRef.current?.abort()
    const controller = new AbortController()
    requestRef.current = controller
    setError('')
    const params = Object.fromEntries(
      Object.entries({ question_type: filters.question_type, status: filters.status,
        difficulty: filters.difficulty, concept_id: filters.concept_id, tag: filters.tag, q: query }).filter(([, v]) => v !== '' && v !== null)
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
  }, [filters.question_type, filters.status, filters.difficulty, filters.concept_id, filters.tag, query])

  useEffect(() => { load(); return () => requestRef.current?.abort() }, [load])
  useEffect(() => {
    const controller = new AbortController()
    api.get('/admin/concepts', { signal: controller.signal }).then(r => {
      if (!controller.signal.aborted) setConceptOptions(r.data.filter(c => c.concept_id))
    }).catch(e => { if (!controller.signal.aborted && e.code !== 'ERR_CANCELED') setError(apiMessage(e)) })
    return () => controller.abort()
  }, [])
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
    setForm(questionToForm(d))
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

  return (
    <div className="space-y-4">
      <AdminPageHeader
        title={t('admin.questions.title')}
        subtitle={t('admin.questions.subtitle')}
      >
        <button type="button" onClick={() => { setEditing(null); setForm(createQuestionForm()); setEditorOpen((open) => !open) }} className={editorOpen ? btnGhost : btnPrimary}>
          {editorOpen ? t('admin.closeEditor') : t('admin.questions.new')}
        </button>
      </AdminPageHeader>

      {/* ---------- filters ---------- */}
      <FilterBar
        activeCount={activeFilterCount}
        onClear={() => setFilters({ question_type: '', status: '', difficulty: '', concept_id: '', tag: '', q: '' })}
        more={<>
          <select value={filters.difficulty} aria-label={t('admin.questions.filterDifficulty')}
            onChange={(e) => setFilters({ ...filters, difficulty: e.target.value })}
            className={selCls}>
            <option value="">{t('admin.questions.allDifficulties')}</option>
            {[1, 2, 3, 4, 5].map((d) => <option key={d} value={d}>{t('exam.difficulty', { value: number(d) })}</option>)}
          </select>
          <select value={filters.concept_id} aria-label={t('admin.questions.filterConcept')} onChange={(e) => setFilters({ ...filters, concept_id: e.target.value })} className={selCls}>
            <option value="">{t('admin.questions.allConcepts')}</option>
            {conceptOptions.map((c) => <option key={c.concept_id} value={c.concept_id}>{c.concept_code}</option>)}
          </select>
        </>}
      >
        <input
          placeholder={t('admin.questions.searchPlaceholder')}
          aria-label={t('admin.questions.search')}
          value={filters.q}
          onChange={(e) => setFilters({ ...filters, q: e.target.value })}
          className={`${inputCls} !py-1.5 min-w-[10rem] flex-1`}
        />
        <select value={filters.question_type} aria-label={t('admin.questions.filterType')}
          onChange={(e) => setFilters({ ...filters, question_type: e.target.value })}
          className={selCls}>
          <option value="">{t('admin.questions.allTypes')}</option>
          <option value="mcq">{typeLabel('mcq')}</option>
          <option value="sql">{typeLabel('sql')}</option>
          <option value="essay">{typeLabel('essay')}</option>
        </select>
        <select value={filters.status} aria-label={t('admin.questions.filterStatus')}
          onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          className={selCls}>
          <option value="">{t('admin.questions.allStatuses')}</option>
          <option value="draft">{statusLabel('draft')}</option>
          <option value="validated">{statusLabel('validated')}</option>
          <option value="retired">{statusLabel('retired')}</option>
        </select>
        <select value={filters.tag} aria-label={t('admin.questions.filterTopic')}
          onChange={(e) => setFilters({ ...filters, tag: e.target.value })}
          className={selCls}>
          <option value="">{t('admin.questions.allTopics')}</option>
          <option value="postgres">{t('admin.questions.allPostgres')}</option>
          {PG_TOPICS.map((slug) => <option key={slug} value={`postgres:${slug}`}>{t(`admin.questions.topic.${slug}`)}</option>)}
        </select>
      </FilterBar>

      {notice && <Notice>{notice}</Notice>}
      {error && !editorOpen && <ErrorState message={resolveMessage(error)} />}
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
        <form onSubmit={save} className="grid gap-4 p-4 text-sm sm:p-5">
          <QuestionAuthoring form={form} setForm={setForm} editing={editing} concepts={conceptOptions} />
          <details className="rounded-lg border border-edge/70 px-3 py-2.5">
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
          <p className="text-xs text-mute">{t('authoring.draftHelp')}</p>
          {error && <ErrorState message={resolveMessage(error)} />}
          <div className="flex gap-2">
            <button type="submit" disabled={busy}
              className={btnPrimary}>
              {busy && <ActionSpinner />}
              {busy ? t('common.saving') : editing ? t('common.saveChanges') : t('authoring.saveDraft')}
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
                  <StatusBadge status={q.status} />
                  {q.legacy_rubric && <Badge title={t('admin.questions.legacyRubricHint')} className="whitespace-nowrap">{t('admin.questions.legacyRubric')}</Badge>}
                  <Badge>{t('authoring.original', { language: t(`authoring.${q.original_locale || 'en'}`) })}</Badge>
                  <Badge>{q.translation_locales?.length ? t('authoring.translationAvailable', { languages: q.translation_locales.join(', ').toUpperCase() }) : t('authoring.noTranslation')}</Badge>
                  <span className="ml-auto flex shrink-0 items-center gap-1">
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
                <p lang={q.localized_prompts?.[locale] ? locale : q.original_locale || 'en'} className="mt-1.5 line-clamp-2 text-ink">{q.localized_prompts?.[locale] || q.prompt}</p>
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
