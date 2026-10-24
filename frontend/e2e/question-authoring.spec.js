import { test, expect } from './browser-fixture.js'
import AxeBuilder from '@axe-core/playwright'

async function openEditor(page, locale = 'en') {
  await page.goto('/login')
  await page.getByLabel('Email', { exact: true }).fill('release-admin@test.dev')
  await page.getByLabel('Password', { exact: true }).fill('ReleaseTest123!')
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  await expect(page).toHaveURL(/\/admin$/)
  await page.goto('/admin/questions')
  await page.getByRole('button', { name: 'New question', exact: true }).click()
  if (locale) await page.getByLabel('Question content language').selectOption(locale)
}

async function fillMCQ(page, prompt) {
  await page.getByLabel('Question prompt', { exact: true }).fill(prompt)
  await page.getByLabel('Option 1 text', { exact: true }).fill('WHERE')
  await page.getByLabel('Option 2 text', { exact: true }).fill('ORDER BY')
  await page.getByRole('radio', { name: 'correct A', exact: true }).check()
}

test('machine preparation remains an unreviewed draft until administrator review', async ({ page }) => {
  await page.route('**/api/v1/admin/question-translation/capability', route => route.fulfill({ json: { available: true } }))
  await page.route('**/api/v1/admin/question-translation/draft', route => route.fulfill({ json: {
    status: 'draft', translation: { locale: 'en', prompt: 'Which clause filters rows?',
      option_texts: { A: 'WHERE', B: 'ORDER BY' }, rubrics: {} },
  } }))
  await openEditor(page, 'vi')
  await fillMCQ(page, 'Mệnh đề nào lọc dòng?')
  await page.getByText(/Optional reviewed translation/).click()
  await page.getByRole('button', { name: 'Prepare translation draft', exact: true }).click()
  await expect(page.getByLabel('Translated question prompt')).toHaveValue('Which clause filters rows?')
  await expect(page.getByLabel('I reviewed this translation against the current original and grading criteria.')).not.toBeChecked()
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([])
  await page.screenshot({ path: test.info().outputPath('machine-draft-needs-review.png'), fullPage: true })
  const saved = page.waitForResponse(r => r.url().endsWith('/api/v1/admin/questions') && r.request().method() === 'POST')
  await page.getByRole('button', { name: 'Save draft', exact: true }).click()
  const response = await saved
  expect(response.status()).toBe(201)
  const question = await response.json()
  expect(question.translations).toEqual([])
  expect(question.options.find(o => o.is_correct).option_label).toBe('A')
})

for (const [locale, prompt] of [['vi', 'Mệnh đề nào lọc dòng?'], ['en', 'Which clause filters rows?']]) {
  test(`detect ${locale} prose without selecting an authoring language`, async ({ page }) => {
    await openEditor(page, null)
    await fillMCQ(page, prompt)
    await expect(page.getByLabel('Question content language')).toHaveValue(locale)
    const saved = page.waitForResponse(r => r.url().endsWith('/api/v1/admin/questions') && r.request().method() === 'POST')
    await page.getByRole('button', { name: 'Save draft', exact: true }).click()
    const response = await saved
    expect(response.status()).toBe(201)
    const question = await response.json()
    expect(question.original_locale).toBe(locale)
    expect(question.translations).toEqual([])
  })
}

for (const locale of ['vi', 'en']) test(`author ${locale} original without translation; edit preserves language and answer`, async ({ page }) => {
  await openEditor(page, locale)
  const prompt = `${locale === 'vi' ? 'Mệnh đề nào lọc dòng?' : 'Which clause filters rows?'} ${Date.now()}`
  await fillMCQ(page, prompt)
  await expect(page.getByLabel('Translated question prompt')).toHaveCount(0)
  const created = page.waitForResponse(r => r.url().endsWith('/api/v1/admin/questions') && r.request().method() === 'POST')
  await page.getByRole('button', { name: 'Save draft', exact: true }).click()
  const response = await created
  expect(response.status()).toBe(201)
  const question = await response.json()
  expect(question.original_locale).toBe(locale)
  expect(question.translations).toEqual([])
  await page.getByLabel('Search prompt').fill(prompt)
  const row = page.locator('li').filter({ hasText: prompt })
  await row.getByRole('button', { name: 'Edit', exact: true }).click()
  await expect(page.getByLabel('Question content language')).toBeDisabled()
  await expect(page.getByLabel('Question content language')).toHaveValue(locale)
  await expect(page.getByRole('radio', { name: 'correct A', exact: true })).toBeChecked()
  await page.getByRole('button', { name: 'Preview question', exact: true }).click()
  await page.getByLabel('Preview content language').selectOption(locale === 'en' ? 'vi' : 'en')
  await expect(page.getByText(/No reviewed translation for this preview/)).toBeVisible()
  const saved = page.waitForResponse(r => r.url().endsWith(`/api/v1/admin/questions/${question.question_id}`) && r.request().method() === 'PUT')
  await page.getByRole('button', { name: 'Save changes', exact: true }).click()
  expect((await saved).status()).toBe(200)
})

test('review an English translation of a Vietnamese original and preserve both on edit', async ({ page }) => {
  await openEditor(page, 'vi')
  const prompt = `Chọn mệnh đề WHERE. ${Date.now()}`
  await fillMCQ(page, prompt)
  await page.getByText('Optional reviewed translation', { exact: false }).click()
  await page.getByLabel('Translated question prompt', { exact: true }).fill('Choose the WHERE clause.')
  await page.getByLabel('Translated option A', { exact: true }).fill('WHERE')
  await page.getByLabel('Translated option B', { exact: true }).fill('ORDER BY')
  await page.getByLabel('I reviewed this translation against the current original and grading criteria.').check()
  await page.getByRole('button', { name: 'Preview question', exact: true }).click()
  await page.getByLabel('Preview content language').selectOption('en')
  await expect(page.getByRole('region', { name: 'Preview question', exact: true }).getByText('Choose the WHERE clause.', { exact: true })).toBeVisible()
  const created = page.waitForResponse(r => r.url().endsWith('/api/v1/admin/questions') && r.request().method() === 'POST')
  await page.getByRole('button', { name: 'Save draft', exact: true }).click()
  const response = await created
  expect(response.status()).toBe(201)
  const original = await response.json()
  expect(original.translations[0].locale).toBe('en')
  await expect(page.getByRole('button', { name: 'Save draft', exact: true })).toHaveCount(0)
  // The full release bank spans multiple pages; locate the new record before
  // asserting its reviewed display, rather than assuming it is on page one.
  await page.getByLabel('Search prompt').fill('Choose the WHERE clause.')
  await expect(page.getByText('Choose the WHERE clause.', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'Language', exact: true }).click()
  await page.getByRole('menuitemradio', { name: 'Tiếng Việt', exact: true }).click()
  await expect(page.getByText(prompt, { exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'Ngôn ngữ', exact: true }).click()
  await page.getByRole('menuitemradio', { name: 'English', exact: true }).click()
  await page.getByLabel('Search prompt').fill(prompt)
  await page.locator('li').filter({ hasText: 'Choose the WHERE clause.' }).getByRole('button', { name: 'Edit', exact: true }).click()
  await expect(page.getByLabel('Question prompt', { exact: true })).toHaveValue(prompt)
  await page.getByText('Optional reviewed translation', { exact: false }).click()
  await expect(page.getByLabel('Translated question prompt', { exact: true })).toHaveValue('Choose the WHERE clause.')
  await expect(page.getByLabel('I reviewed this translation against the current original and grading criteria.')).not.toBeChecked()
  await page.getByLabel('Question prompt', { exact: true }).fill(prompt + ' Sửa nội dung.')
  const saved = page.waitForResponse(r => r.url().endsWith(`/api/v1/admin/questions/${original.question_id}`) && r.request().method() === 'PUT')
  await page.getByRole('button', { name: 'Save changes', exact: true }).click()
  const edited = await (await saved).json()
  expect(edited.translations[0].prompt).toBe('Choose the WHERE clause.')
  expect(edited.translations[0].current).toBe(false)
  expect(edited.options.find(o => o.is_correct).option_label).toBe('A')
})

test('question editor stays accessible and within the viewport', async ({ page }) => {
  await openEditor(page, 'vi')
  await fillMCQ(page, 'Liệt kê students.id, giữ nguyên SELECT.')
  await page.getByRole('button', { name: 'Preview question', exact: true }).click()
  for (const width of [390, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 900 })
    await page.evaluate(() => window.scrollTo(0, 0))
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
    const bankEdit = page.locator('li').filter({ has: page.getByRole('button', { name: 'Edit', exact: true }) }).first().getByRole('button', { name: 'Edit', exact: true })
    await bankEdit.scrollIntoViewIfNeeded()
    const bounds = await bankEdit.boundingBox()
    expect(bounds.x).toBeGreaterThanOrEqual(0)
    expect(bounds.x + bounds.width).toBeLessThanOrEqual(width)
    await page.screenshot({ path: test.info().outputPath(`authoring-${width}.png`), fullPage: true })
  }
  const accessibility = await new AxeBuilder({ page }).analyze()
  expect(accessibility.violations).toEqual([])
})

test('curriculum selects named prerequisites and CLO mappings and preserves saved sets', async ({ page }) => {
  await openEditor(page)
  const token = await page.evaluate(() => localStorage.getItem('dbcas_token'))
  const headers = { Authorization: `Bearer ${token}` }
  const suffix = Date.now()
  const concepts = []
  for (const label of ['TARGET', 'PREP']) {
    const response = await page.request.post('/api/v1/admin/concepts', { headers, data: {
      concept_code: `UX-${label}-${suffix}`, concept_name: `UX ${label} ${suffix}`, subject_area: 'SQL Querying', difficulty_level: 1,
    } })
    expect(response.status()).toBe(201)
    concepts.push(await response.json())
  }
  const cloResponse = await page.request.post('/api/v1/admin/clos', { headers, data: { clo_code: `UX-CLO-${suffix}`, title: 'Disposable named mapping' } })
  expect(cloResponse.status()).toBe(201)
  const clo = await cloResponse.json()
  const [target, prerequisite] = concepts
  await page.goto('/admin/curriculum')
  await page.getByRole('button', { name: 'Prerequisites', exact: true }).click()
  await page.getByLabel('Search concepts', { exact: true }).fill(target.concept_code)
  await page.locator('summary').filter({ hasText: `Prerequisites for ${target.concept_code}` }).click()
  const group = page.getByRole('group', { name: `Prerequisites for ${target.concept_code}`, exact: true })
  const name = `${prerequisite.concept_name} (${prerequisite.concept_code})`
  await group.getByRole('checkbox', { name, exact: true }).check()
  const saved = page.waitForResponse(r => r.url().endsWith(`/admin/concepts/${target.concept_id}/prerequisites`) && r.request().method() === 'PUT')
  await page.locator('li').filter({ has: group }).getByRole('button', { name: 'Save', exact: true }).click()
  expect((await saved).status()).toBe(200)
  await expect(group.getByRole('checkbox', { name, exact: true })).toBeChecked()
  await page.getByRole('button', { name: /Learning outcomes/ }).click()
  await page.locator('summary').filter({ hasText: `Confirmed concepts for ${clo.clo_code}` }).click()
  const mapping = page.getByRole('group', { name: `Confirmed concepts for ${clo.clo_code}`, exact: true })
  await mapping.getByRole('checkbox', { name, exact: true }).check()
  const mapped = page.waitForResponse(r => r.url().endsWith(`/admin/clos/${clo.clo_id}/concepts`) && r.request().method() === 'PUT')
  await page.locator('li').filter({ has: mapping }).getByRole('button', { name: 'Save set', exact: true }).click()
  expect((await mapped).status()).toBe(200)
  await expect(mapping.getByRole('checkbox', { name, exact: true })).toBeChecked()
  await page.setViewportSize({ width: 390, height: 844 })
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
})

test('Vietnamese SQL authoring preserves executable identifiers and fixtures', async ({ page }) => {
  await openEditor(page, 'vi')
  await page.getByLabel('Question type', { exact: true }).selectOption('sql')
  await page.getByLabel('Question prompt', { exact: true }).fill('Liệt kê students.id bằng SELECT.')
  await page.getByLabel('Reference answer', { exact: true }).fill('SELECT id FROM students')
  const datasets = [
    { dataset_name: 'base', setup_sql: 'CREATE TABLE students(id int); INSERT INTO students VALUES (1)', expected_result: { columns: ['id'], rows: [[1]] }, is_edge_case: false },
    { dataset_name: 'empty', setup_sql: 'CREATE TABLE students(id int)', expected_result: { columns: ['id'], rows: [] }, is_edge_case: true },
  ]
  await page.getByRole('textbox', { name: 'datasets (JSON array)', exact: true }).fill(JSON.stringify(datasets))
  await page.getByRole('button', { name: 'Preview question', exact: true }).click()
  await expect(page.getByRole('region', { name: 'Preview question', exact: true })).toContainText('SELECT id FROM students')
  const created = page.waitForResponse(r => r.url().endsWith('/api/v1/admin/questions') && r.request().method() === 'POST')
  await page.getByRole('button', { name: 'Save draft', exact: true }).click()
  const response = await created
  expect(response.status()).toBe(201)
  const stored = await response.json()
  expect(stored.reference_answer).toBe('SELECT id FROM students')
  expect(stored.datasets.map(({ dataset_id, ...row }) => row)).toEqual(datasets)
})

test('Vietnamese essay authoring keeps explicit four-band grading criteria', async ({ page }) => {
  await openEditor(page, 'vi')
  await page.getByLabel('Question type', { exact: true }).selectOption('essay')
  await page.getByLabel('Question prompt', { exact: true }).fill('Giải thích chuẩn hóa.')
  await page.getByRole('button', { name: 'Add four grading bands', exact: true }).click()
  const ranges = [['Incomplete', '0', '0.24'], ['Partial', '0.25', '0.49'], ['Mostly Complete', '0.50', '0.74'], ['Complete', '0.75', '1']]
  for (const [name, low, high] of ranges) {
    await page.getByLabel(`${name}: Minimum score`, { exact: true }).fill(low)
    await page.getByLabel(`${name}: Maximum score`, { exact: true }).fill(high)
    await page.getByLabel(`${name}: Criteria`, { exact: true }).fill(`Tiêu chí gốc ${name}`)
  }
  await page.getByRole('button', { name: 'Preview question', exact: true }).click()
  await expect(page.getByRole('region', { name: 'Preview question', exact: true })).toContainText('Tiêu chí gốc Complete')
  const created = page.waitForResponse(r => r.url().endsWith('/api/v1/admin/questions') && r.request().method() === 'POST')
  await page.getByRole('button', { name: 'Save draft', exact: true }).click()
  const response = await created
  expect(response.status()).toBe(201)
  const stored = await response.json()
  expect(stored.rubrics).toHaveLength(4)
  expect(stored.rubrics.map(r => r.criteria)).toEqual(ranges.map(([name]) => `Tiêu chí gốc ${name}`))
})
