import { t, useLocale, message, number, percent, dateTime, time, dateOnly, intlLocale } from '../../i18n'
import { useCallback, useEffect, useMemo, useState, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api, { apiMessage } from '../../api'
import { ActionSpinner, EmptyState, ErrorState, Loading } from '../../components/States'
import { Icon, Card, btnPrimary, inputCls } from '../../components/SharedComponents'
import heroBg from '../../assets/brand/learner-background.jpg'
import heroVideo from '../../assets/brand/learner-background.mp4'
import BackgroundVideo from '../../components/BackgroundVideo'

const PAGE_SIZES = [5, 8, 12]

// UC12 — pick an active assessment and start (or resume) an adaptive session.
// Published assessments with progress, result links and resumable sessions.
export default function Assessments_User() {
  useLocale()
  const [items, setItems] = useState(null)
  const [sessions, setSessions] = useState([])
  const [error, setError] = useState(null)
  const [busyId, setBusyId] = useState(null)
  const [query, setQuery] = useState('')
  const [status, setStatus] = useState('')
  const [duration, setDuration] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(8)
  const navigate = useNavigate()

  const load = useCallback(() => {
    setError(null)
    Promise.all([api.get('/assessments'), api.get('/sessions')])
      .then(([a, s]) => {
        setItems(a.data)
        setSessions(s.data)
      })
      .catch((e) => {
        setError(apiMessage(e, message('assessment.loadError')))
        setItems([])
      })
  }, [])

  useEffect(load, [load])

  async function start(assessmentId) {
    setBusyId(assessmentId)
    try {
      const r = await api.post(`/assessments/${assessmentId}/sessions`)
      navigate(`/exam/${r.data.session_id}`)
    } catch (e) {
      setError(apiMessage(e, message('assessment.startError')))
      setBusyId(null)
    }
  }

  const decorated = useMemo(() => (items || []).map((a) => {
    const related = sessions.filter((s) => s.assessment_id === a.assessment_id)
      .sort((left, right) => new Date(right.started_at) - new Date(left.started_at))
    const live = related.find((s) => s.status === 'in_progress')
    const completed = related.find((s) => s.status === 'completed' || s.status === 'timed_out')
    const state = live ? 'in_progress' : completed ? 'completed' : 'ready'
    return { a, live, completed, state }
  }), [items, sessions])

  const visible = useMemo(() => decorated.filter(({ a, state }) => {
    if (status && state !== status) return false
    if (duration === 'short' && !(a.duration_min <= 45)) return false
    if (duration === 'medium' && !(a.duration_min > 45 && a.duration_min <= 60)) return false
    if (duration === 'long' && !(a.duration_min > 60)) return false
    const needle = query.trim().toLowerCase()
    if (needle && !(a.title || '').toLowerCase().includes(needle) && !(a.description || '').toLowerCase().includes(needle)) return false
    return true
  }), [decorated, query, status, duration])

  const stats = useMemo(() => {
    const scores = sessions
      .filter((s) => (s.status === 'completed' || s.status === 'timed_out') && s.overall_result_pct != null)
      .map((s) => s.overall_result_pct)
    return {
      ready: decorated.filter((d) => d.state === 'ready').length,
      in_progress: decorated.filter((d) => d.state === 'in_progress').length,
      completed: decorated.filter((d) => d.state === 'completed').length,
      average: scores.length ? scores.reduce((sum, s) => sum + Number(s), 0) / scores.length : null,
    }
  }, [decorated, sessions])

  const pages = Math.max(1, Math.ceil(visible.length / pageSize))
  const safePage = Math.min(page, pages)
  const startIndex = (safePage - 1) * pageSize
  const paged = visible.slice(startIndex, startIndex + pageSize)

  function resetFilters() {
    setQuery('')
    setStatus('')
    setDuration('')
    setPage(1)
  }

  const statusLabel = (state) =>
    state === 'in_progress' ? t('assessment.inProgress')
      : state === 'completed' ? t('assessment.statCompleted')
        : t('assessment.ready')

  if (error && !items?.length) {
    return (
      <div className="content-wrap py-8"><ErrorState message={error} onRetry={load} /></div>
    )
  }
  if (items === null) {
    return (
      <div className="content-wrap py-8"><Loading label={t('assessment.loading')} /></div>
    )
  }

  return (
    <>
      <section className="hero-photo assessment-catalog-hero" style={{ '--hero-img': `url(${heroBg})` }}>
        <BackgroundVideo className="hero-video" src={heroVideo} poster={heroBg} />
        <div className="content-wrap relative z-[1] flex min-h-[160px] flex-wrap items-center justify-between gap-7 py-7">
          <div className="max-w-[720px]">
            <p className="text-[9px] font-semibold tracking-[.14em] text-accent">{t('assessment.heroEyebrow')}</p>
            <h1 className="my-2.5 text-[25px] font-bold leading-normal text-ink">{t('assessment.pageTitle')}</h1>
            <p className="text-xs leading-relaxed text-sub">{t('assessment.intro')}</p>
          </div>
          {items.length > 0 && (
            <div className="le-hero-stats">
              <div><span>{t('assessment.statCompleted')}</span><strong>{number(stats.completed)}<small> {t('assessment.statUnit')}</small></strong></div>
              <div><span>{t('assessment.statAverage')}</span><strong className="le-green">{stats.average == null ? '—' : number(stats.average / 10, { maximumFractionDigits: 1 })}<small> {t('assessment.scoreUnit')}</small></strong></div>
              <div><span>{t('assessment.statReady')}</span><strong>{number(stats.ready)}<small> {t('assessment.statUnit')}</small></strong></div>
            </div>
          )}
        </div>
      </section>

      {items.length > 0 && (
        <section className="le-filter-bar assessment-catalog-filter" aria-label={t('assessment.filterLabel')}>
          <div className="content-wrap le-filters" role="search">
            <label className="le-search">
              <Icon name="search" className="icon h-4 w-4 shrink-0" />
              <input
                type="search"
                value={query}
                onChange={(e) => { setQuery(e.target.value); setPage(1) }}
                placeholder={t('assessment.searchPlaceholder')}
                aria-label={t('assessment.searchPlaceholder')}
              />
            </label>
            <select
              aria-label={t('assessment.durationAll')}
              value={duration}
              onChange={(e) => { setDuration(e.target.value); setPage(1) }}
              className="le-select"
            >
              <option value="">{t('assessment.durationAll')}</option>
              <option value="short">{t('assessment.durationShort')}</option>
              <option value="medium">{t('assessment.durationMedium')}</option>
              <option value="long">{t('assessment.durationLong')}</option>
            </select>
            <select
              aria-label={t('assessment.statusAll')}
              value={status}
              onChange={(e) => { setStatus(e.target.value); setPage(1) }}
              className="le-select"
            >
              <option value="">{t('assessment.statusAll')}</option>
              <option value="ready">{t('assessment.ready')}</option>
              <option value="in_progress">{t('assessment.inProgress')}</option>
              <option value="completed">{t('assessment.statCompleted')}</option>
            </select>
            <button type="button" className="le-reset" onClick={resetFilters}>
              <Icon name="reset" className="icon h-3.5 w-3.5" />
              {t('assessment.resetFilters')}
            </button>
          </div>
        </section>
      )}

      <div className="content-wrap assessment-catalog py-8">
        <PersonalizedAssessment assessments={items} />
        {error && <ErrorState message={error} onRetry={load} />}

        {items.length === 0 ? (
          <EmptyState title={t('assessment.empty')}>{t('assessment.emptyBody')}</EmptyState>
        ) : (
          <>
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <h2 className="assessment-list-heading" aria-label={t('nav.assessments')}>{t('assessment.listTitle')}<span>{number(visible.length)}</span></h2>
            </div>

            <section className="assessment-card-list-shell" aria-label={t('assessment.listTitle')}>
              <div className="assessment-card-grid">
                {paged.map(({ a, live, completed, state }, index) => {
                  const progress = live && a.max_questions ? Math.min(100, Math.round((live.answered_count / a.max_questions) * 100)) : 0
                  const score = completed?.overall_result_pct
                  return <article key={a.assessment_id} className={`assessment-course-card assessment-course-card--${state}`} aria-labelledby={`assessment-title-${a.assessment_id}`}>
                    <div className="assessment-course-summary">
                    <span className="assessment-course-number" aria-hidden="true">{String(startIndex + index + 1).padStart(2, '0')}</span>
                    <div className="assessment-course-copy">
                    <div className="assessment-course-top">
                      <h3 id={`assessment-title-${a.assessment_id}`}>{a.title}</h3>
                      <span className={`assessment-course-status ${state}`}>{statusLabel(state)}</span>
                    </div>
                    {a.description && <p className="assessment-course-description">{a.description}</p>}
                    </div>
                    </div>
                    <div className="assessment-course-details">
                    <div className="assessment-course-meta">
                      <div><span>{t('assessment.colDuration')}</span><strong>{t('assessment.duration', { value: number(a.duration_min) })}</strong></div>
                      <div><span>{t('assessment.colStructure')}</span><strong>{t('assessment.maxQuestions', { value: number(a.max_questions) })}</strong></div>
                      <div><span>{t('assessment.colSkills')}</span><strong>{t('assessment.conceptCount', { count: a.concept_count })}</strong></div>
                    </div>
                    <p className="assessment-course-format"><Icon name="layers" className="icon" />{t('assessment.mix')}</p>
                    {live && <div className="assessment-course-progress">
                      <div><span>{t('assessment.answeredProgress', { answered: number(live.answered_count), max: number(a.max_questions) })}</span><strong>{progress}%</strong></div>
                      <div className="assessment-progress-track" role="progressbar" aria-label={t('assessment.progressLabel', { title: a.title })} aria-valuemin={0} aria-valuemax={a.max_questions} aria-valuenow={live.answered_count}>
                        <span style={{ width: `${progress}%` }} />
                      </div>
                    </div>}
                    {completed && !live && <div className={`le-result assessment-course-result ${score != null && score < 60 ? 'weak' : 'passed'}`}>
                      <strong>{score != null ? percent(score, { maximumFractionDigits: 0 }) : '—'}</strong>
                      <span>{score == null && completed.release_status && completed.release_status !== 'published' ? t(`supervisor.${completed.release_status}`) : score == null ? t('history.noGraded') : t('assessment.statCompleted')}</span>
                    </div>}
                    </div>
                    <div className="assessment-course-footer">
                      {completed && !live && <Link to={`/history/${completed.session_id}`} className="assessment-course-result-link">{t('assessment.viewResult')}</Link>}
                      <button type="button" onClick={() => live ? navigate(`/exam/${live.session_id}`) : start(a.assessment_id)} disabled={busyId !== null} className="assessment-course-start">
                        {busyId === a.assessment_id ? <ActionSpinner /> : <Icon name={live ? 'play' : 'arrowRight'} className="icon" />}
                        {live ? t('assessment.resume') : busyId === a.assessment_id ? t('assessment.starting') : completed ? t('assessment.startAgain') : t('assessment.start')}
                      </button>
                    </div>
                  </article>
                })}
              </div>
              {paged.length === 0 && <div className="assessment-catalog-empty"><EmptyState title={t('assessment.noMatches')} /></div>}
              <div className="le-pager">
                <div className="le-pager-info">
                  <span>{t('assessment.pageInfo', { from: visible.length ? startIndex + 1 : 0, to: Math.min(startIndex + pageSize, visible.length), total: number(visible.length) })}</span>
                  <label>
                    {t('assessment.perPage')}
                    <select value={pageSize} onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1) }}>
                      {PAGE_SIZES.map((n) => <option key={n} value={n}>{n}</option>)}
                    </select>
                  </label>
                </div>
                <nav className="le-pagination" aria-label={t('assessment.pagination')}>
                  <button type="button" className="le-page-btn" disabled={safePage <= 1} onClick={() => setPage(safePage - 1)} aria-label={t('assessment.prevPage')}>‹</button>
                  {Array.from({ length: pages }, (_, i) => i + 1).map((n) => (
                    <button key={n} type="button" className={`le-page-btn${n === safePage ? ' active' : ''}`} onClick={() => setPage(n)} aria-current={n === safePage ? 'page' : undefined}>{n}</button>
                  ))}
                  <button type="button" className="le-page-btn" disabled={safePage >= pages} onClick={() => setPage(safePage + 1)} aria-label={t('assessment.nextPage')}>›</button>
                </nav>
              </div>
            </section>
          </>
        )}

        <div className="assessment-history-corner">
          <Link to="/history" className="assessment-history-link">
            <Icon name="reset" className="icon" />{t('assessment.historyAction')}
            <Icon name="arrowRight" className="icon" />
          </Link>
        </div>
      </div>
    </>
  )
}

export function PersonalizedAssessment({ assessments }) {
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
