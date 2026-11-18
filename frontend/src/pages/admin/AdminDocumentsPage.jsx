import { t, useLocale, message, dateTime, typeLabel, statusLabel } from '../../i18n'
import { useCallback, useEffect, useState } from 'react'
import api, { apiMessage } from '../../api'
import { ActionSpinner, EmptyState, ErrorState, Loading } from '../../components/States'
import { AdminPageHeader } from '../../components/admin'
import {
  Badge,
  Card,
  CardTitle,
  Notice,
  StatusBadge,
  btnGhost,
  btnPrimary,
  inputCls,
  selectCls,
} from '../../components/ui'
import {
  CandidateReviewCard,
  DocumentApprovalForm,
  DocumentMeta,
  GenerationErrorPanel,
} from '../../components/adminDocuments'

const KINDS = ['mcq', 'sql', 'essay']
const DIFFICULTIES = ['EASY', 'MEDIUM', 'HARD']

function readBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result).split(',')[1] || '')
    reader.onerror = () => reject(reader.error)
    reader.readAsDataURL(file)
  })
}

export default function AdminDocumentsPage() {
  const { locale } = useLocale()
  const [documents, setDocuments] = useState(null)
  const [clos, setClos] = useState([])
  const [concepts, setConcepts] = useState([])
  const [candidates, setCandidates] = useState(null)
  const [detail, setDetail] = useState(null)
  const [reviewStatus, setReviewStatus] = useState('')
  const [selection, setSelection] = useState([])
  const [cloDrafts, setCloDrafts] = useState({})
  const [upload, setUpload] = useState({ title: '', file: null })
  const [gen, setGen] = useState({
    clo_id: '',
    concept_id: '',
    question_type: 'mcq',
    count: 1,
    difficulty: 'EASY',
    locale,
  })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [genError, setGenError] = useState(null)

  const load = useCallback(() => {
    setError('')
    return Promise.all([
      api.get('/admin/documents'),
      api.get('/admin/clos'),
      api.get('/admin/concepts'),
      api.get('/admin/question-candidates', {
        params: reviewStatus ? { status: reviewStatus } : {},
      }),
    ])
      .then(([docs, c, k, cands]) => {
        setDocuments(docs.data)
        setClos(c.data.filter((item) => item.status === 'active'))
        setConcepts(k.data)
        setCandidates(cands.data)
        setSelection((ids) =>
          ids.filter((id) =>
            docs.data.some((doc) => doc.document_id === id && doc.status === 'approved'),
          ),
        )
      })
      .catch((e) => {
        setError(apiMessage(e))
        setDocuments([])
        setCandidates([])
      })
  }, [reviewStatus])

  useEffect(() => {
    load()
  }, [load])

  async function run(fn, okMsg) {
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
      setBusy(false)
    }
  }

  function toggleSelection(id) {
    setSelection((ids) => (ids.includes(id) ? ids.filter((value) => value !== id) : [...ids, id]))
  }

  async function uploadDocument(event) {
    event.preventDefault()
    if (!upload.file || !upload.title.trim() || busy) return
    const content_base64 = await readBase64(upload.file)
    const response = await run(
      () =>
        api.post('/admin/documents', {
          title: upload.title.trim(),
          filename: upload.file.name,
          content_base64,
          clo_ids: [],
        }),
      message('admin.documents.uploaded'),
    )
    if (response) setUpload({ title: '', file: null })
  }

  async function generate(event) {
    event.preventDefault()
    if (busy) return
    if (selection.length === 0) {
      setGenError({ uiMessage: message('admin.documents.noDocumentsSelected') })
      return
    }
    setBusy(true)
    setGenError(null)
    setNotice('')
    try {
      const response = await api.post('/admin/document-candidates/generate', {
        clo_id: Number(gen.clo_id),
        concept_id: Number(gen.concept_id),
        document_ids: selection.map(Number),
        question_type: gen.question_type,
        count: Number(gen.count),
        difficulty: gen.difficulty,
        locale: gen.locale,
        request_id: crypto.randomUUID(),
      })
      setNotice(message('admin.documents.generated', { count: response.data.length }))
      setDetail(response.data[0] || null)
      await load()
    } catch (e) {
      setGenError(e)
    } finally {
      setBusy(false)
    }
  }

  async function open(id) {
    const response = await api.get(`/admin/question-candidates/${id}`).catch((e) => {
      setError(apiMessage(e, message('admin.candidates.openError')))
      return null
    })
    if (response) setDetail(response.data)
  }

  async function approveCandidate(candidate) {
    const response = await run(
      () =>
        api.post(`/admin/question-candidates/${candidate.candidate_id}/approve`, {
          content_hash: candidate.validation_detail.content_hash,
          reviewed: true,
        }),
      message('admin.documents.approved'),
    )
    if (response) setDetail(response.data)
  }

  async function rejectCandidate(candidate) {
    const response = await run(
      () => api.post(`/admin/question-candidates/${candidate.candidate_id}/reject`),
      message('admin.documents.rejected'),
    )
    if (response) setDetail(response.data)
  }

  return (
    <div className="space-y-5">
      <AdminPageHeader title={t('admin.documents.title')} subtitle={t('admin.documents.subtitle')}>
        <button type="button" onClick={load} disabled={busy} className={btnGhost}>
          {t('admin.documents.refresh')}
        </button>
      </AdminPageHeader>

      {notice && <Notice>{notice}</Notice>}
      {error && <ErrorState message={error} onRetry={load} />}

      <Card className="p-4 sm:p-5">
        <CardTitle title={t('admin.documents.uploadTitle')} />
        <form
          onSubmit={uploadDocument}
          className="grid gap-3 text-sm sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto] sm:items-end"
        >
          <label className="grid gap-1.5 text-xs font-medium text-sub">
            {t('admin.documents.fieldTitle')}
            <input
              required
              value={upload.title}
              onChange={(event) => setUpload({ ...upload, title: event.target.value })}
              className={inputCls}
            />
          </label>
          <label className="grid gap-1.5 text-xs font-medium text-sub">
            {t('admin.documents.fieldFile')}
            <input
              required
              type="file"
              accept=".txt,.md,.pdf,text/plain,text/markdown,application/pdf"
              onChange={(event) => setUpload({ ...upload, file: event.target.files?.[0] || null })}
              className={inputCls}
            />
          </label>
          <button type="submit" disabled={busy || !upload.file} className={btnPrimary}>
            {busy && <ActionSpinner />}
            {t('admin.documents.upload')}
          </button>
        </form>
      </Card>

      <Card className="overflow-hidden">
        <CardTitle title={t('admin.documents.sections.documents')} />
        {documents === null ? (
          <Loading />
        ) : documents.length === 0 ? (
          <div className="p-4">
            <EmptyState title={t('admin.documents.emptyDocuments')}>
              {t('admin.documents.emptyDocumentsBody')}
            </EmptyState>
          </div>
        ) : (
          <ul className="divide-y divide-edge">
            {documents.map((doc) => {
              const approved = doc.status === 'approved'
              const linked =
                cloDrafts[doc.document_id] ?? (doc.clos || []).map((item) => item.clo_id)
              return (
                <li key={doc.document_id} className="p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="break-words text-sm font-medium text-ink">{doc.title}</p>
                      <p className="mt-0.5 text-xs text-mute">
                        {doc.original_filename || doc.mime_type} ·{' '}
                        {t('admin.documents.uploadedAt', { value: dateTime(doc.uploaded_at) })}
                      </p>
                      <div className="mt-2">
                        <DocumentMeta document={doc} />
                      </div>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <label className="flex items-center gap-1.5 text-xs font-medium text-sub">
                        <input
                          type="checkbox"
                          disabled={!approved}
                          checked={selection.includes(doc.document_id)}
                          onChange={() => toggleSelection(doc.document_id)}
                        />
                        {t('admin.documents.selectForGeneration')}
                      </label>
                      {doc.status !== 'archived' && (
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() =>
                            run(
                              () => api.post(`/admin/documents/${doc.document_id}/archive`),
                              message('admin.documents.archived'),
                            )
                          }
                          className={btnGhost}
                        >
                          {t('admin.documents.archive')}
                        </button>
                      )}
                    </div>
                  </div>

                  <details className="mt-3">
                    <summary className="cursor-pointer text-xs font-medium text-sub">
                      {t('admin.documents.attachClos')}
                    </summary>
                    <div className="mt-2 flex flex-wrap items-center gap-3">
                      {clos.length === 0 ? (
                        <span className="text-xs text-mute">{t('admin.documents.noClos')}</span>
                      ) : (
                        clos.map((item) => (
                          <label
                            key={item.clo_id}
                            className="flex items-center gap-1 text-xs text-sub"
                          >
                            <input
                              type="checkbox"
                              checked={linked.includes(item.clo_id)}
                              onChange={(event) =>
                                setCloDrafts((drafts) => ({
                                  ...drafts,
                                  [doc.document_id]: event.target.checked
                                    ? [...linked, item.clo_id]
                                    : linked.filter((value) => value !== item.clo_id),
                                }))
                              }
                            />
                            {item.clo_code}
                          </label>
                        ))
                      )}
                      <button
                        type="button"
                        disabled={busy || doc.status === 'archived'}
                        onClick={() =>
                          run(
                            () =>
                              api.put(`/admin/documents/${doc.document_id}/clos`, {
                                clo_ids: linked.map(Number),
                              }),
                            message('admin.documents.closSaved'),
                          )
                        }
                        className={btnGhost}
                      >
                        {t('admin.documents.saveClos')}
                      </button>
                    </div>
                  </details>

                  {doc.status === 'draft' && (
                    <DocumentApprovalForm
                      document={doc}
                      busy={busy}
                      onApprove={(id) =>
                        run(
                          () =>
                            api.post(`/admin/documents/${id}/approve`, {
                              confirm_no_personal_data: true,
                            }),
                          message('admin.documents.documentApproved'),
                        )
                      }
                    />
                  )}
                </li>
              )
            })}
          </ul>
        )}
      </Card>

      <Card className="p-4 sm:p-5">
        <CardTitle title={t('admin.documents.generationTitle')} />
        <p className="mb-3 text-xs text-sub">{t('admin.documents.generationHelp')}</p>
        <form
          onSubmit={generate}
          className="grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_7rem_7rem_auto]"
        >
          <label className="grid gap-1.5 text-xs font-medium text-sub">
            {t('admin.documents.fieldClo')}
            <select
              required
              aria-label={t('admin.documents.fieldClo')}
              value={gen.clo_id}
              onChange={(event) => setGen({ ...gen, clo_id: event.target.value })}
              className={selectCls}
            >
              <option value="">{t('admin.documents.selectClo')}</option>
              {clos.map((item) => (
                <option key={item.clo_id} value={item.clo_id}>
                  {item.clo_code} — {item.title}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1.5 text-xs font-medium text-sub">
            {t('admin.documents.fieldConcept')}
            <select
              required
              aria-label={t('admin.documents.fieldConcept')}
              value={gen.concept_id}
              onChange={(event) => setGen({ ...gen, concept_id: event.target.value })}
              className={selectCls}
            >
              <option value="">{t('admin.documents.selectConcept')}</option>
              {concepts.map((item) => (
                <option key={item.concept_id} value={item.concept_id}>
                  {item.concept_code} — {item.concept_name}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1.5 text-xs font-medium text-sub">
            {t('admin.documents.fieldQuestionType')}
            <select
              value={gen.question_type}
              onChange={(event) => setGen({ ...gen, question_type: event.target.value })}
              className={selectCls}
            >
              {KINDS.map((kind) => (
                <option key={kind} value={kind}>
                  {typeLabel(kind)}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1.5 text-xs font-medium text-sub">
            {t('admin.documents.fieldCount')}
            <input
              type="number"
              min="1"
              max="3"
              value={gen.count}
              onChange={(event) => setGen({ ...gen, count: event.target.value })}
              className={inputCls}
            />
          </label>
          <button type="submit" disabled={busy} className={btnPrimary}>
            {busy && <ActionSpinner />}
            {busy ? t('admin.documents.generating') : t('admin.documents.generate')}
          </button>
        </form>
        <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-mute">
          <span>{t('admin.documents.selectedCount', { count: selection.length })}</span>
          <label className="flex items-center gap-1.5">
            {t('admin.documents.fieldLocale')}
            <select
              value={gen.locale}
              onChange={(event) => setGen({ ...gen, locale: event.target.value })}
              className={selectCls}
            >
              <option value="en">English</option>
              <option value="vi">Tiếng Việt</option>
            </select>
          </label>
          <label className="flex items-center gap-1.5">
            {t('admin.documents.fieldDifficulty')}
            <select
              value={gen.difficulty}
              onChange={(event) => setGen({ ...gen, difficulty: event.target.value })}
              className={selectCls}
            >
              {DIFFICULTIES.map((level) => (
                <option key={level} value={level}>
                  {t(`supervisor.${level}`)}
                </option>
              ))}
            </select>
          </label>
        </div>
        <GenerationErrorPanel error={genError} onRetry={generate} />
      </Card>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]">
        <Card className="overflow-hidden">
          <CardTitle title={t('admin.documents.queue')} />
          <div className="border-b border-edge px-4 pb-3">
            <select
              value={reviewStatus}
              aria-label={t('admin.documents.filter')}
              onChange={(event) => setReviewStatus(event.target.value)}
              className={selectCls}
            >
              <option value="">{t('admin.candidates.activeQueue')}</option>
              {['pending', 'validated', 'approved', 'rejected'].map((value) => (
                <option key={value} value={value}>
                  {statusLabel(value)}
                </option>
              ))}
            </select>
          </div>
          {candidates === null ? (
            <Loading />
          ) : candidates.length === 0 ? (
            <div className="p-4">
              <EmptyState title={t('admin.documents.emptyQueue')}>
                {t('admin.documents.emptyQueueBody')}
              </EmptyState>
            </div>
          ) : (
            <ul className="divide-y divide-edge text-sm">
              {candidates.map((item) => (
                <li
                  key={item.candidate_id}
                  className="flex items-center justify-between gap-2 px-4 py-3 hover:bg-surface-hover"
                >
                  <span className="flex min-w-0 flex-wrap items-center gap-1.5">
                    <Badge>#{item.candidate_id}</Badge>
                    <StatusBadge status={item.validation_status} />
                    {item.concept_code && <Badge tone="blue">{item.concept_code}</Badge>}
                  </span>
                  <button
                    type="button"
                    onClick={() => open(item.candidate_id)}
                    className="shrink-0 text-xs font-medium text-cyan-300 hover:underline"
                  >
                    {t('admin.candidates.review')}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Card>

        {detail && (
          <div className="space-y-3">
            <CardTitle
              title={t('admin.documents.detail', { id: detail.candidate_id })}
              className="px-1"
            >
              <button
                type="button"
                onClick={() => setDetail(null)}
                className="text-xs font-medium text-mute hover:underline"
              >
                {t('common.close')}
              </button>
            </CardTitle>
            <CandidateReviewCard
              candidate={detail}
              busy={busy}
              onApprove={approveCandidate}
              onReject={rejectCandidate}
            />
          </div>
        )}
      </div>
    </div>
  )
}
