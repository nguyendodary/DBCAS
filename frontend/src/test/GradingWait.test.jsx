import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, expect, it, vi } from 'vitest'
import api from '../api'
import AssessmentReviewPage from '../pages/AssessmentReviewPage'
import AssessmentAttemptPage from '../pages/AssessmentAttemptPage'
import GradingStatusPanel from '../components/GradingStatusPanel'
import usePendingResults from '../usePendingResults'

vi.mock('../api', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn() },
  apiMessage: (error, fallback) => error?.message || fallback,
}))

const question = {
  question_id: 30,
  question_type: 'mcq',
  prompt: 'Which statement retrieves all columns?',
  difficulty_level: 1,
  points: '1.00',
  concepts: ['SQL-SELECT'],
  options: [{ option_id: 1, option_label: 'A', option_text: 'SELECT * FROM t' }],
}
const session = {
  session_id: 42,
  assessment_id: 5,
  assessment_title: 'PostgreSQL Midterm',
  status: 'in_progress',
  served_count: 1,
  answered_count: 0,
  max_questions: 13,
  remaining_seconds: 3540,
  done: false,
  current_question: question,
}

afterEach(() => vi.useRealTimers())

function resultsPending(status) {
  return Promise.reject({ response: { data: { error: { code: 'results_pending', details: { release_status: status } } } } })
}

function mountEvidence() {
  return render(
    <MemoryRouter initialEntries={['/history/42']}>
      <Routes>
        <Route path="/history/:sessionId" element={<AssessmentReviewPage />} />
        <Route path="/history" element={<p>Assessment history</p>} />
        <Route path="/exam/:sessionId" element={<AssessmentAttemptPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

it('restores the authoritative automatic-grading wait state when a finalized exam is refreshed', async () => {
  api.get.mockImplementation((url) => url === '/sessions/42'
    ? Promise.resolve({ data: { ...session, status: 'completed', release_status: 'auto_grading' } })
    : resultsPending('auto_grading'))
  render(
    <MemoryRouter initialEntries={['/exam/42']}>
      <Routes>
        <Route path="/exam/:sessionId" element={<AssessmentAttemptPage />} />
        <Route path="/history/:sessionId" element={<AssessmentReviewPage />} />
      </Routes>
    </MemoryRouter>,
  )
  expect(await screen.findByRole('heading', { name: 'We’re grading your assessment' })).toBeInTheDocument()
  expect(screen.getByRole('status')).toHaveAttribute('aria-busy', 'true')
  expect(screen.getByRole('link', { name: 'Go to Assessment History' })).toHaveAttribute('href', '/history')
})

it('switches from grading to human review without exposing provisional results', async () => {
  const states = ['auto_grading', 'pending_review']
  api.get.mockImplementation(() => resultsPending(states.shift() || 'pending_review'))
  mountEvidence()
  expect(await screen.findByRole('heading', { name: 'We’re grading your assessment' })).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Refresh status' }))
  expect(await screen.findByRole('heading', { name: 'Your submission is received' })).toBeInTheDocument()
  expect(screen.getByText(/Automated analysis is complete/)).toBeInTheDocument()
  expect(screen.queryByRole('heading', { name: /score|result:/i })).not.toBeInTheDocument()
  expect(document.querySelector('.animate-spin')).not.toBeInTheDocument()
})

it('shows the published evidence automatically for immediate release', async () => {
  api.get.mockResolvedValue({ data: { session_id: 42, status: 'completed', items: [] } })
  mountEvidence()
  expect(await screen.findByRole('heading', { name: 'Assessment evidence' })).toBeInTheDocument()
  expect(screen.getByText('No questions were served in this session')).toBeInTheDocument()
})

it('shows a safe recovery message when grading has failed', async () => {
  api.get.mockImplementation(() => resultsPending('grading_failed'))
  mountEvidence()
  expect(await screen.findByRole('heading', { name: 'Your submission needs grading attention' })).toBeInTheDocument()
  expect(screen.getByText(/grading could not finish automatically/)).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Refresh status' })).toBeEnabled()
  expect(document.querySelector('.animate-spin')).not.toBeInTheDocument()
  expect(screen.queryByText(/Traceback|llm_|provider/i)).not.toBeInTheDocument()
})

it('keeps the confirmed wait state and offers recovery after a transient status request failure', async () => {
  api.get.mockImplementationOnce(() => resultsPending('auto_grading')).mockRejectedValueOnce(new Error('Network disconnected'))
  mountEvidence()
  expect(await screen.findByRole('heading', { name: 'We’re grading your assessment' })).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Refresh status' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('We couldn’t check the latest status just now')
  expect(screen.getByRole('heading', { name: 'We’re grading your assessment' })).toBeInTheDocument()
})

it('allows the learner to refresh manually after bounded automatic polling', async () => {
  vi.useFakeTimers()
  function PollState({ refresh }) {
    const timedOut = usePendingResults(true, refresh)
    return <span>{timedOut ? 'Taking longer' : 'Waiting'}</span>
  }
  const refresh = vi.fn()
  render(<PollState refresh={refresh} />)
  expect(screen.getByText('Waiting')).toBeInTheDocument()
  await act(async () => { await vi.advanceTimersByTimeAsync(300_000) })
  expect(screen.getByText('Taking longer')).toBeInTheDocument()
  expect(refresh).toHaveBeenCalledTimes(60)
})

it('replaces the active grading message with a truthful long-wait notice', () => {
  render(<MemoryRouter><GradingStatusPanel status="auto_grading" timedOut /></MemoryRouter>)
  expect(screen.getByRole('heading', { name: 'Your result is taking longer than expected' })).toBeInTheDocument()
  expect(screen.getByText(/system has not reported grading completion yet/)).toBeInTheDocument()
  expect(document.querySelector('.animate-spin')).toBeInTheDocument()
  expect(document.querySelector('.animate-spin')).toHaveClass('motion-reduce:animate-none')
})
