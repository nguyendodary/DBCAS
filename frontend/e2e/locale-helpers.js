import { readFile } from 'node:fs/promises'
import { expect } from '@playwright/test'

const messages = Object.fromEntries(
  await Promise.all(
    ['vi', 'en'].map(async (locale) => [
      locale,
      JSON.parse(await readFile(new URL(`../src/i18n/${locale}.json`, import.meta.url), 'utf8')),
    ]),
  ),
)

const escapeRegExp = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

// The language menu exposes lang="vi"/"en" on each menuitemradio. Select by
// that stable attribute instead of the localized display name.
export function languageMenuItem(page, locale) {
  return page.locator(`[role="menuitemradio"][lang="${locale}"]`)
}

export async function switchLocale(page, locale) {
  await page.getByRole('button', { name: /^(Language|Ngôn ngữ)$/ }).click()
  await languageMenuItem(page, locale).click()
}

// Admin grading uses either the approve label or the publish label depending
// on session ownership. Both come from the current i18n catalog.
export function approvalButton(scope, locale = 'vi') {
  const { approve, publish } = messages[locale].supervisor
  return scope.getByRole('button', {
    name: new RegExp(`^(${escapeRegExp(approve)}|${escapeRegExp(publish)})$`),
  })
}

export function commentsHeading(scope, locale = 'vi') {
  return scope.getByRole('heading', {
    name: messages[locale].ui.evaluation.questionComments,
  })
}

// AI-official results intentionally carry no per-question comments; legacy or
// manually approved results do. Assert whichever the running app actually
// exposes instead of assuming the old universal heading.
export async function expectQuestionComments(page, sessionId, { locale = 'vi' } = {}) {
  const token = await page.evaluate(() => localStorage.getItem('dbcas_token'))
  const response = await page.request.get(`/api/v1/evaluations/attempts/${sessionId}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  expect(response.ok(), await response.text()).toBe(true)
  const evaluation = await response.json()
  if (evaluation.result == null) {
    await expect(commentsHeading(page, locale)).toHaveCount(0)
    return
  }
  await expect(commentsHeading(page, locale)).toBeVisible({ timeout: 45_000 })
}
