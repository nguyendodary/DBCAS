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
          <ul className="divide-y">
          {items.map((s) => (
            <li key={s.session_id} className="flex items-center justify-between p-4">
              <div>
                <p className="font-medium text-gray-900">{s.assessment_title}</p>
                <p className="mt-0.5 text-xs text-gray-500">
                  {new Date(s.started_at).toLocaleString()} ·{' '}
                  {s.answered_count}/{s.served_count} answered
                </p>
              </div>
              <div className="flex items-center gap-3">
                <StatusBadge status={s.status} />
                {s.status === 'in_progress' ? (
                  <Link
                    to={`/exam/${s.session_id}`}
                    className="text-sm font-medium text-blue-600 hover:underline"
                  >
                    Resume
                  </Link>
                ) : (
                  <Link
                    to={`/history/${s.session_id}`}
                    className="text-sm font-medium text-blue-600 hover:underline"
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
