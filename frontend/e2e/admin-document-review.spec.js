import { test, expect } from './browser-fixture.js'

// Fully deterministic: all API responses are served from fixtures via
// page.route, so the journey depends on no seeded data, timers or sleeps.
const TOKEN = [
  'e30',
  Buffer.from(JSON.stringify({ sub: 1, exp: 4102444800, iat: 1700000000 })).toString('base64url'),
  'sig',
].join('.')

const ADMIN = {
  account_id: 1,
  email: 'admin@test.dev',
  full_name: 'Review Admin',
  roles: ['Administrator'],
  status: 'active',
}

const DOCS = [
  {
    document_id: 11,
    title: 'SQL indexing notes',
    mime_type: 'text/plain',
    original_filename: 'indexing.txt',
    sha256: 'a'.repeat(64),
    char_count: 900,
    page_count: null,
    chunk_count: 12,
    status: 'approved',
    text_policy_version: 'v1',
    uploaded_by: 1,
    uploaded_at: '2026-11-01T00:00:00Z',
    approved_at: '2026-11-02T00:00:00Z',
  },
  {
    document_id: 12,
    title: 'Grouping lecture draft',
    mime_type: 'text/plain',
    original_filename: 'grouping.txt',
    sha256: 'b'.repeat(64),
    char_count: 400,
    page_count: null,
    chunk_count: 4,
    status: 'draft',
    text_policy_version: 'v1',
    uploaded_by: 1,
    uploaded_at: '2026-11-03T00:00:00Z',
    approved_at: null,
  },
]

const CANDIDATE = {
  candidate_id: 99,
  concept_id: 3,
  concept_code: 'SQL-GROUP',
  question_type: 'mcq',
  validation_status: 'validated',
  promoted_question_id: null,
  created_at: '2026-11-02T00:00:00Z',
  quote: 'WHERE filters rows before grouping.',
  citation_support: 'weak',
  citation_warning: 'The question text has little overlap with the cited quote.',
  payload: { prompt: 'Which SQL clause chooses the result columns?' },
  validation_detail: { content_hash: 'c'.repeat(64) },
}

async function seedAdminRoutes(page, options = {}) {
  const approvalBodies = []
  await page.addInitScript((value) => {
    localStorage.setItem('dbcas_token', value)
    localStorage.setItem('dbcas_locale', 'en')
  }, TOKEN)
  await page.route(/\/api\/v1\/auth\/me$/, (route) => route.fulfill({ json: ADMIN }))
  await page.route(/\/api\/v1\/admin\/clos$/, (route) =>
    route.fulfill({
      json: [{ clo_id: 5, clo_code: 'CLO-1', title: 'Query data', status: 'active' }],
    }),
  )
  await page.route(/\/api\/v1\/admin\/concepts$/, (route) =>
    route.fulfill({
      json: [
        {
          concept_id: 3,
          concept_code: 'SQL-GROUP',
          concept_name: 'Grouping',
          subject_area: 'SQL',
          keywords: [],
          learning_objectives: [],
          status: 'active',
        },
      ],
    }),
  )
  await page.route(/\/api\/v1\/admin\/documents$/, (route) => route.fulfill({ json: DOCS }))
  await page.route(/\/api\/v1\/admin\/documents\/12\/approve$/, (route) => {
    approvalBodies.push(route.request().postDataJSON())
    return route.fulfill({ json: { ...DOCS[1], status: 'approved' } })
  })
  await page.route(/\/api\/v1\/admin\/document-candidates\/generate$/, (route) =>
    route.fulfill(
      options.generate || {
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify([CANDIDATE]),
      },
    ),
  )
  await page.route(/\/api\/v1\/admin\/question-candidates(?:\?|$)/, (route) =>
    route.fulfill({ json: [CANDIDATE] }),
  )
  await page.route(/\/api\/v1\/admin\/question-candidates\/99$/, (route) =>
    route.fulfill({ json: CANDIDATE }),
  )
  await page.route(/\/api\/v1\/admin\/question-candidates\/99\/approve$/, (route) =>
    route.fulfill({
      json: { ...CANDIDATE, validation_status: 'approved', promoted_question_id: 123 },
    }),
  )
  return approvalBodies
}

test('admin reviews grounded candidates and confirms no personal data', async ({ page }) => {
  const approvalBodies = await seedAdminRoutes(page)
  await page.goto('/admin/documents')
  await expect(page.getByRole('heading', { name: 'Grounded question review' })).toBeVisible()
  await expect(page.getByText('SQL indexing notes')).toBeVisible()

  await page.getByRole('button', { name: 'Review' }).click()
  const question = page.getByRole('region', { name: 'Question' })
  const quote = page.getByRole('region', { name: 'Cited quote' })
  await expect(question).toContainText('Which SQL clause chooses the result columns?')
  await expect(quote).toContainText('WHERE filters rows before grouping.')
  await expect(page.getByTestId('citation-weak-warning')).toContainText(
    'The question text has little overlap with the cited quote.',
  )
  await expect(page.getByRole('button', { name: 'Approve into bank' })).toBeEnabled()

  const checkbox = page.getByRole('checkbox', {
    name: 'I confirm this document contains no personal data.',
  })
  const approve = page.getByRole('button', { name: 'Approve for generation' })
  await expect(checkbox).toBeVisible()
  await expect(approve).toBeDisabled()
  await checkbox.check()
  await expect(approve).toBeEnabled()
  await approve.click()
  await expect.poll(() => approvalBodies).toEqual([{ confirm_no_personal_data: true }])
})

test('generation errors are shown clearly without reloading', async ({ page }) => {
  await seedAdminRoutes(page, {
    generate: {
      status: 422,
      contentType: 'application/json',
      body: JSON.stringify({
        error: { code: 'too_many_eligible_chunks', message: 'server detail' },
      }),
    },
  })
  await page.goto('/admin/documents')
  await page.getByLabel('Course learning outcome', { exact: true }).selectOption('5')
  await page.getByLabel('Concept', { exact: true }).selectOption('3')
  await page.getByRole('checkbox', { name: 'Use for generation' }).first().check()
  await page.getByRole('button', { name: 'Generate drafts' }).click()
  await expect(page.getByRole('alert')).toContainText(
    'The selected documents exceed the per-request chunk limit. Select fewer documents and retry.',
  )
})

test('non-admin users cannot open the grounded document screen', async ({ page }) => {
  await page.addInitScript((value) => {
    localStorage.setItem('dbcas_token', value)
    localStorage.setItem('dbcas_locale', 'en')
  }, TOKEN)
  await page.route(/\/api\/v1\/auth\/me$/, (route) =>
    route.fulfill({ json: { ...ADMIN, roles: ['Learner'] } }),
  )
  await page.goto('/admin/documents')
  await expect(page).toHaveURL(/\/dashboard$/)
})
