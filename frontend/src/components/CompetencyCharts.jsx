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
import { Bar, Radar } from 'react-chartjs-2'

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

// Dark-theme chart chrome: faint gridlines, muted ticks, the cyan accent
// for measured values and rose for benchmark targets (index.css tokens).
const TICKS = { stepSize: 20, color: '#98a8be', backdropColor: 'transparent' }
const SCALE_RADAR = {
  min: 0,
  max: 100,
  ticks: TICKS,
  grid: { color: 'rgba(148, 163, 184, 0.15)' },
  angleLines: { color: 'rgba(148, 163, 184, 0.15)' },
  pointLabels: { color: '#b7c3d5' },
}
const SCALE_Y = {
  min: 0,
  max: 100,
  ticks: { stepSize: 20, color: '#98a8be' },
  grid: { color: 'rgba(148, 163, 184, 0.12)' },
}
const SCALE_X = { ticks: { color: '#b7c3d5' }, grid: { display: false } }
const LEGEND = { position: 'bottom', labels: { color: '#b7c3d5' } }
const ANIMATION = typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
  ? false : { duration: 240, easing: 'easeOutQuart' }

// FR-13 — radar of per-concept mastery against the administrator benchmark.
// Values come straight from the API: the backend is the source of truth and
// the chart never recalculates competency.
export function CompetencyRadar({ concepts }) {
  const data = {
    labels: concepts.map((c) => c.concept_name),
    datasets: [
      {
        label: 'Competency %',
        data: concepts.map((c) => Number(c.competency_pct)),
        backgroundColor: 'rgba(34, 211, 238, 0.18)',
        borderColor: 'rgba(34, 211, 238, 1)',
        borderWidth: 2,
        pointBackgroundColor: 'rgba(34, 211, 238, 1)',
      },
      {
        label: 'Target %',
        data: concepts.map((c) => (c.target_pct == null ? null : Number(c.target_pct))),
        backgroundColor: 'rgba(251, 113, 133, 0.05)',
        borderColor: 'rgba(251, 113, 133, 0.85)',
        borderDash: [6, 4],
        borderWidth: 2,
        pointRadius: 0,
      },
    ],
  }
  return (
    <Radar
      data={data}
      options={{
        responsive: true,
        maintainAspectRatio: false,
        animation: ANIMATION,
        scales: { r: SCALE_RADAR },
        plugins: { legend: LEGEND },
      }}
    />
  )
}

// A radar collapses to a line with fewer than three concepts. Keep those
// early learner profiles legible with a horizontal comparison instead.
export function CompetencyConceptBars({ concepts }) {
  return <Bar
    data={{
      labels: concepts.map((c) => c.concept_name),
      datasets: [
        { label: 'Competency %', data: concepts.map((c) => Number(c.competency_pct)), backgroundColor: 'rgba(34, 211, 238, 0.72)' },
        { label: 'Target %', data: concepts.map((c) => c.target_pct == null ? null : Number(c.target_pct)), backgroundColor: 'rgba(251, 113, 133, 0.55)' },
      ],
    }}
    options={{ responsive: true, maintainAspectRatio: false, indexAxis: 'y', animation: ANIMATION,
      scales: { x: SCALE_Y, y: SCALE_X }, plugins: { legend: LEGEND } }}
  />
}

// FR-13 — the same evidence aggregated into the documented subject-area
// competency categories for a second view.
export function CompetencyBar({ concepts }) {
  const areas = [...new Set(concepts.map((c) => c.subject_area))]
  const avg = (area, field) => {
    const rows = concepts.filter((c) => c.subject_area === area)
    const vals = rows
      .map((c) => (c[field] == null ? null : Number(c[field])))
      .filter((v) => v != null)
    return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0
  }
  const data = {
    labels: areas,
    datasets: [
      {
        label: 'Competency %',
        data: areas.map((a) => avg(a, 'competency_pct')),
        backgroundColor: 'rgba(34, 211, 238, 0.65)',
      },
      {
        label: 'Target %',
        data: areas.map((a) => avg(a, 'target_pct')),
        backgroundColor: 'rgba(251, 113, 133, 0.55)',
      },
    ],
  }
  return (
    <Bar
      data={data}
      options={{
        responsive: true,
        maintainAspectRatio: false,
        animation: ANIMATION,
        scales: { x: SCALE_X, y: SCALE_Y },
        plugins: { legend: LEGEND },
      }}
    />
  )
}
