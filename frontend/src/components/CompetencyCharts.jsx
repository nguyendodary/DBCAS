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

const CHART_FALLBACKS = [
  '#60a5fa', '#fb923c', '#4ade80', '#c084fc', '#facc15',
  '#ef4444', '#22d3ee', '#2dd4bf', '#e879f9', '#a3e635',
]

function useChartTheme() {
  const { resolvedTheme } = useTheme()
  return useMemo(() => {
    const colors = CHART_FALLBACKS.map((fallback, index) => themeColor(`--chart-${index + 1}`, fallback))
    const primary = colors[0]
    const target = themeColor('--chart-target', '#fb7185')
    const grid = themeColor('--chart-grid', 'rgba(161, 161, 170, 0.2)')
    const label = themeColor('--chart-label', '#d4d4d8')
    const muted = themeColor('--chart-muted', '#a1a1aa')
    const tooltip = themeColor('--chart-tooltip', '#18191b')
    const tooltipText = themeColor('--chart-tooltip-text', '#fafafa')
    return {
      colors,
      barColors: colors.map((color) => withAlpha(color, 0.86)),
      barHoverColors: colors,
      primary,
      primaryFill: withAlpha(primary, 0.18),
      primaryLineFill: withAlpha(primary, 0.1),
      target,
      targetFill: withAlpha(target, 0.08),
      targetBar: withAlpha(target, 0.76),
      targetBarHover: target,
      grid,
      label,
      muted,
      tooltip,
      tooltipText,
      tooltipOptions: {
        backgroundColor: tooltip,
        titleColor: tooltipText,
        bodyColor: tooltipText,
        borderColor: grid,
        borderWidth: 1,
        padding: 12,
        cornerRadius: 8,
        displayColors: true,
        titleFont: { weight: '600' },
        bodyFont: { weight: '500' },
      },
      radarScale: {
        min: 0, max: 100,
        ticks: { stepSize: 20, color: muted, backdropColor: 'transparent' },
        grid: { color: grid }, angleLines: { color: grid }, pointLabels: { color: label },
        border: { color: grid },
      },
      yScale: { min: 0, max: 100, ticks: { stepSize: 20, color: muted, padding: 8 }, grid: { color: grid }, border: { color: grid } },
      xScale: { ticks: { color: label, padding: 8 }, grid: { display: false }, border: { color: grid } },
      legend: { position: 'bottom', labels: { color: label, usePointStyle: true, pointStyle: 'circle', boxWidth: 8, boxHeight: 8, padding: 18 } },
    }
  }, [resolvedTheme])
}

function chartOptions(palette, scales) {
  return {
    locale: intlLocale(),
    responsive: true,
    maintainAspectRatio: false,
    animation: ANIMATION,
    hover: { mode: 'nearest', intersect: true },
    interaction: { mode: 'nearest', intersect: false },
    scales,
    plugins: { legend: palette.legend, tooltip: palette.tooltipOptions },
  }
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
        pointBorderColor: palette.tooltip,
        pointRadius: 3,
        pointHoverRadius: 6,
        pointHitRadius: 10,
      },
      {
        label: t('charts.target'),
        data: concepts.map((c) => (c.target_pct == null ? null : Number(c.target_pct))),
        backgroundColor: palette.targetFill,
        borderColor: palette.target,
        borderDash: [6, 4],
        borderWidth: 2,
        pointRadius: 0,
      },
    ],
  }
  return (
    <Radar
      role="img" aria-label={t('charts.conceptDescription')} tabIndex={0} className="chart-canvas"
      data={data}
      options={chartOptions(palette, { r: palette.radarScale })}
    />
  )
}

// A radar collapses to a line with fewer than three concepts. Keep those
// early learner profiles legible with a horizontal comparison instead.
export function CompetencyConceptBars({ concepts }) {
  useLocale()
  const palette = useChartTheme()
  return <Bar
    role="img" aria-label={t('charts.conceptDescription')} tabIndex={0} className="chart-canvas"
    data={{
      labels: concepts.map((c) => c.concept_name),
      datasets: [
        {
          label: t('charts.competency'),
          data: concepts.map((c) => Number(c.competency_pct)),
          backgroundColor: concepts.map((_, index) => palette.barColors[index % palette.barColors.length]),
          hoverBackgroundColor: concepts.map((_, index) => palette.barHoverColors[index % palette.barHoverColors.length]),
          borderRadius: 6,
          borderSkipped: false,
        },
        {
          label: t('charts.target'),
          data: concepts.map((c) => c.target_pct == null ? null : Number(c.target_pct)),
          backgroundColor: palette.targetBar,
          hoverBackgroundColor: palette.targetBarHover,
          borderRadius: 6,
          borderSkipped: false,
        },
      ],
    }}
    options={{ ...chartOptions(palette, { x: palette.yScale, y: palette.xScale }), indexAxis: 'y' }}
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
        backgroundColor: categories.map((_, index) => palette.barColors[index % palette.barColors.length]),
        hoverBackgroundColor: categories.map((_, index) => palette.barHoverColors[index % palette.barHoverColors.length]),
        borderRadius: 6,
        borderSkipped: false,
      },
      {
        label: t('charts.meanTarget'),
        data: categories.map((c) => c.mean_target_pct == null ? null : Number(c.mean_target_pct)),
        backgroundColor: palette.targetBar,
        hoverBackgroundColor: palette.targetBarHover,
        borderRadius: 6,
        borderSkipped: false,
      },
    ],
  }
  return (
    <Bar
      role="img" aria-label={t('charts.areaDescription')} tabIndex={0} className="chart-canvas"
      data={data}
      options={chartOptions(palette, { x: palette.xScale, y: palette.yScale })}
    />
  )
}

export function ResultTrend({ points = [] }) {
  useLocale()
  const palette = useChartTheme()
  return <Line role="img" aria-label={t('charts.trendDescription')} tabIndex={0} className="chart-canvas" data={{ labels: points.map((p) => dateOnly(p.date)), datasets: [{
    label: t('charts.meanResult'), data: points.map((p) => p.mean_result_pct == null ? null : Number(p.mean_result_pct)),
    borderColor: palette.primary, backgroundColor: palette.primaryLineFill, tension: 0.15,
    borderWidth: 2.5, pointBackgroundColor: palette.primary, pointBorderColor: palette.tooltip,
    pointRadius: 3, pointHoverRadius: 6, pointHitRadius: 10,
  }] }} options={chartOptions(palette, { x: palette.xScale, y: palette.yScale })} />
}
