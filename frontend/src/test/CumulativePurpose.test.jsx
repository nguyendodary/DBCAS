import { act, render, screen, within } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, expect, it, vi } from 'vitest'
import api from '../api'
import CumulativePage from '../pages/CumulativePage'
import { setLocale } from '../i18n'

vi.mock('../api', () => ({ default: { get: vi.fn() }, apiMessage: (e) => e.message }))
vi.mock('../components/CompetencyCharts', () => ({ CompetencyConceptBars: () => null }))

const concept = {
  concept_id: 1,
  concept_code: 'JOIN',
  concept_name: 'Joins',
  subject_area: 'SQL',
  competency_pct: '50.00',
  target_pct: '60.00',
  below_target: true,
  points_earned: '1.00',
  points_possible: '2.00',
  contributing_sessions: [1],
  contributing_attempts: [1],
  below_target_assessments: 1,
  meeting_target_assessments: 0,
}

const cumulative = {
  learner_id: 1,
  concepts: [concept],
  gaps: [concept],
  categories: [],
  summary: {
    assessed_concepts: 1,
    benchmarked_concepts: 1,
    meeting_target: 0,
    unbenchmarked_concepts: 0,
    finalized_assessments: 1,
  },
  adaptive_estimates: [
    {
      session_id: 2,
      assessment_title: 'Adaptive practice',
      started_at: '2026-10-10T10:00:00Z',
      submitted_at: '2026-10-10T11:00:00Z',
      band: 'MEDIUM',
      ability_index: 3.25,
      confidence: 'medium',
      evidence_count: 4,
    },
  ],
}

beforeEach(async () => {
  vi.resetAllMocks()
  await act(() => setLocale('en'))
  api.get.mockImplementation((path) => {
    if (path === '/admin/analytics/statistics')
      return Promise.resolve({
        data: {
          dimensions: { overall: { competency_pct: null }, clos: [], topics: [], difficulties: [] },
          published_formal_sessions: 0,
          graded_sessions: 0,
          progress: [],
          progress_total: 0,
          score_distribution: [],
          ranking: [],
        },
      })
    if (/^\/admin\/learners\/\d+\/competency\/cumulative$/.test(path))
      return Promise.resolve({ data: cumulative })
    throw new Error(`Unexpected request: ${path}`)
  })
})

it('keeps adaptive ability estimates separate from the official percentage table', async () => {
  render(
    <MemoryRouter initialEntries={['/admin/learners/1/competency']}>
      <Routes>
        <Route path="/admin/learners/:learnerId/competency" element={<CumulativePage />} />
      </Routes>
    </MemoryRouter>,
  )
  const heading = await screen.findByRole('heading', { name: 'Adaptive ability estimates' })
  const card = heading.closest('.surface-card')
  expect(within(card).getByText('Adaptive practice')).toBeInTheDocument()
  expect(within(card).getByText('3.25/5')).toBeInTheDocument()
  expect(within(card).getAllByText('Medium')).toHaveLength(2)
  expect(within(card).getByText('4')).toBeInTheDocument()
  expect(
    within(card).getByText(/These results are separate from the official percentage above/),
  ).toBeInTheDocument()
})

it('does not render the adaptive table when no published estimate exists', async () => {
  api.get.mockImplementation((path) => {
    if (path === '/admin/analytics/statistics')
      return Promise.resolve({
        data: {
          dimensions: { overall: { competency_pct: null }, clos: [], topics: [], difficulties: [] },
          published_formal_sessions: 0,
          graded_sessions: 0,
          progress: [],
          progress_total: 0,
          score_distribution: [],
          ranking: [],
        },
      })
    if (/^\/admin\/learners\/\d+\/competency\/cumulative$/.test(path))
      return Promise.resolve({ data: { ...cumulative, adaptive_estimates: [] } })
    throw new Error(`Unexpected request: ${path}`)
  })
  render(
    <MemoryRouter initialEntries={['/admin/learners/1/competency']}>
      <Routes>
        <Route path="/admin/learners/:learnerId/competency" element={<CumulativePage />} />
      </Routes>
    </MemoryRouter>,
  )
  expect(await screen.findByText('1 published assessment')).toBeInTheDocument()
  expect(
    screen.queryByRole('heading', { name: 'Adaptive ability estimates' }),
  ).not.toBeInTheDocument()
})
