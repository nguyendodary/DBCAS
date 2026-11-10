import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api, { apiMessage } from '../api'
import { Card, btnPrimary, btnGhost, inputCls } from '../components/ui'
import { ActionSpinner, EmptyState, ErrorState, Loading } from '../components/States'

const BANDS = [
  ['EASY', 'Dễ'],
  ['MEDIUM', 'Vừa'],
  ['HARD', 'Khó'],
]
const toggle = (items, value) =>
  items.includes(value) ? items.filter((item) => item !== value) : [...items, value]

export default function AssessmentsPage() {
  const [options, setOptions] = useState(null)
  const [selected, setSelected] = useState([])
  const [bands, setBands] = useState(BANDS.map(([value]) => value))
  const [source, setSource] = useState('bank')
  const [count, setCount] = useState(null)
  const [search, setSearch] = useState('')
  const [active, setActive] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const requestId = useRef(crypto.randomUUID())
  const guard = useRef(false)
  const navigate = useNavigate()
  const load = useCallback(() => {
    setError(null)
    let canceled = false
    Promise.all([api.get('/practice/options'), api.get('/sessions')])
      .then(([o, s]) => {
        if (canceled) return
        if (!Array.isArray(o.data?.concepts) || !Array.isArray(s.data))
          throw new Error('Invalid practice options response')
        const limits = o.data.question_count
        if (
          !limits ||
          ![limits.min, limits.default, limits.max].every(Number.isInteger) ||
          limits.min > limits.default ||
          limits.default > limits.max ||
          !Array.isArray(limits.presets)
        )
          throw new Error('Invalid question count configuration')
        setOptions(o.data)
        setCount(limits.default)
        setSelected([])
        setActive(s.data.find((item) => item.status === 'in_progress') || null)
      })
      .catch((e) => {
        if (!canceled) setError(apiMessage(e))
      })
    return () => {
      canceled = true
    }
  }, [])
  useEffect(load, [load])
  useEffect(() => {
    requestId.current = crypto.randomUUID()
  }, [selected, bands, source, count])
  async function start(event) {
    event.preventDefault()
    if (guard.current) return
    guard.current = true
    setBusy(true)
    setError(null)
    try {
      const r = await api.post('/practice/start', {
        concept_ids: selected,
        difficulties: bands,
        source,
        question_count: Number(count),
        request_id: requestId.current,
      })
      navigate(`/exam/${r.data.session_id}`)
    } catch (e) {
      const code = e?.response?.data?.error?.code
      const details = e?.response?.data?.error?.details
      if (code === 'active_practice' && details?.session_id) {
        navigate(`/exam/${details.session_id}`)
        return
      } else setError(apiMessage(e, 'Chưa tạo được bài luyện tập. Hãy thử lại.'))
    } finally {
      guard.current = false
      setBusy(false)
    }
  }
  return (
    <div className="content-wrap mx-auto max-w-4xl space-y-6 py-8">
      <header>
        <p className="text-sm font-semibold text-cyan-300">Luyện tập cơ sở dữ liệu</p>
        <h1 className="mt-2 text-3xl font-bold text-ink">Tạo bài luyện tập</h1>
        <p className="mt-3 text-sub">Chọn nội dung bạn muốn ôn và bắt đầu ngay.</p>
      </header>
      {error && !options && <ErrorState message={error} onRetry={load} />}
      {!options ? (
        !error && <Loading />
      ) : !options.concepts.length ? (
        <EmptyState title="Ngân hàng chưa có khái niệm">
          Giảng viên cần bổ sung khái niệm và câu hỏi trước khi bạn bắt đầu.
        </EmptyState>
      ) : active ? (
        <Card className="space-y-4 p-6">
          <h2 className="text-lg font-semibold">Bạn có bài đang làm</h2>
          <p className="text-sub">Câu trả lời đã lưu sẽ được khôi phục.</p>
          <Link className={btnPrimary} to={`/exam/${active.session_id}`}>
            Tiếp tục bài làm
          </Link>
        </Card>
      ) : (
        <form onSubmit={start}>
          <Card className="space-y-7 p-5 sm:p-7">
            <fieldset disabled={busy} className="space-y-7">
              <fieldset className="min-w-0">
                <legend className="text-lg font-semibold">1. Chọn khái niệm</legend>
                <button
                  type="button"
                  className={`${btnGhost} my-3`}
                  onClick={() => setSelected(options.concepts.map((c) => c.concept_id))}
                >
                  Chọn tất cả khái niệm
                </button>
                {options.concepts.length > 12 && (
                  <label className="mb-3 block text-sm text-sub">
                    Tìm khái niệm
                    <input
                      type="search"
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                      className={`${inputCls} mt-1 w-full`}
                    />
                  </label>
                )}
                <div className="flex flex-wrap gap-2 pb-1">
                  {options.concepts
                    .filter((c) =>
                      c.concept_name
                        .toLocaleLowerCase('vi')
                        .includes(search.toLocaleLowerCase('vi')),
                    )
                    .map((c) => (
                      <button
                        key={c.concept_id}
                        type="button"
                        aria-label={c.concept_name}
                        aria-pressed={selected.includes(c.concept_id)}
                        className={`max-w-full whitespace-normal break-words rounded-full border px-4 py-2 text-left text-sm ${selected.includes(c.concept_id) ? 'border-cyan-400 bg-cyan-400/15 font-semibold text-ink' : 'border-edge text-sub'}`}
                        onClick={() => setSelected(toggle(selected, c.concept_id))}
                      >
                        {selected.includes(c.concept_id) && <span aria-hidden="true">✓ </span>}
                        {c.concept_name}
                      </button>
                    ))}
                </div>
                <p className="mt-3 text-sm text-mute">Đã chọn {selected.length} khái niệm.</p>
              </fieldset>
              <fieldset>
                <legend className="mb-3 text-lg font-semibold">2. Chọn độ khó</legend>
                <div className="flex flex-wrap gap-3">
                  {BANDS.map(([value, label]) => (
                    <button
                      type="button"
                      key={value}
                      aria-pressed={bands.includes(value)}
                      className={`rounded-lg border px-5 py-2 ${bands.includes(value) ? 'border-cyan-400 bg-cyan-400/15 font-semibold text-ink' : 'border-edge text-sub'}`}
                      onClick={() => setBands(toggle(bands, value))}
                    >
                      {bands.includes(value) && <span aria-hidden="true">✓ </span>}
                      {label}
                    </button>
                  ))}
                </div>
              </fieldset>
              <fieldset>
                <legend className="mb-3 text-lg font-semibold">3. Chọn nguồn câu hỏi</legend>
                <div className="grid gap-3 sm:grid-cols-2">
                  {[
                    ['bank', 'Từ ngân hàng câu hỏi'],
                    ['ai', 'AI tạo câu hỏi'],
                  ].map(([value, label]) => (
                    <label
                      key={value}
                      className="flex cursor-pointer items-center gap-3 rounded-xl border border-edge p-4"
                    >
                      <input
                        type="radio"
                        name="source"
                        value={value}
                        checked={source === value}
                        onChange={() => setSource(value)}
                      />
                      {label}
                    </label>
                  ))}
                </div>
              </fieldset>
              <fieldset>
                <legend className="mb-3 text-lg font-semibold">4. Số câu</legend>
                <div className="mb-3 flex flex-wrap gap-2">
                  {options.question_count.presets.map((value) => (
                    <button
                      type="button"
                      key={value}
                      aria-pressed={Number(count) === value}
                      onClick={() => setCount(value)}
                      className={`${btnGhost} ${Number(count) === value ? 'border-cyan-400 text-cyan-300' : ''}`}
                    >
                      {value} câu
                    </button>
                  ))}
                </div>
                <label className="text-sm text-sub">
                  Số câu ({options.question_count.min}–{options.question_count.max})
                  <input
                    type="number"
                    min={options.question_count.min}
                    max={options.question_count.max}
                    required
                    value={count ?? ''}
                    onChange={(e) => setCount(e.target.value)}
                    className={`${inputCls} ml-3 w-24`}
                  />
                </label>
              </fieldset>
              <p className="text-sm text-sub">
                AI sẽ chấm và đánh giá sơ bộ sau khi nộp; Admin kiểm tra, chạy SQL, điều chỉnh điểm
                nếu cần rồi duyệt trước khi công bố kết quả chính thức.
              </p>
              {error && <ErrorState message={error} />}
              <button
                type="submit"
                className={btnPrimary}
                disabled={
                  busy ||
                  !selected.length ||
                  !bands.length ||
                  !Number.isInteger(Number(count)) ||
                  Number(count) < options.question_count.min ||
                  Number(count) > options.question_count.max
                }
              >
                {busy && <ActionSpinner />}
                {busy
                  ? source === 'ai'
                    ? 'Đang tạo câu hỏi...'
                    : 'Đang chuẩn bị bài...'
                  : error
                    ? 'Thử lại'
                    : 'Bắt đầu'}
              </button>
              {busy && (
                <p role="status" className="text-sm text-sub">
                  {source === 'ai' ? 'Đang tạo câu hỏi...' : 'Đang chuẩn bị bài...'}
                </p>
              )}
            </fieldset>
          </Card>
        </form>
      )}
    </div>
  )
}
