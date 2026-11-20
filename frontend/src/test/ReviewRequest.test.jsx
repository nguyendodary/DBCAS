import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, expect, it, vi } from 'vitest'
import api from '../api'
import EvaluationPage from '../pages/EvaluationPage'

vi.mock('../api', () => ({
  default: { get: vi.fn(), post: vi.fn() },
  apiMessage: () => 'Could not reach the server.',
}))
vi.mock('../components/EvaluationCharts', () => ({ EvaluationCharts: () => null }))

const reviewPath = '/sessions/7/review-request'
const sessionPath = '/sessions/7'
const evaluationPath = '/evaluations/attempts/7'
const session = {
  session_id: 7,
  runner_mode: 'fixed',
  purpose: 'TEST',
  can_request_review: true,
  review_window_expires_at: '2020-05-04T09:30:00Z',
  review_status: 'OFFICIAL',
}
const v1 = {
  status: 'ready',
  source: 'ai',
  final: true,
  is_current: true,
  result_version: 1,
  result: null,
  score: { earned: '7.00', possible: '10.00', percentage: 70 },
}
const v2 = {
  ...v1,
  result_version: 2,
  score: { earned: '8.00', possible: '10.00', percentage: 80 },
}
const clickName = 'Request admin review'
const reason = 'Please check the SQL grading.'
const responseError = (status, code) => ({ response: { status, data: { error: { code } } } })

function resultPage({ meta = session, review = null, readScore = () => v1 } = {}) {
  api.get.mockImplementation(async (path) => {
    if (path === sessionPath) return { data: meta }
    if (path === evaluationPath) return { data: readScore() }
    if (path !== reviewPath) throw new Error(`Unexpected path: ${path}`)
    const data = typeof review === 'function' ? review() : review
    if (data === null) throw responseError(404, 'review_not_found')
    return { data }
  })
  return render(
    <MemoryRouter initialEntries={['/evaluations/7']}>
      <Routes>
        <Route path="/evaluations/:sessionId" element={<EvaluationPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

async function enterReason() {
  const button = await screen.findByRole('button', { name: clickName })
  expect(button).toBeDisabled()
  fireEvent.change(screen.getByRole('textbox', { name: /reason for review/i }), {
    target: { value: reason },
  })
  return button
}

beforeEach(() => vi.resetAllMocks())

it('uses the server eligibility and displays the supplied deadline regardless of browser date', async () => {
  resultPage()
  expect(await screen.findByRole('button', { name: clickName })).toBeInTheDocument()
  expect(screen.getByText(/request a review by.*2020/i)).toBeInTheDocument()
  expect(screen.getByText('70.00%')).toBeInTheDocument()
})

it('hides submission when the server says the window has closed', async () => {
  resultPage({ meta: { ...session, can_request_review: false } })
  await waitFor(() => expect(api.get).toHaveBeenCalledWith(reviewPath, expect.any(Object)))
  expect(screen.queryByRole('button', { name: clickName })).not.toBeInTheDocument()
})

it.each([
  ['practice', { purpose: 'PRACTICE' }],
  ['adaptive', { runner_mode: 'adaptive' }],
  ['legacy', { review_status: 'LEGACY' }],
])('hides review and skips the review endpoint for %s', async (_kind, changes) => {
  resultPage({ meta: { ...session, ...changes } })
  await waitFor(() => expect(api.get).toHaveBeenCalledWith(sessionPath))
  expect(screen.queryByRole('button', { name: clickName })).not.toBeInTheDocument()
  expect(api.get.mock.calls.some(([path]) => path === reviewPath)).toBe(false)
})

it('posts once during a double submission, sends a UUID and replaces the form with Pending', async () => {
  let finish
  api.post.mockImplementation(
    () =>
      new Promise((resolve) => {
        finish = resolve
      }),
  )
  resultPage()
  const button = await enterReason()
  const form = button.closest('form')
  fireEvent.submit(form)
  fireEvent.submit(form)
  expect(button).toBeDisabled()
  expect(api.post).toHaveBeenCalledTimes(1)
  expect(api.post).toHaveBeenCalledWith(
    reviewPath,
    { reason },
    expect.objectContaining({
      headers: { 'Idempotency-Key': expect.stringMatching(/^[0-9a-f]{8}-[0-9a-f-]{27}$/i) },
    }),
  )
  finish({ data: { status: 'REQUESTED', v2_state: 'NONE' } })
  expect(await screen.findByText('Pending')).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: clickName })).not.toBeInTheDocument()
  expect(screen.getByText('V1 official')).toBeInTheDocument()
})

it.each([
  ['IN_REVIEW', 'In review'],
  ['REJECTED', 'Rejected'],
  ['EXPIRED', 'Expired'],
])('renders %s and offers no second request', async (status, label) => {
  resultPage({ review: { status, v2_state: 'NONE' } })
  expect(await screen.findByText(label)).toBeInTheDocument()
  expect(screen.getByText('V1 official')).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: clickName })).not.toBeInTheDocument()
})

it('keeps V1 through pending and failed analysis, then fetches the official V2 score', async () => {
  let review = { status: 'IN_REVIEW', v2_state: 'ANALYSIS_PENDING' }
  let score = v1
  resultPage({ review: () => review, readScore: () => score })
  expect(await screen.findByText('V2 analysis is pending.')).toBeInTheDocument()
  expect(screen.getByText('70.00%')).toBeInTheDocument()
  review = {
    status: 'IN_REVIEW',
    v2_state: 'ANALYSIS_FAILED_V1_KEPT',
    claimed_by: 9571,
    resolved_by: 9572,
    resolution_note: 'Private admin comment',
  }
  fireEvent.click(screen.getByRole('button', { name: 'Check review status' }))
  expect(await screen.findByText('v1 kept, admin will retry')).toBeInTheDocument()
  expect(screen.getByText('V1 official')).toBeInTheDocument()
  expect(screen.getByText('70.00%')).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: /retry/i })).not.toBeInTheDocument()
  expect(screen.queryByText(/9571|9572|private admin comment/i)).not.toBeInTheDocument()
  review = { status: 'REGRADED', v2_state: 'OFFICIAL' }
  score = v2
  fireEvent.click(screen.getByRole('button', { name: 'Check review status' }))
  expect(await screen.findByText('80.00%')).toBeInTheDocument()
  expect(screen.getByText('V2 official')).toBeInTheDocument()
  expect(screen.queryByText('70.00%')).not.toBeInTheDocument()
  expect(api.post).not.toHaveBeenCalled()
})

it.each([
  [403, 'review_forbidden', 'You cannot access this review request.'],
  [404, 'session_not_found', 'This review request is unavailable.'],
])('fails closed on review GET %i while keeping V1 visible', async (status, code, message) => {
  resultPage({
    review: () => {
      throw responseError(status, code)
    },
  })
  expect(await screen.findByRole('alert')).toHaveTextContent(message)
  expect(screen.getByText('70.00%')).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: clickName })).not.toBeInTheDocument()
})

it.each([
  [403, 'review_forbidden', 'You cannot access this review request.'],
  [404, 'session_not_found', 'This review request is unavailable.'],
  [409, 'review_window_closed', 'The review request window has closed.'],
])('closes the form when submission returns %i', async (status, code, message) => {
  api.post.mockRejectedValue(responseError(status, code))
  resultPage()
  fireEvent.click(await enterReason())
  expect(await screen.findByRole('alert')).toHaveTextContent(message)
  expect(screen.queryByRole('button', { name: clickName })).not.toBeInTheDocument()
  expect(screen.getByText('70.00%')).toBeInTheDocument()
})

it('reuses the original UUID and payload after a network error', async () => {
  api.post.mockRejectedValueOnce(new Error('network')).mockResolvedValueOnce({
    data: { status: 'REQUESTED', v2_state: 'NONE' },
  })
  resultPage()
  const button = await enterReason()
  fireEvent.click(button)
  expect(await screen.findByRole('alert')).toHaveTextContent('Could not reach the server.')
  expect(button).toBeEnabled()
  fireEvent.click(button)
  expect(await screen.findByText('Pending')).toBeInTheDocument()
  expect(api.post).toHaveBeenCalledTimes(2)
  expect(api.post.mock.calls[0]).toEqual(api.post.mock.calls[1])
})

it('loads the existing review after a duplicate from another browser tab', async () => {
  let review = null
  api.post.mockImplementation(async () => {
    review = { status: 'IN_REVIEW', v2_state: 'NONE' }
    throw responseError(409, 'review_exists')
  })
  resultPage({ review: () => review })
  fireEvent.click(await enterReason())
  expect(await screen.findByText('In review')).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: clickName })).not.toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Check review status' })).toBeEnabled()
})

it('recovers a failed V2 result fetch without displaying mismatched status and score', async () => {
  let review = { status: 'IN_REVIEW', v2_state: 'ANALYSIS_PENDING' }
  let score = v1
  resultPage({ review: () => review, readScore: () => score })
  await screen.findByText('V2 analysis is pending.')
  review = { status: 'REGRADED', v2_state: 'OFFICIAL' }
  fireEvent.click(screen.getByRole('button', { name: 'Check review status' }))
  expect(await screen.findByRole('alert')).toBeInTheDocument()
  expect(screen.getByText('70.00%')).toBeInTheDocument()
  expect(screen.queryByText('V2 official')).not.toBeInTheDocument()
  score = v2
  fireEvent.click(screen.getByRole('button', { name: 'Check review status' }))
  expect(await screen.findByText('V2 official')).toBeInTheDocument()
  expect(screen.getByText('80.00%')).toBeInTheDocument()
})
