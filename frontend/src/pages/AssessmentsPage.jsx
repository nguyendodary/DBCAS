import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import api, { apiMessage } from '../api'
import { Card, btnPrimary, btnGhost, inputCls } from '../components/ui'
import { ActionSpinner, EmptyState, ErrorState, Loading } from '../components/States'
import AssessmentStylePicker from '../components/AssessmentStylePicker'
import {
  ADAPTIVE,
  ADAPTIVE_MAX_QUESTIONS,
  ADAPTIVE_MIN_QUESTIONS,
  FIXED,
  buildPracticePayload,
  clampAdaptiveCount,
  isSelectionValid,
} from '../assessmentStyle'
import { t, useLocale } from '../i18n'

const BANDS = [
  ['EASY', 'Dễ'],
  ['MEDIUM', 'Vừa'],
  ['HARD', 'Khó'],
]
const toggle = (items, value) =>
  items.includes(value) ? items.filter((item) => item !== value) : [...items, value]

export function parseConceptIds(value) {
  if (!value) return []
  return [
    ...new Set(
      value
        .split(',')
        .map(Number)
        .filter((id) => Number.isInteger(id) && id > 0),
    ),
  ]
}

export default function AssessmentsPage() {
  useLocale()
  const [searchParams] = useSearchParams()
  const requestedConcepts = searchParams.get('concepts') || ''
  const [options, setOptions] = useState(null)
  const [style, setStyle] = useState(FIXED)
  const [selected, setSelected] = useState([])
  const [bands, setBands] = useState(BANDS.map(([value]) => value))
  const [source, setSource] = useState('bank')
  const [count, setCount] = useState(null)
  const [search, setSearch] = useState('')
  const [active, setActive] = useState(null)
  const [preview, setPreview] = useState(null)
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
        const available = new Set(o.data.concepts.map((c) => c.concept_id))
        setSelected(parseConceptIds(requestedConcepts).filter((id) => available.has(id)))
        setActive(s.data.find((item) => item.status === 'in_progress') || null)
      })
      .catch((e) => {
        if (!canceled) setError(apiMessage(e))
      })
    return () => {
      canceled = true
    }
  }, [requestedConcepts])
  useEffect(load, [load])
  useEffect(() => {
    requestId.current = crypto.randomUUID()
    setPreview(null)
  }, [selected, bands, source, count])
  // Keep the browser selection inside the backend's ADAPTIVE constraints:
  // bank-only, exactly one concept and one starting band, 3..50 MCQ questions.
  useEffect(() => {
    if (style !== ADAPTIVE) return
    setSource('bank')
    setSelected((previous) => previous.slice(0, 1))
    setBands((previous) => (previous.length ? previous.slice(0, 1) : ['MEDIUM']))
    setCount((previous) => clampAdaptiveCount(previous))
  }, [style])
  function toggleConcept(id) {
    setSelected(style === ADAPTIVE ? [id] : toggle(selected, id))
  }
  function toggleBand(value) {
    setBands(style === ADAPTIVE ? [value] : toggle(bands, value))
  }
  function handleStartError(e) {
    const code = e?.response?.data?.error?.code
    const details = e?.response?.data?.error?.details
    if (code === 'active_practice' && details?.session_id) {
      navigate(`/exam/${details.session_id}`)
      return
    }
    setError(apiMessage(e, 'Chưa tạo được bài luyện tập. Hãy thử lại.'))
  }
  async function create(payload) {
    const r = await api.post('/practice/start', payload)
    navigate(`/exam/${r.data.session_id}`)
  }
  async function start(event) {
    event.preventDefault()
    if (guard.current) return
    guard.current = true
    setBusy(true)
    setError(null)
    const payload = buildPracticePayload({
      style,
      selected,
      bands,
      source,
      count,
      requestId: requestId.current,
    })
    try {
      const checked = await api.post('/practice/preview', payload)
      if (checked.data?.uncovered_concepts?.length) {
        setPreview({ payload, data: checked.data })
        return
      }
      await create(payload)
    } catch (e) {
      handleStartError(e)
    } finally {
      guard.current = false
      setBusy(false)
    }
  }
  async function continueStart() {
    if (!preview || guard.current) return
    guard.current = true
    setBusy(true)
    setError(null)
    try {
      await create(preview.payload)
      setPreview(null)
    } catch (e) {
      handleStartError(e)
    } finally {
      guard.current = false
      setBusy(false)
    }
  }
  const selectedConcepts =
    options?.concepts.filter((concept) => selected.includes(concept.concept_id)) || []
  const baseLimits = options?.question_count
  const limits =
    style === ADAPTIVE
      ? {
          min: ADAPTIVE_MIN_QUESTIONS,
          max: ADAPTIVE_MAX_QUESTIONS,
          presets: (baseLimits?.presets || []).filter(
            (value) => value >= ADAPTIVE_MIN_QUESTIONS && value <= ADAPTIVE_MAX_QUESTIONS,
          ),
        }
      : baseLimits
  const selectionValid = options
    ? isSelectionValid({ style, selected, bands, source, count, limits })
    : false
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
      ) : preview ? (
        <Card className="space-y-4 p-6">
          <h2 className="text-lg font-semibold">Một số khái niệm chưa có câu hỏi phù hợp</h2>
          <p className="text-sub">{preview.data.notice}</p>
          <ul className="list-disc space-y-1 pl-5 text-sub">
            {preview.data.uncovered_concepts.map((c) => (
              <li key={c.concept_id}>{c.concept_name}</li>
            ))}
          </ul>
          {error && <ErrorState message={error} />}
          <div className="flex flex-wrap gap-3">
            <button type="button" className={btnPrimary} disabled={busy} onClick={continueStart}>
              {busy && <ActionSpinner />}
              Tiếp tục
            </button>
            <button
              type="button"
              className={btnGhost}
              disabled={busy}
              onClick={() => {
                setPreview(null)
                setError(null)
              }}
            >
              Chọn lại
            </button>
          </div>
        </Card>
      ) : (
        <form onSubmit={start}>
          <Card className="space-y-7 p-5 sm:p-7">
            <fieldset disabled={busy} className="space-y-7">
              <AssessmentStylePicker value={style} onChange={setStyle} disabled={busy} />
              <fieldset className="min-w-0">
                <legend className="text-lg font-semibold">1. Chọn khái niệm</legend>
                {style === ADAPTIVE ? (
                  <p role="status" className="my-3 text-sm text-sub">
                    {t('assessmentStyle.adaptive.conceptNote')}
                  </p>
                ) : (
                  <button
                    type="button"
                    className={`${btnGhost} my-3`}
                    onClick={() => setSelected(options.concepts.map((c) => c.concept_id))}
                  >
                    Chọn tất cả khái niệm
                  </button>
                )}
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
                        onClick={() => toggleConcept(c.concept_id)}
                      >
                        {selected.includes(c.concept_id) && <span aria-hidden="true">✓ </span>}
                        {c.concept_name}
                      </button>
                    ))}
                </div>
                <p className="mt-3 text-sm text-mute">Đã chọn {selected.length} khái niệm.</p>
                {requestedConcepts && selected.length > 0 && (
                  <p
                    role="status"
                    className="mt-3 rounded-lg border border-cyan-400/40 bg-cyan-400/10 p-3 text-sm text-sub"
                  >
                    {t('weakPractice.preselectedNotice')}
                  </p>
                )}
                {selectedConcepts.length > 0 && (
                  <section
                    aria-labelledby="selected-concepts-heading"
                    className="mt-4 rounded-xl border border-edge p-4"
                  >
                    <h2 id="selected-concepts-heading" className="text-base font-semibold text-ink">
                      {t('weakPractice.selectedTitle')}
                    </h2>
                    <p className="mt-1 text-sm text-mute">{t('weakPractice.selectedHelp')}</p>
                    <ul className="mt-3 space-y-2">
                      {selectedConcepts.map((concept) => (
                        <li key={concept.concept_id} className="rounded-lg bg-elev/40 p-3">
                          <p className="font-medium text-ink">{concept.concept_name}</p>
                          {concept.clos?.length ? (
                            <ul className="mt-1 space-y-0.5 text-sm text-sub">
                              {concept.clos.map((clo) => (
                                <li key={clo.clo_id}>
                                  <span className="font-medium">{clo.clo_code}</span> — {clo.title}
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <p className="mt-1 text-sm text-mute">{t('weakPractice.noClo')}</p>
                          )}
                        </li>
                      ))}
                    </ul>
                  </section>
                )}
              </fieldset>
              <fieldset>
                <legend className="mb-3 text-lg font-semibold">2. Chọn độ khó</legend>
                {style === ADAPTIVE && (
                  <p className="mb-3 text-sm text-sub">
                    {t('assessmentStyle.adaptive.difficultyNote')}
                  </p>
                )}
                <div className="flex flex-wrap gap-3">
                  {BANDS.map(([value, label]) => (
                    <button
                      type="button"
                      key={value}
                      aria-pressed={bands.includes(value)}
                      className={`rounded-lg border px-5 py-2 ${bands.includes(value) ? 'border-cyan-400 bg-cyan-400/15 font-semibold text-ink' : 'border-edge text-sub'}`}
                      onClick={() => toggleBand(value)}
                    >
                      {bands.includes(value) && <span aria-hidden="true">✓ </span>}
                      {label}
                    </button>
                  ))}
                </div>
              </fieldset>
              <fieldset>
                <legend className="mb-3 text-lg font-semibold">3. Chọn nguồn câu hỏi</legend>
                {style === ADAPTIVE ? (
                  <p role="status" className="rounded-lg border border-edge p-4 text-sm text-sub">
                    {t('assessmentStyle.adaptive.sourceNote')}
                  </p>
                ) : (
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
                )}
              </fieldset>
              <fieldset>
                <legend className="mb-3 text-lg font-semibold">4. Số câu</legend>
                <div className="mb-3 flex flex-wrap gap-2">
                  {limits.presets.map((value) => (
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
                  Số câu ({limits.min}–{limits.max})
                  <input
                    type="number"
                    min={limits.min}
                    max={limits.max}
                    required
                    value={count ?? ''}
                    onChange={(e) => setCount(e.target.value)}
                    className={`${inputCls} ml-3 w-24`}
                  />
                </label>
              </fieldset>
              {style === ADAPTIVE ? (
                <p className="text-sm text-sub">{t('assessmentStyle.adaptive.startNote')}</p>
              ) : (
                <p className="text-sm text-sub">
                  AI sẽ chấm và đánh giá sơ bộ sau khi nộp; Admin kiểm tra, chạy SQL, điều chỉnh
                  điểm nếu cần rồi duyệt trước khi công bố kết quả chính thức.
                </p>
              )}
              {error && <ErrorState message={error} />}
              <button type="submit" className={btnPrimary} disabled={busy || !selectionValid}>
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
