import { message } from './i18n'
import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react'
import api, { apiMessage } from './api'

const valuesFor = (q) => ({ option: q?.draft?.selected_option_id ?? null, ...(q?.multiple_answers || q?.draft?.selected_option_ids != null ? { options: q?.draft?.selected_option_ids ?? (q?.draft?.selected_option_id != null ? [q.draft.selected_option_id] : []) } : {}), sql: q?.draft?.sql_answer ?? '', essay: q?.draft?.essay_answer ?? '' })
const answerFor = (q, values) => q.question_type === 'mcq' ? (q.multiple_answers ? { selected_option_ids: values.options || [] } : { selected_option_id: values.option }) : q.question_type === 'sql' ? { sql_answer: values.sql } : { essay_answer: values.essay }

// Draft revisions and a serialized save chain prevent typing/retry races.
// Domain grading stays entirely on the server.
export function useAnswerDraft(sessionId, question) {
  const [local, setLocal] = useState(null)
  const [saveStatus, setSaveStatus] = useState('idle')
  const [saveError, setSaveError] = useState(null)
  const [saveConflict, setSaveConflict] = useState(false)
  const record = useRef(null)
  const chain = useRef(Promise.resolve())
  const questionRef = useRef(question)
  questionRef.current = question
  const key = `${sessionId}:${question?.question_id ?? ''}`

  // Initialize before paint: the visible input must never target the previous
  // question's record or have its first change discarded by later hydration.
  useLayoutEffect(() => {
    const values = valuesFor(questionRef.current)
    record.current = { key, q: questionRef.current, values, revision: questionRef.current?.draft_revision ?? 0, saved: JSON.stringify(values), dirty: false, persisted: questionRef.current?.draft != null }
    setLocal({ key, values })
    setSaveStatus(questionRef.current?.draft != null ? 'saved' : 'idle')
    setSaveError(null)
    setSaveConflict(false)
  }, [key])

  const draft = local?.key === key ? local.values : valuesFor(question)
  const setDraft = useCallback((update) => {
    const current = record.current
    if (!current?.q) return
    current.values = typeof update === 'function' ? update(current.values) : update
    current.dirty = JSON.stringify(current.values) !== current.saved
    setLocal({ key: current.key, values: current.values })
    setSaveStatus(current.dirty ? 'unsaved' : current.persisted ? 'saved' : 'idle')
    setSaveError(null)
  }, [])

  const flush = useCallback(() => {
    const current = record.current
    if (!current?.q || !current.dirty) return chain.current
    const captured = { ...current.values }
    const serialized = JSON.stringify(captured)
    chain.current = chain.current.catch(() => {}).then(async () => {
      if (serialized === current.saved) return
      if (record.current === current) setSaveStatus('saving')
      try {
        const result = await api.put(`/sessions/${sessionId}/draft`, { question_id: current.q.question_id, revision: current.revision + 1, ...answerFor(current.q, captured) })
        current.revision = result.data.revision
        current.saved = serialized
        current.dirty = JSON.stringify(current.values) !== serialized
        current.persisted = true
        if (record.current === current) {
          setSaveStatus(current.dirty ? 'unsaved' : 'saved')
          setSaveError(null)
          setSaveConflict(false)
        }
      } catch (error) {
        if (record.current === current) {
          setSaveStatus('error')
          setSaveError(apiMessage(error, message('exam.draftError')))
          setSaveConflict(error?.response?.data?.error?.code === 'draft_revision_conflict')
        }
        throw error
      }
    })
    return chain.current
  }, [sessionId])

  const reloadSavedDraft = useCallback(async () => {
    const current = record.current
    if (!current?.q) return
    const response = await api.get(`/sessions/${sessionId}/draft`, { params: { question_id: current.q.question_id } })
    if (record.current !== current) return
    current.values = valuesFor({ ...current.q, draft: response.data.answer })
    current.revision = response.data.revision
    current.saved = JSON.stringify(current.values)
    current.dirty = false
    current.persisted = true
    setLocal({ key: current.key, values: current.values })
    setSaveStatus('saved')
    setSaveError(null)
    setSaveConflict(false)
  }, [sessionId])

  useEffect(() => {
    if (local?.key !== key || !record.current?.dirty) return
    const timer = setTimeout(() => flush().catch(() => {}), 450)
    return () => clearTimeout(timer)
  }, [local, key, flush])

  useEffect(() => {
    const saveOnLeave = () => { flush().catch(() => {}) }
    const warnOnClose = (event) => {
      if (record.current?.dirty) { event.preventDefault(); event.returnValue = '' }
    }
    window.addEventListener('pagehide', saveOnLeave)
    window.addEventListener('beforeunload', warnOnClose)
    return () => {
      window.removeEventListener('pagehide', saveOnLeave)
      window.removeEventListener('beforeunload', warnOnClose)
      flush().catch(() => {})
    }
  }, [flush])

  return { draft, setDraft, flushDraft: flush, saveStatus, saveError, saveConflict, reloadSavedDraft }
}
