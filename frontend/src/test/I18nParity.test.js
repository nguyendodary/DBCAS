import { expect, it } from 'vitest'
import en from '../i18n/en.json'
import vi from '../i18n/vi.json'

function flatten(value, prefix = '') {
  return Object.entries(value).flatMap(([key, child]) => {
    const path = prefix ? `${prefix}.${key}` : key
    return child && typeof child === 'object' && !Array.isArray(child)
      ? flatten(child, path)
      : [path]
  })
}

it('keeps the English and Vietnamese translation key sets identical', () => {
  const english = flatten(en).sort()
  const vietnamese = flatten(vi).sort()
  expect(vietnamese).toEqual(english)
})
