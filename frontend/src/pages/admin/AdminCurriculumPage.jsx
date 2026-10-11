import { useCallback, useEffect, useState } from 'react'
import api, { apiMessage } from '../../api'
import { EmptyState, ErrorState, Loading } from '../../components/States'
import { Badge, Card, CardTitle, ConfirmDialog, Icon, Notice, PageHeader, StatusBadge, btnPrimary, inputCls } from '../../components/ui'

// UC05/UC06 + skill graph — concept model, CLOs, mappings (incl. AI
// suggestions), and prerequisites.
export default function AdminCurriculumPage() {
  const [concepts, setConcepts] = useState(null)
  const [clos, setClos] = useState(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [conceptForm, setConceptForm] = useState({
    concept_code: '', concept_name: '', subject_area: '', description: '',
    difficulty_level: 1,
  })
  const [cloForm, setCloForm] = useState({ clo_code: '', title: '', description: '' })
  const [prereqEdit, setPrereqEdit] = useState({}) // concept_id -> "1,2"
  const [linkEdit, setLinkEdit] = useState({})   // clo_id -> "3,4"
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [deleting, setDeleting] = useState(false)

  const load = useCallback(() => {
    setError('')
    Promise.all([api.get('/admin/concepts'), api.get('/admin/clos')])
      .then(([c, l]) => {
        setConcepts(c.data)
        setClos(l.data)
      })
      .catch((e) => {
        setError(apiMessage(e))
        setConcepts([])
        setClos([])
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
      return true
    } catch (e) {
      setError(apiMessage(e))
      return false
    }
  }

  async function confirmDelete() {
    if (!deleteTarget || deleting) return
    setDeleting(true)
    const path = deleteTarget.kind === 'concept'
      ? `/admin/concepts/${deleteTarget.id}` : `/admin/clos/${deleteTarget.id}`
    const deleted = await run(() => api.delete(path), `${deleteTarget.kind === 'concept' ? 'Concept' : 'CLO'} deleted.`)
    setDeleting(false)
    if (deleted) setDeleteTarget(null)
  }

  const parseIds = (s) =>
    s.split(',').map((x) => Number(x.trim())).filter((n) => Number.isInteger(n) && n > 0)

  if (concepts === null && !error) return <Loading />

  return (
    <div className="space-y-4">
      <PageHeader
        title="Curriculum"
        subtitle="Concepts, course learning outcomes, and the prerequisite skill graph."
      />
      {notice && <Notice>{notice}</Notice>}
      {error && <ErrorState message={error} />}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* ---------- concepts ---------- */}
        <Card className="overflow-hidden">
          <CardTitle title="Concept model" />
          <div className="p-4">
          <form
            className="grid gap-2"
            onSubmit={(e) => {
              e.preventDefault()
              run(
                () => api.post('/admin/concepts', conceptForm),
                'Concept created.'
              ).then((ok) => ok &&
                setConceptForm({
                  concept_code: '', concept_name: '', subject_area: '',
                  description: '', difficulty_level: 1,
                })
              )
            }}
          >
            <div className="grid gap-2 sm:grid-cols-2">
              <input required aria-label="Concept code" placeholder="Code (e.g. SQL-SELECT)" value={conceptForm.concept_code}
                onChange={(e) => setConceptForm({ ...conceptForm, concept_code: e.target.value })}
                className={inputCls} />
              <input required aria-label="Concept name" placeholder="Name" value={conceptForm.concept_name}
                onChange={(e) => setConceptForm({ ...conceptForm, concept_name: e.target.value })}
                className={inputCls} />
            </div>
            <div className="grid gap-2 sm:grid-cols-2">
              <input required aria-label="Subject area" placeholder="Subject area" value={conceptForm.subject_area}
                onChange={(e) => setConceptForm({ ...conceptForm, subject_area: e.target.value })}
                className={inputCls} />
              <label className="flex items-center gap-2 text-sm text-sub">
                Difficulty
                <input type="number" min="1" max="5" value={conceptForm.difficulty_level}
                  onChange={(e) => setConceptForm({ ...conceptForm, difficulty_level: Number(e.target.value) })}
                  className="w-16 rounded-md border border-edge2 px-2 py-1.5 text-sm focus:border-cyan-400/60 focus:outline-none" />
              </label>
            </div>
            <input aria-label="Concept description" placeholder="Description" value={conceptForm.description}
              onChange={(e) => setConceptForm({ ...conceptForm, description: e.target.value })}
              className={inputCls} />
            <button type="submit" className={`w-fit ${btnPrimary}`}>
              Add concept
            </button>
          </form>

          <ul className="mt-4 divide-y divide-edge text-sm">
            {(concepts || []).map((c) => (
              <li key={c.concept_id} className="py-2.5">
                <div className="flex items-center justify-between">
                  <span>
                    <span className="font-mono text-xs text-faint">#{c.concept_id}</span>{' '}
                    <span className="font-medium">{c.concept_code}</span> — {c.concept_name}
                    <Badge className="ml-2">d{c.difficulty_level}</Badge>
                  </span>
                  <button
                    type="button"
                    onClick={() => setDeleteTarget({ kind: 'concept', id: c.concept_id, label: c.concept_name })}
                    className="text-xs font-medium text-rose-300 hover:underline"
                  >
                    Delete
                  </button>
                </div>
                <div className="mt-1.5 flex items-center gap-2 text-xs text-mute">
                  <span>prerequisites (ids):</span>
                  <input
                    value={prereqEdit[c.concept_id] ?? ''}
                    onChange={(e) => setPrereqEdit({ ...prereqEdit, [c.concept_id]: e.target.value })}
                    placeholder="e.g. 1,2"
                    aria-label={`Prerequisites for ${c.concept_code}`}
                    className="w-28 rounded-md border border-edge2 px-1.5 py-1 focus:border-cyan-400/60 focus:outline-none"
                  />
                  <button
                    type="button"
                    onClick={() => run(
                      () => api.put(`/admin/concepts/${c.concept_id}/prerequisites`,
                        { prerequisite_concept_ids: parseIds(prereqEdit[c.concept_id] || '') }),
                      'Prerequisites saved.'
                    )}
                    className="font-medium text-cyan-300 hover:underline"
                  >
                    Save
                  </button>
                </div>
              </li>
            ))}
            {concepts && concepts.length === 0 && (
              <li className="flex items-center gap-2 py-4 text-sm text-mute"><Icon name="inbox" className="h-4 w-4" />No concepts yet. Add one above to build the curriculum.</li>
            )}
          </ul>
          </div>
        </Card>

        {/* ---------- CLOs ---------- */}
        <Card className="overflow-hidden">
          <CardTitle title="Course learning outcomes" />
          <div className="p-4">
          <form
            className="grid gap-2"
            onSubmit={(e) => {
              e.preventDefault()
              run(() => api.post('/admin/clos', cloForm), 'CLO created.')
                .then((ok) => ok && setCloForm({ clo_code: '', title: '', description: '' }))
            }}
          >
            <div className="grid gap-2 sm:grid-cols-3">
              <input required aria-label="CLO code" placeholder="Code" value={cloForm.clo_code}
                onChange={(e) => setCloForm({ ...cloForm, clo_code: e.target.value })}
                className={inputCls} />
              <input required aria-label="CLO title" placeholder="Title" value={cloForm.title}
                onChange={(e) => setCloForm({ ...cloForm, title: e.target.value })}
                className={`sm:col-span-2 ${inputCls}`} />
            </div>
            <input aria-label="CLO description" placeholder="Description" value={cloForm.description}
              onChange={(e) => setCloForm({ ...cloForm, description: e.target.value })}
              className={inputCls} />
            <button type="submit" className={`w-fit ${btnPrimary}`}>
              Add CLO
            </button>
          </form>

          <ul className="mt-4 divide-y divide-edge text-sm">
            {(clos || []).map((clo) => (
              <li key={clo.clo_id} className="py-3">
                <div className="flex items-center justify-between">
                  <span className="font-medium">{clo.clo_code} — {clo.title}</span>
                  <div className="flex gap-3 text-xs">
                    <button
                      type="button"
                      onClick={() => run(
                        () => api.post(`/admin/clos/${clo.clo_id}/ai-suggest`),
                        'AI suggestions added as pending links.'
                      )}
                      className="font-medium text-violet-300 hover:underline"
                    >
                      AI suggest
                    </button>
                    <button
                      type="button"
                      onClick={() => setDeleteTarget({ kind: 'clo', id: clo.clo_id, label: clo.title })}
                      className="font-medium text-rose-300 hover:underline"
                    >
                      Delete
                    </button>
                  </div>
                </div>
                {clo.concepts.length > 0 && (
                  <ul className="mt-1.5 space-y-1">
                    {clo.concepts.map((l) => (
                      <li key={l.concept_id} className="flex items-center gap-2 text-xs">
                        <StatusBadge status={l.status} />
                        <Badge>{l.mapping_source}</Badge>
                        <span>{l.concept_code} — {l.concept_name}</span>
                        {l.status === 'pending' && (
                          <span className="ml-auto flex gap-2">
                            <button
                              type="button"
                              onClick={() => run(
                                () => api.post(`/admin/clos/${clo.clo_id}/concepts/${l.concept_id}/confirm`),
                                'Mapping confirmed.'
                              )}
                              className="font-medium text-emerald-300 hover:underline"
                            >
                              Confirm
                            </button>
                            <button
                              type="button"
                              onClick={() => run(
                                () => api.delete(`/admin/clos/${clo.clo_id}/concepts/${l.concept_id}`),
                                'Suggestion rejected.'
                              )}
                              className="font-medium text-rose-300 hover:underline"
                            >
                              Reject
                            </button>
                          </span>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
                <div className="mt-1.5 flex items-center gap-2 text-xs text-mute">
                  <span>confirmed set (concept ids):</span>
                  <input
                    value={linkEdit[clo.clo_id] ?? clo.concepts.filter((l) => l.status === 'confirmed').map((l) => l.concept_id).join(',')}
                    onChange={(e) => setLinkEdit({ ...linkEdit, [clo.clo_id]: e.target.value })}
                    aria-label={`Confirmed concepts for ${clo.clo_code}`}
                    className="w-36 rounded-md border border-edge2 px-1.5 py-1 focus:border-cyan-400/60 focus:outline-none"
                  />
                  <button
                    type="button"
                    onClick={() => run(
                      () => api.put(`/admin/clos/${clo.clo_id}/concepts`,
                        { concept_ids: parseIds(linkEdit[clo.clo_id] || '') }),
                      'Mapping set saved.'
                    )}
                    className="font-medium text-cyan-300 hover:underline"
                  >
                    Save set
                  </button>
                </div>
              </li>
            ))}
            {clos && clos.length === 0 && (
              <li className="flex items-center gap-2 py-4 text-sm text-mute"><Icon name="inbox" className="h-4 w-4" />No CLOs yet. Add one above to link learning outcomes.</li>
            )}
          </ul>
          </div>
        </Card>
      </div>
      {concepts === null && <Loading />}
      {error && concepts === null && <ErrorState message={error} onRetry={load} />}
      <ConfirmDialog open={!!deleteTarget} title={`Delete this ${deleteTarget?.kind === 'clo' ? 'learning outcome' : 'concept'}?`} confirmLabel={deleting ? 'Deleting…' : 'Delete'} cancelLabel="Cancel" busy={deleting} onConfirm={confirmDelete} onCancel={() => setDeleteTarget(null)}>
        {deleteTarget?.label} will be removed from the curriculum. This action cannot be undone.
        {error && <p role="alert" className="mt-2 text-rose-300">{error}</p>}
      </ConfirmDialog>
    </div>
  )
}
