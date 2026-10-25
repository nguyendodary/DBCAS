import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, expect, it, vi } from 'vitest'
import api from '../api'
import CumulativeCompetency_User from '../pages/user/CumulativeCompetency_User'

vi.mock('../api', () => ({ default: { get: vi.fn() }, apiMessage: e => e.message }))

const needs = { concept_id: 1, concept_name: 'JOIN', concept_code: 'SQL-JOIN', subject_area: 'SQL',
  points_earned: '7', points_possible: '10', competency_pct: '70', target_pct: '80', below_target: true,
  contributing_attempts: [1, 2, 3], contributing_sessions: [4, 5], below_target_assessments: 1, meeting_target_assessments: 1 }
const met = { ...needs, concept_id: 2, concept_name: 'SELECT', concept_code: 'SQL-SELECT', competency_pct: '90', below_target: false }
const noTarget = { ...needs, concept_id: 3, concept_name: 'Transactions', target_pct: null, below_target: false }
beforeEach(() => api.get.mockResolvedValue({ data: { concepts: [needs, met, noTarget], gaps: [needs], summary: { finalized_assessments: 2 } } }))

it('shows student progress without formulas, point totals or internal record links', async () => {
  const { container } = render(<MemoryRouter><CumulativeCompetency_User /></MemoryRouter>)
  await screen.findByRole('heading', { name: 'Your concepts in detail' })
  expect(screen.getByRole('img', { name: 'JOIN: 70%; Target: 80%' })).toBeInTheDocument()
  const row = container.querySelector('.cumulative-skill.improve')
  expect(row).not.toHaveAttribute('open')
  await userEvent.click(row.querySelector('summary'))
  expect(row).toHaveAttribute('open')
  expect(within(row).queryByText(/7 \/ 10/)).not.toBeInTheDocument()
  expect(within(row).queryByText('How is this calculated?')).not.toBeInTheDocument()
  expect(within(row).getByText('10 percentage points below the target.')).toBeInTheDocument()
  expect(within(row).queryByRole('link')).not.toBeInTheDocument()
  expect(within(row).getByText('Below benchmark in 1 assessment')).toBeInTheDocument()
})

it('filters weak skills and keeps unbenchmarked results distinct from a failure', async () => {
  const { container } = render(<MemoryRouter><CumulativeCompetency_User /></MemoryRouter>)
  await screen.findByRole('heading', { name: 'Your concepts in detail' })
  await userEvent.click(screen.getByRole('button', { name: 'Needs improvement 1' }))
  expect(container.querySelectorAll('.cumulative-skill')).toHaveLength(1)
  await userEvent.click(screen.getByRole('button', { name: 'No target set 1' }))
  expect(container.querySelectorAll('.cumulative-skill')).toHaveLength(1)
  const row = container.querySelector('.cumulative-skill.neutral')
  expect(row).toHaveTextContent('Transactions')
  await userEvent.click(row.querySelector('summary'))
  expect(within(row).getByText('Graded evidence exists, but no benchmark is set. This is not a below-target result.')).toBeInTheDocument()
})

it('searches across all skills and leaves the backend percentages unchanged', async () => {
  const { container } = render(<MemoryRouter><CumulativeCompetency_User /></MemoryRouter>)
  await userEvent.type(await screen.findByRole('searchbox'), 'SQL-SELECT')
  expect(container.querySelectorAll('.cumulative-skill')).toHaveLength(1)
  expect(container.querySelector('.cumulative-skill')).toHaveTextContent('90%')
})

it('opens a priority concept directly even when the detail list is filtered', async () => {
  const { container } = render(<MemoryRouter><CumulativeCompetency_User /></MemoryRouter>)
  await screen.findByRole('heading', { name: 'Your concepts in detail' })
  await userEvent.click(screen.getByRole('button', { name: 'No target set 1' }))
  expect(container.querySelector('#cumulative-skill-1')).not.toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'JOIN', exact: true }))
  const row = container.querySelector('#cumulative-skill-1')
  expect(row).toHaveAttribute('open')
  expect(row.querySelector('summary')).toHaveFocus()
  expect(screen.getByRole('button', { name: 'All 3' })).toHaveAttribute('aria-pressed', 'true')
})
