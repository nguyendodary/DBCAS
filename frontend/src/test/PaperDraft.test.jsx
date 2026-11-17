import { act, renderHook } from '@testing-library/react'
import { beforeEach, expect, it, vi } from 'vitest'
import api from '../api'
import { usePaperDraft } from '../usePaperDraft'

vi.mock('../api', async (original) => ({
  ...(await original()),
  default: { get: vi.fn(), put: vi.fn() },
}))

const question = (seq, overrides = {}) => ({
  seq_no: seq,
  question_id: 100 + seq,
  question_type: 'essay',
  draft: null,
  draft_revision: 0,
  flagged: false,
  flag_revision: 0,
  ...overrides,
})

beforeEach(() => {
  vi.clearAllMocks()
  api.put.mockResolvedValue({ data: { seq_no: 1, revision: 1, answered: true } })
})

it('saves by seq and keeps local answers for every visited question', async () => {
  const saved = vi.fn()
  const { result } = renderHook(() => usePaperDraft('42', saved))
  act(() => result.current.hydrate(question(1)))
  act(() => result.current.setDraft({ essay: 'Answer one' }))
  await act(async () => result.current.flushDraft())
  expect(api.put).toHaveBeenCalledWith('/sessions/42/paper/1/draft', {
    revision: 1,
    essay_answer: 'Answer one',
  })
  expect(saved).toHaveBeenCalledWith({ seq: 1, answered: true, revision: 1 })

  act(() => result.current.hydrate(question(2)))
  act(() => result.current.setDraft({ essay: 'Answer two' }))
  await act(async () => result.current.flushDraft())
  expect(api.put).toHaveBeenCalledWith('/sessions/42/paper/2/draft', {
    revision: 1,
    essay_answer: 'Answer two',
  })

  act(() =>
    result.current.hydrate(
      question(1, { draft_revision: 1, draft: { essay_answer: 'Answer one' } }),
    ),
  )
  expect(result.current.draft.essay).toBe('Answer one')
})

it('flags a revision conflict without discarding the local answer', async () => {
  api.put.mockRejectedValueOnce({
    response: { data: { error: { code: 'draft_revision_conflict' } } },
  })
  const { result } = renderHook(() => usePaperDraft('42'))
  act(() => result.current.hydrate(question(1)))
  act(() => result.current.setDraft({ essay: 'My answer' }))

  await act(async () => {
    await result.current.flushDraft().catch(() => {})
  })
  expect(result.current.saveConflict).toBe(true)
  expect(result.current.draft.essay).toBe('My answer')
  expect(result.current.saveStatus).toBe('error')
})

it('reloads the authoritative draft on request after a conflict', async () => {
  api.put.mockRejectedValueOnce({
    response: { data: { error: { code: 'draft_revision_conflict' } } },
  })
  api.get.mockResolvedValue({
    data: question(1, { draft: { essay_answer: 'Server answer' }, draft_revision: 7 }),
  })
  const { result } = renderHook(() => usePaperDraft('42'))
  act(() => result.current.hydrate(question(1)))
  act(() => result.current.setDraft({ essay: 'My answer' }))
  await act(async () => {
    await result.current.flushDraft().catch(() => {})
  })
  await act(async () => {
    await result.current.reloadSavedDraft()
  })
  expect(api.get).toHaveBeenCalledWith('/sessions/42/paper/1')
  expect(result.current.draft.essay).toBe('Server answer')
  expect(result.current.saveConflict).toBe(false)
  expect(result.current.saveStatus).toBe('saved')
})

it('flushes every dirty record before final submission', async () => {
  const { result } = renderHook(() => usePaperDraft('42'))
  act(() => result.current.hydrate(question(1)))
  act(() => result.current.setDraft({ essay: 'One' }))
  act(() => result.current.hydrate(question(2)))
  act(() => result.current.setDraft({ essay: 'Two' }))
  await act(async () => result.current.flushAll())
  expect(api.put).toHaveBeenCalledTimes(2)
  expect(api.put.mock.calls.map(([, body]) => body.essay_answer)).toEqual(['One', 'Two'])
})

it('keeps the newest local value when an earlier save resolves later', async () => {
  vi.useFakeTimers()
  let releaseFirst
  api.put
    .mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          releaseFirst = resolve
        }),
    )
    .mockResolvedValue({ data: { seq_no: 1, revision: 2, answered: true } })
  const { result } = renderHook(() => usePaperDraft('42'))
  act(() => {
    result.current.hydrate(question(1))
    result.current.setDraft({ essay: 'First' })
  })
  let pending
  await act(async () => {
    pending = result.current.flushDraft()
    await Promise.resolve()
  })
  expect(typeof releaseFirst).toBe('function')
  act(() => result.current.setDraft({ essay: 'Second' }))
  await act(async () => {
    vi.advanceTimersByTime(450)
    await Promise.resolve()
  })
  await act(async () => {
    releaseFirst({ data: { seq_no: 1, revision: 1, answered: true } })
    await pending
  })
  expect(result.current.draft.essay).toBe('Second')
  expect(api.put.mock.calls.at(-1)[1].essay_answer).toBe('Second')
  vi.useRealTimers()
})
