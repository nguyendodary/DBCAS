import { useCallback, useEffect, useState } from 'react'
import api, { apiMessage } from '../../api'
import AdminNav from '../../components/AdminNav'
import { EmptyState, ErrorState, Loading } from '../../components/States'

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
    } catch (e) {
      setError(apiMessage(e))
    }
  }

  const parseIds = (s) =>
    s.split(',').map((x) => Number(x.trim())).filter((n) => Number.isInteger(n) && n > 0)

  if (concepts === null && !error) return <div><AdminNav /><Loading /></div>

  return (
    <div>
      <AdminNav />
      <h1 className="text-xl font-semibold text-gray-900">Curriculum</h1>
      {notice && <p role="status" className="mt-3 rounded bg-green-50 p-2 text-sm text-green-700">{notice}</p>}
      {error && <div className="mt-3"><ErrorState message={error} /></div>}

      <div className="mt-4 grid gap-6 lg:grid-cols-2">
        {/* ---------- concepts ---------- */}
        <section className="rounded-md border bg-white p-4">
          <h2 className="font-medium text-gray-900">Concept model</h2>
          <form
            className="mt-3 grid gap-2"
            onSubmit={(e) => {
              e.preventDefault()
              run(
                () => api.post('/admin/concepts', conceptForm),
                'Concept created.'
              ).then(() =>
                setConceptForm({
                  concept_code: '', concept_name: '', subject_area: '',
                  description: '', difficulty_level: 1,
                })
              )
            }}
          >
            <div className="grid grid-cols-2 gap-2">
              <input required placeholder="Code (e.g. SQL-SELECT)" value={conceptForm.concept_code}
                onChange={(e) => setConceptForm({ ...conceptForm, concept_code: e.target.value })}
                className="rounded border border-gray-300 px-2 py-1 text-sm" />
              <input required placeholder="Name" value={conceptForm.concept_name}
                onChange={(e) => setConceptForm({ ...conceptForm, concept_name: e.target.value })}
                className="rounded border border-gray-300 px-2 py-1 text-sm" />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <input required placeholder="Subject area" value={conceptForm.subject_area}
                onChange={(e) => setConceptForm({ ...conceptForm, subject_area: e.target.value })}
                className="rounded border border-gray-300 px-2 py-1 text-sm" />
              <label className="flex items-center gap-2 text-sm text-gray-600">
                Difficulty
                <input type="number" min="1" max="5" value={conceptForm.difficulty_level}
                  onChange={(e) => setConceptForm({ ...conceptForm, difficulty_level: Number(e.target.value) })}
                  className="w-16 rounded border border-gray-300 px-2 py-1 text-sm" />
              </label>
            </div>
            <input placeholder="Description" value={conceptForm.description}
              onChange={(e) => setConceptForm({ ...conceptForm, description: e.target.value })}
              className="rounded border border-gray-300 px-2 py-1 text-sm" />
            <button type="submit" className="w-fit rounded bg-blue-600 px-3 py-1 text-sm font-medium text-white hover:bg-blue-700">
              Add concept
            </button>
          </form>

          <ul className="mt-4 divide-y text-sm">
            {(concepts || []).map((c) => (
              <li key={c.concept_id} className="py-2">
                <div className="flex items-center justify-between">
                  <span>
                    <span className="font-mono text-xs text-gray-500">#{c.concept_id}</span>{' '}
                    <span className="font-medium">{c.concept_code}</span> — {c.concept_name}
                    <span className="ml-2 text-xs text-gray-500">d{c.difficulty_level}</span>
                  </span>
                  <button
                    type="button"
                    onClick={() => run(() => api.delete(`/admin/concepts/${c.concept_id}`), 'Concept deleted.')}
                    className="text-xs text-red-600 hover:underline"
                  >
                    Delete
                  </button>
                </div>
                <div className="mt-1 flex items-center gap-2 text-xs text-gray-500">
                  <span>prerequisites (ids):</span>
                  <input
                    value={prereqEdit[c.concept_id] ?? ''}
                    onChange={(e) => setPrereqEdit({ ...prereqEdit, [c.concept_id]: e.target.value })}
                    placeholder="e.g. 1,2"
                    className="w-28 rounded border border-gray-300 px-1 py-0.5"
                  />
                  <button
                    type="button"
                    onClick={() => run(
                      () => api.put(`/admin/concepts/${c.concept_id}/prerequisites`,
                        { prerequisite_concept_ids: parseIds(prereqEdit[c.concept_id] || '') }),
                      'Prerequisites saved.'
                    )}
                    className="text-blue-600 hover:underline"
                  >
                    Save
                  </button>
                </div>
              </li>
            ))}
            {concepts && concepts.length === 0 && (
              <li className="py-3 text-sm text-gray-500">No concepts yet.</li>
            )}
          </ul>
        </section>

        {/* ---------- CLOs ---------- */}
        <section className="rounded-md border bg-white p-4">
          <h2 className="font-medium text-gray-900">Course learning outcomes</h2>
          <form
            className="mt-3 grid gap-2"
            onSubmit={(e) => {
              e.preventDefault()
              run(() => api.post('/admin/clos', cloForm), 'CLO created.')
                .then(() => setCloForm({ clo_code: '', title: '', description: '' }))
            }}
          >
            <div className="grid grid-cols-3 gap-2">
              <input required placeholder="Code" value={cloForm.clo_code}
                onChange={(e) => setCloForm({ ...cloForm, clo_code: e.target.value })}
                className="rounded border border-gray-300 px-2 py-1 text-sm" />
              <input required placeholder="Title" value={cloForm.title}
                onChange={(e) => setCloForm({ ...cloForm, title: e.target.value })}
                className="col-span-2 rounded border border-gray-300 px-2 py-1 text-sm" />
            </div>
            <input placeholder="Description" value={cloForm.description}
              onChange={(e) => setCloForm({ ...cloForm, description: e.target.value })}
              className="rounded border border-gray-300 px-2 py-1 text-sm" />
            <button type="submit" className="w-fit rounded bg-blue-600 px-3 py-1 text-sm font-medium text-white hover:bg-blue-700">
              Add CLO
            </button>
          </form>

          <ul className="mt-4 divide-y text-sm">
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
                      className="text-purple-600 hover:underline"
                    >
                      AI suggest
                    </button>
                    <button
                      type="button"
                      onClick={() => run(() => api.delete(`/admin/clos/${clo.clo_id}`), 'CLO deleted.')}
                      className="text-red-600 hover:underline"
                    >
                      Delete
                    </button>
                  </div>
                </div>
                {clo.concepts.length > 0 && (
                  <ul className="mt-1 space-y-0.5">
                    {clo.concepts.map((l) => (
                      <li key={l.concept_id} className="flex items-center gap-2 text-xs">
                        <span
                          className={`rounded px-1.5 py-0.5 font-medium ${
                            l.status === 'confirmed'
                              ? 'bg-green-50 text-green-700'
                              : 'bg-amber-50 text-amber-700'
                          }`}
                        >
                          {l.status}
                        </span>
                        <span className="rounded bg-gray-100 px-1.5 py-0.5">{l.mapping_source}</span>
                        <span>{l.concept_code} — {l.concept_name}</span>
                        {l.status === 'pending' && (
                          <span className="ml-auto flex gap-2">
                            <button
                              type="button"
                              onClick={() => run(
                                () => api.post(`/admin/clos/${clo.clo_id}/concepts/${l.concept_id}/confirm`),
                                'Mapping confirmed.'
                              )}
                              className="text-green-600 hover:underline"
                            >
                              Confirm
                            </button>
                            <button
                              type="button"
                              onClick={() => run(
                                () => api.delete(`/admin/clos/${clo.clo_id}/concepts/${l.concept_id}`),
                                'Suggestion rejected.'
                              )}
                              className="text-red-600 hover:underline"
                            >
                              Reject
                            </button>
                          </span>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
                <div className="mt-1 flex items-center gap-2 text-xs text-gray-500">
                  <span>confirmed set (concept ids):</span>
                  <input
                    value={linkEdit[clo.clo_id] ?? clo.concepts.filter((l) => l.status === 'confirmed').map((l) => l.concept_id).join(',')}
                    onChange={(e) => setLinkEdit({ ...linkEdit, [clo.clo_id]: e.target.value })}
                    className="w-36 rounded border border-gray-300 px-1 py-0.5"
                  />
                  <button
                    type="button"
                    onClick={() => run(
                      () => api.put(`/admin/clos/${clo.clo_id}/concepts`,
                        { concept_ids: parseIds(linkEdit[clo.clo_id] || '') }),
                      'Mapping set saved.'
                    )}
                    className="text-blue-600 hover:underline"
                  >
                    Save set
                  </button>
                </div>
              </li>
            ))}
            {clos && clos.length === 0 && (
              <li className="py-3 text-sm text-gray-500">No CLOs yet.</li>
            )}
          </ul>
        </section>
      </div>
      {concepts === null && <Loading />}
      {error && concepts === null && <ErrorState message={error} onRetry={load} />}
    </div>
  )
}
