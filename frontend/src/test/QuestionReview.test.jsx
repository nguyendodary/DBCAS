import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import api from '../api'
import AdminQuestionsPage from '../pages/admin/AdminQuestionsPage'

vi.mock('../api', () => ({ default: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() }, apiMessage: (e) => e.message }))
beforeEach(() => {
  vi.resetAllMocks()
  api.get.mockResolvedValue({ data: [{ question_id: 5, question_type: 'mcq', prompt: 'Identify a candidate key', difficulty_level: 1, points: '1', status: 'draft', source: 'bank',
    concepts: [{ concept_id: 3, concept_code: 'KEYS', confirmed: false, review_status: 'rejected' }],
    ai_review: { status: 'pending', difficulty_level: 3, evaluation_criteria: 'Explain minimal uniqueness' },
  }] })
  api.post.mockResolvedValue({ data: {} })
})
it('keeps difficulty and criteria pending until explicit approval', async () => {
  render(<AdminQuestionsPage />)
  await screen.findByText('Suggested difficulty: 3')
  expect(api.post).not.toHaveBeenCalled()
  await userEvent.click(screen.getByRole('button', { name: 'Approve difficulty and criteria' }))
  await waitFor(() => expect(api.post).toHaveBeenCalledWith('/admin/questions/5/ai-review', { decision: 'confirmed', apply_difficulty: true }))
})
it('supports explicit rejection and displays rejected tags without pending actions', async () => {
  render(<AdminQuestionsPage />)
  expect(await screen.findByText('KEYS (Rejected)')).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Confirm', exact: true })).not.toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Reject suggestion' }))
  await waitFor(() => expect(api.post).toHaveBeenCalledWith('/admin/questions/5/ai-review', { decision: 'rejected' }))
})
