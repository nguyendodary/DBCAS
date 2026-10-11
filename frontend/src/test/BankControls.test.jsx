import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import api from '../api'
import AdminQuestionsPage from '../pages/admin/AdminQuestionsPage'
import AdminAssessmentsPage from '../pages/admin/AdminAssessmentsPage'

vi.mock('../api', () => ({ default: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), put: vi.fn(), delete: vi.fn() }, apiMessage: (e) => e.message }))
const row = { question_id: 7, question_type: 'mcq', prompt: 'Projection', difficulty_level: 1, status: 'validated', source: 'bank', concepts: [{ concept_id: 3, concept_code: 'SQL-SELECT', concept_name: 'SELECT', confirmed: true }] }
beforeEach(() => { vi.resetAllMocks(); api.get.mockResolvedValue({ data: [row] }) })

it('filters by real concept IDs and sends the selected value to the backend', async () => {
  render(<AdminQuestionsPage />)
  await screen.findByText('Projection')
  await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Filter by concept' }), '3')
  await waitFor(() => expect(api.get).toHaveBeenLastCalledWith('/admin/questions', expect.objectContaining({ params: { concept_id: '3' } })))
})

it('debounces text search and cancels superseded requests', async () => {
  render(<AdminQuestionsPage />)
  await screen.findByText('Projection')
  const firstSignal = api.get.mock.calls[0][1].signal
  await userEvent.type(screen.getByRole('textbox', { name: 'Search prompt' }), 'normalization')
  await waitFor(() => expect(api.get).toHaveBeenLastCalledWith('/admin/questions', expect.objectContaining({ params: { q: 'normalization' } })))
  expect(firstSignal.aborted).toBe(true)
  expect(api.get.mock.calls.filter(([, options]) => options.params.q)).toHaveLength(1)
})

it('labels assessment fields and fixes the documented question and time limits', async () => {
  api.get.mockResolvedValue({ data: [] })
  render(<AdminAssessmentsPage />)
  await userEvent.click(screen.getByRole('button', { name: 'New assessment' }))
  expect(screen.getByRole('textbox', { name: 'Assessment title' })).toBeInTheDocument()
  expect(screen.getByRole('textbox', { name: 'Assessment description' })).toBeInTheDocument()
  expect(screen.getByRole('combobox', { name: 'Target concept 1' })).toBeInTheDocument()
  expect(screen.getByRole('spinbutton', { name: 'Maximum difficulty for concept 1' })).toBeInTheDocument()
  expect(screen.getByRole('spinbutton', { name: 'minutes' })).toHaveValue(60)
  expect(screen.getByRole('spinbutton', { name: 'max q' })).toHaveAttribute('readonly')
  expect(screen.getByRole('spinbutton', { name: 'mcq' })).toHaveValue(10)
  expect(screen.getByRole('spinbutton', { name: 'sql' })).toHaveValue(2)
  expect(screen.getByRole('spinbutton', { name: 'essay' })).toHaveValue(1)
})
