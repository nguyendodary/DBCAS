import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, expect, it, vi } from 'vitest'
import api from '../api'
import StatisticsPanel, { statisticsCsv } from '../components/StatisticsPanel'
import { setLocale } from '../i18n'

vi.mock('../api', () => ({ default: { get: vi.fn() }, apiMessage: (err) => err.message }))
const metric = { competency_pct: '75', evidence_count: 4, points_earned: '3', points_possible: '4' }
const stats = {
  dimensions: {
    overall: metric,
    clos: [{ ...metric, key: 'CLO1', label: 'CLO1 · Querying' }],
    topics: [{ ...metric, key: 'SQL', label: 'SQL' }],
    difficulties: [{ ...metric, key: '2', label: '2' }],
    clo_mapping_unknown_attempts: 0,
  },
  published_formal_sessions: 2,
  graded_sessions: 2,
  progress: [{ ...metric, session_id: 9, completed_at: '2026-11-02T00:00:00Z' }],
  progress_total: 1,
  score_distribution: [{ lower_bound: 60, upper_bound: 80, count: 2 }],
  ranking: [{ ...metric, learner_id: 77, rank: 1 }],
}
beforeEach(async () => {
  vi.resetAllMocks()
  await act(() => setLocale('en'))
})

it('shows real own rank and competency dimensions without a peer roster', async () => {
  api.get.mockImplementation((path) =>
    Promise.resolve({
      data: path.endsWith('/ranking') ? { rank: 2, participants: 3 } : { ...stats, ranking: [] },
    }),
  )
  render(
    <MemoryRouter>
      <StatisticsPanel />
    </MemoryRouter>,
  )
  expect(await screen.findByText('2 / 3')).toBeInTheDocument()
  await userEvent.click(
    screen.getByText('View competency details, progress and score distribution'),
  )
  expect(screen.getByText('CLO1 · Querying')).toBeVisible()
  expect(screen.getByRole('link', { name: /Nov/ })).toHaveAttribute('href', '/history/9')
  expect(screen.queryByText('Learner ranking')).not.toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Export CSV report' })).not.toBeInTheDocument()
})

it('uses the administrator assessment filter and exports an actual named ranking', async () => {
  api.get.mockResolvedValue({ data: stats })
  render(
    <MemoryRouter>
      <StatisticsPanel
        admin
        assessmentId="8"
        learners={[{ account_id: 77, full_name: 'Learner Linh' }]}
      />
    </MemoryRouter>,
  )
  expect(await screen.findByRole('button', { name: 'Export CSV report' })).toBeEnabled()
  expect(api.get).toHaveBeenCalledWith(
    '/admin/analytics/statistics',
    expect.objectContaining({ params: { assessment_id: 8, limit: 10, offset: 0 } }),
  )
  await userEvent.click(
    screen.getByText('View competency details, progress and score distribution'),
  )
  expect(screen.getByRole('link', { name: '1. Learner Linh' })).toHaveAttribute(
    'href',
    '/admin/learners/77/competency',
  )
  expect(statisticsCsv(stats, { 77: 'Learner Linh' })).toContain('"1","Learner Linh","75"')
})

it('retries a failed statistics load with one click', async () => {
  let first = true
  api.get.mockImplementation((path) => {
    if (path.endsWith('/ranking')) return Promise.resolve({ data: { rank: 1, participants: 1 } })
    if (first) {
      first = false
      return Promise.reject(new Error('Temporary failure'))
    }
    return Promise.resolve({ data: stats })
  })
  render(
    <MemoryRouter>
      <StatisticsPanel />
    </MemoryRouter>,
  )
  expect(await screen.findByRole('alert')).toHaveTextContent('Temporary failure')
  await userEvent.click(screen.getByRole('button', { name: /Retry|Try again/ }))
  expect(await screen.findByText('1 / 1')).toBeInTheDocument()
  expect(screen.queryByRole('alert')).not.toBeInTheDocument()
})

it('keeps missing evidence distinct from zero and escapes spreadsheet formulas', async () => {
  api.get.mockImplementation((path) =>
    Promise.resolve({
      data: path.endsWith('/ranking')
        ? { rank: null, participants: 0 }
        : {
            ...stats,
            graded_sessions: 0,
            published_formal_sessions: 0,
            dimensions: { ...stats.dimensions, overall: { ...metric, competency_pct: null } },
          },
    }),
  )
  render(
    <MemoryRouter>
      <StatisticsPanel />
    </MemoryRouter>,
  )
  expect(await screen.findByText('No published formal assessment yet')).toBeInTheDocument()
  expect(screen.queryByText('0%')).not.toBeInTheDocument()
  const csv = statisticsCsv(stats, { 77: '=SUM(1,1)' })
  expect(csv).toContain('"\'=SUM(1,1)"')
  expect(csv).toContain('"60–80%","2"')
})

it('shows one action and no invented statistics before the first published attempt', async () => {
  api.get.mockImplementation((path) =>
    Promise.resolve({
      data: path.endsWith('/ranking')
        ? { rank: null, participants: 0 }
        : {
            ...stats,
            graded_sessions: 0,
            published_formal_sessions: 0,
            progress: [],
          },
    }),
  )
  render(
    <MemoryRouter>
      <StatisticsPanel />
    </MemoryRouter>,
  )
  expect(await screen.findByText('No published formal assessment yet')).toBeVisible()
  expect(screen.getByRole('link', { name: 'Start assessment' })).toHaveAttribute(
    'href',
    '/assessments',
  )
  expect(screen.queryByText('Cumulative score')).not.toBeInTheDocument()
  expect(screen.queryByText('Your rank')).not.toBeInTheDocument()
  expect(screen.queryByText('Progress across assessments')).not.toBeInTheDocument()
})

it('uses only single-assessment dimensions and advice with exactly one graded attempt', async () => {
  api.get.mockImplementation((path) =>
    Promise.resolve({
      data: path.endsWith('/ranking')
        ? { rank: 1, participants: 1 }
        : {
            ...stats,
            graded_sessions: 1,
            published_formal_sessions: 1,
          },
    }),
  )
  render(
    <MemoryRouter>
      <StatisticsPanel />
    </MemoryRouter>,
  )
  expect(await screen.findByText("This assessment's score")).toBeVisible()
  expect(screen.getByText('CLO1 · Querying')).toBeVisible()
  expect(screen.getByText(/Complete another assessment to see trends/)).toBeVisible()
  for (const label of [
    'Cumulative score',
    'Your rank',
    'Progress across assessments',
    'Assessment score distribution',
  ]) {
    expect(screen.queryByText(label)).not.toBeInTheDocument()
  }
})

it('keeps pending attempts separate and reloads after a coordinated refresh', async () => {
  api.get.mockImplementation((path) =>
    Promise.resolve({
      data: path.endsWith('/ranking')
        ? { rank: 1, participants: 1 }
        : {
            ...stats,
            pending_formal_sessions: 1,
          },
    }),
  )
  const view = render(
    <MemoryRouter>
      <StatisticsPanel refreshKey={0} />
    </MemoryRouter>,
  )
  expect(
    await screen.findByText(/1 assessments awaiting grading or publication are excluded/),
  ).toHaveAttribute('role', 'status')
  const calls = api.get.mock.calls.length
  view.rerender(
    <MemoryRouter>
      <StatisticsPanel refreshKey={1} />
    </MemoryRouter>,
  )
  await act(async () => {})
  expect(api.get.mock.calls.length).toBe(calls + 2)
})
