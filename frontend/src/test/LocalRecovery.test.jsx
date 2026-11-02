import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, it, vi } from 'vitest'
import ErrorBoundary from '../components/ErrorBoundary'
import AssessmentPoolEditor from './historical/AssessmentPoolEditor'
import api from '../api'

vi.mock('../api', () => ({ default: { get: vi.fn(), put: vi.fn() }, apiMessage: error => error.message }))
afterEach(() => vi.restoreAllMocks())

it('contains unexpected render failures and offers one retry without showing internal errors', async () => {
  vi.spyOn(console, 'error').mockImplementation(() => {})
  const retry = vi.fn()
  function Broken() { throw new Error('private internal traceback') }
  render(<ErrorBoundary onRetry={retry}><Broken /></ErrorBoundary>)
  expect(screen.getByRole('alert')).not.toHaveTextContent('private internal traceback')
  await userEvent.click(screen.getByRole('button', { name: 'Retry' }))
  expect(retry).toHaveBeenCalledOnce()
})

it('saves a complete question selection through the real pool API contract', async () => {
  const questions = Array.from({ length: 13 }, (_, index) => ({ question_id: index + 1,
    question_type: index < 10 ? 'mcq' : index < 12 ? 'sql' : 'essay', status: 'validated',
    prompt: `Question ${index + 1}`, difficulty_level: 1, concepts: [{ concept_id: 1, confirmed: true }] }))
  api.get.mockImplementation(path => Promise.resolve({ data: path === '/admin/questions' ? questions
    : path.endsWith('/questions') ? { question_ids: [] } : { concepts: [{ concept_id: 1, min_difficulty: 1, max_difficulty: 5 }] } }))
  api.put.mockResolvedValue({ data: { question_ids: questions.map(question => question.question_id) } })
  const saved = vi.fn()
  render(<AssessmentPoolEditor assessment={{ assessment_id: 8, title: 'Demo' }} onClose={vi.fn()} onSaved={saved} />)
  await userEvent.click(await screen.findByLabelText("Use all eligible questions for this assessment's skills"))
  expect(screen.getByRole('button', { name: 'Save changes' })).toBeDisabled()
  await userEvent.click(screen.getByRole('button', { name: 'Select all visible questions' }))
  await userEvent.click(screen.getByRole('button', { name: 'Save changes' }))
  expect(api.put).toHaveBeenCalledWith('/admin/assessments/8/questions', { question_ids: questions.map(question => question.question_id) })
  expect(saved).toHaveBeenCalledOnce()
})
