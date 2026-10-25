import { t, useLocale, message, number, statusLabel } from '../../i18n'
import { resolveMessage } from '../../i18n'
import { useCallback, useEffect, useRef, useState } from 'react'
import api, { apiMessage } from '../../api'
import { EmptyState, ErrorState, Loading } from '../../components/States'
import { Card, CardTitle, ConfirmDialog, Notice, StatusBadge, btnGhost, btnPrimary, inputCls } from '../../components/ui'
import { AdminPageHeader, FormSection, MenuItem, RowMenu, SegmentedFilter } from '../../components/admin'

const EMPTY = {
  title: '',
  description: '',
  max_questions: 13,
  duration_min: 60,
  target_mcq: 10,
  target_sql: 2,
  target_essay: 1,
  result_release_policy: 'IMMEDIATE',
  concepts: [],
}

// UC09 — adaptive assessment configuration (draft → active → closed).
export default function AdminAssessmentsPage() {
  useLocale()
  const [items, setItems] = useState(null)
  const [concepts, setConcepts] = useState([])
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [form, setForm] = useState(EMPTY)
  const [editing, setEditing] = useState(null)
  const [busy, setBusy] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [deleting, setDeleting] = useState(false)
  const [statusFilter, setStatusFilter] = useState('')
  const mutationRef = useRef(false)

  const load = useCallback(() => {
    setError('')
    return Promise.all([
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

  useEffect(() => { load() }, [load])

  async function run(fn, okMsg) {
    if (mutationRef.current) return null
    mutationRef.current = true
    setBusy(true)
    setError('')
    setNotice('')
    try {
      const response = await fn()
      if (okMsg) setNotice(okMsg)
      await load()
      return response
    } catch (e) {
      setError(apiMessage(e))
      return null
    } finally {
      mutationRef.current = false
      setBusy(false)
    }
  }

  function setConceptRow(i, key, value) {
    setForm(f => ({ ...f, concepts: f.concepts.map((c, j) => j === i ? { ...c, [key]: value } : c) }))
  }

  function toggleConcept(id) {
    setForm(f => ({
      ...f,
      concepts: f.concepts.some(c => Number(c.concept_id) === id)
        ? f.concepts.filter(c => Number(c.concept_id) !== id)
        : [...f.concepts, { concept_id: id, min_difficulty: 1, max_difficulty: 5, target_pct: '60.00' }],
    }))
  }

  async function save(e) {
    e.preventDefault()
    if (!form.concepts.length) { setError(message('admin.assessments.chooseRequired')); return }
    setBusy(true)
    try {
      const payload = {
        title: form.title,
        description: form.description || null,
        max_questions: 13,
        duration_min: 60,
        target_mcq: 10,
        target_sql: 2,
        target_essay: 1,
        result_release_policy: form.result_release_policy || 'IMMEDIATE',
        concepts: form.concepts.map((c) => ({
          concept_id: Number(c.concept_id),
          min_difficulty: Number(c.min_difficulty),
          max_difficulty: Number(c.max_difficulty),
          target_pct: String(c.target_pct),
        })),
      }
      const saved = editing
        ? await run(() => api.put(`/admin/assessments/${editing}`, payload), message('admin.assessments.updated'))
        : await run(() => api.post('/admin/assessments', payload), message('admin.assessments.created'))
      if (saved) {
        setEditing(null)
        setForm(EMPTY)
        setShowForm(false)
      }
    } finally {
      setBusy(false)
    }
  }

  function startEdit(a) {
    api.get(`/admin/assessments/${a.assessment_id}`).then((r) => {
      const d = r.data
      setEditing(a.assessment_id)
      setShowForm(true)
      setForm({
        title: d.title,
        result_release_policy: d.result_release_policy || 'IMMEDIATE',
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
      window.scrollTo({ top: 0, behavior: window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' })
    }).catch((e) => setError(apiMessage(e, message('admin.assessments.openError'))))
  }

  async function deleteAssessment() {
    if (!deleteTarget || deleting) return
    setDeleting(true)
    const deleted = await run(() => api.delete(`/admin/assessments/${deleteTarget.assessment_id}`), message('admin.assessments.deleted'))
    setDeleting(false)
    if (deleted) setDeleteTarget(null)
  }

  const statusCounts = (items || []).reduce((acc, a) => ({ ...acc, [a.status]: (acc[a.status] || 0) + 1 }), {})
  const visibleItems = (items || []).filter((a) => !statusFilter || a.status === statusFilter)

  return (
    <div data-admin-view="assessments" className="space-y-4">
      <AdminPageHeader icon="file"
        title={t('admin.assessments.title')}
        subtitle={t('admin.assessments.subtitle')}
      >
        <button type="button" disabled={busy} onClick={() => { setEditing(null); setForm(EMPTY); setShowForm((open) => !open) }} className={showForm ? btnGhost : btnPrimary}>{showForm ? t('admin.closeEditor') : t('admin.assessments.new')}</button>
      </AdminPageHeader>
      <div className="grid gap-3 sm:grid-cols-3">
        {['stepBank', 'stepScope', 'stepOpen'].map((key, i) => <div key={key} className="flex items-start gap-3 rounded-xl border border-edge bg-panel p-4">
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent/10 text-sm font-semibold text-accent">{i + 1}</span>
          <p className="text-sm leading-relaxed text-sub">{t(`admin.assessments.${key}`)}</p>
        </div>)}
      </div>
      {busy && <p role="status" className="text-sm text-sub">{t('admin.assessments.saving')}</p>}

      {showForm && <Card className="overflow-hidden">
        <CardTitle title={editing ? t('admin.assessments.edit', { id: editing }) : t('admin.assessments.new')} />
        <form onSubmit={save} className="grid gap-4 p-4 text-sm sm:p-5">
          <FormSection title={t('admin.assessments.sectionGeneral')} className="!border-t-0 !pt-0">
            <div className="grid gap-2 sm:grid-cols-2">
              <input required aria-label={t('admin.assessments.formTitle')} maxLength={200} placeholder={t('common.title')} value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                className={inputCls} />
              <input aria-label={t('admin.assessments.description')} placeholder={t('common.description')} value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                className={inputCls} />
            </div>
            <p className="text-xs text-mute">{t('admin.assessments.contract')}</p>
          </FormSection>

          <FormSection title={t('admin.assessments.sectionTargets')}>
            <p className="text-sm text-sub">{t('admin.assessments.selectionHelp')}</p>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <span className="text-sm font-medium text-ink">{t('admin.assessments.selectedCount', { count: form.concepts.length })}</span>
              <button type="button" className={btnGhost} onClick={() => setForm(f => ({
                ...f,
                concepts: concepts.map(k => f.concepts.find(c => Number(c.concept_id) === k.concept_id) || {
                  concept_id: k.concept_id, min_difficulty: 1, max_difficulty: 5, target_pct: '60.00',
                }),
              }))}>{t('admin.assessments.selectAll')}</button>
            </div>
            <div className="grid max-h-80 gap-2 overflow-y-auto pr-1 sm:grid-cols-2">
              {concepts.map(k => {
                const selected = form.concepts.some(c => Number(c.concept_id) === k.concept_id)
                return <label key={k.concept_id} className={`flex cursor-pointer items-start gap-3 rounded-xl border p-3 transition-colors ${selected ? 'border-accent/40 bg-accent/5' : 'border-edge bg-panel hover:bg-surface-hover'}`}>
                  <input type="checkbox" checked={selected} onChange={() => toggleConcept(k.concept_id)} className="mt-1 h-4 w-4 shrink-0 accent-[var(--primary)]" />
                  <span className="min-w-0"><span className="block font-medium text-ink">{k.concept_name || k.concept_code}</span><span className="mt-1 block text-xs text-sub">{k.concept_code}</span></span>
                </label>
              })}
            </div>
            {!concepts.length && <p className="text-sm text-sub">{t('admin.assessments.noConcepts')}</p>}
          </FormSection>

          <details className="rounded-xl border border-edge bg-panel p-4">
            <summary className="cursor-pointer font-medium text-ink">{t('admin.assessments.advanced')}</summary>
            <div className="mt-4 space-y-4">
              <p className="text-sm text-sub">{t('admin.assessments.advancedHelp')}</p>
              {form.concepts.map((c, i) => <div key={c.concept_id} className="grid items-end gap-3 rounded-lg border border-edge p-3 sm:grid-cols-4">
                <span className="self-center text-sm font-medium text-ink">{concepts.find(k => k.concept_id === Number(c.concept_id))?.concept_name || concepts.find(k => k.concept_id === Number(c.concept_id))?.concept_code || c.concept_id}</span>
                <label className="text-xs text-sub">{t('admin.assessments.minDifficulty')}
                  <input required type="number" min="1" max={c.max_difficulty} value={c.min_difficulty} onChange={e => setConceptRow(i, 'min_difficulty', e.target.value)} className={`${inputCls} mt-2 w-full`} />
                </label>
                <label className="text-xs text-sub">{t('admin.assessments.maxDifficulty', { number: i + 1 })}
                  <input required type="number" min={c.min_difficulty} max="5" value={c.max_difficulty} onChange={e => setConceptRow(i, 'max_difficulty', e.target.value)} className={`${inputCls} mt-2 w-full`} />
                </label>
                <label className="text-xs text-sub">{t('admin.assessments.benchmark')}
                  <input required type="number" min="0" max="100" step="0.01" value={c.target_pct} onChange={e => setConceptRow(i, 'target_pct', e.target.value)} className={`${inputCls} mt-2 w-full`} />
                </label>
              </div>)}
            </div>
          </details>
          <div className="flex gap-2">
            <button type="submit" disabled={busy || !form.concepts.length} className={btnPrimary}>
              {busy ? t('common.saving') : editing ? t('common.saveChanges') : t('admin.assessments.createDraft')}
            </button>
            <button type="button" onClick={() => { setEditing(null); setForm(EMPTY); setShowForm(false) }} className={btnGhost}>{t('common.cancel')}</button>
          </div>
        </form>
      </Card>}

      {notice && <Notice>{notice}</Notice>}
      {error && <ErrorState message={resolveMessage(error)} />}

      {items === null ? (
        <Loading />
      ) : items.length === 0 ? (
        <EmptyState title={t('admin.assessments.empty')} />
      ) : (
        <>
          <SegmentedFilter
            ariaLabel={t('admin.assessments.filterStatus')}
            value={statusFilter}
            onChange={setStatusFilter}
            options={[
              { value: '', label: t('common.all'), count: items.length },
              { value: 'draft', label: statusLabel('draft'), count: statusCounts.draft || 0 },
              { value: 'published', label: statusLabel('published'), count: statusCounts.published || 0 },
              { value: 'closed', label: statusLabel('closed'), count: statusCounts.closed || 0 },
            ]}
          />
          <Card className="overflow-hidden">
            <CardTitle title={t('admin.assessments.count', { count: visibleItems.length })} />
            <ul className="divide-y divide-edge text-sm">
            {visibleItems.map((a) => (
              <li key={a.assessment_id} className="px-5 py-4 transition-colors hover:bg-surface-hover">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium text-ink">{a.title}</span>
                  <StatusBadge status={a.status} />
                  <span className="text-xs text-sub">{t('admin.assessments.learnerReleaseChoice')}</span>
                  <span className="ml-auto flex items-center gap-3 text-xs">
                    {a.status === 'draft' && (
                      <>
                        <button type="button" disabled={busy} onClick={() => startEdit(a)} className="font-medium text-cyan-300 hover:underline">{t('common.edit')}</button>
                        <button type="button" disabled={busy}
                          onClick={() => run(() => api.patch(`/admin/assessments/${a.assessment_id}`, { status: 'published' }), message('admin.assessments.published'))}
                          className="rounded-md bg-emerald-400/15 px-2.5 py-1 font-semibold text-emerald-300 ring-1 ring-inset ring-emerald-400/30 transition-colors hover:bg-emerald-400/25 disabled:opacity-50">{t('admin.assessments.publish')}</button>
                      </>
                    )}
                    {a.status === 'published' && (
                      <button type="button" disabled={busy}
                        onClick={() => run(() => api.patch(`/admin/assessments/${a.assessment_id}`, { status: 'closed' }), message('admin.assessments.closed'))}
                        className="font-medium text-amber-300 hover:underline">{t('common.close')}</button>
                    )}
                    {a.status === 'closed' && (
                      <button type="button" disabled={busy}
                        onClick={() => run(() => api.patch(`/admin/assessments/${a.assessment_id}`, { status: 'draft' }), message('admin.assessments.versionCreated'))}
                        className="font-medium text-cyan-300 hover:underline">{t('admin.assessments.newVersion')}</button>
                    )}
                    {a.status === 'draft' && (
                      <RowMenu>
                        <MenuItem danger onSelect={() => setDeleteTarget(a)}>{t('common.delete')}</MenuItem>
                      </RowMenu>
                    )}
                  </span>
                </div>
                <p className="mt-1.5 text-xs text-mute">
                  {t('admin.assessments.summary', { questions: number(a.max_questions), minutes: number(a.duration_min), concepts: number(a.target_count), sessions: number(a.session_count) })}
                </p>
              </li>
            ))}
            </ul>
          </Card>
        </>
      )}
      <ConfirmDialog open={!!deleteTarget} title={t('admin.assessments.deleteTitle')} confirmLabel={deleting ? t('common.deleting') : t('admin.assessments.delete')} cancelLabel={t('common.cancel')} busy={deleting} onConfirm={deleteAssessment} onCancel={() => setDeleteTarget(null)}>
        {t('admin.assessments.deleteBody', { title: deleteTarget?.title || '' })}
        {error && <p role="alert" className="mt-2 text-rose-300">{resolveMessage(error)}</p>}
      </ConfirmDialog>
    </div>
  )
}
