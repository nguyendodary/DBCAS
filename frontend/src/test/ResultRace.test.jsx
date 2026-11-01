import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Link, MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, expect, it, vi } from 'vitest'
import api from '../api'
import EvidencePage from '../pages/EvidencePage'
import HistoryPage from '../pages/HistoryPage'
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
    <Routes><Route path="/history/:sessionId" element={<EvidencePage />} /></Routes>
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
  render(<MemoryRouter><HistoryPage /></MemoryRouter>)
  const refresh = await screen.findByRole('button', { name: 'Refresh results', exact: true })
  await userEvent.click(refresh)
  await userEvent.click(refresh)
  expect(await screen.findByText(/100%/)).toBeInTheDocument()
  await act(async () => resolveOld({ data: [{ ...row, release_status: 'pending_review', overall_result_pct: null }] }))
  expect(screen.getByText(/100%/)).toBeInTheDocument()
})

it('loads the published result with a single refresh click', async () => {
  api.get.mockResolvedValueOnce({ data: [] }).mockResolvedValueOnce({ data: [{
    session_id: 3, assessment_title: 'Published', status: 'completed',
    release_status: 'published', overall_result_pct: '75', concepts: [],
  }] })
  render(<MemoryRouter><HistoryPage /></MemoryRouter>)
  await userEvent.click(await screen.findByRole('button', { name: 'Refresh results', exact: true }))
  expect(await screen.findByText(/75%/)).toBeInTheDocument()
  expect(api.get).toHaveBeenCalledTimes(2)
})

it('cancels a stalled refresh and retries without accepting its late failure', async () => {
  let rejectOld
  api.get.mockResolvedValueOnce({ data: [] })
    .mockReturnValueOnce(new Promise((resolve, reject) => { rejectOld = reject }))
    .mockResolvedValueOnce({ data: [] })
  render(<MemoryRouter><HistoryPage /></MemoryRouter>)
  const refresh = await screen.findByRole('button', { name: 'Refresh results', exact: true })
  await userEvent.click(refresh)
  const oldSignal = api.get.mock.calls[1][1].signal
  expect(refresh).toBeEnabled()
  await userEvent.click(refresh)
  expect(oldSignal.aborted).toBe(true)
  await act(async () => rejectOld(new Error('Old request failed')))
  expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  expect(refresh).toHaveAttribute('aria-busy', 'false')
})
