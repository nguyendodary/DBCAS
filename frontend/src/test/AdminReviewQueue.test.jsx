import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, expect, it, vi } from 'vitest'
import api from '../api'
import { useAuth } from '../auth'
import AdminGradingPage from '../pages/admin/AdminGradingPage'

vi.mock('../api', () => ({
  default: { get: vi.fn(), post: vi.fn() },
  apiMessage: () => 'Request failed',
}))

vi.mock('../auth', () => ({ useAuth: vi.fn() }))

const queuePath = '/admin/review-requests'
const path = queuePath + '/7'
const request = {
  review_request_id: 7,
  session_id: 42,
  learner_name: 'Synthetic Learner',
  status: 'REQUESTED',
  revision: 0,
  reason: 'Please verify the MCQ score.',
  question_reports: [],
  deviations: [],
}

function setup(accountId, detail = request) {
  useAuth.mockReturnValue({ account: { account_id: accountId } })
  api.get.mockImplementation(async (url) => ({ data: url === queuePath ? [detail] : detail }))
  return render(
    <MemoryRouter initialEntries={['/admin/grading?queue=review-requests']}>
      <AdminGradingPage />
    </MemoryRouter>,
  )
}

async function open() {
  fireEvent.click(await screen.findByRole('button', { name: /Review #7 · Synthetic Learner/ }))
  await screen.findByRole('link', { name: 'Open submitted result' })
}

beforeEach(() => vi.resetAllMocks())

it('claims a case by revision and requires a note for approval', async () => {
  setup(9)
  await open()
  const claimed = { ...request, revision: 1, status: 'IN_REVIEW', claimed_by: 9 }
  api.post.mockImplementationOnce(async () => {
    api.get.mockImplementation(async (url) => ({ data: url === queuePath ? [claimed] : claimed }))
    return { data: claimed }
  })
  fireEvent.click(screen.getByRole('button', { name: 'Claim review' }))
  const approve = await screen.findByRole('button', { name: 'Approve and regrade' })
  await waitFor(() => expect(api.get).toHaveBeenCalledWith(path, expect.any(Object)))
  expect(approve).toBeDisabled()
  expect(api.post).toHaveBeenCalledWith(path + '/claim', { expected_revision: 0 })
  fireEvent.change(screen.getByRole('textbox', { name: /Action note/ }), {
    target: { value: 'Synthetic adjudication of the submitted result.' },
  })
  api.post.mockResolvedValueOnce({
    data: { ...claimed, regraded_result_version_id: 11, analysis_status: 'ANALYSIS_FAILED' },
  })
  fireEvent.click(approve)
  await waitFor(() =>
    expect(api.post).toHaveBeenCalledWith(path + '/decision', {
      expected_revision: 1,
      outcome: 'APPROVE',
      note: 'Synthetic adjudication of the submitted result.',
    }),
  )
})

it('offers score confirmation to the nominee and keeps decision controls with the claimant', async () => {
  setup(10, {
    ...request,
    revision: 1,
    status: 'IN_REVIEW',
    claimed_by: 9,
    deviations: [{ deviation_id: 5, ai_score: 1, reviewed_score: 0, second_reviewer_id: 10 }],
  })
  await open()
  expect(screen.queryByRole('button', { name: 'Approve and regrade' })).toBeNull()
  api.post.mockResolvedValueOnce({ data: { deviation_id: 5, confirmed_by: 10 } })
  fireEvent.click(screen.getByRole('button', { name: 'Confirm score change' }))
  expect(await screen.findByText(/Confirmed/)).toBeInTheDocument()
  expect(api.post).toHaveBeenCalledWith(path + '/deviations/5/confirm', undefined)
})
