import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import api from '../api'
import ExamPage from '../pages/ExamPage'

vi.mock('../api', async (importOriginal) => ({
  ...(await importOriginal()),
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn() },
}))

const NOW = '2030-01-01T00:00:00.000Z'
const END = '2030-01-01T00:30:00.000Z'

const state = (overrides = {}) => ({
  session_id: 42,
  assessment_id: null,
  assessment_title: 'Fixed paper',
  status: 'in_progress',
  runner_mode: 'fixed',
  locale: 'en',
  server_now: NOW,
  expires_at: END,
  remaining_seconds: 1800,
  current_question: null,
  ...overrides,
})

const metaQuestion = (seq, overrides = {}) => ({
  seq_no: seq,
  question_id: 100 + seq,
  question_type: seq === 2 ? 'essay' : 'mcq',
  answered: false,
  flagged: false,
  opened: seq === 1,
  draft_revision: 0,
  ...overrides,
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
  question_count: 3,
  answered_count: 0,
  flagged_count: 0,
  last_opened_seq: 1,
  questions: [metaQuestion(1), metaQuestion(2), metaQuestion(3)],
  ...overrides,
})

const question = (seq, overrides = {}) => ({
  seq_no: seq,
  question_id: 100 + seq,
  question_type: seq === 2 ? 'essay' : 'mcq',
  content_locale: 'en',
  prompt: `Question text ${seq}`,
  options:
    seq === 2
      ? []
      : [
          { option_id: seq * 10, option_label: 'A', option_text: 'First option' },
          { option_id: seq * 10 + 1, option_label: 'B', option_text: 'Second option' },
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
  ...overrides,
})

function mockApi({ stateOverrides, metaOverrides, views = {} } = {}) {
  api.get.mockImplementation((url) => {
    if (url === '/sessions/42') return Promise.resolve({ data: state(stateOverrides) })
    if (url === '/sessions/42/paper') return Promise.resolve({ data: metadata(metaOverrides) })
    const match = /^\/sessions\/42\/paper\/(\d+)$/.exec(url)
    if (match) {
      const seq = Number(match[1])
      return Promise.resolve({ data: views[seq] ?? question(seq) })
    }
    return Promise.reject(new Error(`Unexpected GET ${url}`))
  })
}

function mount() {
  return render(
    <MemoryRouter initialEntries={['/exam/42']}>
      <Routes>
        <Route path="/exam/:sessionId" element={<ExamPage />} />
        <Route path="/evaluations/:sessionId" element={<p>RESULTS MARKER</p>} />
        <Route path="/history/:sessionId" element={<p>RESULTS MARKER</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  sessionStorage.clear()
  vi.spyOn(performance, 'now').mockImplementation(() => 0)
  mockApi()
  api.put.mockResolvedValue({ data: { seq_no: 1, revision: 1, saved_at: NOW, answered: true } })
  api.post.mockResolvedValue({
    data: {
      status: 'completed',
      answered_count: 0,
      unanswered_count: 3,
      flagged_count: 0,
      final: true,
      next: '/evaluations/42',
    },
  })
})

afterEach(() => {
  vi.useRealTimers()
  vi.restoreAllMocks()
})

it('renders every question state in the palette and jumps freely by seq', async () => {
  mockApi({
    metaOverrides: {
      questions: [
        metaQuestion(1, { answered: true, flagged: true }),
        metaQuestion(2),
        metaQuestion(3),
      ],
    },
    views: {
      1: question(1, {
        answered: true,
        flagged: true,
        flag_revision: 1,
        draft: { selected_option_id: 10 },
        draft_revision: 3,
      }),
    },
  })
  mount()
  expect(
    await screen.findByRole('button', { name: 'Question 1, current, answered, flagged' }),
  ).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Question 2, unanswered' })).toBeEnabled()
  expect(screen.getByRole('button', { name: 'Question 3, unanswered' })).toBeEnabled()
  await userEvent.click(screen.getByRole('button', { name: 'Question 3, unanswered' }))
  expect(await screen.findByText('QUESTION 3 / 3')).toBeInTheDocument()
  expect(screen.getByText('Question text 3')).toBeInTheDocument()
  expect(api.get).toHaveBeenCalledWith('/sessions/42/paper/3')
  expect(screen.queryByRole('button', { name: 'Submit answer & continue' })).not.toBeInTheDocument()
})

it('toggles a flag with its revision and mirrors it in the palette', async () => {
  api.put.mockImplementation((url, body) =>
    url.endsWith('/flag')
      ? Promise.resolve({ data: { seq_no: 1, flagged: body.flagged, revision: body.revision + 1 } })
      : Promise.resolve({ data: { seq_no: 1, revision: 1, saved_at: NOW, answered: true } }),
  )
  mount()
  await screen.findByText('Question text 1')
  await userEvent.click(screen.getByRole('button', { name: 'Flag for review' }))
  await waitFor(() =>
    expect(api.put).toHaveBeenCalledWith('/sessions/42/paper/1/flag', {
      flagged: true,
      revision: 0,
    }),
  )
  expect(
    await screen.findByRole('button', { name: 'Question 1, current, unanswered, flagged' }),
  ).toBeInTheDocument()
  api.put.mockResolvedValue({ data: { seq_no: 1, flagged: false, revision: 2 } })
  await userEvent.click(screen.getByRole('button', { name: 'Remove flag' }))
  expect(api.put).toHaveBeenLastCalledWith('/sessions/42/paper/1/flag', {
    flagged: false,
    revision: 1,
  })
})

it('reloads the latest flag state after a revision conflict instead of overwriting it', async () => {
  api.put.mockRejectedValueOnce({
    response: { data: { error: { code: 'flag_revision_conflict' } } },
  })
  let opens = 0
  api.get.mockImplementation((url) => {
    if (url === '/sessions/42') return Promise.resolve({ data: state() })
    if (url === '/sessions/42/paper') return Promise.resolve({ data: metadata() })
    if (url === '/sessions/42/paper/1') {
      opens += 1
      return Promise.resolve({
        data:
          opens === 1
            ? question(1)
            : question(1, { flagged: true, flag_revision: 4, answered: true }),
      })
    }
    return Promise.reject(new Error(`Unexpected GET ${url}`))
  })
  mount()
  await screen.findByText('Question text 1')
  await userEvent.click(screen.getByRole('button', { name: 'Flag for review' }))
  expect(
    await screen.findByText('The flag changed elsewhere. The latest state was reloaded.'),
  ).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Remove flag' })).toBeEnabled()
  expect(api.put).toHaveBeenCalledTimes(1)
})

it('autosaves a draft and supports an explicit retry after a failed save', async () => {
  api.put.mockRejectedValueOnce(new Error('Save interrupted')).mockResolvedValue({
    data: { seq_no: 2, revision: 1, saved_at: NOW, answered: true },
  })
  mockApi({
    metaOverrides: {
      last_opened_seq: 2,
      questions: [metaQuestion(1), metaQuestion(2), metaQuestion(3)],
    },
    views: { 2: question(2) },
  })
  mount()
  const editor = await screen.findByRole('textbox')
  fireEvent.change(editor, { target: { value: 'A normalized relation.' } })
  await waitFor(() =>
    expect(screen.getByRole('alert')).toHaveTextContent(
      'The draft could not be saved. Retry before leaving this question.',
    ),
  )
  expect(api.put).toHaveBeenCalledWith('/sessions/42/paper/2/draft', {
    revision: 1,
    essay_answer: 'A normalized relation.',
  })
  await userEvent.click(screen.getByRole('button', { name: 'Retry' }))
  await waitFor(() => expect(api.put).toHaveBeenCalledTimes(2))
  expect(api.put).toHaveBeenLastCalledWith('/sessions/42/paper/2/draft', {
    revision: 1,
    essay_answer: 'A normalized relation.',
  })
})

it('flushes the newest answer before a rapid jump and stays put when the save fails', async () => {
  mount()
  await screen.findByText('Question text 1')
  await userEvent.click(screen.getByRole('radio', { name: 'A: First option' }))
  await userEvent.click(screen.getByRole('button', { name: 'Question 3, unanswered' }))
  await waitFor(() =>
    expect(api.put).toHaveBeenCalledWith('/sessions/42/paper/1/draft', {
      revision: 1,
      selected_option_id: 10,
    }),
  )
  expect(await screen.findByText('Question text 3')).toBeInTheDocument()

  api.put.mockRejectedValue(new Error('Save interrupted'))
  api.get.mockImplementation((url) => {
    if (url === '/sessions/42') return Promise.resolve({ data: state() })
    if (url === '/sessions/42/paper') return Promise.resolve({ data: metadata() })
    if (url === '/sessions/42/paper/1')
      return Promise.resolve({
        data: question(1, { answered: true, draft: { selected_option_id: 10 }, draft_revision: 1 }),
      })
    return Promise.reject(new Error(`Unexpected GET ${url}`))
  })
  await userEvent.click(screen.getByRole('button', { name: /Question 1,/ }))
  await userEvent.click(screen.getByRole('radio', { name: 'B: Second option' }))
  await userEvent.click(screen.getByRole('button', { name: 'Question 2, unanswered' }))
  expect(await screen.findByRole('alert')).toHaveTextContent(
    'The draft could not be saved. Retry before leaving this question.',
  )
  expect(screen.getByText('Question text 1')).toBeInTheDocument()
  expect(screen.queryByText('Question text 2')).not.toBeInTheDocument()
})

it('resumes the last opened question with its saved draft, flag and server clock', async () => {
  mockApi({
    metaOverrides: {
      last_opened_seq: 2,
      questions: [
        metaQuestion(1),
        metaQuestion(2, { answered: true, flagged: true }),
        metaQuestion(3),
      ],
    },
    views: {
      2: question(2, {
        draft: { essay_answer: 'Restored answer.' },
        draft_revision: 5,
        answered: true,
        flagged: true,
        flag_revision: 3,
      }),
    },
  })
  mount()
  expect(await screen.findByRole('textbox')).toHaveValue('Restored answer.')
  expect(
    screen.getByRole('button', { name: 'Question 2, current, answered, flagged' }),
  ).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Remove flag' })).toBeInTheDocument()
  expect(screen.getByLabelText('Time remaining')).toHaveTextContent('30:00')
  expect(api.post).not.toHaveBeenCalled()
})

it('confirms answered, unanswered and flagged counts and submits the whole paper once', async () => {
  let release
  api.post.mockImplementationOnce(
    () =>
      new Promise((resolve) => {
        release = resolve
      }),
  )
  mount()
  await screen.findByText('Question text 1')
  await userEvent.click(screen.getByRole('button', { name: 'Submit final answers' }))
  const dialog = await screen.findByRole('dialog')
  expect(dialog).toHaveTextContent('You answered 0 of 3 questions')
  expect(dialog).toHaveTextContent('left 3 unanswered')
  expect(dialog).toHaveTextContent('flagged 0 for review')
  const confirm = within(dialog).getByRole('button', { name: 'Submit final answers' })
  await act(async () => {
    fireEvent.click(confirm)
    fireEvent.click(confirm)
  })
  expect(api.post).toHaveBeenCalledTimes(1)
  await act(async () => {
    release({
      data: {
        status: 'completed',
        answered_count: 0,
        unanswered_count: 3,
        flagged_count: 0,
        final: true,
        next: '/evaluations/42',
      },
    })
  })
  expect(await screen.findByText('RESULTS MARKER')).toBeInTheDocument()
})

it('finalizes automatically when the server clock reaches zero', async () => {
  mockApi({
    stateOverrides: { server_now: NOW, expires_at: NOW, remaining_seconds: 0 },
    metaOverrides: { server_now: NOW, expires_at: NOW, remaining_seconds: 0 },
    views: { 1: question(1, { server_now: NOW, remaining_seconds: 0 }) },
  })
  mount()
  expect(await screen.findByText('RESULTS MARKER', {}, { timeout: 3000 })).toBeInTheDocument()
  expect(api.post).toHaveBeenCalledWith(
    '/sessions/42/paper/submit',
    expect.objectContaining({ request_id: expect.any(String) }),
  )
})

it('routes to results when a draft save loses the race against expiry', async () => {
  api.put.mockRejectedValue({
    response: { data: { error: { code: 'session_expired', message: 'expired' } } },
  })
  mount()
  await screen.findByText('Question text 1')
  fireEvent.click(screen.getByRole('radio', { name: 'A: First option' }))
  await waitFor(() => expect(screen.getByText('RESULTS MARKER')).toBeInTheDocument())
  expect(api.post).toHaveBeenCalledWith('/sessions/42/paper/submit', {})
})
