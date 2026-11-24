import {
  Chart as ChartJS,
  BarElement,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
} from 'chart.js'
import { Bar, Line } from 'react-chartjs-2'
import { Card } from './ui'
import { useChartTheme } from './CompetencyCharts'
import { t, useLocale } from '../i18n'
ChartJS.register(BarElement, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend)

export function EvaluationCharts({ dimensions = {}, history = [] }) {
  useLocale()
  const theme = useChartTheme()
  const baseOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      legend: { display: false },
      tooltip: { callbacks: { label: (context) => `${context.parsed.y.toFixed(2)}%` } },
    },
    scales: {
      x: {
        ticks: { maxRotation: 30 },
        title: { display: true, text: t('ui.charts.group') },
      },
      y: {
        min: 0,
        max: 100,
        ticks: { callback: (value) => `${value}%` },
        title: { display: true, text: t('ui.charts.scoreRate') },
      },
    },
  }
  const options = {
    ...baseOptions,
    plugins: {
      ...baseOptions.plugins,
      tooltip: { ...theme.tooltipOptions, ...baseOptions.plugins.tooltip },
    },
    scales: {
      x: { ...theme.xScale, title: { ...baseOptions.scales.x.title, color: theme.label } },
      y: {
        ...theme.yScale,
        title: { ...baseOptions.scales.y.title, color: theme.label },
        ticks: { ...theme.yScale.ticks, callback: (value) => `${value}%` },
      },
    },
  }
  return (
    <div className="space-y-5">
      {history.length >= 2 && (
        <Card className="min-w-0 p-5">
          <h2 className="mb-4 text-lg font-semibold">{t('ui.charts.trendTitle')}</h2>
          <div className="relative h-60">
            <Line
              className="chart-canvas"
              role="img"
              aria-label={t('ui.charts.trendAria')}
              options={{
                ...options,
                scales: {
                  ...options.scales,
                  x: {
                    ...options.scales.x,
                    title: {
                      display: true,
                      text: t('ui.charts.trendAxis'),
                      color: theme.label,
                    },
                  },
                },
              }}
              data={{
                labels: history.map((item, i) =>
                  t('ui.charts.attempt', { n: item.ordinal || i + 1 }),
                ),
                datasets: [
                  {
                    label: t('ui.charts.score'),
                    data: history.map((item) => item.percentage),
                    borderColor: theme.primary,
                    backgroundColor: theme.primary,
                    pointStyle: 'rectRot',
                    pointRadius: 5,
                  },
                ],
              }}
            />
          </div>
          <p className="mt-3 text-sm text-sub">
            {history
              .map(
                (item, i) =>
                  `${t('ui.charts.attempt', { n: item.ordinal || i + 1 })}: ${Number(item.percentage).toFixed(2)}%`,
              )
              .join(' · ')}
          </p>
        </Card>
      )}
      {Object.entries({
        clo: t('ui.charts.clo'),
        topic: t('ui.charts.topic'),
        difficulty: t('ui.charts.difficulty'),
      }).map(([key, title]) => (
        <Card className="min-w-0 p-5" key={key}>
          <h2 className="mb-4 text-lg font-semibold">{title}</h2>
          {dimensions[key]?.length ? (
            <>
              <div className="relative h-60">
                <Bar
                  className="chart-canvas"
                  role="img"
                  aria-label={t('ui.charts.scaleAria', { title })}
                  options={options}
                  data={{
                    labels: dimensions[key].map((item) => item.label),
                    datasets: [
                      {
                        label: t('ui.charts.score'),
                        data: dimensions[key].map((item) => item.percentage),
                        backgroundColor: theme.primary,
                        borderColor: theme.primary,
                        borderWidth: 1,
                        borderRadius: 2,
                        maxBarThickness: 56,
                      },
                    ],
                  }}
                />
              </div>
              <ul className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-sm text-sub tabular-nums">
                {dimensions[key].map((item) => (
                  <li key={item.label}>
                    {item.label}: {Number(item.percentage).toFixed(2)}% ({item.earned}/
                    {item.possible} {t('ui.charts.points')})
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <p className="text-sm text-sub">{t('ui.charts.noEvidence')}</p>
          )}
        </Card>
      ))}
    </div>
  )
}
