import { render, screen, waitFor, within, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, expect, it, vi } from 'vitest'
import api from '../api'
import PersonalizedAssessment from './historical/PersonalizedAssessment'
import CumulativePage from '../pages/CumulativePage'
import EvidencePage from '../pages/EvidencePage'
import AdminGradingPage from '../pages/admin/AdminGradingPage'
import AdminAssessmentsPage from './historical/AdminAssessmentsPage'
import AdminCurriculumPage from '../pages/admin/AdminCurriculumPage'
import { setLocale, t } from '../i18n'

vi.mock('../api', () => ({
  default: { get: vi.fn(), post: vi.fn(), patch: vi.fn() },
  apiMessage: (e) => e.message || 'Request failed',
}))
vi.mock('../components/CompetencyCharts', () => ({
  CompetencyConceptBars: () => <div data-testid="cumulative-chart" />,
}))
const templates = [
  {
    assessment_id: 1,
    title: 'Database rules',
    result_release_policy: 'HUMAN_VERIFIED',
    concepts: [
      { concept_id: 2, concept_name: 'Joins', concept_code: 'JOIN' },
      { concept_id: 3, concept_name: 'Filtering', concept_code: 'WHERE' },
    ],
  },
]
const pending = {
  session_id: 9,
  learner_name: 'Test learner',
  assessment_title: 'Database rules',
  release_status: 'pending_review',
  result_release_policy: 'HUMAN_VERIFIED',
  revision: 1,
  items: [
    {
      attempt_id: 21,
      question_type: 'sql',
      prompt: 'Select rows from the table',
      points: 2,
      reference_answer: 'SELECT id FROM t',
      sql_answer: 'SELECT * FROM t',
      automated_score: 1.5,
      automated_detail: { datasets_passed: 1, datasets_total: 2 },
      options: [],
      rubrics: [],
      revision: 0,
      grading_status: 'graded',
      submitted_at: '2026-10-18T00:00:00Z',
      review: null,
    },
  ],
  events: [],
}
beforeEach(async () => {
  vi.resetAllMocks()
  await act(() => setLocale('en'))
})

it('updates a directly linked practice review when asynchronous evaluation finishes', async () => {
  vi.useFakeTimers()
  const initial = {
    ...pending,
    learner_defined: true,
    release_status: 'auto_grading',
    evaluation: null,
  }
  const completed = {
    ...initial,
    release_status: 'provisional_ai',
    evaluation: {
      evaluation: {
        summary: 'Ready for review',
        strengths: ['strength'],
        weaknesses: ['weakness'],
        suggestions: ['suggestion'],
        learning_path: ['path'],
        question_comments: [],
        concepts: [],
      },
      evaluator_fallback: true,
    },
  }
  let reads = 0
  api.get.mockImplementation((path) =>
    Promise.resolve({
      data: path === '/admin/grading-reviews' ? [initial] : ++reads === 1 ? initial : completed,
    }),
  )
  try {
    render(
      <MemoryRouter initialEntries={['/admin/grading/9']}>
        <Routes>
          <Route path="/admin/grading/:reviewSessionId" element={<AdminGradingPage />} />
        </Routes>
      </MemoryRouter>,
    )
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0)
    })
    expect(screen.getByRole('button', { name: 'Duyệt', exact: true })).toBeDisabled()
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2100)
    })
    expect(screen.getByRole('button', { name: 'Duyệt', exact: true })).toBeEnabled()
    expect(screen.getAllByText('Ready for review').length).toBeGreaterThan(0)
    expect(screen.getByRole('button', { name: /Test learner.*Database rules/ })).toHaveTextContent(
      t('supervisor.provisional_ai'),
    )
    expect(
      screen.getByRole('button', { name: /Test learner.*Database rules/ }),
    ).not.toHaveTextContent(t('supervisor.auto_grading'))
  } finally {
    vi.useRealTimers()
  }
})

it('labels an adjusted practice score as current and hides unneeded pagination', async () => {
  const detail = {
    ...pending,
    learner_defined: true,
    items: [{ ...pending.items[0], automated_score: 0.25 }],
    evaluation: { evaluation: { summary: 'Reviewed evidence', question_comments: [] } },
    score_edits: [],
  }
  api.get.mockImplementation((path) =>
    Promise.resolve({ data: path === '/admin/grading-reviews' ? [detail] : detail }),
  )
  render(
    <MemoryRouter initialEntries={['/admin/grading/9']}>
      <Routes>
        <Route path="/admin/grading/:reviewSessionId" element={<AdminGradingPage />} />
      </Routes>
    </MemoryRouter>,
  )
  expect(await screen.findByText(/^Điểm hiện tại:/)).toHaveTextContent('0.25 / 2')
  expect(screen.queryByText(/Automated suggested score/)).not.toBeInTheDocument()
  expect(
    screen.queryByRole('navigation', { name: t('supervisor.reviewPages') }),
  ).not.toBeInTheDocument()
})

it('submits edited final feedback when the administrator approves', async () => {
  const practice = {
    ...pending,
    learner_defined: true,
    release_status: 'provisional_ai',
    evaluation: {
      evaluation: {
        summary: 'AI draft',
        strengths: ['s'],
        weaknesses: ['w'],
        suggestions: ['g'],
        learning_path: ['p'],
        question_comments: [],
        concepts: [],
      },
      evaluator_fallback: true,
    },
    concept_results: [{ concept_id: 2, concept_name: 'Joins' }],
  }
  api.get.mockImplementation((path) =>
    Promise.resolve({
      data: path === '/admin/grading-reviews' ? [practice] : practice,
    }),
  )
  api.post.mockResolvedValue({
    data: { ...practice, release_status: 'published', final_result: { source: 'admin' } },
  })
  render(
    <MemoryRouter initialEntries={['/admin/grading']}>
      <Routes>
        <Route path="/admin/grading" element={<AdminGradingPage />} />
      </Routes>
    </MemoryRouter>,
  )
  await userEvent.click(
    await screen.findByRole('button', { name: /Test learner.*Database rules/ }),
  )
  const summary = await screen.findByLabelText('Tóm tắt')
  await userEvent.clear(summary)
  await userEvent.type(summary, 'Admin final summary')
  await userEvent.click(screen.getByRole('button', { name: 'Lưu và duyệt' }))
  expect(api.post).toHaveBeenCalledWith(
    '/admin/grading-reviews/9/publish',
    expect.objectContaining({
      final_feedback: expect.objectContaining({ summary: 'Admin final summary' }),
    }),
  )
})

it('keeps pagination available on a full queue and returns from an empty next page', async () => {
  api.get.mockImplementation((path, config) =>
    Promise.resolve({
      data: config?.params?.offset
        ? []
        : Array.from({ length: 100 }, (_, i) => ({ ...pending, session_id: i + 1 })),
    }),
  )
  render(
    <MemoryRouter>
      <AdminGradingPage />
    </MemoryRouter>,
  )
  const pages = await screen.findByRole('navigation', { name: t('supervisor.reviewPages') })
  expect(within(pages).getByRole('button', { name: t('assessment.prevPage') })).toBeDisabled()
  await userEvent.click(within(pages).getByRole('button', { name: t('assessment.nextPage') }))
  expect(await screen.findByText(t('supervisor.queueEmpty'))).toBeVisible()
  expect(within(pages).getByRole('button', { name: t('assessment.prevPage') })).toBeEnabled()
  expect(within(pages).getByRole('button', { name: t('assessment.nextPage') })).toBeDisabled()
  await userEvent.click(within(pages).getByRole('button', { name: t('assessment.prevPage') }))
  await waitFor(() =>
    expect(screen.getAllByRole('button', { name: /Test learner.*Database rules/ })).toHaveLength(
      100,
    ),
  )
})

it('stops loading after a review queue error and recovers with one retry', async () => {
  api.get
    .mockRejectedValueOnce(new Error('Review queue unavailable'))
    .mockResolvedValue({ data: [pending] })
  render(
    <MemoryRouter>
      <AdminGradingPage />
    </MemoryRouter>,
  )
  const error = await screen.findByRole('alert')
  expect(error).toHaveTextContent('Review queue unavailable')
  expect(screen.queryByRole('status', { name: /loading/i })).not.toBeInTheDocument()
  await userEvent.click(within(error).getByRole('button'))
  expect(await screen.findByRole('button', { name: /Test learner.*Database rules/ })).toBeVisible()
  expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  expect(api.get).toHaveBeenCalledTimes(2)
})

it('retries the failed review detail instead of leaving its queue as the only result', async () => {
  let attempts = 0
  api.get.mockImplementation((path) => {
    if (path === '/admin/grading-reviews') return Promise.resolve({ data: [pending] })
    return ++attempts === 1
      ? Promise.reject(new Error('Review detail unavailable'))
      : Promise.resolve({ data: pending })
  })
  render(
    <MemoryRouter>
      <AdminGradingPage />
    </MemoryRouter>,
  )
  await userEvent.click(await screen.findByRole('button', { name: /Test learner.*Database rules/ }))
  const error = await screen.findByRole('alert')
  expect(error).toHaveTextContent('Review detail unavailable')
  await userEvent.click(within(error).getByRole('button'))
  expect(await screen.findByLabelText('Approved score')).toBeEnabled()
  expect(api.get.mock.calls.filter(([path]) => path === '/admin/grading-reviews/9')).toHaveLength(2)
  expect(screen.queryByRole('alert')).not.toBeInTheDocument()
})

it('offers instructor grading for a saved essay when optional AI is unavailable', async () => {
  const detail = {
    ...pending,
    manual_review_required: true,
    result_release_policy: 'IMMEDIATE',
    items: [
      {
        ...pending.items[0],
        question_type: 'essay',
        automated_score: null,
        grading_status: 'pending',
        essay_answer: 'Explain normalization',
        automated_detail: { awaiting_instructor: true },
      },
    ],
  }
  api.get.mockImplementation((path) =>
    Promise.resolve({ data: path === '/admin/grading-reviews' ? [detail] : detail }),
  )
  render(
    <MemoryRouter>
      <AdminGradingPage />
    </MemoryRouter>,
  )
  await userEvent.click(await screen.findByRole('button', { name: /Test learner.*Database rules/ }))
  expect(
    await screen.findByText(
      'AI is unavailable. The saved essay is awaiting instructor grading and publication.',
    ),
  ).toBeInTheDocument()
  expect(screen.getByLabelText('Approved score')).toBeEnabled()
  expect(screen.getByRole('button', { name: 'Approve score', exact: true })).toBeEnabled()
})

it('focuses on required grading while preserving optional MCQ review behind details', async () => {
  const detail = {
    ...pending,
    items: [
      ...pending.items,
      {
        ...pending.items[0],
        attempt_id: 22,
        question_type: 'mcq',
        prompt: 'Automatically marked question',
        selected_option_id: 4,
        options: [{ option_id: 4, option_text: 'Correct', is_correct: true }],
      },
    ],
  }
  api.get.mockImplementation((path) =>
    Promise.resolve({ data: path === '/admin/grading-reviews' ? [detail] : detail }),
  )
  render(
    <MemoryRouter>
      <AdminGradingPage />
    </MemoryRouter>,
  )
  await userEvent.click(await screen.findByRole('button', { name: /Test learner.*Database rules/ }))
  expect(await screen.findAllByRole('spinbutton')).toHaveLength(1)
  await userEvent.click(screen.getByText('Automatically graded MCQs (optional details)'))
  expect(screen.getAllByRole('spinbutton')).toHaveLength(2)
  expect(screen.getByText('Automatically marked question')).toBeVisible()
})

it('searches skills while retaining selected skills and their exact request values', async () => {
  api.post.mockRejectedValue(new Error('Pool incomplete'))
  render(
    <MemoryRouter>
      <PersonalizedAssessment assessments={templates} />
    </MemoryRouter>,
  )
  await userEvent.click(screen.getByLabelText(/Joins/))
  await userEvent.type(screen.getByLabelText('Search skills'), 'where')
  expect(screen.getByLabelText(/Joins/)).toBeChecked()
  await userEvent.click(screen.getByLabelText(/Filtering/))
  expect(screen.getByText('Selected skills: 2')).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Start assessment' }))
  await waitFor(() =>
    expect(api.post).toHaveBeenCalledWith(
      '/assessments/1/sessions',
      expect.objectContaining({ concept_ids: [2, 3], difficulty: 'EASY', question_count: null }),
    ),
  )
})

it('requires skills and sends comprehensive skills, chosen difficulty and a request UUID', async () => {
  api.post.mockResolvedValue({ data: { session_id: 8 } })
  render(
    <MemoryRouter>
      <Routes>
        <Route path="/" element={<PersonalizedAssessment assessments={templates} />} />
        <Route path="/exam/:id" element={<p>Exam started</p>} />
      </Routes>
    </MemoryRouter>,
  )
  expect(screen.getByRole('button', { name: 'Start assessment' })).toBeDisabled()
  await userEvent.click(screen.getByRole('button', { name: /Select all skills/ }))
  await userEvent.click(screen.getByRole('radio', { name: 'Hard', exact: true }))
  await userEvent.click(screen.getByRole('button', { name: 'Start assessment' }))
  expect(await screen.findByText('Exam started')).toBeInTheDocument()
  expect(api.post).toHaveBeenCalledWith('/assessments/1/sessions', {
    concept_ids: [2, 3],
    difficulty: 'HARD',
    mode: 'PRACTICE',
    question_count: null,
    request_id: expect.stringMatching(/^[a-f0-9-]{36}$/),
  })
})

it('keeps technical options secondary and uses understandable searchable curriculum skills', async () => {
  const manySkills = Array.from({ length: 4 }, (_, i) => ({
    concept_id: i + 1,
    concept_name: `SQL skill ${i + 1}`,
    subject_area: 'SQL',
    concept_code: `INTERNAL-${i}`,
  }))
  api.post.mockResolvedValue({ data: { session_id: 8 } })
  render(
    <MemoryRouter>
      <PersonalizedAssessment assessments={[{ ...templates[0], concepts: manySkills }]} />
    </MemoryRouter>,
  )
  expect(screen.getByText('Assessment options').closest('details')).not.toHaveAttribute('open')
  expect(screen.getAllByRole('radio')).toHaveLength(3)
  expect(screen.queryByText('INTERNAL-0')).not.toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'SQL', exact: true }))
  expect(screen.getByRole('button', { name: 'SQL', exact: true })).toHaveAttribute(
    'aria-pressed',
    'true',
  )
  expect(screen.getAllByRole('checkbox').every((box) => box.checked)).toBe(true)
  await userEvent.click(screen.getByRole('radio', { name: 'Medium', exact: true }))
  await userEvent.click(screen.getByRole('button', { name: 'Start assessment', exact: true }))
  expect(api.post).toHaveBeenCalledWith(
    '/assessments/1/sessions',
    expect.objectContaining({
      concept_ids: [1, 2, 3, 4],
      difficulty: 'MEDIUM',
      mode: 'PRACTICE',
      question_count: null,
    }),
  )
})

it('does not silently replace a missing skill search with another scope', async () => {
  render(
    <MemoryRouter>
      <PersonalizedAssessment assessments={templates} />
    </MemoryRouter>,
  )
  await userEvent.type(screen.getByRole('searchbox'), 'Normalization')
  expect(screen.getByRole('status')).toHaveTextContent('No matching skills')
  expect(screen.getByRole('button', { name: 'Start assessment', exact: true })).toBeDisabled()
  expect(api.post).not.toHaveBeenCalled()
})

it('automatically finds an open assessment for the skill and rejects unsupported combinations', async () => {
  api.post.mockRejectedValue(new Error('Start interrupted'))
  const additional = {
    assessment_id: 2,
    title: 'Design rules',
    concepts: [
      {
        concept_id: 9,
        concept_name: 'Normalization',
        concept_code: 'DB-NORM',
        subject_area: 'Database Design',
      },
    ],
  }
  render(
    <MemoryRouter>
      <PersonalizedAssessment assessments={[...templates, additional]} />
    </MemoryRouter>,
  )
  await userEvent.click(screen.getByRole('checkbox', { name: 'Normalization', exact: true }))
  await userEvent.click(screen.getByRole('button', { name: 'Start assessment', exact: true }))
  await waitFor(() =>
    expect(api.post).toHaveBeenCalledWith(
      '/assessments/2/sessions',
      expect.objectContaining({ concept_ids: [9] }),
    ),
  )
  await userEvent.click(screen.getByRole('checkbox', { name: 'Joins', exact: true }))
  expect(screen.getByRole('button', { name: 'Start assessment', exact: true })).toBeDisabled()
  expect(screen.getByRole('status')).toHaveTextContent('No open assessment covers this skill group')
  expect(api.post).toHaveBeenCalledTimes(1)
})

it('keeps the selection and idempotency request for recovery after a failed start', async () => {
  api.post.mockRejectedValue(new Error('Insufficient approved questions'))
  render(
    <MemoryRouter>
      <PersonalizedAssessment assessments={templates} />
    </MemoryRouter>,
  )
  await userEvent.click(screen.getByLabelText(/Joins/))
  const button = screen.getByRole('button', { name: 'Start assessment' })
  await userEvent.click(button)
  expect(await screen.findByRole('alert')).toHaveTextContent('Insufficient approved questions')
  expect(screen.getByLabelText(/Joins/)).toBeChecked()
  await userEvent.click(button)
  await waitFor(() => expect(api.post).toHaveBeenCalledTimes(2))
  expect(api.post.mock.calls[0][1]).toEqual(api.post.mock.calls[1][1])
})

it('offers an explicit formal format that retains the configured examination contract', async () => {
  api.post.mockRejectedValue(new Error('Pool incomplete'))
  render(
    <MemoryRouter>
      <PersonalizedAssessment assessments={templates} />
    </MemoryRouter>,
  )
  await userEvent.selectOptions(screen.getByLabelText('Assessment format'), 'FORMAL')
  expect(screen.queryByLabelText('Number of questions')).not.toBeInTheDocument()
  await userEvent.click(screen.getByLabelText(/Joins/))
  await userEvent.click(screen.getByRole('button', { name: 'Start assessment' }))
  await waitFor(() =>
    expect(api.post).toHaveBeenCalledWith(
      '/assessments/1/sessions',
      expect.objectContaining({ concept_ids: [2], difficulty: 'EASY' }),
    ),
  )
  expect(api.post.mock.calls[0][1]).not.toHaveProperty('question_count')
})

it('offers optional single-skill adaptive practice without exposing algorithm controls', async () => {
  api.post.mockRejectedValue(new Error('Inventory insufficient'))
  render(
    <MemoryRouter>
      <PersonalizedAssessment assessments={templates} />
    </MemoryRouter>,
  )
  await userEvent.selectOptions(screen.getByLabelText('Assessment format'), 'ADAPTIVE')
  expect(screen.queryByLabelText('Number of questions')).not.toBeInTheDocument()
  await userEvent.click(screen.getByLabelText('Joins'))
  await userEvent.click(screen.getByRole('button', { name: 'Start assessment' }))
  await waitFor(() =>
    expect(api.post).toHaveBeenCalledWith(
      '/assessments/1/sessions',
      expect.objectContaining({ mode: 'ADAPTIVE', concept_ids: [2], difficulty: 'EASY' }),
    ),
  )
  await userEvent.click(screen.getByLabelText('Filtering'))
  expect(screen.getByRole('button', { name: 'Start assessment' })).toBeDisabled()
})

it('preserves an existing human-verification policy when reopening the assessment editor', async () => {
  const assessment = {
    assessment_id: 1,
    title: 'Verified draft',
    status: 'draft',
    result_release_policy: 'HUMAN_VERIFIED',
    concepts: [],
    max_questions: 13,
    duration_min: 60,
  }
  api.get.mockImplementation((url) =>
    Promise.resolve({
      data:
        url === '/admin/assessments'
          ? [assessment]
          : url === '/admin/assessments/1'
            ? assessment
            : [],
    }),
  )
  render(
    <MemoryRouter>
      <AdminAssessmentsPage />
    </MemoryRouter>,
  )
  await userEvent.click(await screen.findByRole('button', { name: 'Edit', exact: true }))
  expect(await screen.findByLabelText('Result release policy')).toHaveValue('HUMAN_VERIFIED')
})

it('displays pending verification without attempting to render grading evidence', async () => {
  api.get.mockRejectedValue({
    response: {
      data: { error: { code: 'results_pending', details: { release_status: 'pending_review' } } },
    },
  })
  render(
    <MemoryRouter initialEntries={['/history/9']}>
      <Routes>
        <Route path="/history/:sessionId" element={<EvidencePage />} />
      </Routes>
    </MemoryRouter>,
  )
  expect(
    await screen.findByRole('heading', { name: 'Your submission is received' }),
  ).toBeInTheDocument()
  expect(screen.getByRole('status')).toHaveTextContent(
    'An instructor will grade the essay or verify automatic scores',
  )
  expect(screen.queryByText('Automated suggested score')).not.toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Refresh status' }))
  await waitFor(() => expect(api.get).toHaveBeenCalledTimes(2))
})

it('shows instructor-readable AI feedback and citations without a raw implementation object', async () => {
  const graded = {
    ...pending,
    items: [
      {
        ...pending.items[0],
        question_type: 'essay',
        automated_score: '4.38',
        automated_detail: {
          grader: 'essay_llm',
          feedback: 'Add a lossless-join example.',
          explanation: 'Dependencies are correct.',
          matched_criteria: ['Functional dependencies'],
          evidence: ['The key determines grade.'],
        },
      },
    ],
  }
  api.get.mockImplementation((path) =>
    Promise.resolve({ data: path === '/admin/grading-reviews' ? [graded] : graded }),
  )
  render(
    <MemoryRouter>
      <AdminGradingPage />
    </MemoryRouter>,
  )
  await userEvent.click(await screen.findByRole('button', { name: /Test learner.*Database rules/ }))
  await userEvent.click(await screen.findByText('Automated feedback and SQL evaluation'))
  expect(screen.getByText('Add a lossless-join example.')).toBeVisible()
  expect(screen.getByText('The key determines grade.')).toBeVisible()
  expect(screen.queryByText(/"grader"/)).not.toBeInTheDocument()
})

it('supports a cumulative empty state with no invented scores', async () => {
  api.get.mockImplementation((path) =>
    Promise.resolve({
      data:
        path === '/sessions/competency/cumulative'
          ? { concepts: [], gaps: [], summary: { finalized_assessments: 0 } }
          : path === '/sessions/ranking'
            ? { rank: null, participants: 0 }
            : {
                dimensions: {
                  overall: { competency_pct: null },
                  clos: [],
                  topics: [],
                  difficulties: [],
                },
                graded_sessions: 0,
                published_formal_sessions: 0,
                pending_formal_sessions: 0,
                progress: [],
                score_distribution: [],
                ranking: [],
              },
    }),
  )
  render(
    <MemoryRouter>
      <CumulativePage />
    </MemoryRouter>,
  )
  expect(await screen.findByText('No published formal assessment yet')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Start assessment' })).toHaveAttribute(
    'href',
    '/assessments',
  )
  expect(screen.queryByText('Cumulative score')).not.toBeInTheDocument()
  expect(screen.queryByText('Your rank')).not.toBeInTheDocument()
  expect(api.get).toHaveBeenCalledWith('/sessions/competency/cumulative')
  expect(screen.queryByTestId('cumulative-chart')).not.toBeInTheDocument()
})

it('shows the approved result and teacher comments in published learner evidence', async () => {
  api.get.mockResolvedValue({
    data: {
      session_id: 9,
      status: 'completed',
      items: [
        {
          seq_no: 1,
          attempt_id: 21,
          question_id: 3,
          question_type: 'essay',
          prompt: 'Explain a database concept',
          difficulty_level: 3,
          points: '1',
          score: '0.5',
          concepts: [],
          options: [],
          rubrics: [],
          essay_answer: 'Recorded learner response',
          grading_detail: {
            grader: 'human_verified',
            reviewer_comments: 'Explain the missing dependency before decomposing the relation.',
          },
        },
      ],
    },
  })
  render(
    <MemoryRouter initialEntries={['/history/9']}>
      <Routes>
        <Route path="/history/:sessionId" element={<EvidencePage />} />
      </Routes>
    </MemoryRouter>,
  )
  expect(
    await screen.findByText('Explain the missing dependency before decomposing the relation.'),
  ).toBeInTheDocument()
  expect(screen.getByText('Approved', { exact: true })).toBeInTheDocument()
})

it('renders cumulative evidence, weighted backend scores and recurring gaps', async () => {
  const concept = {
    concept_id: 1,
    concept_name: 'Joins',
    concept_code: 'JOIN',
    points_earned: '1',
    points_possible: '10',
    competency_pct: '10.00',
    target_pct: '78',
    below_target: true,
    contributing_attempts: [1, 2],
    contributing_sessions: [1, 2],
    below_target_assessments: 1,
  }
  api.get.mockResolvedValue({
    data: { concepts: [concept], gaps: [concept], summary: { finalized_assessments: 2 } },
  })
  render(
    <MemoryRouter>
      <CumulativePage />
    </MemoryRouter>,
  )
  expect(await screen.findByText('2 published assessments')).toBeInTheDocument()
  expect(screen.getByText('10%')).toBeInTheDocument()
  expect(screen.getByText('2 questions · 2 assessments')).toBeInTheDocument()
  expect(screen.getByText('Below benchmark in 1 assessment')).toBeInTheDocument()
  expect(screen.getByTestId('cumulative-chart')).toBeInTheDocument()
})

it('filters cumulative concepts and explains a result on demand', async () => {
  const below = {
    concept_id: 1,
    concept_name: 'Joins',
    concept_code: 'JOIN',
    subject_area: 'Querying',
    points_earned: '4',
    points_possible: '10',
    competency_pct: '40.00',
    target_pct: '80',
    below_target: true,
    contributing_attempts: [1, 2],
    contributing_sessions: [1, 2],
    below_target_assessments: 2,
    meeting_target_assessments: 0,
  }
  const met = {
    concept_id: 2,
    concept_name: 'Indexes',
    concept_code: 'IDX',
    subject_area: 'Physical design',
    points_earned: '9',
    points_possible: '10',
    competency_pct: '90.00',
    target_pct: '80',
    below_target: false,
    contributing_attempts: [3],
    contributing_sessions: [2],
    below_target_assessments: 0,
    meeting_target_assessments: 1,
  }
  const neutral = {
    concept_id: 3,
    concept_name: 'Atomicity',
    concept_code: 'ATOM',
    subject_area: 'Transactions',
    points_earned: '6',
    points_possible: '10',
    competency_pct: '60.00',
    target_pct: null,
    below_target: false,
    contributing_attempts: [4],
    contributing_sessions: [1],
    below_target_assessments: 0,
    meeting_target_assessments: 0,
  }
  api.get.mockResolvedValue({
    data: { concepts: [below, met, neutral], gaps: [below], summary: { finalized_assessments: 2 } },
  })
  render(
    <MemoryRouter>
      <CumulativePage />
    </MemoryRouter>,
  )
  await screen.findByText('2 published assessments')
  expect(screen.getByText('Showing 3 of 3 concepts')).toBeInTheDocument()

  await userEvent.click(within(screen.getByRole('table')).getByRole('button', { name: /Joins/ }))
  expect(screen.getByText('What does this mean?')).toBeInTheDocument()
  expect(screen.getByText('40 percentage points below the benchmark.')).toBeInTheDocument()
  expect(screen.getByText(/Review Joins, then practice related questions/)).toBeInTheDocument()

  await userEvent.click(screen.getByRole('button', { name: /^Target met/ }))
  expect(screen.getByText('Showing 1 of 3 concepts')).toBeInTheDocument()
  expect(within(screen.getByRole('table')).getByText('Indexes')).toBeInTheDocument()
  expect(within(screen.getByRole('table')).queryByText('Joins')).not.toBeInTheDocument()

  await userEvent.click(screen.getByRole('button', { name: /^All/ }))
  await userEvent.type(screen.getByRole('searchbox', { name: 'Search concepts' }), 'atomicity')
  expect(within(screen.getByRole('table')).getByText('Atomicity')).toBeInTheDocument()
  expect(within(screen.getByRole('table')).queryByText('Indexes')).not.toBeInTheDocument()

  await userEvent.type(screen.getByRole('searchbox', { name: 'Search concepts' }), 'zzz')
  expect(screen.getByText('No concepts match these filters.')).toBeInTheDocument()
  expect(screen.queryByRole('table')).not.toBeInTheDocument()
})

it('provides SQL evidence and score correction, retaining concurrency revision', async () => {
  api.get.mockImplementation((url) =>
    Promise.resolve({ data: url === '/admin/grading-reviews' ? [pending] : pending }),
  )
  api.post.mockResolvedValue({
    data: {
      ...pending,
      release_status: 'reviewed',
      revision: 3,
      items: [
        {
          ...pending.items[0],
          revision: 1,
          review: { reviewer_id: 1, reviewed_at: '2026-10-18T00:00:00Z' },
          final_score: 1,
        },
      ],
    },
  })
  render(
    <MemoryRouter>
      <AdminGradingPage />
    </MemoryRouter>,
  )
  await userEvent.click(await screen.findByRole('button', { name: /Test learner.*Database rules/ }))
  expect(await screen.findByText('SELECT * FROM t')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Publish verified results' })).toBeDisabled()
  const input = screen.getByLabelText('Approved score')
  await userEvent.clear(input)
  await userEvent.type(input, '1')
  await userEvent.type(screen.getByLabelText('Grader comments'), 'Reviewed query semantics')
  await userEvent.click(screen.getByRole('button', { name: 'Approve score' }))
  await waitFor(() =>
    expect(api.post).toHaveBeenCalledWith('/admin/grading-reviews/9/attempts/21', {
      score: '1',
      comments: 'Reviewed query semantics',
      revision: 0,
    }),
  )
  await waitFor(() =>
    expect(screen.getByRole('button', { name: 'Publish verified results' })).toBeEnabled(),
  )
  await userEvent.click(screen.getByRole('button', { name: 'Publish verified results' }))
  expect(api.post).toHaveBeenLastCalledWith('/admin/grading-reviews/9/publish', { revision: 3 })
})

it('shows review conflicts and allows refreshing the current review', async () => {
  api.get.mockImplementation((url) =>
    Promise.resolve({ data: url === '/admin/grading-reviews' ? [pending] : pending }),
  )
  api.post.mockRejectedValue(new Error('Another grader updated this submission'))
  render(
    <MemoryRouter>
      <AdminGradingPage />
    </MemoryRouter>,
  )
  await userEvent.click(await screen.findByRole('button', { name: /Test learner.*Database rules/ }))
  await userEvent.click(await screen.findByRole('button', { name: 'Approve score' }))
  expect(await screen.findByRole('alert')).toHaveTextContent(
    'Another grader updated this submission',
  )
  expect(screen.getByRole('button', { name: 'Publish verified results' })).toBeDisabled()
})

it('saves the administrator result release policy', async () => {
  api.get.mockImplementation((url) =>
    Promise.resolve({ data: url === '/admin/concepts' ? templates[0].concepts : [] }),
  )
  api.post.mockResolvedValue({ data: { assessment_id: 1 } })
  render(
    <MemoryRouter>
      <AdminAssessmentsPage />
    </MemoryRouter>,
  )
  await userEvent.click(screen.getByRole('button', { name: 'New assessment' }))
  await userEvent.type(screen.getByLabelText('Assessment title'), 'Verified exam')
  await userEvent.selectOptions(screen.getByLabelText('Result release policy'), 'HUMAN_VERIFIED')
  const choices = screen.getAllByRole('combobox')
  const conceptSelect = choices.find((select) => [...select.options].some((o) => o.value === '2'))
  await userEvent.selectOptions(conceptSelect, '2')
  await userEvent.click(screen.getByRole('button', { name: 'Create draft' }))
  await waitFor(() =>
    expect(api.post).toHaveBeenCalledWith(
      '/admin/assessments',
      expect.objectContaining({ result_release_policy: 'HUMAN_VERIFIED' }),
    ),
  )
})

it('manages concept keywords and learning objectives in the existing curriculum form', async () => {
  api.get.mockResolvedValue({ data: [] })
  api.post.mockResolvedValue({ data: {} })
  render(
    <MemoryRouter>
      <AdminCurriculumPage />
    </MemoryRouter>,
  )
  const keyword = await screen.findByLabelText('Concept keywords (comma separated)')
  await userEvent.type(screen.getByLabelText('Concept code'), 'JOIN')
  await userEvent.type(screen.getByLabelText('Concept name'), 'Joins')
  await userEvent.type(screen.getByLabelText('Subject area'), 'SQL')
  await userEvent.type(keyword, 'join,relationship')
  await userEvent.type(
    screen.getByLabelText('Learning objectives (one per line)'),
    'Explain joins\nCompare outer joins',
  )
  await userEvent.click(screen.getByRole('button', { name: 'Add concept' }))
  await waitFor(() =>
    expect(api.post).toHaveBeenCalledWith(
      '/admin/concepts',
      expect.objectContaining({
        keywords: ['join', 'relationship'],
        learning_objectives: ['Explain joins', 'Compare outer joins'],
      }),
    ),
  )
})
