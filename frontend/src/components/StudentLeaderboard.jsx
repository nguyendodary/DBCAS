import { useEffect, useState } from 'react'
import api, { apiMessage } from '../api'
import { useAuth } from '../auth'
import { t } from '../i18n'
import { Loading, ErrorState } from './States'
import LearnerLeaderboard from './LearnerLeaderboard'

export default function StudentLeaderboard({ full = false }) {
  const account = useAuth()?.account
  const [rows, setRows] = useState(null)
  const [error, setError] = useState(null)
  const [retry, setRetry] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    setError(null)
    api.get('/sessions/leaderboard', { signal: controller.signal })
      .then(r => { if (!controller.signal.aborted) setRows(r.data) })
      .catch(e => { if (!controller.signal.aborted) setError(apiMessage(e)) })
    return () => controller.abort()
  }, [retry])
  if (error) return <ErrorState message={error} onRetry={() => setRetry(n => n + 1)} />
  if (!rows) return <Loading label={t('admin.analytics.rankingTitle')} />
  return <LearnerLeaderboard rows={rows} full={full} studentView currentAccountId={account?.account_id} />
}
