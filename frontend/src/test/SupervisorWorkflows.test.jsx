import { render, screen, waitFor, within, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, expect, it, vi } from 'vitest'
import api from '../api'
import PersonalizedAssessment from '../components/PersonalizedAssessment'
import CumulativeCompetencyPage from '../pages/CumulativeCompetencyPage'
import AssessmentReviewPage from '../pages/AssessmentReviewPage'
import AdminEssayReviewPage from '../pages/admin/AdminEssayReviewPage'
import AdminAssessmentsPage from '../pages/admin/AdminAssessmentsPage'
import AdminCurriculumPage from '../pages/admin/AdminCurriculumPage'
import { setLocale } from '../i18n'

vi.mock('../api', () => ({ default: { get: vi.fn(), post: vi.fn(), patch: vi.fn() }, apiMessage: e => e.message || 'Request failed' }))
vi.mock('../components/CompetencyCharts', () => ({ CompetencyConceptBars: () => <div data-testid="cumulative-chart" /> }))
const templates = [{ assessment_id: 1, title: 'Database rules', result_release_policy: 'HUMAN_VERIFIED',
  concepts: [{ concept_id: 2, concept_name: 'Joins', concept_code: 'JOIN' }, { concept_id: 3, concept_name: 'Filtering', concept_code: 'WHERE' }] }]
const pending = { session_id: 9, learner_name: 'Test learner', assessment_title: 'Database rules',
  release_status: 'pending_review', result_release_policy: 'HUMAN_VERIFIED', revision: 1,
  items: [{ attempt_id: 21, question_type: 'essay', prompt: 'Explain how SQL filters rows', points: 2,
    reference_answer: 'WHERE filters rows before grouping.', essay_answer: 'WHERE filters each row.', automated_score: 1.5,
    automated_detail: { datasets_passed: 1, datasets_total: 2 }, options: [], rubrics: [],
    revision: 0, grading_status: 'graded', submitted_at: '2026-10-18T00:00:00Z', review: null }], events: [] }
beforeEach(async () => { vi.resetAllMocks(); await act(() => setLocale('en')) })

it.each(['mcq', 'sql', 'essay'])('shows the stored AI explanation directly below each %s answer without new AI requests', async question_type => {
  const item = { seq_no: 1, attempt_id: 21, question_id: 3, question_type,
    prompt: 'Explain this answer', difficulty_level: 1, points: '1', score: '1',
    concepts: [], options: [{ option_id: 1, option_label: 'A', option_text: 'SELECT', is_correct: true }],
    selected_option_id: 1, sql_answer: 'SELECT * FROM students', essay_answer: 'My explanation',
    grading_detail: { grader: 'answer_key', ai_analysis: { reasoning: 'SELECT retrieves all columns because the star selects every column.', next_step: 'Try selecting only the required columns.' } } }
  api.get.mockResolvedValue({ data: { session_id: 9, status: 'completed', items: [item] } })
  render(<MemoryRouter initialEntries={['/history/9']}><Routes><Route path="/history/:sessionId" element={<AssessmentReviewPage />} /></Routes></MemoryRouter>)
  expect(await screen.findByRole('heading', { name: 'AI explanation for this question' })).toBeInTheDocument()
  expect(screen.getByText('SELECT retrieves all columns because the star selects every column.')).toBeInTheDocument()
  expect(screen.getByText('Try selecting only the required columns.')).toBeInTheDocument()
  expect(api.post).not.toHaveBeenCalled()
})

it('does not invent an AI explanation from a teacher answer key', async () => {
  api.get.mockResolvedValue({ data: { session_id: 9, status: 'completed', items: [{
    seq_no: 1, attempt_id: 21, question_id: 3, question_type: 'mcq', prompt: 'Select all rows',
    difficulty_level: 1, points: '1', score: '1', concepts: [], options: [],
    explanation: 'Teacher-authored explanation', grading_detail: { grader: 'answer_key' },
  }] } })
  render(<MemoryRouter initialEntries={['/history/9']}><Routes><Route path="/history/:sessionId" element={<AssessmentReviewPage />} /></Routes></MemoryRouter>)
  expect(await screen.findByText('An AI explanation is not available for this question yet.')).toBeInTheDocument()
  expect(api.post).not.toHaveBeenCalled()
})

it('shows the original AI explanation after the essay was reviewed', async () => {
  api.get.mockResolvedValue({ data: { session_id: 9, status: 'completed', items: [{
    seq_no: 1, attempt_id: 21, question_id: 3, question_type: 'essay', prompt: 'Explain a key',
    difficulty_level: 1, points: '1', score: '1', concepts: [], options: [], essay_answer: 'A key identifies a row.',
    grading_detail: { grader: 'human_verified', reviewer_comments: 'Confirmed by reviewer.', automated_evaluation: { grader: 'llm_rubric', explanation: 'You correctly identify the uniqueness requirement.', feedback: 'Add a short table example.' } },
  }] } })
  render(<MemoryRouter initialEntries={['/history/9']}><Routes><Route path="/history/:sessionId" element={<AssessmentReviewPage />} /></Routes></MemoryRouter>)
  expect(await screen.findByText('You correctly identify the uniqueness requirement.')).toBeInTheDocument()
  expect(screen.getByText('Confirmed by reviewer.')).toBeInTheDocument()
})

it('requires skills and sends comprehensive skills, chosen difficulty and a request UUID', async () => {
  api.post.mockResolvedValue({ data: { session_id: 8 } })
  render(<MemoryRouter><Routes><Route path="/" element={<PersonalizedAssessment assessments={templates} />} /><Route path="/exam/:id" element={<p>Exam started</p>} /></Routes></MemoryRouter>)
  expect(screen.getByRole('button', { name: 'Start personalized assessment' })).toBeDisabled()
  await userEvent.click(screen.getByRole('button', { name: /Select all skills/ }))
  await userEvent.selectOptions(screen.getByLabelText('Assessment difficulty'), 'HARD')
  await userEvent.click(screen.getByRole('button', { name: 'Start personalized assessment' }))
  expect(await screen.findByText('Exam started')).toBeInTheDocument()
  expect(api.post).toHaveBeenCalledWith('/assessments/1/sessions', { concept_ids: [2, 3], difficulty: 'HARD', mode: 'PRACTICE', question_count: 3, request_id: expect.stringMatching(/^[a-f0-9-]{36}$/) })
})

it('keeps the selection and idempotency request for recovery after a failed start', async () => {
  api.post.mockRejectedValue(new Error('Insufficient approved questions'))
  render(<MemoryRouter><PersonalizedAssessment assessments={templates} /></MemoryRouter>)
  await userEvent.click(screen.getByLabelText(/Joins/))
  const button = screen.getByRole('button', { name: 'Start personalized assessment' })
  await userEvent.click(button)
  expect(await screen.findByRole('alert')).toHaveTextContent('Insufficient approved questions')
  expect(screen.getByLabelText(/Joins/)).toBeChecked()
  await userEvent.click(button)
  await waitFor(() => expect(api.post).toHaveBeenCalledTimes(2))
  expect(api.post.mock.calls[0][1]).toEqual(api.post.mock.calls[1][1])
})

it('offers an explicit formal format that retains the configured examination contract', async () => {
  api.post.mockRejectedValue(new Error('Pool incomplete'))
  render(<MemoryRouter><PersonalizedAssessment assessments={templates} /></MemoryRouter>)
  await userEvent.selectOptions(screen.getByLabelText('Assessment format'), 'FORMAL')
  expect(screen.queryByLabelText('Number of questions')).not.toBeInTheDocument()
  await userEvent.click(screen.getByLabelText(/Joins/))
  await userEvent.click(screen.getByRole('button', { name: 'Start personalized assessment' }))
  await waitFor(() => expect(api.post).toHaveBeenCalledWith('/assessments/1/sessions', expect.objectContaining({ concept_ids: [2], difficulty: 'EASY' })))
  expect(api.post.mock.calls[0][1]).not.toHaveProperty('question_count')
})

it('preserves an existing human-verification policy when reopening the assessment editor', async () => {
  const assessment = { assessment_id: 1, title: 'Verified draft', status: 'draft', result_release_policy: 'HUMAN_VERIFIED', concepts: [], max_questions: 13, duration_min: 60 }
  api.get.mockImplementation(url => Promise.resolve({ data: url === '/admin/assessments' ? [assessment] : url === '/admin/assessments/1' ? assessment : [] }))
  render(<MemoryRouter><AdminAssessmentsPage /></MemoryRouter>)
  await userEvent.click(await screen.findByRole('button', { name: 'Edit', exact: true }))
  expect(await screen.findByLabelText('Result release policy')).toHaveValue('HUMAN_VERIFIED')
})

it('displays pending verification without attempting to render grading evidence', async () => {
  api.get.mockRejectedValue({ response: { data: { error: { code: 'results_pending', details: { release_status: 'pending_review' } } } } })
  render(<MemoryRouter initialEntries={['/history/9']}><Routes><Route path="/history/:sessionId" element={<AssessmentReviewPage />} /></Routes></MemoryRouter>)
  expect(await screen.findByRole('heading', { name: 'Your submission is received' })).toBeInTheDocument()
  expect(screen.getByRole('status')).toHaveTextContent('Automated analysis is complete')
  expect(screen.queryByText('Automated suggested score')).not.toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Refresh status' }))
  await waitFor(() => expect(api.get).toHaveBeenCalledTimes(2))
})

it('supports a cumulative empty state with no invented scores', async () => {
  api.get.mockResolvedValue({ data: { concepts: [], gaps: [], summary: { finalized_assessments: 0 } } })
  render(<MemoryRouter><CumulativeCompetencyPage /></MemoryRouter>)
  expect(await screen.findByText('No published competency evidence yet')).toBeInTheDocument()
  expect(api.get).toHaveBeenCalledWith('/sessions/competency/cumulative')
  expect(screen.queryByTestId('cumulative-chart')).not.toBeInTheDocument()
})

it('shows the approved result and teacher comments in published learner evidence', async () => {
  api.get.mockResolvedValue({ data: { session_id: 9, status: 'completed', items: [{
    seq_no: 1, attempt_id: 21, question_id: 3, question_type: 'essay', prompt: 'Explain a database concept',
    difficulty_level: 3, points: '1', score: '0.5', concepts: [], options: [], rubrics: [],
    essay_answer: 'Recorded learner response', grading_detail: { grader: 'human_verified', reviewer_comments: 'Explain the missing dependency before decomposing the relation.' },
  }] } })
  render(<MemoryRouter initialEntries={['/history/9']}><Routes><Route path="/history/:sessionId" element={<AssessmentReviewPage />} /></Routes></MemoryRouter>)
  expect(await screen.findByText('Explain the missing dependency before decomposing the relation.')).toBeInTheDocument()
  expect(screen.getByText('Approved', { exact: true })).toBeInTheDocument()
})

it('renders cumulative evidence, weighted backend scores and recurring gaps', async () => {
  const concept = { concept_id: 1, concept_name: 'Joins', concept_code: 'JOIN', points_earned: '1', points_possible: '10',
    competency_pct: '10.00', target_pct: '78', below_target: true, contributing_attempts: [1, 2],
    contributing_sessions: [1, 2], below_target_assessments: 1 }
  api.get.mockResolvedValue({ data: { concepts: [concept], gaps: [concept], summary: { finalized_assessments: 2 } } })
  render(<MemoryRouter><CumulativeCompetencyPage /></MemoryRouter>)
  await screen.findByRole('heading', { name: 'Cumulative competency chart' })
  expect(screen.queryByText('Published assessments')).not.toBeInTheDocument()
  expect(screen.getAllByText('10%')[0]).toBeInTheDocument()
  expect(screen.queryByText('2 questions · 2 assessments')).not.toBeInTheDocument()
  expect(screen.getByText('Below benchmark in 1 assessment')).toBeInTheDocument()
  expect(screen.getByRole('img', { name: 'Joins: 10%; Target: 78%' })).toBeInTheDocument()
})

it('provides essay evidence and score confirmation, retaining concurrency revision', async () => {
  api.get.mockImplementation(url => Promise.resolve({ data: url === '/admin/grading-reviews' ? [pending] : pending }))
  api.post.mockResolvedValue({ data: { ...pending, release_status: 'reviewed', revision: 3,
    items: [{ ...pending.items[0], revision: 1, review: { reviewer_id: 1, reviewed_at: '2026-10-18T00:00:00Z' }, final_score: 1 }] } })
  render(<MemoryRouter><AdminEssayReviewPage /></MemoryRouter>)
  await userEvent.click(await screen.findByRole('button', { name: /Test learner.*Database rules/ }))
  expect(await screen.findByText('WHERE filters each row.')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Publish verified results' })).toBeDisabled()
  const input = screen.getByLabelText('Approved score')
  await userEvent.clear(input)
  await userEvent.type(input, '1')
  await userEvent.type(screen.getByLabelText('Grader comments'), 'Reviewed explanation')
  await userEvent.click(screen.getByRole('button', { name: 'Approve score' }))
  await waitFor(() => expect(api.post).toHaveBeenCalledWith('/admin/grading-reviews/9/attempts/21', { score: '1', comments: 'Reviewed explanation', revision: 0 }))
  await waitFor(() => expect(screen.getByRole('button', { name: 'Publish verified results' })).toBeEnabled())
  await userEvent.click(screen.getByRole('button', { name: 'Publish verified results' }))
  expect(api.post).toHaveBeenLastCalledWith('/admin/grading-reviews/9/publish', { revision: 3 })
})

it.each(['published', 'auto_grading'])('allows admin feedback and score review for an immediate result in %s', async (release_status) => {
  const immediate = { ...pending, result_release_policy: 'IMMEDIATE', release_status }
  api.get.mockImplementation(url => Promise.resolve({ data: url === '/admin/grading-reviews' ? [immediate] : immediate }))
  api.post.mockResolvedValue({ data: { ...immediate, items: [{ ...immediate.items[0], review: { reviewer_id: 1, reviewed_at: '2026-10-18T00:00:00Z', comments: 'Checked after publication' }, final_score: 1.5 }] } })
  render(<MemoryRouter><AdminEssayReviewPage /></MemoryRouter>)
  await userEvent.click(await screen.findByRole('button', { name: /Test learner.*Database rules/ }))
  await userEvent.type(await screen.findByLabelText('Grader comments'), 'Checked after publication')
  await userEvent.click(screen.getByRole('button', { name: 'Approve score' }))
  await waitFor(() => expect(api.post).toHaveBeenCalledWith('/admin/grading-reviews/9/attempts/21', { score: 1.5, comments: 'Checked after publication', revision: 0 }))
  expect(await screen.findByText('Checked after publication')).toBeInTheDocument()
})

it('shows published scores while reference answers and feedback await admin review', async () => {
  api.get.mockResolvedValue({ data: { session_id: 9, status: 'completed', items: [{
    attempt_id: 1, question_id: 1, seq_no: 1, question_type: 'mcq', prompt: 'Choose a query',
    content_locale: 'en', difficulty_level: 1, points: '1', score: '1', concepts: [],
    feedback_pending: true, grading_detail: null, selected_option_ids: [2],
    options: [{ option_id: 2, option_label: 'A', option_text: 'My query', is_correct: null }],
    served_at: '2026-10-18T00:00:00Z', submitted_at: '2026-10-18T00:01:00Z',
  }] } })
  render(<MemoryRouter initialEntries={['/history/9']}><Routes><Route path="/history/:sessionId" element={<AssessmentReviewPage />} /></Routes></MemoryRouter>)
  expect(await screen.findByText('Your score is published. Reference answers and feedback will appear after an admin reviews this answer.')).toBeInTheDocument()
  expect(screen.getByText(/1.00 \/ 1.00 pts/)).toBeInTheDocument()
  expect(screen.getByText(/My query/)).toBeInTheDocument()
  expect(document.querySelector('[data-icon="x"]')).not.toBeInTheDocument()
})

it('shows review conflicts and allows refreshing the current review', async () => {
  api.get.mockImplementation(url => Promise.resolve({ data: url === '/admin/grading-reviews' ? [pending] : pending }))
  api.post.mockRejectedValue(new Error('Another grader updated this submission'))
  render(<MemoryRouter><AdminEssayReviewPage /></MemoryRouter>)
  await userEvent.click(await screen.findByRole('button', { name: /Test learner.*Database rules/ }))
  await userEvent.click(await screen.findByRole('button', { name: 'Approve score' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Another grader updated this submission')
  expect(screen.getByRole('button', { name: 'Publish verified results' })).toBeDisabled()
})

it('saves the administrator result release policy', async () => {
  api.get.mockImplementation(url => Promise.resolve({ data: url === '/admin/concepts' ? templates[0].concepts : [] }))
  api.post.mockResolvedValue({ data: { assessment_id: 1 } })
  render(<MemoryRouter><AdminAssessmentsPage /></MemoryRouter>)
  await userEvent.click(screen.getByRole('button', { name: 'New assessment' }))
  await userEvent.type(screen.getByLabelText('Assessment title'), 'Verified exam')
  await userEvent.selectOptions(screen.getByLabelText('Result release policy'), 'HUMAN_VERIFIED')
  const choices = screen.getAllByRole('combobox')
  const conceptSelect = choices.find(select => [...select.options].some(o => o.value === '2'))
  await userEvent.selectOptions(conceptSelect, '2')
  await userEvent.click(screen.getByRole('button', { name: 'Create draft' }))
  await waitFor(() => expect(api.post).toHaveBeenCalledWith('/admin/assessments', expect.objectContaining({ result_release_policy: 'HUMAN_VERIFIED' })))
})

it('manages concept keywords and learning objectives in the existing curriculum form', async () => {
  api.get.mockResolvedValue({ data: [] })
  api.post.mockResolvedValue({ data: {} })
  render(<MemoryRouter><AdminCurriculumPage /></MemoryRouter>)
  const keyword = await screen.findByLabelText('Concept keywords (comma separated)')
  await userEvent.type(screen.getByLabelText('Concept code'), 'JOIN')
  await userEvent.type(screen.getByLabelText('Concept name'), 'Joins')
  await userEvent.type(screen.getByLabelText('Subject area'), 'SQL')
  await userEvent.type(keyword, 'join,relationship')
  await userEvent.type(screen.getByLabelText('Learning objectives (one per line)'), 'Explain joins\nCompare outer joins')
  await userEvent.click(screen.getByRole('button', { name: 'Add concept' }))
  await waitFor(() => expect(api.post).toHaveBeenCalledWith('/admin/concepts', expect.objectContaining({ keywords: ['join', 'relationship'], learning_objectives: ['Explain joins', 'Compare outer joins'] })))
})
