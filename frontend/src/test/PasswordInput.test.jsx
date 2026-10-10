import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import PasswordInput from '../components/PasswordInput'

// Ported from the static-pages mockups: show/hide password toggle.
describe('PasswordInput', () => {
  it('renders a masked password field', () => {
    render(<PasswordInput id="pw" value="" onChange={() => {}} />)
    expect(document.getElementById('pw')).toHaveAttribute('type', 'password')
  })

  it('reveals and re-masks the password on toggle', async () => {
    const user = userEvent.setup()
    render(<PasswordInput id="pw" value="secret" onChange={() => {}} />)

    const toggle = screen.getByRole('button', { name: 'Show password' })
    expect(toggle).toHaveAttribute('aria-pressed', 'false')

    await user.click(toggle)
    const input = document.getElementById('pw')
    expect(input).toHaveAttribute('type', 'text')
    expect(screen.getByRole('button', { name: 'Hide password' })).toHaveAttribute(
      'aria-pressed',
      'true'
    )

    await user.click(screen.getByRole('button', { name: 'Hide password' }))
    expect(input).toHaveAttribute('type', 'password')
  })

  it('toggle is type=button so it never submits the enclosing form', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn((e) => e.preventDefault())
    render(
      <form onSubmit={onSubmit}>
        <PasswordInput id="pw" value="" onChange={() => {}} />
      </form>
    )
    await user.click(screen.getByRole('button', { name: 'Show password' }))
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('still accepts typed input', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<PasswordInput id="pw" value="" onChange={onChange} />)
    await user.type(document.getElementById('pw'), 'a')
    expect(onChange).toHaveBeenCalled()
  })
})
