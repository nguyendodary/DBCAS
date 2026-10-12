import { t, useLocale, message, number, percent, dateTime, time, dateOnly, intlLocale } from '../i18n'
import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api, { apiMessage } from '../api'
import { EmptyState, ErrorState, Loading } from '../components/States'
import { Badge, Icon, PageHeader, StatusBadge, TypeBadge } from '../components/ui'

// UC18 — the evidence record of one finalized session.
// Per-question outcome cards render the immutable server grading record.
export default function EvidencePage() {
  useLocale()
  const { sessionId } = useParams()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  const load = useCallback(() => {
    setError(null)
    api
      .get(`/sessions/${sessionId}/evidence`)
      .then((r) => setData(r.data))
      .catch((e) => setError(apiMessage(e, message('evidence.loadError'))))
  }, [sessionId])

  useEffect(load, [load])

  if (error) return <ErrorState message={error} onRetry={load} />
  if (!data) return <Loading label={t('evidence.loading')} />

  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <PageHeader title={t('evidence.title')} subtitle={t('evidence.subtitle', { id: data.session_id })}>
        <StatusBadge status={data.status} />
      </PageHeader>

      {data.items.length === 0 ? (
        <EmptyState title={t('evidence.empty')} />
      ) : (
        <ol className="space-y-3">
          {data.items.map((item) => (
            <AttemptCard key={item.attempt_id} item={item} />
          ))}
        </ol>
      )}
      <p className="text-sm">
        <Link to="/history" className="text-cyan-300 hover:underline">{t('evidence.back')}</Link>
      </p>
    </div>
  )
}

function outcome(item) {
  if (item.score === null) return 'ungraded'
  if (Number(item.score) >= Number(item.points)) return 'correct'
  if (Number(item.score) > 0) return 'partial'
  return 'wrong'
}

function AttemptCard({ item }) {
  useLocale()
  const o = outcome(item)
  const tone = {
    correct: 'border-l-emerald-400',
    partial: 'border-l-amber-400',
    wrong: 'border-l-rose-400',
    ungraded: 'border-l-edge2',
  }[o]
  const scoreCls = {
    correct: 'text-emerald-300',
    partial: 'text-amber-300',
    wrong: 'text-rose-300',
    ungraded: 'text-mute',
  }[o]
  return (
    <li className={`overflow-hidden rounded-xl border border-edge border-l-2 bg-panel ${tone}`}>
      <div className="flex flex-wrap items-center gap-2 border-b border-edge/60 px-5 py-3 text-xs text-mute">
        <span className="text-sm font-semibold text-ink">{t('exam.questionNumber', { number: number(item.seq_no) })}</span>
        <TypeBadge type={item.question_type} />
        <Badge>{t('exam.difficulty', { value: number(item.difficulty_level) })}</Badge>
        {item.concepts.map((c) => (
          <Badge key={c.concept_id} tone="blue">
            {c.concept_name}
          </Badge>
        ))}
        <span className={`ml-auto flex items-center gap-1 text-sm font-semibold ${scoreCls}`}>
          {o !== 'ungraded' && <Icon name={o === 'correct' ? 'check' : o === 'partial' ? 'info' : 'x'} className="h-4 w-4" />}
          {item.score === null ? t('evidence.notGraded') : t('evidence.score', { score: number(item.score, { minimumFractionDigits: 2 }), points: number(item.points, { minimumFractionDigits: 2 }) })}
        </span>
      </div>
      <div className="px-5 py-4">
        <p className="whitespace-pre-wrap text-sm font-medium leading-relaxed text-ink">{item.prompt}</p>
        <div className="mt-3">
          {item.question_type === 'mcq' && <McqReview item={item} />}
          {item.question_type === 'sql' && <SqlReview item={item} />}
          {item.question_type === 'essay' && <EssayReview item={item} />}
        </div>
        <GradingDetail item={item} />
        <p className="mt-3 text-xs text-faint">
          {t('evidence.served', { time: time(item.served_at) })}
          {item.submitted_at &&
            t('evidence.answered', { time: time(item.submitted_at) })}
        </p>
      </div>
    </li>
  )
}

function McqReview({ item }) {
  useLocale()
  const chosen = item.options.find((o) => o.option_id === item.selected_option_id)
  return (
    <>
      <ul className="grid gap-2 sm:grid-cols-2">
        {item.options.map((o) => {
          const isChosen = o.option_id === item.selected_option_id
          const cls = o.is_correct
            ? 'border-emerald-500/50 bg-emerald-500/10 text-emerald-300'
            : isChosen
              ? 'border-rose-500/40 bg-rose-500/10 text-rose-300'
              : 'border-edge bg-panel text-sub'
          return (
            <li key={o.option_id} className={`flex items-start gap-2 rounded-lg border p-2.5 text-sm ${cls}`}>
              <span className="font-mono font-bold">{o.option_label}.</span>
              <span className="flex-1">
                {o.option_text}
                {isChosen && t('evidence.yourChoice')}
              </span>
              {o.is_correct && <Icon name="check" className="mt-0.5 h-4 w-4 shrink-0 text-emerald-300" />}
              {isChosen && !o.is_correct && <Icon name="x" className="mt-0.5 h-4 w-4 shrink-0 text-rose-300" />}
            </li>
          )
        })}
      </ul>
      {!chosen && <p className="mt-2 text-sm italic text-mute">{t('evidence.noAnswer')}</p>}
    </>
  )
}

function SqlReview({ item }) {
  useLocale()
  return item.sql_answer ? (
    <div>
      <p className="text-xs font-medium text-mute">{t('essay.answer')}</p>
      <pre tabIndex={0} role="region" aria-label={t('evidence.submittedAnswer')} className="mt-1 overflow-x-auto rounded-lg border border-edge bg-abyss p-4 font-mono text-xs leading-5 text-ink">
        {item.sql_answer}
      </pre>
    </div>
  ) : (
    <p className="text-sm italic text-mute">{t('evidence.noAnswerInline')}</p>
  )
}

function EssayReview({ item }) {
  useLocale()
  return (
    <div className="rounded-lg border border-edge bg-panel p-3">
      <p className="text-xs font-medium text-mute">{t('essay.answer')}</p>
      <p className="mt-1 whitespace-pre-wrap text-sm text-ink">
        {item.essay_answer || t('evidence.noAnswerInline')}
      </p>
    </div>
  )
}

// Renders whatever evidence the grader recorded — rubric criteria for
// essays, dataset checks for SQL, the answer key for MCQ. All fields come
// straight from attempt.grading_detail; absent fields are skipped.
function GradingDetail({ item }) {
  useLocale()
  const d = item.grading_detail
  if (!d || typeof d !== 'object') return null
  const rows = []
  if (d.feedback) rows.push({ label: t('evidence.feedback'), value: d.feedback })
  if (d.explanation && d.explanation !== d.feedback)
    rows.push({ label: t('evidence.explanation'), value: d.explanation })
  if (d.rubric_level) rows.push({ label: t('evidence.rubric'), value: d.rubric_level })
  if (Array.isArray(d.matched_criteria) && d.matched_criteria.length)
    rows.push({ label: t('evidence.criteria'), value: d.matched_criteria.join(' · ') })
  if (Array.isArray(d.missing_concepts) && d.missing_concepts.length)
    rows.push({ label: t('evidence.missingConcepts'), value: d.missing_concepts.join(' · ') })
  if (d.datasets_total !== undefined)
    rows.push({ label: t('evidence.datasets'), value: t('evidence.passedChecks', { passed: number(d.datasets_passed ?? 0), total: number(d.datasets_total) }) })
  if (Array.isArray(d.missing_required_concepts) && d.missing_required_concepts.length)
    rows.push({ label: t('evidence.missingSql'), value: d.missing_required_concepts.join(' · ') })
  if (Array.isArray(d.unverified_required_concepts) && d.unverified_required_concepts.length)
    rows.push({ label: t('evidence.unverifiedSql'), value: d.unverified_required_concepts.join(' · ') })
  if (rows.length === 0) return null
  return (
    <div className="mt-4 rounded-lg border border-edge bg-elev/40 p-4 text-xs text-sub">
      <p className="mb-1.5 flex items-center gap-1 font-semibold text-ink">
        <Icon name="info" className="h-3.5 w-3.5" />{t('evidence.detail')}</p>
      <dl className="space-y-1">
        {rows.map((r) => (
          <div key={r.label} className="flex flex-wrap gap-x-3 gap-y-0.5 sm:flex-nowrap">
            <dt className="w-32 shrink-0 font-medium text-mute">{r.label}</dt>
            <dd className="whitespace-pre-wrap">{r.value}</dd>
          </div>
        ))}
      </dl>
    </div>
  )
}
