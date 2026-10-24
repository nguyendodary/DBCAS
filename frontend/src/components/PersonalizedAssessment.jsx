import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api, { apiMessage } from '../api'
import { t, useLocale } from '../i18n'
import { Card, btnPrimary, inputCls } from './ui'
import { ErrorState } from './States'

export default function PersonalizedAssessment({ assessments }) {
  useLocale()
  const navigate = useNavigate()
  const templates = assessments.filter(a => a.concepts?.length)
  const [templateId, setTemplateId] = useState('')
  const [skills, setSkills] = useState([])
  const [skillQuery, setSkillQuery] = useState('')
  const [difficulty, setDifficulty] = useState('EASY')
  const [mode, setMode] = useState('PRACTICE')
  const [questionCount, setQuestionCount] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const request = useRef(null)
  const guard = useRef(false)
  if (!templates.length) return null
  const selected = templateId ? templates.find(a => String(a.assessment_id) === templateId)
    : templates.find(a => skills.every(id => a.concepts.some(c => c.concept_id === id)))
  const catalog = templateId ? selected.concepts : [...new Map(templates.flatMap(a => a.concepts).map(c => [c.concept_id, c])).values()]
  const visibleSkills = catalog.filter(c => skills.includes(c.concept_id) || `${c.concept_name} ${c.concept_code || ''} ${c.subject_area || ''}`.toLocaleLowerCase().includes(skillQuery.trim().toLocaleLowerCase()))
  const groups = [...new Set(catalog.map(c => c.subject_area).filter(Boolean))]
  function changeSkills(next) { setSkills(next); request.current = null }
  async function start(event) {
    event.preventDefault()
    if (guard.current || !skills.length || !selected) return
    guard.current = true
    setBusy(true)
    setError(null)
    request.current ||= crypto.randomUUID()
    try {
      const result = await api.post(`/assessments/${selected.assessment_id}/sessions`, {
        concept_ids: skills, difficulty, request_id: request.current,
        ...(mode === 'PRACTICE' ? { mode, question_count: questionCount || null } : {}),
      })
      navigate(`/exam/${result.data.session_id}`)
    } catch (err) { setError(apiMessage(err)) }
    finally { guard.current = false; setBusy(false) }
  }
  return <Card className="mb-6 p-5">
    <h2 className="text-lg font-bold text-ink">{t('supervisor.personalized')}</h2>
    <p className="mt-1 text-sm text-sub">{t('supervisor.selectionHelp')}</p>
    <form onSubmit={start} className="mt-4 space-y-4">
      <fieldset disabled={busy} className="space-y-4">
        <fieldset className="rounded-xl border border-edge p-4">
          <legend className="px-1 text-sm font-semibold text-ink">{t('supervisor.skills')}</legend>
          <input type="search" aria-label={t('supervisor.searchSkills')} placeholder={t('supervisor.searchSkills')} value={skillQuery} onChange={e => setSkillQuery(e.target.value)} className={`${inputCls} mb-3 w-full`} />
          <div className="mb-4 flex flex-wrap gap-2">
            {groups.map(group => {
              const ids = catalog.filter(c => c.subject_area === group).map(c => c.concept_id)
              const allSelected = ids.every(id => skills.includes(id))
              return <button key={group} type="button" aria-pressed={allSelected} className="rounded-lg border border-edge px-3 py-2 text-sm text-ink aria-pressed:border-cyan-400 aria-pressed:bg-cyan-400/10" onClick={() => changeSkills(allSelected ? skills.filter(id => !ids.includes(id)) : [...new Set([...skills, ...ids])])}>{group}</button>
            })}
          </div>
          <div className="grid max-h-64 gap-3 overflow-y-auto sm:grid-cols-2 lg:grid-cols-3">
            {visibleSkills.map(c => <label key={c.concept_id} className="flex cursor-pointer items-start gap-2 rounded-lg border border-edge p-3 text-sm text-sub has-checked:border-cyan-400/60 has-checked:bg-cyan-400/5">
              <input type="checkbox" className="mt-0.5" checked={skills.includes(c.concept_id)} onChange={e => changeSkills(e.target.checked ? [...skills, c.concept_id] : skills.filter(id => id !== c.concept_id))} />
              <span>{c.concept_name}</span>
            </label>)}
          </div>
          {!visibleSkills.length && <p role="status" className="text-sm text-sub">{t('supervisor.noMatchingSkills')}</p>}
          <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs text-sub">
            <span>{t('authoring.selectedCount', { count: skills.length })}</span>
            <button type="button" className="underline" onClick={() => changeSkills((selected || templates[0]).concepts.map(c => c.concept_id))}>{t('supervisor.comprehensive')}</button>
          </div>
        </fieldset>
        <fieldset>
          <legend className="mb-2 text-sm font-semibold text-ink">{t('supervisor.difficulty')}</legend>
          <div className="inline-flex max-w-full rounded-xl border border-edge bg-panel p-1">
            {['EASY', 'MEDIUM', 'HARD'].map(d => <label key={d} className="relative cursor-pointer">
              <input className="peer absolute inset-0 z-10 m-0 h-full w-full cursor-pointer opacity-0" type="radio" name="assessment-difficulty" value={d} checked={difficulty === d} onChange={() => { setDifficulty(d); request.current = null }} />
              <span className="pointer-events-none block rounded-lg px-5 py-2 text-sm font-medium text-sub peer-checked:bg-cyan-400/15 peer-checked:text-ink peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-cyan-400">{t(`supervisor.difficulty${d}`)}</span>
            </label>)}
          </div>
        </fieldset>
        <details className="rounded-lg border border-edge px-3 py-2 text-sm text-sub">
          <summary className="cursor-pointer font-medium">{t('supervisor.assessmentOptions')}</summary>
          <div className="mt-3 space-y-3">
          <div className="grid gap-3 sm:grid-cols-2">
          <label className="block text-sm text-sub">{t('supervisor.format')}
            <select aria-label={t('supervisor.format')} className={`${inputCls} mt-1 w-full`} value={mode} onChange={e => { setMode(e.target.value); request.current = null }}>
              {['PRACTICE', 'FORMAL'].map(value => <option key={value} value={value}>{t(`supervisor.${value}`)}</option>)}
            </select>
          </label>
          {mode === 'PRACTICE' && <label className="block text-sm text-sub">{t('supervisor.questionCount')}
            <select aria-label={t('supervisor.questionCount')} className={`${inputCls} mt-1 w-full`} value={questionCount} onChange={e => { setQuestionCount(e.target.value ? Number(e.target.value) : ''); request.current = null }}>
              <option value="">{t('supervisor.automaticLength')}</option>
              {[1, 2, 3, 5, 10, 13].map(count => <option key={count} value={count}>{count}</option>)}
            </select>
          </label>}
        </div>
        <p className="text-xs text-mute">{t(mode === 'PRACTICE' ? 'supervisor.practiceHelp' : 'supervisor.formalHelp')}</p>
        <label className="block text-sm text-sub">{t('supervisor.rules')}
          <select aria-label={t('supervisor.rules')} className={`${inputCls} mt-1 w-full`} value={templateId} onChange={e => { setTemplateId(e.target.value); changeSkills([]); setSkillQuery('') }}>
            <option value="">{t('supervisor.automaticLength')}</option>
            {templates.map(a => <option key={a.assessment_id} value={a.assessment_id}>{a.title}</option>)}
          </select>
        </label>
          </div>
        </details>
        <p role={!selected ? 'status' : undefined} className="text-sm text-sub">{!selected ? t('supervisor.unavailableSelection') : t(selected.result_release_policy === 'HUMAN_VERIFIED' ? 'supervisor.humanHelp' : 'supervisor.immediateHelp')}</p>
        <button type="submit" className={btnPrimary} disabled={busy || !skills.length || !selected}>{busy ? t('assessment.starting') : t('supervisor.start')}</button>
      </fieldset>
    </form>
    {error && <div className="mt-3"><ErrorState message={error} onRetry={() => setError(null)} /></div>}
  </Card>
}
