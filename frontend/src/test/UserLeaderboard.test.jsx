import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, expect, it, vi } from 'vitest'
import api from '../api'
import UserLeaderboard from '../components/UserLeaderboard'

vi.mock('../api', () => ({ default: { get: vi.fn() }, apiMessage: e => e.message }))
vi.mock('../auth', () => ({ useAuth: () => ({ account: { account_id: 1 } }) }))
const rows = Array.from({ length: 12 }, (_, i) => ({ account_id: i + 1, full_name: `Student ${i + 1}`,
  email: `private${i + 1}@example.test`, rank: i + 1, average_pct: 90 - i, assessments_graded: 2 }))
beforeEach(() => { vi.clearAllMocks(); api.get.mockResolvedValue({ data: rows }) })

it('shows the same top-three preview with learner links and no emails', async () => {
  const { container } = render(<MemoryRouter><UserLeaderboard /></MemoryRouter>)
  expect(await screen.findByText('Student 1')).toBeInTheDocument()
  expect(screen.getByText('Student 1').closest('.leaderboard-winner')).toBeInTheDocument()
  expect(screen.getByText('You')).toBeInTheDocument()
  expect(within(screen.getByRole('table')).getByText('Student 4')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'View all students' })).toHaveAttribute('href', '/leaderboard')
  expect(container.querySelector('a[href^="/admin"]')).not.toBeInTheDocument()
  expect(screen.queryByText(/private1@example/)).not.toBeInTheDocument()
  expect(api.get).toHaveBeenCalledWith('/sessions/leaderboard', expect.any(Object))
})

it('searches by student name and paginates the full ranking', async () => {
  render(<MemoryRouter><UserLeaderboard full /></MemoryRouter>)
  await screen.findByText('Student 1')
  await userEvent.click(screen.getByRole('button', { name: 'Next', exact: true }))
  expect(screen.getByText('Student 12')).toBeInTheDocument()
  const search = screen.getByRole('searchbox', { name: 'Search by student name...' })
  await userEvent.type(search, 'Student 12')
  expect(screen.getByText('Student 12')).toBeInTheDocument()
  expect(screen.queryByText('Student 11')).not.toBeInTheDocument()
  await userEvent.clear(search)
  await userEvent.type(search, 'private12@example.test')
  expect(screen.getByText('No matching students')).toBeInTheDocument()
})
