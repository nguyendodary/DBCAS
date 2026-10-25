import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, it, vi } from 'vitest'
import { RowMenu, MenuItem } from '../components/admin'

afterEach(() => vi.restoreAllMocks())

it('escapes a clipped card and opens upwards near the viewport bottom', async () => {
  vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockImplementation(function () {
    return this.getAttribute('role') === 'menu'
      ? { width: 200, height: 120, top: 0, bottom: 120, left: 0, right: 200 }
      : { width: 30, height: 30, top: window.innerHeight - 45, bottom: window.innerHeight - 15, left: 300, right: 330 }
  })
  const action = vi.fn()
  render(<div style={{ overflow: 'hidden', height: 40 }}><RowMenu><MenuItem onSelect={action}>Delete question</MenuItem></RowMenu></div>)
  await userEvent.click(screen.getByRole('button', { name: 'Actions' }))
  const menu = screen.getByRole('menu')
  expect(menu.parentElement).toBe(document.body)
  expect(parseFloat(menu.style.top) + 120).toBeLessThan(window.innerHeight - 45)
  await userEvent.click(screen.getByRole('menuitem', { name: 'Delete question' }))
  expect(action).toHaveBeenCalledOnce()
  expect(screen.queryByRole('menu')).not.toBeInTheDocument()
})

it('supports keyboard navigation, skips disabled actions and restores focus on Escape', async () => {
  render(<RowMenu><MenuItem disabled>Unavailable</MenuItem><MenuItem>First</MenuItem><MenuItem>Last</MenuItem></RowMenu>)
  const trigger = screen.getByRole('button', { name: 'Actions' })
  await userEvent.click(trigger)
  expect(screen.getByRole('menuitem', { name: 'First' })).toHaveFocus()
  await userEvent.keyboard('{ArrowDown}')
  expect(screen.getByRole('menuitem', { name: 'Last' })).toHaveFocus()
  await userEvent.keyboard('{Escape}')
  expect(trigger).toHaveFocus()
  expect(screen.queryByRole('menu')).not.toBeInTheDocument()
  await userEvent.click(trigger)
  fireEvent.mouseDown(document.body)
  expect(screen.queryByRole('menu')).not.toBeInTheDocument()
})
