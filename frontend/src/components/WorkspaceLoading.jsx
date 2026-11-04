import { useEffect, useState } from 'react'
import { t, useLocale } from '../i18n'
import { ErrorState, Loading } from './States'

export default function WorkspaceLoading({ label, onRetry = () => window.location.reload() }) {
  useLocale()
  const [expired, setExpired] = useState(false)
  useEffect(() => {
    const timer = setTimeout(() => setExpired(true), 15000)
    return () => clearTimeout(timer)
  }, [])
  if (!expired) return <Loading label={label} />
  return (
    <div className="space-y-4 py-5">
      <h1 className="text-2xl font-bold text-ink">{t('common.workspaceTimeoutTitle')}</h1>
      <ErrorState message={t('errors.workspace_timeout')} onRetry={onRetry} />
    </div>
  )
}
