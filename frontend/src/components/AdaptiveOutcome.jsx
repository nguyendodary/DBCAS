import { t } from '../i18n'

export default function AdaptiveOutcome({ progress }) {
  if (!progress?.stop_reason) return null
  return <div className="rounded-lg border border-edge p-3 text-sm text-sub" role="status">
    <p>{t(`supervisor.adaptiveStop.${progress.stop_reason}`)}</p>
    <p>{t(progress.evidence_sufficient ? 'supervisor.adaptiveEvidenceMet' : 'supervisor.adaptiveEvidenceLow')}</p>
    {progress.inventory_limited && <p>{t('supervisor.adaptiveLimited')}</p>}
  </div>
}
