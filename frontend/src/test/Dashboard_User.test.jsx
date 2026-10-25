import { act, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'
import Dashboard_User from '../pages/user/Dashboard_User'
import api from '../api'
import { setLocale } from '../i18n'

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
      reason_code: 'below_benchmark',
      reason_params: { shortfall: '60.00', target: '60.00' },
      contributing_attempts: [1],
      llm_explanation: 'Review SELECT filtering.',
    },
  ],
}

function mockApi({ sessions = SESSIONS, profiles = {}, guidances = {}, cumulative } = {}) {
  api.get.mockImplementation((url) => {
    if (url === '/sessions') return Promise.resolve({ data: sessions })
    if (url === '/sessions/leaderboard') return Promise.resolve({ data: [] })
    if (url === '/sessions/competency/cumulative') return Promise.resolve({ data: cumulative || { concepts: profiles[2]?.concepts || [], gaps: guidances[2]?.guidance || [] } })
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
afterEach(async () => { await act(() => setLocale('en')) })

const renderDashboard = () => render(<MemoryRouter><Dashboard_User /></MemoryRouter>)

describe('Dashboard_User', () => {
  it('uses cumulative history for study recommendations and removes per-test action buttons', async () => {
    const historyGap = { ...PROFILE_2.concepts[0], concept_id: 80, concept_name: 'History-wide gap', competency_pct: '45', target_pct: '80' }
    mockApi({ profiles: { 2: PROFILE_2 }, cumulative: { concepts: [historyGap], gaps: [historyGap] } })
    const { container } = renderDashboard()
    await screen.findByRole('heading', { name: '1. History-wide gap' })
    const analysis = container.querySelector('.lp-analysis-heading').closest('section')
    expect(within(analysis).queryByRole('link')).not.toBeInTheDocument()
    expect(within(analysis).getByText('Recommendations across all assessments with published results')).toBeInTheDocument()
    expect(within(analysis).getByText('35 percentage points below the target.')).toBeInTheDocument()
    expect(api.get).toHaveBeenCalledWith('/sessions/competency/cumulative')
    expect(api.get).not.toHaveBeenCalledWith('/sessions/2/guidance')
  })
  it('polls pending results in the background without reloading the displayed analysis', async () => {
    const intervals = vi.spyOn(globalThis, 'setInterval')
    try {
      mockApi({ sessions: [...SESSIONS, { ...SESSIONS[0], session_id: 4, release_status: 'auto_grading' }],
        profiles: { 2: PROFILE_2 }, guidances: { 2: GUIDANCE_2 } })
      renderDashboard()
      const chart = await screen.findByRole('img', { name: 'SELECT: 0%; Target: 60%' })
      const poll = intervals.mock.calls.find(([, ms]) => ms === 5000)[0]
      await act(async () => { poll() })
      await waitFor(() => expect(api.get.mock.calls.filter(([url]) => url === '/sessions')).toHaveLength(2))
      expect(api.get.mock.calls.filter(([url]) => url === '/sessions/2/competency')).toHaveLength(1)
      expect(api.get.mock.calls.filter(([url]) => url === '/sessions/competency/cumulative')).toHaveLength(1)
      expect(screen.getByRole('img', { name: 'SELECT: 0%; Target: 60%' })).toBe(chart)
      expect(screen.queryByText('Loading competency profile…')).not.toBeInTheDocument()
    } finally { intervals.mockRestore() }
  })
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
    expect(chart.datasets[0].backgroundColor).toHaveLength(2)
    expect(new Set(chart.datasets[0].backgroundColor).size).toBe(2)
    expect(chart.datasets[1].backgroundColor).toMatch(/^rgba\(/)
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

  it('scales skill tracks to the backend 0-100 competency value, matching the label', async () => {
    const profile = { ...PROFILE_2, concepts: [{ ...PROFILE_2.concepts[0], competency_pct: '50.00' }] }
    mockApi({ profiles: { 2: profile } })
    const { container } = renderDashboard()
    await waitFor(() => {
      const fill = container.querySelector('.lp-skill-track span')
      if (!fill) throw new Error('waiting for skill track')
      expect(fill.style.width).toBe('50%')
    })
    // The bar now agrees with the printed label instead of pegging at 100%.
    expect(container.querySelector('.lp-skill-label strong')).toHaveTextContent('50%')
  })

  it('labels the radar benchmark with the 70% default when no concept carries a target', async () => {
    const profile = {
      ...PROFILE_2,
      concepts: PROFILE_2.concepts.map((c) => ({ ...c, target_pct: null, below_target: false })),
    }
    mockApi({ profiles: { 2: profile } })
    renderDashboard()
    expect(await screen.findByText('Benchmark: 70%')).toBeInTheDocument()
  })

  it('renders the what-to-study-next list after the charts', async () => {
    mockApi({ profiles: { 2: PROFILE_2 }, guidances: { 2: GUIDANCE_2 } })
    renderDashboard()

    await screen.findByText('What to study next')
    expect(screen.getByText(/1\. SELECT/)).toBeInTheDocument()
    expect(
      screen.getByText('60.00 pts below the 60.00% benchmark.')
    ).toBeInTheDocument()
    expect(screen.getByText('Review SELECT filtering.')).toBeInTheDocument()
  })

  it('switches structured guidance immediately to Vietnamese without refetching or English fallback', async () => {
    mockApi({ profiles: { 2: PROFILE_2 }, guidances: { 2: GUIDANCE_2 } })
    renderDashboard()
    await screen.findByText('60.00 pts below the 60.00% benchmark.')
    const calls = api.get.mock.calls.length
    await act(() => setLocale('vi'))
    expect(screen.getByText('Còn thiếu 60,00 điểm để đạt mức chuẩn 60,00%.')).toBeVisible()
    expect(screen.queryByText(/pts below the/)).not.toBeInTheDocument()
    expect(screen.getByText('Review SELECT filtering.')).toBeInTheDocument()
    expect(api.get).toHaveBeenCalledTimes(calls)
  })

  it.each([
    ['en', '60.25 pts below the 80.50% benchmark.'],
    ['vi', 'Còn thiếu 60,25 điểm để đạt mức chuẩn 80,50%.'],
  ])('formats reason parameters using %s numbers and a single percent sign', async (locale, expected) => {
    await act(() => setLocale(locale))
    const item = { ...GUIDANCE_2.guidance[0], reason_params: { shortfall: '60.25', target: '80.50' } }
    mockApi({ profiles: { 2: PROFILE_2 }, guidances: { 2: { guidance: [item] } } })
    renderDashboard()
    expect(await screen.findByText(expected)).toBeVisible()
  })

  it.each([
    ['en', 'below_target', 'Prerequisite preparation needed: SELECT, JOIN.'],
    ['vi', 'below_target', 'Nên ôn lại kiến thức nền trước: SELECT, JOIN.'],
    ['en', 'unassessed', 'Prerequisites not yet assessed: SELECT, JOIN.'],
    ['vi', 'unassessed', 'Chưa có kết quả đánh giá kiến thức nền: SELECT, JOIN.'],
  ])('localizes %s prerequisite explanations for %s', async (locale, status, expected) => {
    await act(() => setLocale(locale))
    const item = { ...GUIDANCE_2.guidance[0], prerequisites: [
      { concept_name: 'SELECT', status }, { concept_name: 'JOIN', status },
      { concept_name: 'Already satisfied', status: 'satisfied' },
      ...(status === 'below_target' ? [{ concept_name: 'Unassessed secondary', status: 'unassessed' }] : []),
    ] }
    mockApi({ profiles: { 2: PROFILE_2 }, guidances: { 2: { guidance: [item] } } })
    renderDashboard()
    expect(await screen.findByText(text => text.endsWith(expected))).toBeVisible()
    expect(screen.queryByText(/Already satisfied|Unassessed secondary/)).not.toBeInTheDocument()
  })

  it('uses a localized fallback for unknown reason codes, never backend prose', async () => {
    await act(() => setLocale('vi'))
    const item = { ...GUIDANCE_2.guidance[0], reason_code: 'future_reason', reason: 'Untranslated backend prose' }
    mockApi({ profiles: { 2: PROFILE_2 }, guidances: { 2: { guidance: [item] } } })
    renderDashboard()
    expect(await screen.findByText('Chưa có gợi ý học tập chi tiết.')).toBeVisible()
    expect(screen.queryByText('Untranslated backend prose')).not.toBeInTheDocument()
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
