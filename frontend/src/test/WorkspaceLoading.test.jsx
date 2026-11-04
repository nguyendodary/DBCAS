import { lazy, Suspense } from 'react'
import { act, render, screen } from '@testing-library/react'
import { it, expect, vi } from 'vitest'
import WorkspaceLoading from '../components/WorkspaceLoading'

it('bounds a stalled module load, offers Retry and recovers when the module arrives', async () => {
  vi.useFakeTimers()
  const retry = vi.fn()
  let release
  const Page = lazy(
    () =>
      new Promise((resolve) => {
        release = resolve
      }),
  )
  try {
    render(
      <Suspense fallback={<WorkspaceLoading label="Loading workspace" onRetry={retry} />}>
        <Page />
      </Suspense>,
    )
    expect(screen.getByRole('status', { name: 'Loading workspace' })).toBeVisible()
    await act(async () => {
      await vi.advanceTimersByTimeAsync(15001)
    })
    expect(screen.getByRole('alert')).toBeVisible()
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
    await act(async () => {
      screen.getByRole('button', { name: /Retry|Thử lại/i }).click()
    })
    expect(retry).toHaveBeenCalledTimes(1)
    await act(async () => {
      release({ default: () => <h1>Loaded workspace</h1> })
    })
    expect(screen.getByRole('heading', { name: 'Loaded workspace' })).toBeVisible()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  } finally {
    vi.useRealTimers()
  }
})
