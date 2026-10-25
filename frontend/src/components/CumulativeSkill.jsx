import { t, number, percent } from '../i18n'
import { Badge, Icon } from './ui'

export default function CumulativeSkill({ concept: c }) {
  const hasTarget = c.target_pct != null
  const state = !hasTarget ? 'neutral' : c.below_target ? 'improve' : 'met'
  const status = !hasTarget ? 'common.noBenchmark' : c.below_target ? 'common.belowTarget' : 'common.onTarget'
  const gap = hasTarget ? Math.max(0, Number(c.target_pct) - Number(c.competency_pct)) : null
  const sessions = c.contributing_sessions || []
  return <details id={`cumulative-skill-${c.concept_id}`} className={`cumulative-skill ${state}`}>
    <summary>
      <div className="cumulative-skill-name"><h3>{c.concept_name}</h3>{c.subject_area && <span>{c.subject_area}</span>}</div>
      <div className="cumulative-skill-measure">
        <div><strong>{percent(c.competency_pct)}</strong><span>{hasTarget ? t('cumulativeView.target', { value: percent(c.target_pct) }) : t('common.noBenchmark')}</span></div>
        <div className="cumulative-track" aria-hidden="true"><span style={{ width: `${Math.max(0, Math.min(100, Number(c.competency_pct)))}%` }} />{hasTarget && <i style={{ left: `${Math.max(0, Math.min(100, Number(c.target_pct)))}%` }} />}</div>
      </div>
      <Badge tone={state === 'met' ? 'green' : state === 'improve' ? 'amber' : undefined}>{t(status)}</Badge>
      <Icon name="chevronDown" className="cumulative-detail-chevron h-4 w-4" />
    </summary>
    <div className="cumulative-skill-detail">
      <div className="cumulative-detail-grid cumulative-student-detail">
        <section><h4>{t('cumulativeView.interpretation')}</h4>
          <p>{!hasTarget ? t('cumulativeView.noTargetHelp') : c.below_target ? t('cumulativeView.gap', { value: number(gap, { maximumFractionDigits: 2 }) }) : t('cumulativeView.metHelp')}</p>
          {hasTarget && <><p>{t('supervisor.recurringCount', { count: c.below_target_assessments || 0 })}</p><p>{t('supervisor.recurringStrengthCount', { count: c.meeting_target_assessments || 0 })}</p></>}
        </section>
      </div>
      <div className="cumulative-next-step"><Icon name="book" className="h-4 w-4 shrink-0" /><p>{t(c.below_target ? 'cumulativeView.nextImprove' : hasTarget ? 'cumulativeView.nextMaintain' : 'cumulativeView.nextUnbenchmarked', { name: c.concept_name })}</p></div>
      {sessions.length === 1 && <p className="cumulative-limited">{t('cumulativeView.limitedSkill')}</p>}
    </div>
  </details>
}
