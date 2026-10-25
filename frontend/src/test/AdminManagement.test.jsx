import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
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

it('saves essay criteria as four canonical rubric bands without a JSON input', async () => {
  api.get.mockResolvedValue({ data: [] })
  api.post.mockResolvedValue({ data: { question_id: 50 } })
  render(<AdminQuestionsPage />)
  await userEvent.click(screen.getByRole('button', { name: 'New question' }))
  await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Question type' }), 'essay')
  fireEvent.change(screen.getByRole('textbox', { name: 'Question prompt' }), { target: { value: 'Explain WHERE and HAVING' } })
  const criteria = screen.getAllByRole('textbox', { name: /^Criteria/ })
  expect(criteria).toHaveLength(4)
  for (let i = 0; i < criteria.length; i++) fireEvent.change(criteria[i], { target: { value: `Expected response ${i}` } })
  const submit = screen.getByRole('button', { name: 'Create', exact: true })
  await userEvent.click(submit)
  await waitFor(() => expect(api.post).toHaveBeenCalledWith('/admin/questions', expect.objectContaining({
    rubrics: [
      { level_name: 'Incomplete', min_score: 0, max_score: 0.24, criteria: 'Expected response 0' },
      { level_name: 'Partial', min_score: 0.25, max_score: 0.49, criteria: 'Expected response 1' },
      { level_name: 'Mostly Complete', min_score: 0.5, max_score: 0.74, criteria: 'Expected response 2' },
      { level_name: 'Complete', min_score: 0.75, max_score: 1, criteria: 'Expected response 3' },
    ],
  })))
})

it('creates an assessment from multiple concept checkboxes with default difficulty ranges', async () => {
  api.get.mockImplementation(path => Promise.resolve({ data: path === '/admin/concepts' ? [
    { concept_id: 1, concept_code: 'SQL-SELECT', concept_name: 'Select rows' },
    { concept_id: 2, concept_code: 'SQL-WHERE', concept_name: 'Filter rows' },
  ] : [] }))
  api.post.mockResolvedValue({ data: { assessment_id: 12 } })
  render(<AdminAssessmentsPage />)
  await userEvent.click(await screen.findByRole('button', { name: 'New assessment' }))
  const save = screen.getByRole('button', { name: 'Create draft' })
  expect(save).toBeDisabled()
  await userEvent.type(screen.getByRole('textbox', { name: 'Assessment title' }), 'SQL basics')
  await userEvent.click(screen.getByRole('checkbox', { name: /Select rows/ }))
  await userEvent.click(screen.getByRole('checkbox', { name: /Filter rows/ }))
  await userEvent.click(save)
  await waitFor(() => expect(api.post).toHaveBeenCalledWith('/admin/assessments', expect.objectContaining({
    title: 'SQL basics',
    concepts: [
      { concept_id: 1, min_difficulty: 1, max_difficulty: 5, target_pct: '60.00' },
      { concept_id: 2, min_difficulty: 1, max_difficulty: 5, target_pct: '60.00' },
    ],
  })))
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

it('starts with four empty answers and allows multiple correct selections without preselection', async () => {
  api.get.mockResolvedValue({ data: [] })
  render(<AdminQuestionsPage />)
  await userEvent.click(screen.getByRole('button', { name: 'New question' }))
  expect(screen.getByRole('textbox', { name: 'Question prompt' })).toHaveAttribute('placeholder', 'Enter the question')
  const answers = screen.getAllByRole('textbox', { name: /Option \d text/ })
  expect(answers).toHaveLength(4)
  answers.forEach(answer => expect(answer).toHaveValue(''))
  await userEvent.type(answers[0], 'My answer')
  expect(answers[0]).toHaveValue('My answer')
  expect(screen.getAllByRole('checkbox', { name: /Mark option/ }).every(checkbox => !checkbox.checked)).toBe(true)
  await userEvent.click(screen.getByRole('checkbox', { name: 'Mark option A as correct' }))
  await userEvent.click(screen.getByRole('checkbox', { name: 'Mark option C as correct' }))
  expect(screen.getByRole('checkbox', { name: 'Mark option A as correct' })).toBeChecked()
  expect(screen.getByRole('checkbox', { name: 'Mark option C as correct' })).toBeChecked()
  expect(screen.getAllByRole('checkbox', { name: /Mark option/ }).filter(checkbox => checkbox.checked)).toHaveLength(2)
})

it.each(['Which query returns rows?', 'Câu lệnh nào trả về dữ liệu?'])('creates a question with one prompt and one set of options: %s', async (prompt) => {
  api.get.mockResolvedValue({ data: [] })
  api.post.mockResolvedValue({ data: { question_id: 123 } })
  render(<AdminQuestionsPage />)
  await userEvent.click(screen.getByRole('button', { name: 'New question' }))
  expect(screen.getAllByRole('textbox', { name: 'Question prompt' })).toHaveLength(1)
  expect(screen.queryByRole('textbox', { name: 'Reference answer' })).not.toBeInTheDocument()
  fireEvent.change(screen.getByRole('textbox', { name: 'Question prompt' }), { target: { value: prompt } })
  fireEvent.change(screen.getByRole('textbox', { name: 'Option 1 text' }), { target: { value: 'SELECT lấy dữ liệu' } })
  for (const index of [2, 3, 4]) fireEvent.change(screen.getByRole('textbox', { name: `Option ${index} text` }), { target: { value: `Choice ${index}` } })
  await userEvent.click(screen.getByRole('checkbox', { name: 'Mark option A as correct' }))
  await userEvent.click(screen.getByRole('button', { name: 'Create', exact: true }))
  await waitFor(() => expect(api.post).toHaveBeenCalledWith('/admin/questions', expect.objectContaining({
    prompt,
    translations: [expect.objectContaining({ locale: 'vi', prompt, option_texts: expect.objectContaining({ A: 'SELECT lấy dữ liệu' }) })],
  })))
})

it.each(['mcq', 'essay'])('selects %s concepts without redundant required-concept checkboxes', async type => {
  api.get.mockImplementation(url => Promise.resolve({ data: url === '/admin/concepts' ? [
    { concept_id: 1, concept_code: 'SQL-JOIN', concept_name: 'Joins', subject_area: 'SQL' },
    { concept_id: 2, concept_code: 'SQL-WHERE', concept_name: 'Filters', subject_area: 'SQL' },
  ] : [] }))
  api.post.mockResolvedValue({ data: { question_id: 123 } })
  render(<AdminQuestionsPage />)
  await userEvent.click(screen.getByRole('button', { name: 'New question' }))
  fireEvent.change(screen.getByRole('textbox', { name: 'Question prompt' }), { target: { value: 'Pick the correct query' } })
  await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Question type' }), type)
  if (type === 'mcq') {
    for (const index of [1, 2, 3, 4]) fireEvent.change(screen.getByRole('textbox', { name: `Option ${index} text` }), { target: { value: `Choice ${index}` } })
    await userEvent.click(screen.getByRole('checkbox', { name: 'Mark option A as correct' }))
  }
  const joins = await screen.findByRole('checkbox', { name: /Joins.*SQL-JOIN/ })
  await userEvent.click(joins)
  expect(screen.queryByRole('checkbox', { name: 'Required: Joins' })).not.toBeInTheDocument()
  await userEvent.click(joins)
  expect(screen.queryByRole('checkbox', { name: 'Required: Joins' })).not.toBeInTheDocument()
  await userEvent.click(screen.getByRole('checkbox', { name: /Filters.*SQL-WHERE/ }))
  if (type === 'essay') {
    screen.getAllByRole('textbox', { name: /^Criteria/ }).forEach((field, index) =>
      fireEvent.change(field, { target: { value: `Expected answer level ${index}` } }))
  }
  await userEvent.click(screen.getByRole('button', { name: 'Create', exact: true }))
  await waitFor(() => expect(api.post).toHaveBeenCalledWith('/admin/questions', expect.objectContaining({ concept_ids: [2], required_concept_ids: [] })))
})

it('retains seeded PostgreSQL provenance through the single-content edit form', async () => {
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
  const difficulty = await screen.findByRole('spinbutton', { name: 'Difficulty' })
  await userEvent.clear(difficulty)
  await userEvent.type(difficulty, '3')
  await userEvent.click(screen.getByRole('button', { name: 'Save changes', exact: true }))
  await waitFor(() => expect(api.put).toHaveBeenCalledWith('/admin/questions/119', expect.objectContaining({
    difficulty_level: 3, tags: source.tags, source_refs: source.source_refs,
    translations: [expect.objectContaining({ locale: 'vi', prompt: source.prompt })],
  })))
  await userEvent.click(await screen.findByRole('button', { name: 'Details' }))
  expect(screen.getAllByRole('link').map(link => link.getAttribute('href'))).toEqual(source.source_refs.map(ref => ref.url))
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
  expect(screen.queryByRole('textbox', { name: 'Concept code' })).not.toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Add concept' }))
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
