import { message } from './i18n'
import { useCallback, useEffect, useRef, useState } from 'react'
import api, { apiMessage } from './api'

const valuesFor = (question) => ({
  option: question?.draft?.selected_option_id ?? null,
  sql: question?.draft?.sql_answer ?? '',
  essay: question?.draft?.essay_answer ?? '',
})

const answerFor = (question, values) =>
  question?.question_type === 'mcq'
    ? { selected_option_id: values.option }
    : question?.question_type === 'sql'
      ? { sql_answer: values.sql }
      : { essay_answer: values.essay }

// One record per seq keeps locally edited answers alive while jumping between
// questions. Saves are serialized through a single chain so a failed or slow
// request can never be overwritten by a later keystroke or navigation.
export function usePaperDraft(sessionId, onSaved) {
  const onSavedRef = useRef(onSaved)
  onSavedRef.current = onSaved
  const records = useRef(new Map())
  const chain = useRef(Promise.resolve())
  const current = useRef(null)
  const [draft, setDraftState] = useState(null)
  const [saveStatus, setSaveStatus] = useState('idle')
  const [saveError, setSaveError] = useState(null)
  const [saveConflict, setSaveConflict] = useState(false)

  const hydrate = useCallback((question) => {
    if (!question) {
      current.current = null
      setDraftState(null)
      setSaveStatus('idle')
      setSaveError(null)
      setSaveConflict(false)
      return
    }
    const seq = question.seq_no
    const previous = records.current.get(seq)
    const values = previous ? previous.values : valuesFor(question)
    const record = {
      seq,
      question,
      values,
      revision: previous ? previous.revision : (question.draft_revision ?? 0),
      saved: previous ? previous.saved : JSON.stringify(values),
      dirty: previous ? previous.dirty : false,
      persisted: previous ? previous.persisted : question.draft != null,
    }
    records.current.set(seq, record)
    current.current = record
    setDraftState({ ...values })
    setSaveStatus(record.dirty ? 'unsaved' : record.persisted ? 'saved' : 'idle')
    setSaveError(null)
    setSaveConflict(false)
  }, [])

  const setDraft = useCallback((update) => {
    const record = current.current
    if (!record) return
    record.values = typeof update === 'function' ? update(record.values) : update
    record.dirty = JSON.stringify(record.values) !== record.saved
    setDraftState({ ...record.values })
    setSaveStatus(record.dirty ? 'unsaved' : record.persisted ? 'saved' : 'idle')
    setSaveError(null)
    setSaveConflict(false)
  }, [])

  const flush = useCallback(
    (seq) => {
      const record = seq == null ? current.current : records.current.get(seq)
      if (!record || !record.dirty) return chain.current
      const captured = { ...record.values }
      const serialized = JSON.stringify(captured)
      chain.current = chain.current
        .catch(() => {})
        .then(async () => {
          if (serialized === record.saved) return
          if (current.current === record) setSaveStatus('saving')
          try {
            const result = await api.put(`/sessions/${sessionId}/paper/${record.seq}/draft`, {
              revision: record.revision + 1,
              ...answerFor(record.question, captured),
            })
            record.revision = result.data.revision
            record.saved = serialized
            record.dirty = JSON.stringify(record.values) !== serialized
            record.persisted = true
            onSavedRef.current?.({
              seq: record.seq,
              answered: result.data.answered,
              revision: result.data.revision,
            })
            if (current.current === record) {
              setSaveStatus(record.dirty ? 'unsaved' : 'saved')
              setSaveError(null)
              setSaveConflict(false)
            }
          } catch (error) {
            if (current.current === record) {
              setSaveStatus('error')
              setSaveError(apiMessage(error, message('paper.draftError')))
              setSaveConflict(error?.response?.data?.error?.code === 'draft_revision_conflict')
            }
            throw error
          }
        })
      return chain.current
    },
    [sessionId],
  )

  const flushAll = useCallback(async () => {
    for (const record of records.current.values()) {
      if (record.dirty) await flush(record.seq)
    }
  }, [flush])

  const reloadSavedDraft = useCallback(async () => {
    const record = current.current
    if (!record) return
    const { data } = await api.get(`/sessions/${sessionId}/paper/${record.seq}`)
    if (current.current !== record) return
    record.values = valuesFor(data)
    record.revision = data.draft_revision ?? 0
    record.saved = JSON.stringify(record.values)
    record.dirty = false
    record.persisted = true
    record.question = data
    setDraftState({ ...record.values })
    setSaveStatus('saved')
    setSaveError(null)
    setSaveConflict(false)
    return data
  }, [sessionId])

  // Debounced autosave; the timer is cleared whenever a newer value arrives.
  useEffect(() => {
    if (!current.current?.dirty || !['idle', 'unsaved', 'saved'].includes(saveStatus)) return
    const timer = setTimeout(() => flush().catch(() => {}), 450)
    return () => clearTimeout(timer)
  }, [draft, saveStatus, flush])

  // Best-effort persistence when the tab is hidden or closed. The server draft
  // remains authoritative if a debounce had not fired yet.
  useEffect(() => {
    const saveOnLeave = () => flush().catch(() => {})
    window.addEventListener('pagehide', saveOnLeave)
    return () => {
      window.removeEventListener('pagehide', saveOnLeave)
      flush().catch(() => {})
    }
  }, [flush])

  return {
    draft,
    setDraft,
    hydrate,
    flushDraft: flush,
    flushAll,
    saveStatus,
    saveError,
    saveConflict,
    reloadSavedDraft,
  }
}
