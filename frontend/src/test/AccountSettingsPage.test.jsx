import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'
import AccountSettingsPage from '../pages/AccountSettingsPage'
import { useAuth } from '../auth'

vi.mock('../auth', () => ({ useAuth: vi.fn() }))

function renderSettings() {
  return render(<MemoryRouter><AccountSettingsPage /></MemoryRouter>)
}

describe('AccountSettingsPage', () => {
  it.each([
    ['Administrator', true],
    ['Learner', false],
  ])('routes a %s account to the %s header treatment', (role, admin) => {
    useAuth.mockReturnValue({
      account: { account_id: 1, full_name: 'A User', email: 'a@b.c', roles: [role], status: 'active' },
      hasRole: (r) => r === role,
    })
    const { container } = renderSettings()
    expect(screen.getByRole('heading', { level: 1, name: 'Settings' })).toBeInTheDocument()
    expect(Boolean(container.querySelector('.hero-band'))).toBe(!admin)
  })
})
