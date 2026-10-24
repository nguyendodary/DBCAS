import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { beforeEach, expect, it, vi } from 'vitest'
import api from '../api'
import ExamPage from '../pages/ExamPage'
import { setLocale } from '../i18n'

vi.mock('../api', async original => ({ ...(await original()), default: { get: vi.fn(), put: vi.fn(), post: vi.fn() } }))
const previous = { seq_no: 1, question_id: 1, question_type: 'mcq', prompt: 'Saved SQL question', content_locale: 'en',
  selected_option_id: 11, options: [{ option_id: 11, option_label: 'A', option_text: 'SELECT' }] }
const current = { seq_no: 2, question_id: 2, question_type: 'sql', prompt: 'Write a query', points: '1',
  difficulty_level: 3, content_locale: 'en', concepts: [], draft_revision: 0 }
const state = { session_id: 42, status: 'in_progress', assessment_title: 'SQL assessment', locale: 'en',
  max_questions: 3, served_count: 2, answered_count: 1, remaining_seconds: 3600, current_question: current }
beforeEach(async () => {
  vi.clearAllMocks(); sessionStorage.clear(); await setLocale('en')
  api.get.mockImplementation((url, config) => Promise.resolve({ data: url.endsWith('/questions')
    ? [{ ...previous, prompt: config?.params?.display_locale === 'vi' ? 'Câu hỏi SQL đã lưu' : previous.prompt }, current] : state }))
  api.put.mockImplementation((_, body) => Promise.resolve({ data: { revision: body.revision } }))
})
async function mount() {
  await act(async () => render(<MemoryRouter initialEntries={['/exam/42']}><Routes><Route path="/exam/:sessionId" element={<ExamPage />} /></Routes></MemoryRouter>))
  await screen.findByRole('textbox')
}
it('revisits a saved answer without losing the current SQL draft or resetting the timer', async () => {
  await mount()
  const editor = screen.getByRole('textbox')
  const sql = "SELECT 'Mã sinh viên', employee_id FROM employee;"
  fireEvent.change(editor, { target: { value: sql } })
  await userEvent.click(screen.getByRole('button', { name: 'Go to question 1' }))
  expect(await screen.findByText('Saved SQL question')).toBeVisible()
  expect(screen.getByText('Your answer', { exact: true })).toBeVisible()
  expect(screen.getByText('Your submitted answer is saved. Submitted answers cannot be changed.')).toBeVisible()
  expect(screen.getByRole('button', { name: 'Go to question 3' })).toBeDisabled()
  expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
  expect(api.put).toHaveBeenCalledWith('/sessions/42/draft', { question_id: 2, revision: 1, sql_answer: sql })
  await act(() => setLocale('vi'))
  expect(await screen.findByText('Câu hỏi SQL đã lưu')).toBeVisible()
  await userEvent.click(screen.getByRole('button', { name: 'Trở về câu hỏi hiện tại' }))
  expect(screen.getByRole('textbox')).toBe(editor)
  expect(editor).toHaveValue(sql)
  expect(screen.getByLabelText('Thời gian còn lại')).toHaveTextContent(/59:5\d|60:00/)
  expect(api.post).not.toHaveBeenCalled()
  await act(() => setLocale('en'))
})
it('keeps the saved current draft on a history-load failure and supports a retry', async () => {
  await mount()
  api.get.mockRejectedValueOnce(new Error('Connection interrupted'))
  await userEvent.click(screen.getByRole('button', { name: 'Go to question 1' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Could not load the session')
  await userEvent.click(screen.getByRole('button', { name: 'Retry', exact: true }))
  expect(await screen.findByText('Saved SQL question')).toBeVisible()
  await userEvent.click(screen.getByRole('button', { name: 'Return to current question' }))
  expect(screen.getByRole('textbox')).toHaveValue('')
  expect(api.post).not.toHaveBeenCalled()
})
it('stays with the current answer when its draft cannot be saved before navigation', async () => {
  await mount()
  api.put.mockRejectedValue(new Error('Draft save interrupted'))
  fireEvent.change(screen.getByRole('textbox'), { target: { value: 'SELECT 1;' } })
  await userEvent.click(screen.getByRole('button', { name: 'Go to question 1' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('The draft could not be saved. Retry before leaving this page.')
  expect(screen.getByRole('textbox')).toHaveValue('SELECT 1;')
  expect(api.get).not.toHaveBeenCalledWith('/sessions/42/questions', expect.anything())
})

it('keeps the latest navigation choice when a slower draft save completes afterward', async () => {
  await mount()
  let completeSave
  api.put.mockImplementation(() => new Promise(resolve => { completeSave = resolve }))
  fireEvent.change(screen.getByRole('textbox'), { target: { value: 'SELECT employee_id FROM employee;' } })
  fireEvent.click(screen.getByRole('button', { name: 'Go to question 1' }))
  await waitFor(() => expect(completeSave).toBeTypeOf('function'))
  fireEvent.click(screen.getByRole('button', { name: 'Go to question 2' }))
  await act(async () => { completeSave({ data: { revision: 1 } }) })
  expect(screen.getByRole('textbox')).toHaveValue('SELECT employee_id FROM employee;')
  expect(screen.queryByText('Saved SQL question')).not.toBeInTheDocument()
  expect(api.get).not.toHaveBeenCalledWith('/sessions/42/questions', expect.anything())
})
