import { test, expect } from './browser-fixture.js'

export const API = 'http://127.0.0.1:8100/api/v1'
export const PASSWORD = 'ReleaseTest123!'
export async function call(page, path, token, method = 'GET', data) {
  const response = await page.request.fetch(`${API}${path}`, {
    method,
    data,
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  expect(response.ok(), `${method} ${path}: HTTP ${response.status()}`).toBe(true)
  return response.json()
}
export async function login(page, email) {
  await page.goto('/login')
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

// These cases are also imported by the normal app.main browser gate. OAuth
// registrations belong to the disposable launcher, never the owner's .env.
export function entrypointCases() {
  test('configured OAuth entry points keep state and safe callbacks without live authentication', async ({
    page,
    browserName,
  }, testInfo) => {
    await page.goto('/login')
    const providers = await call(page, '/auth/oauth/providers')
    expect(
      providers.providers
        .filter((p) => p.configured)
        .map((p) => p.name)
        .sort(),
    ).toEqual(['github', 'google'])
    for (const [provider, label, host] of [
      ['google', 'Google', 'accounts.google.com'],
      ['github', 'GitHub', 'github.com'],
    ]) {
      await page.goto('/login')
      const startPath = `/api/v1/auth/oauth/${provider}/start`
      let upstreamStatus, authorization, flowCookies
      // Intercept before the redirect chain. Routing only the external
      // destination can let a browser follow the initial unhandled redirect.
      // Fetch the real backend response once, with redirect following disabled.
      await page.route(`**${startPath}`, async (route) => {
        const upstream = await route.fetch({ maxRedirects: 0 })
        upstreamStatus = upstream.status()
        authorization = new URL(upstream.headers().location)
        flowCookies = upstream
          .headersArray()
          .filter((header) => header.name.toLowerCase() === 'set-cookie')
          .map(({ value }) => ({
            name: value.slice(0, value.indexOf('=')),
            httpOnly: /(?:^|;)\s*HttpOnly(?:;|$)/i.test(value),
            sameSiteLax: /(?:^|;)\s*SameSite=Lax(?:;|$)/i.test(value),
            correctPath: /(?:^|;)\s*Path=\/api\/v1\/auth\/oauth(?:;|$)/i.test(value),
          }))
        const headers = { ...upstream.headers(), 'content-type': 'text/html' }
        delete headers.location
        delete headers['content-length']
        await route.fulfill({
          response: upstream,
          status: 200,
          headers,
          body: '<main><h1>Controlled provider authorization landing</h1></main>',
        })
      })
      const button = page.getByRole('link', { name: new RegExp(label) })
      await expect(button).not.toHaveAttribute('aria-disabled', 'true')
      await expect(button).toHaveAttribute('href', `/api/v1/auth/oauth/${provider}/start`)
      await button.click()
      await expect(
        page.getByRole('heading', { name: 'Controlled provider authorization landing' }),
      ).toBeVisible()
      expect(upstreamStatus).toBe(302)
      expect(authorization.hostname === host).toBe(true)
      expect(authorization.searchParams.has('state')).toBe(true)
      expect(
        authorization.searchParams.get('redirect_uri') ===
          `http://127.0.0.1:5174/api/v1/auth/oauth/${provider}/callback`,
      ).toBe(true)
      if (provider === 'google')
        expect(authorization.searchParams.get('code_challenge_method') === 'S256').toBe(true)
      const names =
        provider === 'google'
          ? ['dbcas_oauth_state', 'dbcas_oauth_verifier']
          : ['dbcas_oauth_state']
      expect(flowCookies.map((cookie) => cookie.name).sort()).toEqual(names)
      expect(
        flowCookies.every((cookie) => cookie.httpOnly && cookie.sameSiteLax && cookie.correctPath),
      ).toBe(true)
      const cookies = await page
        .context()
        .cookies(`http://127.0.0.1:5174/api/v1/auth/oauth/${provider}/callback`)
      // Native Windows WebKit reports every SameSite mode as None, including
      // real HTTP cookies and context.addCookies. Keep the wire policy strict.
      // https://github.com/microsoft/playwright/blob/main/tests/library/browsercontext-cookies.spec.ts#L121-L131
      const sameSite =
        browserName === 'webkit' &&
        process.platform === 'win32' &&
        testInfo.project.use.channel !== 'webkit-wsl'
          ? 'None'
          : 'Lax'
      for (const name of names) {
        const cookie = cookies.find((cookie) => cookie.name === name)
        expect(cookie?.httpOnly).toBe(true)
        expect(cookie?.path).toBe('/api/v1/auth/oauth')
        expect(cookie?.sameSite).toBe(sameSite)
      }
      expect(await page.evaluate(() => document.cookie.includes('dbcas_oauth_'))).toBe(false)
      await page.unroute(`**${startPath}`)
    }
  })

  test('concept authoring generates its reference and persists meaningful metadata', async ({
    page,
  }) => {
    const admin = await login(page, 'release-admin@test.dev')
    await page.goto('/admin/curriculum')
    const name = `Reviewed joins ${Date.now()}`
    await expect(page.getByLabel('Concept code', { exact: true })).not.toBeVisible()
    await page.getByLabel('Concept name', { exact: true }).fill(name)
    await page.getByLabel('Subject area', { exact: true }).fill('SQL')
    await page
      .getByLabel('Concept description', { exact: true })
      .fill('Combine related rows and explain the difference between join types.')
    await page
      .getByLabel('Concept keywords (comma separated)', { exact: true })
      .fill('join, relationship')
    await page
      .getByLabel('Learning objectives (one per line)', { exact: true })
      .fill('Compare inner and outer joins\nPreserve unmatched rows with outer joins')
    const creating = page.waitForResponse(
      (r) => r.request().method() === 'POST' && r.url().endsWith('/admin/concepts'),
    )
    await page.getByRole('button', { name: 'Add concept', exact: true }).click()
    const response = await creating
    expect(response.status()).toBe(201)
    const concept = await response.json()
    expect(concept.concept_code.length).toBeGreaterThan(0)
    expect(concept.concept_code.length).toBeLessThanOrEqual(30)
    expect(concept.keywords).toEqual(['join', 'relationship'])
    expect(concept.learning_objectives).toHaveLength(2)
    const stored = (await call(page, '/admin/concepts', admin)).find(
      (c) => c.concept_id === concept.concept_id,
    )
    expect(stored.concept_name).toBe(name)
    expect(stored.concept_code).toBe(concept.concept_code)
    // A new concept has no authored questions yet: widening must be disclosed
    // and the requested count must still be exact.
    const learnerEmail = `catalog-${Date.now()}@test.dev`
    await call(page, '/auth/register', null, 'POST', {
      name: 'Catalog boundary learner',
      email: learnerEmail,
      password: PASSWORD,
      password_confirm: PASSWORD,
    })
    const learner = await call(page, '/auth/login', null, 'POST', {
      email: learnerEmail,
      password: PASSWORD,
    })
    const options = await call(page, '/practice/options', learner.access_token)
    expect(options.concepts.some((c) => c.concept_id === concept.concept_id)).toBe(true)
    const expanded = await page.request.post(`${API}/practice/start`, {
      headers: { Authorization: `Bearer ${learner.access_token}` },
      data: {
        concept_ids: [concept.concept_id],
        difficulties: ['EASY'],
        source: 'bank',
        question_count: 3,
        request_id: crypto.randomUUID(),
      },
    })
    expect(expanded.status()).toBe(200)
    const state = await expanded.json()
    expect(state.max_questions).toBe(3)
    expect(state.selected_concept_ids).toEqual([concept.concept_id])
    expect(state.selection_notice).toContain('mở rộng')
    const questions = await call(
      page,
      `/sessions/${state.session_id}/questions`,
      learner.access_token,
    )
    expect(questions).toHaveLength(1) // Only the first question has been delivered.
    await call(page, `/sessions/${state.session_id}/finish`, learner.access_token, 'POST')
    await call(
      page,
      `/evaluations/attempts/${state.session_id}/retry`,
      learner.access_token,
      'POST',
    )
    await expect
      .poll(
        async () =>
          (await call(page, `/evaluations/attempts/${state.session_id}`, learner.access_token))
            .status,
        { timeout: 45_000 },
      )
      .toBe('ready')
    const evidence = await call(
      page,
      `/sessions/${state.session_id}/evidence`,
      learner.access_token,
    )
    expect(evidence.items).toHaveLength(3)
    expect(new Set(evidence.items.map((q) => q.question_id)).size).toBe(3)
    expect(evidence.items.every((q) => Number(q.score) === 0)).toBe(true)
  })
}
