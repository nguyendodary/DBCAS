import { expect } from './browser-fixture.js'

export const API = 'http://127.0.0.1:8100/api/v1'
export const PASSWORD = 'ReleaseTest123!'
export async function call(page, path, token, method = 'GET', data) {
  const response = await page.request.fetch(`${API}${path}`, {
    method,
    data,
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  expect(
    response.ok(),
    `${method} ${path}: ${response.status()} ${await response.text()}`,
  ).toBeTruthy()
  return response.json()
}
export async function login(page, email = 'release-admin@test.dev') {
  await page.goto('/login')
  await page.evaluate(() => localStorage.setItem('dbcas_locale', 'en'))
  await page.reload()
  await expect(page.getByRole('heading', { name: 'Sign in to DBCAS', exact: true })).toBeVisible()
  await page.getByLabel('Email', { exact: true }).fill(email)
  await page.getByLabel('Password', { exact: true }).fill(PASSWORD)
  const response = page.waitForResponse(
    (r) => r.request().method() === 'POST' && r.url().endsWith('/auth/login'),
  )
  await page.getByRole('button', { name: 'Sign in', exact: true }).click()
  expect((await response).status()).toBe(200)
  await expect(page).toHaveURL(email === 'release-admin@test.dev' ? /\/admin$/ : /\/dashboard$/)
  await expect(
    page.getByRole('heading', {
      name: email === 'release-admin@test.dev' ? 'Cohort Overview' : 'My competency',
      exact: true,
    }),
  ).toBeVisible()
  return page.evaluate(() => localStorage.getItem('dbcas_token'))
}
export async function register(page) {
  const email = `adaptive-${Date.now()}-${Math.random().toString(16).slice(2, 7)}@test.dev`
  await page.evaluate(() => localStorage.removeItem('dbcas_token'))
  await page.goto('/register')
  for (const [name, value] of [
    ['Full name', 'Adaptive practice learner'],
    ['Email', email],
    ['Password', PASSWORD],
    ['Confirm password', PASSWORD],
  ])
    await page.getByLabel(name, { exact: true }).fill(value)
  await page.getByRole('button', { name: 'Register', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Sign in to DBCAS', exact: true })).toBeVisible()
  return login(page, email)
}
export async function createConceptUi(
  page,
  description = 'Interpret SELECT projection and WHERE filtering using query results.',
) {
  await page.goto('/admin/curriculum')
  const name = `Optional query skill ${Date.now()}-${Math.random().toString(16).slice(2, 6)}`
  await page.getByLabel('Concept name', { exact: true }).fill(name)
  await page.getByLabel('Subject area', { exact: true }).fill('SQL Querying')
  await page.getByLabel('Concept description', { exact: true }).fill(description)
  await page
    .getByLabel('Concept keywords (comma separated)', { exact: true })
    .fill('SELECT, projection, WHERE')
  await page
    .getByLabel('Learning objectives (one per line)', { exact: true })
    .fill('Distinguish result-column projection from filtering of result rows.')
  const response = page.waitForResponse(
    (r) => r.request().method() === 'POST' && r.url().endsWith('/admin/concepts'),
  )
  await page.getByRole('button', { name: 'Add concept', exact: true }).click()
  const result = await response
  expect(result.status()).toBe(201)
  return result.json()
}
