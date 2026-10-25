import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'
import History_User from '../pages/user/History_User'
import api from '../api'

vi.mock('../api', () => ({ default: { get: vi.fn() }, apiMessage: (e) => e.message }))
const session = { session_id: 1, assessment_title: 'Recorded assessment', status: 'completed',
  started_at: '2026-10-10T10:00:00Z', submitted_at: '2026-10-10T11:00:00Z',
  served_count: 3, answered_count: 3, overall_result_pct: '42.25',
  concepts: [{ concept_id: 1, concept_name: 'Joins', competency_pct: '50.00', target_pct: '60.00', below_target: true },
    { concept_id: 2, concept_name: 'ER modeling', competency_pct: '100.00', target_pct: null, below_target: false }] }
const renderPage = () => render(<MemoryRouter><History_User /></MemoryRouter>)

it('shows the server answer result and per-concept history with an evidence link', async () => {
  api.get.mockResolvedValue({ data: [session] })
  renderPage()
  expect(await screen.findByText('Answer result: 42.25%')).toBeInTheDocument()
  expect(screen.getByText('Joins: 50.00% · below target')).toBeInTheDocument()
  expect(screen.getByText('ER modeling: 100.00% · no benchmark')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Evidence' })).toHaveAttribute('href', '/history/1')
})

it('distinguishes pending grading from a scored final result', async () => {
  api.get.mockResolvedValue({ data: [{ ...session, overall_result_pct: null, pending_grading_count: 1 }] })
  renderPage()
  expect(await screen.findByText('Grading pending')).toBeInTheDocument()
  expect(screen.queryByText(/Answer result:/)).not.toBeInTheDocument()
})

it('offers resume for an in-progress session instead of reporting final scores', async () => {
  api.get.mockResolvedValue({ data: [{ ...session, status: 'in_progress', overall_result_pct: null, concepts: [] }] })
  renderPage()
  expect(await screen.findByRole('link', { name: 'Resume' })).toHaveAttribute('href', '/exam/1')
  expect(screen.queryByText('Per-concept results')).not.toBeInTheDocument()
})
