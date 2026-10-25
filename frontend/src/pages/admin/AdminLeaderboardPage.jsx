import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import api, { apiMessage } from '../../api'
import { t, useLocale } from '../../i18n'
import { AdminPageHeader } from '../../components/admin'
import LearnerLeaderboard from '../../components/LearnerLeaderboard'
import { ErrorState, Loading } from '../../components/States'
import { btnGhost } from '../../components/ui'

export default function AdminLeaderboardPage() {
  useLocale()
  const [params] = useSearchParams()
  const assessmentId = params.get('assessment_id') || ''
  const [rows, setRows] = useState(null)
  const [error, setError] = useState('')
  const [retry, setRetry] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    setRows(null)
    setError('')
    api.get('/admin/analytics/cohort', { params: assessmentId ? { assessment_id: Number(assessmentId) } : {}, signal: controller.signal })
      .then(response => { if (!controller.signal.aborted) setRows(response.data.leaderboard || []) })
      .catch(err => { if (!controller.signal.aborted) setError(apiMessage(err)) })
    return () => controller.abort()
  }, [assessmentId, retry])
  return <div className="space-y-5">
    <AdminPageHeader title={t('admin.analytics.rankingTitle')} subtitle={t('admin.analytics.rankingHelp')}>
      <Link className={btnGhost} to="/admin">{t('admin.analytics.rankingBack')}</Link>
    </AdminPageHeader>
    {error ? <ErrorState message={error} onRetry={() => setRetry(value => value + 1)} /> : rows === null ? <Loading /> : <LearnerLeaderboard key={assessmentId} rows={rows} full />}
  </div>
}
