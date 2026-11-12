import { start as beginPractice, approveWithApi } from './practice-harness.js'
import { test, expect, request as apiRequest } from './browser-fixture.js'
import { successfulGetPathsFrom, unexpectedWebkitPageErrors } from './requestFailurePolicy.js'
import { readFile } from 'node:fs/promises'

const PASSWORD = 'ReleaseTest123!'

test('final acceptance: single, multiple and comprehensive skills, resume, retries and reserved bank editing', async ({
  page,
  browser,
  browserDiagnostics,
}) => {
  test.setTimeout(360_000)
  const api = await apiRequest.newContext({ baseURL: 'http://127.0.0.1:8100', timeout: 30_000 })
  const adminContext = await browser.newContext()
  browserDiagnostics.observe(adminContext)
  const adminPage = await adminContext.newPage()
  const errors = []
  page.on('pageerror', (error) => errors.push({ message: error.message, stack: error.stack }))
  adminPage.on('pageerror', (error) => errors.push({ message: error.message, stack: error.stack }))
  const unique = `acceptance-${Date.now()}`
  async function call(path, token, method = 'GET', data) {
    const response = await api.fetch(path, {
      method,
      data,
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    expect(response.ok(), `${method} ${path}: ${await response.text()}`).toBeTruthy()
    return response.json()
  }
  async function login(target, email) {
    await target.goto('/login')
    await target.evaluate(() => localStorage.setItem('dbcas_locale', 'en'))
    await target.reload()
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
    const bank = await call('/api/v1/admin/questions?status=validated', admin)
    expect(bank.length).toBeGreaterThan(0)
    // The archived browser fixture retains historical definitions. New
    // authoring must use the current reviewed content and its references.
    const reviewed = JSON.parse(
      await readFile(new URL('../../db/benchmark_pack.json', import.meta.url), 'utf8'),
    )
    const translations = JSON.parse(
      await readFile(new URL('../../db/question_translations_vi.json', import.meta.url), 'utf8'),
    ).questions
    const sources = {}
    for (const kind of ['mcq', 'sql', 'essay']) {
      const item = reviewed.questions.find(
        (q) => q.question_type === kind && q.status !== 'retired',
      )
      expect(item).toBeTruthy()
      sources[kind] = {
        ...item,
        options: item.options || [],
        datasets: item.datasets || [],
        rubrics: item.rubrics || [],
        translations: [{ ...translations[item.key], locale: 'vi', current: true }],
      }
    }
    const topics = []
    for (let i = 0; i < 3; i++) {
      topics.push(
        await call('/api/v1/admin/concepts', admin, 'POST', {
          concept_code: `${unique}-${i}`,
          concept_name: `${unique} skill ${i + 1}`,
          subject_area: 'SQL',
          description: 'Isolated acceptance fixture copied from the reviewed SQL bank.',
          keywords: ['SELECT'],
          learning_objectives: ['Interpret the supplied query and evidence'],
        }),
      )
    }
    const sourcePayload = (source, prompt, difficulty, conceptIds) => ({
      question_type: source.question_type,
      prompt,
      difficulty_level: difficulty,
      points: source.points,
      original_locale: source.original_locale || 'en',
      source_refs: source.source_refs,
      reference_answer: source.reference_answer,
      explanation: source.explanation,
      concept_ids: conceptIds,
      required_concept_ids: [],
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
          prompt: `${unique}: ${item.prompt}`,
          explanation: item.explanation,
          option_texts: item.option_texts,
          rubrics: item.rubrics,
        })),
    })
    // All mutations belong to this disposable browser fixture's own records.
    for (const [kind, count] of [
      ['mcq', 10],
      ['sql', 2],
      ['essay', 1],
    ]) {
      for (let i = 0; i < count; i++) {
        const source = sources[kind]
        const question = await call(
          '/api/v1/admin/questions',
          admin,
          'POST',
          sourcePayload(
            source,
            `${unique} ${kind} ${i}: ${source.prompt}`,
            kind === 'mcq' && i < 3 ? 1 : 3,
            [topics[i % topics.length].concept_id],
          ),
        )
        await call(`/api/v1/admin/questions/${question.question_id}`, admin, 'PATCH', {
          status: 'validated',
        })
      }
    }
    const email = `${unique}@test.dev`
    await call('/api/v1/auth/register', null, 'POST', {
      name: 'Isolated final acceptance learner',
      email,
      password: PASSWORD,
      password_confirm: PASSWORD,
    })
    const learner = await login(page, email)
    const sessions = []
    for (const count of [1, 2, 3]) {
      const started = await beginPractice(page, 'bank', count, {
        concept_ids: topics.slice(0, count).map((c) => c.concept_id),
        difficulties: ['EASY'],
      })
      const selection = started._startRequest
      const sid = started.session_id
      sessions.push(sid)
      expect((await call('/api/v1/practice/start', learner, 'POST', selection)).session_id).toBe(
        sid,
      )
      const seen = new Set()
      const answers = []
      for (let i = 0; i < count; i++) {
        const before = await call(`/api/v1/sessions/${sid}`, learner)
        const question = before.current_question
        expect(question.difficulty_level).toBe(1)
        expect(before.selected_concept_ids).toEqual(topics.slice(0, count).map((c) => c.concept_id))
        expect(seen.has(question.question_id)).toBe(false)
        seen.add(question.question_id)
        const original = await call(`/api/v1/admin/questions/${question.question_id}`, admin)
        expect(
          original.concepts
            .filter((c) => c.confirmed)
            .every((c) => selection.concept_ids.includes(c.concept_id)),
        ).toBe(true)
        const option = original.options.find((o) => o.is_correct)
        if (count === 3 && i === 2) {
          await page.locator(`input[value="${option.option_id}"]`).locator('..').click()
          await page.getByRole('button', { name: 'Save draft', exact: true }).click()
          await expect
            .poll(
              async () =>
                (
                  await call(
                    `/api/v1/sessions/${sid}/draft?question_id=${question.question_id}`,
                    learner,
                  )
                ).revision,
            )
            .toBeGreaterThan(0)
          await adminPage.goto('/admin/questions')
          await adminPage.getByLabel('Search prompt', { exact: true }).fill(original.prompt)
          const row = adminPage.locator('li').filter({ hasText: original.prompt })
          await row.getByRole('button', { name: 'Details', exact: true }).click()
          await row.getByRole('button', { name: 'Edit', exact: true }).click()
          await adminPage
            .getByLabel('Question prompt', { exact: true })
            .fill(`${unique} revised prompt`)
          const editing = adminPage.waitForResponse(
            (r) =>
              r.request().method() === 'PUT' &&
              r.url().endsWith(`/questions/${question.question_id}`),
          )
          await adminPage.getByRole('button', { name: 'Save changes', exact: true }).click()
          const editedResponse = await editing
          expect(editedResponse.status()).toBe(200)
          expect((await editedResponse.json()).question_id).not.toBe(question.question_id)
          const deletion = await api.delete(`/api/v1/admin/questions/${question.question_id}`, {
            headers: { Authorization: `Bearer ${admin}` },
          })
          expect(deletion.status()).toBe(409)
          await page.reload()
          await expect(page.getByText(original.prompt, { exact: true })).toBeVisible()
          await expect(page.locator(`input[value="${option.option_id}"]`)).toBeChecked()
          const resumed = await call(`/api/v1/sessions/${sid}`, learner)
          expect(resumed.answered_count).toBe(2)
          expect(resumed.expires_at).toBe(before.expires_at)
          expect(resumed.remaining_seconds).toBeLessThanOrEqual(before.remaining_seconds)
          expect(resumed.current_question.question_id).toBe(question.question_id)
          expect(
            (await call('/api/v1/practice/start', learner, 'POST', selection)).session_id,
          ).toBe(sid)
        }
        await page.locator(`input[value="${option.option_id}"]`).locator('..').click()
        const submitted = page.waitForResponse(
          (r) => r.request().method() === 'POST' && r.url().endsWith(`/sessions/${sid}/submit`),
        )
        await page.getByRole('button', { name: 'Submit answer & continue', exact: true }).click()
        expect((await submitted).status()).toBe(200)
        answers.push({ question_id: question.question_id, selected_option_id: option.option_id })
      }
      await page.getByRole('button', { name: 'Finish assessment', exact: true }).first().click()
      await page.getByRole('button', { name: 'Yes, finish', exact: true }).click()
      await expect(page).toHaveURL(new RegExp(`/evaluations/${sid}$`))
      await approveWithApi(page, sid)
      await page.reload()
      await expect(page.getByRole('heading', { name: 'Nhận xét từng câu' })).toBeVisible({
        timeout: 45000,
      })
      const evidence = await call(`/api/v1/sessions/${sid}/evidence`, learner)
      expect(evidence.items).toHaveLength(count)
      for (const answer of answers)
        expect(
          evidence.items.find((item) => item.question_id === answer.question_id).selected_option_id,
        ).toBe(answer.selected_option_id)
      expect((await call('/api/v1/practice/start', learner, 'POST', selection)).session_id).toBe(
        sid,
      )
    }
    const history = await call('/api/v1/sessions', learner)
    expect(history).toHaveLength(3)
    expect(new Set(sessions).size).toBe(3)
    for (const [index, sid] of sessions.entries()) {
      const record = history.find((s) => s.session_id === sid)
      expect(record.selected_concept_ids).toEqual(
        topics.slice(0, index + 1).map((c) => c.concept_id),
      )
      expect(record.difficulty).toBe('EASY')
      expect(Number(record.overall_result_pct)).toBe(100)
    }
    await page.goto('/competency')
    await expect(page.getByRole('heading', { name: 'Nhận xét', exact: true })).toBeVisible({
      timeout: 45000,
    })
    await expect(page.getByRole('heading', { name: 'Xu hướng qua các bài' })).toBeVisible()
    const cumulative = await call('/api/v1/sessions/competency/cumulative', learner)
    expect(cumulative.summary.finalized_assessments).toBe(3)
    expect(cumulative.concepts.length).toBeGreaterThan(0)
    await page.reload()
    await expect(page.getByRole('heading', { name: 'Nhận xét', exact: true })).toBeVisible()
    expect(await call('/api/v1/sessions/competency/cumulative', learner)).toEqual(cumulative)
    expect(
      unexpectedWebkitPageErrors(errors, {
        successfulGetPaths: successfulGetPathsFrom(browserDiagnostics.records.responses),
        routeVerified: true,
      }).map((error) => error.message),
    ).toEqual([])
  } finally {
    await adminContext.close()
    await api.dispose()
  }
})
