import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api, { apiMessage } from '../api'
import { Card, btnPrimary, btnGhost } from '../components/ui'
import { ActionSpinner, ErrorState } from '../components/States'
import { EvaluationCharts } from '../components/EvaluationCharts'
import AdaptiveResult from '../components/AdaptiveResult'
import ReviewRequestCard from '../components/ReviewRequestCard'
import { isAdaptiveResult } from '../assessmentStyle'
import { t, useLocale } from '../i18n'

const MAX_POLL_DURATION_MS = 5 * 60 * 1000
export const MAX_WEAK_PRACTICE_CONCEPTS = 5

function isOfficialResult(data) {
  return (
    data?.status === 'ready' &&
    data.is_current === true &&
    data.final === true &&
    data.source === 'ai' &&
    data.result_version > 0 &&
    Boolean(data.score)
  )
}

function validateView(data) {
  if (
    !data ||
    ![
      'empty',
      'pending',
      'processing',
      'updating',
      'provisional',
      'ready',
      'awaiting_approval',
      'cancelled',
    ].includes(data.status) ||
    (['provisional', 'ready'].includes(data.status) &&
      !data.result?.evaluation &&
      !isOfficialResult(data))
  )
    throw new Error('Invalid evaluation response')
  return data
}

// Reuses the result's documented below-target rule; no new scoring model.
// Largest shortfall first, with concept id as the deterministic tie-breaker.
export function weakPracticeConcepts(conceptResults = []) {
  if (!Array.isArray(conceptResults)) return []
  return conceptResults
    .filter(
      (c) =>
        c?.below_target &&
        c.covered !== false &&
        Number.isInteger(c.concept_id) &&
        c.competency_pct != null &&
        c.target_pct != null &&
        Number.isFinite(Number(c.competency_pct)) &&
        Number.isFinite(Number(c.target_pct)),
    )
    .map((c) => ({
      ...c,
      shortfall: Number(c.target_pct) - Number(c.competency_pct),
    }))
    .sort((a, b) => b.shortfall - a.shortfall || a.concept_id - b.concept_id)
    .slice(0, MAX_WEAK_PRACTICE_CONCEPTS)
}

export function EvaluationContent({ data, overall = false }) {
  useLocale()
  const [recommendationDismissed, setRecommendationDismissed] = useState(false)
  const evaluation = data.result?.evaluation
  const weakConcepts = weakPracticeConcepts(data.concept_results)
  const questionResults = Object.fromEntries(
    (data.question_results || []).map((item) => [item.attempt_id, item]),
  )
  return (
    <div className="space-y-5">
      {data.provisional && (
        <p role="status" className="rounded-xl border border-amber-500 p-4 font-semibold">
          {t('assessmentStyle.fixed.provisionalTitle')}
          <span className="mt-1 block text-sm font-normal">
            {t('assessmentStyle.fixed.provisionalBody')}
          </span>
        </p>
      )}
      {data.approved && (
        <p role="status" className="rounded-xl border border-emerald-500 p-4 font-semibold">
          {t('assessmentStyle.fixed.approvedTitle')}
          {data.adjusted && (
            <span className="mt-1 block text-sm font-normal">
              {t('assessmentStyle.fixed.approvedAdjusted')}
            </span>
          )}
        </p>
      )}
      {data.pending_count > 0 && overall && (
        <p className="text-sm text-sub">
          {t('ui.evaluation.pendingCount', { count: data.pending_count })}
        </p>
      )}
      {overall && data.attempt_count === 1 && (
        <p className="rounded-lg border border-edge p-4 text-sub">{t('ui.evaluation.needMore')}</p>
      )}
      {data.result?.evaluator_fallback && (
        <p className="text-sm text-sub">{t('ui.evaluation.fallback')}</p>
      )}
      {data.score && (
        <Card className="p-5">
          <p className="text-sm font-semibold uppercase tracking-wide text-cyan-300">
            {t(
              data.provisional || data.status === 'provisional'
                ? 'assessmentStyle.fixed.provisionalLabel'
                : 'assessmentStyle.fixed.resultLabel',
            )}
          </p>
          <h2 className="mt-1 text-lg font-semibold">
            {overall ? t('ui.evaluation.cumulativeScore') : t('ui.evaluation.attemptScore')}
          </h2>
          <p className="mt-3 text-3xl font-bold tabular-nums">
            {Number(data.score.percentage).toFixed(2)}%
          </p>
          <p className="mt-2 text-sub">
            {t('ui.evaluation.scoreLine', {
              earned: data.score.earned,
              possible: data.score.possible,
              count: data.attempt_count,
            })}
          </p>
        </Card>
      )}
      {weakConcepts.length > 0 && !recommendationDismissed && (
        <Card className="p-5">
          <section aria-labelledby="weak-practice-heading">
            <h2 id="weak-practice-heading" className="text-lg font-semibold">
              {t('weakPractice.promptTitle')}
            </h2>
            <p className="mt-2 text-sub">{t('weakPractice.promptBody')}</p>
            <p className="mt-3 text-sm font-medium text-ink">{t('weakPractice.promptListLabel')}</p>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sub">
              {weakConcepts.map((c) => (
                <li key={c.concept_id}>{c.concept_name || `#${c.concept_id}`}</li>
              ))}
            </ul>
            <div className="mt-4 flex flex-wrap gap-3">
              <Link
                className={btnPrimary}
                to={`/assessments?concepts=${weakConcepts.map((c) => c.concept_id).join(',')}`}
              >
                {t('weakPractice.promptAction')}
              </Link>
              <button
                type="button"
                className={btnGhost}
                onClick={() => setRecommendationDismissed(true)}
              >
                {t('weakPractice.promptDismiss')}
              </button>
            </div>
            <p className="mt-3 text-sm text-mute">{t('weakPractice.promptHint')}</p>
          </section>
        </Card>
      )}
      {data.uncovered_concepts?.length > 0 && (
        <Card className="p-5">
          <h2 className="text-lg font-semibold">{t('ui.evaluation.uncoveredTitle')}</h2>
          <p className="mt-2 text-sub">{t('ui.evaluation.uncoveredBody')}</p>
          <ul className="mt-3 list-disc space-y-1 pl-5 text-sub">
            {data.uncovered_concepts.map((c) => (
              <li key={c.concept_id}>{c.concept_name}</li>
            ))}
          </ul>
        </Card>
      )}
      {data.concept_results?.length > 0 && (
        <Card className="p-5">
          <h2 className="text-lg font-semibold">{t('ui.evaluation.conceptTitle')}</h2>
          <ul className="mt-4 space-y-4">
            {data.concept_results.map((c) => (
              <li key={c.concept_id} className="border-b border-edge pb-4 last:border-0">
                <p className="font-semibold text-ink">
                  {c.concept_name || `#${c.concept_id}`}
                  {c.competency_pct != null && (
                    <span className="mt-1 block break-words font-normal text-sub">
                      {Number(c.competency_pct).toFixed(2)}%
                      {c.target_pct != null &&
                        ` / ${t('ui.evaluation.target', {
                          value: Number(c.target_pct).toFixed(2),
                        })}`}
                    </span>
                  )}
                </p>
                {!c.covered && (
                  <p className="mt-1 text-sm text-amber-300">{t('ui.evaluation.noQuestion')}</p>
                )}
                {c.strength && (
                  <p className="mt-1 text-sm text-emerald-300">
                    {t('ui.evaluation.strength', { value: c.strength })}
                  </p>
                )}
                {c.weakness && (
                  <p className="mt-1 text-sm text-amber-300">
                    {t('ui.evaluation.weakness', { value: c.weakness })}
                  </p>
                )}
                {c.recommendation && (
                  <p className="mt-1 text-sm text-sub">
                    {t('ui.evaluation.recommendation', { value: c.recommendation })}
                  </p>
                )}
              </li>
            ))}
          </ul>
        </Card>
      )}
      {evaluation && (
        <Card className="p-5">
          <h2 className="text-xl font-semibold">{t('ui.evaluation.commentsTitle')}</h2>
          <p className="mt-3 whitespace-pre-wrap text-sub">{evaluation.summary}</p>
          {overall && data.attempt_count >= 2 && evaluation.trend && (
            <p className="mt-3 text-sub">{evaluation.trend}</p>
          )}
        </Card>
      )}
      <EvaluationCharts
        dimensions={data.dimensions}
        history={overall && data.attempt_count >= 2 ? data.history : []}
      />
      {evaluation && (
        <>
          <div className="grid gap-4 md:grid-cols-2">
            {[
              ['strengths', t('ui.evaluation.strengths')],
              ['weaknesses', t('ui.evaluation.weaknesses')],
              ['suggestions', t('ui.evaluation.suggestions')],
              ['learning_path', t('ui.evaluation.learningPath')],
            ].map(([key, label]) => (
              <Card className="p-5" key={key}>
                <h2 className="text-lg font-semibold">{label}</h2>
                <ul className="mt-3 list-disc space-y-2 pl-5 text-sub">
                  {evaluation[key].map((text, i) => (
                    <li key={i}>{text}</li>
                  ))}
                </ul>
              </Card>
            ))}
          </div>
          {!overall && (
            <Card className="p-5">
              <h2 className="text-xl font-semibold">{t('ui.evaluation.questionComments')}</h2>
              <ol className="mt-4 space-y-4">
                {evaluation.question_comments.map((item, i) => (
                  <li key={item.attempt_id} className="border-b border-edge pb-4 last:border-0">
                    <h3 className="font-semibold">{t('ui.evaluation.questionN', { n: i + 1 })}</h3>
                    {questionResults[item.attempt_id] && (
                      <p className="mt-1 text-sm text-sub">
                        {t('ui.evaluation.score', {
                          score: questionResults[item.attempt_id].score ?? '—',
                          points: questionResults[item.attempt_id].points,
                        })}
                      </p>
                    )}
                    <p className="mt-2 text-sub">{item.comment}</p>
                    {item.essay_score_proposal != null && (
                      <p className="mt-1 text-sm text-sub">
                        {t('ui.evaluation.essayProposal', { value: item.essay_score_proposal })}
                      </p>
                    )}
                  </li>
                ))}
              </ol>
            </Card>
          )}
          {data.details_truncated && (
            <p className="text-sm text-mute">
              {overall ? t('ui.evaluation.truncatedOverall') : t('ui.evaluation.truncatedAttempt')}
            </p>
          )}
        </>
      )}
    </div>
  )
}

export default function EvaluationPage({ overall = false }) {
  const { sessionId } = useParams()
  const [data, setData] = useState(null)
  const [sessionResult, setSessionResult] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [expired, setExpired] = useState(false)
  const [reload, setReload] = useState(0)
  const sequence = useRef(0)
  const path = overall ? '/evaluations/overall' : `/evaluations/attempts/${sessionId}`
  const refreshOfficialResult = useCallback(
    async (signal) => {
      const { data: result } = await api.get(path, { signal })
      if (signal.aborted) return
      if (!isOfficialResult(result) || result.result_version < 2)
        throw new Error('Official V2 unavailable')
      setData(result)
    },
    [path],
  )
  useEffect(() => {
    const run = ++sequence.current
    const started = Date.now()
    let timer,
      canceled = false
    setData(null)
    setError(null)
    setExpired(false)
    setBusy(false)
    async function poll() {
      try {
        const r = await api.get(path, { timeout: 15000 })
        if (canceled || run !== sequence.current) return
        setData(validateView(r.data))
        const elapsed = Date.now() - started
        const withinBudget = elapsed < MAX_POLL_DURATION_MS
        if (r.data.status === 'awaiting_approval') {
          if (withinBudget) timer = setTimeout(poll, elapsed < 45000 ? 1500 : 10000)
          else setExpired(true)
        } else if (r.data.status === 'provisional') {
          if (withinBudget) timer = setTimeout(poll, 15000)
          else setExpired(true)
        } else if (r.data.status === 'updating') {
          if (withinBudget) timer = setTimeout(poll, 2000)
          else setExpired(true)
        } else if (['pending', 'processing'].includes(r.data.status)) {
          if (Date.now() - started < 45000) timer = setTimeout(poll, 1500)
          else {
            const fallback = await api.post(`${path}/retry`, null, { timeout: 15000 })
            if (!canceled && run === sequence.current) {
              setData(validateView(fallback.data))
              setExpired(fallback.data.status !== 'ready')
            }
          }
        }
      } catch (e) {
        if (!canceled && run === sequence.current) {
          setError(apiMessage(e))
          setExpired(true)
        }
      }
    }
    poll()
    return () => {
      canceled = true
      clearTimeout(timer)
      sequence.current += 1
    }
  }, [path, reload])
  // The evaluation endpoint does not carry the result kind. Session state does,
  // so read it here to decide between an official score and estimated ability.
  useEffect(() => {
    if (overall || !sessionId) return
    let active = true
    api
      .get(`/sessions/${sessionId}`)
      .then(({ data: session }) => {
        if (active) setSessionResult(session)
      })
      .catch(() => {
        /* the evaluation view still renders if session metadata is unavailable */
      })
    return () => {
      active = false
    }
  }, [overall, sessionId])
  async function retry() {
    if (busy) return
    setBusy(true)
    setError(null)
    const run = ++sequence.current
    try {
      const r = await api.post(`${path}/retry`, null, { timeout: 15000 })
      if (run === sequence.current) {
        setData(validateView(r.data))
        if (['pending', 'processing'].includes(r.data.status)) setReload((value) => value + 1)
        else setExpired(!['ready', 'empty'].includes(r.data.status))
      }
    } catch (e) {
      if (run === sequence.current) setError(apiMessage(e))
    } finally {
      if (run === sequence.current) setBusy(false)
    }
  }
  const waiting = !data || ['pending', 'processing'].includes(data.status)
  const adaptive = isAdaptiveResult(sessionResult)
  return (
    <div className="content-wrap mx-auto max-w-5xl space-y-5 py-8">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-3xl font-bold">
          {overall ? t('ui.evaluation.titleOverall') : t('ui.evaluation.titleAttempt')}
        </h1>
        {!overall && (
          <Link className={btnGhost} to={`/history/${sessionId}`}>
            {t('ui.evaluation.viewSubmission')}
          </Link>
        )}
      </header>
      {error && <ErrorState message={error} onRetry={retry} />}
      {data?.status === 'empty' ? (
        <Card className="space-y-4 p-6">
          <h2 className="text-xl font-semibold">{t('ui.evaluation.startTitle')}</h2>
          <p className="text-sub">{t('ui.evaluation.startBody')}</p>
          {data.pending_count > 0 && (
            <p className="text-sub">
              {t('ui.evaluation.pendingShort', { count: data.pending_count })}
            </p>
          )}
          <Link className={btnPrimary} to="/assessments">
            {t('ui.evaluation.startPractice')}
          </Link>
        </Card>
      ) : data?.status === 'cancelled' ? (
        <Card className="space-y-4 p-6">
          <h2 className="text-xl font-semibold">{t('paper.tabLeaveCancelledTitle')}</h2>
          <p role="alert" className="text-sub">
            {t('paper.tabLeaveCancelledBody', {
              count: data.tab_leave_count ?? 0,
              limit: 3,
            })}
          </p>
          <p className="text-3xl font-bold tabular-nums">
            {Number(data.score?.percentage ?? 0).toFixed(2)}%
          </p>
          <p className="text-sm text-mute">{t('paper.tabLeaveCancelledReason')}</p>
          <Link className="underline" to="/history">
            {t('nav.history')}
          </Link>
        </Card>
      ) : !error &&
        expired &&
        ['awaiting_approval', 'provisional', 'updating'].includes(data?.status) ? (
        <Card className="space-y-4 p-6">
          <h2 className="text-xl font-semibold">{t('ui.evaluation.processingTitle')}</h2>
          <p className="text-sub">{t('ui.evaluation.processingBody')}</p>
          <div className="flex flex-wrap gap-3">
            <button className={btnGhost} onClick={() => setReload((value) => value + 1)}>
              {t('ui.evaluation.checkAgain')}
            </button>
            <Link className="self-center underline" to="/history">
              {t('ui.evaluation.history')}
            </Link>
          </div>
        </Card>
      ) : data?.status === 'awaiting_approval' ? (
        <Card className="space-y-4 p-6">
          <h2 className="text-xl font-semibold">{t('ui.evaluation.awaitingTitle')}</h2>
          <p className="text-sub">{t('ui.evaluation.awaitingBody')}</p>
          <button className={btnGhost} onClick={() => setReload((value) => value + 1)}>
            {t('ui.evaluation.checkUpdates')}
          </button>
          <Link className="ml-3 underline" to="/history">
            {t('ui.evaluation.history')}
          </Link>
        </Card>
      ) : data?.status === 'updating' ? (
        <Card className="space-y-4 p-6">
          <h2 className="text-xl font-semibold">{t('ui.evaluation.updatingTitle')}</h2>
          <p className="text-sub">{t('ui.evaluation.updatingBody')}</p>
          <div className="flex flex-wrap gap-3">
            <button className={btnGhost} onClick={() => setReload((value) => value + 1)}>
              {t('ui.evaluation.checkUpdates')}
            </button>
            <Link className="self-center underline" to="/history">
              {t('ui.evaluation.history')}
            </Link>
          </div>
        </Card>
      ) : waiting ? (
        <Card className="space-y-4 p-6">
          <div role="status" className="flex items-center gap-3">
            {!expired && !error && <ActionSpinner />}
            <p>
              {expired || error ? t('ui.evaluation.waitingLong') : t('ui.evaluation.waitingAI')}
            </p>
          </div>
          <button type="button" disabled={busy} onClick={retry} className={btnGhost}>
            {busy ? t('ui.evaluation.loading') : t('common.retry')}
          </button>
          <Link to="/history" className="ml-3 underline">
            {t('ui.evaluation.history')}
          </Link>
        </Card>
      ) : adaptive ? (
        <AdaptiveResult session={sessionResult} data={data} />
      ) : (
        <EvaluationContent data={data} overall={overall} />
      )}
      {!overall &&
        String(sessionResult?.session_id) === sessionId &&
        sessionResult.runner_mode === 'fixed' &&
        sessionResult.purpose === 'TEST' &&
        sessionResult.review_status &&
        sessionResult.review_status !== 'LEGACY' &&
        isOfficialResult(data) && (
          <ReviewRequestCard
            key={sessionId}
            session={sessionResult}
            resultVersion={data.result_version}
            onOfficial={refreshOfficialResult}
          />
        )}
    </div>
  )
}
