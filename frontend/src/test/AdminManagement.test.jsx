import { act, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import api from '../api'
import AdminQuestionsPage from '../pages/admin/AdminQuestionsPage'
import AdminAssessmentsPage from '../pages/admin/AdminAssessmentsPage'
import AdminCurriculumPage from '../pages/admin/AdminCurriculumPage'
import postgresPack from '../../../db/postgres_knowledge_pack.json'
import translations from '../../../db/question_translations_vi.json'

vi.mock('../api', () => ({
  default: { get: vi.fn(), delete: vi.fn(), post: vi.fn(), put: vi.fn(), patch: vi.fn() },
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
  const row = screen.getByText('Which query returns rows?').closest('li')
  await userEvent.click(within(row).getByRole('button', { name: 'Actions' }))
  await userEvent.click(screen.getByRole('menuitem', { name: 'Delete' }))
  expect(screen.getByRole('dialog', { name: 'Delete this question?' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Cancel' })).toHaveFocus()
  expect(api.delete).not.toHaveBeenCalled()
  await userEvent.keyboard('{Escape}')
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  expect(api.delete).not.toHaveBeenCalled()
  await userEvent.click(within(row).getByRole('button', { name: 'Actions' }))
  await userEvent.click(screen.getByRole('menuitem', { name: 'Delete' }))
  await userEvent.click(screen.getByRole('button', { name: 'Delete question' }))
  await waitFor(() => expect(api.delete).toHaveBeenCalledWith('/admin/questions/7'))
})

it('retains seeded PostgreSQL provenance through the bilingual edit form', async () => {
  const scroll = vi.spyOn(window, 'scrollTo').mockImplementation(() => {})
  const source = postgresPack.questions.find(q => q.key === 'pg-m089')
  const detail = { ...source, question_id: 119, status: 'validated', source: 'bank', concepts: [],
    translations: [{ locale: 'vi', ...translations.questions[source.key], current: true }] }
  api.get.mockImplementation(url => Promise.resolve({ data: url === '/admin/concepts' ? []
    : url === '/admin/questions/119' ? detail : [detail] }))
  api.put.mockResolvedValue({ data: detail })
  render(<AdminQuestionsPage />)
  await screen.findByText(source.prompt)
  await userEvent.click(screen.getByRole('button', { name: 'Edit', exact: true }))
  const difficulty = await screen.findByRole('combobox', { name: 'Difficulty' })
  await userEvent.selectOptions(difficulty, '3')
  await userEvent.click(screen.getByRole('button', { name: 'Save changes', exact: true }))
  await waitFor(() => expect(api.put).toHaveBeenCalledWith('/admin/questions/119', expect.objectContaining({
    difficulty_level: 3, tags: source.tags, source_refs: source.source_refs,
  })))
  expect(api.put.mock.calls[0][1]).not.toHaveProperty('translations')
  await userEvent.click(await screen.findByRole('button', { name: 'Details' }))
  expect(screen.getAllByRole('link').map(link => link.getAttribute('href'))).toEqual(['/admin/candidates', ...source.source_refs.map(ref => ref.url)])
  scroll.mockRestore()
})

it('labels a retired historical essay and hides its four-band validation action', async () => {
  api.get.mockResolvedValue({ data: [{
    question_id: 5, question_type: 'essay', difficulty_level: 3, status: 'retired',
    source: 'bank', prompt: 'Explain why indexes speed up reads but slow down writes.',
    concepts: [{ concept_id: 7, concept_code: 'IDX', confirmed: true }], legacy_rubric: true,
  }] })
  render(<AdminQuestionsPage />)
  expect(await screen.findByText('Legacy rubric')).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Validate' })).not.toBeInTheDocument()
})

it('requires confirmation before removing a draft assessment', async () => {
  api.get.mockImplementation((url) => Promise.resolve({ data: url === '/admin/concepts' ? [] : [{
    assessment_id: 4, title: 'Database basics', status: 'draft', max_questions: 8,
    duration_min: 30, target_count: 2, session_count: 0,
  }] }))
  render(<AdminAssessmentsPage />)
  expect(await screen.findByText('Database basics')).toBeInTheDocument()
  const row = screen.getByText('Database basics').closest('li')
  await userEvent.click(within(row).getByRole('button', { name: 'Actions' }))
  await userEvent.click(screen.getByRole('menuitem', { name: 'Delete' }))
  expect(screen.getByRole('dialog', { name: 'Delete this assessment?' })).toBeInTheDocument()
  expect(api.delete).not.toHaveBeenCalled()
  await userEvent.click(screen.getByRole('button', { name: 'Delete assessment' }))
  await waitFor(() => expect(api.delete).toHaveBeenCalledWith('/admin/assessments/4'))
})

it('blocks competing assessment actions until activation and reload finish', async () => {
  let resolve
  let published = false
  api.get.mockImplementation((url) => Promise.resolve({ data: url === '/admin/concepts' ? [] : [{
    assessment_id: 4, title: 'Database basics', status: published ? 'published' : 'draft', max_questions: 13,
    duration_min: 60, target_count: 12, session_count: 0,
  }] }))
  api.patch.mockImplementation(() => new Promise((done) => { resolve = done }))
  render(<AdminAssessmentsPage />)
  await screen.findByText('Database basics')
  const activate = screen.getByRole('button', { name: 'Publish' })
  await userEvent.click(activate)
  expect(activate).toBeDisabled()
  expect(screen.getByRole('button', { name: 'Edit' })).toBeDisabled()
  expect(screen.getByRole('button', { name: 'New assessment' })).toBeDisabled()
  await userEvent.click(activate)
  expect(api.patch).toHaveBeenCalledTimes(1)
  published = true
  await act(async () => resolve({ data: {} }))
  expect(await screen.findByRole('button', { name: 'Close', exact: true })).toBeEnabled()
  expect(screen.queryByText('Saving assessment changes…')).not.toBeInTheDocument()
})

it('surfaces a failed activation and restores retry controls', async () => {
  api.get.mockImplementation((url) => Promise.resolve({ data: url === '/admin/concepts' ? [] : [{
    assessment_id: 4, title: 'Invalid bank', status: 'draft', max_questions: 13,
    duration_min: 60, target_count: 1, session_count: 0,
  }] }))
  api.patch.mockRejectedValueOnce(new Error('Add an edge-case SQL dataset before activation'))
  render(<AdminAssessmentsPage />)
  await screen.findByText('Invalid bank')
  await userEvent.click(screen.getByRole('button', { name: 'Publish' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Add an edge-case SQL dataset before activation')
  expect(screen.getByRole('button', { name: 'Publish' })).toBeEnabled()
})

it('keeps a failed question deletion open with its API error', async () => {
  api.get.mockResolvedValue({ data: [{
    question_id: 7, question_type: 'mcq', difficulty_level: 1, status: 'draft',
    source: 'bank', prompt: 'Which query returns rows?', concepts: [],
  }] })
  api.delete.mockRejectedValueOnce(new Error('Question is used by a session'))
  render(<AdminQuestionsPage />)
  await screen.findByText('Which query returns rows?')
  const row = screen.getByText('Which query returns rows?').closest('li')
  await userEvent.click(within(row).getByRole('button', { name: 'Actions' }))
  await userEvent.click(screen.getByRole('menuitem', { name: 'Delete' }))
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
