import { act, render } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import usePendingResults from '../usePendingResults'

function Wait({ active, refresh }) { usePendingResults(active, refresh); return null }
afterEach(() => vi.useRealTimers())

it('refreshes outstanding automatic grades and stops when publication completes', () => {
  vi.useFakeTimers()
  const refresh = vi.fn()
  const view = render(<Wait active={false} refresh={refresh} />)
  act(() => vi.advanceTimersByTime(5000))
  expect(refresh).not.toHaveBeenCalled()
  view.rerender(<Wait active refresh={refresh} />)
  act(() => vi.advanceTimersByTime(5000))
  expect(refresh).toHaveBeenCalledTimes(1)
  view.rerender(<Wait active={false} refresh={refresh} />)
  act(() => vi.advanceTimersByTime(10000))
  expect(refresh).toHaveBeenCalledTimes(1)
})

it('uses the current refresh action and cancels outstanding work on navigation', () => {
  vi.useFakeTimers()
  const first = vi.fn(), second = vi.fn()
  const view = render(<Wait active refresh={first} />)
  view.rerender(<Wait active refresh={second} />)
  act(() => vi.advanceTimersByTime(5000))
  expect(first).not.toHaveBeenCalled()
  expect(second).toHaveBeenCalledTimes(1)
  view.unmount()
  act(() => vi.advanceTimersByTime(10000))
  expect(second).toHaveBeenCalledTimes(1)
})

it('bounds polling when grading remains unavailable', () => {
  vi.useFakeTimers()
  const refresh = vi.fn()
  render(<Wait active refresh={refresh} />)
  act(() => vi.advanceTimersByTime(600000))
  expect(refresh).toHaveBeenCalledTimes(60)
})
