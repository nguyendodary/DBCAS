import { t, useLocale, message, number, percent, dateTime, time, dateOnly, intlLocale } from '../i18n'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api, { apiMessage } from '../api'
import { ActionSpinner, EmptyState, ErrorState, Loading } from '../components/States'
import { Icon } from '../components/ui'
import heroBg from '../assets/brand/nen1.jpg'
import heroVideo from '../assets/brand/video1.mp4'
import BackgroundVideo from '../components/BackgroundVideo'
import PersonalizedAssessment from '../components/PersonalizedAssessment'

const PAGE_SIZES = [5, 8, 12]

// UC12 — pick an active assessment and start (or resume) an adaptive session.
// Exact visual port of the learner prototype's exam centre: photo hero with
// the stats card, dark filter band, the bordered exam table and a pager.
export default function AssessmentsPage() {
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
      <section className="hero-photo" style={{ '--hero-img': `url(${heroBg})` }}>
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
        <section className="le-filter-bar" aria-label={t('assessment.filterLabel')}>
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

      <div className="content-wrap py-6">
        <PersonalizedAssessment assessments={items} />
        {error && <ErrorState message={error} onRetry={load} />}

        {items.length === 0 ? (
          <EmptyState title={t('assessment.empty')}>{t('assessment.emptyBody')}</EmptyState>
        ) : (
          <>
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-base font-bold text-ink" aria-label={t('nav.assessments')}>{t('assessment.listTitle')}</h2>
              <div className="lp-legend">
                <span><i className="lp-legend-dot" />{t('assessment.legendReady', { count: number(stats.ready) })}</span>
                <span><i className="lp-legend-dot rose" />{t('assessment.legendDone', { count: number(stats.completed) })}</span>
              </div>
            </div>

            <section className="le-table-card">
              <div className="overflow-x-auto" role="region" aria-label={t('assessment.listTitle')} tabIndex={0}>
                <table className="le-table">
                  <colgroup>
                    <col className="le-col-title" />
                    <col className="le-col-structure" />
                    <col className="le-col-duration" />
                    <col className="le-col-skills" />
                    <col className="le-col-result" />
                    <col className="le-col-action" />
                  </colgroup>
                  <thead>
                    <tr>
                      <th scope="col">{t('assessment.colName')}</th>
                      <th scope="col">{t('assessment.colStructure')}</th>
                      <th scope="col">{t('assessment.colDuration')}</th>
                      <th scope="col">{t('assessment.colSkills')}</th>
                      <th scope="col">{t('assessment.colResult')}</th>
                      <th scope="col">{t('assessment.colAction')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {paged.map(({ a, live, completed, state }) => {
                      const progress = live && a.max_questions ? Math.min(100, Math.round((live.answered_count / a.max_questions) * 100)) : 0
                      const score = completed?.overall_result_pct
                      const iconState = state === 'ready' ? 'available' : state
                      return (
                        <tr key={a.assessment_id} className={state === 'ready' ? 'le-available-row' : ''}>
                          <td>
                            <div className="le-exam-name">
                              <span className={`le-exam-icon ${iconState}`}>
                                <Icon name={state === 'completed' ? 'check' : state === 'in_progress' ? 'play' : 'file'} className="icon h-3.5 w-3.5" />
                              </span>
                              <div>
                                <span className={`le-status-label ${iconState}`}>{statusLabel(state)}</span>
                                <h3>{a.title}</h3>
                                {a.description && <p>{a.description}</p>}
                              </div>
                            </div>
                          </td>
                          <td><span className="le-structure">{t('assessment.maxQuestions', { value: number(a.max_questions) })}</span></td>
                          <td>
                            <span className="le-duration">
                              <Icon name="clock" className="icon" />
                              {t('assessment.duration', { value: number(a.duration_min) })}
                            </span>
                          </td>
                          <td>
                            <div className="le-tags">
                              <strong>{t('assessment.conceptCount', { count: a.concept_count })}</strong>
                              <span>{t('assessment.mix')}</span>
                            </div>
                          </td>
                          <td>
                            {live ? (
                              <div className="le-result">
                                <div className="flex justify-between text-[9px] text-mute"><span>{t('assessment.answeredProgress', { answered: number(live.answered_count), max: number(a.max_questions) })}</span><span>{progress}%</span></div>
                                <div className="mt-1 h-1.5 w-24 rounded-full bg-elev" role="progressbar" aria-label={t('assessment.progressLabel', { title: a.title })} aria-valuemin={0} aria-valuemax={a.max_questions} aria-valuenow={live.answered_count}>
                                  <div className="h-full rounded-full bg-cyan-400" style={{ width: `${progress}%` }} />
                                </div>
                              </div>
                            ) : completed ? (
                              <div className={`le-result ${score != null && score < 60 ? 'weak' : 'passed'}`}>
                                <strong>{score != null ? percent(score, { maximumFractionDigits: 0 }) : '—'}</strong>
                                <span>{score == null && completed.release_status && completed.release_status !== 'published' ? t(`supervisor.${completed.release_status}`) : score == null ? t('history.noGraded') : t('assessment.statCompleted')}</span>
                              </div>
                            ) : (
                              <span className="le-status-pill available">{t('assessment.ready')}</span>
                            )}
                          </td>
                          <td>
                            {completed && !live && <Link to={`/history/${completed.session_id}`} className="le-action mb-1">{t('assessment.viewResult')}</Link>}
                            <button
                              type="button"
                              onClick={() => (live ? navigate(`/exam/${live.session_id}`) : start(a.assessment_id))}
                              disabled={busyId === a.assessment_id}
                              className={`le-action ${completed && !live ? '' : 'primary'}`}
                            >
                              {busyId === a.assessment_id ? <ActionSpinner /> : <Icon name="arrowRight" className="icon" />}
                              {live ? t('assessment.resume') : busyId === a.assessment_id ? t('assessment.starting') : completed ? t('assessment.startAgain') : t('assessment.start')}
                            </button>
                          </td>
                        </tr>
                      )
                    })}
                    {paged.length === 0 && (
                      <tr><td colSpan={6} className="le-empty">{t('assessment.noMatches')}</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
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

        <p className="mt-5 text-sm text-mute">{t('assessment.pastSessions')}{' '}
          <Link to="/history" className="text-cyan-300 hover:underline">{t('assessment.historyLink')}</Link>
          .
        </p>
      </div>
    </>
  )
}
