import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import api from '../api'
import AssessmentsPage from '../pages/AssessmentsPage'
import AdaptiveResult from '../components/AdaptiveResult'
import AssessmentStylePicker from '../components/AssessmentStylePicker'
import { EvaluationContent } from '../pages/EvaluationPage'
import { resources, t } from '../i18n'
import {
  ADAPTIVE,
  ADAPTIVE_MAX_QUESTIONS,
  ADAPTIVE_MIN_QUESTIONS,
  FIXED,
  FIXED_DEFAULT_MIX,
  FIXED_MIXED_TOTAL_LIMIT,
  buildPracticePayload,
  clampAdaptiveCount,
  fixedMixTotal,
  isAdaptiveResult,
  isSelectionValid,
  validateFixedMix,
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

describe('assessment mode helpers', () => {
  it('builds a bank-only FIXED payload with one band and the current mix', () => {
    const payload = buildPracticePayload({
      style: FIXED,
      selected: [1, 2],
      bands: ['EASY', 'HARD'],
      source: 'ai',
      count: 99,
      mix: FIXED_DEFAULT_MIX,
      requestId: 'req-1',
    })
    expect(payload).toEqual({
      concept_ids: [1, 2],
      difficulties: ['EASY'],
      source: 'bank',
      question_count: 13,
      question_mix: { mcq: 10, sql: 2, essay: 1 },
      request_id: 'req-1',
      assessment_style: FIXED,
    })
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

  it('mirrors the FIXED single-type, mixed-type and total caps', () => {
    expect(validateFixedMix({ mcq: 50, sql: 0, essay: 0 }).valid).toBe(true)
    expect(validateFixedMix({ mcq: 51, sql: 0, essay: 0 }).errors).toContainEqual({
      code: 'single_limit',
      kind: 'mcq',
      limit: 50,
    })
    expect(validateFixedMix({ mcq: 20, sql: 2, essay: 3 }).valid).toBe(true)
    expect(validateFixedMix({ mcq: 21, sql: 1, essay: 0 }).errors).toContainEqual({
      code: 'type_limit',
      kind: 'mcq',
      limit: 20,
    })
    expect(validateFixedMix({ mcq: 20, sql: 2, essay: 4 }).errors).toContainEqual({
      code: 'total_limit',
      limit: FIXED_MIXED_TOTAL_LIMIT,
    })
    expect(validateFixedMix({ mcq: 0, sql: 0, essay: 0 }).errors).toContainEqual({
      code: 'empty',
    })
    expect(validateFixedMix({ mcq: 1.5, sql: 0, essay: 0 }).errors).toContainEqual({
      code: 'invalid',
    })
    expect(fixedMixTotal({ mcq: 4, sql: 2, essay: 1 })).toBe(7)
  })

  it('validates FIXED selection as one band, bank source and a valid mix', () => {
    const base = {
      style: FIXED,
      selected: [1],
      bands: ['MEDIUM'],
      source: 'bank',
      count: 13,
      limits: { min: 1, max: 25 },
      mix: FIXED_DEFAULT_MIX,
    }
    expect(isSelectionValid(base)).toBe(true)
    expect(isSelectionValid({ ...base, bands: ['EASY', 'HARD'] })).toBe(false)
    expect(isSelectionValid({ ...base, source: 'ai' })).toBe(false)
    expect(isSelectionValid({ ...base, mix: { mcq: 0, sql: 0, essay: 0 } })).toBe(false)
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
  it('explains the test constraints and both modes', async () => {
    const onChange = vi.fn()
    render(<AssessmentStylePicker value={FIXED} onChange={onChange} />)
    expect(screen.getByRole('radio', { name: 'Test' })).toBeChecked()
    expect(screen.getByRole('radio', { name: 'Adaptive practice' })).toBeInTheDocument()
    expect(screen.getByText('Exactly one difficulty band')).toBeInTheDocument()
    expect(
      screen.getByText('Official score only after administrator publication'),
    ).toBeInTheDocument()
    await userEvent.click(screen.getByRole('radio', { name: 'Adaptive practice' }))
    expect(onChange).toHaveBeenCalledWith(ADAPTIVE)
    expect(screen.queryByText('Adaptive practice constraints')).not.toBeInTheDocument()
  })

  it('documents the adaptive policy without the stale five-per-round copy', () => {
    render(<AssessmentStylePicker value={ADAPTIVE} onChange={() => {}} />)
    expect(screen.getByText('Adaptive practice constraints')).toBeInTheDocument()
    expect(screen.getByText('Exactly one concept')).toBeInTheDocument()
    expect(screen.getByText('Multiple-choice questions only')).toBeInTheDocument()
    expect(screen.getByText('3–50 questions')).toBeInTheDocument()
    expect(t('supervisor.adaptiveHelp')).toContain('3 anchor MCQs')
    expect(t('supervisor.adaptiveHelp')).toContain('3–50')
    expect(t('supervisor.adaptiveHelp')).not.toContain('13 questions')
  })
})

describe('practice start flow', () => {
  it('creates a FIXED test from the picker and lands in the exam room', async () => {
    renderPractice()
    await userEvent.click(await screen.findByRole('button', { name: 'SELECT', exact: true }))
    expect(screen.getByText('13 questions in this test.')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Start' }))

    const start = api.post.mock.calls.find(([url]) => url === '/practice/start')
    expect(start).toBeDefined()
    expect(start[1]).toMatchObject({
      assessment_style: FIXED,
      source: 'bank',
      concept_ids: [1],
      difficulties: ['EASY'],
      question_count: 13,
      question_mix: { mcq: 10, sql: 2, essay: 1 },
    })
    expect(await screen.findByText('EXAM ROOM')).toBeInTheDocument()
  })

  it('updates the FIXED mix and shows an inline limit message', async () => {
    renderPractice()
    await userEvent.click(await screen.findByRole('button', { name: 'SELECT', exact: true }))
    const mcq = screen.getByLabelText('MCQ')
    await userEvent.clear(mcq)
    await userEvent.type(mcq, '21')
    await userEvent.clear(screen.getByLabelText('SQL'))
    await userEvent.type(screen.getByLabelText('SQL'), '1')
    expect(screen.getByRole('alert')).toHaveTextContent(
      'A mixed test allows at most 20 MCQ questions.',
    )
    expect(screen.getByRole('button', { name: 'Start' })).toBeDisabled()
  })

  it('enforces adaptive constraints and starts an adaptive session', async () => {
    renderPractice()
    await userEvent.click(await screen.findByRole('button', { name: 'SELECT', exact: true }))
    await userEvent.click(screen.getByRole('radio', { name: 'Adaptive practice' }))

    expect(await screen.findByText('Adaptive practice constraints')).toBeInTheDocument()
    expect(screen.getByText('Exactly one concept')).toBeInTheDocument()
    expect(screen.getByText('3–50 questions')).toBeInTheDocument()

    const count = screen.getByLabelText('Number of questions (3–50)')
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
    await userEvent.click(screen.getByRole('button', { name: 'Start' }))

    const start = api.post.mock.calls.find(([url]) => url === '/practice/start')
    expect(start).toBeDefined()
    expect(start[1]).toMatchObject({
      assessment_style: ADAPTIVE,
      source: 'bank',
      concept_ids: [2],
      difficulties: ['EASY'],
      question_count: 5,
    })
    expect(start[1]).not.toHaveProperty('question_mix')
  })
})

describe('result labels and copy', () => {
  it('never labels a provisional result as official', () => {
    render(
      <EvaluationContent
        data={{
          status: 'provisional',
          provisional: true,
          approved: false,
          score: { percentage: '80.00', earned: '8', possible: '10' },
          attempt_count: 1,
          concept_results: [],
          dimensions: {},
          history: [],
          result: null,
        }}
      />,
    )
    expect(screen.getByText('Provisional score')).toBeInTheDocument()
    expect(screen.getByText('Provisional result — AI graded, not yet approved')).toBeInTheDocument()
    expect(screen.queryByText('Official score')).not.toBeInTheDocument()
  })

  it('labels a published result as official', () => {
    const { container } = render(
      <EvaluationContent
        data={{
          status: 'ready',
          provisional: false,
          approved: true,
          adjusted: true,
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
    expect(screen.getByText('✓ Approved by an administrator — official result')).toBeInTheDocument()
    expect(screen.getByText('Scores were adjusted')).toBeInTheDocument()
    expect(screen.queryByText('Provisional score')).not.toBeInTheDocument()
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
    expect(screen.getAllByText('Medium')).toHaveLength(2)
    expect(screen.getByText('SELECT')).toBeInTheDocument()
    expect(screen.getByText(/review this concept next/)).toBeInTheDocument()
    expect(container.textContent).not.toContain('%')
    expect(container.textContent).toMatch(/3\.4/)
  })

  it('keeps user-facing role copy as User and the Vietnamese official label distinct', () => {
    expect(t('status.learner')).toBe('User')
    expect(resources.vi.translation.status.learner).not.toBe('Learner')
    expect(resources.vi.translation.assessmentStyle.fixed.provisionalLabel).toBe('Điểm tạm thời')
    expect(resources.vi.translation.assessmentStyle.fixed.resultLabel).toBe('Điểm chính thức')
    expect(resources.vi.translation.supervisor.adaptiveHelp).toContain('3 câu trắc nghiệm neo')
  })
})
