import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api, { apiMessage } from '../api'
import { EmptyState, ErrorState, Loading } from '../components/States'
import { Badge, Card, Icon, PageHeader, StatusBadge, TypeBadge } from '../components/ui'

// UC18 — the evidence record of one finalized session.
// Layout borrows the prototypes' review page: summary chips up top and
// per-question cards tinted by outcome with checkmark option rows.
export default function EvidencePage() {
  const { sessionId } = useParams()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  const load = useCallback(() => {
    setError(null)
    api
      .get(`/sessions/${sessionId}/evidence`)
      .then((r) => setData(r.data))
      .catch((e) => setError(apiMessage(e, 'Could not load the evidence record')))
  }, [sessionId])

  useEffect(load, [load])

  if (error) return <ErrorState message={error} onRetry={load} />
  if (!data) return <Loading label="Loading evidence…" />

  const graded = data.items.filter((i) => i.score !== null)
  const earned = graded.reduce((acc, i) => acc + Number(i.score), 0)
  const possible = data.items.reduce((acc, i) => acc + Number(i.points), 0)
  const full = graded.filter((i) => Number(i.score) >= Number(i.points)).length
  const ungraded = data.items.length - graded.length
  const pct = possible > 0 ? Math.round((earned / possible) * 100) : 0

  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <PageHeader title="Assessment evidence" subtitle={`Session #${data.session_id} · Question-by-question grading record`}>
        <StatusBadge status={data.status} />
      </PageHeader>

      <div className="grid gap-3 sm:grid-cols-3">
        <SummaryChip label="Score" value={`${earned} / ${possible} pts`} accent="text-cyan-300" />
        <SummaryChip
          label="Percentage"
          value={`${pct}%`}
          accent={pct >= 70 ? 'text-emerald-300' : pct >= 40 ? 'text-amber-300' : 'text-rose-300'}
        />
        <SummaryChip
          label="Questions"
          value={`${full} full marks · ${graded.length - full} partial/missed${ungraded ? ` · ${ungraded} not graded` : ''}`}
        />
      </div>

      {data.items.length === 0 ? (
        <EmptyState title="No questions were served in this session" />
      ) : (
        <ol className="space-y-3">
          {data.items.map((item) => (
            <AttemptCard key={item.attempt_id} item={item} />
          ))}
        </ol>
      )}
      <p className="text-sm">
        <Link to="/history" className="text-cyan-300 hover:underline">
          ← Back to history
        </Link>
      </p>
    </div>
  )
}

function SummaryChip({ label, value, accent = 'text-ink' }) {
  return (
    <Card className="p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-mute">{label}</p>
      <p className={`mt-1 text-xl font-semibold ${accent}`}>{value}</p>
    </Card>
  )
}

function outcome(item) {
  if (item.score === null) return 'ungraded'
  if (Number(item.score) >= Number(item.points)) return 'correct'
  if (Number(item.score) > 0) return 'partial'
  return 'wrong'
}

function AttemptCard({ item }) {
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
        <span className="text-sm font-semibold text-ink">Q{item.seq_no}</span>
        <TypeBadge type={item.question_type} />
        <Badge>difficulty {item.difficulty_level}</Badge>
        {item.concepts.map((c) => (
          <Badge key={c.concept_id} tone="blue">
            {c.concept_name}
          </Badge>
        ))}
        <span className={`ml-auto flex items-center gap-1 text-sm font-semibold ${scoreCls}`}>
          {o !== 'ungraded' && <Icon name={o === 'correct' ? 'check' : o === 'partial' ? 'info' : 'x'} className="h-4 w-4" />}
          {item.score === null ? 'not graded' : `${item.score} / ${item.points} pts`}
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
          served {new Date(item.served_at).toLocaleTimeString()}
          {item.submitted_at &&
            ` · answered ${new Date(item.submitted_at).toLocaleTimeString()}`}
        </p>
      </div>
    </li>
  )
}

function McqReview({ item }) {
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
                {isChosen && ' (your answer)'}
              </span>
              {o.is_correct && <Icon name="check" className="mt-0.5 h-4 w-4 shrink-0 text-emerald-300" />}
              {isChosen && !o.is_correct && <Icon name="x" className="mt-0.5 h-4 w-4 shrink-0 text-rose-300" />}
            </li>
          )
        })}
      </ul>
      {!chosen && <p className="mt-2 text-sm italic text-mute">No answer submitted.</p>}
    </>
  )
}

function SqlReview({ item }) {
  return item.sql_answer ? (
    <div>
      <p className="text-xs font-medium text-mute">Your answer</p>
      <pre className="mt-1 overflow-x-auto rounded-lg border border-edge bg-abyss p-4 font-mono text-xs leading-5 text-ink">
        {item.sql_answer}
      </pre>
    </div>
  ) : (
    <p className="text-sm italic text-mute">— no answer submitted —</p>
  )
}

function EssayReview({ item }) {
  return (
    <div className="rounded-lg border border-edge bg-panel p-3">
      <p className="text-xs font-medium text-mute">Your answer</p>
      <p className="mt-1 whitespace-pre-wrap text-sm text-ink">
        {item.essay_answer || '— no answer submitted —'}
      </p>
    </div>
  )
}

// Renders whatever evidence the grader recorded — rubric criteria for
// essays, dataset checks for SQL, the answer key for MCQ. All fields come
// straight from attempt.grading_detail; absent fields are skipped.
function GradingDetail({ item }) {
  const d = item.grading_detail
  if (!d || typeof d !== 'object') return null
  const rows = []
  if (d.feedback) rows.push({ label: 'Feedback', value: d.feedback })
  if (d.explanation && d.explanation !== d.feedback)
    rows.push({ label: 'Explanation', value: d.explanation })
  if (d.rubric_level) rows.push({ label: 'Rubric level', value: d.rubric_level })
  if (Array.isArray(d.matched_criteria) && d.matched_criteria.length)
    rows.push({ label: 'Criteria met', value: d.matched_criteria.join(' · ') })
  if (Array.isArray(d.missing_concepts) && d.missing_concepts.length)
    rows.push({ label: 'Missing concepts', value: d.missing_concepts.join(' · ') })
  if (d.datasets_total !== undefined)
    rows.push({ label: 'Dataset checks', value: `${d.datasets_passed ?? 0} / ${d.datasets_total} passed` })
  if (Array.isArray(d.missing_required_concepts) && d.missing_required_concepts.length)
    rows.push({ label: 'Missing SQL concepts', value: d.missing_required_concepts.join(' · ') })
  if (Array.isArray(d.unverified_required_concepts) && d.unverified_required_concepts.length)
    rows.push({ label: 'Unverified SQL concepts', value: d.unverified_required_concepts.join(' · ') })
  if (rows.length === 0) return null
  return (
    <div className="mt-4 rounded-lg border border-edge bg-elev/40 p-4 text-xs text-sub">
      <p className="mb-1.5 flex items-center gap-1 font-semibold text-ink">
        <Icon name="info" className="h-3.5 w-3.5" /> Grading detail
      </p>
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
