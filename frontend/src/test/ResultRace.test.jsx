import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Link, MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, expect, it, vi } from 'vitest'
import api from '../api'
import AssessmentReviewPage from '../pages/AssessmentReviewPage'
import AssessmentHistoryPage from '../pages/AssessmentHistoryPage'
import { setLocale } from '../i18n'

vi.mock('../api', () => ({ default: { get: vi.fn() }, apiMessage: e => e.message }))
const pending = { response: { data: { error: { code: 'results_pending', details: { release_status: 'pending_review' } } } } }
const published = { session_id: 2, status: 'completed', items: [] }
beforeEach(async () => { vi.resetAllMocks(); await act(() => setLocale('en')) })

it.each(['published', 'pending'])('ignores an old %s evidence response after changing sessions', async oldState => {
  let resolveOld, rejectOld
  api.get.mockReturnValueOnce(new Promise((resolve, reject) => { resolveOld = resolve; rejectOld = reject }))
  if (oldState === 'published') api.get.mockRejectedValueOnce(pending)
  else api.get.mockResolvedValueOnce({ data: published })
  render(<MemoryRouter initialEntries={['/history/1']}>
    <Link to="/history/2">Next session</Link>
    <Routes><Route path="/history/:sessionId" element={<AssessmentReviewPage />} /></Routes>
  </MemoryRouter>)
  await userEvent.click(screen.getByRole('link', { name: 'Next session' }))
  const expected = oldState === 'published' ? 'Your submission is received' : 'Assessment evidence'
  expect(await screen.findByRole('heading', { name: expected, exact: true })).toBeInTheDocument()
  await act(async () => {
    if (oldState === 'published') resolveOld({ data: { ...published, session_id: 1 } })
    else rejectOld(pending)
  })
  expect(screen.getByRole('heading', { name: expected, exact: true })).toBeInTheDocument()
})

it('keeps published history when an older refresh returns a pending snapshot', async () => {
  let resolveOld
  const row = { session_id: 2, assessment_title: 'Latest published result', status: 'completed',
    release_status: 'published', started_at: '2026-10-18T00:00:00Z', answered_count: 1,
    served_count: 1, overall_result_pct: '100', concepts: [] }
  api.get.mockResolvedValueOnce({ data: [] })
    .mockReturnValueOnce(new Promise(resolve => { resolveOld = resolve }))
    .mockResolvedValueOnce({ data: [row] })
  render(<MemoryRouter><AssessmentHistoryPage /></MemoryRouter>)
  const refresh = await screen.findByRole('button', { name: 'Refresh results', exact: true })
  await userEvent.click(refresh)
  await userEvent.click(refresh)
  expect(await screen.findByText(/100%/)).toBeInTheDocument()
  await act(async () => resolveOld({ data: [{ ...row, release_status: 'pending_review', overall_result_pct: null }] }))
  expect(screen.getByText(/100%/)).toBeInTheDocument()
})
