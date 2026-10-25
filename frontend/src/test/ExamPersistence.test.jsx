import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import api from '../api'
import ExamPage from '../pages/ExamPage'

vi.mock('../api', () => ({ default: { get: vi.fn(), post: vi.fn(), put: vi.fn() }, apiMessage: (e, fallback) => e?.message || fallback }))

const question = { question_id: 1, question_type: 'mcq', prompt: 'Choose a projection clause', difficulty_level: 1, points: '1', concepts: [], options: [{ option_id: 11, option_label: 'A', option_text: 'SELECT' }, { option_id: 12, option_label: 'B', option_text: 'DELETE' }] }
const state = { session_id: 42, assessment_title: 'Draft test', status: 'in_progress', served_count: 1, answered_count: 0, max_questions: 13, remaining_seconds: 3600, current_question: question }

function mount() {
  return render(<MemoryRouter initialEntries={['/exam/42']}><Routes><Route path="/exam/:sessionId" element={<ExamPage />} /><Route path="/history/:sessionId" element={<p>Assessment results</p>} /><Route path="/dashboard" element={<p>Results dashboard</p>} /></Routes></MemoryRouter>)
}

beforeEach(() => {
  vi.resetAllMocks()
  sessionStorage.clear()
  api.get.mockResolvedValue({ data: state })
  api.put.mockImplementation((_, body) => Promise.resolve({ data: { revision: body.revision } }))
  api.post.mockResolvedValue({ data: { status: 'completed' } })
})
afterEach(() => { vi.restoreAllMocks(); vi.useRealTimers() })

it('restores the saved MCQ option on resume without grading it', async () => {
  api.get.mockResolvedValue({ data: { ...state, current_question: { ...question, draft: { selected_option_id: 11 }, draft_revision: 3 } } })
  mount()
  expect(await screen.findByRole('radio', { name: 'A: SELECT' })).toBeChecked()
  expect(api.post).not.toHaveBeenCalled()
  expect(api.put).not.toHaveBeenCalled()
})

it('restores every selected option of a multiple-answer draft', async () => {
  api.get.mockResolvedValue({ data: { ...state, current_question: { ...question, multiple_answers: true, draft: { selected_option_ids: [11, 12] }, draft_revision: 3 } } })
  mount()
  expect(await screen.findByRole('checkbox', { name: 'A: SELECT' })).toBeChecked()
  expect(screen.getByRole('checkbox', { name: 'B: DELETE' })).toBeChecked()
  await userEvent.click(screen.getByRole('checkbox', { name: 'B: DELETE' }))
  await waitFor(() => expect(api.put).toHaveBeenCalledWith('/sessions/42/draft', { question_id: 1, selected_option_ids: [11], revision: 4 }))
  expect(api.post).not.toHaveBeenCalled()
})

it.each(['sql', 'essay'])('restores a saved %s draft', async (type) => {
  const field = type === 'sql' ? 'sql_answer' : 'essay_answer'
  const saved = type === 'sql' ? 'SELECT id FROM t' : 'A normalized relation satisfies 3NF.'
  api.get.mockResolvedValue({ data: { ...state, current_question: { ...question, question_type: type, draft: { [field]: saved }, draft_revision: 2 } } })
  mount()
  expect(await screen.findByRole('textbox')).toHaveValue(saved)
})

it('autosaves an ungraded draft and displays save completion', async () => {
  mount()
  await userEvent.click(await screen.findByText('SELECT'))
  await waitFor(() => expect(api.put).toHaveBeenCalledWith('/sessions/42/draft', { question_id: 1, selected_option_id: 11, revision: 1 }))
  expect(await screen.findByText('Draft saved')).toBeInTheDocument()
  expect(api.post).not.toHaveBeenCalled()
})

it('does not claim a draft was saved on a fresh unanswered question', async () => {
  const { container } = mount()
  await screen.findByText('Choose a projection clause')
  const status = container.querySelector('.save-status')
  expect(status).toBeInTheDocument()
  expect(status.textContent.trim()).toBe('')
})

it('shows the saved status on a question that already carries a draft', async () => {
  api.get.mockResolvedValue({ data: { ...state, current_question: { ...question, draft: { selected_option_id: 11 }, draft_revision: 3 } } })
  const { container } = mount()
  expect(await screen.findByText('Draft saved')).toBeInTheDocument()
  expect(container.querySelector('.save-status')).toHaveTextContent('Draft saved')
})

it('flushes the current draft, shows wait feedback, then opens results', async () => {
  const order=[]
  api.put.mockImplementation((_, body) => { order.push('save'); return Promise.resolve({ data: { revision: body.revision } }) })
  api.post.mockImplementation(() => { order.push('finish'); return Promise.resolve({ data: { status: 'completed' } }) })
  mount()
  await userEvent.click(await screen.findByText('SELECT'))
  await userEvent.click(screen.getByRole('button', { name: 'Finish assessment' }))
  await userEvent.click(screen.getByRole('button', { name: 'Yes, finish' }))
  expect(await screen.findByText('Assessment results')).toBeInTheDocument()
  expect(order).toEqual(['save', 'finish'])
})

it('recovers the authoritative next question after a lost submission response', async () => {
  api.get.mockResolvedValueOnce({ data: state }).mockResolvedValueOnce({ data: { ...state, answered_count: 1, served_count: 2, current_question: { ...question, question_id: 2, prompt: 'Recovered next question' } } })
  api.post.mockRejectedValueOnce(new Error('Connection interrupted'))
  mount()
  await userEvent.click(await screen.findByText('SELECT'))
  await userEvent.click(screen.getByRole('button', { name: 'Next question' }))
  expect(await screen.findByText('Recovered next question')).toBeInTheDocument()
  expect(screen.queryByText('Choose a projection clause')).not.toBeInTheDocument()
  expect(screen.getByText('Answer submitted. Your session has been restored.')).toBeInTheDocument()
})

it('finishes at authoritative expiry without saving a late UI draft', async () => {
  api.get.mockResolvedValue({ data: { ...state, remaining_seconds: 0, server_now: '2030-01-01T01:00:00Z', expires_at: '2030-01-01T01:00:00Z' } })
  mount()
  expect(await screen.findByText('Assessment results')).toBeInTheDocument()
  expect(api.post).toHaveBeenCalledWith('/sessions/42/finish')
  expect(api.put).not.toHaveBeenCalled()
})

it('does not finalize early during the final fractional second', async () => {
  let elapsed = 0
  vi.spyOn(performance, 'now').mockImplementation(() => elapsed)
  vi.useFakeTimers()
  api.get.mockResolvedValue({ data: { ...state, server_now: '2030-01-01T00:00:00.000Z', expires_at: '2030-01-01T00:00:00.900Z' } })
  mount()
  await act(async () => { await Promise.resolve() })
  elapsed = 500
  await act(async () => { vi.advanceTimersByTime(500) })
  expect(api.post).not.toHaveBeenCalled()
  expect(screen.getByText('00:01')).toBeInTheDocument()
  elapsed = 1000
  await act(async () => { vi.advanceTimersByTime(500); await Promise.resolve() })
  expect(api.post).toHaveBeenCalledWith('/sessions/42/finish')
})

it('uses elapsed monotonic time after timer callback drift and warns once', async () => {
  let now=100
  vi.spyOn(performance, 'now').mockImplementation(() => now)
  api.get.mockResolvedValue({ data: { ...state, remaining_seconds: 601 } })
  mount()
  await screen.findByText('Choose a projection clause')
  now += 61_000
  await waitFor(() => expect(screen.getByLabelText('Time remaining')).toHaveTextContent('09:00'))
  expect(screen.getByRole('alert')).toHaveTextContent('10 minutes')
  now += 241_000
  await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('5 minutes'))
  expect(sessionStorage.getItem('dbcas-time-warning:42:10')).toBe('shown')
  expect(sessionStorage.getItem('dbcas-time-warning:42:5')).toBe('shown')
})

it('shows pending grading without a fabricated score', async () => {
  api.post.mockResolvedValue({ data: { answer: { grading_status: 'pending', score: null }, state: { ...state, answered_count: 1, current_question: null } } })
  mount()
  await userEvent.click(await screen.findByText('SELECT'))
  await userEvent.click(screen.getByRole('button', { name: 'Next question' }))
  expect(await screen.findByText('Answer saved. Grading is pending and will retry automatically.')).toBeInTheDocument()
  expect(screen.queryByText(/scored null/)).not.toBeInTheDocument()
})
