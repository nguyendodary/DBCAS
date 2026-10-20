import { test, expect } from './browser-fixture.js'
import fs from 'node:fs/promises'

const PASSWORD = 'ReleaseTest123!'
const catalogs = Object.fromEntries(await Promise.all(['en', 'vi'].map(async locale =>
  [locale, JSON.parse(await fs.readFile(new URL(`../src/i18n/${locale}.json`, import.meta.url), 'utf8'))])))
const label = (locale, key) => key.split('.').reduce((value, part) => value[part], catalogs[locale])

for (const locale of ['en', 'vi']) test(`${locale}: authored questions, pinned locale and history`, async ({ page }) => {
  async function api(route, { method = 'GET', data, token } = {}) {
    token ??= await page.evaluate(() => localStorage.getItem('dbcas_token'))
    const response = await page.request.fetch(`http://127.0.0.1:8100${route}`, {
      method, data, headers: { 'Accept-Language': locale, ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    })
    expect(response.ok(), `${route}: ${await response.text()}`).toBeTruthy()
    return response.json()
  }
  await page.goto('/login')
  await page.evaluate(value => localStorage.setItem('dbcas_locale', value), locale)
  await page.reload()
  const email = `question-${locale}-${Date.now()}@test.dev`
  await api('/api/v1/auth/register', { method: 'POST', token: '', data: {
    name: 'Bilingual content learner', email, password: PASSWORD, password_confirm: PASSWORD,
  } })
  await page.getByLabel(label(locale, 'common.email'), { exact: true }).fill(email)
  await page.getByLabel(label(locale, 'auth.password'), { exact: true }).fill(PASSWORD)
  await page.getByRole('button', { name: label(locale, 'auth.signIn'), exact: true }).click()
  await expect(page).toHaveURL(/\/dashboard$/)
  await page.goto('/assessments')
  await page.getByRole('button', { name: label(locale, 'assessment.start'), exact: true }).click()
  await expect(page).toHaveURL(/\/exam\/\d+$/)
  const sid = Number(page.url().split('/').at(-1))
  const admin = await api('/api/v1/auth/login', { method: 'POST', token: '', data: {
    email: 'release-admin@test.dev', password: PASSWORD,
  } })
  const seen = new Set()
  const prompts = new Map()
  for (let i = 0; i < 13; i++) {
    const state = await api(`/api/v1/sessions/${sid}`)
    const q = state.current_question
    expect(q).toBeTruthy()
    expect(state.locale).toBe(locale)
    expect(q.content_locale).toBe(locale)
    const canonical = await api(`/api/v1/admin/questions/${q.question_id}`, { token: admin.access_token })
    const translation = canonical.translations.find(row => row.locale === 'vi')
    expect(q.prompt).toBe(locale === 'vi' ? translation.prompt : canonical.prompt)
    await page.reload()
    await expect(page.getByText(q.prompt, { exact: true })).toBeVisible()
    if (q.question_type === 'mcq') for (const option of q.options) {
      const expected = locale === 'vi' ? translation.option_texts[option.option_label]
        : canonical.options.find(row => row.option_label === option.option_label).option_text
      expect(option.option_text).toBe(expected)
      await expect(page.getByText(expected, { exact: true })).toBeVisible()
    }
    if (i === 0) {
      await page.getByRole('radio').first().locator('..').click()
      const selected = await page.getByRole('radio').first().inputValue()
      for (const uiLocale of [locale === 'vi' ? 'en' : 'vi', locale]) {
        await page.getByRole('button', { name: /^(Language|Ngôn ngữ)$/ }).click()
        await page.getByRole('menuitemradio', { name: uiLocale === 'vi' ? 'Tiếng Việt' : 'English', exact: true }).click()
        await expect(page.getByText(q.prompt, { exact: true })).toBeVisible()
        await expect(page.locator(`input[value="${selected}"]`)).toBeChecked()
        const after = await api(`/api/v1/sessions/${sid}`)
        expect(after.expires_at).toBe(state.expires_at)
        expect(after.current_question.question_id).toBe(q.question_id)
      }
    }
    seen.add(q.question_type)
    prompts.set(q.question_id, q.prompt)
    await api(`/api/v1/sessions/${sid}/submit`, { method: 'POST', data: {
      question_id: q.question_id,
      ...(q.question_type === 'mcq' ? { selected_option_id: canonical.options.find(row => row.is_correct).option_id }
        : q.question_type === 'sql' ? { sql_answer: canonical.reference_answer } : { essay_answer: canonical.reference_answer }),
    } })
  }
  expect([...seen].sort()).toEqual(['essay', 'mcq', 'sql'])
  await api(`/api/v1/sessions/${sid}/finish`, { method: 'POST' })
  // /finish only queues grading: official evidence stays gated (HTTP 409
  // results_pending) until every attempt is graded and the session publishes.
  // Poll the documented session state instead of assuming grading already ran.
  const policy = (await api(`/api/v1/sessions/${sid}`)).result_release_policy
  expect(policy, 'this spec covers immediate publication').toBe('IMMEDIATE')
  await expect.poll(async () => {
    const { release_status: status } = await api(`/api/v1/sessions/${sid}`)
    expect(status, 'grading must not fail').not.toBe('grading_failed')
    return status
  }, {
    message: `session ${sid} must publish results before evidence is readable`,
    timeout: 60_000,
    intervals: [250, 500, 1_000],
  }).toBe('published')
  const evidence = await api(`/api/v1/sessions/${sid}/evidence`)
  for (const item of evidence.items) {
    expect(item.prompt).toBe(prompts.get(item.question_id))
    expect(item.content_locale).toBe(locale)
    if (item.question_type === 'essay') {
      expect(item.grading_detail.explanation).toBe(locale === 'vi'
        ? 'Câu trả lời đáp ứng các tiêu chí đã nêu.' : 'The fixture answer meets the supplied criteria.')
      expect(item.grading_detail.rubric_level).toBe('Complete')
    }
  }
  await page.goto(`/history/${sid}`)
  for (const prompt of prompts.values()) await expect(page.getByText(prompt, { exact: true })).toBeVisible()
  const essay = evidence.items.find(item => item.question_type === 'essay')
  await expect(page.getByText(essay.grading_detail.explanation, { exact: true })).toBeVisible()
  await expect(page.getByText(essay.grading_detail.feedback, { exact: true })).toBeVisible()
  await expect(page.getByText(essay.grading_detail.rubric_level_label || essay.grading_detail.rubric_level, { exact: true })).toBeVisible()
})

for (const locale of ['en', 'vi']) test(`${locale}: retired legacy essay and active successor share the admin bank`, async ({ page }) => {
  await page.goto('/login')
  await page.evaluate(value => localStorage.setItem('dbcas_locale', value), locale)
  await page.reload()
  await page.getByLabel(label(locale, 'common.email'), { exact: true }).fill('release-admin@test.dev')
  await page.getByLabel(label(locale, 'auth.password'), { exact: true }).fill(PASSWORD)
  await page.getByRole('button', { name: label(locale, 'auth.signIn'), exact: true }).click()
  await expect(page).toHaveURL(/\/admin$/)
  await page.goto('/admin/questions')
  const search = page.getByLabel(label(locale, 'admin.questions.search'))
  await search.fill('Explain why indexes speed up reads but slow down writes.')
  await expect(page.getByText('Explain why indexes speed up reads but slow down writes.', { exact: true })).toBeVisible()
  await expect(page.getByText(label(locale, 'admin.questions.legacyRubric'))).toBeVisible()
  await search.fill('A PostgreSQL table is read frequently')
  await expect(page.getByText(/^A PostgreSQL table is read frequently/)).toBeVisible()
  await expect(page.getByText(label(locale, 'admin.questions.legacyRubric'))).toHaveCount(0)
})
