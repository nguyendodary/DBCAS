import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { vi } from 'vitest'
import { ConfirmDialog } from '../components/ui'
import SqlEditor, { sqlTokens } from '../components/SqlEditor'

function Confirmation({ busy = false }) {
  const [open, setOpen] = useState(false)
  return <div style={{ transform: 'translateY(6px)' }}><button onClick={() => setOpen(true)}>Open confirmation</button>
    <ConfirmDialog open={open} busy={busy} title="Finish assessment?" confirmLabel="Finish" onConfirm={() => setOpen(false)} onCancel={() => setOpen(false)}>
      Your saved answers will be submitted.
    </ConfirmDialog></div>
}

it('portals the dialog outside transformed ancestors and restores scroll, background and focus', async () => {
  const { container } = render(<Confirmation />)
  const opener = screen.getByRole('button', { name: 'Open confirmation' })
  await userEvent.click(opener)
  const dialog = screen.getByRole('dialog', { name: 'Finish assessment?' })
  expect(dialog.parentElement.parentElement).toBe(document.body)
  expect(container).toHaveAttribute('inert')
  expect(container).toHaveAttribute('aria-hidden', 'true')
  expect(document.body.style.overflow).toBe('hidden')
  expect(dialog).toHaveAccessibleDescription('Your saved answers will be submitted.')
  expect(screen.getByRole('button', { name: 'Keep going' })).toHaveFocus()
  await userEvent.keyboard('{Escape}')
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  expect(container).not.toHaveAttribute('inert')
  expect(document.body.style.overflow).not.toBe('hidden')
  expect(opener).toHaveFocus()
})

it('traps keyboard focus at both ends and prevents busy dismissal', async () => {
  render(<Confirmation />)
  await userEvent.click(screen.getByRole('button', { name: 'Open confirmation' }))
  await userEvent.keyboard('{Shift>}{Tab}{/Shift}')
  expect(screen.getByRole('button', { name: 'Finish' })).toHaveFocus()
  await userEvent.keyboard('{Tab}')
  expect(screen.getByRole('button', { name: 'Keep going' })).toHaveFocus()
})

it('keeps a busy dialog open and focuses the dialog when all controls are disabled', async () => {
  render(<Confirmation busy />)
  await userEvent.click(screen.getByRole('button', { name: 'Open confirmation' }))
  expect(screen.getByRole('dialog')).toHaveFocus()
  await userEvent.keyboard('{Escape}{Tab}')
  expect(screen.getByRole('dialog')).toHaveFocus()
})

it('preserves existing background accessibility attributes on dismissal', async () => {
  const { container } = render(<Confirmation />)
  container.setAttribute('aria-hidden', 'false')
  await userEvent.click(screen.getByRole('button', { name: 'Open confirmation' }))
  await userEvent.click(screen.getByRole('button', { name: 'Keep going' }))
  expect(container).toHaveAttribute('aria-hidden', 'false')
})

it('highlights SQL without changing text or interpreting markup', () => {
  const sql = `SELECT COALESCE("total", 1.00), '<script>alert(1)</script>' -- comment\nFROM sales WHERE id = 1234;`
  const tokens = sqlTokens(sql)
  expect(tokens.map((t) => t.text).join('')).toBe(sql)
  expect(tokens.find((t) => t.text === 'SELECT').kind).toBe('keyword')
  expect(tokens.find((t) => t.text === 'COALESCE').kind).toBe('function')
  const { container } = render(<SqlEditor value={sql} onChange={vi.fn()} />)
  expect(screen.getByRole('textbox', { name: 'Your query' })).toHaveValue(sql)
  expect(container.querySelector('script')).toBeNull()
  expect(container.querySelector('pre')).toHaveAttribute('aria-hidden', 'true')
})

it('keeps native editing and Tab navigation while synchronizing editor scroll', async () => {
  const changed = vi.fn()
  const { container } = render(<><SqlEditor value="SELECT 1" onChange={changed} /><button>Run SQL</button></>)
  const editor = screen.getByRole('textbox', { name: 'Your query' })
  fireEvent.change(editor, { target: { value: 'SELECT 2' } })
  expect(changed).toHaveBeenCalledWith('SELECT 2')
  editor.scrollTop = 48
  editor.scrollLeft = 100
  fireEvent.scroll(editor)
  expect(container.querySelector('pre').scrollTop).toBe(48)
  expect(container.querySelector('pre').scrollLeft).toBe(100)
  editor.focus()
  await userEvent.tab()
  expect(screen.getByRole('button', { name: 'Run SQL' })).toHaveFocus()
})
