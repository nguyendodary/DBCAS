import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, expect, it, vi } from 'vitest'
import api from '../api'
import { setLocale } from '../i18n'
import EvaluationPage from '../pages/EvaluationPage'
import AssessmentsPage from '../pages/AssessmentsPage'

vi.mock('../api', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn() },
  apiMessage: () => 'Request failed',
}))
vi.mock('../components/EvaluationCharts', () => ({
  EvaluationCharts: () => <div data-testid="charts" />,
}))

const concept = (id, name, pct, belowTarget = true) => ({
  concept_id: id,
  concept_name: name,
  competency_pct: pct,
  target_pct: 70,
  below_target: belowTarget,
  covered: true,
})
const concepts = [
  concept(1, 'SELECT basics', 90, false),
  concept(2, 'WHERE filters', 60),
  concept(3, 'GROUP BY', 40),
]
const result = {
  status: 'provisional',
  provisional: true,
  final: false,
  attempt_count: 1,
  pending_count: 0,
  dimensions: {},
  history: [],
  approved: false,
  concept_results: concepts,
  result: {
    evaluation: {
      summary: 'Evidence-based feedback.',
      strengths: [],
      weaknesses: [],
      suggestions: [],
      learning_path: [],
      trend: null,
      question_comments: [],
    },
    evaluator_fallback: false,
  },
}
const clo = (id, code, title) => ({ clo_id: id, clo_code: code, title })
const option = (id, name, area, clos) => ({
  concept_id: id,
  concept_name: name,
  subject_area: area,
  clos,
})
const options = {
  question_count: { min: 1, default: 5, max: 13, presets: [5, 10, 13] },
  concepts: [
    option(1, 'SELECT basics', 'Querying', [clo(11, 'CLO-01', 'Write basic SELECT queries')]),
    option(2, 'WHERE filters', 'Querying', [clo(11, 'CLO-01', 'Write basic SELECT queries')]),
    option(3, 'GROUP BY', 'Aggregation', [clo(12, 'CLO-02', 'Summarize grouped data')]),
  ],
}

function renderEvaluation(data) {
  api.get.mockResolvedValue({ data })
  return render(
    <MemoryRouter initialEntries={['/evaluations/7']}>
      <Routes>
        <Route path="/evaluations/:sessionId" element={<EvaluationPage />} />
      </Routes>
    </MemoryRouter>,
  )
}
function renderBuilder() {
  api.get.mockImplementation((url) =>
    Promise.resolve({ data: url === '/practice/options' ? options : [] }),
  )
  return render(
    <MemoryRouter initialEntries={['/assessments?concepts=1,2']}>
      <Routes>
        <Route path="/assessments" element={<AssessmentsPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

beforeEach(() => vi.clearAllMocks())

it('offers ranked weak-skill practice, links the builder and dismisses cleanly', async () => {
  renderEvaluation(result)
  expect(await screen.findByRole('heading', { name: 'Practice your weak skills?' })).toBeVisible()
  expect(screen.getByRole('link', { name: 'Practice weak skills' })).toHaveAttribute(
    'href',
    '/assessments?concepts=3,2',
  )
  const prompt = screen.getByRole('region', { name: 'Practice your weak skills?' })
  expect(within(prompt).getByText('GROUP BY')).toBeVisible()
  expect(within(prompt).getByText('WHERE filters')).toBeVisible()
  expect(within(prompt).queryByText('SELECT basics')).not.toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Not now' }))
  expect(
    screen.queryByRole('heading', { name: 'Practice your weak skills?' }),
  ).not.toBeInTheDocument()
  expect(screen.getByText('Evidence-based feedback.')).toBeVisible()
})

it('shows no recommendation when every concept meets its target', async () => {
  renderEvaluation({ ...result, concept_results: [concepts[0]] })
  await screen.findByText('Evidence-based feedback.')
  expect(
    screen.queryByRole('heading', { name: 'Practice your weak skills?' }),
  ).not.toBeInTheDocument()
})

it('does not recommend a concept without competency evidence', async () => {
  renderEvaluation({ ...result, concept_results: [{ ...concepts[1], competency_pct: null }] })
  await screen.findByText('Evidence-based feedback.')
  expect(
    screen.queryByRole('heading', { name: 'Practice your weak skills?' }),
  ).not.toBeInTheDocument()
})

it('uses the Vietnamese translation for the recommendation', async () => {
  await setLocale('vi')
  renderEvaluation(result)
  expect(await screen.findByRole('heading', { name: 'Luyện tập điểm yếu?' })).toBeVisible()
  expect(screen.getByRole('link', { name: 'Luyện tập điểm yếu' })).toBeVisible()
})

it('uses the Vietnamese labels in the practice builder', async () => {
  await setLocale('vi')
  renderBuilder()
  expect(
    await screen.findByRole('heading', { name: 'Khái niệm đã chọn và chuẩn đầu ra' }),
  ).toBeVisible()
  expect(screen.getByText(/Các khái niệm từ kết quả gần nhất đã được chọn sẵn/)).toBeVisible()
})

it('preselects requested concepts, shows their CLOs and allows manual changes', async () => {
  renderBuilder()
  const select = await screen.findByRole('button', { name: 'SELECT basics' })
  const where = screen.getByRole('button', { name: 'WHERE filters' })
  const group = screen.getByRole('button', { name: 'GROUP BY' })
  expect(select).toHaveAttribute('aria-pressed', 'true')
  expect(where).toHaveAttribute('aria-pressed', 'true')
  expect(group).toHaveAttribute('aria-pressed', 'false')
  expect(
    screen.getByRole('heading', { name: 'Selected concepts and learning outcomes' }),
  ).toBeVisible()
  expect(screen.getAllByText(/CLO-01/)).toHaveLength(2)
  expect(screen.queryByText(/CLO-02/)).not.toBeInTheDocument()
  expect(api.post).not.toHaveBeenCalled()

  await userEvent.click(select)
  await userEvent.click(group)
  expect(select).toHaveAttribute('aria-pressed', 'false')
  expect(group).toHaveAttribute('aria-pressed', 'true')
  expect(screen.getAllByText(/CLO-01/)).toHaveLength(1)
  expect(screen.getByText(/CLO-02/)).toBeVisible()
  expect(api.post).not.toHaveBeenCalled()
})
