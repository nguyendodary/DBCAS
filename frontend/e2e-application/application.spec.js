import { test, expect } from '../e2e/browser-fixture.js'
import fs from 'node:fs/promises'
import path from 'node:path'
import { reviewedBankQuestion } from '../e2e/reviewed-bank.js'
import {
  start as beginPractice,
  register as registerPractice,
  login as loginPractice,
  take,
  setFlow,
  api as practiceApi,
  vi,
} from '../e2e/practice-harness.js'

const API = 'http://127.0.0.1:8100/api/v1'
const PASSWORD = 'ReleaseTest123!'
const artifacts = path.resolve(process.env.DBCAS_E2E_OUTPUT ?? '../../_review/e2e-application')

async function call(page, route, token, method = 'GET', data) {
  const response = await page.request.fetch(`${API}${route}`, {
    method,
    data,
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  expect(response.ok(), `${method} ${route}: ${response.status()}`).toBeTruthy()
  return response.json()
}
async function login(page, email) {
  await page.addInitScript(() => {
    if (window.top === window && /^https?:$/.test(location.protocol))
      localStorage.setItem('dbcas_locale', 'en')
  })
  if (!page.url().endsWith('/login')) await page.goto('/login')
  await expect(page.getByRole('heading', { name: 'Sign in to DBCAS', exact: true })).toBeVisible()
  await page.getByLabel('Email', { exact: true }).fill(email)
  await page.getByLabel('Password', { exact: true }).fill(PASSWORD)
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page).toHaveURL(email === 'release-admin@test.dev' ? /\/admin$/ : /\/dashboard$/)
  await expect(
    page.getByRole('heading', {
      name: email === 'release-admin@test.dev' ? 'Cohort Overview' : 'My competency',
      exact: true,
    }),
  ).toBeVisible()
  return page.evaluate(() => localStorage.getItem('dbcas_token'))
}
async function register(page) {
  const email = `real-app-${Date.now()}-${Math.random().toString(16).slice(2, 8)}@test.dev`
  await page.goto('/register')
  for (const [name, value] of [
    ['Full name', 'Isolated application learner'],
    ['Email', email],
    ['Password', PASSWORD],
    ['Confirm password', PASSWORD],
  ])
    await page.getByLabel(name, { exact: true }).fill(value)
  await page.getByRole('button', { name: 'Register', exact: true }).click()
  await expect(page).toHaveURL(/\/login$/)
  return login(page, email)
}

test('real role manager promotes and revokes an account with immediate token enforcement', async ({
  browser,
  browserDiagnostics,
}) => {
  test.setTimeout(120_000)
  const adminContext = await browser.newContext({
    baseURL: 'http://127.0.0.1:5174',
    locale: 'en-US',
  })
  browserDiagnostics.observe(adminContext)
  const adminPage = await adminContext.newPage()
  const targetContext = await browser.newContext({
    baseURL: 'http://127.0.0.1:5174',
    locale: 'en-US',
  })
  browserDiagnostics.observe(targetContext)
  const targetPage = await targetContext.newPage()
  try {
    const adminToken = await login(adminPage, 'release-admin@test.dev')
    const email = `role-target-${Date.now()}@test.dev`
    const created = await adminPage.request.post(`${API}/auth/register`, {
      data: {
        name: 'Role management E2E learner',
        email,
        password: PASSWORD,
        password_confirm: PASSWORD,
      },
    })
    expect(created.status()).toBe(201)
    const targetToken = await login(targetPage, email)

    await adminPage.goto('/admin/accounts')
    const row = adminPage.getByRole('row').filter({ hasText: email })
    await expect(row).toBeVisible()
    await row.getByRole('button', { name: 'Grant Administrator Access', exact: true }).click()
    const grantDialog = adminPage.getByRole('dialog', {
      name: 'Grant Administrator access to this user?',
    })
    await expect(grantDialog).toContainText('They will be able to access administrative features.')
    await grantDialog
      .getByRole('button', { name: 'Grant Administrator Access', exact: true })
      .click()
    await expect(row).toContainText('Administrator')
    await expect(adminPage.getByRole('status')).toContainText(
      `Administrator access granted to ${email}`,
    )

    const adminAccess = await targetPage.request.get(`${API}/admin/accounts`, {
      headers: { Authorization: `Bearer ${targetToken}` },
    })
    expect(adminAccess.status()).toBe(200)
    await targetPage.reload()
    // Promotion replaces the Learner role, so /dashboard redirects to the admin portal.
    await expect(targetPage).toHaveURL(/\/admin$/)
    await expect(
      targetPage.getByRole('heading', { name: 'Cohort Overview', exact: true }),
    ).toBeVisible()
    await targetPage.goto('/admin')
    await expect(targetPage).toHaveURL(/\/admin$/)
    await expect(targetPage.getByRole('heading', { level: 1 })).toBeVisible()

    await row.getByRole('button', { name: 'Revoke Administrator Access', exact: true }).click()
    const revokeDialog = adminPage.getByRole('dialog', { name: 'Revoke Administrator access?' })
    await expect(revokeDialog).toContainText(
      'This user will lose access to administrative features.',
    )
    await revokeDialog
      .getByRole('button', { name: 'Revoke Administrator Access', exact: true })
      .click()
    await expect(row).toContainText('Learner')
    const revokedAccess = await targetPage.request.get(`${API}/admin/accounts`, {
      headers: { Authorization: `Bearer ${targetToken}` },
    })
    expect(revokedAccess.status()).toBe(403)
    await targetPage.reload()
    await expect(targetPage).toHaveURL(/\/dashboard$/)
    await expect(
      targetPage.getByRole('heading', { name: 'My competency', exact: true }),
    ).toBeVisible()
    await targetPage.goto('/admin')
    await expect(targetPage).toHaveURL(/\/dashboard$/)
    const audit = await adminPage.request.get(`${API}/admin/accounts/role-audit`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    })
    expect(audit.status()).toBe(200)
    const changes = (await audit.json()).filter((event) => event.target_account_id > 0)
    expect(changes).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          action_type: 'ROLE_GRANTED',
          previous_role: 'Learner',
          new_role: 'Administrator',
        }),
        expect.objectContaining({
          action_type: 'ROLE_REVOKED',
          previous_role: 'Administrator',
          new_role: 'Learner',
        }),
      ]),
    )
  } finally {
    await targetContext.close()
    await adminContext.close()
  }
})
async function setTheme(page, theme) {
  await page.goto('/settings')
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  if ((await page.locator('html').getAttribute('data-theme')) !== theme) {
    await page
      .locator('#main-content')
      .getByRole('button', { name: `Switch to ${theme} theme`, exact: true })
      .click()
  }
  await expect(page.locator('html')).toHaveAttribute('data-theme', theme)
  await expect(page.locator('html')).not.toHaveAttribute('data-theme-transitioning', 'true')
}
async function fixture(adminPage, token) {
  const bank = await call(adminPage, '/admin/questions?status=validated', token)
  const sources = {}
  for (const kind of ['mcq', 'sql', 'essay'])
    sources[kind] = reviewedBankQuestion(
      await call(
        adminPage,
        `/admin/questions/${bank.find((q) => q.question_type === kind).question_id}`,
        token,
      ),
    )
  const label = `E2E-${Date.now()}`
  await adminPage.goto('/admin/curriculum')
  await adminPage.getByText('Reference code (optional)', { exact: true }).click()
  await adminPage.getByLabel('Concept code', { exact: true }).fill(label)
  await adminPage
    .getByLabel('Concept name', { exact: true })
    .fill(`${label} approved database examples`)
  await adminPage.getByLabel('Subject area', { exact: true }).fill('Database competency')
  // The concept form has one technique select; all other controls are text inputs.
  await adminPage
    .locator('form')
    .filter({ has: adminPage.getByLabel('Concept code', { exact: true }) })
    .getByRole('combobox')
    .selectOption('select')
  await adminPage
    .getByLabel('Concept keywords (comma separated)', { exact: true })
    .fill('projection, approved bank')
  await adminPage
    .getByLabel('Learning objectives (one per line)', { exact: true })
    .fill('Execute read-only SQL\nExplain the supplied database concepts')
  const creating = adminPage.waitForResponse(
    (r) => r.request().method() === 'POST' && r.url().endsWith('/admin/concepts'),
  )
  await adminPage.getByRole('button', { name: 'Add concept', exact: true }).click()
  const created = await creating
  expect(created.status()).toBe(201)
  const topic = await created.json()
  expect(topic.keywords).toEqual(['projection', 'approved bank'])
  expect(topic.learning_objectives).toHaveLength(2)
  // Keep each band usable and provide four SQL/essay cases for a balanced
  // thirteen-question learner-defined practice at Medium difficulty.
  for (const [kind, levels] of [
    ['mcq', [...Array(10).fill(1), ...Array(10).fill(3), 5]],
    ['sql', [3, 3, 3, 3, 1, 5]],
    ['essay', [3, 3, 3, 3, 1, 5]],
  ]) {
    for (const [i, difficulty] of levels.entries()) {
      const source = sources[kind]
      const q = await call(adminPage, '/admin/questions', token, 'POST', {
        question_type: kind,
        prompt: `${label} ${kind} ${i}: ${source.prompt}`,
        points: source.points,
        difficulty_level: difficulty,
        reference_answer: source.reference_answer,
        source_refs: source.source_refs,
        original_locale: source.original_locale || 'en',
        explanation: source.explanation,
        concept_ids: [topic.concept_id],
        required_concept_ids: kind === 'sql' ? [topic.concept_id] : [],
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
            prompt: `${label}: ${item.prompt}`,
            explanation: item.explanation,
            option_texts: item.option_texts,
            rubrics: item.rubrics,
          })),
      })
      await call(adminPage, `/admin/questions/${q.question_id}`, token, 'PATCH', {
        status: 'validated',
      })
    }
  }
  return { topic }
}

test('real entrypoint: authentication, refresh, logout and role boundaries', async ({ page }) => {
  const schema = await (await page.request.get('http://127.0.0.1:8100/openapi.json')).json()
  expect(Object.keys(schema.paths).some((p) => p.startsWith('/__test'))).toBe(false)
  expect((await page.request.get('http://127.0.0.1:8100/readiness')).status()).toBe(200)
  await page.goto('/admin/grading')
  await expect(page).toHaveURL(/\/login$/)
  await page.getByLabel('Email', { exact: true }).fill(`invalid-${Date.now()}@test.dev`)
  await page.getByLabel('Password', { exact: true }).fill(PASSWORD)
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page.getByRole('alert')).toBeVisible()
  const learner = await register(page)
  await page.reload()
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  await expect(page).toHaveURL(/\/dashboard$/)
  await page.goto('/admin/grading')
  await expect(page).toHaveURL(/\/dashboard$/)
  expect(
    (
      await page.request.get(`${API}/admin/grading-reviews`, {
        headers: { Authorization: `Bearer ${learner}` },
      })
    ).status(),
  ).toBe(403)
  await page.getByRole('banner').getByRole('button', { name: 'Log out', exact: true }).click()
  await page.goto('/history')
  await expect(page).toHaveURL(/\/login$/)
})

for (const [width, height] of [
  [1440, 900],
  [1366, 768],
  [768, 1024],
  [390, 844],
]) {
  test(`real entrypoint ${width}x${height}: learner/admin navigation in both themes`, async ({
    page,
    browser,
    browserDiagnostics,
  }) => {
    test.setTimeout(180_000)
    await page.setViewportSize({ width, height })
    await register(page)
    const adminContext = await browser.newContext({
      baseURL: 'http://127.0.0.1:5174',
      locale: 'en-US',
      viewport: { width, height },
    })
    browserDiagnostics.observe(adminContext)
    const adminPage = await adminContext.newPage()
    try {
      await login(adminPage, 'release-admin@test.dev')
      for (const [actor, routes] of [
        [page, ['/dashboard', '/assessments', '/history', '/competency', '/settings']],
        [
          adminPage,
          [
            '/admin',
            '/admin/curriculum',
            '/admin/questions',
            '/admin/system',
            '/admin/grading',
            '/admin/accounts',
            '/settings',
          ],
        ],
      ]) {
        for (const theme of ['light', 'dark']) {
          await setTheme(actor, theme)
          for (const route of routes) {
            await actor.goto(route)
            await expect(actor.getByRole('heading', { level: 1 })).toBeVisible()
            await expect(actor.locator('.skeleton')).toHaveCount(0)
            await expect(actor.getByRole('alert')).toHaveCount(0)
            expect(
              await actor.evaluate(() => document.documentElement.scrollWidth),
            ).toBeLessThanOrEqual(width + 1)
            if (actor === adminPage && width >= 768) {
              const sidebar = await actor.locator('.app-sidebar').boundingBox()
              const footer = await actor.getByRole('contentinfo').boundingBox()
              expect(
                footer.x,
                'Administrator footer must clear the fixed sidebar',
              ).toBeGreaterThanOrEqual(sidebar.x + sidebar.width)
            }
            await fs.mkdir(path.join(artifacts, 'screenshots'), { recursive: true })
            await actor.screenshot({
              path: path.join(
                artifacts,
                'screenshots',
                `${route.replaceAll('/', '-')}-${theme}-${width}x${height}.png`,
              ),
              fullPage: true,
            })
          }
          await actor.reload()
          await expect(actor.locator('html')).toHaveAttribute('data-theme', theme)
          // Theme initializes before authentication: await the actual page
          // before the next navigation, rather than cancelling bootstrap XHRs.
          await expect(actor.getByRole('heading', { level: 1 })).toBeVisible()
          await expect(actor.locator('.skeleton')).toHaveCount(0)
        }
      }
      expect(browserDiagnostics.records.pageErrors).toEqual([])
    } finally {
      await adminContext.close()
    }
  })
}

test('real entrypoint: strict difficulty, drafts, unavailable AI, human correction and cumulative evidence', async ({
  page,
  browser,
  browserDiagnostics,
}, info) => {
  test.setTimeout(240_000)
  const schema = await (await page.request.get('http://127.0.0.1:8100/openapi.json')).json()
  expect(Object.keys(schema.paths).some((p) => p.startsWith('/__test'))).toBe(false)
  const context = await browser.newContext({ baseURL: 'http://127.0.0.1:5174', locale: 'en-US' })
  browserDiagnostics.observe(context)
  const adminPage = await context.newPage()
  const allEvidence = []
  try {
    const admin = await login(adminPage, 'release-admin@test.dev')
    const { topic } = await fixture(adminPage, admin)
    await loginPractice(adminPage, 'release-admin@test.dev', PASSWORD)
    await setFlow(adminPage, 'IMMEDIATE')
    await registerPractice(page, 'real-entrypoint')
    expect((await practiceApi(page, '/evaluations/overall')).attempt_count).toBe(0)
    let count = 0
    for (const [difficulty, level] of [
      ['EASY', 1],
      ['MEDIUM', 3],
      ['HARD', 5],
    ]) {
      const state = await beginPractice(page, 'bank', 1, {
        concept_ids: [topic.concept_id],
        difficulties: [difficulty],
      })
      expect(state.max_questions).toBe(1)
      expect(state.current_question.difficulty_level).toBe(level)
      const key = await call(
        adminPage,
        `/admin/questions/${state.current_question.question_id}`,
        admin,
      )
      expect(key.concepts.filter((c) => c.confirmed).map((c) => c.concept_id)).toEqual([
        topic.concept_id,
      ])
      await page
        .locator(`input[value="${key.options.find((o) => o.is_correct).option_id}"]`)
        .locator('..')
        .click()
      const submitted = page.waitForResponse(
        (r) =>
          r.request().method() === 'POST' &&
          r.url().endsWith(`/sessions/${state.session_id}/submit`),
      )
      await page.getByRole('button', { name: vi.exam.submit, exact: true }).click()
      const response = await submitted
      expect(response.status()).toBe(200)
      const body = await response.json()
      expect(body.answer.score).toBeNull()
      expect(body.answer.is_correct).toBeNull()
      await take(page, body.state)
      await expect(page.getByRole('heading', { name: 'Nhận xét từng câu' })).toBeVisible({
        timeout: 45000,
      })
      const evidence = await practiceApi(page, `/sessions/${state.session_id}/evidence`)
      expect(evidence.items).toHaveLength(1)
      expect(Number(evidence.items[0].score)).toBe(Number(key.points))
      allEvidence.push(...evidence.items)
      expect(
        (await practiceApi(page, '/practice/start', 'POST', state._startRequest)).session_id,
      ).toBe(state.session_id)
      expect((await practiceApi(page, '/sessions/statistics')).published_formal_sessions).toBe(
        ++count,
      )
      expect(
        (await practiceApi(page, '/sessions/competency/cumulative')).summary.finalized_assessments,
      ).toBe(count)
    }
    await setFlow(adminPage, 'HUMAN_VERIFIED')
    const state = await beginPractice(page, 'ai', 13, {
      concept_ids: [topic.concept_id],
      difficulties: ['MEDIUM'],
    })
    expect(state.max_questions).toBe(13)
    expect(state.generation_fallback).toBe(true)
    expect(state.selection_notice || '').not.toContain('mở rộng')
    const { sid, kinds } = await take(page, state, {
      refresh: true,
      sandbox: true,
      answerFor: async (q) => call(adminPage, `/admin/questions/${q.question_id}`, admin),
    })
    expect(kinds).toHaveLength(13)
    expect(
      kinds.reduce((counts, kind) => ({ ...counts, [kind]: (counts[kind] || 0) + 1 }), {}),
    ).toEqual({ mcq: 5, sql: 4, essay: 4 })
    await expect(
      page.getByRole('heading', { name: 'Đang chờ giảng viên duyệt', exact: true }),
    ).toBeVisible()
    await page.reload()
    await expect(
      page.getByRole('heading', { name: 'Đang chờ giảng viên duyệt', exact: true }),
    ).toBeVisible()
    const token = await page.evaluate(() => localStorage.getItem('dbcas_token'))
    for (const endpoint of ['evidence', 'competency', 'gaps', 'guidance']) {
      expect(
        (
          await page.request.get(`${API}/sessions/${sid}/${endpoint}`, {
            headers: { Authorization: `Bearer ${token}` },
          })
        ).status(),
      ).toBe(409)
    }
    expect((await practiceApi(page, '/sessions/statistics')).published_formal_sessions).toBe(3)
    const waiting = await practiceApi(page, `/evaluations/attempts/${sid}`)
    expect(waiting.status).toBe('awaiting_approval')
    expect(waiting).not.toHaveProperty('score')
    await adminPage.goto(`/admin/grading/${sid}`)
    await expect(adminPage.getByRole('button', { name: 'Duyệt', exact: true })).toBeEnabled({
      timeout: 45000,
    })
    let detail = await call(adminPage, `/admin/grading-reviews/${sid}`, admin)
    expect(detail.evaluation.evaluator_fallback).toBe(true)
    for (const item of detail.items.filter((q) => q.question_type === 'sql'))
      expect(Number(item.automated_score)).toBe(Number(item.points))
    const editable = detail.items.find((item) => item.question_type !== 'mcq')
    const missingReason = await adminPage.request.post(
      `${API}/admin/grading-reviews/${sid}/attempts/${editable.attempt_id}`,
      {
        headers: { Authorization: `Bearer ${admin}` },
        data: { score: '0.25', revision: editable.revision, comments: null },
      },
    )
    expect(missingReason.status()).toBe(422)
    await adminPage.getByRole('button', { name: 'Chạy SQL kiểm tra', exact: true }).first().click()
    await expect(adminPage.getByText(/Thành công · 1 dòng/).first()).toBeVisible()
    await adminPage.getByLabel('SQL kiểm tra (chỉ SELECT)').first().fill('DELETE FROM students')
    await adminPage.getByRole('button', { name: 'Chạy SQL kiểm tra', exact: true }).first().click()
    await expect(adminPage.getByText(/Không chạy được truy vấn/).first()).toBeVisible()
    const form = adminPage.locator('form').first()
    await form.getByRole('spinbutton').fill('0.25')
    await expect(form.getByLabel('Lý do điều chỉnh')).toHaveAttribute('required', '')
    await form
      .getByLabel('Lý do điều chỉnh')
      .fill('Kiểm chứng SQL và rubric bằng dịch vụ thật, không có khóa AI.')
    await form.getByRole('button', { name: 'Lưu điểm điều chỉnh' }).click()
    await expect(adminPage.getByRole('heading', { name: 'Lịch sử điều chỉnh điểm' })).toBeVisible()
    detail = await call(adminPage, `/admin/grading-reviews/${sid}`, admin)
    for (const item of detail.items.filter((q) => q.question_type === 'essay')) {
      await call(
        adminPage,
        `/admin/grading-reviews/${sid}/attempts/${item.attempt_id}`,
        admin,
        'POST',
        {
          score: String(Number(item.points) / 2),
          comments: 'Manual rubric verification without an AI key.',
          revision: item.revision,
        },
      )
    }
    detail = await call(adminPage, `/admin/grading-reviews/${sid}`, admin)
    const stale = await adminPage.request.post(`${API}/admin/grading-reviews/${sid}/publish`, {
      headers: { Authorization: `Bearer ${admin}` },
      data: { revision: detail.revision - 1 },
    })
    expect(stale.status()).toBe(409)
    await adminPage.reload()
    await expect(adminPage.getByRole('button', { name: 'Duyệt', exact: true })).toBeEnabled({
      timeout: 45000,
    })
    await adminPage.getByRole('button', { name: 'Duyệt', exact: true }).click()
    await expect(page.getByText(/Đã được giảng viên duyệt/)).toBeVisible({ timeout: 45000 })
    const final = await practiceApi(page, `/sessions/${sid}/evidence`)
    expect(final.items).toHaveLength(13)
    expect(new Set(final.items.map((q) => q.question_id)).size).toBe(13)
    for (const item of final.items) {
      expect(item.difficulty_level).toBe(3)
      expect(item.concepts.map((c) => c.concept_id)).toEqual([topic.concept_id])
      if (item.question_type === 'essay') expect(Number(item.score)).toBe(Number(item.points) / 2)
    }
    allEvidence.push(...final.items)
    expect((await practiceApi(page, '/sessions/statistics')).published_formal_sessions).toBe(4)
    const cumulative = await practiceApi(page, '/sessions/competency/cumulative')
    expect(cumulative.summary.finalized_assessments).toBe(4)
    const concept = cumulative.concepts.find((c) => c.concept_id === topic.concept_id)
    expect(concept.contributing_sessions).toEqual(
      expect.arrayContaining([
        ...new Set(allEvidence.filter((q) => q.session_id).map((q) => q.session_id)),
        sid,
      ]),
    )
    const earned = allEvidence.reduce((sum, q) => sum + Math.round(Number(q.score) * 100), 0)
    const possible = allEvidence.reduce((sum, q) => sum + Math.round(Number(q.points) * 100), 0)
    expect(Number(concept.competency_pct)).toBe(Math.round((earned * 10000) / possible) / 100)
    await page.goto('/competency')
    await expect(page.getByRole('heading', { name: 'Xu hướng qua các bài' })).toBeVisible({
      timeout: 45000,
    })
    const overall = await practiceApi(page, '/evaluations/overall')
    expect(overall.status).toBe('ready')
    expect(overall.score.percentage).toBe(Math.round((earned * 10000) / possible) / 100)
    await page.screenshot({
      path: info.outputPath('application-current-cumulative.png'),
      fullPage: true,
    })
    await page.reload()
    await expect(page.getByRole('heading', { name: 'Xu hướng qua các bài' })).toBeVisible({
      timeout: 45000,
    })
    expect((await practiceApi(page, '/evaluations/overall')).input_hash).toBe(overall.input_hash)
    expect(browserDiagnostics.records.pageErrors).toEqual([])
  } finally {
    await setFlow(adminPage, 'IMMEDIATE')
    await context.close()
  }
})

test('real entrypoint: a start request used to resume remains idempotent after completion', async ({
  page,
}) => {
  await registerPractice(page, 'real-idempotency')
  const options = await practiceApi(page, '/practice/options')
  const state = await beginPractice(page, 'bank', 1, {
    concept_ids: [options.concepts[0].concept_id],
    difficulties: ['EASY'],
  })
  const resumed = await practiceApi(page, '/practice/start', 'POST', state._startRequest)
  expect(resumed.session_id).toBe(state.session_id)
  expect(resumed.expires_at).toBe(state.expires_at)
  const token = await page.evaluate(() => localStorage.getItem('dbcas_token'))
  const conflicting = await page.request.post(`${API}/practice/start`, {
    headers: { Authorization: `Bearer ${token}` },
    data: { ...state._startRequest, request_id: crypto.randomUUID() },
  })
  expect(conflicting.status()).toBe(409)
  expect((await conflicting.json()).error.code).toBe('active_practice')
  await take(page, state, { refresh: true })
  await expect(page.getByRole('heading', { name: 'Nhận xét từng câu' })).toBeVisible({
    timeout: 45000,
  })
  const retry = await practiceApi(page, '/practice/start', 'POST', state._startRequest)
  expect(retry.session_id).toBe(state.session_id)
  expect(retry.status).toBe('completed')
  expect((await practiceApi(page, '/sessions')).length).toBe(1)
})
