import { act, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'
import Dashboard_Admin from '../pages/admin/Dashboard_Admin'
import api from '../api'
import { setLocale } from '../i18n'

// AdminNav uses NavLink → needs a router context.
function renderPage() {
  return render(
    <MemoryRouter>
      <Dashboard_Admin />
    </MemoryRouter>
  )
}

vi.mock('../api', () => ({
  default: { get: vi.fn() },
  apiMessage: (e, fb) => e?.response?.data?.error?.message || e?.message || fb,
}))

vi.mock('react-chartjs-2', async () => {
  const React = await import('react')
  const mk = (name) => (props) =>
    React.createElement('div', {
      'data-testid': name,
      'data-payload': JSON.stringify(props.data),
    })
  return { Radar: mk('radar'), Bar: mk('bar'), Line: mk('line') }
})

const COHORT = {
  learner_count: 2,
  finalized_sessions: 3,
  concepts: [
    {
      concept_id: 10,
      concept_code: 'SQL-SELECT',
      concept_name: 'SELECT',
      subject_area: 'SQL Querying',
      learners_assessed: 2,
      avg_competency_pct: '62.50',
      below_target_count: 1,
      gap_rate_pct: '50.00',
    },
    {
      concept_id: 11,
      concept_code: 'SQL-JOIN',
      concept_name: 'JOIN',
      subject_area: 'SQL Querying',
      learners_assessed: 2,
      avg_competency_pct: '100.00',
      below_target_count: 0,
      gap_rate_pct: '0.00',
    },
  ],
  weakest_concepts: [
    {
      concept_id: 10,
      concept_code: 'SQL-SELECT',
      concept_name: 'SELECT',
      subject_area: 'SQL Querying',
      learners_assessed: 2,
      avg_competency_pct: '62.50',
      below_target_count: 1,
      gap_rate_pct: '50.00',
    },
  ],
}

const LEARNERS = [
  {
    account_id: 7,
    email: 'one@test.dev',
    full_name: 'Learner One',
    sessions_total: 1,
    sessions_completed: 1,
    last_activity: '2026-11-20T10:30:00Z',
  },
  {
    account_id: 8,
    email: 'two@test.dev',
    full_name: 'Learner Two',
    sessions_total: 2,
    sessions_completed: 2,
    last_activity: '2026-11-21T10:30:00Z',
  },
]

const LEARNER_7_SESSIONS = {
  account_id: 7,
  email: 'one@test.dev',
  full_name: 'Learner One',
  sessions: [
    {
      session_id: 42,
      assessment_id: 1,
      assessment_title: 'Midterm',
      status: 'completed',
      started_at: '2026-11-20T10:00:00Z',
      expires_at: '2026-11-20T11:00:00Z',
      submitted_at: '2026-11-20T10:30:00Z',
      served_count: 3,
      answered_count: 3,
    },
  ],
}

const PROFILE_42 = {
  session_id: 42,
  assessment_id: 1,
  status: 'completed',
  concepts: [
    {
      concept_id: 10,
      concept_code: 'SQL-SELECT',
      concept_name: 'SELECT',
      subject_area: 'SQL Querying',
      competency_pct: '25.00',
      target_pct: '60.00',
      below_target: true,
    },
  ],
}

function mockApi() {
  api.get.mockImplementation((url) => {
    if (url === '/admin/analytics/cohort') return Promise.resolve({ data: COHORT })
    if (url === '/admin/learners') return Promise.resolve({ data: LEARNERS })
    if (url === '/admin/assessments') return Promise.resolve({ data: [{ assessment_id: 1, title: 'Midterm' }] })
    if (url === '/admin/learners/7/sessions')
      return Promise.resolve({ data: LEARNER_7_SESSIONS })
    if (url === '/admin/sessions/42/competency')
      return Promise.resolve({ data: PROFILE_42 })
    return Promise.reject(new Error(`unexpected ${url}`))
  })
}

beforeEach(() => vi.clearAllMocks())

describe('Dashboard_Admin', () => {
  it('shows a loading state while cohort data is fetched', () => {
    api.get.mockReturnValue(new Promise(() => {}))
    renderPage()
    expect(screen.getByRole('status')).toHaveTextContent('Loading')
  })

  it('renders cohort summary and gap analytics sorted worst-first', async () => {
    mockApi()
    renderPage()

    expect(await screen.findByText('Cohort Overview')).toBeInTheDocument()
    expect(screen.getByText('Learners assessed')).toBeInTheDocument()
    // SELECT row shows the below-benchmark prevalence from the API unchanged
    expect(screen.getByText('SELECT')).toBeInTheDocument()
    expect(screen.getByText('62.50%')).toBeInTheDocument()
    expect(screen.getByText('50.00%')).toBeInTheDocument()
    const rows = screen.getAllByRole('row')
    expect(rows[1]).toHaveTextContent('SELECT')
    expect(rows[2]).toHaveTextContent('JOIN')
  })

  it('drills into a learner and shows a readable single-concept profile', async () => {
    mockApi()
    renderPage()
    await screen.findByText('Learner One')

    await userEvent.click(screen.getByText('Learner One'))
    await waitFor(() =>
      expect(api.get).toHaveBeenCalledWith('/admin/learners/7/sessions')
    )
    await waitFor(() =>
      expect(api.get).toHaveBeenCalledWith('/admin/sessions/42/competency')
    )

    const chart = JSON.parse(
      (await screen.findByTestId('bar')).dataset.payload
    )
    expect(chart.labels).toEqual(['SELECT'])
    expect(chart.datasets[0].data).toEqual([25])
    expect(chart.datasets[1].data).toEqual([60])
  })

  it('formats both cohort table counts by locale without refetching or changing data', async () => {
    mockApi()
    const original = api.get.getMockImplementation()
    const concept = { ...COHORT.concepts[0], learners_assessed: 12345, below_target_count: 6789 }
    api.get.mockImplementation((url, config) => url === '/admin/analytics/cohort'
      ? Promise.resolve({ data: { ...COHORT, concepts: [concept] } }) : original(url, config))
    renderPage()
    const row = (await screen.findByText('SELECT')).closest('tr')
    expect(within(row).getByRole('cell', { name: '12,345', exact: true })).toBeInTheDocument()
    expect(within(row).getByRole('cell', { name: '6,789', exact: true })).toBeInTheDocument()
    const calls = api.get.mock.calls.length
    try {
      await act(() => setLocale('vi'))
      expect(within(row).getByRole('cell', { name: '12.345', exact: true })).toBeInTheDocument()
      expect(within(row).getByRole('cell', { name: '6.789', exact: true })).toBeInTheDocument()
      expect(api.get).toHaveBeenCalledTimes(calls)
      expect(concept.learners_assessed).toBe(12345)
      expect(concept.below_target_count).toBe(6789)
    } finally {
      await act(() => setLocale('en'))
      localStorage.removeItem('dbcas_locale')
    }
  })

  it('prompts to select a learner before any drill-down', async () => {
    mockApi()
    renderPage()
    expect(
      await screen.findByText(/Select a learner to view their competency profile/)
    ).toBeInTheDocument()
  })

  it('shows an error state when the cohort request fails', async () => {
    api.get.mockRejectedValue({
      response: { data: { error: { message: 'forbidden' } } },
    })
    renderPage()
    expect(await screen.findByRole('alert')).toHaveTextContent('forbidden')
  })

  it('shows empty states when the cohort has no data', async () => {
    api.get.mockImplementation((url) => {
      if (url === '/admin/analytics/cohort')
        return Promise.resolve({
          data: {
            learner_count: 0,
            finalized_sessions: 0,
            concepts: [],
            weakest_concepts: [],
          },
        })
      if (url === '/admin/learners') return Promise.resolve({ data: [] })
      if (url === '/admin/assessments') return Promise.resolve({ data: [] })
      return Promise.reject(new Error(url))
    })
    renderPage()
    expect(await screen.findByText(/No assessed concepts yet/)).toBeInTheDocument()
    expect(screen.getByText(/No learners registered yet/)).toBeInTheDocument()
  })

  it('scopes cohort analytics to the selected assessment', async () => {
    mockApi()
    renderPage()
    await screen.findByLabelText('Analytics assessment')
    await userEvent.selectOptions(screen.getByLabelText('Analytics assessment'), '1')
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/admin/analytics/cohort', { params: { assessment_id: 1 } }))
    await screen.findByText('Cohort Overview')
  })

  it('renders a valid empty competency result without a perpetual loading state', async () => {
    mockApi()
    const original = api.get.getMockImplementation()
    api.get.mockImplementation((url, config) => url === '/admin/sessions/42/competency'
      ? Promise.resolve({ data: { concepts: [], categories: [] } }) : original(url, config))
    renderPage()
    await userEvent.click(await screen.findByText('Learner One'))
    expect(await screen.findByText('No graded concept evidence for this session')).toBeInTheDocument()
    expect(screen.queryByText('Loading competency…')).not.toBeInTheDocument()
  })

  it('plots API trend values without deriving scores in the browser', async () => {
    mockApi()
    const original = api.get.getMockImplementation()
    api.get.mockImplementation((url, config) => url === '/admin/analytics/cohort'
      ? Promise.resolve({ data: { ...COHORT, trend: [{ date: '2026-10-11', mean_result_pct: '72.35' }] } }) : original(url, config))
    renderPage()
    const data = JSON.parse((await screen.findByTestId('line')).dataset.payload)
    expect(data.labels).toEqual(['Oct 11, 2026'])
    expect(data.datasets[0].data).toEqual([72.35])
  })
})
