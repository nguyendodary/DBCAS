import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { it, expect, vi } from 'vitest'
import api from '../api'
import AdminLeaderboardPage from '../pages/admin/AdminLeaderboardPage'
import LearnerLeaderboard from '../components/LearnerLeaderboard'

vi.mock('../api', () => ({ default: { get: vi.fn() }, apiMessage: e => e.message }))

it('shows all students with search, pagination and an unscored state', async () => {
  const leaderboard = Array.from({ length: 12 }, (_, i) => ({
    account_id: i + 1, email: `student${i + 1}@example.test`, full_name: `Student ${i + 1}`,
    rank: i === 11 ? null : i + 1, average_pct: i === 11 ? null : 95 - i,
    assessments_graded: i === 11 ? 0 : 2,
  }))
  api.get.mockImplementation(url => Promise.resolve({ data:
    url === '/admin/analytics/cohort' ? { learner_count: 11, finalized_sessions: 22, concepts: [], leaderboard }
      : url === '/admin/learners' ? leaderboard.map(row => ({ ...row, sessions_completed: 2 })) : [],
  }))
  render(<MemoryRouter initialEntries={['/admin/leaderboard?assessment_id=42']}><AdminLeaderboardPage /></MemoryRouter>)
  const table = within(await screen.findByRole('table', { name: '' }))
  expect(table.getByText('Student 1')).toBeInTheDocument()
  expect(table.queryByText('Student 12')).not.toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Next', exact: true }))
  expect(table.getByText('Student 12')).toBeInTheDocument()
  expect(table.queryByText('Student 1')).not.toBeInTheDocument()
  const search = screen.getByRole('searchbox', { name: 'Search students by name or email' })
  await userEvent.type(search, 'student12@example.test')
  expect(table.getByText('Student 12')).toBeInTheDocument()
  expect(table.getByText('No score yet')).toBeInTheDocument()
  expect(table.queryByText('Student 1')).not.toBeInTheDocument()
  await userEvent.clear(search)
  expect(table.getByText('Student 1')).toBeInTheDocument()
  await userEvent.type(search, 'nobody-matches')
  expect(screen.getByText('No matching students')).toBeInTheDocument()
  expect(api.get).toHaveBeenCalledWith('/admin/analytics/cohort', expect.objectContaining({ params: { assessment_id: 42 } }))
})

it('previews the top three above five more students and links to the full ranking', () => {
  const rows = Array.from({ length: 12 }, (_, i) => ({ account_id: i + 1,
    full_name: `Student ${i + 1}`, email: `student${i + 1}@example.test`,
    rank: i + 1, average_pct: 95 - i, assessments_graded: 2 }))
  render(<MemoryRouter><LearnerLeaderboard rows={rows} assessmentId="42" /></MemoryRouter>)
  expect(screen.getByText('Student 1').closest('.leaderboard-winner')).toBeInTheDocument()
  expect(screen.getByText('Student 2').closest('.leaderboard-winner')).toBeInTheDocument()
  expect(screen.getByText('Student 3').closest('.leaderboard-winner')).toBeInTheDocument()
  const table = within(screen.getByRole('table'))
  expect(table.getByText('Student 4')).toBeInTheDocument()
  expect(table.queryByText('Student 1')).not.toBeInTheDocument()
  expect(screen.queryByText('Student 9')).not.toBeInTheDocument()
  expect(screen.queryByRole('searchbox')).not.toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'View all students' })).toHaveAttribute('href', '/admin/leaderboard?assessment_id=42')
})
