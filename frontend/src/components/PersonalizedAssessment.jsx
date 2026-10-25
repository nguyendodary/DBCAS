import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api, { apiMessage } from '../api'
import { t, useLocale } from '../i18n'
import { Card, btnPrimary, inputCls } from './SharedComponents'
import { ErrorState } from './States'

export default function PersonalizedAssessment({ assessments }) {
  useLocale()
  const navigate = useNavigate()
  const templates = assessments.filter(a => a.concepts?.length)
  const [templateId, setTemplateId] = useState('')
  const [skills, setSkills] = useState([])
  const [difficulty, setDifficulty] = useState('EASY')
  const [mode, setMode] = useState('PRACTICE')
  const [questionCount, setQuestionCount] = useState(3)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const request = useRef(null)
  const guard = useRef(false)
  if (!templates.length) return null
  const selected = templates.find(a => String(a.assessment_id) === templateId) || templates[0]
  function changeSkills(next) { setSkills(next); request.current = null }
  async function start(event) {
    event.preventDefault()
    if (guard.current || !skills.length) return
    guard.current = true
    setBusy(true)
    setError(null)
    request.current ||= crypto.randomUUID()
    try {
      const result = await api.post(`/assessments/${selected.assessment_id}/sessions`, {
        concept_ids: skills, difficulty, request_id: request.current,
        ...(mode === 'PRACTICE' ? { mode, question_count: questionCount } : {}),
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
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="block text-sm text-sub">{t('supervisor.format')}
            <select aria-label={t('supervisor.format')} className={`${inputCls} mt-1 w-full`} value={mode} onChange={e => { setMode(e.target.value); request.current = null }}>
              {['PRACTICE', 'FORMAL'].map(value => <option key={value} value={value}>{t(`supervisor.${value}`)}</option>)}
            </select>
          </label>
          {mode === 'PRACTICE' && <label className="block text-sm text-sub">{t('supervisor.questionCount')}
            <select aria-label={t('supervisor.questionCount')} className={`${inputCls} mt-1 w-full`} value={questionCount} onChange={e => { setQuestionCount(Number(e.target.value)); request.current = null }}>
              {[1, 2, 3, 5, 10, 13].map(count => <option key={count} value={count}>{count}</option>)}
            </select>
          </label>}
        </div>
        <p className="text-xs text-mute">{t(mode === 'PRACTICE' ? 'supervisor.practiceHelp' : 'supervisor.formalHelp')}</p>
        <label className="block text-sm text-sub">{t('supervisor.rules')}
          <select aria-label={t('supervisor.rules')} className={`${inputCls} mt-1 w-full`} value={selected.assessment_id} onChange={e => { setTemplateId(e.target.value); changeSkills([]) }}>
            {templates.map(a => <option key={a.assessment_id} value={a.assessment_id}>{a.title}</option>)}
          </select>
        </label>
        <fieldset className="rounded-lg border border-edge p-3">
          <legend className="px-1 text-sm font-semibold text-ink">{t('supervisor.skills')}</legend>
          <button type="button" className="mb-3 text-sm text-cyan-300 underline" onClick={() => { changeSkills(selected.concepts.map(c => c.concept_id)); if (selected.concepts.length > questionCount) setQuestionCount([1, 2, 3, 5, 10, 13].find(count => count >= selected.concepts.length) || 13) }}>{t('supervisor.comprehensive')}</button>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {selected.concepts.map(c => <label key={c.concept_id} className="flex items-start gap-2 text-sm text-sub">
              <input type="checkbox" className="mt-1" checked={skills.includes(c.concept_id)} onChange={e => changeSkills(e.target.checked ? [...skills, c.concept_id] : skills.filter(id => id !== c.concept_id))} />
              <span>{c.concept_name}<span className="block text-xs text-mute">{c.concept_code}</span></span>
            </label>)}
          </div>
        </fieldset>
        <label className="block text-sm text-sub">{t('supervisor.difficulty')}
          <select aria-label={t('supervisor.difficulty')} className={`${inputCls} mt-1 w-full sm:w-64`} value={difficulty} onChange={e => { setDifficulty(e.target.value); request.current = null }}>
            {['EASY', 'MEDIUM', 'HARD'].map(d => <option key={d} value={d}>{t(`supervisor.${d}`)}</option>)}
          </select>
        </label>
        <p className="text-sm text-sub">{t(selected.result_release_policy === 'HUMAN_VERIFIED' ? 'supervisor.humanHelp' : 'supervisor.immediateHelp')}</p>
        <button type="submit" className={btnPrimary} disabled={busy || !skills.length}>{busy ? t('assessment.starting') : t('supervisor.start')}</button>
      </fieldset>
    </form>
    {error && <div className="mt-3"><ErrorState message={error} onRetry={() => setError(null)} /></div>}
  </Card>
}
