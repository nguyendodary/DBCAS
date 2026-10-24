import { t, useLocale, message, number, percent, dateTime, statusLabel, typeLabel, validationError, resources } from '../../i18n'
import { resolveMessage } from '../../i18n'
import { useCallback, useEffect, useState } from 'react'
import api, { apiMessage } from '../../api'
import { EmptyState, ErrorState, Loading } from '../../components/States'
import { Badge, Card, CardTitle, ConfirmDialog, Icon, Notice, StatusBadge, btnPrimary, inputCls, focusDialogTrigger } from '../../components/ui'
import { AdminPageHeader, SegmentedFilter } from '../../components/admin'
import { ConceptPicker } from '../../components/QuestionAuthoring'

// UC05/UC06 + skill graph — concept model, CLOs, mappings (incl. AI
// suggestions), and prerequisites.
export default function AdminCurriculumPage() {
  useLocale()
  const [concepts, setConcepts] = useState(null)
  const [clos, setClos] = useState(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)
  const [editingConcept, setEditingConcept] = useState(null)
  const [editingClo, setEditingClo] = useState(null)
  const [prerequisites, setPrerequisites] = useState({})
  const [conceptForm, setConceptForm] = useState({
    concept_code: '', concept_name: '', subject_area: '', description: '',
    difficulty_level: 1, sql_feature: null,
  })
  const [cloForm, setCloForm] = useState({ clo_code: '', title: '', description: '' })
  const [prereqEdit, setPrereqEdit] = useState({}) // concept_id -> "1,2"
  const [linkEdit, setLinkEdit] = useState({})   // clo_id -> "3,4"
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [deleting, setDeleting] = useState(false)
  const [tab, setTab] = useState('concepts')
  const [conceptQuery, setConceptQuery] = useState('')
  const [showAll, setShowAll] = useState(false)

  const load = useCallback(() => {
    setError('')
    return Promise.all([api.get('/admin/concepts'), api.get('/admin/clos'), api.get('/concepts/graph')])
      .then(([c, l, graph]) => {
        setConcepts(c.data)
        setClos(l.data)
        setPrerequisites(Object.fromEntries(graph.data.nodes.map((node) => [node.concept_id, node.prerequisites.join(',')])) )
        setPrereqEdit({})
        setLinkEdit({})
      })
      .catch((e) => {
        setError(apiMessage(e))
        setConcepts([])
        setClos([])
      })
  }, [])

  useEffect(() => { load() }, [load])

  async function run(fn, okMsg) {
    if (busy) return false
    setBusy(true)
    setError('')
    setNotice('')
    try {
      await fn()
      if (okMsg) setNotice(okMsg)
      await load()
      return true
    } catch (e) {
      setError(apiMessage(e))
      return false
    } finally {
      setBusy(false)
    }
  }

  async function confirmDelete() {
    if (!deleteTarget || deleting) return
    setDeleting(true)
    const path = deleteTarget.kind === 'concept'
      ? `/admin/concepts/${deleteTarget.id}` : `/admin/clos/${deleteTarget.id}`
    const deleted = await run(() => api.delete(path), message(deleteTarget.kind === 'concept' ? 'admin.curriculum.deletedConcept' : 'admin.curriculum.deletedClo'))
    setDeleting(false)
    if (deleted) setDeleteTarget(null)
  }

  const parseIds = (s) => {
    if (!s.trim()) return []
    const ids = s.split(',').map((x) => Number(x.trim()))
    if (ids.some((n) => !Number.isInteger(n) || n <= 0) || new Set(ids).size !== ids.length)
      throw validationError('validation.conceptIds')
    return ids
  }
  const prerequisiteValue = (id) => prereqEdit[id] ?? prerequisites[id] ?? ''
  const mappingValue = (clo) => linkEdit[clo.clo_id] ?? clo.concepts.filter((l) => l.status === 'confirmed').map((l) => l.concept_id).join(',')
  const query = conceptQuery.trim().toLowerCase()
  const visibleConcepts = (concepts || []).filter((c) =>
    !query || c.concept_code.toLowerCase().includes(query) || c.concept_name.toLowerCase().includes(query))
  const displayedConcepts = query || showAll ? visibleConcepts : visibleConcepts.slice(0, 30)

  if (concepts === null && !error) return <Loading />

  return (
    <div className="space-y-4">
      <AdminPageHeader
        title={t('admin.curriculum.title')}
        subtitle={t('admin.curriculum.subtitle')}
      />
      {notice && <Notice>{notice}</Notice>}
      {busy && <p role="status" className="text-sm text-mute">{t('admin.curriculum.saving')}</p>}
      {error && <ErrorState message={resolveMessage(error)} />}

      <SegmentedFilter
        ariaLabel={t('admin.curriculum.title')}
        value={tab}
        onChange={setTab}
        options={[
          { value: 'concepts', label: t('admin.curriculum.tabConcepts'), count: concepts?.length },
          { value: 'clos', label: t('admin.curriculum.tabClos'), count: clos?.length },
          { value: 'prereqs', label: t('admin.curriculum.tabPrereqs') },
        ]}
      />

      <fieldset disabled={busy} className="grid min-w-0 gap-6">
        {/* ---------- concepts ---------- */}
        {tab === 'concepts' && <Card className="overflow-hidden">
          <CardTitle title={editingConcept ? t('admin.curriculum.editConcept') : t('admin.curriculum.model')} />
          <div className="p-4">
          <form
            className="grid gap-2"
            onSubmit={(e) => {
              e.preventDefault()
              run(
                () => editingConcept
                  ? api.patch(`/admin/concepts/${editingConcept}`, {
                    concept_name: conceptForm.concept_name, subject_area: conceptForm.subject_area,
                    description: conceptForm.description, difficulty_level: conceptForm.difficulty_level,
                    ...(Object.hasOwn(conceptForm, 'keywords') ? { keywords: conceptForm.keywords } : {}),
                    ...(Object.hasOwn(conceptForm, 'learning_objectives') ? { learning_objectives: conceptForm.learning_objectives } : {}),
                    ...(Object.hasOwn(conceptForm, 'sql_feature') ? { sql_feature: conceptForm.sql_feature } : {}),
                  }) : api.post('/admin/concepts', { ...conceptForm, concept_code: conceptForm.concept_code.trim() || null }),
                editingConcept ? message('admin.curriculum.updatedConcept') : message('admin.curriculum.createdConcept')
              ).then((ok) => ok &&
                (setEditingConcept(null), setConceptForm({
                  concept_code: '', concept_name: '', subject_area: '',
                  description: '', difficulty_level: 1,
                }))
              )
            }}
          >
            <div className="grid gap-2 sm:grid-cols-2">
              <input required maxLength={100} aria-label={t('admin.curriculum.conceptName')} placeholder={t('common.name')} value={conceptForm.concept_name}
                onChange={(e) => setConceptForm({ ...conceptForm, concept_name: e.target.value })}
                className={inputCls} />
            </div>
            <details className="rounded-lg border border-edge p-3 text-sm text-sub">
              <summary className="cursor-pointer">{t('supervisor.referenceCode')}</summary>
              <p className="my-2 text-xs">{t('supervisor.generatedCodeHelp')}</p>
              <input maxLength={30} disabled={!!editingConcept} aria-label={t('admin.curriculum.conceptCode')} value={conceptForm.concept_code}
                onChange={(e) => setConceptForm({ ...conceptForm, concept_code: e.target.value })} className={inputCls} />
            </details>
            <div className="grid gap-2 sm:grid-cols-2">
              <input required maxLength={100} aria-label={t('common.subjectArea')} placeholder={t('common.subjectArea')} value={conceptForm.subject_area}
                onChange={(e) => setConceptForm({ ...conceptForm, subject_area: e.target.value })}
                className={inputCls} />
              <label className="flex items-center gap-2 text-sm text-sub">{t('common.difficulty')}<input type="number" min="1" max="5" value={conceptForm.difficulty_level}
                  onChange={(e) => setConceptForm({ ...conceptForm, difficulty_level: Number(e.target.value) })}
                  className="w-16 rounded-md border border-edge2 px-2 py-1.5 text-sm focus:border-cyan-400/60 focus:outline-none" />
              </label>
            </div>
            <input aria-label={t('admin.curriculum.conceptDescription')} placeholder={t('common.description')} value={conceptForm.description}
              onChange={(e) => setConceptForm({ ...conceptForm, description: e.target.value })}
              className={inputCls} />
            <label className="text-xs text-sub">{t('admin.curriculum.techniqueHelp')}<select aria-label={t('admin.curriculum.technique')} value={conceptForm.sql_feature || ''} onChange={(e) => setConceptForm({ ...conceptForm, sql_feature: e.target.value || null })} className={inputCls}>
                <option value="">{t('admin.curriculum.noTechnique')}</option>
                {['select', 'where', 'join', 'group_by', 'having', 'subquery', 'aggregate', 'cte', 'window', 'set_operation', 'distinct', 'order_by', 'limit', 'case', 'null_handling'].map((feature) => <option key={feature} value={feature}>{t(`sql.technique.${feature}`)}</option>)}
              </select>
            </label>
            <label className="text-xs text-sub">{t('supervisor.keywords')}<input maxLength={3000} value={(conceptForm.keywords || []).join(',')} onChange={e => setConceptForm({ ...conceptForm, keywords: e.target.value.split(',') })} className={`${inputCls} mt-1 w-full`} /></label>
            <label className="text-xs text-sub">{t('supervisor.objectives')}<textarea maxLength={20000} value={(conceptForm.learning_objectives || []).join('\n')} onChange={e => setConceptForm({ ...conceptForm, learning_objectives: e.target.value.split('\n') })} className={`${inputCls} mt-1 w-full`} /></label>
            <button type="submit" disabled={busy} aria-busy={busy} className={`w-fit ${btnPrimary}`}>
              {busy ? t('common.saving') : editingConcept ? t('admin.curriculum.saveConcept') : t('admin.curriculum.addConcept')}
            </button>
            {editingConcept && <button type="button" onClick={() => { setEditingConcept(null); setConceptForm({ concept_code: '', concept_name: '', subject_area: '', description: '', difficulty_level: 1 }) }} className="w-fit text-sm text-sub">{t('admin.curriculum.cancelConcept')}</button>}
          </form>

          <input
            aria-label={t('admin.curriculum.searchConcepts')}
            placeholder={t('admin.curriculum.searchPlaceholder')}
            value={conceptQuery}
            onChange={(e) => setConceptQuery(e.target.value)}
            className={`${inputCls} mt-4`}
          />
          <ul className="mt-2 divide-y divide-edge text-sm">
            {displayedConcepts.map((c) => (
              <li key={c.concept_id} className="py-2.5">
                <div className="flex items-center justify-between">
                  <span>
                    <span className="font-medium">{c.concept_name}</span>
                    <Badge className="ml-2">{t('exam.difficulty', { value: number(c.difficulty_level) })}</Badge>
                  </span>
                  <div className="flex shrink-0 gap-3">
                  <button type="button" disabled={busy} onClick={() => { setEditingConcept(c.concept_id); setConceptForm({ ...c, description: c.description || '' }) }} className="text-xs font-medium text-cyan-300 hover:underline">{t('common.edit')}</button>
                  <button disabled={busy}
                    type="button"
                    onClick={(event) => { focusDialogTrigger(event); setDeleteTarget({ kind: 'concept', id: c.concept_id, label: c.concept_name }) }}
                    className="text-xs font-medium text-rose-300 hover:underline"
                  >{t('common.delete')}</button>
                  </div>
                </div>
              </li>
            ))}
            {concepts && visibleConcepts.length === 0 && (
              <li className="flex items-center gap-2 py-4 text-sm text-mute"><Icon name="inbox" className="h-4 w-4" />{t('admin.curriculum.emptyConcepts')}</li>
            )}
          </ul>
          {visibleConcepts.length > displayedConcepts.length && (
            <button type="button" onClick={() => setShowAll(true)}
              className="mt-2 text-xs font-medium text-cyan-300 hover:underline">
              {t('admin.curriculum.showAll', { count: visibleConcepts.length })}
            </button>
          )}
          </div>
        </Card>}

        {/* ---------- CLOs ---------- */}
        {tab === 'clos' && <Card className="overflow-hidden">
          <CardTitle title={editingClo ? t('admin.curriculum.editClo') : t('admin.curriculum.outcomes')} />
          <div className="p-4">
          <form
            className="grid gap-2"
            onSubmit={(e) => {
              e.preventDefault()
              run(() => editingClo ? api.patch(`/admin/clos/${editingClo}`, { title: cloForm.title, description: cloForm.description }) : api.post('/admin/clos', cloForm), editingClo ? message('admin.curriculum.updatedClo') : message('admin.curriculum.createdClo'))
                .then((ok) => ok && (setEditingClo(null), setCloForm({ clo_code: '', title: '', description: '' })))
            }}
          >
            <div className="grid gap-2 sm:grid-cols-3">
              <input required maxLength={20} disabled={!!editingClo} aria-label={t('admin.curriculum.cloCode')} placeholder={t('admin.curriculum.code')} value={cloForm.clo_code}
                onChange={(e) => setCloForm({ ...cloForm, clo_code: e.target.value })}
                className={inputCls} />
              <input required maxLength={200} aria-label={t('admin.curriculum.cloTitle')} placeholder={t('common.title')} value={cloForm.title}
                onChange={(e) => setCloForm({ ...cloForm, title: e.target.value })}
                className={`sm:col-span-2 ${inputCls}`} />
            </div>
            <input aria-label={t('admin.curriculum.cloDescription')} placeholder={t('common.description')} value={cloForm.description}
              onChange={(e) => setCloForm({ ...cloForm, description: e.target.value })}
              className={inputCls} />
            <button type="submit" disabled={busy} aria-busy={busy} className={`w-fit ${btnPrimary}`}>
              {busy ? t('common.saving') : editingClo ? t('admin.curriculum.saveClo') : t('admin.curriculum.addClo')}
            </button>
            {editingClo && <button type="button" onClick={() => { setEditingClo(null); setCloForm({ clo_code: '', title: '', description: '' }) }} className="w-fit text-sm text-sub">{t('admin.curriculum.cancelClo')}</button>}
          </form>

          <ul className="mt-4 divide-y divide-edge text-sm">
            {(clos || []).map((clo) => (
              <li key={clo.clo_id} className="py-3">
                <div className="flex items-center justify-between">
                  <span className="font-medium">{clo.clo_code} — {clo.title}</span>
                  <div className="flex gap-3 text-xs">
                    <button type="button" disabled={busy} onClick={() => { setEditingClo(clo.clo_id); setCloForm({ ...clo, description: clo.description || '' }) }} className="font-medium text-cyan-300 hover:underline">{t('common.edit')}</button>
                    <button
                      type="button"
                      onClick={() => run(
                        () => api.post(`/admin/clos/${clo.clo_id}/ai-suggest`),
                        message('admin.curriculum.pendingLinks')
                      )}
                      className="font-medium text-violet-300 hover:underline"
                    >{t('admin.curriculum.aiSuggest')}</button>
                    <button
                      type="button"
                      onClick={(event) => { focusDialogTrigger(event); setDeleteTarget({ kind: 'clo', id: clo.clo_id, label: clo.title }) }}
                      className="font-medium text-rose-300 hover:underline"
                    >{t('common.delete')}</button>
                  </div>
                </div>
                {clo.concepts.length > 0 && (
                  <ul className="mt-1.5 space-y-1">
                    {clo.concepts.map((l) => (
                      <li key={l.concept_id} className="flex items-center gap-2 text-xs">
                        <StatusBadge status={l.status} />
                        <Badge>{statusLabel(l.mapping_source)}</Badge>
                        <span>{l.concept_code} — {l.concept_name}</span>
                        {l.status === 'pending' && (
                          <span className="ml-auto flex gap-2">
                            <button
                              type="button"
                              onClick={() => run(
                                () => api.post(`/admin/clos/${clo.clo_id}/concepts/${l.concept_id}/confirm`),
                                message('admin.curriculum.confirmed')
                              )}
                              className="font-medium text-emerald-300 hover:underline"
                            >{t('common.confirm')}</button>
                            <button
                              type="button"
                              onClick={() => run(
                                () => api.delete(`/admin/clos/${clo.clo_id}/concepts/${l.concept_id}`),
                                message('admin.rejectedSuggestion')
                              )}
                              className="font-medium text-rose-300 hover:underline"
                            >{t('common.reject')}</button>
                          </span>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
                <div className="mt-1.5 flex flex-wrap items-start gap-2 text-xs text-mute">
                  <details className="min-w-0 flex-1">
                    <summary className="cursor-pointer text-cyan-300">{t('admin.curriculum.confirmedFor', { code: clo.clo_code })}</summary>
                    <ConceptPicker label={t('admin.curriculum.confirmedFor', { code: clo.clo_code })}
                      concepts={(concepts || []).filter(c => !clo.concepts.some(link => link.concept_id === c.concept_id && link.mapping_source === 'ai' && link.status !== 'confirmed'))}
                      value={parseIds(mappingValue(clo))}
                      onChange={ids => setLinkEdit(previous => ({ ...previous, [clo.clo_id]: ids.join(',') }))} />
                  </details>
                  <button
                    type="button"
                    onClick={() => run(
                      () => api.put(`/admin/clos/${clo.clo_id}/concepts`,
                        { concept_ids: parseIds(mappingValue(clo)) }),
                      message('admin.curriculum.savedSet')
                    )}
                    className="font-medium text-cyan-300 hover:underline"
                  >{t('admin.curriculum.saveSet')}</button>
                </div>
              </li>
            ))}
            {clos && clos.length === 0 && (
              <li className="flex items-center gap-2 py-4 text-sm text-mute"><Icon name="inbox" className="h-4 w-4" />{t('admin.curriculum.emptyClos')}</li>
            )}
          </ul>
          </div>
        </Card>}

        {/* ---------- prerequisites ---------- */}
        {tab === 'prereqs' && <Card className="overflow-hidden">
          <CardTitle title={t('admin.curriculum.tabPrereqs')} />
          <div className="p-4">
            <input
              aria-label={t('admin.curriculum.searchConcepts')}
              placeholder={t('admin.curriculum.searchPlaceholder')}
              value={conceptQuery}
              onChange={(e) => setConceptQuery(e.target.value)}
              className={inputCls}
            />
            <ul className="mt-2 divide-y divide-edge text-sm">
              {displayedConcepts.map((c) => (
                <li key={c.concept_id} className="flex flex-wrap items-center gap-2 py-2.5">
                  <span className="min-w-0">
                    <span className="font-mono text-xs text-faint">#{c.concept_id}</span>{' '}
                    <span className="font-medium">{c.concept_code}</span>{' '}
                    <span className="text-mute">— {c.concept_name}</span>
                  </span>
                  <div className="w-full space-y-2 text-xs text-mute">
                    <p>{parseIds(prerequisiteValue(c.concept_id)).map(id => concepts.find(item => item.concept_id === id)?.concept_name || id).join(', ') || '—'}</p>
                    <details className="min-w-0 flex-1">
                      <summary className="cursor-pointer text-cyan-300">{t('admin.curriculum.prerequisitesFor', { code: c.concept_code })}</summary>
                      <ConceptPicker label={t('admin.curriculum.prerequisitesFor', { code: c.concept_code })}
                        concepts={(concepts || []).filter(item => item.concept_id !== c.concept_id)}
                        value={parseIds(prerequisiteValue(c.concept_id))}
                        onChange={ids => setPrereqEdit(previous => ({ ...previous, [c.concept_id]: ids.join(',') }))} />
                    </details>
                    <button
                      type="button" disabled={busy}
                      onClick={() => run(
                        () => api.put(`/admin/concepts/${c.concept_id}/prerequisites`,
                          { prerequisite_concept_ids: parseIds(prerequisiteValue(c.concept_id)) }),
                        message('admin.curriculum.savedPrereqs')
                      )}
                      className="font-medium text-cyan-300 hover:underline"
                    >{t('common.save')}</button>
                  </div>
                </li>
              ))}
              {concepts && visibleConcepts.length === 0 && (
                <li className="flex items-center gap-2 py-4 text-sm text-mute"><Icon name="inbox" className="h-4 w-4" />{t('admin.curriculum.emptyConcepts')}</li>
              )}
            </ul>
            {visibleConcepts.length > displayedConcepts.length && (
              <button type="button" onClick={() => setShowAll(true)}
                className="mt-2 text-xs font-medium text-cyan-300 hover:underline">
                {t('admin.curriculum.showAll', { count: visibleConcepts.length })}
              </button>
            )}
          </div>
        </Card>}
      </fieldset>
      {concepts === null && <Loading />}
      {error && concepts === null && <ErrorState message={resolveMessage(error)} onRetry={load} />}
      <ConfirmDialog open={!!deleteTarget} title={t(deleteTarget?.kind === 'clo' ? 'admin.curriculum.deleteCloTitle' : 'admin.curriculum.deleteConceptTitle')} confirmLabel={deleting ? t('common.deleting') : t('common.delete')} cancelLabel={t('common.cancel')} busy={deleting} onConfirm={confirmDelete} onCancel={() => setDeleteTarget(null)}>
        {t('admin.curriculum.deleteBody', { name: deleteTarget?.label || '' })}
        {error && <p role="alert" className="mt-2 text-rose-300">{resolveMessage(error)}</p>}
      </ConfirmDialog>
    </div>
  )
}
