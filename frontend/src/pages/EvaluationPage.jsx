import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api, { apiMessage } from '../api'
import { Card, btnPrimary, btnGhost } from '../components/ui'
import { ActionSpinner, ErrorState } from '../components/States'
import { EvaluationCharts } from '../components/EvaluationCharts'

function validateView(data) {
  if (
    !data ||
    ![
      'empty',
      'pending',
      'processing',
      'updating',
      'provisional',
      'ready',
      'awaiting_approval',
    ].includes(data.status) ||
    (['provisional', 'ready'].includes(data.status) && !data.result?.evaluation)
  )
    throw new Error('Invalid evaluation response')
  return data
}

export function EvaluationContent({ data, overall = false }) {
  const evaluation = data.result?.evaluation
  const questionResults = Object.fromEntries(
    (data.question_results || []).map((item) => [item.attempt_id, item]),
  )
  return (
    <div className="space-y-5">
      {data.provisional && (
        <p role="status" className="rounded-xl border border-amber-500 p-4 font-semibold">
          Kết quả tạm thời – AI đã chấm, chưa được giảng viên xác nhận
          <span className="mt-1 block text-sm font-normal">
            Điểm và nhận xét có thể thay đổi sau khi giảng viên kiểm tra và duyệt.
          </span>
        </p>
      )}
      {data.approved && (
        <p role="status" className="rounded-xl border border-emerald-500 p-4 font-semibold">
          ✓ Đã được giảng viên duyệt — kết quả chính thức
          {data.adjusted && (
            <span className="mt-1 block text-sm font-normal">Điểm đã được điều chỉnh</span>
          )}
        </p>
      )}
      {data.pending_count > 0 && overall && (
        <p className="text-sm text-sub">
          {data.pending_count} bài đang chờ chấm hoặc duyệt, chưa được đưa vào đánh giá.
        </p>
      )}
      {overall && data.attempt_count === 1 && (
        <p className="rounded-lg border border-edge p-4 text-sub">Làm thêm bài để xem xu hướng</p>
      )}
      {data.result?.evaluator_fallback && (
        <p className="text-sm text-sub">
          Đánh giá dự phòng theo quy tắc. Điểm tự luận là đề xuất tự động.
        </p>
      )}
      {data.score && (
        <Card className="p-5">
          <h2 className="text-lg font-semibold">{overall ? 'Điểm tích lũy' : 'Điểm bài làm'}</h2>
          <p className="mt-3 text-3xl font-bold tabular-nums">
            {Number(data.score.percentage).toFixed(2)}%
          </p>
          <p className="mt-2 text-sub">
            {data.score.earned} / {data.score.possible} điểm · {data.attempt_count} bài đã công bố
          </p>
        </Card>
      )}
      {data.uncovered_concepts?.length > 0 && (
        <Card className="p-5">
          <h2 className="text-lg font-semibold">Khái niệm chưa được kiểm tra</h2>
          <p className="mt-2 text-sub">
            Ngân hàng chưa có câu hỏi phù hợp cho các khái niệm sau; kết quả không đánh giá chúng.
          </p>
          <ul className="mt-3 list-disc space-y-1 pl-5 text-sub">
            {data.uncovered_concepts.map((c) => (
              <li key={c.concept_id}>{c.concept_name}</li>
            ))}
          </ul>
        </Card>
      )}
      {data.concept_results?.length > 0 && (
        <Card className="p-5">
          <h2 className="text-lg font-semibold">Điểm mạnh và điểm cần cải thiện theo khái niệm</h2>
          <ul className="mt-4 space-y-4">
            {data.concept_results.map((c) => (
              <li key={c.concept_id} className="border-b border-edge pb-4 last:border-0">
                <p className="font-semibold text-ink">
                  {c.concept_name || `#${c.concept_id}`}
                  {c.competency_pct != null && (
                    <span className="mt-1 block break-words font-normal text-sub">
                      {Number(c.competency_pct).toFixed(2)}%
                      {c.target_pct != null && ` / mục tiêu ${Number(c.target_pct).toFixed(2)}%`}
                    </span>
                  )}
                </p>
                {!c.covered && <p className="mt-1 text-sm text-amber-300">Chưa có câu hỏi.</p>}
                {c.strength && <p className="mt-1 text-sm text-emerald-300">Mạnh: {c.strength}</p>}
                {c.weakness && (
                  <p className="mt-1 text-sm text-amber-300">Cần cải thiện: {c.weakness}</p>
                )}
                {c.recommendation && (
                  <p className="mt-1 text-sm text-sub">Gợi ý: {c.recommendation}</p>
                )}
              </li>
            ))}
          </ul>
        </Card>
      )}
      {evaluation && (
        <Card className="p-5">
          <h2 className="text-xl font-semibold">Nhận xét</h2>
          <p className="mt-3 whitespace-pre-wrap text-sub">{evaluation.summary}</p>
          {overall && data.attempt_count >= 2 && evaluation.trend && (
            <p className="mt-3 text-sub">{evaluation.trend}</p>
          )}
        </Card>
      )}
      <EvaluationCharts
        dimensions={data.dimensions}
        history={overall && data.attempt_count >= 2 ? data.history : []}
      />
      {evaluation && (
        <>
          <div className="grid gap-4 md:grid-cols-2">
            {[
              ['strengths', 'Điểm mạnh'],
              ['weaknesses', 'Điểm cần cải thiện'],
              ['suggestions', 'Gợi ý luyện tập'],
              ['learning_path', 'Lộ trình học'],
            ].map(([key, label]) => (
              <Card className="p-5" key={key}>
                <h2 className="text-lg font-semibold">{label}</h2>
                <ul className="mt-3 list-disc space-y-2 pl-5 text-sub">
                  {evaluation[key].map((text, i) => (
                    <li key={i}>{text}</li>
                  ))}
                </ul>
              </Card>
            ))}
          </div>
          {!overall && (
            <Card className="p-5">
              <h2 className="text-xl font-semibold">Nhận xét từng câu</h2>
              <ol className="mt-4 space-y-4">
                {evaluation.question_comments.map((item, i) => (
                  <li key={item.attempt_id} className="border-b border-edge pb-4 last:border-0">
                    <h3 className="font-semibold">Câu {i + 1}</h3>
                    {questionResults[item.attempt_id] && (
                      <p className="mt-1 text-sm text-sub">
                        Điểm: {questionResults[item.attempt_id].score ?? '—'} /{' '}
                        {questionResults[item.attempt_id].points}
                      </p>
                    )}
                    <p className="mt-2 text-sub">{item.comment}</p>
                    {item.essay_score_proposal != null && (
                      <p className="mt-1 text-sm text-sub">
                        Điểm tự luận đề xuất: {item.essay_score_proposal}
                      </p>
                    )}
                  </li>
                ))}
              </ol>
            </Card>
          )}
          {data.details_truncated && (
            <p className="text-sm text-mute">
              {overall
                ? 'Thống kê gồm toàn bộ bài đã công bố. Nhận xét chi tiết tập trung vào các câu gần nhất.'
                : 'Một số nội dung dài được rút gọn khi tạo nhận xét. Điểm và đáp án gốc vẫn xem đầy đủ trong bài làm.'}
            </p>
          )}
        </>
      )}
    </div>
  )
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
    let timer,
      canceled = false
    setData(null)
    setError(null)
    setExpired(false)
    setBusy(false)
    async function poll() {
      try {
        const r = await api.get(path, { timeout: 15000 })
        if (canceled || run !== sequence.current) return
        setData(validateView(r.data))
        if (r.data.status === 'awaiting_approval') {
          timer = setTimeout(poll, Date.now() - started < 45000 ? 1500 : 10000)
        } else if (r.data.status === 'provisional') {
          timer = setTimeout(poll, 15000)
        } else if (r.data.status === 'updating') {
          timer = setTimeout(poll, 2000)
        } else if (['pending', 'processing'].includes(r.data.status)) {
          if (Date.now() - started < 45000) timer = setTimeout(poll, 1500)
          else {
            const fallback = await api.post(`${path}/retry`, null, { timeout: 15000 })
            if (!canceled && run === sequence.current) {
              setData(validateView(fallback.data))
              setExpired(fallback.data.status !== 'ready')
            }
          }
        }
      } catch (e) {
        if (!canceled && run === sequence.current) {
          setError(apiMessage(e))
          setExpired(true)
        }
      }
    }
    poll()
    return () => {
      canceled = true
      clearTimeout(timer)
      sequence.current += 1
    }
  }, [path, reload])
  async function retry() {
    if (busy) return
    setBusy(true)
    setError(null)
    const run = ++sequence.current
    try {
      const r = await api.post(`${path}/retry`, null, { timeout: 15000 })
      if (run === sequence.current) {
        setData(validateView(r.data))
        if (['pending', 'processing'].includes(r.data.status)) setReload((value) => value + 1)
        else setExpired(!['ready', 'empty'].includes(r.data.status))
      }
    } catch (e) {
      if (run === sequence.current) setError(apiMessage(e))
    } finally {
      if (run === sequence.current) setBusy(false)
    }
  }
  const waiting = !data || ['pending', 'processing'].includes(data.status)
  return (
    <div className="content-wrap mx-auto max-w-5xl space-y-5 py-8">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-3xl font-bold">{overall ? 'Đánh giá tổng thể' : 'Đánh giá bài làm'}</h1>
        {!overall && (
          <Link className={btnGhost} to={`/history/${sessionId}`}>
            Xem bài làm
          </Link>
        )}
      </header>
      {error && <ErrorState message={error} onRetry={retry} />}
      {data?.status === 'empty' ? (
        <Card className="space-y-4 p-6">
          <h2 className="text-xl font-semibold">Bắt đầu hành trình của bạn</h2>
          <p className="text-sub">Hoàn thành một bài luyện tập để nhận đánh giá năng lực.</p>
          {data.pending_count > 0 && (
            <p className="text-sub">{data.pending_count} bài đang chờ chấm hoặc duyệt.</p>
          )}
          <Link className={btnPrimary} to="/assessments">
            Bắt đầu luyện tập
          </Link>
        </Card>
      ) : data?.status === 'awaiting_approval' ? (
        <Card className="space-y-4 p-6">
          <h2 className="text-xl font-semibold">Đang chờ giảng viên duyệt</h2>
          <p className="text-sub">
            AI đã chấm và đánh giá sơ bộ. Giảng viên đang kiểm tra đáp án, chạy SQL, điều chỉnh điểm
            nếu cần và duyệt trước khi công bố kết quả chính thức.
          </p>
          <button className={btnGhost} onClick={() => setReload((value) => value + 1)}>
            Kiểm tra cập nhật
          </button>
          <Link className="ml-3 underline" to="/history">
            Lịch sử bài làm
          </Link>
        </Card>
      ) : data?.status === 'updating' ? (
        <Card className="space-y-4 p-6">
          <h2 className="text-xl font-semibold">Kết quả đang được cập nhật</h2>
          <p className="text-sub">
            Giảng viên vừa điều chỉnh điểm. Hệ thống đang tạo lại đánh giá AI cho bài làm; kết quả
            tạm thời cũ không còn hiệu lực.
          </p>
          <div className="flex flex-wrap gap-3">
            <button className={btnGhost} onClick={() => setReload((value) => value + 1)}>
              Kiểm tra cập nhật
            </button>
            <Link className="self-center underline" to="/history">
              Lịch sử bài làm
            </Link>
          </div>
        </Card>
      ) : waiting ? (
        <Card className="space-y-4 p-6">
          <div role="status" className="flex items-center gap-3">
            {!expired && !error && <ActionSpinner />}
            <p>
              {expired || error
                ? 'Đánh giá đang mất nhiều thời gian. Bạn có thể thử lại hoặc quay về lịch sử.'
                : 'Đang chờ AI đánh giá...'}
            </p>
          </div>
          <button type="button" disabled={busy} onClick={retry} className={btnGhost}>
            {busy ? 'Đang tải...' : 'Thử lại'}
          </button>
          <Link to="/history" className="ml-3 underline">
            Lịch sử bài làm
          </Link>
        </Card>
      ) : (
        <EvaluationContent data={data} overall={overall} />
      )}
    </div>
  )
}
