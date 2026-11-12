import { test, expect } from './browser-fixture.js'

test.use({ legacyEnglish: false, reducedMotion: 'reduce' })

const longName = 'INSERT/UPDATE/DELETE/RETURNING'
const account = {
  account_id: 1,
  full_name: 'Visual fixture administrator',
  email: 'visual@test.dev',
  roles: ['Administrator'],
  status: 'active',
}
const review = {
  session_id: 9,
  learner_name: 'Visual fixture learner',
  assessment_title: 'Visual fixture',
  learner_defined: true,
  release_status: 'pending_review',
  result_release_policy: 'HUMAN_VERIFIED',
  revision: 1,
  events: [],
  score_edits: [],
  evaluation: { evaluation: { summary: 'Ready for administrator review', question_comments: [] } },
  items: ['sql', 'essay'].map((kind, i) => ({
    attempt_id: i + 1,
    question_type: kind,
    prompt: `Visual ${kind} question`,
    points: 1,
    automated_score: 1,
    automated_detail: {},
    options: [],
    rubrics: [],
    revision: 0,
    grading_status: 'graded',
    review: null,
    reference_answer:
      kind === 'sql' ? 'SELECT 1 AS reference' : 'Essay reference with Vietnamese: dữ liệu.',
    ...(kind === 'sql'
      ? { sql_answer: 'SELECT 1 AS response' }
      : { essay_answer: 'Essay response with Vietnamese: dữ liệu.' }),
  })),
}

// These read-only fixtures isolate visual edge cases; the real learner/admin
// journeys in the other specs continue to exercise the live application API.
async function visualFixture(page, { locale = 'en', theme = 'light', admin = true } = {}) {
  await page.addInitScript(
    ({ locale, theme, admin }) => {
      localStorage.setItem('dbcas_locale', locale)
      localStorage.setItem('dbcas_theme', theme)
      if (admin) localStorage.setItem('dbcas_token', 'visual-fixture-token')
    },
    { locale, theme, admin },
  )
  const responses = {
    '/auth/me': account,
    '/auth/oauth/providers': { providers: [] },
    '/admin/concepts': [
      {
        concept_id: 1,
        concept_code: 'DML',
        concept_name: longName,
        subject_area: 'SQL',
        difficulty_level: 2,
        description: '',
        keywords: [],
        learning_objectives: [],
      },
    ],
    '/admin/clos': [],
    '/concepts/graph': { nodes: [] },
    '/admin/grading-reviews': [review],
    '/admin/grading-reviews/9': review,
    '/admin/analytics/cohort': {
      learner_count: 1,
      finalized_sessions: 1,
      concepts: [],
      trend: [{ date: '2026-11-10', mean_result_pct: 40.24 }],
    },
    '/admin/learners': [],
    '/admin/analytics/statistics': {
      dimensions: {},
      graded_sessions: 0,
      pending_formal_sessions: 0,
    },
  }
  await page.route('**/api/v1/**', async (route) => {
    const key = new URL(route.request().url()).pathname.replace('/api/v1', '')
    expect(route.request().method(), key).toBe('GET')
    expect(Object.hasOwn(responses, key), `Unexpected fixture request: ${key}`).toBe(true)
    await route.fulfill({ json: responses[key] })
  })
}

test('authentication introduction describes chosen practice and approval in both languages', async ({
  page,
}) => {
  await visualFixture(page, { admin: false })
  await page.setViewportSize({ width: 1280, height: 900 })
  await page.goto('/login')
  for (const [locale, expected] of [
    [
      'en',
      'Choose concepts, difficulty and question count. Results appear after administrator approval.',
    ],
    ['vi', 'Chọn khái niệm, độ khó và số câu. Kết quả hiển thị sau khi quản trị viên duyệt.'],
  ]) {
    if (locale === 'vi') {
      await page.getByRole('button', { name: 'Language', exact: true }).click()
      await page.getByRole('menuitemradio', { name: 'Tiếng Việt', exact: true }).click()
    }
    await expect(page.getByText(expected, { exact: true })).toBeVisible()
  }
})

test('long curriculum names leave mobile edit and delete actions inside the card', async ({
  page,
}) => {
  await visualFixture(page, { locale: 'vi' })
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/admin/curriculum')
  const name = page.getByText(longName, { exact: true })
  await expect(name).toBeVisible()
  await page.evaluate(() => document.fonts.ready)
  const row = name.locator('xpath=ancestor::li[1]')
  await row.scrollIntoViewIfNeeded()
  const edit = row.getByRole('button', { name: 'Chỉnh sửa', exact: true })
  const remove = row.getByRole('button', { name: 'Xóa', exact: true })
  const bounds = await row.evaluate((li) => {
    const name = li.querySelector('.font-medium').getBoundingClientRect()
    const buttons = [...li.querySelectorAll('button')].map((button) =>
      button.getBoundingClientRect(),
    )
    const card = li.closest('.overflow-hidden').getBoundingClientRect()
    return {
      nameRight: name.right,
      actionsLeft: buttons[0].left,
      actionsRight: buttons.at(-1).right,
      cardRight: card.right,
    }
  })
  expect(bounds.nameRight).toBeLessThanOrEqual(bounds.actionsLeft - 3)
  expect(bounds.actionsRight).toBeLessThanOrEqual(bounds.cardRight)
  await expect(remove).toBeInViewport({ ratio: 1 })
  await edit.click()
  await expect(page.getByRole('textbox', { name: 'Tên khái niệm', exact: true })).toHaveValue(
    longName,
  )
})

test('administrator review uses Inter for essay prose and JetBrains Mono for SQL', async ({
  page,
}) => {
  await visualFixture(page)
  await page.goto('/admin/grading/9')
  await expect(page.getByText('Visual essay question', { exact: true })).toBeVisible()
  await page.evaluate(() => document.fonts.ready)
  const essay = page.locator('pre').filter({ hasText: 'Essay response with Vietnamese' })
  const sql = page.locator('pre').filter({ hasText: 'SELECT 1 AS response' })
  await expect(essay).toHaveCSS('font-family', /Inter Variable/)
  await expect(sql).toHaveCSS('font-family', /JetBrains Mono/)
  const card = page
    .locator('.space-y-3.p-4')
    .filter({ has: page.getByText('Visual essay question', { exact: true }) })
  await card.locator('summary').first().click()
  await expect(
    card.locator('pre').filter({ hasText: 'Essay reference with Vietnamese' }),
  ).toHaveCSS('font-family', /Inter Variable/)
})

test('a single-date trend point is visible inside the plot and has a numeric text equivalent', async ({
  page,
}) => {
  await visualFixture(page)
  await page.goto('/admin')
  const chart = page.getByRole('img', { name: /^Daily mean fully graded session results/ })
  await expect(chart).toBeVisible()
  await page.evaluate(() => document.fonts.ready)
  await expect
    .poll(() =>
      chart.evaluate((canvas) => {
        const { width, height } = canvas
        const data = canvas.getContext('2d').getImageData(0, 0, width, height).data
        let count = 0,
          sum = 0
        // Exclude the bottom legend; only the blue data point qualifies in this area.
        for (let y = 0; y < height * 0.75; y++)
          for (let x = 0; x < width; x++) {
            const i = (y * width + x) * 4
            const [r, g, b, alpha] = data.slice(i, i + 4)
            if (alpha > 200 && b > 170 && b > r * 1.4 && b > g * 1.15) {
              count++
              sum += x
            }
          }
        return count > 10 ? sum / count / width : 0
      }),
    )
    .toBeGreaterThan(0.3)
  await expect(chart).toHaveAttribute('aria-label', /40\.24%/)
  await expect(page.getByText(/: 40\.24%$/, { exact: false })).toBeVisible()
})
