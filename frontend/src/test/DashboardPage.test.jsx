import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'
import DashboardPage from '../pages/DashboardPage'
import api from '../api'

vi.mock('../api', () => ({
  default: { get: vi.fn() },
  apiMessage: (e, fb) => e?.response?.data?.error?.message || e?.message || fb,
}))

// jsdom has no canvas — stub the chart components and capture the `data`
// prop so tests can assert the backend values reach the chart unchanged.
vi.mock('react-chartjs-2', async () => {
  const React = await import('react')
  const mk = (name) => (props) =>
    React.createElement('div', {
      'data-testid': name,
      'data-payload': JSON.stringify(props.data),
    })
  return { Radar: mk('radar'), Bar: mk('bar'), Line: mk('line') }
})

const SESSIONS = [
  {
    session_id: 2,
    assessment_id: 1,
    assessment_title: 'Midterm Check',
    status: 'completed',
    started_at: '2026-11-20T10:00:00Z',
    expires_at: '2026-11-20T11:00:00Z',
    submitted_at: '2026-11-20T10:30:00Z',
    served_count: 3,
    answered_count: 3,
  },
  {
    session_id: 1,
    assessment_id: 1,
    assessment_title: 'Midterm Check',
    status: 'completed',
    started_at: '2026-11-10T10:00:00Z',
    expires_at: '2026-11-10T11:00:00Z',
    submitted_at: '2026-11-10T10:40:00Z',
    served_count: 2,
    answered_count: 2,
  },
  {
    session_id: 3,
    assessment_id: 1,
    assessment_title: 'Live Session',
    status: 'in_progress',
    started_at: '2026-11-21T10:00:00Z',
    expires_at: '2026-11-21T11:00:00Z',
    submitted_at: null,
    served_count: 1,
    answered_count: 0,
  },
]

const PROFILE_2 = {
  session_id: 2,
  assessment_id: 1,
  status: 'completed',
  categories: [
    { subject_area: 'SQL Querying', mean_competency_pct: '0.00', mean_target_pct: '60.00' },
    { subject_area: 'Design Fundamentals', mean_competency_pct: '100.00', mean_target_pct: '60.00' },
  ],
  summary: { meeting_target: 1, benchmarked_concepts: 2, unbenchmarked_concepts: 0, finalized_assessments: 2 },
  concepts: [
    {
      concept_id: 10,
      concept_code: 'SQL-SELECT',
      concept_name: 'SELECT',
      subject_area: 'SQL Querying',
      points_earned: '0.00',
      points_possible: '4.00',
      competency_pct: '0.00',
      target_pct: '60.00',
      below_target: true,
      contributing_attempts: [1],
    },
    {
      concept_id: 11,
      concept_code: 'DB-NORM',
      concept_name: 'Normalization',
      subject_area: 'Design Fundamentals',
      points_earned: '4.00',
      points_possible: '4.00',
      competency_pct: '100.00',
      target_pct: '60.00',
      below_target: false,
      contributing_attempts: [2],
    },
  ],
}

const PROFILE_1 = { ...PROFILE_2, session_id: 1, concepts: [PROFILE_2.concepts[1]] }

const GUIDANCE_2 = {
  session_id: 2,
  assessment_id: 1,
  status: 'completed',
  guidance: [
    {
      concept_id: 10,
      concept_code: 'SQL-SELECT',
      concept_name: 'SELECT',
      subject_area: 'SQL Querying',
      description: 'Basic retrieval queries',
      competency_pct: '0.00',
      target_pct: '60.00',
      shortfall: '60.00',
      priority: 1,
      ready: true,
      prerequisites: [],
      reason: '60.00 pts below the 60.00% benchmark',
      contributing_attempts: [1],
      llm_explanation: 'Review SELECT filtering.',
    },
  ],
}

function mockApi({ sessions = SESSIONS, profiles = {}, guidances = {} } = {}) {
  api.get.mockImplementation((url) => {
    if (url === '/sessions') return Promise.resolve({ data: sessions })
    const comp = url.match(/^\/sessions\/(\d+)\/competency$/)
    if (comp) return Promise.resolve({ data: profiles[comp[1]] || { concepts: [] } })
    const guide = url.match(/^\/sessions\/(\d+)\/guidance$/)
    if (guide) return Promise.resolve({ data: guidances[guide[1]] || { guidance: [] } })
    return Promise.reject(new Error(`unexpected ${url}`))
  })
}

function conceptChartData() {
  return JSON.parse(screen.getAllByTestId('bar')[0].dataset.payload)
}

beforeEach(() => vi.clearAllMocks())

const renderDashboard = () => render(<MemoryRouter><DashboardPage /></MemoryRouter>)

describe('DashboardPage', () => {
  it('shows a loading state while sessions are fetched', () => {
    api.get.mockReturnValue(new Promise(() => {}))
    renderDashboard()
    expect(screen.getByRole('status')).toHaveTextContent('Loading')
    expect(screen.getByRole('heading', { level: 1, name: 'My competency' })).toBeVisible()
  })

  it('renders readable concept and subject charts fed unchanged by backend values', async () => {
    mockApi({ profiles: { 2: PROFILE_2 }, guidances: { 2: GUIDANCE_2 } })
    renderDashboard()

    const chart = await waitFor(conceptChartData)
    expect(chart.labels).toEqual(['SELECT', 'Normalization'])
    // 0% and 100% extremes survive to the chart as numbers, with the
    // target benchmark shown as the second dataset.
    expect(chart.datasets[0].data).toEqual([0, 100])
    expect(chart.datasets[1].data).toEqual([60, 60])
    expect(screen.getAllByTestId('bar')).toHaveLength(2)
    expect(screen.getByText('0.00%')).toBeInTheDocument()
    expect(screen.getByText('100.00%')).toBeInTheDocument()
    expect(screen.getByText('Below target')).toBeInTheDocument()
    expect(screen.getByText('On target')).toBeInTheDocument()
  })

  it('uses the radar comparison once three concepts can form an area', async () => {
    const third = { ...PROFILE_2.concepts[0], concept_id: 12, concept_name: 'Joins', competency_pct: '50.00' }
    mockApi({ profiles: { 2: { ...PROFILE_2, concepts: [...PROFILE_2.concepts, third] } } })
    renderDashboard()
    const radar = JSON.parse((await screen.findByTestId('radar')).dataset.payload)
    expect(radar.labels).toEqual(['SELECT', 'Normalization', 'Joins'])
  })

  it('renders the what-to-study-next list after the charts', async () => {
    mockApi({ profiles: { 2: PROFILE_2 }, guidances: { 2: GUIDANCE_2 } })
    renderDashboard()

    await screen.findByText('What to study next')
    expect(screen.getByText(/1\. SELECT/)).toBeInTheDocument()
    expect(
      screen.getByText('60.00 pts below the 60.00% benchmark')
    ).toBeInTheDocument()
    expect(screen.getByText('Review SELECT filtering.')).toBeInTheDocument()
  })

  it('shows an empty state when there are no completed sessions', async () => {
    mockApi({ sessions: [] })
    renderDashboard()
    expect(await screen.findByText(/No completed assessments yet/)).toBeInTheDocument()
    expect(screen.getByRole('heading', { level: 1, name: 'My competency' })).toBeVisible()
    expect(screen.getByRole('link', { name: 'Browse assessments' })).toHaveAttribute('href', '/assessments')
  })

  it('treats in-progress sessions as not yet reportable', async () => {
    mockApi({ sessions: [SESSIONS[2]] })
    renderDashboard()
    expect(await screen.findByText(/No completed assessments yet/)).toBeInTheDocument()
  })

  it('shows the API error and offers a retry', async () => {
    api.get.mockRejectedValue({ response: { data: { error: { message: 'boom' } } } })
    renderDashboard()
    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('boom')
  })

  it('retains page orientation and recovers a temporary session-list error', async () => {
    api.get.mockRejectedValueOnce(new Error('Session list unavailable')).mockResolvedValue({ data: [] })
    renderDashboard()
    expect(await screen.findByRole('alert')).toHaveTextContent('Session list unavailable')
    expect(screen.getByRole('heading', { level: 1, name: 'My competency' })).toBeVisible()
    await userEvent.click(screen.getByRole('button', { name: 'Retry' }))
    await screen.findByText('No completed assessments yet')
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1)
  })

  it('fetches another session when the learner switches sessions', async () => {
    mockApi({
      profiles: { 2: PROFILE_2, 1: PROFILE_1 },
      guidances: { 2: GUIDANCE_2 },
    })
    renderDashboard()
    await waitFor(conceptChartData)

    await userEvent.selectOptions(
      screen.getByLabelText(/Select assessment session/),
      '1'
    )
    await waitFor(() =>
      expect(api.get).toHaveBeenCalledWith('/sessions/1/competency')
    )
    const chart = await waitFor(() => {
      const data = conceptChartData()
      if (data.labels[0] !== 'Normalization') throw new Error('Waiting for selected session')
      return data
    })
    expect(chart.labels).toEqual(['Normalization'])
  })

  it('shows an empty-competency state for a session without evidence', async () => {
    mockApi({ profiles: { 2: { ...PROFILE_2, concepts: [] } } })
    renderDashboard()
    expect(
      await screen.findByText(/No competency data for this session/)
    ).toBeInTheDocument()
  })

  it('surfaces a profile API error distinctly', async () => {
    api.get.mockImplementation((url) => {
      if (url === '/sessions') return Promise.resolve({ data: SESSIONS })
      if (url.includes('/competency'))
        return Promise.reject({
          response: { data: { error: { message: 'profile broke' } } },
        })
      if (url.includes('/guidance')) return Promise.resolve({ data: { guidance: [] } })
      return Promise.reject(new Error(url))
    })
    renderDashboard()
    expect((await screen.findAllByRole('alert')).length).toBeGreaterThan(0)
    expect(screen.getByText('profile broke')).toBeInTheDocument()
  })

  it('uses server category values and distinguishes unbenchmarked concepts', async () => {
    const profile = { ...PROFILE_2, summary: { meeting_target: 1, benchmarked_concepts: 1, unbenchmarked_concepts: 1, finalized_assessments: 2 },
      categories: [{ subject_area: 'API category', mean_competency_pct: '37.25', mean_target_pct: null }],
      concepts: [PROFILE_2.concepts[1], { ...PROFILE_2.concepts[0], target_pct: null, below_target: false }] }
    mockApi({ profiles: { 2: profile } })
    renderDashboard()
    expect(await screen.findByText('No benchmark')).toBeInTheDocument()
    expect(screen.getByText('1 / 1')).toBeInTheDocument()
    const data = JSON.parse(screen.getAllByTestId('bar')[1].dataset.payload)
    expect(data.labels).toEqual(['API category'])
    expect(data.datasets[0].data).toEqual([37.25])
    expect(data.datasets[1].data).toEqual([null])
  })

  it('keeps the highest shortfall priority even when prerequisite preparation is needed', async () => {
    const first = { ...GUIDANCE_2.guidance[0], ready: false, concept_name: 'Highest priority' }
    const second = { ...first, concept_id: 11, concept_name: 'Lower priority', ready: true, priority: 2, shortfall: '10.00' }
    mockApi({ profiles: { 2: PROFILE_2 }, guidances: { 2: { guidance: [first, second] } } })
    renderDashboard()
    await screen.findByText('Next to study')
    expect(screen.getByText('Next to study').parentElement).toHaveTextContent('Highest priority')
    expect(screen.getByText('Prerequisite preparation needed')).toBeInTheDocument()
  })
})
