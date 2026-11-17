import AdaptiveOutcome from './AdaptiveOutcome'
import { Card } from './ui'
import { number, t, useLocale } from '../i18n'

// Adaptive sessions return an estimated ability, never a percentage score.
// This panel deliberately renders no "%" and no earned/possible score.
export default function AdaptiveResult({ session, data }) {
  useLocale()
  const estimate = session?.ability_estimate
  const suggestions = session?.study_suggestions || []
  return (
    <div className="space-y-5">
      {data?.provisional && (
        <p role="status" className="rounded-xl border border-amber-500 p-4 text-sm text-sub">
          {t('assessmentStyle.adaptive.provisional')}
        </p>
      )}
      {data?.approved && (
        <p role="status" className="rounded-xl border border-emerald-500 p-4 text-sm text-sub">
          {t('assessmentStyle.adaptive.approved')}
        </p>
      )}
      <Card className="p-5">
        <p className="text-sm font-semibold uppercase tracking-wide text-cyan-300">
          {t('assessmentStyle.adaptive.resultLabel')}
        </p>
        {estimate ? (
          <>
            <p
              aria-label={t('assessmentStyle.adaptive.index')}
              className="mt-2 text-3xl font-bold tabular-nums"
            >
              {number(estimate.index, { minimumFractionDigits: 1, maximumFractionDigits: 2 })}
              <span className="ml-1 text-lg font-normal text-sub">/ 5</span>
            </p>
            <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
              <div>
                <dt className="text-mute">{t('assessmentStyle.adaptive.band')}</dt>
                <dd className="font-medium text-ink">
                  {t(`assessmentStyle.adaptive.bandValues.${estimate.band}`)}
                </dd>
              </div>
              <div>
                <dt className="text-mute">{t('assessmentStyle.adaptive.confidence')}</dt>
                <dd className="font-medium text-ink">
                  {t(`assessmentStyle.adaptive.confidenceValues.${estimate.confidence}`)}
                </dd>
              </div>
              <div>
                <dt className="text-mute">{t('assessmentStyle.adaptive.evidence')}</dt>
                <dd className="font-medium text-ink">{number(estimate.evidence_count)}</dd>
              </div>
            </dl>
            {estimate.provisional && (
              <p className="mt-3 text-sm text-sub">{t('assessmentStyle.adaptive.estimateNote')}</p>
            )}
          </>
        ) : (
          <p className="mt-3 text-sub">{t('assessmentStyle.adaptive.pendingEstimate')}</p>
        )}
        <p role="note" className="mt-4 rounded-lg border border-edge p-3 text-sm text-sub">
          {t('assessmentStyle.adaptive.notOfficial')}
        </p>
      </Card>
      <AdaptiveOutcome progress={session?.adaptive_progress} />
      <Card className="p-5">
        <h2 className="text-lg font-semibold">{t('assessmentStyle.adaptive.suggestionsTitle')}</h2>
        {suggestions.length ? (
          <ul className="mt-3 list-disc space-y-2 pl-5 text-sub">
            {suggestions.map((suggestion) => (
              <li key={suggestion.concept_id}>
                <span className="font-medium text-ink">{suggestion.concept_name}</span>
                {suggestion.reason === 'below_target' && (
                  <span> — {t('assessmentStyle.adaptive.suggestionReason')}</span>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-2 text-sub">{t('assessmentStyle.adaptive.suggestionsEmpty')}</p>
        )}
      </Card>
    </div>
  )
}
