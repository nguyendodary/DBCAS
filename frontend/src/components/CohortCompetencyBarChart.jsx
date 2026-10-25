import { useState } from 'react'
import { t, percent, number } from '../i18n'
import { Card, CardTitle, btnGhost } from './ui'
import { EmptyState } from './States'
import { Bar } from 'react-chartjs-2'
import { useChartTheme } from './CompetencyCharts'

export default function CohortCompetencyBarChart({ concepts = [] }) {
  const [page, setPage] = useState(0)
  const palette = useChartTheme()
  const pageCount = Math.ceil(concepts.length / 12)
  const currentPage = Math.min(page, Math.max(0, pageCount - 1))
  const visible = concepts.slice(currentPage * 12, currentPage * 12 + 12)
  return <Card className="min-w-0 overflow-hidden">
    <CardTitle title={t('admin.analytics.competencySummary')} />
    <div className="p-4 sm:p-5">
      <p className="mb-5 text-xs leading-relaxed text-mute">{t('admin.analytics.competencySummaryHelp')}</p>
      {!concepts.length ? <EmptyState title={t('admin.analytics.noConcepts')} /> : <>
        <div className="relative min-w-0" style={{ height: Math.max(230, visible.length * 42 + 40) }}>
          <Bar role="img" aria-label={t('admin.analytics.competencySummary')} data={{
            labels: visible.map(concept => concept.concept_name),
            datasets: [{
              label: t('admin.analytics.scoreScale'),
              data: visible.map(concept => Number(concept.avg_competency_pct)),
              backgroundColor: palette.barColors[0], hoverBackgroundColor: palette.primary,
              borderRadius: 5, borderSkipped: false, maxBarThickness: 20,
            }],
          }} options={{
            responsive: true, maintainAspectRatio: false, indexAxis: 'y',
            animation: false,
            scales: {
              x: { min: 0, max: 100, position: 'top', border: { display: false },
                ticks: { color: palette.muted, stepSize: 25, callback: value => `${number(value)}%` },
                grid: { color: palette.grid },
              },
              y: { border: { display: false }, grid: { display: false },
                ticks: { color: palette.label, font: { size: 11 }, autoSkip: false,
                  callback: (_, index) => {
                    const name = visible[index]?.concept_name || ''
                    return name.length > 23 ? `${name.slice(0, 22)}…` : name
                  },
                },
              },
            },
            plugins: {
              legend: { display: false },
              tooltip: { ...palette.tooltipOptions, displayColors: false, callbacks: {
                title: items => visible[items[0]?.dataIndex]?.concept_name || '',
                label: item => `${t('admin.analytics.scoreScale')}: ${percent(item.parsed.x, { maximumFractionDigits: 1 })}`,
                afterLabel: item => t('admin.analytics.assessedCount', { count: visible[item.dataIndex].learners_assessed }),
              } },
            },
          }} />
        </div>
        {pageCount > 1 && <nav className="mt-5 flex flex-wrap items-center justify-end gap-3" aria-label={t('admin.analytics.conceptPages')}>
          <button type="button" className={btnGhost} disabled={currentPage === 0} onClick={() => setPage(currentPage - 1)}>{t('assessment.prevPage')}</button>
          <span className="text-xs text-mute" aria-live="polite">{number(currentPage + 1)} / {number(pageCount)}</span>
          <button type="button" className={btnGhost} disabled={currentPage + 1 >= pageCount} onClick={() => setPage(currentPage + 1)}>{t('assessment.nextPage')}</button>
        </nav>}
      </>}
    </div>
  </Card>
}
