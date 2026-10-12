import { act, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'
import ThemeProvider, { useTheme } from '../components/ThemeProvider'
import ThemeSelector from '../components/ThemeSelector'
import { i18n, setLocale } from '../i18n'
import { applyTheme, applyThemeImmediately, currentSystemTheme, readThemePreference, resolveTheme, THEME_KEY } from '../theme'

function mockSystemTheme(isDark) {
  const listeners = new Set()
  const query = {
    matches: isDark,
    media: '(prefers-color-scheme: dark)',
    addEventListener: (_event, listener) => listeners.add(listener),
    removeEventListener: (_event, listener) => listeners.delete(listener),
  }
  Object.defineProperty(window, 'matchMedia', { configurable: true, value: vi.fn(() => query) })
  return {
    query,
    change(value) {
      query.matches = value
      for (const listener of listeners) listener({ matches: value })
    },
    listenerCount: () => listeners.size,
  }
}

function Probe() {
  const { theme, resolvedTheme, setTheme } = useTheme()
  return <>
    <output data-testid="theme-mode">{theme}</output>
    <output data-testid="resolved-theme">{resolvedTheme}</output>
    <button onClick={() => setTheme('light')}>Choose light</button>
    <button onClick={() => setTheme('not-a-theme')}>Choose invalid</button>
  </>
}

beforeEach(async () => {
  localStorage.clear()
  await i18n.changeLanguage('en')
})

afterEach(() => {
  delete window.matchMedia
  delete document.documentElement.dataset.theme
  delete document.documentElement.dataset.themeMode
  document.documentElement.style.colorScheme = ''
  localStorage.clear()
})

it('resolves supported modes, uses system safely, and ignores invalid storage', () => {
  expect(resolveTheme('light', 'dark')).toBe('light')
  expect(resolveTheme('dark', 'light')).toBe('dark')
  expect(resolveTheme('system', 'dark')).toBe('dark')
  expect(resolveTheme('invalid', 'light')).toBe('light')
  expect(readThemePreference({ getItem: () => 'invalid' })).toBe('system')
  expect(readThemePreference({ getItem: () => { throw new Error('blocked') } })).toBe('system')
  expect(currentSystemTheme(() => ({ matches: true }))).toBe('dark')
})

it('falls back to system mode when localStorage access is blocked', () => {
  const descriptor = Object.getOwnPropertyDescriptor(globalThis, 'localStorage')
  try {
    Object.defineProperty(globalThis, 'localStorage', {
      configurable: true,
      get() { throw new Error('blocked') },
    })
    expect(readThemePreference()).toBe('system')
  } finally {
    if (descriptor) Object.defineProperty(globalThis, 'localStorage', descriptor)
    else delete globalThis.localStorage
  }
})

it('applies the saved preference at provider startup', () => {
  localStorage.setItem(THEME_KEY, 'light')
  mockSystemTheme(true)
  render(<ThemeProvider><Probe /></ThemeProvider>)
  expect(screen.getByTestId('theme-mode')).toHaveTextContent('light')
  expect(screen.getByTestId('resolved-theme')).toHaveTextContent('light')
  expect(document.documentElement).toHaveAttribute('data-theme', 'light')
  expect(document.documentElement).toHaveAttribute('data-theme-mode', 'light')
  expect(document.documentElement.style.colorScheme).toBe('light')
})

it('follows live OS changes only in system mode and removes its listener', async () => {
  const system = mockSystemTheme(false)
  const view = render(<ThemeProvider><Probe /></ThemeProvider>)
  expect(screen.getByTestId('resolved-theme')).toHaveTextContent('light')
  expect(system.listenerCount()).toBe(1)
  await act(async () => system.change(true))
  expect(screen.getByTestId('resolved-theme')).toHaveTextContent('dark')
  expect(document.documentElement).toHaveAttribute('data-theme', 'dark')
  await userEvent.click(screen.getByRole('button', { name: 'Choose light' }))
  await act(async () => system.change(false))
  expect(screen.getByTestId('theme-mode')).toHaveTextContent('light')
  expect(screen.getByTestId('resolved-theme')).toHaveTextContent('light')
  expect(localStorage.getItem(THEME_KEY)).toBe('light')
  view.unmount()
  expect(system.listenerCount()).toBe(0)
})

it('rejects unsupported selections without changing the saved mode', async () => {
  mockSystemTheme(false)
  render(<ThemeProvider><Probe /></ThemeProvider>)
  await userEvent.click(screen.getByRole('button', { name: 'Choose invalid' }))
  expect(screen.getByTestId('theme-mode')).toHaveTextContent('system')
  expect(localStorage.getItem(THEME_KEY)).toBeNull()
})

it('localizes the selector and keeps locale and theme preferences independent', async () => {
  mockSystemTheme(false)
  render(<ThemeProvider><ThemeSelector /></ThemeProvider>)
  const selector = screen.getByRole('combobox', { name: 'Appearance' })
  expect(selector).toHaveValue('system')
  expect(within(selector).getByRole('option', { name: 'Light' })).toHaveValue('light')
  await userEvent.selectOptions(selector, 'dark')
  expect(localStorage.getItem(THEME_KEY)).toBe('dark')
  await act(() => setLocale('vi'))
  expect(screen.getByRole('combobox', { name: 'Giao diện' })).toHaveValue('dark')
  expect(screen.getByRole('option', { name: 'Theo hệ thống' })).toHaveValue('system')
  expect(localStorage.getItem('dbcas_locale')).toBe('vi')
  await act(() => setLocale('en'))
  expect(localStorage.getItem(THEME_KEY)).toBe('dark')
})

it('runs the theme bootstrap before the React entry point', () => {
  const html = fs.readFileSync(path.resolve('index.html'), 'utf8')
  const bootstrap = fs.readFileSync(path.resolve('public/theme-init.js'), 'utf8')
  expect(html.indexOf('/theme-init.js')).toBeGreaterThanOrEqual(0)
  expect(html.indexOf('/theme-init.js')).toBeLessThan(html.indexOf('/src/main.jsx'))
  expect(bootstrap).toContain("localStorage.getItem('dbcas_theme')")
  expect(bootstrap).toContain('document.documentElement.dataset.theme = resolved')
})

it('applies a resolved theme and its native control color scheme to the root', () => {
  applyTheme(document.documentElement, 'dark', 'system')
  expect(document.documentElement).toHaveAttribute('data-theme', 'dark')
  expect(document.documentElement).toHaveAttribute('data-theme-mode', 'system')
  expect(document.documentElement.style.colorScheme).toBe('dark')
})

it('prevents low-contrast control transitions while a theme is changing', () => {
  const frames = []
  const scheduleFrame = callback => frames.push(callback)
  applyThemeImmediately(document.documentElement, 'light', 'light', scheduleFrame)
  expect(document.documentElement).toHaveAttribute('data-theme-transitioning', 'true')
  expect(document.documentElement).toHaveAttribute('data-theme', 'light')
  frames.shift()()
  expect(document.documentElement).toHaveAttribute('data-theme-transitioning', 'true')
  frames.shift()()
  expect(document.documentElement).not.toHaveAttribute('data-theme-transitioning')
})
