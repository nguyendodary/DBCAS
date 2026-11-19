import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api, { apiMessage } from '../api'
import { Card, btnPrimary, btnGhost, inputCls } from '../components/ui'
import { ActionSpinner, EmptyState, ErrorState, Loading } from '../components/States'
import heroBg from '../assets/brand/nen1.jpg'
import heroVideo from '../assets/brand/video1.mp4'
import BackgroundVideo from '../components/BackgroundVideo'

const BANDS = [
  ['EASY', 'Dễ', 'Củng cố kiến thức nền', 'bg-emerald-400/10 text-emerald-300'],
  ['MEDIUM', 'Trung bình', 'Vận dụng kiến thức', 'bg-amber-400/10 text-amber-300'],
  ['HARD', 'Khó', 'Thử thách nâng cao', 'bg-violet-400/10 text-violet-300'],
]
const toggle = (items, value) =>
  items.includes(value) ? items.filter((item) => item !== value) : [...items, value]

function durationForQuestionCount(questionCount) {
  const count = Number(questionCount)
  if (!Number.isInteger(count) || count < 1) return null
  if (count < 15) return 20
  if (count <= 30) return 45
  return 60
}

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
  const allConceptsSelected =
    options?.concepts?.length > 0 && selected.length === options.concepts.length
  const durationMin = durationForQuestionCount(count)
  const normalizedSearch = search.trim().toLocaleLowerCase('vi')
  const visibleConcepts =
    options?.concepts?.filter((c) =>
      c.concept_name.toLocaleLowerCase('vi').includes(normalizedSearch),
    ) ?? []
  const load = useCallback(() => {
    setError(null)
    let canceled = false
    Promise.all([api.get('/practice/options'), api.get('/sessions')])
      .then(([o, s]) => {
        if (canceled) return
        if (!Array.isArray(o.data?.concepts) || !Array.isArray(s.data))
          throw new Error('Invalid assessment options response')
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
      } else setError(apiMessage(e, 'Chưa bắt đầu được bài đánh giá. Hãy thử lại.'))
    } finally {
      guard.current = false
      setBusy(false)
    }
  }
  return (
    <>
      <section className="hero-photo" style={{ '--hero-img': `url(${heroBg})` }}>
        <BackgroundVideo className="hero-video" src={heroVideo} poster={heroBg} />
        <div className="content-wrap mx-auto max-w-4xl hero-photo-inner">
      <header>
        <p className="text-sm font-semibold text-cyan-300">ĐÁNH GIÁ NĂNG LỰC CƠ SỞ DỮ LIỆU</p>
        <h1 className="mt-2 text-3xl font-bold text-ink">Đánh giá kiến thức của bạn</h1>
        <p className="mt-3 text-sub">
          Bài đánh giá giúp bạn nhận ra điểm mạnh và nội dung cần củng cố.
        </p>
      </header>
        </div>
      </section>
      <div className="content-wrap mx-auto max-w-4xl space-y-6 py-8">
      {error && !options && <ErrorState message={error} onRetry={load} />}
      {!options ? (
        !error && <Loading />
      ) : !options.concepts.length ? (
        <EmptyState title="Chưa có dữ liệu để đánh giá">
          Giảng viên cần bổ sung khái niệm và câu hỏi trước khi bài đánh giá có thể bắt đầu.
        </EmptyState>
      ) : active ? (
        <Card className="space-y-4 p-6">
          <h2 className="text-lg font-semibold">Bạn có bài đánh giá đang làm</h2>
          <p className="text-sub">Câu trả lời đã lưu sẽ được khôi phục khi bạn tiếp tục.</p>
          <Link className={btnPrimary} to={`/exam/${active.session_id}`}>
            Tiếp tục bài đánh giá
          </Link>
        </Card>
      ) : (
        <form onSubmit={start}>
          <Card className="space-y-7 p-5 sm:p-7">
            <fieldset disabled={busy} className="space-y-7">
              <fieldset className="min-w-0">
                <legend className="text-lg font-semibold">1. Chọn khái niệm</legend>
                <div className="mt-4 overflow-hidden rounded-2xl border border-edge/80 bg-surface/40">
                  <div className="flex flex-col gap-3 border-b border-edge/70 bg-surface/60 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <p className="text-sm font-semibold text-ink">Phạm vi đánh giá</p>
                      <p className="mt-0.5 text-xs text-mute">Chọn các khái niệm muốn kiểm tra trong bài.</p>
                    </div>
                    <span className="inline-flex w-fit items-center gap-1.5 rounded-full border border-cyan-400/25 bg-cyan-400/10 px-3 py-1.5 text-xs font-semibold text-cyan-300">
                      <span className="text-sm tabular-nums">{selected.length}</span>
                      <span>/ {options.concepts.length} đã chọn</span>
                    </span>
                  </div>

                  <div className="space-y-3 p-3 sm:p-4">
                    {options.concepts.length > 12 && (
                      <label className="relative block">
                        <span className="sr-only">Tìm khái niệm</span>
                        <svg
                          aria-hidden="true"
                          viewBox="0 0 24 24"
                          fill="none"
                          className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-mute"
                        >
                          <circle cx="10.8" cy="10.8" r="6.8" stroke="currentColor" strokeWidth="1.7" />
                          <path d="m16 16 4.2 4.2" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
                        </svg>
                        <input
                          type="search"
                          value={search}
                          onChange={(e) => setSearch(e.target.value)}
                          placeholder="Tìm theo tên khái niệm..."
                          className={`${inputCls} w-full pl-10`}
                        />
                      </label>
                    )}

                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="text-xs text-mute">
                        {search
                          ? `Đang hiển thị ${visibleConcepts.length}/${options.concepts.length} khái niệm`
                          : `${options.concepts.length} khái niệm`}
                      </p>
                      <button
                        type="button"
                        aria-pressed={allConceptsSelected}
                        onClick={() =>
                          setSelected(
                            allConceptsSelected ? [] : options.concepts.map((c) => c.concept_id),
                          )
                        }
                        className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-2 text-xs font-semibold transition-colors ${allConceptsSelected ? 'border-edge text-sub hover:border-rose-400/40 hover:text-rose-300' : 'border-cyan-400/30 bg-cyan-400/10 text-cyan-300 hover:border-cyan-400/50 hover:bg-cyan-400/15'}`}
                      >
                        {allConceptsSelected ? 'Bỏ chọn tất cả' : 'Chọn tất cả'}
                      </button>
                    </div>

                    <div
                      className={`grid grid-cols-1 gap-2 sm:grid-cols-2 ${options.concepts.length > 12 ? 'max-h-72 overflow-y-auto overscroll-contain pr-1' : ''}`}
                    >
                      {visibleConcepts.length > 0 ? (
                        visibleConcepts.map((c) => {
                          const isSelected = selected.includes(c.concept_id)
                          return (
                            <button
                              key={c.concept_id}
                              type="button"
                              aria-label={c.concept_name}
                              aria-pressed={isSelected}
                              onClick={() => setSelected(toggle(selected, c.concept_id))}
                              className={`group flex min-h-12 min-w-0 items-center gap-3 rounded-xl border p-3 text-left transition duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400/70 ${isSelected ? 'border-cyan-400/60 bg-cyan-400/10 text-ink shadow-sm shadow-cyan-950/20' : 'border-edge bg-panel/70 text-sub hover:border-cyan-400/40 hover:bg-surface-hover'}`}
                            >
                              <span
                                className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-md border transition-colors ${isSelected ? 'border-cyan-400 bg-cyan-400 text-slate-950' : 'border-edge bg-surface text-transparent group-hover:border-cyan-400/60'}`}
                                aria-hidden="true"
                              >
                                {isSelected && (
                                  <svg viewBox="0 0 16 16" fill="none" className="h-3.5 w-3.5">
                                    <path d="m3 8 3.1 3.1L13 4.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                  </svg>
                                )}
                              </span>
                              <span className="min-w-0 flex-1 break-words text-sm font-medium leading-snug">
                                {c.concept_name}
                              </span>
                            </button>
                          )
                        })
                      ) : (
                        <p className="col-span-full rounded-xl border border-dashed border-edge p-6 text-center text-sm text-mute">
                          Không tìm thấy khái niệm phù hợp.
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </fieldset>
              <fieldset>
                <legend className="mb-3 text-lg font-semibold">2. Chọn độ khó</legend>
                <p className="mb-3 max-w-2xl text-sm text-sub">
                  Chọn độ khó câu hỏi phù hợp với mức độ bạn muốn đánh giá.
                </p>
                <div className="grid gap-2.5 sm:grid-cols-3">
                  {BANDS.map(([value, label, hint, tone], index) => {
                    const isSelected = bands.includes(value)
                    return (
                      <button
                        type="button"
                        key={value}
                        aria-pressed={isSelected}
                        onClick={() => setBands(toggle(bands, value))}
                        className={`group relative flex min-h-28 flex-col justify-between overflow-hidden rounded-xl border p-3 text-left transition duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400/70 ${isSelected ? 'border-cyan-400/70 bg-cyan-400/[0.08] shadow-md shadow-cyan-950/15' : 'border-edge bg-panel/70 hover:-translate-y-0.5 hover:border-cyan-400/45 hover:bg-surface-hover'}`}
                      >
                        <span
                          aria-hidden="true"
                          className={`absolute inset-x-0 top-0 h-0.5 transition-colors ${isSelected ? 'bg-cyan-300' : 'bg-transparent group-hover:bg-cyan-400/50'}`}
                        />
                        <span className="flex w-full items-center justify-between">
                          <span
                            className={`flex h-9 w-9 items-center justify-center rounded-lg text-sm font-bold ring-1 ring-inset ${tone}`}
                          >
                            {index + 1}
                          </span>
                          <span
                            className={`flex h-5 w-5 items-center justify-center rounded-full border transition-colors ${isSelected ? 'border-cyan-400 bg-cyan-400 text-slate-950' : 'border-edge bg-surface text-transparent'}`}
                            aria-hidden="true"
                          >
                            {isSelected && (
                                <svg viewBox="0 0 16 16" fill="none" className="h-3 w-3">
                                <path d="m3 8 3.1 3.1L13 4.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                              </svg>
                            )}
                          </span>
                        </span>
                        <span className="mt-3 block">
                          <span className={`block text-sm font-semibold ${isSelected ? 'text-ink' : 'text-sub'}`}>
                            {label}
                          </span>
                          <span className="mt-1 block text-xs leading-relaxed text-mute">{hint}</span>
                        </span>
                      </button>
                    )
                  })}
                </div>
              </fieldset>
              <fieldset>
                <legend className="mb-3 text-lg font-semibold">3. Nguồn câu hỏi</legend>
                <div className="grid gap-3 sm:grid-cols-2">
                  {[
                    ['bank', 'Từ ngân hàng câu hỏi'],
                    ['ai', 'AI tạo câu hỏi đánh giá'],
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
                <legend className="mb-3 text-lg font-semibold">4. Số câu hỏi</legend>
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
                  Số câu hỏi ({options.question_count.min}–{options.question_count.max})
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
                {durationMin && (
                  <div
                    aria-live="polite"
                    className="mt-4 rounded-xl border border-cyan-400/20 bg-cyan-400/[0.06] px-4 py-3"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-semibold text-ink">Thời gian cả bài</span>
                      <span className="text-lg font-bold tabular-nums text-cyan-300">
                        {durationMin} phút
                      </span>
                    </div>
                    <p className="mt-1 text-xs leading-relaxed text-sub">
                      Dưới 15 câu: 20 phút · 15–30 câu: 45 phút · Trên 30 câu: 60 phút.
                    </p>
                  </div>
                )}
              </fieldset>
              <p className="text-sm text-sub">
                Sau khi nộp, AI chấm sơ bộ câu trả lời. Quản trị viên kiểm tra kết quả, chạy SQL khi
                cần và duyệt trước khi công bố điểm đánh giá.
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
                    ? 'Đang tạo câu hỏi đánh giá...'
                    : 'Đang chuẩn bị bài đánh giá...'
                  : error
                    ? 'Thử lại'
                    : 'Bắt đầu đánh giá'}
              </button>
              {busy && (
                <p role="status" className="text-sm text-sub">
                  {source === 'ai'
                    ? 'Đang tạo câu hỏi đánh giá...'
                    : 'Đang chuẩn bị bài đánh giá...'}
                </p>
              )}
            </fieldset>
          </Card>
        </form>
      )}
      </div>
    </>
  )
}
