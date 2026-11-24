import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { DemoCostsPanel, DemoPlanPanel } from '../demo/freePro'

beforeEach(() => localStorage.clear())
afterEach(() => vi.unstubAllEnvs())

describe('Free/Pro UI simulation', () => {
  it('renders nothing when the flag is off', () => {
    vi.stubEnv('VITE_DEMO_FREE_PRO', 'false')
    const { container } = render(
      <>
        <DemoPlanPanel />
        <DemoCostsPanel isAdmin />
      </>,
    )
    expect(container).toBeEmptyDOMElement()
  })

  it('shows Free, flips to Pro in-browser, and marks the demo', async () => {
    vi.stubEnv('VITE_DEMO_FREE_PRO', 'true')
    render(<DemoPlanPanel />)
    expect(screen.getByText(/Free · 5 sessions per day/)).toBeVisible()
    expect(screen.getByText('DEMO')).toBeVisible()
    await userEvent.click(screen.getByRole('button', { name: 'Upgrade to Pro (Demo)' }))
    expect(screen.getByText(/Pro \(Demo\) · 99,000 VND \/ 30 days/)).toBeVisible()
    expect(screen.queryByRole('button', { name: 'Upgrade to Pro (Demo)' })).not.toBeInTheDocument()
    expect(localStorage.getItem('dbcas_demo_plan')).toBe('pro')
  })

  it('enables the demo by default and restores a saved Pro plan', () => {
    localStorage.setItem('dbcas_demo_plan', 'pro')
    render(<DemoPlanPanel />)
    expect(screen.getByText(/Pro \(Demo\) · 99,000 VND \/ 30 days/)).toBeVisible()
  })

  it('renders static costs only for admins', () => {
    vi.stubEnv('VITE_DEMO_FREE_PRO', 'true')
    const { unmount } = render(<DemoCostsPanel isAdmin={false} />)
    expect(screen.queryByTestId('demo-costs-panel')).not.toBeInTheDocument()
    unmount()
    render(<DemoCostsPanel isAdmin />)
    expect(screen.getByTestId('demo-costs-panel')).toBeVisible()
    expect(screen.getByText(/2026-11/)).toBeVisible()
    expect(screen.getByText(/Sample data only/)).toBeVisible()
  })
})
