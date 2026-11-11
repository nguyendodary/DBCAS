import { test, expect, request as apiRequest } from './browser-fixture.js'
import AxeBuilder from '@axe-core/playwright'

const API = 'http://127.0.0.1:8100'
const PASSWORD = 'ReleaseTest123!'
async function openHelp(page) {
  await page.getByRole('button', { name: /^(Help|Hướng dẫn)$/ }).click()
  const dialog = page.getByRole('dialog')
  await expect(dialog).toBeVisible()
  // Entrance must not fade the panel: mid-animation text would render below
  // AA contrast even though the settled colors pass.
  expect(await dialog.evaluate((element) => getComputedStyle(element).opacity)).toBe('1')
  return dialog
}

test('first-time user: registration, role boundary, help discovery and accessibility', async ({
  page,
}) => {
  test.setTimeout(180_000)
  const api = await apiRequest.newContext({ baseURL: API, timeout: 30_000 })
  const email = `ftu-onboarding-${Date.now()}@test.dev`
  try {
    await page.addInitScript(() => {
      if (window.top === window && /^https?:$/.test(location.protocol))
        localStorage.setItem('dbcas_locale', 'en')
    })
    await page.goto('/register')
    const help = page.getByRole('button', { name: 'Help', exact: true })
    await expect(help).toBeVisible()
    await expect(page.getByRole('dialog')).toHaveCount(0)

    let dialog = await openHelp(page)
    await expect(
      dialog.getByRole('heading', { name: 'How to use DBCAS', exact: true }),
    ).toBeVisible()
    expect(await page.evaluate(() => getComputedStyle(document.body).overflow)).toBe('hidden')
    await expect(page.locator('#root')).toHaveAttribute('inert', '')
    await page.keyboard.press('Escape')
    await expect(dialog).toHaveCount(0)
    await expect(help).toBeFocused()

    dialog = await openHelp(page)
    await dialog.getByRole('button', { name: 'SQL sandbox', exact: true }).click()
    await expect
      .poll(() => page.evaluate(() => document.activeElement?.id))
      .toBe('help-section-sql')
    await dialog.getByRole('button', { name: 'Close help', exact: true }).click()
    await expect(dialog).toHaveCount(0)

    await page.getByRole('button', { name: 'Language', exact: true }).click()
    await page.getByRole('menuitemradio', { name: 'Tiếng Việt', exact: true }).click()
    const viDialog = await openHelp(page)
    await expect(
      viDialog.getByRole('heading', { name: 'Cách sử dụng DBCAS', exact: true }),
    ).toBeVisible()
    await expect(viDialog.getByText('Hướng dẫn trong ứng dụng', { exact: true })).toBeVisible()
    await page.keyboard.press('Escape')
    await page.getByRole('button', { name: 'Ngôn ngữ', exact: true }).click()
    await page.getByRole('menuitemradio', { name: 'English', exact: true }).click()

    await page.getByLabel('Full name', { exact: true }).fill('First-time Learner')
    await page.getByLabel('Email', { exact: true }).fill(email)
    await page.getByLabel('Password', { exact: true }).fill(PASSWORD)
    await page.getByLabel('Confirm password', { exact: true }).fill(PASSWORD)
    await page.getByRole('button', { name: 'Register', exact: true }).click()
    await expect(page).toHaveURL(/\/login$/)
    await expect(page.getByRole('heading', { name: 'Sign in to DBCAS', exact: true })).toBeVisible()
    await page.getByLabel('Email', { exact: true }).fill(email)
    await page.getByLabel('Password', { exact: true }).fill(PASSWORD)
    const signedIn = page.waitForResponse(
      (response) =>
        response.request().method() === 'POST' &&
        new URL(response.url()).pathname === '/api/v1/auth/login',
    )
    await page.getByRole('button', { name: 'Sign in', exact: true }).click()
    expect((await signedIn).status()).toBe(200)
    await expect(page).toHaveURL(/\/dashboard$/)
    await expect(page.getByRole('heading', { name: 'My competency', exact: true })).toBeVisible()

    // Learner role: no administration navigation and the guarded route returns home.
    await expect(page.locator('a[href="/admin"]')).toHaveCount(0)
    await page.goto('/admin')
    await expect(page).toHaveURL(/\/dashboard$/)
    await expect(page.getByRole('heading', { name: 'My competency', exact: true })).toBeVisible()
    await page.goto('/dashboard')
    await expect(page.getByRole('heading', { name: 'My competency', exact: true })).toBeVisible()

    for (const [path, context] of [
      ['/dashboard', 'Your dashboard'],
      ['/assessments', 'Starting an assessment'],
      ['/history', 'Your assessment history'],
      ['/competency', 'Cumulative competency'],
      ['/settings', 'Account settings'],
    ]) {
      await page.goto(path)
      await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
      const drawer = await openHelp(page)
      await expect(drawer.getByText(context, { exact: true })).toBeVisible()
      await page.keyboard.press('Escape')
    }

    // Learner-only guide section; no administrator guide for this role.
    await page.goto('/dashboard')
    await expect(page.getByRole('heading', { name: 'My competency', exact: true })).toBeVisible()
    let drawer = await openHelp(page)
    await expect(drawer.getByRole('heading', { name: 'Learner guide', exact: true })).toBeVisible()
    await expect(
      drawer.getByRole('heading', { name: 'Administrator guide', exact: true }),
    ).toHaveCount(0)
    let scan = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze()
    expect(scan.violations).toEqual([])
    await page.keyboard.press('Escape')

    // Theme and mobile layout.
    const themeBefore = await page.evaluate(() => document.documentElement.dataset.theme)
    await page.getByRole('button', { name: /Switch to (light|dark) theme/ }).click()
    await expect
      .poll(() => page.evaluate(() => document.documentElement.dataset.theme))
      .not.toBe(themeBefore)
    await page.setViewportSize({ width: 390, height: 844 })
    await page.reload()
    drawer = await openHelp(page)
    const box = await drawer.boundingBox()
    expect(box.width).toBeLessThanOrEqual(391)
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(391)
    scan = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze()
    expect(scan.violations).toEqual([])
    await page.keyboard.press('Escape')
    await page.setViewportSize({ width: 1440, height: 1000 })

    // Public guide content covers learner and administrator roles plus support.
    await page.goto('/assessments')
    await page.getByRole('button', { name: 'Log out', exact: true }).first().click()
    await expect(page).toHaveURL(/\/login$/)
    await expect(page.getByRole('heading', { name: 'Sign in to DBCAS', exact: true })).toBeVisible()
    drawer = await openHelp(page)
    await expect(
      drawer.getByRole('heading', { name: 'Administrator guide', exact: true }),
    ).toBeVisible()
    for (const section of [
      'Overview',
      'Getting started',
      'Question sources',
      'Question types',
      'SQL sandbox',
      'Essay and AI processing',
      'Results and release',
      'Language and theme',
      'Accessibility',
      'Troubleshooting',
    ]) {
      await expect(drawer.getByRole('button', { name: section, exact: true })).toBeVisible()
    }
    await page.keyboard.press('Escape')
  } finally {
    await api.dispose()
  }
})

test('49 learner-defined concept and difficulty scopes start through the visible UI', async ({
  page,
}) => {
  test.setTimeout(900000)
  const { register, start, api, vi, approveWithApi } = await import('./practice-harness.js')
  await register(page, 'scope-matrix')
  const options = await api(page, '/practice/options')
  expect(options.concepts.length).toBeGreaterThan(0)
  const scopes = options.concepts
    .flatMap((concept) => ['EASY', 'MEDIUM', 'HARD'].map((band) => ({ concept, band })))
    .slice(0, 49)
  expect(scopes).toHaveLength(49)
  const ids = new Set()
  for (const { concept, band } of scopes) {
    const state = await start(page, 'ai', 3, {
      concept_ids: [concept.concept_id],
      difficulties: [band],
    })
    expect(state.assessment_id).toBeNull()
    expect(state.selected_concept_ids).toEqual([concept.concept_id])
    expect(ids.has(state.session_id)).toBe(false)
    ids.add(state.session_id)
    const replay = await api(page, '/practice/start', 'POST', state._startRequest)
    expect(replay.session_id).toBe(state.session_id)
    const plan = await api(page, `/sessions/${state.session_id}/questions`)
    expect(plan).toHaveLength(1)
    const low = band === 'EASY' ? 1 : band === 'MEDIUM' ? 3 : 4
    const high = band === 'EASY' ? 2 : band === 'MEDIUM' ? 3 : 5
    const widened = state.selection_notice?.includes('mở rộng')
    if (widened) {
      expect(state.generation_fallback).toBe(true)
      await expect(page.getByText(state.selection_notice, { exact: true })).toBeVisible()
    } else {
      expect(state.current_question.difficulty_level).toBeGreaterThanOrEqual(low)
      expect(state.current_question.difficulty_level).toBeLessThanOrEqual(high)
    }
    expect(state.max_questions).toBe(3)
    await page.getByRole('button', { name: vi.exam.finish, exact: true }).first().click()
    await page
      .getByRole('dialog')
      .getByRole('button', { name: vi.exam.confirmFinish, exact: true })
      .click()
    await expect(page).toHaveURL(new RegExp(`/evaluations/${state.session_id}$`))
    await approveWithApi(page, state.session_id)
    await page.reload()
    const result = await api(page, `/evaluations/attempts/${state.session_id}/retry`, 'POST')
    expect(['pending', 'processing', 'ready']).toContain(result.status)
    await expect(page.getByRole('heading', { name: 'Nhận xét từng câu' })).toBeVisible({
      timeout: 45000,
    })
    expect((await api(page, `/evaluations/attempts/${state.session_id}`)).status).toBe('ready')
    const evidence = await api(page, `/sessions/${state.session_id}/evidence`)
    expect(evidence.items).toHaveLength(3)
    expect(evidence.items.every((item) => Number(item.score) === 0)).toBe(true)
    expect(new Set(evidence.items.map((item) => item.question_id)).size).toBe(3)
    for (const item of evidence.items) {
      if (!widened) {
        expect(item.difficulty_level).toBeGreaterThanOrEqual(low)
        expect(item.difficulty_level).toBeLessThanOrEqual(high)
        expect(item.concepts.every((c) => c.concept_id === concept.concept_id)).toBe(true)
      } else {
        expect(item.concepts.length).toBeGreaterThan(0)
        expect(item.difficulty_level).toBeGreaterThanOrEqual(1)
        expect(item.difficulty_level).toBeLessThanOrEqual(5)
      }
      if (item.question_type === 'mcq')
        expect(item.options.filter((o) => o.is_correct)).toHaveLength(1)
      if (item.question_type === 'essay') expect(item.rubrics).toHaveLength(4)
    }
  }
  expect(ids.size).toBe(49)
})
