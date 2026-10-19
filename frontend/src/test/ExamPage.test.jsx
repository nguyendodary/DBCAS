import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { vi } from 'vitest'
import api from '../api'
import ExamPage from '../pages/ExamPage'

vi.mock('../api', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn() },
  apiMessage: (e, fb) => e?.response?.data?.error?.message || e?.message || fb,
}))

const MCQ = {
  question_id: 30,
  question_type: 'mcq',
  prompt: 'Which statement retrieves all columns?',
  difficulty_level: 1,
  points: '1.00',
  concepts: ['SQL-SELECT'],
  options: [
    { option_id: 1, option_label: 'A', option_text: 'GET * FROM t' },
    { option_id: 2, option_label: 'B', option_text: 'SELECT * FROM t' },
  ],
}

const STATE_MCQ = {
  session_id: 42,
  assessment_id: 5,
  assessment_title: 'PostgreSQL Midterm',
  status: 'in_progress',
  served_count: 1,
  answered_count: 0,
  max_questions: 13,
  remaining_seconds: 3540,
  done: false,
  current_question: MCQ,
}

const STATE_NEXT = {
  ...STATE_MCQ,
  served_count: 2,
  answered_count: 1,
  current_question: {
    question_id: 31,
    question_type: 'essay',
    prompt: 'Explain normalization.',
    difficulty_level: 2,
    points: '4.00',
    concepts: ['DB-NORM'],
  },
}

function renderExam() {
  return render(
    <MemoryRouter initialEntries={['/exam/42']}>
      <Routes>
        <Route path="/exam/:sessionId" element={<ExamPage />} />
        <Route path="/history/:sessionId" element={<div>ASSESSMENT RESULTS</div>} />
        <Route path="/dashboard" element={<div>DASHBOARD</div>} />
      </Routes>
    </MemoryRouter>
  )
}

beforeEach(() => { vi.resetAllMocks(); sessionStorage.clear(); api.put.mockImplementation((url, body) => Promise.resolve({ data: { revision: body.revision } })) })

describe('ExamPage', () => {
  it('shows saved feedback without a correctness verdict for human-verified results', async () => {
    api.get.mockResolvedValue({ data: { ...STATE_MCQ, result_release_policy: 'HUMAN_VERIFIED' } })
    api.post.mockResolvedValue({ data: { state: STATE_NEXT, answer: { score: null, is_correct: null, grading_status: 'graded', points_possible: '1' } } })
    renderExam()
    await userEvent.click(await screen.findByText('SELECT * FROM t'))
    await userEvent.click(screen.getByRole('button', { name: 'Submit answer & continue' }))
    expect(await screen.findByText('Answer saved. Official grading will be available after verification.')).toBeInTheDocument()
    expect(screen.queryByText(/Incorrect — scored/)).not.toBeInTheDocument()
  })
  it('renders the served MCQ with options and a countdown', async () => {
    api.get.mockResolvedValue({ data: STATE_MCQ })
    renderExam()
    expect(
      await screen.findByText('Which statement retrieves all columns?')
    ).toBeInTheDocument()
    expect(screen.getByText('SELECT * FROM t')).toBeInTheDocument()
    expect(screen.getByLabelText('Time remaining')).toHaveTextContent('59:00')
    expect(screen.getByText(/Question 1 of up to 13/)).toBeInTheDocument()
    // answer key must not be present in the served payload rendering
    expect(screen.queryByText(/correct/i)).not.toBeInTheDocument()
  })

  it('submits the selected option, shows feedback, and serves the next question', async () => {
    api.get
      .mockResolvedValueOnce({ data: STATE_MCQ })
      .mockResolvedValueOnce({ data: STATE_NEXT })
    api.post.mockImplementation((url) => {
      if (url === '/sessions/42/submit')
        return Promise.resolve({
          data: { state: STATE_NEXT, answer: {
            attempt_id: 7,
            session_id: 42,
            question_id: 30,
            score: '1.00',
            points_possible: '1.00',
            is_correct: true,
            submitted_at: 'x',
          } },
        })
      if (url === '/sessions/42/serve-next')
        return Promise.resolve({ data: { done: false } })
      return Promise.reject(new Error(url))
    })
    renderExam()
    await userEvent.click(await screen.findByText('SELECT * FROM t'))
    await userEvent.click(screen.getByRole('button', { name: 'Submit answer & continue' }))

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/sessions/42/submit', {
        question_id: 30,
        selected_option_id: 2,
      })
    )
    expect(api.post).not.toHaveBeenCalledWith('/sessions/42/serve-next')
    expect(api.put).toHaveBeenCalledWith('/sessions/42/draft', { question_id: 30, selected_option_id: 2, revision: 1 })
    expect(await screen.findByText(/Correct — scored 1.00 \/ 1.00 pts/)).toBeInTheDocument()
    expect(await screen.findByText('Explain normalization.')).toBeInTheDocument()
  })

  it('shows an error instead of crashing when grading fails', async () => {
    api.get.mockResolvedValue({ data: STATE_MCQ })
    api.post.mockRejectedValue({
      response: { data: { error: { message: 'rubric_not_configured' } } },
    })
    renderExam()
    await userEvent.click(await screen.findByText('SELECT * FROM t'))
    await userEvent.click(screen.getByRole('button', { name: 'Submit answer & continue' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('rubric_not_configured')
  })

  it('confirms and shows a submission wait state before opening results', async () => {
    api.get.mockResolvedValue({ data: STATE_MCQ })
    let finishRequest
    api.post.mockImplementation(() => new Promise(resolve => { finishRequest = resolve }))
    renderExam()
    await userEvent.click(
      await screen.findByRole('button', { name: 'Finish assessment' })
    )
    await userEvent.click(screen.getByRole('button', { name: 'Yes, finish' }))
    expect(await screen.findByRole('heading', { name: 'Submitting your assessment' })).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveAttribute('aria-busy', 'true')
    expect(screen.queryByText(/You can leave this page/)).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Yes, finish' })).not.toBeInTheDocument()
    expect(api.post).toHaveBeenCalledTimes(1)
    finishRequest({ data: { status: 'completed' } })
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/sessions/42/finish'))
    expect(await screen.findByText('ASSESSMENT RESULTS')).toBeInTheDocument()
  })

  it('keeps the session available when finishing fails', async () => {
    api.get.mockResolvedValue({ data: STATE_MCQ })
    api.post.mockRejectedValue(new Error('Server unavailable'))
    renderExam()
    await userEvent.click(await screen.findByRole('button', { name: 'Finish assessment' }))
    await userEvent.click(screen.getByRole('button', { name: 'Yes, finish' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Server unavailable')
    expect(screen.getByText('Which statement retrieves all columns?')).toBeInTheDocument()
    expect(screen.queryByText('DASHBOARD')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Finish assessment' })).toBeEnabled()
  })

  it('opens results when a refreshed session is already finalized', async () => {
    api.get.mockResolvedValue({ data: { ...STATE_MCQ, status: 'completed' } })
    renderExam()
    expect(await screen.findByText('ASSESSMENT RESULTS')).toBeInTheDocument()
  })

  it('renders a SQL question with a schema viewer and sandbox run', async () => {
    const sqlState = {
      ...STATE_MCQ,
      current_question: {
        question_id: 40,
        question_type: 'sql',
        prompt: 'List employees in dept 10.',
        difficulty_level: 2,
        points: '2.00',
        concepts: ['SQL-WHERE'],
        schema_sql: 'CREATE TABLE emp(id int, dept int);',
      },
    }
    api.get.mockResolvedValue({ data: sqlState })
    api.post.mockImplementation((url) => {
      if (url === '/sessions/42/sql-run')
        return Promise.resolve({
          data: {
            success: true,
            columns: ['id'],
            rows: [[1], [2]],
            row_count: 2,
            execution_time_ms: 12,
          },
        })
      return Promise.reject(new Error(url))
    })
    renderExam()
    await userEvent.type(
      await screen.findByPlaceholderText('SELECT ...'),
      'SELECT id FROM emp'
    )
    await userEvent.click(screen.getByRole('button', { name: 'Run in sandbox' }))
    expect(await screen.findByText('2 rows · 12 ms')).toBeInTheDocument()
    expect(api.post).toHaveBeenCalledWith('/sessions/42/sql-run', {
      question_id: 40,
      sql: 'SELECT id FROM emp',
    })
  })
})
