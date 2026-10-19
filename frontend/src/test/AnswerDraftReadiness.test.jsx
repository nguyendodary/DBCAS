import { act, renderHook } from '@testing-library/react'
import { useLayoutEffect } from 'react'
import { beforeEach, expect, it, vi } from 'vitest'
import api from '../api'
import { useAnswerDraft } from '../useAnswerDraft'

vi.mock('../api', () => ({ default: { put: vi.fn() }, apiMessage: (error) => error.message }))

beforeEach(() => {
  vi.resetAllMocks()
  api.put.mockImplementation((_, body) => Promise.resolve({ data: { revision: body.revision } }))
})

it.each([
  ['mcq', 'option', 17, 'selected_option_id'],
  ['sql', 'sql', 'SELECT 1', 'sql_answer'],
  ['essay', 'essay', 'Keys identify rows uniquely.', 'essay_answer'],
])('retains and saves the earliest %s input when a question becomes interactive', async (type, field, value, answerField) => {
  const { result, rerender } = renderHook(({ question }) => {
    const answer = useAnswerDraft('42', question)
    // An input can become interactive at commit, before passive effects run.
    useLayoutEffect(() => {
      if (question) answer.setDraft(previous => ({ ...previous, [field]: value }))
    }, [question?.question_id])
    return answer
  }, { initialProps: { question: null } })

  rerender({ question: { question_id: 9, question_type: type, draft_revision: 0 } })
  expect(result.current.draft[field]).toBe(value)
  await act(async () => { await result.current.flushDraft() })
  expect(api.put).toHaveBeenCalledWith('/sessions/42/draft', {
    question_id: 9, revision: 1, [answerField]: value,
  })
  expect(result.current.saveStatus).toBe('saved')
})
