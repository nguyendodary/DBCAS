import { Chart as ChartJS, BarElement, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend } from 'chart.js'
import { Bar, Line } from 'react-chartjs-2'
import { Card } from './ui'
ChartJS.register(BarElement, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend)
const options = { responsive: true, maintainAspectRatio: false, animation: false,
  plugins: { legend: { display: false }, tooltip: { callbacks: { label: context => `${context.parsed.y.toFixed(2)}%` } } },
  scales: { x: { ticks: { color: '#94a3b8', maxRotation: 30 }, title: { display: true, text: 'Nhóm bằng chứng', color: '#94a3b8' } },
    y: { min: 0, max: 100, ticks: { color: '#94a3b8', callback: value => `${value}%` }, title: { display: true, text: 'Tỷ lệ điểm (%)', color: '#94a3b8' } } } }

export function EvaluationCharts({ dimensions = {}, history = [] }) {
  return <div className="space-y-5">{history.length >= 2 && <Card className="min-w-0 p-5"><h2 className="mb-4 text-lg font-semibold">Xu hướng qua các bài</h2><div className="relative h-60"><Line role="img" aria-label="Xu hướng điểm từ 0 đến 100 phần trăm" options={{ ...options, scales: { ...options.scales, x: { ...options.scales.x, title: { display: true, text: 'Bài làm theo thứ tự thời gian', color: '#94a3b8' } } } }} data={{ labels: history.map((_, i) => `Bài ${i+1}`), datasets: [{ label: 'Điểm (%)', data: history.map(item => item.percentage), borderColor: '#0e7490', backgroundColor: '#0e7490', pointStyle: 'rectRot', pointRadius: 5 }] }} /></div><p className="mt-3 text-sm text-sub">{history.map((item, i) => `Bài ${i+1}: ${Number(item.percentage).toFixed(2)}%`).join(' · ')}</p></Card>}
    {Object.entries({ clo: 'Điểm theo CLO', topic: 'Điểm theo chủ đề', difficulty: 'Điểm theo độ khó' }).map(([key, title]) => <Card className="min-w-0 p-5" key={key}><h2 className="mb-4 text-lg font-semibold">{title}</h2>{dimensions[key]?.length ? <><div className="relative h-60"><Bar role="img" aria-label={`${title}, thang 0 đến 100 phần trăm`} options={options} data={{ labels: dimensions[key].map(item => item.label), datasets: [{ label: 'Điểm (%)', data: dimensions[key].map(item => item.percentage), backgroundColor: '#0e7490', borderColor: '#155e75', borderWidth: 1 }] }} /></div><ul className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-sm text-sub">{dimensions[key].map(item => <li key={item.label}>{item.label}: {Number(item.percentage).toFixed(2)}% ({item.earned}/{item.possible} điểm)</li>)}</ul></> : <p className="text-sm text-sub">Chưa có bằng chứng cho nhóm này.</p>}</Card>)}
  </div>
}
