import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import fs from 'node:fs'
import vm from 'node:vm'
import ThemeProvider, { useTheme } from '../components/ThemeProvider'
import ThemeSelector from '../components/ThemeSelector'
import { i18n, setLocale } from '../i18n'
import { applyThemeImmediately, readThemePreference, resolveTheme, THEME_KEY } from '../theme'

beforeEach(async () => { localStorage.clear(); await i18n.changeLanguage('en') })
afterEach(() => { localStorage.clear(); vi.restoreAllMocks(); delete document.documentElement.dataset.themeTransitioning })

it.each([null, 'system', 'invalid', 'dark', 'light'])('restores %s with dark as the safe default', (saved) => {
  if (saved !== null) localStorage.setItem(THEME_KEY, saved)
  render(<ThemeProvider><ThemeSelector /></ThemeProvider>)
  const expected = saved === 'light' ? 'light' : 'dark'
  expect(document.documentElement).toHaveAttribute('data-theme', expected)
  expect(document.documentElement).toHaveAttribute('data-theme-mode', expected)
  expect(document.documentElement.style.colorScheme).toBe(expected)
  if (saved !== null) expect(localStorage.getItem(THEME_KEY)).toBe(expected)
})

it('ignores OS preference even on a first visit', () => {
  const matchMedia = vi.fn(() => ({ matches: false }))
  vi.stubGlobal('matchMedia', matchMedia)
  render(<ThemeProvider><ThemeSelector /></ThemeProvider>)
  expect(document.documentElement).toHaveAttribute('data-theme', 'dark')
  expect(matchMedia).not.toHaveBeenCalled()
  vi.unstubAllGlobals()
})

it('handles unavailable storage', () => {
  expect(readThemePreference({ getItem() { throw new Error('blocked') } })).toBe('dark')
  expect(resolveTheme('system')).toBe('dark')
})

it('keeps an explicit choice when persistence is blocked', async () => {
  vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('blocked') })
  render(<ThemeProvider><ThemeSelector /></ThemeProvider>)
  await userEvent.click(screen.getByRole('button', { name: 'Switch to light theme' }))
  expect(document.documentElement).toHaveAttribute('data-theme', 'light')
})

it('toggles immediately with action icons, persists, and has no system selector', async () => {
  render(<ThemeProvider><ThemeSelector /></ThemeProvider>)
  const sun = screen.getByRole('button', { name: 'Switch to light theme' })
  expect(sun.querySelector('[data-icon="sun"]')).not.toBeNull()
  await userEvent.click(sun)
  expect(document.documentElement).toHaveAttribute('data-theme', 'light')
  expect(localStorage.getItem(THEME_KEY)).toBe('light')
  const moon = screen.getByRole('button', { name: 'Switch to dark theme' })
  expect(moon.querySelector('[data-icon="moon"]')).not.toBeNull()
  await userEvent.click(moon)
  expect(document.documentElement).toHaveAttribute('data-theme', 'dark')
  expect(localStorage.getItem(THEME_KEY)).toBe('dark')
  expect(screen.queryByRole('combobox')).not.toBeInTheDocument()
  expect(screen.queryByText(/system/i)).not.toBeInTheDocument()
})

it('supports keyboard activation and localized action labels independently of locale persistence', async () => {
  render(<ThemeProvider><ThemeSelector /></ThemeProvider>)
  await userEvent.tab()
  await userEvent.keyboard('{Enter}')
  expect(document.documentElement).toHaveAttribute('data-theme', 'light')
  await act(() => setLocale('vi'))
  expect(screen.getByRole('button', { name: 'Chuyển sang giao diện tối' })).toHaveFocus()
  await userEvent.keyboard(' ')
  expect(localStorage.getItem(THEME_KEY)).toBe('dark')
  expect(localStorage.getItem('dbcas_locale')).toBe('vi')
})

it('rejects unsupported selections', async () => {
  function Probe() { const { setTheme } = useTheme(); return <button onClick={() => setTheme('system')}>Invalid</button> }
  render(<ThemeProvider><Probe /></ThemeProvider>)
  await userEvent.click(screen.getByRole('button'))
  expect(document.documentElement).toHaveAttribute('data-theme', 'dark')
  expect(localStorage.getItem(THEME_KEY)).toBeNull()
})

it.each([null, 'dark', 'light', 'system', 'invalid'])('bootstraps %s before React without an OS query', (saved) => {
  const storage = { getItem: () => saved, setItem: vi.fn() }
  const root = { dataset: {}, style: {} }
  vm.runInNewContext(fs.readFileSync('public/theme-init.js', 'utf8'), { localStorage: storage, document: { documentElement: root } })
  expect(root.dataset.theme).toBe(saved === 'light' ? 'light' : 'dark')
  expect(root.style.colorScheme).toBe(root.dataset.theme)
  if (['system', 'invalid'].includes(saved)) expect(storage.setItem).toHaveBeenCalledWith(THEME_KEY, 'dark')
  const html = fs.readFileSync('index.html', 'utf8')
  expect(html.indexOf('/theme-init.js')).toBeLessThan(html.indexOf('/src/main.jsx'))
})

it('suppresses low-contrast transitions while changing theme', () => {
  const frames = []
  applyThemeImmediately(document.documentElement, 'light', 'light', callback => frames.push(callback))
  expect(document.documentElement).toHaveAttribute('data-theme-transitioning', 'true')
  frames.shift()(); frames.shift()()
  expect(document.documentElement).not.toHaveAttribute('data-theme-transitioning')
})
