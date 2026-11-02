import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api, { apiMessage } from '../api'
import { Card, btnPrimary, btnGhost } from '../components/ui'
import { ActionSpinner, ErrorState } from '../components/States'
import { EvaluationCharts } from '../components/EvaluationCharts'

function validateView(data) {
  if (!data || !['empty', 'pending', 'processing', 'ready', 'awaiting_approval'].includes(data.status)
    || (data.status === 'ready' && !data.result?.evaluation)) throw new Error('Invalid evaluation response')
  return data
}

export function EvaluationContent({ data, overall = false }) {
  const evaluation = data.result?.evaluation
  return <div className="space-y-5">
    {data.approved && <p role="status" className="rounded-xl border border-emerald-500 p-4 font-semibold">✓ Đã được giảng viên duyệt{data.adjusted && <span className="mt-1 block text-sm font-normal">Điểm đã được điều chỉnh</span>}</p>}
    {data.pending_count > 0 && overall && <p className="text-sm text-sub">{data.pending_count} bài đang chờ chấm hoặc duyệt, chưa được đưa vào đánh giá.</p>}
    {overall && data.attempt_count === 1 && <p className="rounded-lg border border-edge p-4 text-sub">Làm thêm bài để xem xu hướng</p>}
    {data.result?.evaluator_fallback && <p className="text-sm text-sub">Đánh giá dự phòng theo quy tắc. Điểm tự luận là đề xuất tự động.</p>}
    {data.score && <Card className="p-5"><h2 className="text-lg font-semibold">{overall ? 'Điểm tích lũy' : 'Điểm bài làm'}</h2><p className="mt-3 text-3xl font-bold">{Number(data.score.percentage).toFixed(2)}%</p><p className="mt-2 text-sub">{data.score.earned} / {data.score.possible} điểm · {data.attempt_count} bài đã công bố</p></Card>}
    {evaluation && <Card className="p-5"><h2 className="text-xl font-semibold">Nhận xét</h2><p className="mt-3 whitespace-pre-wrap text-sub">{evaluation.summary}</p>{overall && data.attempt_count >= 2 && evaluation.trend && <p className="mt-3 text-sub">{evaluation.trend}</p>}</Card>}
    <EvaluationCharts dimensions={data.dimensions} history={overall && data.attempt_count >= 2 ? data.history : []} />
    {evaluation && <>
      <div className="grid gap-4 md:grid-cols-2">{[['strengths', 'Điểm mạnh'], ['weaknesses', 'Điểm cần cải thiện'], ['suggestions', 'Gợi ý luyện tập'], ['learning_path', 'Lộ trình học']].map(([key, label]) => <Card className="p-5" key={key}><h2 className="text-lg font-semibold">{label}</h2><ul className="mt-3 list-disc space-y-2 pl-5 text-sub">{evaluation[key].map((text, i) => <li key={i}>{text}</li>)}</ul></Card>)}</div>
      {!overall && <Card className="p-5"><h2 className="text-xl font-semibold">Nhận xét từng câu</h2><ol className="mt-4 space-y-4">{evaluation.question_comments.map((item, i) => <li key={item.attempt_id} className="border-b border-edge pb-4 last:border-0"><h3 className="font-semibold">Câu {i+1}</h3><p className="mt-2 text-sub">{item.comment}</p>{item.essay_score_proposal != null && <p className="mt-1 text-sm text-sub">Điểm tự luận đề xuất: {item.essay_score_proposal}</p>}</li>)}</ol></Card>}
      {data.details_truncated && <p className="text-sm text-mute">Thống kê sử dụng toàn bộ bài đã công bố; nhận xét chi tiết ưu tiên các câu gần nhất để giới hạn kích thước prompt.</p>}
    </>}
  </div>
}

export default function EvaluationPage({ overall = false }) {
  const { sessionId } = useParams()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [expired, setExpired] = useState(false)
  const [reload, setReload] = useState(0)
  const sequence = useRef(0)
  const path = overall ? '/evaluations/overall' : `/evaluations/attempts/${sessionId}`
  useEffect(() => {
    const run = ++sequence.current
    const started = Date.now()
    let timer, canceled = false
    setData(null); setError(null); setExpired(false); setBusy(false)
    async function poll() {
      try {
        const r = await api.get(path, { timeout: 15000 })
        if (canceled || run !== sequence.current) return
        setData(validateView(r.data))
        if (['pending', 'processing', 'awaiting_approval'].includes(r.data.status)) {
          if (Date.now() - started < 45000) timer = setTimeout(poll, 1500)
          else if (r.data.status !== 'awaiting_approval') {
            const fallback = await api.post(`${path}/retry`, null, { timeout: 15000 })
            if (!canceled && run === sequence.current) { setData(validateView(fallback.data)); setExpired(fallback.data.status !== 'ready') }
          } else setExpired(true)
        }
      } catch (e) { if (!canceled && run === sequence.current) { setError(apiMessage(e)); setExpired(true) } }
    }
    poll()
    return () => { canceled = true; clearTimeout(timer); sequence.current += 1 }
  }, [path, reload])
  async function retry() {
    if (busy) return
    setBusy(true); setError(null)
    const run = ++sequence.current
    try {
      const r = await api.post(`${path}/retry`, null, { timeout: 15000 })
      if (run === sequence.current) { setData(validateView(r.data)); setExpired(!['ready', 'empty'].includes(r.data.status)) }
    } catch (e) { if (run === sequence.current) setError(apiMessage(e)) }
    finally { if (run === sequence.current) setBusy(false) }
  }
  const waiting = !data || ['pending', 'processing'].includes(data.status)
  return <div className="content-wrap mx-auto max-w-5xl space-y-5 py-8">
    <header className="flex flex-wrap items-center justify-between gap-3"><h1 className="text-3xl font-bold">{overall ? 'Đánh giá tổng thể' : 'Đánh giá bài làm'}</h1>{!overall && <Link className={btnGhost} to={`/history/${sessionId}`}>Xem bài làm</Link>}</header>
    {error && <ErrorState message={error} onRetry={retry} />}
    {data?.status === 'empty' ? <Card className="space-y-4 p-6"><h2 className="text-xl font-semibold">Bắt đầu hành trình của bạn</h2><p className="text-sub">Hoàn thành một bài luyện tập để nhận đánh giá năng lực.</p>{data.pending_count > 0 && <p className="text-sub">{data.pending_count} bài đang chờ chấm hoặc duyệt.</p>}<Link className={btnPrimary} to="/assessments">Bắt đầu luyện tập</Link></Card> : data?.status === 'awaiting_approval' ? <Card className="space-y-4 p-6"><h2 className="text-xl font-semibold">Đang chờ giảng viên duyệt</h2><p className="text-sub">Bài đã nộp an toàn. Kết quả sẽ xuất hiện sau khi giảng viên duyệt.</p><button className={btnGhost} onClick={() => setReload(value => value+1)}>Kiểm tra cập nhật</button><Link className="ml-3 underline" to="/history">Lịch sử bài làm</Link></Card> : waiting ? <Card className="space-y-4 p-6"><div role="status" className="flex items-center gap-3">{!expired && !error && <ActionSpinner />}<p>{expired || error ? 'Đánh giá đang mất nhiều thời gian. Bạn có thể thử lại hoặc quay về lịch sử.' : 'Đang chờ AI đánh giá...'}</p></div><button type="button" disabled={busy} onClick={retry} className={btnGhost}>{busy ? 'Đang tải...' : 'Thử lại'}</button><Link to="/history" className="ml-3 underline">Lịch sử bài làm</Link></Card> : <EvaluationContent data={data} overall={overall} />}
  </div>
}
