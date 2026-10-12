import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, it } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'
import LanguageSelector from '../components/LanguageSelector'
import { detectLocale, i18n, LOCALE_KEY, setLocale, t, number, percent, dateOnly, dateTime, time, message, resolveMessage, resources } from '../i18n'

afterEach(async () => { localStorage.removeItem(LOCALE_KEY); await act(() => i18n.changeLanguage('en')) })

it('prefers a saved supported locale over the browser preference', () => {
  expect(detectLocale({ getItem: () => 'en' }, ['vi-VN'])).toBe('en')
  expect(detectLocale({ getItem: () => 'vi' }, ['en-US'])).toBe('vi')
})
it('ignores invalid storage and uses the primary browser language or English', () => {
  expect(detectLocale({ getItem: () => 'fr' }, ['vi-VN'])).toBe('vi')
  expect(detectLocale({ getItem: () => null }, ['en-GB'])).toBe('en')
  expect(detectLocale({ getItem: () => null }, ['fr-FR', 'vi'])).toBe('en')
  expect(detectLocale({ getItem: () => { throw new Error('restricted') } }, ['vi'])).toBe('vi')
})
it('switches immediately, persists the preference, and synchronizes html lang', async () => {
  render(<LanguageSelector />)
  await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Language' }), 'vi')
  expect(document.documentElement.lang).toBe('vi')
  expect(localStorage.getItem(LOCALE_KEY)).toBe('vi')
  expect(screen.getByRole('combobox', { name: 'Ngôn ngữ' })).toHaveValue('vi')
  expect(detectLocale(localStorage, ['en'])).toBe('vi')
  expect(await setLocale('fr')).toBe(false)
  expect(i18n.language).toBe('vi')
})
it('resolves plural forms and stored messages in the active locale', async () => {
  const stored = message('common.items', { count: 2 })
  expect(t('common.items', { count: 1 })).toBe('1 item')
  expect(resolveMessage(stored)).toBe('2 items')
  await act(() => setLocale('vi'))
  expect(t('common.items', { count: 1 })).toBe('1 mục')
  expect(resolveMessage(stored)).toBe('2 mục')
})
it('formats numbers, percentages, timestamps and calendar dates by locale', async () => {
  expect(number(1234.5)).toBe('1,234.5')
  expect(percent('60.25')).toBe('60.25%')
  const instant = '2026-10-12T00:00:00Z'
  expect(dateTime(instant)).toBe(new Intl.DateTimeFormat('en-US', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(instant)))
  expect(time(instant)).toBe(new Intl.DateTimeFormat('en-US', { timeStyle: 'medium' }).format(new Date(instant)))
  await act(() => setLocale('vi'))
  expect(number(1234.5)).toBe('1.234,5')
  expect(percent('60.25')).toBe('60,25%')
  expect(dateOnly('2026-10-12')).toBe(new Intl.DateTimeFormat('vi-VN', { dateStyle: 'medium', timeZone: 'UTC' }).format(new Date(instant)))
  expect(time(instant)).toBe(new Intl.DateTimeFormat('vi-VN', { timeStyle: 'medium' }).format(new Date(instant)))
  expect(number(null)).toBe('—')
  expect(dateTime('invalid')).toBe('—')
})
it('has matching nonempty EN/VI leaves and interpolation names', () => {
  const leaves = (obj, prefix = '') => Object.entries(obj).flatMap(([key, value]) => typeof value === 'string' ? [[`${prefix}${key}`, value]] : leaves(value, `${prefix}${key}.`))
  const english = Object.fromEntries(leaves(resources.en.translation))
  const vietnamese = Object.fromEntries(leaves(resources.vi.translation))
  expect(Object.keys(english).sort()).toEqual(Object.keys(vietnamese).sort())
  for (const [key, value] of Object.entries(english)) {
    expect(value.trim(), key).not.toBe('')
    expect(vietnamese[key].trim(), key).not.toBe('')
    const slots = (text) => [...text.matchAll(/{{\s*([^},]+)/g)].map(match => match[1].trim()).sort()
    expect(slots(value), key).toEqual(slots(vietnamese[key]))
  }
})
it('fails visibly on a missing translation instead of silently falling back to English', () => {
  expect(() => t('missing.key')).toThrow('Missing DBCAS translation: missing.key')
})
it('resolves every literal translation and message key used by production modules in both locales', () => {
  const files = (directory) => fs.readdirSync(directory, { withFileTypes: true }).flatMap(entry => {
    const file = path.join(directory, entry.name)
    return entry.isDirectory() ? (entry.name === 'test' ? [] : files(file)) : /\.[jt]sx?$/.test(file) ? [file] : []
  })
  const missing = []
  for (const file of files(path.resolve('src'))) {
    const source = fs.readFileSync(file, 'utf8')
    for (const [, , key] of source.matchAll(/\b(?:t|message|validationError)\(\s*(['"])([^'"]+)\1/g)) {
      for (const lng of ['en', 'vi']) {
        if (!i18n.exists(key, { lng, count: 2 })) missing.push(`${path.relative('src', file)}: ${lng}:${key}`)
      }
    }
  }
  expect(missing).toEqual([])
})
