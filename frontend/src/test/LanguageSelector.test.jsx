import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, it, vi } from 'vitest'
import LanguageSelector from '../components/LanguageSelector'
import { i18n } from '../i18n'

beforeEach(async () => { localStorage.clear(); await i18n.changeLanguage('en') })

it('opens on hover, stays open over the popup, and closes after leaving both', async () => {
  const user = userEvent.setup()
  render(<LanguageSelector />)
  const trigger = screen.getByRole('button', { name: 'Language' })
  await user.hover(trigger)
  expect(trigger).toHaveAttribute('aria-expanded', 'true')
  await user.hover(screen.getByRole('menuitemradio', { name: 'English' }))
  await new Promise(resolve => setTimeout(resolve, 160))
  expect(screen.getByRole('menu')).toBeVisible()
  expect(screen.getByRole('menuitemradio', { name: 'English' })).toHaveAttribute('aria-checked', 'true')
  await user.unhover(screen.getByRole('menuitemradio', { name: 'English' }))
  await waitFor(() => expect(screen.queryByRole('menu')).not.toBeInTheDocument())
})

it('changes locale on selection, persists, closes, and restores focus', async () => {
  render(<LanguageSelector />)
  await userEvent.hover(screen.getByRole('button', { name: 'Language' }))
  await userEvent.click(screen.getByRole('menuitemradio', { name: 'Tiếng Việt' }))
  expect(document.documentElement.lang).toBe('vi')
  expect(localStorage.getItem('dbcas_locale')).toBe('vi')
  expect(screen.queryByRole('menu')).not.toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Ngôn ngữ' })).toHaveFocus()
})

it('supports focus, arrows, Home/End, selection, Escape and Tab dismissal', async () => {
  render(<><LanguageSelector /><button>After menu</button></>)
  const user = userEvent.setup()
  await user.tab()
  expect(screen.getByRole('menu')).toBeVisible()
  await user.keyboard('{ArrowDown}')
  await waitFor(() => expect(screen.getByRole('menuitemradio', { name: 'Tiếng Việt' })).toHaveFocus())
  await user.keyboard('{ArrowUp}')
  await waitFor(() => expect(screen.getByRole('menuitemradio', { name: 'English' })).toHaveFocus())
  await user.keyboard('{Home}')
  await waitFor(() => expect(screen.getByRole('menuitemradio', { name: 'Tiếng Việt' })).toHaveFocus())
  await user.keyboard('{End}')
  await waitFor(() => expect(screen.getByRole('menuitemradio', { name: 'English' })).toHaveFocus())
  await user.keyboard('{Escape}')
  expect(screen.queryByRole('menu')).not.toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Language' })).toHaveFocus()
  await user.keyboard('{Enter}')
  await waitFor(() => expect(screen.getByRole('menuitemradio', { name: 'English' })).toHaveFocus())
  await user.keyboard('{ArrowDown}')
  await waitFor(() => expect(screen.getByRole('menuitemradio', { name: 'Tiếng Việt' })).toHaveFocus())
  await user.keyboard(' ')
  expect(localStorage.getItem('dbcas_locale')).toBe('vi')
  await user.keyboard(' ')
  await waitFor(() => expect(screen.getByRole('menuitemradio', { name: 'Tiếng Việt' })).toHaveFocus())
  await user.tab()
  expect(screen.getByRole('button', { name: 'After menu' })).toHaveFocus()
  expect(screen.queryByRole('menu')).not.toBeInTheDocument()
})

it('supports touch/click without hover and dismisses on outside interaction', async () => {
  render(<><LanguageSelector /><button>Outside</button></>)
  const trigger = screen.getByRole('button', { name: 'Language' })
  fireEvent.pointerEnter(trigger, { pointerType: 'touch' })
  await userEvent.click(trigger)
  expect(screen.getByRole('menu')).toBeVisible()
  await userEvent.click(screen.getByRole('button', { name: 'Outside' }))
  expect(screen.queryByRole('menu')).not.toBeInTheDocument()
})
