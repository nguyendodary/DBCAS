import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, afterEach, expect, it, vi } from 'vitest'
import api from '../api'
import { i18n, setLocale } from '../i18n'
import ExamPage from '../pages/ExamPage'

vi.mock('../api', async (original) => ({ ...(await original()), default: { get: vi.fn(), post: vi.fn(), put: vi.fn() } }))
const base = { session_id: 42, assessment_title: 'Original assessment', status: 'in_progress', served_count: 1, answered_count: 0, max_questions: 13, remaining_seconds: 3600 }
const question = { question_id: 1, question_type: 'mcq', prompt: 'Original question', difficulty_level: 1, points: '1', concepts: [], options: [{ option_id: 11, option_label: 'A', option_text: 'SELECT' }] }
async function mount(type = 'mcq', questionContent = question) {
  api.get.mockResolvedValue({ data: { ...base, current_question: { ...question, ...questionContent, question_type: type } } })
  // Settle the mocked session request and draft initialization before editing.
  // A visible textbox alone does not guarantee passive effects have completed.
  await act(async () => {
    render(<MemoryRouter initialEntries={['/exam/42']}><Routes><Route path="/exam/:sessionId" element={<ExamPage />} /></Routes></MemoryRouter>)
  })
}
beforeEach(async () => {
  vi.clearAllMocks(); sessionStorage.clear(); await i18n.changeLanguage('en')
  api.put.mockImplementation((_, body) => Promise.resolve({ data: { revision: body.revision } }))
})
afterEach(async () => { await act(() => i18n.changeLanguage('en')); localStorage.clear() })
it('keeps the selected MCQ and authoritative timer when requesting reviewed content in another locale', async () => {
  await mount()
  await userEvent.click(await screen.findByRole('radio', { name: 'A: SELECT' }))
  await userEvent.click(screen.getByRole('button', { name: 'Language' }))
  await userEvent.click(screen.getByRole('menuitemradio', { name: 'Tiếng Việt' }))
  expect(screen.getByRole('radio', { name: 'A: SELECT' })).toBeChecked()
  expect(screen.getByText('Original question')).toBeInTheDocument()
  expect(screen.getByLabelText('Thời gian còn lại')).toHaveTextContent(/59:5\d|60:00/)
  expect(api.get).toHaveBeenCalledTimes(2)
  await userEvent.click(screen.getByRole('button', { name: 'Lưu bản nháp' }))
  expect(api.put).toHaveBeenCalledWith('/sessions/42/draft', { question_id: 1, selected_option_id: 11, revision: 1 })
  expect(api.post).not.toHaveBeenCalled()
})
it.each(['sql', 'essay'])('retains the unsaved %s text across language switches', async (type) => {
  await mount(type)
  const editor = await screen.findByRole('textbox')
  const answer = type === 'sql' ? "SELECT 'English text', 1.00;" : 'Normalization preserves dependency semantics.'
  fireEvent.change(editor, { target: { value: answer } })
  await act(() => setLocale('vi'))
  expect(screen.getByRole('textbox')).toBe(editor)
  expect(editor).toHaveValue(answer)
  expect(screen.getByRole('button', { name: 'Nộp câu trả lời' })).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Lưu bản nháp' }))
  expect(api.put).toHaveBeenCalledWith('/sessions/42/draft', { question_id: 1, revision: 1, [type === 'sql' ? 'sql_answer' : 'essay_answer']: answer })
  expect(api.get).toHaveBeenCalledTimes(2)
})
it('keeps Vietnamese fallback question text and answer state when the UI switches to English', async () => {
  const viQuestion = {
    ...question,
    prompt: 'Câu hỏi được chụp bằng tiếng Việt.',
    content_locale: 'vi',
    options: [{ option_id: 11, option_label: 'A', option_text: 'Phương án A' }],
  }
  await mount('mcq', viQuestion)
  const option = await screen.findByRole('radio', { name: 'A: Phương án A' })
  await userEvent.click(option)
  await act(() => setLocale('en'))
  expect(screen.getByText('Câu hỏi được chụp bằng tiếng Việt.')).toBeInTheDocument()
  expect(option).toBeChecked()
  await act(() => setLocale('vi'))
  expect(screen.getByText('Câu hỏi được chụp bằng tiếng Việt.')).toBeInTheDocument()
  expect(option).toBeChecked()
  expect(api.get).toHaveBeenCalledTimes(2)
})
it('keeps SQL output verbatim and does not rerun SQL when switching locale', async () => {
  await mount('sql')
  fireEvent.change(await screen.findByRole('textbox'), { target: { value: 'SELECT 1234.5' } })
  expect(screen.getByRole('textbox')).toHaveValue('SELECT 1234.5')
  api.post.mockResolvedValue({ data: { success: true, columns: ['numeric_value'], rows: [[1234.5]], row_count: 1, execution_time_ms: 1.5 } })
  await userEvent.click(screen.getByRole('button', { name: 'Run in sandbox' }))
  expect(await screen.findByText('1 row · 1.5 ms')).toBeInTheDocument()
  await act(() => setLocale('vi'))
  expect(screen.getByText('1 hàng · 1,5 ms')).toBeInTheDocument()
  expect(screen.getByRole('cell')).toHaveTextContent('1234.5')
  expect(api.post).toHaveBeenCalledExactlyOnceWith('/sessions/42/sql-run', { question_id: 1, sql: 'SELECT 1234.5' })
})

it('displays a reviewed projection while preserving the selected answer and restores the original', async () => {
  await mount()
  await userEvent.click(await screen.findByRole('radio', { name: 'A: SELECT' }))
  api.get.mockImplementation((url, config) => Promise.resolve({ data: {
    ...base, locale: 'en', current_question: { ...question,
      prompt: config?.params?.display_locale === 'vi' ? 'Chọn câu lệnh.' : 'Original question',
      content_locale: config?.params?.display_locale || 'en',
    },
  } }))
  await act(() => setLocale('vi'))
  expect(await screen.findByText('Chọn câu lệnh.')).toBeInTheDocument()
  expect(screen.getByRole('radio', { name: 'A: SELECT' })).toBeChecked()
  fireEvent(document, new Event('visibilitychange'))
  await waitFor(() => expect(api.get).toHaveBeenLastCalledWith('/sessions/42', { params: { display_locale: 'vi' } }))
  expect(await screen.findByText('Chọn câu lệnh.')).toBeInTheDocument()
  await act(() => setLocale('en'))
  expect(await screen.findByText('Original question')).toBeInTheDocument()
  expect(screen.getByRole('radio', { name: 'A: SELECT' })).toBeChecked()
  expect(api.post).not.toHaveBeenCalled()
})

it('keeps the question and answer on a display-language failure and allows a safe retry', async () => {
  await mount()
  await userEvent.click(await screen.findByRole('radio', { name: 'A: SELECT' }))
  api.get.mockRejectedValue(new Error('offline'))
  await act(() => setLocale('vi'))
  expect(await screen.findByText(/Không tải được ngôn ngữ đã chọn/)).toBeInTheDocument()
  expect(screen.getByText('Original question')).toBeInTheDocument()
  expect(screen.getByRole('radio', { name: 'A: SELECT' })).toBeChecked()
  api.get.mockResolvedValue({ data: { ...base, current_question: { ...question, prompt: 'Chọn câu lệnh.', content_locale: 'vi' } } })
  await userEvent.click(screen.getByRole('button', { name: 'Thử lại' }))
  expect(await screen.findByText('Chọn câu lệnh.')).toBeInTheDocument()
  expect(screen.getByRole('radio', { name: 'A: SELECT' })).toBeChecked()
  expect(api.post).not.toHaveBeenCalled()
})
it('localizes sandbox error codes and finish confirmation without resetting the dialog', async () => {
  await mount('sql')
  fireEvent.change(await screen.findByRole('textbox'), { target: { value: 'DELETE FROM t' } })
  api.post.mockResolvedValue({ data: { success: false, error_type: 'not_a_select', error_message: 'untrusted raw text' } })
  await userEvent.click(screen.getByRole('button', { name: 'Run in sandbox' }))
  await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Only a single read-only SELECT'))
  await userEvent.click(screen.getByRole('button', { name: 'Finish assessment' }))
  const dialog = screen.getByRole('dialog')
  await act(() => setLocale('vi'))
  expect(screen.getByRole('dialog', { name: 'Nộp bài?' })).toBe(dialog)
  expect(dialog).toHaveTextContent('Bạn đã nộp 0 câu trả lời.')
  await userEvent.keyboard('{Escape}')
  expect(screen.getByRole('alert')).toHaveTextContent('Mỗi lần chỉ chạy một câu lệnh SELECT để đọc dữ liệu.')
  expect(screen.queryByText('untrusted raw text')).not.toBeInTheDocument()
})
