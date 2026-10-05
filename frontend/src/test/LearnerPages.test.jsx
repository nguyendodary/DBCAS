import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { vi } from 'vitest'
import api from '../api'
import AssessmentsPage from '../pages/AssessmentsPage'
import HistoryPage from '../pages/HistoryPage'
import EvidencePage from '../pages/EvidencePage'

vi.mock('../api', () => ({
  default: { get: vi.fn(), post: vi.fn() },
  apiMessage: (e, fb) => e?.response?.data?.error?.message || e?.message || fb,
}))

const ACTIVE = [
  {
    assessment_id: 5,
    title: 'PostgreSQL Midterm',
    description: 'Covers querying and joins',
    max_questions: 13,
    duration_min: 60,
    concept_count: 4,
  },
]

const SESSIONS = [
  {
    session_id: 42,
    assessment_id: 5,
    assessment_title: 'PostgreSQL Midterm',
    status: 'completed',
    started_at: '2026-11-20T10:00:00Z',
    expires_at: '2026-11-20T11:00:00Z',
    submitted_at: '2026-11-20T10:30:00Z',
    served_count: 4,
    answered_count: 3,
  },
  {
    session_id: 43,
    assessment_id: 5,
    assessment_title: 'PostgreSQL Midterm',
    status: 'in_progress',
    started_at: '2026-11-21T10:00:00Z',
    expires_at: '2026-11-21T11:00:00Z',
    submitted_at: null,
    served_count: 2,
    answered_count: 1,
  },
]

function renderRoutes(initial, element, path) {
  return render(
    <MemoryRouter initialEntries={[initial]}>
      <Routes>
        <Route path={path} element={element} />
        <Route path="/exam/:id" element={<div>EXAM ROOM</div>} />
      </Routes>
    </MemoryRouter>
  )
}

beforeEach(() => vi.clearAllMocks())

describe('AssessmentsPage', () => {
  it('lists active assessments with duration and concept count', async () => {
    api.get.mockImplementation((url) => {
      if (url === '/assessments') return Promise.resolve({ data: ACTIVE })
      if (url === '/sessions') return Promise.resolve({ data: [] })
      return Promise.reject(new Error(url))
    })
    renderRoutes('/assessments', <AssessmentsPage />, '/assessments')
    expect(await screen.findByText('PostgreSQL Midterm')).toBeInTheDocument()
    expect(screen.getByText(/13 questions · 60 minutes · 4 concepts/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Start' })).toBeInTheDocument()
  })

  it('starts a session and navigates to the exam room', async () => {
    api.get.mockImplementation((url) => {
      if (url === '/assessments') return Promise.resolve({ data: ACTIVE })
      if (url === '/sessions') return Promise.resolve({ data: [] })
      return Promise.reject(new Error(url))
    })
    api.post.mockResolvedValue({ data: { session_id: 99 } })
    renderRoutes('/assessments', <AssessmentsPage />, '/assessments')
    await userEvent.click(await screen.findByRole('button', { name: 'Start' }))
    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/assessments/5/sessions')
    )
    expect(await screen.findByText('EXAM ROOM')).toBeInTheDocument()
  })

  it('offers Resume instead of Start when a live session exists', async () => {
    api.get.mockImplementation((url) => {
      if (url === '/assessments') return Promise.resolve({ data: ACTIVE })
      if (url === '/sessions') return Promise.resolve({ data: SESSIONS })
      return Promise.reject(new Error(url))
    })
    renderRoutes('/assessments', <AssessmentsPage />, '/assessments')
    await userEvent.click(await screen.findByRole('button', { name: 'Resume' }))
    // live session 43 → navigates straight to the exam, no POST
    expect(await screen.findByText('EXAM ROOM')).toBeInTheDocument()
    expect(api.post).not.toHaveBeenCalled()
  })

  it('shows an empty state when nothing is active', async () => {
    api.get.mockImplementation((url) =>
      Promise.resolve({ data: url === '/assessments' ? [] : [] })
    )
    renderRoutes('/assessments', <AssessmentsPage />, '/assessments')
    expect(await screen.findByText(/No assessments available/)).toBeInTheDocument()
  })
})

describe('HistoryPage', () => {
  it('renders sessions with status badges and the right links', async () => {
    api.get.mockResolvedValue({ data: SESSIONS })
    renderRoutes('/history', <HistoryPage />, '/history')
    const titles = await screen.findAllByText('PostgreSQL Midterm')
    expect(titles).toHaveLength(2)
    expect(screen.getByText('completed')).toBeInTheDocument()
    expect(screen.getByText('in progress')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Resume' })).toHaveAttribute('href', '/exam/43')
    expect(screen.getByRole('link', { name: 'Evidence' })).toHaveAttribute('href', '/history/42')
  })

  it('shows an empty state for a fresh learner', async () => {
    api.get.mockResolvedValue({ data: [] })
    renderRoutes('/history', <HistoryPage />, '/history')
    expect(await screen.findByText(/No sessions yet/)).toBeInTheDocument()
  })

  it('shows an error state when the request fails', async () => {
    api.get.mockRejectedValue({ response: { data: { error: { message: 'nope' } } } })
    renderRoutes('/history', <HistoryPage />, '/history')
    expect(await screen.findByRole('alert')).toHaveTextContent('nope')
  })
})

describe('EvidencePage', () => {
  const EVIDENCE = {
    session_id: 42,
    status: 'completed',
    items: [
      {
        attempt_id: 7,
        seq_no: 1,
        question_id: 30,
        question_type: 'mcq',
        prompt: 'Which retrieves all rows?',
        difficulty_level: 1,
        points: '1.00',
        score: '1.00',
        is_correct: true,
        served_at: '2026-11-20T10:01:00Z',
        submitted_at: '2026-11-20T10:02:00Z',
        selected_option_id: 2,
        options: [
          { option_id: 1, option_label: 'A', option_text: 'GET *', is_correct: false },
          { option_id: 2, option_label: 'B', option_text: 'SELECT *', is_correct: true },
        ],
        sql_answer: null,
        essay_answer: null,
        concepts: [{ concept_id: 10, concept_name: 'SELECT', concept_code: 'SQL-SELECT' }],
        grading_detail: { feedback: 'Well done' },
      },
    ],
  }

  it('renders the graded attempt with correct-answer evidence', async () => {
    api.get.mockResolvedValue({ data: EVIDENCE })
    renderRoutes('/history/42', <EvidencePage />, '/history/:sessionId')
    expect(await screen.findByText(/Which retrieves all rows/)).toBeInTheDocument()
    expect(screen.getByText(/SELECT \*/)).toBeInTheDocument()
    expect(screen.getByText(/\(your answer\)/)).toBeInTheDocument()
    expect(screen.getByText(/1.00 \/ 1.00 pts/)).toBeInTheDocument()
    expect(screen.getByText(/Well done/)).toBeInTheDocument()
    expect(api.get).toHaveBeenCalledWith('/sessions/42/evidence')
  })
})
