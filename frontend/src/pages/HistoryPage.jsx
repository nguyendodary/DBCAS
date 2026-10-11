import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api, { apiMessage } from '../api'
import { EmptyState, ErrorState, Loading } from '../components/States'
import { Card, PageHeader, StatusBadge } from '../components/ui'

// UC18 — the learner's assessment history.
export default function HistoryPage() {
  const [items, setItems] = useState(null)
  const [error, setError] = useState(null)

  const load = useCallback(() => {
    setError(null)
    api
      .get('/sessions')
      .then((r) => setItems(r.data))
      .catch((e) => {
        setError(apiMessage(e, 'Could not load your history'))
        setItems([])
      })
  }, [])

  useEffect(load, [load])

  if (error) return <ErrorState message={error} onRetry={load} />
  if (items === null) return <Loading label="Loading history…" />

  return (
    <div className="space-y-4">
      <PageHeader title="Assessment history" />
      {items.length === 0 ? (
        <EmptyState title="No sessions yet">
          Start an assessment and your completed results will appear here.
        </EmptyState>
      ) : (
        <Card className="overflow-hidden">
          <ul className="divide-y divide-edge">
          {items.map((s) => (
            <li key={s.session_id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-4 transition-colors hover:bg-white/[0.035]">
              <div className="min-w-0">
                <p className="font-medium text-ink">{s.assessment_title}</p>
                <p className="mt-0.5 text-xs text-mute">
                  {new Date(s.submitted_at || s.started_at).toLocaleString()} ·{' '}
                  {s.answered_count}/{s.served_count} answered
                </p>
                {s.status !== 'in_progress' && <>
                  <p className="mt-2 text-sm text-sub">{s.pending_grading_count ? 'Grading pending' : s.failed_grading_count ? 'Grading requires retry' : s.overall_result_pct != null ? `Answer result: ${s.overall_result_pct}%` : 'No graded answers'}</p>
                  <ul aria-label="Per-concept results" className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-mute">
                    {(s.concepts || []).map((c) => <li key={c.concept_id}>{c.concept_name}: {c.competency_pct}%{c.target_pct == null ? ' · no benchmark' : c.below_target ? ' · below target' : ' · meets target'}</li>)}
                  </ul>
                </>}
              </div>
              <div className="flex items-center gap-3">
                <StatusBadge status={s.status} />
                {s.status === 'in_progress' ? (
                  <Link
                    to={`/exam/${s.session_id}`}
                    className="text-sm font-medium text-cyan-300 hover:underline"
                  >
                    Resume
                  </Link>
                ) : (
                  <Link
                    to={`/history/${s.session_id}`}
                    className="text-sm font-medium text-cyan-300 hover:underline"
                  >
                    Evidence
                  </Link>
                )}
              </div>
            </li>
          ))}
          </ul>
        </Card>
      )}
    </div>
  )
}
