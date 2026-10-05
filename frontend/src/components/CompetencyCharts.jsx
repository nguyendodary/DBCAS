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

const SCALE = { min: 0, max: 100, ticks: { stepSize: 20 } }

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
        backgroundColor: 'rgba(37, 99, 235, 0.25)',
        borderColor: 'rgba(37, 99, 235, 1)',
        borderWidth: 2,
        pointBackgroundColor: 'rgba(37, 99, 235, 1)',
      },
      {
        label: 'Target %',
        data: concepts.map((c) => (c.target_pct == null ? null : Number(c.target_pct))),
        backgroundColor: 'rgba(220, 38, 38, 0.05)',
        borderColor: 'rgba(220, 38, 38, 0.8)',
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
        scales: { r: SCALE },
        plugins: { legend: { position: 'bottom' } },
      }}
    />
  )
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
        backgroundColor: 'rgba(37, 99, 235, 0.7)',
      },
      {
        label: 'Target %',
        data: areas.map((a) => avg(a, 'target_pct')),
        backgroundColor: 'rgba(220, 38, 38, 0.55)',
      },
    ],
  }
  return (
    <Bar
      data={data}
      options={{
        responsive: true,
        maintainAspectRatio: false,
        scales: { y: SCALE },
        plugins: { legend: { position: 'bottom' } },
      }}
    />
  )
}
