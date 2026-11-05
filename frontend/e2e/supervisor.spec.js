import {
  start as beginPractice,
  register as registerPractice,
  take,
  setFlow,
  api as practiceApi,
} from './practice-harness.js'
import { test, expect, request as apiRequest } from './browser-fixture.js'
import AxeBuilder from '@axe-core/playwright'
import { successfulGetPathsFrom, unexpectedWebkitPageErrors } from './requestFailurePolicy.js'
import { reviewedBankQuestion } from './reviewed-bank.js'

const API = 'http://127.0.0.1:8100'
const PASSWORD = 'ReleaseTest123!'

test('supervisor journeys A–E: classification, personalization, both release policies and cumulative evidence', async ({
  page,
  browser,
  browserDiagnostics,
}) => {
  test.setTimeout(360_000)
  const errors = []
  page.on('pageerror', (e) => errors.push({ message: e.message, stack: e.stack }))
  const api = await apiRequest.newContext({ baseURL: API, timeout: 30_000 })
  const adminContext = await browser.newContext()
  browserDiagnostics.observe(adminContext)
  const adminPage = await adminContext.newPage()
  adminPage.on('pageerror', (e) => errors.push({ message: e.message, stack: e.stack }))
  const unique = `supervisor-${Date.now()}`
  async function request(route, { token, method = 'GET', data } = {}) {
    const response = await api.fetch(route, {
      method,
      data,
      headers: { Connection: 'close', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    })
    expect(response.ok(), `${method} ${route}: ${await response.text()}`).toBeTruthy()
    return response.status() === 204 ? null : response.json()
  }
  async function login(target, email) {
    await target.addInitScript(() => {
      if (window.top === window && /^https?:$/.test(location.protocol))
        localStorage.setItem('dbcas_locale', 'en')
    })
    await target.goto('/login')
    await target.getByLabel('Email', { exact: true }).fill(email)
    await target.getByLabel('Password', { exact: true }).fill(PASSWORD)
    await target.getByRole('button', { name: 'Sign in', exact: true }).click()
    await expect(target).toHaveURL(email === 'release-admin@test.dev' ? /\/admin$/ : /\/dashboard$/)
    await expect(
      target.getByRole('heading', {
        name: email === 'release-admin@test.dev' ? 'Cohort Overview' : 'My competency',
        exact: true,
      }),
    ).toBeVisible()
    return target.evaluate(() => localStorage.getItem('dbcas_token'))
  }
  try {
    const admin = await login(adminPage, 'release-admin@test.dev')
    const questions = await request('/api/v1/admin/questions?status=validated', { token: admin })
    const sources = {}
    for (const kind of ['mcq', 'sql', 'essay']) {
      sources[kind] = reviewedBankQuestion(
        await request(
          `/api/v1/admin/questions/${questions.find((q) => q.question_type === kind).question_id}`,
          { token: admin },
        ),
      )
    }
    const conceptIds = [
      ...new Set(
        Object.values(sources).flatMap((q) =>
          q.concepts.filter((c) => c.confirmed).map((c) => c.concept_id),
        ),
      ),
    ]
    await test.step('Journey E: classify a bank item and configure shared release rules in the administrator UI', async () => {
      let first
      for (const [kind, count] of [
        ['mcq', 10],
        ['sql', 2],
        ['essay', 1],
        ['opening', 3],
      ]) {
        const source = sources[kind === 'opening' ? 'mcq' : kind]
        for (let i = 0; i < count; i++) {
          const result = await request('/api/v1/admin/questions', {
            token: admin,
            method: 'POST',
            data: {
              question_type: source.question_type,
              prompt: `${unique} ${kind} ${i}: ${source.prompt}`,
              reference_answer: source.reference_answer,
              original_locale: source.original_locale || 'en',
              source_refs: source.source_refs,
              points: source.points,
              explanation: source.explanation,
              difficulty_level: kind === 'opening' || (kind === 'mcq' && i === 0) ? 1 : 3,
              concept_ids: source.concepts.filter((c) => c.confirmed).map((c) => c.concept_id),
              required_concept_ids: source.concepts
                .filter((c) => c.confirmed && c.is_required)
                .map((c) => c.concept_id),
              options: source.options.map(({ option_label, option_text, is_correct }) => ({
                option_label,
                option_text,
                is_correct,
              })),
              datasets: source.datasets.map(
                ({ dataset_name, setup_sql, expected_result, is_edge_case }) => ({
                  dataset_name,
                  setup_sql,
                  expected_result,
                  is_edge_case,
                }),
              ),
              rubrics: source.rubrics.map(({ level_name, min_score, max_score, criteria }) => ({
                level_name,
                min_score,
                max_score,
                criteria,
              })),
              translations: source.translations
                .filter((item) => item.current)
                .map((item) => ({
                  locale: item.locale,
                  prompt: `${unique} ${kind} ${i}: ${item.prompt}`,
                  explanation: item.explanation,
                  option_texts: item.option_texts,
                  rubrics: item.rubrics,
                })),
            },
          })
          if (kind === 'mcq' && i === 0) first = result
          else
            await request(`/api/v1/admin/questions/${result.question_id}`, {
              token: admin,
              method: 'PATCH',
              data: { status: 'validated' },
            })
        }
      }
      await adminPage.goto('/admin/questions')
      await adminPage.getByLabel('Search prompt', { exact: true }).fill(first.prompt)
      const row = adminPage.locator('li').filter({ hasText: first.prompt })
      await row.getByRole('button', { name: 'Details', exact: true }).click()
      await row.getByRole('button', { name: 'Edit', exact: true }).click()
      await adminPage.getByLabel('Difficulty', { exact: true }).selectOption('3')
      for (const concept of first.concepts.filter((c) => c.confirmed)) {
        const name = `${concept.concept_name} (${concept.concept_code})`
        await adminPage.getByRole('checkbox', { name, exact: true }).check()
      }
      const saved = adminPage.waitForResponse(
        (r) =>
          r.request().method() === 'PUT' &&
          r.url().endsWith(`/admin/questions/${first.question_id}`),
      )
      await adminPage.getByRole('button', { name: 'Save changes', exact: true }).click()
      const savedResponse = await saved
      expect(savedResponse.status()).toBe(200)
      const classified = await savedResponse.json()
      expect(classified.difficulty_level).toBe(3)
      expect(
        classified.concepts
          .filter((c) => c.confirmed)
          .map((c) => c.concept_id)
          .sort((a, b) => a - b),
      ).toEqual(
        first.concepts
          .filter((c) => c.confirmed)
          .map((c) => c.concept_id)
          .sort((a, b) => a - b),
      )
      await row.getByRole('button', { name: 'Actions', exact: true }).click()
      await adminPage.getByRole('menuitem', { name: 'Validate', exact: true }).click()
      await expect(row).toContainText('Validated')
      await expect(adminPage.locator('.app-sidebar nav').getByRole('link')).toHaveCount(5)
    })
    await registerPractice(page, 'supervisor')
    for (const policy of ['IMMEDIATE', 'HUMAN_VERIFIED']) {
      await test.step(`Learner-selected practice and publication ${policy}`, async () => {
        await setFlow(adminPage, policy)
        const state = await beginPractice(page, 'bank', 3, { concept_ids: conceptIds })
        const { sid, kinds } = await take(page, state, { refresh: true, sandbox: true })
        expect(new Set(kinds)).toEqual(new Set(['mcq', 'sql', 'essay']))
        if (policy === 'HUMAN_VERIFIED') {
          await expect(
            page.getByRole('heading', { name: 'Đang chờ giảng viên duyệt', exact: true }),
          ).toBeVisible()
          expect(
            (await practiceApi(page, '/sessions/competency/cumulative')).summary
              .finalized_assessments,
          ).toBe(1)
          await adminPage.goto(`/admin/grading/${sid}`)
          await expect(adminPage.getByRole('button', { name: 'Duyệt', exact: true })).toBeEnabled({
            timeout: 45000,
          })
          await adminPage.getByRole('button', { name: 'Duyệt', exact: true }).click()
          await expect(page.getByText(/Đã được giảng viên duyệt/)).toBeVisible({ timeout: 45000 })
        }
        await expect(page.getByRole('heading', { name: 'Nhận xét từng câu' })).toBeVisible({
          timeout: 45000,
        })
        const evidence = await practiceApi(page, `/sessions/${sid}/evidence`)
        expect(evidence.items).toHaveLength(3)
        expect(evidence.items.every((item) => item.score !== null)).toBe(true)
      })
    }
    await page.goto('/competency')
    await expect(page.getByRole('heading', { name: 'Xu hướng qua các bài' })).toBeVisible({
      timeout: 45000,
    })
    const cumulative = await practiceApi(page, '/sessions/competency/cumulative')
    expect(cumulative.summary.finalized_assessments).toBe(2)
    expect(cumulative.concepts.length).toBeGreaterThan(0)
    expect(
      (await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze()).violations,
    ).toEqual([])
    expect(
      unexpectedWebkitPageErrors(errors, {
        successfulGetPaths: successfulGetPathsFrom(browserDiagnostics.records.responses),
        routeVerified: true,
      }).map((e) => e.message),
    ).toEqual([])
  } finally {
    await setFlow(adminPage, 'IMMEDIATE')
    await adminContext.close()
    await api.dispose()
  }
})

test('single-topic practice works with the existing approved bank at a narrow viewport', async ({
  page,
}) => {
  const api = await apiRequest.newContext({ baseURL: API, timeout: 30_000 })
  async function call(path, token, data) {
    const response = await api.fetch(path, {
      method: data ? 'POST' : 'GET',
      data,
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    expect(response.ok(), `${path}: ${await response.text()}`).toBeTruthy()
    return response.json()
  }
  try {
    const { access_token: admin } = await call('/api/v1/auth/login', null, {
      email: 'release-admin@test.dev',
      password: PASSWORD,
    })
    const bank = await call('/api/v1/admin/questions?status=validated', admin)
    const email = `single-topic-${Date.now()}@test.dev`
    await call('/api/v1/auth/register', null, {
      name: 'Single topic learner',
      email,
      password: PASSWORD,
      password_confirm: PASSWORD,
    })
    await page.goto('/login')
    await page.evaluate(() => {
      if (window.top === window && /^https?:$/.test(location.protocol))
        localStorage.setItem('dbcas_locale', 'en')
    })
    await page.reload()
    await page.getByLabel('Email', { exact: true }).fill(email)
    await page.getByLabel('Password', { exact: true }).fill(PASSWORD)
    await page.getByRole('button', { name: 'Sign in', exact: true }).click()
    await expect(page).toHaveURL(/\/dashboard$/)
    const learner = await page.evaluate(() => localStorage.getItem('dbcas_token'))
    const question = bank.find(
      (q) =>
        q.question_type === 'mcq' &&
        q.difficulty_level <= 2 &&
        q.concepts.filter((c) => c.confirmed).length === 1,
    )
    expect(question).toBeTruthy()
    const conceptId = question.concepts.find((c) => c.confirmed).concept_id
    await page.setViewportSize({ width: 390, height: 900 })
    const state = await beginPractice(page, 'bank', 1, {
      concept_ids: [conceptId],
      difficulties: ['EASY'],
    })
    expect(
      (await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze()).violations,
    ).toEqual([])
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(391)
    const sid = state.session_id
    expect(state.max_questions).toBe(1)
    expect(state.selected_concept_ids).toEqual([conceptId])
    expect(state.current_question.difficulty_level).toBeLessThanOrEqual(2)
    const key = await call(`/api/v1/admin/questions/${state.current_question.question_id}`, admin)
    await page
      .locator(`input[value="${key.options.find((o) => o.is_correct).option_id}"]`)
      .locator('..')
      .click()
    await page.getByRole('button', { name: 'Submit answer & continue', exact: true }).click()
    await expect(page.getByText('All questions served', { exact: true })).toBeVisible()
    await page.getByRole('button', { name: 'Finish assessment', exact: true }).first().click()
    await page.getByRole('button', { name: 'Yes, finish', exact: true }).click()
    await expect(page).toHaveURL(new RegExp(`/evaluations/${sid}$`))
    await expect(page.getByRole('heading', { name: 'Nhận xét từng câu' })).toBeVisible({
      timeout: 45000,
    })
    await page.goto(`/history/${sid}`)
    await expect(
      page.getByRole('heading', { name: 'Assessment evidence', exact: true }),
    ).toBeVisible()
    expect((await call(`/api/v1/sessions/${sid}/evidence`, learner)).items).toHaveLength(1)
  } finally {
    await api.dispose()
  }
})
