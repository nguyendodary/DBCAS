import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Link, MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, expect, it, vi } from 'vitest'
import api from '../api'
import CumulativeCompetency_User from '../pages/user/CumulativeCompetency_User'
import { setLocale } from '../i18n'

vi.mock('../api', () => ({ default: { get: vi.fn() }, apiMessage: e => e.message }))
vi.mock('../components/CompetencyCharts', () => ({ CompetencyConceptBars: () => null }))

beforeEach(async () => { vi.resetAllMocks(); await act(() => setLocale('en')) })

it.each([
  ['refresh', 'success'], ['refresh', 'failure'],
  ['learner navigation', 'success'], ['learner navigation', 'failure'],
])('ignores an older cumulative response after %s (%s)', async (action, outcome) => {
  let resolveOld, rejectOld
  api.get.mockReturnValueOnce(new Promise((resolve, reject) => { resolveOld = resolve; rejectOld = reject }))
    .mockResolvedValueOnce({ data: { concepts: [], gaps: [], summary: { finalized_assessments: 2 } } })
  render(<MemoryRouter initialEntries={['/admin/learners/1/competency']}>
    <Link to="/admin/learners/2/competency">Next learner</Link>
    <Routes><Route path="/admin/learners/:learnerId/competency" element={<CumulativeCompetency_User />} /></Routes>
  </MemoryRouter>)
  await userEvent.click(screen.getByRole(action === 'refresh' ? 'button' : 'link', {
    name: action === 'refresh' ? 'Refresh results' : 'Next learner', exact: true,
  }))
  expect(await screen.findByText('2 published assessments')).toBeInTheDocument()
  await act(async () => {
    if (outcome === 'success') resolveOld({ data: { concepts: [], gaps: [], summary: { finalized_assessments: 1 } } })
    else rejectOld(new Error('Superseded request failed'))
  })
  expect(screen.getByText('2 published assessments')).toBeInTheDocument()
  expect(screen.queryByText('1 published assessment')).not.toBeInTheDocument()
  expect(screen.queryByRole('alert')).not.toBeInTheDocument()
})
