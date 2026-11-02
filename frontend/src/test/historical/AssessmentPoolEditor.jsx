import { useCallback, useEffect, useRef, useState } from 'react'
import api, { apiMessage } from '../../api'
import { t, useLocale, typeLabel } from '../../i18n'
import { Card, btnGhost, btnPrimary, inputCls } from '../../components/ui'
import { Loading, EmptyState, ErrorState } from '../../components/States'

export default function AssessmentPoolEditor({ assessment, onClose, onSaved }) {
  const { locale } = useLocale()
  const [questions, setQuestions] = useState(null)
  const [selected, setSelected] = useState([])
  const [all, setAll] = useState(true)
  const [query, setQuery] = useState('')
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)
  const [retry, setRetry] = useState(0)
  const heading = useRef(null)
  const guard = useRef(false)
  useEffect(() => {
    const previous = document.activeElement
    heading.current?.focus()
    return () => { if (previous?.isConnected) previous.focus() }
  }, [])
  const load = useCallback(() => {
    let cancelled = false
    const controller = new AbortController()
    setError(null)
    setQuestions(null)
    Promise.all([
      api.get(`/admin/assessments/${assessment.assessment_id}`, { signal: controller.signal }),
      api.get(`/admin/assessments/${assessment.assessment_id}/questions`, { signal: controller.signal }),
      api.get('/admin/questions', { params: { status: 'validated' }, signal: controller.signal }),
    ]).then(([detail, pool, bank]) => {
      if (cancelled) return
      const targets = new Map(detail.data.concepts.map(target => [target.concept_id, target]))
      setQuestions(bank.data.filter(question => question.status === 'validated' && question.concepts.some(tag => {
        const target = targets.get(tag.concept_id)
        return tag.confirmed && target && target.min_difficulty <= question.difficulty_level && question.difficulty_level <= target.max_difficulty
      })))
      setSelected(pool.data.question_ids)
      setAll(pool.data.question_ids.length === 0)
    }).catch(err => { if (!cancelled) setError(apiMessage(err)) })
    return () => { cancelled = true; controller.abort() }
  }, [assessment.assessment_id])
  useEffect(load, [load, retry])
  const visible = (questions || []).filter(question => `${question.prompt} ${question.localized_prompts?.[locale] || ''}`.toLowerCase().includes(query.trim().toLowerCase()))
  const chosen = (questions || []).filter(question => selected.includes(question.question_id))
  const counts = Object.fromEntries(['mcq', 'sql', 'essay'].map(type => [type, chosen.filter(question => question.question_type === type).length]))
  const stale = chosen.length !== selected.length
  const complete = counts.mcq >= 10 && counts.sql >= 2 && counts.essay >= 1
    && chosen.filter(question => question.question_type === 'mcq' && question.difficulty_level <= 2).length >= 3
  async function save(event) {
    event.preventDefault()
    if (guard.current || !questions || (!all && (stale || !complete))) return
    guard.current = true
    setSaving(true)
    setError(null)
    try {
      await api.put(`/admin/assessments/${assessment.assessment_id}/questions`, { question_ids: all ? [] : selected })
      onSaved()
    } catch (err) { setError(apiMessage(err)) }
    finally { guard.current = false; setSaving(false) }
  }
  return <Card className="p-5">
    <h2 ref={heading} tabIndex={-1} className="font-bold text-ink">{t('local.poolTitle')} · {assessment.title}</h2>
    <p className="mt-2 text-sm text-sub">{t('local.poolHelp')}</p>
    {error && <div className="mt-3"><ErrorState message={error} onRetry={() => setRetry(value => value + 1)} /></div>}
    <form onSubmit={save} className="mt-4 space-y-4">
      {!questions ? !error && <Loading /> : <fieldset disabled={saving} className="space-y-3">
        <label className="flex items-start gap-2 text-sm text-sub"><input type="checkbox" checked={all} onChange={event => setAll(event.target.checked)} />{t('local.poolAll')}</label>
        {!all && <>
          <input aria-label={t('local.poolSearch')} type="search" className={`${inputCls} w-full`} value={query} onChange={event => setQuery(event.target.value)} />
          <button type="button" className={btnGhost} onClick={() => setSelected(value => [...new Set([...value, ...visible.map(question => question.question_id)])])}>{t('local.poolSelectAll')}</button>
          <p role="status" className="text-sm text-sub">{t('local.poolMix', counts)}</p>
          {stale && <p className="text-sm text-amber-300">{t('local.poolStale')}</p>}
          <div className="max-h-72 space-y-2 overflow-y-auto">{visible.map(question => <label key={question.question_id} className="flex gap-3 rounded-lg border border-edge p-3 text-sm text-sub">
            <input type="checkbox" checked={selected.includes(question.question_id)} onChange={event => setSelected(value => event.target.checked ? [...value, question.question_id] : value.filter(id => id !== question.question_id))} />
            <span><strong className="text-ink">{typeLabel(question.question_type)}</strong> · {question.localized_prompts?.[locale] || question.prompt}</span>
          </label>)}</div>
          {!visible.length && <EmptyState title={t('analytics.noEvidence')} />}
        </>}
      </fieldset>}
      <div className="flex gap-3"><button className={btnPrimary} type="submit" disabled={saving || !questions || (!all && (stale || !complete))}>{saving ? t('common.saving') : t('common.saveChanges')}</button><button className={btnGhost} type="button" disabled={saving} onClick={onClose}>{t('common.cancel')}</button></div>
    </form>
  </Card>
}
