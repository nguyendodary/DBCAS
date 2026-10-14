import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, afterEach, expect, it, vi } from 'vitest'
import api from '../api'
import { i18n, setLocale, dateOnly } from '../i18n'
import { useLocalizedValidation } from '../i18n/validation'
import AssessmentsPage from '../pages/AssessmentsPage'
import HistoryPage from '../pages/HistoryPage'
import AdminQuestionsPage from '../pages/admin/AdminQuestionsPage'
import AdminAccountsPage from '../pages/admin/AdminAccountsPage'
import AdminCurriculumPage from '../pages/admin/AdminCurriculumPage'
vi.mock('../api', async (original) => ({ ...(await original()), default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), patch: vi.fn(), delete: vi.fn() } }))
beforeEach(async () => { vi.clearAllMocks(); await i18n.changeLanguage('en') })
afterEach(async () => { await act(() => i18n.changeLanguage('en')); localStorage.clear() })
it('localizes the assessment list and preserves its real resume route and progress', async () => {
  api.get.mockImplementation(url => Promise.resolve({ data: url === '/assessments' ? [{ assessment_id: 3, title: 'Original title', duration_min: 60, max_questions: 13, concept_count: 2 }] : [{ session_id: 9, assessment_id: 3, status: 'in_progress', answered_count: 4, started_at: '2026-10-10T10:00:00Z' }] }))
  render(<MemoryRouter><AssessmentsPage /></MemoryRouter>)
  await screen.findByText('Original title')
  await act(() => setLocale('vi'))
  expect(screen.getByRole('heading', { name: 'Bài đánh giá', level: 1 })).toBeInTheDocument()
  expect(screen.getByText('60 phút')).toBeInTheDocument()
  expect(screen.getByText('Đã trả lời 4 câu · Tối đa 13 câu')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Tiếp tục làm bài' })).toBeInTheDocument()
  expect(api.get).toHaveBeenCalledTimes(2)
})
it('localizes history results without changing concept content or evidence links', async () => {
  api.get.mockResolvedValue({ data: [{ session_id: 9, assessment_title: 'Original title', status: 'completed', started_at: '2026-10-10T10:00:00Z', answered_count: 4, served_count: 4, overall_result_pct: '62.50', concepts: [{ concept_id: 3, concept_name: 'Original concept', competency_pct: '62.50', target_pct: null }] }] })
  render(<MemoryRouter><HistoryPage /></MemoryRouter>)
  await screen.findByText('Original title')
  await act(() => setLocale('vi'))
  expect(screen.getByText('Kết quả: 62,5%')).toBeInTheDocument()
  expect(screen.getByText('Original concept: 62,50% · chưa có mức chuẩn')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Xem kết quả' })).toHaveAttribute('href', '/history/9')
  expect(api.get).toHaveBeenCalledTimes(1)
  expect(dateOnly('2026-10-11')).toContain('11')
})
it('preserves question editor text and domain filter values while switching locale', async () => {
  api.get.mockResolvedValue({ data: [] })
  render(<AdminQuestionsPage />)
  await userEvent.click(screen.getByRole('button', { name: 'New question' }))
  fireEvent.change(screen.getByRole('textbox', { name: 'Question prompt' }), { target: { value: 'Original authored question' } })
  await act(() => setLocale('vi'))
  expect(screen.getByRole('textbox', { name: 'Nội dung câu hỏi' })).toHaveValue('Original authored question')
  expect(screen.getByRole('textbox', { name: 'Nội dung lựa chọn 1' })).toHaveValue('Option A')
  await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Lọc theo loại' }), 'essay')
  await waitFor(() => expect(api.get).toHaveBeenLastCalledWith('/admin/questions', expect.objectContaining({ params: { question_type: 'essay' } })))
  expect(within(screen.getByRole('combobox', { name: 'Lọc theo loại' })).getByRole('option', { name: 'Tự luận' })).toHaveValue('essay')
})
it('submits the existing Administrator role and localizes an already visible notice', async () => {
  api.get.mockResolvedValue({ data: [] }); api.post.mockResolvedValue({ data: {} })
  render(<AdminAccountsPage />)
  await userEvent.type(screen.getByLabelText('Full name'), 'Local test admin')
  await userEvent.type(screen.getByLabelText('Email address'), 'local@test.dev')
  await userEvent.type(screen.getByLabelText('Temporary password'), 'TestOnly123!')
  await userEvent.click(screen.getByRole('button', { name: 'Provision', exact: true }))
  expect(await screen.findByRole('status')).toHaveTextContent('Provisioned local@test.dev')
  await act(() => setLocale('vi'))
  expect(screen.getByRole('status')).toHaveTextContent('Đã tạo tài khoản local@test.dev')
  expect(api.post).toHaveBeenCalledWith('/admin/accounts', { name: 'Local test admin', email: 'local@test.dev', password: 'TestOnly123!', role: 'Administrator' })
  expect(screen.getByRole('option', { name: 'Quản trị viên' })).toHaveValue('Administrator')
})
it('localizes curriculum validation without sending invalid IDs', async () => {
  api.get.mockImplementation(url => Promise.resolve({ data: url === '/admin/concepts' ? [{ concept_id: 1, concept_code: 'SELECT', concept_name: 'Original name', difficulty_level: 1 }] : url === '/concepts/graph' ? { nodes: [{ concept_id: 1, prerequisites: [] }] } : [] }))
  render(<AdminCurriculumPage />)
  const ids = await screen.findByRole('textbox', { name: 'Prerequisites for SELECT' })
  fireEvent.change(ids, { target: { value: '2,2' } })
  await userEvent.click(screen.getByRole('button', { name: 'Save', exact: true }))
  await act(() => setLocale('vi'))
  expect(screen.getByRole('alert')).toHaveTextContent('Nhập ID khái niệm là số nguyên dương, không trùng nhau')
  expect(api.put).not.toHaveBeenCalled()
  expect(ids).toHaveValue('2,2')
})
function ValidationForm() { useLocalizedValidation(); return <form><input aria-label="Email" type="email" required /><button>Submit</button></form> }
it.each(['questions', 'curriculum'])('updates a visible %s rejection notice without repeating the mutation', async (workspace) => {
  api.get.mockImplementation(url => Promise.resolve({ data: url === '/admin/questions' ? [{
    question_id: 5, question_type: 'mcq', prompt: 'Original authored question', status: 'draft', source: 'bank', difficulty_level: 1,
    ai_review: { status: 'pending', difficulty_level: 2, evaluation_criteria: 'Original criteria' },
  }] : url === '/admin/clos' ? [{ clo_id: 1, clo_code: 'CLO1', title: 'Original outcome', concepts: [{ concept_id: 3, concept_code: 'KEYS', concept_name: 'Original concept', status: 'pending', mapping_source: 'ai' }] }]
    : url === '/concepts/graph' ? { nodes: [] } : [] }))
  api.post.mockResolvedValue({ data: {} }); api.delete.mockResolvedValue({ data: {} })
  render(workspace === 'questions' ? <AdminQuestionsPage /> : <AdminCurriculumPage />)
  await userEvent.click(await screen.findByRole('button', { name: workspace === 'questions' ? 'Reject suggestion' : 'Reject', exact: true }))
  expect(await screen.findByRole('status')).toHaveTextContent('Suggestion rejected.')
  const calls = api.get.mock.calls.length
  await act(() => setLocale('vi'))
  expect(screen.getByRole('status')).toHaveTextContent('Đã từ chối đề xuất.')
  expect(api.get).toHaveBeenCalledTimes(calls)
  if (workspace === 'questions') {
    expect(api.post).toHaveBeenCalledExactlyOnceWith('/admin/questions/5/ai-review', { decision: 'rejected' })
    expect(api.delete).not.toHaveBeenCalled()
  } else {
    expect(api.delete).toHaveBeenCalledExactlyOnceWith('/admin/clos/1/concepts/3')
    expect(api.post).not.toHaveBeenCalled()
  }
})
it('localizes native validation while preserving constraints and clearing corrected errors', async () => {
  render(<ValidationForm />)
  const input = screen.getByLabelText('Email')
  fireEvent.invalid(input)
  expect(input.validationMessage).toBe('Please fill out this field.')
  await act(() => setLocale('vi'))
  expect(input.validationMessage).toBe('Vui lòng nhập thông tin này.')
  fireEvent.input(input, { target: { value: 'bad-email' } }); fireEvent.invalid(input)
  expect(input.validationMessage).toBe('Nhập địa chỉ email hợp lệ.')
  fireEvent.input(input, { target: { value: 'valid@test.dev' } })
  expect(input.checkValidity()).toBe(true)
})
