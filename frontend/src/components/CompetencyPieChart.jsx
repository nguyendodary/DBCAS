import { t, percent } from '../i18n'
import { useState } from 'react'

const COLORS = ['#a78bfa', '#20c9df', '#2dce9e', '#f5b66f', '#ed83b5', '#7aabf5', '#d8c669', '#64c5b1', '#f18080', '#b2a2df', '#90bc65', '#df90c7', '#5cabe0', '#cba172', '#7cd9c6', '#ce9ce8', '#e3ba4f', '#8c9de8', '#d17e98', '#87c6aa']

export default function CompetencyPieChart({ concepts }) {
  const [activeId, setActiveId] = useState(null)
  if (!concepts.length) return null
  const values = concepts.map(concept => Math.max(0, Number(concept.competency_pct) || 0))
  const total = values.reduce((sum, value) => sum + value, 0)
  const activeConcept = concepts.find(concept => concept.concept_id === activeId)
  let start = -Math.PI / 2
  return <div className="reference-analysis">
    <div className="reference-analysis-visual">
      <div className="reference-analysis-pie" role="img" aria-label={concepts.map(concept => `${concept.concept_name}: ${percent(concept.competency_pct)}`).join('; ')}>
        <svg viewBox="0 0 240 240" onMouseLeave={() => setActiveId(null)}>
          {!total && <circle cx="120" cy="120" r="100" fill="var(--border)" />}
          {concepts.map((concept, index) => {
            if (!values[index] || !total) return null
            const angle = values[index] / total * Math.PI * 2
            const end = start + angle
            const middle = start + angle / 2
            const path = `M120 120 L${120 + 100 * Math.cos(start)} ${120 + 100 * Math.sin(start)} A100 100 0 ${angle > Math.PI ? 1 : 0} 1 ${120 + 100 * Math.cos(end)} ${120 + 100 * Math.sin(end)} Z`
            start = end
            const active = activeId === concept.concept_id
            const props = {
              className: `reference-slice${active ? ' is-active' : ''}`,
              fill: COLORS[index % COLORS.length],
              style: {
                transform: active && values[index] !== total ? `translate(${Math.cos(middle) * 10}px, ${Math.sin(middle) * 10}px)` : 'translate(0px, 0px)',
                opacity: activeId != null && !active ? .3 : 1,
              },
              onMouseEnter: () => setActiveId(concept.concept_id),
              onClick: () => setActiveId(current => current === concept.concept_id ? null : concept.concept_id),
            }
            const title = `${concept.concept_name}: ${percent(concept.competency_pct)}`
            return <g key={concept.concept_id} {...props}>
              <title>{title}</title>
              {values[index] === total ? <circle cx="120" cy="120" r="100" /> : <path d={path} />}
            </g>
          })}
        </svg>
        <div className="reference-active-value" aria-live="polite">{activeConcept && <><span>{activeConcept.concept_name}</span><strong>{percent(activeConcept.competency_pct)}</strong></>}</div>
      </div>
      <ul className="reference-analysis-legend reference-concept-legend">
        {concepts.map((concept, index) => <li key={concept.concept_id}>
          <button type="button" className="reference-concept-choice" aria-pressed={activeId === concept.concept_id}
            onMouseEnter={() => setActiveId(concept.concept_id)} onMouseLeave={() => setActiveId(null)}
            onFocus={() => setActiveId(concept.concept_id)} onBlur={() => setActiveId(null)}
            onClick={() => setActiveId(concept.concept_id)}>
          <span className="reference-legend-dot" style={{ background: COLORS[index % COLORS.length] }} />
          <div><span>{concept.concept_name}</span><small>{concept.target_pct == null ? t('overviewDonut.unbenchmarked') : t('overviewDonut.target', { value: percent(concept.target_pct) })}</small></div>
          <strong>{percent(concept.competency_pct)}</strong>
          </button>
        </li>)}
      </ul>
    </div>
    <p className="reference-analysis-description">{t('overviewDonut.conceptSlicesNote')}</p>
  </div>
}
