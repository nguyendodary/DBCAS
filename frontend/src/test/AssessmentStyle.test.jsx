import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import api from '../api'
import AssessmentsPage from '../pages/AssessmentsPage'
import AdaptiveResult from '../components/AdaptiveResult'
import AssessmentStylePicker from '../components/AssessmentStylePicker'
import { EvaluationContent } from '../pages/EvaluationPage'
import {
  ADAPTIVE,
  ADAPTIVE_MAX_QUESTIONS,
  ADAPTIVE_MIN_QUESTIONS,
  FIXED,
  buildPracticePayload,
  clampAdaptiveCount,
  isAdaptiveResult,
  isSelectionValid,
} from '../assessmentStyle'

vi.mock('../api', () => ({
  default: { get: vi.fn(), post: vi.fn() },
  apiMessage: (e, fb) => e?.response?.data?.error?.message || e?.message || fb,
}))

const OPTIONS = {
  question_count: { min: 1, default: 5, max: 13, presets: [5, 10, 13] },
  concepts: [
    { concept_id: 1, concept_name: 'SELECT' },
    { concept_id: 2, concept_name: 'JOIN' },
  ],
}

beforeEach(() => {
  vi.clearAllMocks()
  api.get.mockImplementation((url) =>
    Promise.resolve({ data: url === '/practice/options' ? OPTIONS : [] }),
  )
  api.post.mockImplementation((url) =>
    Promise.resolve({
      data:
        url === '/practice/preview'
          ? { can_start: true, uncovered_concepts: [], notice: null }
          : { session_id: 99 },
    }),
  )
})

function renderPractice() {
  return render(
    <MemoryRouter initialEntries={['/assessments']}>
      <Routes>
        <Route path="/assessments" element={<AssessmentsPage />} />
        <Route path="/exam/:id" element={<div>EXAM ROOM</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('assessment style helpers', () => {
  it('keeps the free-practice payload unchanged for FIXED', () => {
    const payload = buildPracticePayload({
      style: FIXED,
      selected: [1, 2],
      bands: ['EASY', 'HARD'],
      source: 'ai',
      count: 13,
      requestId: 'req-1',
    })
    expect(payload).toEqual({
      concept_ids: [1, 2],
      difficulties: ['EASY', 'HARD'],
      source: 'ai',
      question_count: 13,
      request_id: 'req-1',
    })
    expect(payload).not.toHaveProperty('assessment_style')
  })

  it('sends only ADAPTIVE-compatible fields and clamps the question count', () => {
    const payload = buildPracticePayload({
      style: ADAPTIVE,
      selected: [1, 2],
      bands: ['EASY', 'HARD'],
      source: 'ai',
      count: 99,
      requestId: 'req-2',
    })
    expect(payload).toEqual({
      concept_ids: [1],
      difficulties: ['EASY'],
      source: 'bank',
      question_count: ADAPTIVE_MAX_QUESTIONS,
      request_id: 'req-2',
      assessment_style: ADAPTIVE,
    })
    expect(payload).not.toHaveProperty('question_mix')
    expect(clampAdaptiveCount(1)).toBe(ADAPTIVE_MIN_QUESTIONS)
  })

  it('validates adaptive selections against the single-concept, single-band rule', () => {
    const limits = {
      min: ADAPTIVE_MIN_QUESTIONS,
      max: ADAPTIVE_MAX_QUESTIONS,
      presets: [],
    }
    expect(
      isSelectionValid({
        style: ADAPTIVE,
        selected: [1],
        bands: ['MEDIUM'],
        source: 'bank',
        count: 5,
        limits,
      }),
    ).toBe(true)
    expect(
      isSelectionValid({
        style: ADAPTIVE,
        selected: [1, 2],
        bands: ['MEDIUM'],
        source: 'bank',
        count: 5,
        limits,
      }),
    ).toBe(false)
    expect(
      isSelectionValid({
        style: ADAPTIVE,
        selected: [1],
        bands: ['MEDIUM'],
        source: 'ai',
        count: 5,
        limits,
      }),
    ).toBe(false)
  })

  it('detects an estimated-ability result from session metadata', () => {
    expect(isAdaptiveResult({ result_kind: 'estimated_ability' })).toBe(true)
    expect(isAdaptiveResult({ runner_mode: 'adaptive' })).toBe(true)
    expect(isAdaptiveResult({ result_kind: 'official_score' })).toBe(false)
    expect(isAdaptiveResult(null)).toBe(false)
  })
})

describe('AssessmentStylePicker', () => {
  it('explains both modes and lists the adaptive constraints', async () => {
    const onChange = vi.fn()
    render(<AssessmentStylePicker value={FIXED} onChange={onChange} />)
    expect(screen.getByRole('radio', { name: 'Free practice' })).toBeChecked()
    expect(screen.getByRole('radio', { name: 'Adaptive practice' })).toBeInTheDocument()
    expect(screen.queryByText('Adaptive practice constraints')).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole('radio', { name: 'Adaptive practice' }))
    expect(onChange).toHaveBeenCalledWith(ADAPTIVE)
  })
})

describe('practice start flow', () => {
  it('enforces adaptive constraints and starts an adaptive session', async () => {
    renderPractice()
    await userEvent.click(await screen.findByRole('button', { name: 'SELECT', exact: true }))
    await userEvent.click(screen.getByRole('radio', { name: 'Adaptive practice' }))

    expect(await screen.findByText('Adaptive practice constraints')).toBeInTheDocument()
    expect(screen.getByText('Exactly one concept')).toBeInTheDocument()
    expect(screen.getByText('3–50 questions')).toBeInTheDocument()
    expect(screen.queryByRole('radio', { name: 'AI tạo câu hỏi' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Chọn tất cả khái niệm' })).not.toBeInTheDocument()

    const count = screen.getByLabelText('Số câu (3–50)')
    expect(count).toHaveAttribute('min', '3')
    expect(count).toHaveAttribute('max', '50')

    await userEvent.click(screen.getByRole('button', { name: 'JOIN', exact: true }))
    expect(screen.getByRole('button', { name: 'SELECT', exact: true })).toHaveAttribute(
      'aria-pressed',
      'false',
    )
    expect(screen.getByRole('button', { name: 'JOIN', exact: true })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
    await userEvent.click(screen.getByRole('button', { name: 'Bắt đầu' }))

    const start = api.post.mock.calls.find(([url]) => url === '/practice/start')
    expect(start).toBeDefined()
    expect(start[1]).toMatchObject({
      assessment_style: ADAPTIVE,
      source: 'bank',
      concept_ids: [2],
      difficulties: ['EASY'],
      question_count: 5,
    })
  })
})

describe('result labels', () => {
  it('labels a graded result as an official score', () => {
    const { container } = render(
      <EvaluationContent
        data={{
          score: { percentage: '80.00', earned: '8', possible: '10' },
          attempt_count: 1,
          concept_results: [],
          dimensions: {},
          history: [],
          result: null,
        }}
      />,
    )
    expect(screen.getByText('Official score')).toBeInTheDocument()
    expect(container.textContent).toContain('80.00%')
  })

  it('shows estimated ability with confidence and suggestions, never a percentage', () => {
    const { container } = render(
      <AdaptiveResult
        session={{
          ability_estimate: {
            band: 'MEDIUM',
            index: 3.4,
            confidence: 'medium',
            evidence_count: 6,
            provisional: true,
          },
          study_suggestions: [
            {
              concept_id: 1,
              concept_code: 'C1',
              concept_name: 'SELECT',
              subject_area: 'SQL',
              reason: 'below_target',
            },
          ],
          adaptive_progress: null,
        }}
        data={{}}
      />,
    )
    expect(screen.getByText('Estimated ability')).toBeInTheDocument()
    expect(screen.getAllByText('Medium')).toHaveLength(2) // band + confidence
    expect(screen.getByText('SELECT')).toBeInTheDocument()
    expect(screen.getByText(/review this concept next/)).toBeInTheDocument()
    expect(container.textContent).not.toContain('%')
    expect(container.textContent).toMatch(/3\.4/)
  })
})
