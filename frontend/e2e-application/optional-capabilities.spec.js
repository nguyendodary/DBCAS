import { test, expect } from '../e2e/browser-fixture.js'
import { adaptiveAcceptance, call, createConceptUi, login } from '../e2e/optional-capabilities.js'

adaptiveAcceptance(test)

test('real application: unavailable AI generation produces a visible failure and no fabricated draft', async ({ page }) => {
  const admin = await login(page)
  const topic = await createConceptUi(page)
  await page.goto('/admin/candidates')
  await page.getByRole('combobox', { name: 'Concept', exact: true }).selectOption(String(topic.concept_id))
  const response = page.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith('/question-candidates/generate'))
  await page.getByRole('button', { name: 'Generate', exact: true }).click()
  const result = await response
  expect(result.status()).toBe(503)
  expect((await result.json()).error.code).toBe('llm_not_configured')
  await expect(page.getByRole('alert').first()).toBeVisible()
  expect((await call(page, '/admin/question-candidates', admin)).filter(c => c.concept_id === topic.concept_id)).toEqual([])
})
