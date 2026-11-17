import { act, fireEvent, render, renderHook, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import api from '../api'
import ExamPage from '../pages/ExamPage'
import { TAB_LEAVE_DEBOUNCE_MS, useTabLeaveGuard } from '../useTabLeaveGuard'

vi.mock('../api', async (importOriginal) => ({
  ...(await importOriginal()),
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn() },
}))

const NOW = '2030-01-01T00:00:00.000Z'
const END = '2030-01-01T00:30:00.000Z'

const leaveState = (count, overrides = {}) => ({
  session_id: 42,
  status: count >= 3 ? 'cancelled' : 'in_progress',
  violation_count: count,
  violation_limit: 3,
  grace_seconds: 3,
  counted: true,
  warning_level: count > 0 && count < 3 ? count : 0,
  cancelled: count >= 3,
  cancel_reason: count >= 3 ? 'tab_leave_limit' : null,
  server_now: NOW,
  ...overrides,
})

beforeEach(() => {
  vi.clearAllMocks()
  vi.useFakeTimers()
  sessionStorage.clear()
  vi.spyOn(performance, 'now').mockImplementation(() => 0)
})

afterEach(() => {
  vi.useRealTimers()
  vi.restoreAllMocks()
})

it('debounces focus transitions and adopts the server counter', async () => {
  let count = 0
  api.post.mockImplementation((url, body) => {
    if (url === '/sessions/42/paper/tab-leave') {
      if (body.event === 'return') count += 1
      return Promise.resolve({ data: leaveState(count) })
    }
    return Promise.resolve({ data: {} })
  })
  const { result } = renderHook(() =>
    useTabLeaveGuard({
      sessionId: 42,
      initialState: { violation_count: 0, violation_limit: 3, grace_seconds: 3 },
    }),
  )
  expect(result.current?.violation_count).toBe(0)

  act(() => window.dispatchEvent(new Event('blur')))
  await act(async () => vi.advanceTimersByTimeAsync(TAB_LEAVE_DEBOUNCE_MS + 10))
  expect(api.post).toHaveBeenCalledWith('/sessions/42/paper/tab-leave', {
    event: 'leave',
    event_id: expect.any(String),
  })
  expect(sessionStorage.getItem('dbcas-tab-leave:42')).toBeTruthy()

  act(() => window.dispatchEvent(new Event('focus')))
  await act(async () => vi.advanceTimersByTimeAsync(TAB_LEAVE_DEBOUNCE_MS + 10))
  expect(result.current.violation_count).toBe(1)
  expect(result.current.warning_level).toBe(1)
  expect(sessionStorage.getItem('dbcas-tab-leave:42')).toBeNull()

  // A duplicate focus does not create another event.
  const calls = api.post.mock.calls.length
  act(() => window.dispatchEvent(new Event('focus')))
  await act(async () => vi.advanceTimersByTimeAsync(TAB_LEAVE_DEBOUNCE_MS + 10))
  expect(api.post).toHaveBeenCalledTimes(calls)
})

const metadata = (overrides = {}) => ({
  session_id: 42,
  runner_mode: 'fixed',
  status: 'in_progress',
  assessment_title: 'Fixed paper',
  started_at: NOW,
  expires_at: END,
  server_now: NOW,
  remaining_seconds: 1800,
  question_count: 1,
  answered_count: 0,
  flagged_count: 0,
  last_opened_seq: 1,
  tab_leave_count: 0,
  tab_leave_grace_seconds: 3,
  tab_leave_violation_limit: 3,
  questions: [
    {
      seq_no: 1,
      question_id: 101,
      question_type: 'mcq',
      answered: false,
      flagged: false,
      opened: true,
      draft_revision: 0,
    },
  ],
  ...overrides,
})

const question = {
  seq_no: 1,
  question_id: 101,
  question_type: 'mcq',
  content_locale: 'en',
  prompt: 'Question text 1',
  options: [
    { option_id: 10, option_label: 'A', option_text: 'First option' },
    { option_id: 11, option_label: 'B', option_text: 'Second option' },
  ],
  schema_sql: null,
  draft: null,
  draft_revision: 0,
  answered: false,
  flagged: false,
  flag_revision: 0,
  first_opened_at: null,
  remaining_seconds: 1800,
  server_now: NOW,
}

function mountRunner() {
  return render(
    <MemoryRouter initialEntries={['/exam/42']}>
      <Routes>
        <Route path="/exam/:sessionId" element={<ExamPage />} />
        <Route path="/evaluations/:sessionId" element={<p>RESULTS MARKER</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

it('warns on the first two violations and renders the cancelled state on the third', async () => {
  let count = 0
  api.get.mockImplementation((url) => {
    if (url === '/sessions/42') {
      return Promise.resolve({
        data: {
          session_id: 42,
          status: 'in_progress',
          runner_mode: 'fixed',
          server_now: NOW,
          expires_at: END,
          remaining_seconds: 1800,
        },
      })
    }
    if (url === '/sessions/42/paper') return Promise.resolve({ data: metadata() })
    if (url === '/sessions/42/paper/1') return Promise.resolve({ data: question })
    return Promise.reject(new Error(`Unexpected GET ${url}`))
  })
  api.post.mockImplementation((url, body) => {
    if (url === '/sessions/42/paper/tab-leave') {
      if (body.event === 'return') count += 1
      return Promise.resolve({ data: leaveState(count) })
    }
    return Promise.resolve({ data: {} })
  })

  mountRunner()
  await act(async () => {})
  expect(screen.getByText('Question text 1')).toBeInTheDocument()

  const cycle = async () => {
    fireEvent.blur(window)
    await act(async () => vi.advanceTimersByTimeAsync(TAB_LEAVE_DEBOUNCE_MS + 10))
    fireEvent.focus(window)
    await act(async () => vi.advanceTimersByTimeAsync(TAB_LEAVE_DEBOUNCE_MS + 10))
  }

  await cycle()
  expect(screen.getByRole('alert')).toHaveTextContent('Warning 1 of 3')
  await cycle()
  expect(screen.getByRole('alert')).toHaveTextContent('Warning 2 of 3')
  await cycle()
  expect(screen.getByText('Attempt cancelled')).toBeInTheDocument()
  expect(screen.queryByText('Question text 1')).not.toBeInTheDocument()
  expect(api.post.mock.calls.filter(([, body]) => body?.event === 'return')).toHaveLength(3)
})
