import { act, render } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import usePendingResults from '../usePendingResults'

function Wait({ active, refresh, retry }) { const timedOut = usePendingResults(active, refresh, retry); return <span>{timedOut ? 'Expired' : 'Checking'}</span> }
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

it('backs off and bounds polling when grading remains unavailable', async () => {
  vi.useFakeTimers()
  const refresh = vi.fn()
  render(<Wait active refresh={refresh} />)
  await act(async () => vi.advanceTimersByTimeAsync(600000))
  expect(refresh).toHaveBeenCalledTimes(20)
})

it('does not overlap slow checks and expires even when a request never resolves', async () => {
  vi.useFakeTimers()
  const refresh = vi.fn(() => new Promise(() => {}))
  const view = render(<Wait active="auto_grading" refresh={refresh} />)
  await act(async () => vi.advanceTimersByTimeAsync(300000))
  expect(refresh).toHaveBeenCalledTimes(1)
  expect(view.getByText('Expired')).toBeInTheDocument()
})

it('restarts after retry and checks once when returning to an expired tab', async () => {
  vi.useFakeTimers()
  const refresh = vi.fn()
  const view = render(<Wait active="auto_grading" refresh={refresh} retry={0} />)
  await act(async () => vi.advanceTimersByTimeAsync(300000))
  expect(view.getByText('Expired')).toBeInTheDocument()
  const calls = refresh.mock.calls.length
  await act(async () => window.dispatchEvent(new Event('focus')))
  expect(refresh).toHaveBeenCalledTimes(calls + 1)
  view.rerender(<Wait active="auto_grading" refresh={refresh} retry={1} />)
  expect(view.getByText('Checking')).toBeInTheDocument()
  await act(async () => vi.advanceTimersByTimeAsync(5000))
  expect(refresh).toHaveBeenCalledTimes(calls + 2)
})

it('continues slow instructor publication checks beyond the AI timeout without a busy spinner', async () => {
  vi.useFakeTimers()
  const refresh = vi.fn()
  const view = render(<Wait active="pending_review" refresh={refresh} />)
  await act(async () => vi.advanceTimersByTimeAsync(600000))
  expect(view.getByText('Checking')).toBeInTheDocument()
  expect(refresh).toHaveBeenCalledTimes(22)
  expect(view.queryByText('Expired')).not.toBeInTheDocument()
})
