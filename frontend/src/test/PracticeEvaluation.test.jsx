import { act, fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { vi, beforeEach, afterEach, it, expect } from 'vitest'
import api from '../api'
import EvaluationPage from '../pages/EvaluationPage'
import AssessmentsPage from '../pages/AssessmentsPage'
import AdminSystemPage from '../pages/admin/AdminSystemPage'
vi.mock('../api', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn() },
  apiMessage: () => 'Kết nối gián đoạn. Hãy thử lại.',
}))
vi.mock('../components/EvaluationCharts', () => ({
  EvaluationCharts: ({ history = [] }) => (
    <div data-testid="charts">{history.length >= 2 ? 'TREND' : 'NO TREND'}</div>
  ),
}))
const result = {
  evaluation: {
    summary: 'Nhận xét dựa trên bằng chứng.',
    strengths: ['Điểm mạnh'],
    weaknesses: ['Điểm cần ôn'],
    suggestions: ['Luyện thêm'],
    learning_path: ['Ôn SELECT'],
    trend: null,
    question_comments: [
      { attempt_id: 1, question_id: 4, comment: 'Câu trả lời đúng.', essay_score_proposal: null },
    ],
  },
  evaluator_fallback: true,
}
const ready = {
  status: 'ready',
  attempt_count: 1,
  pending_count: 0,
  result,
  dimensions: {},
  history: [{ percentage: 80 }],
}
function renderEvaluation(overall = false) {
  return render(
    <MemoryRouter initialEntries={['/evaluations/7']}>
      <Routes>
        <Route path="/evaluations/:sessionId" element={<EvaluationPage overall={overall} />} />
      </Routes>
    </MemoryRouter>,
  )
}
beforeEach(() => vi.clearAllMocks())
afterEach(() => vi.useRealTimers())

it('shows loading, automatically refreshes and renders per-question feedback', async () => {
  api.get.mockResolvedValueOnce({ data: { status: 'pending' } }).mockResolvedValue({ data: ready })
  renderEvaluation()
  expect(screen.getByText('Đang chờ AI đánh giá...')).toBeInTheDocument()
  expect(await screen.findByText('Câu trả lời đúng.', {}, { timeout: 3000 })).toBeInTheDocument()
  expect(api.get).toHaveBeenCalledTimes(2)
  expect(screen.getByText(/Đánh giá dự phòng/)).toBeInTheDocument()
})
it('recovers from an offline request with a bounded explicit retry', async () => {
  api.get.mockRejectedValue(new Error('secret internal error'))
  api.post.mockResolvedValue({ data: ready })
  renderEvaluation()
  await screen.findByRole('alert')
  expect(screen.queryByText('secret internal error')).not.toBeInTheDocument()
  await userEvent.click(screen.getAllByRole('button', { name: /Thử lại/i }).at(-1))
  expect(await screen.findByText('Câu trả lời đúng.')).toBeInTheDocument()
  expect(api.post).toHaveBeenCalledWith('/evaluations/attempts/7/retry', null, { timeout: 15000 })
})
it('continues checking when a retry returns a pending evaluation', async () => {
  api.get.mockResolvedValueOnce({ data: { status: 'pending' } }).mockResolvedValue({ data: ready })
  api.post.mockResolvedValue({ data: { status: 'pending' } })
  renderEvaluation()
  await screen.findByText('Đang chờ AI đánh giá...')
  await userEvent.click(screen.getByRole('button', { name: 'Thử lại' }))
  expect(await screen.findByText('Câu trả lời đúng.', {}, { timeout: 3000 })).toBeVisible()
})
it('rejects a ready response without feedback instead of rendering an empty chart screen', async () => {
  api.get.mockResolvedValue({ data: { status: 'ready', result: null } })
  renderEvaluation()
  expect(await screen.findByRole('alert')).toBeInTheDocument()
  expect(screen.queryByTestId('charts')).not.toBeInTheDocument()
  expect(screen.getByText(/Đánh giá đang mất nhiều thời gian/)).toBeInTheDocument()
})
it.each([0, 1, 3])('adapts overall evaluation to %s completed attempts', async (count) => {
  api.get.mockResolvedValue({
    data: {
      ...ready,
      status: count ? 'ready' : 'empty',
      attempt_count: count,
      pending_count: 2,
      history: Array.from({ length: count }, () => ({ percentage: 80 })),
      result: {
        ...result,
        evaluation: { ...result.evaluation, trend: count >= 2 ? 'Tiến bộ theo thời gian' : null },
      },
    },
  })
  renderEvaluation(true)
  await screen.findByRole('heading', { name: count ? 'Nhận xét' : 'Bắt đầu hành trình của bạn' })
  if (!count)
    expect(screen.getByRole('link', { name: 'Bắt đầu luyện tập' })).toHaveAttribute(
      'href',
      '/assessments',
    )
  else if (count === 1) {
    expect(screen.getByText('Làm thêm bài để xem xu hướng')).toBeInTheDocument()
    expect(screen.getByTestId('charts')).toHaveTextContent('NO TREND')
  } else {
    expect(screen.getByTestId('charts')).toHaveTextContent('TREND')
    expect(screen.getByText('Tiến bộ theo thời gian')).toBeInTheDocument()
  }
  expect(screen.getByText(/2 bài đang chờ/)).toBeInTheDocument()
})
it('hides all grades and comments while awaiting approval', async () => {
  api.get.mockResolvedValue({ data: { status: 'awaiting_approval' } })
  renderEvaluation()
  expect(
    await screen.findByRole('heading', { name: 'Đang chờ giảng viên duyệt' }),
  ).toBeInTheDocument()
  expect(screen.queryByTestId('charts')).not.toBeInTheDocument()
  expect(screen.queryByText('Câu trả lời đúng.')).not.toBeInTheDocument()
})
it('marks approved and adjusted results clearly', async () => {
  api.get.mockResolvedValue({ data: { ...ready, approved: true, adjusted: true } })
  renderEvaluation()
  expect(await screen.findByText(/Đã được giảng viên duyệt/)).toBeInTheDocument()
  expect(screen.getByText('Điểm đã được điều chỉnh')).toBeInTheDocument()
})
it('keeps checking a long instructor review and shows approval without reloading', async () => {
  vi.useFakeTimers()
  let approved = false
  api.get.mockImplementation(() =>
    Promise.resolve({
      data: approved ? { ...ready, approved: true } : { status: 'awaiting_approval' },
    }),
  )
  renderEvaluation()
  await act(async () => {
    await vi.advanceTimersByTimeAsync(61000)
  })
  expect(screen.getByRole('heading', { name: 'Đang chờ giảng viên duyệt' })).toBeVisible()
  expect(api.post).not.toHaveBeenCalled()
  approved = true
  await act(async () => {
    await vi.advanceTimersByTimeAsync(10000)
  })
  expect(screen.getByText(/Đã được giảng viên duyệt/)).toBeVisible()
  expect(screen.getByText('Câu trả lời đúng.')).toBeVisible()
})
it('falls back after 45 seconds and stops the spinner', async () => {
  vi.useFakeTimers()
  api.get.mockResolvedValue({ data: { status: 'processing' } })
  api.post.mockResolvedValue({ data: ready })
  renderEvaluation()
  await act(async () => {
    await vi.advanceTimersByTimeAsync(46000)
  })
  expect(api.post).toHaveBeenCalledTimes(1)
  expect(screen.getByText('Câu trả lời đúng.')).toBeInTheDocument()
  expect(screen.queryByText('Đang chờ AI đánh giá...')).not.toBeInTheDocument()
})
it('prevents double submit, shows generation state and keeps the request id for retry', async () => {
  api.get.mockImplementation((url) =>
    Promise.resolve({
      data:
        url === '/practice/options'
          ? {
              question_count: { min: 1, default: 5, max: 20, presets: [5, 10, 15, 20] },
              concepts: [{ concept_id: 1, concept_name: 'SELECT' }],
            }
          : [],
    }),
  )
  let reject
  api.post.mockImplementation(
    () =>
      new Promise((_, fail) => {
        reject = fail
      }),
  )
  render(
    <MemoryRouter>
      <AssessmentsPage />
    </MemoryRouter>,
  )
  await userEvent.click(await screen.findByRole('button', { name: 'Chọn tất cả khái niệm' }))
  await userEvent.click(screen.getByRole('radio', { name: 'AI tạo câu hỏi' }))
  await userEvent.click(screen.getByRole('button', { name: '15 câu', exact: true }))
  const button = screen.getByRole('button', { name: 'Bắt đầu' })
  fireEvent.click(button)
  fireEvent.click(button)
  expect(api.post).toHaveBeenCalledTimes(1)
  const id = api.post.mock.calls[0][1].request_id
  const setup = api.post.mock.calls[0][1]
  expect(screen.getByRole('status')).toHaveTextContent('Đang tạo câu hỏi...')
  await act(async () => reject(new Error('offline')))
  fireEvent.click(screen.getByRole('button', { name: 'Thử lại' }))
  expect(api.post.mock.calls[1][1].request_id).toBe(id)
  expect(api.post.mock.calls[1][1]).toEqual(setup)
})
it('shows the mandatory review workflow and AI status without a release toggle', async () => {
  api.get.mockResolvedValue({
    data: {
      database: 'PostgreSQL 17',
      pipeline: 'Prompt Builder → Evaluator → Admin review',
    },
  })
  render(<AdminSystemPage />)
  expect(await screen.findByText(/Every submission goes through two steps/)).toBeInTheDocument()
  expect(screen.queryByRole('radio')).not.toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Lưu cấu hình' })).not.toBeInTheDocument()
  expect(screen.getAllByText(/Prompt builder/).length).toBeGreaterThan(0)
  expect(screen.getAllByText(/administrator approves/).length).toBeGreaterThan(0)
})
