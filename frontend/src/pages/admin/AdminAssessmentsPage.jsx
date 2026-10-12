import { t, useLocale, message, number, percent, dateTime, statusLabel, typeLabel, validationError, resources } from '../../i18n'
import { resolveMessage } from '../../i18n'
import { useCallback, useEffect, useRef, useState } from 'react'
import api, { apiMessage } from '../../api'
import { EmptyState, ErrorState, Loading } from '../../components/States'
import { Badge, Card, CardTitle, ConfirmDialog, Notice, PageHeader, StatusBadge, btnGhost, btnPrimary, inputCls, focusDialogTrigger } from '../../components/ui'

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
  'w-16 rounded-md border border-edge2 px-1.5 py-1.5 text-sm focus:border-cyan-400/60 focus:outline-none'

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
        max_questions: 13,
        duration_min: 60,
        target_mcq: 10,
        target_sql: 2,
        target_essay: 1,
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

  return (
    <div className="space-y-4">
      <PageHeader
        title={t('admin.assessments.title')}
        subtitle={t('admin.assessments.subtitle')}
      >
        <button type="button" disabled={busy} onClick={() => { setEditing(null); setForm(EMPTY); setShowForm((open) => !open) }} className={showForm ? btnGhost : btnPrimary}>{showForm ? t('admin.closeEditor') : t('admin.assessments.new')}</button>
      </PageHeader>
      {busy && <p role="status" className="text-sm text-sub">{t('admin.assessments.saving')}</p>}

      {showForm && <Card className="overflow-hidden">
        <CardTitle title={editing ? t('admin.assessments.edit', { id: editing }) : t('admin.assessments.new')} />
        <form onSubmit={save} className="grid gap-3 p-4 text-sm">
          <div className="grid gap-2 sm:grid-cols-2">
            <input required aria-label={t('admin.assessments.formTitle')} maxLength={200} placeholder={t('common.title')} value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className={inputCls} />
            <input aria-label={t('admin.assessments.description')} placeholder={t('common.description')} value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className={inputCls} />
          </div>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5 text-sub">
            <label className="flex items-center gap-1.5">{t('admin.assessments.maxQuestions')}<input type="number" readOnly value={13}
                onChange={(e) => setForm({ ...form, max_questions: e.target.value })}
                className={numCls} /></label>
            <label className="flex items-center gap-1.5">{t('admin.assessments.minutes')}<input type="number" readOnly value={60}
                onChange={(e) => setForm({ ...form, duration_min: e.target.value })}
                className={numCls} /></label>
            <label className="flex items-center gap-1.5">{typeLabel('mcq')}
              <input type="number" readOnly value={10}
                onChange={(e) => setForm({ ...form, target_mcq: e.target.value })}
                className={numCls} /></label>
            <label className="flex items-center gap-1.5">{typeLabel('sql')}
              <input type="number" readOnly value={2}
                onChange={(e) => setForm({ ...form, target_sql: e.target.value })}
                className={numCls} /></label>
            <label className="flex items-center gap-1.5">{typeLabel('essay')}
              <input type="number" readOnly value={1}
                onChange={(e) => setForm({ ...form, target_essay: e.target.value })}
                className={numCls} /></label>
          </div>

          <p className="mt-1 text-xs font-medium uppercase tracking-wide text-mute">{t('admin.assessments.targets')}</p>
          {form.concepts.map((c, i) => (
            <div key={i} className="flex flex-wrap items-center gap-2">
              <select required aria-label={t('admin.assessments.targetConcept', { number: i + 1 })} value={c.concept_id}
                onChange={(e) => setConceptRow(i, 'concept_id', e.target.value)}
                className="rounded-md border border-edge2 px-2 py-1.5 text-sm focus:border-cyan-400/60 focus:outline-none">
                <option value="">{t('admin.assessments.selectConcept')}</option>
                {concepts.map((k) => (
                  <option key={k.concept_id} value={k.concept_id}>{k.concept_code}</option>
                ))}
              </select>
              <label className="text-xs text-sub">{t('common.difficulty')}
                <input type="number" min="1" max="5" value={c.min_difficulty}
                  onChange={(e) => setConceptRow(i, 'min_difficulty', e.target.value)}
                  className="ml-1 w-12 rounded-md border border-edge2 px-1.5 py-1 focus:border-cyan-400/60 focus:outline-none" />
                {' '}–{' '}
                <input type="number" min="1" max="5" aria-label={t('admin.assessments.maxDifficulty', { number: i + 1 })} value={c.max_difficulty}
                  onChange={(e) => setConceptRow(i, 'max_difficulty', e.target.value)}
                  className="w-12 rounded-md border border-edge2 px-1.5 py-1 focus:border-cyan-400/60 focus:outline-none" />
              </label>
              <label className="text-xs text-sub">{t('admin.assessments.benchmark')}<input value={c.target_pct}
                  onChange={(e) => setConceptRow(i, 'target_pct', e.target.value)}
                  className="ml-1 w-16 rounded-md border border-edge2 px-1.5 py-1 focus:border-cyan-400/60 focus:outline-none" />
              </label>
              <button type="button"
                onClick={() => setForm((f) => ({ ...f, concepts: f.concepts.filter((_, j) => j !== i) }))}
                disabled={form.concepts.length <= 1}
                className="text-xs font-medium text-rose-300 hover:underline disabled:opacity-40">{t('admin.remove')}
              </button>
            </div>
          ))}
          <button type="button"
            onClick={() => setForm((f) => ({
              ...f,
              concepts: [...f.concepts, { concept_id: '', min_difficulty: 1, max_difficulty: 5, target_pct: '60.00' }],
            }))}
            className="w-fit text-xs font-medium text-cyan-300 hover:underline">{t('admin.assessments.addConcept')}</button>
          <div className="flex gap-2">
            <button type="submit" disabled={busy} className={btnPrimary}>
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
        <Card className="overflow-hidden">
          <CardTitle title={t('admin.assessments.count', { count: items.length })} />
          <ul className="divide-y divide-edge text-sm">
            {items.map((a) => (
              <li key={a.assessment_id} className="px-5 py-4 transition-colors hover:bg-surface-hover">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium text-ink">{a.title}</span>
                  <StatusBadge status={a.status} />
                  <Badge>
                    {t('admin.assessments.summary', { questions: number(a.max_questions), minutes: number(a.duration_min), concepts: number(a.target_count), sessions: number(a.session_count) })}
                  </Badge>
                  <span className="ml-auto flex gap-3 text-xs">
                    {a.status === 'draft' && (
                      <>
                        <button type="button" disabled={busy} onClick={() => startEdit(a)} className="font-medium text-cyan-300 hover:underline">{t('common.edit')}</button>
                        <button type="button" disabled={busy}
                          onClick={() => run(() => api.patch(`/admin/assessments/${a.assessment_id}`, { status: 'published' }), message('admin.assessments.published'))}
                          className="font-medium text-emerald-300 hover:underline">{t('admin.activate')}</button>
                        <button type="button" disabled={busy}
                          onClick={(event) => { focusDialogTrigger(event); setDeleteTarget(a) }}
                          className="font-medium text-rose-300 hover:underline">{t('common.delete')}</button>
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
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </Card>
      )}
      <ConfirmDialog open={!!deleteTarget} title={t('admin.assessments.deleteTitle')} confirmLabel={deleting ? t('common.deleting') : t('admin.assessments.delete')} cancelLabel={t('common.cancel')} busy={deleting} onConfirm={deleteAssessment} onCancel={() => setDeleteTarget(null)}>
        {t('admin.assessments.deleteBody', { title: deleteTarget?.title || '' })}
        {error && <p role="alert" className="mt-2 text-rose-300">{resolveMessage(error)}</p>}
      </ConfirmDialog>
    </div>
  )
}
