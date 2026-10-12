import { t, useLocale, message, number, percent, dateTime, time, dateOnly, intlLocale } from '../i18n'
import { useMemo } from 'react'
import { useTheme } from './ThemeProvider'
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  RadialLinearScale,
  Tooltip,
} from 'chart.js'
import { Bar, Radar, Line } from 'react-chartjs-2'

ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement
)

const ANIMATION = typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
  ? false : { duration: 240, easing: 'easeOutQuart' }

function themeColor(name, fallback) {
  if (typeof document === 'undefined') return fallback
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback
}

function withAlpha(color, alpha) {
  const hex = color.match(/^#([\da-f]{3}|[\da-f]{6})$/i)?.[1]
  if (!hex) return color
  const full = hex.length === 3 ? [...hex].map((part) => part + part).join('') : hex
  const [r, g, b] = [0, 2, 4].map((offset) => Number.parseInt(full.slice(offset, offset + 2), 16))
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

function useChartTheme() {
  const { resolvedTheme } = useTheme()
  return useMemo(() => {
    const primary = themeColor('--chart-1', '#22d3ee')
    const target = themeColor('--chart-2', '#fb7185')
    const grid = themeColor('--chart-grid', 'rgba(148, 163, 184, 0.15)')
    const label = themeColor('--chart-label', '#b7c3d5')
    const muted = themeColor('--chart-muted', '#98a8be')
    const tooltip = themeColor('--chart-tooltip', '#0e1729')
    const tooltipText = themeColor('--chart-tooltip-text', '#e8eef8')
    return {
      primary,
      primaryFill: withAlpha(primary, 0.18),
      primaryBar: withAlpha(primary, 0.68),
      primaryLineFill: withAlpha(primary, 0.1),
      target,
      targetFill: withAlpha(target, 0.08),
      targetBar: withAlpha(target, 0.55),
      grid,
      label,
      muted,
      tooltip,
      tooltipText,
      tooltipOptions: { backgroundColor: tooltip, titleColor: tooltipText, bodyColor: tooltipText, borderColor: grid, borderWidth: 1 },
      radarScale: {
        min: 0, max: 100,
        ticks: { stepSize: 20, color: muted, backdropColor: 'transparent' },
        grid: { color: grid }, angleLines: { color: grid }, pointLabels: { color: label },
      },
      yScale: { min: 0, max: 100, ticks: { stepSize: 20, color: muted }, grid: { color: grid } },
      xScale: { ticks: { color: label }, grid: { display: false } },
      legend: { position: 'bottom', labels: { color: label } },
    }
  }, [resolvedTheme])
}

// FR-13 — radar of per-concept mastery against the administrator benchmark.
// Values come straight from the API: the backend is the source of truth and
// the chart never recalculates competency.
export function CompetencyRadar({ concepts }) {
  useLocale()
  const palette = useChartTheme()
  const data = {
    labels: concepts.map((c) => c.concept_name),
    datasets: [
      {
        label: t('charts.competency'),
        data: concepts.map((c) => Number(c.competency_pct)),
        backgroundColor: palette.primaryFill,
        borderColor: palette.primary,
        borderWidth: 2,
        pointBackgroundColor: palette.primary,
      },
      {
        label: t('charts.target'),
        data: concepts.map((c) => (c.target_pct == null ? null : Number(c.target_pct))),
        backgroundColor: palette.targetFill,
        borderColor: withAlpha(palette.target, 0.85),
        borderDash: [6, 4],
        borderWidth: 2,
        pointRadius: 0,
      },
    ],
  }
  return (
    <Radar
      role="img" aria-label={t('charts.conceptDescription')}
      data={data}
      options={{ locale: intlLocale(),
        responsive: true,
        maintainAspectRatio: false,
        animation: ANIMATION,
        scales: { r: palette.radarScale },
        plugins: { legend: palette.legend, tooltip: palette.tooltipOptions },
      }}
    />
  )
}

// A radar collapses to a line with fewer than three concepts. Keep those
// early learner profiles legible with a horizontal comparison instead.
export function CompetencyConceptBars({ concepts }) {
  useLocale()
  const palette = useChartTheme()
  return <Bar
    role="img" aria-label={t('charts.conceptDescription')}
    data={{
      labels: concepts.map((c) => c.concept_name),
      datasets: [
        { label: t('charts.competency'), data: concepts.map((c) => Number(c.competency_pct)), backgroundColor: palette.primaryBar },
        { label: t('charts.target'), data: concepts.map((c) => c.target_pct == null ? null : Number(c.target_pct)), backgroundColor: palette.targetBar },
      ],
    }}
    options={{ locale: intlLocale(), responsive: true, maintainAspectRatio: false, indexAxis: 'y', animation: ANIMATION,
      scales: { x: palette.yScale, y: palette.xScale }, plugins: { legend: palette.legend, tooltip: palette.tooltipOptions } }}
  />
}

// FR-13 — the same evidence aggregated into the documented subject-area
// competency categories for a second view.
export function CompetencyBar({ categories = [] }) {
  useLocale()
  const palette = useChartTheme()
  const data = {
    labels: categories.map((c) => c.subject_area),
    datasets: [
      {
        label: t('charts.meanConcept'),
        data: categories.map((c) => Number(c.mean_competency_pct)),
        backgroundColor: palette.primaryBar,
      },
      {
        label: t('charts.meanTarget'),
        data: categories.map((c) => c.mean_target_pct == null ? null : Number(c.mean_target_pct)),
        backgroundColor: palette.targetBar,
      },
    ],
  }
  return (
    <Bar
      role="img" aria-label={t('charts.areaDescription')}
      data={data}
      options={{ locale: intlLocale(),
        responsive: true,
        maintainAspectRatio: false,
        animation: ANIMATION,
        scales: { x: palette.xScale, y: palette.yScale },
        plugins: { legend: palette.legend, tooltip: palette.tooltipOptions },
      }}
    />
  )
}

export function ResultTrend({ points = [] }) {
  useLocale()
  const palette = useChartTheme()
  return <Line role="img" aria-label={t('charts.trendDescription')} data={{ labels: points.map((p) => dateOnly(p.date)), datasets: [{
    label: t('charts.meanResult'), data: points.map((p) => p.mean_result_pct == null ? null : Number(p.mean_result_pct)),
    borderColor: palette.primary, backgroundColor: palette.primaryLineFill, tension: 0.15,
  }] }} options={{ locale: intlLocale(), responsive: true, maintainAspectRatio: false, animation: ANIMATION,
    scales: { x: palette.xScale, y: palette.yScale }, plugins: { legend: palette.legend, tooltip: palette.tooltipOptions } }} />
}
