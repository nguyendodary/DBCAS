import { Link } from 'react-router-dom'
import { t, useLocale } from '../i18n'
import { Icon } from '../components/ui'
import StudentLeaderboard from '../components/StudentLeaderboard'

export default function LearnerLeaderboardPage() {
  useLocale()
  return <div className="content-wrap space-y-5 py-6">
    <div className="flex flex-wrap items-center justify-between gap-3"><h1 className="text-2xl font-semibold text-ink">{t('admin.analytics.rankingTitle')}</h1><Link to="/dashboard" className="inline-flex items-center gap-2 text-sm text-accent"><Icon name="arrowLeft" className="h-3.5 w-3.5" />{t('nav.dashboard')}</Link></div>
    <StudentLeaderboard full />
  </div>
}
