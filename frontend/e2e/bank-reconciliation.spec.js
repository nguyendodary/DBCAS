import { test, expect } from '@playwright/test'
import fs from 'node:fs'

const resources = Object.fromEntries(['en', 'vi'].map(locale =>
  [locale, JSON.parse(fs.readFileSync(new URL(`../src/i18n/${locale}.json`, import.meta.url), 'utf8'))]))

const template = JSON.parse(fs.readFileSync(new URL('../../db/assessment_templates/postgres_foundations_current.json', import.meta.url), 'utf8'))
const label = (locale, key) => key.split('.').reduce((value, part) => value[part], resources[locale])

for (const locale of ['en', 'vi']) test(`${locale}: PostgreSQL filter and current foundations publish validation`, async ({ page }) => {
  await page.goto('/login')
  await page.evaluate(value => localStorage.setItem('dbcas_locale', value), locale)
  await page.reload()
  await page.getByLabel(label(locale, 'common.email'), { exact: true }).fill('release-admin@test.dev')
  await page.getByLabel(label(locale, 'auth.password'), { exact: true }).fill('ReleaseTest123!')
  await page.getByRole('button', { name: label(locale, 'auth.signIn'), exact: true }).click()
  await expect(page).toHaveURL(/\/admin$/)
  const token = await page.evaluate(() => localStorage.getItem('dbcas_token'))
  const headers = { Authorization: `Bearer ${token}`, 'Accept-Language': locale }
  const api = (path, options = {}) => page.request.fetch(`http://127.0.0.1:8100/api/v1${path}`, { ...options, headers })
  await page.goto('/admin/questions')
  await page.getByLabel(label(locale, 'admin.questions.filterTopic')).selectOption('postgres')
  const prompt = 'Querying jsonb_path_ops vs jsonb_ops GIN indexes differ mainly in:'
  await page.getByLabel(label(locale, 'admin.questions.search')).fill(prompt)
  await expect(page.getByText(prompt, { exact: true })).toBeVisible()
  const found = await api(`/admin/questions?q=${encodeURIComponent(prompt)}&tag=postgres`)
  expect(found.ok()).toBeTruthy()
  const questions = await found.json()
  expect(questions).toHaveLength(1)
  const detail = await (await api(`/admin/questions/${questions[0].question_id}`)).json()
  const correct = detail.options.find(option => option.is_correct)
  expect(correct.option_label).toBe('C')
  expect(correct.option_text).toContain('@>, @?, and @@')
  expect(detail.translations.find(row => row.locale === 'vi').current).toBe(true)
  const concepts = await (await api('/admin/concepts')).json()
  const payload = { ...template, title: `${template.title} ${locale} ${Date.now()}`,
    concepts: template.concepts.map(({ concept_code, ...target }) => ({ ...target,
      concept_id: concepts.find(c => c.concept_code === concept_code).concept_id })) }
  const oldConfig = await api('/admin/assessments', { method: 'POST', data: { ...payload,
    duration_min: 30, max_questions: 8, target_mcq: 4, target_sql: 2, target_essay: 2 } })
  expect(oldConfig.status()).toBe(422)
  const created = await api('/admin/assessments', { method: 'POST', data: payload })
  expect(created.ok()).toBeTruthy()
  const draft = await created.json()
  try {
    await page.goto('/admin/assessments')
    await expect(page.getByText(payload.title, { exact: true })).toBeVisible()
    const published = await api(`/admin/assessments/${draft.assessment_id}`, { method: 'PATCH', data: { status: 'published' } })
    expect(published.ok(), await published.text()).toBeTruthy()
    expect((await published.json()).status).toBe('published')
  } finally {
    const removed = await api(`/admin/assessments/${draft.assessment_id}`, { method: 'DELETE' })
    expect(removed.ok()).toBeTruthy()
  }
})
