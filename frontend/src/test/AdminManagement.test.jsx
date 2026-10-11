import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import api from '../api'
import AdminQuestionsPage from '../pages/admin/AdminQuestionsPage'
import AdminAssessmentsPage from '../pages/admin/AdminAssessmentsPage'
import AdminCurriculumPage from '../pages/admin/AdminCurriculumPage'

vi.mock('../api', () => ({
  default: { get: vi.fn(), delete: vi.fn(), post: vi.fn(), patch: vi.fn() },
  apiMessage: (e, fb) => e?.response?.data?.error?.message || e?.message || fb,
}))

beforeEach(() => {
  vi.clearAllMocks()
  api.delete.mockResolvedValue({ data: {} })
})

it('keeps the question bank visible and requires confirmation before deletion', async () => {
  api.get.mockResolvedValue({ data: [{
    question_id: 7, question_type: 'mcq', difficulty_level: 1, status: 'draft',
    source: 'bank', prompt: 'Which query returns rows?', concepts: [],
  }] })
  render(<AdminQuestionsPage />)
  expect(await screen.findByText('Which query returns rows?')).toBeInTheDocument()
  expect(screen.queryByText('New question', { selector: 'h2' })).not.toBeInTheDocument()
  const deleteButton = screen.getByRole('button', { name: 'Delete' })
  await userEvent.click(deleteButton)
  expect(screen.getByRole('dialog', { name: 'Delete this question?' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Cancel' })).toHaveFocus()
  expect(api.delete).not.toHaveBeenCalled()
  await userEvent.keyboard('{Escape}')
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  expect(deleteButton).toHaveFocus()
  expect(api.delete).not.toHaveBeenCalled()
  await userEvent.click(deleteButton)
  await userEvent.click(screen.getByRole('button', { name: 'Delete question' }))
  await waitFor(() => expect(api.delete).toHaveBeenCalledWith('/admin/questions/7'))
})

it('requires confirmation before removing a draft assessment', async () => {
  api.get.mockImplementation((url) => Promise.resolve({ data: url === '/admin/concepts' ? [] : [{
    assessment_id: 4, title: 'Database basics', status: 'draft', max_questions: 8,
    duration_min: 30, target_count: 2, session_count: 0,
  }] }))
  render(<AdminAssessmentsPage />)
  expect(await screen.findByText('Database basics')).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Delete' }))
  expect(screen.getByRole('dialog', { name: 'Delete this assessment?' })).toBeInTheDocument()
  expect(api.delete).not.toHaveBeenCalled()
  await userEvent.click(screen.getByRole('button', { name: 'Delete assessment' }))
  await waitFor(() => expect(api.delete).toHaveBeenCalledWith('/admin/assessments/4'))
})

it('keeps a failed question deletion open with its API error', async () => {
  api.get.mockResolvedValue({ data: [{
    question_id: 7, question_type: 'mcq', difficulty_level: 1, status: 'draft',
    source: 'bank', prompt: 'Which query returns rows?', concepts: [],
  }] })
  api.delete.mockRejectedValueOnce(new Error('Question is used by a session'))
  render(<AdminQuestionsPage />)
  await screen.findByText('Which query returns rows?')
  await userEvent.click(screen.getByRole('button', { name: 'Delete' }))
  const dialog = screen.getByRole('dialog', { name: 'Delete this question?' })
  await userEvent.click(within(dialog).getByRole('button', { name: 'Delete question' }))
  expect(await within(dialog).findByRole('alert')).toHaveTextContent('Question is used by a session')
  expect(dialog).toBeInTheDocument()
})

it('keeps curriculum form values on a failed save and confirms concept removal', async () => {
  api.get.mockImplementation((url) => Promise.resolve({ data: url === '/admin/concepts' ? [{
    concept_id: 3, concept_code: 'SQL-SELECT', concept_name: 'SELECT basics', difficulty_level: 1,
  }] : url === '/concepts/graph' ? { nodes: [] } : [] }))
  api.post.mockRejectedValue(new Error('Save failed'))
  render(<AdminCurriculumPage />)
  expect(await screen.findByText(/SELECT basics/)).toBeInTheDocument()
  await userEvent.type(screen.getByRole('textbox', { name: 'Concept code' }), 'SQL-NEW')
  await userEvent.type(screen.getByRole('textbox', { name: 'Concept name' }), 'New concept')
  await userEvent.type(screen.getByRole('textbox', { name: 'Subject area' }), 'Querying')
  await userEvent.click(screen.getByRole('button', { name: 'Add concept' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Save failed')
  expect(screen.getByRole('textbox', { name: 'Concept name' })).toHaveValue('New concept')
  await userEvent.click(screen.getByRole('button', { name: 'Delete' }))
  expect(screen.getByRole('dialog', { name: 'Delete this concept?' })).toBeInTheDocument()
  expect(api.delete).not.toHaveBeenCalled()
})
