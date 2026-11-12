import { test, expect } from './browser-fixture.js'
import AxeBuilder from '@axe-core/playwright'
import vi from '../src/i18n/vi.json' with { type: 'json' }
import en from '../src/i18n/en.json' with { type: 'json' }

for (const theme of ['light', 'dark']) {
  for (const locale of ['vi', 'en']) {
    for (const width of [1280, 390]) {
      test(`OAuth remains discoverable without credentials: ${theme}/${locale}/${width}`, async ({
        page,
      }) => {
        const copy = locale === 'vi' ? vi : en
        await page.addInitScript(
          ({ theme, locale }) => {
            localStorage.setItem('dbcas_theme', theme)
            localStorage.setItem('dbcas_locale', locale)
          },
          { theme, locale },
        )
        await page.route('**/api/v1/auth/oauth/providers', (route) =>
          route.fulfill({
            json: { providers: ['google', 'github'].map((name) => ({ name, configured: false })) },
          }),
        )
        await page.setViewportSize({ width, height: 900 })
        let starts = 0
        page.on('request', (request) => {
          if (/\/auth\/oauth\/[^/]+\/start/.test(request.url())) starts++
        })
        for (const screen of ['login', 'register']) {
          await page.goto(`/${screen}`)
          for (const label of ['Google', 'GitHub']) {
            const control = page.getByRole('button', {
              name: copy.auth.continueProvider.replace('{{provider}}', label),
            })
            await expect(control).toBeVisible()
            await expect(control).toBeEnabled()
            await control.click()
            await expect(page.getByRole('status')).toHaveText(
              copy.auth.providerNotConfigured.replace('{{provider}}', label),
            )
            await expect(page).toHaveURL(new RegExp(`/${screen}$`))
          }
          expect(
            await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
          ).toBe(true)
          expect(
            (await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze()).violations,
          ).toEqual([])
        }
        expect(starts).toBe(0)
      })
    }
  }
}

test('metadata failure keeps both controls safe', async ({ page }) => {
  await page.route('**/api/v1/auth/oauth/providers', (route) =>
    route.fulfill({ status: 503, json: {} }),
  )
  await page.goto('/login')
  const google = page.getByRole('button', { name: 'Continue with Google' })
  await expect(google).toBeEnabled()
  await google.click()
  await expect(page.getByRole('status')).toHaveText(
    en.auth.providerNotConfigured.replace('{{provider}}', 'Google'),
  )
  await expect(page.getByRole('button', { name: 'Continue with GitHub' })).toBeVisible()
})

async function fakeProviderBoundary(page) {
  // Intercept the initial navigation: Chromium can follow a server redirect
  // before a route on the external destination has a chance to handle it.
  for (const provider of ['google', 'github']) {
    await page.route(`**/api/v1/auth/oauth/${provider}/start`, async (route) => {
      const upstream = await route.fetch({ maxRedirects: 0 })
      expect(upstream.status()).toBe(302)
      const authorization = new URL(upstream.headers().location)
      expect(authorization.hostname).toBe(
        provider === 'google' ? 'accounts.google.com' : 'github.com',
      )
      const headers = {
        ...upstream.headers(),
        location: `http://127.0.0.1:8101/${provider}/authorize${authorization.search}`,
      }
      delete headers['content-length']
      return route.fulfill({
        response: upstream,
        status: 302,
        headers,
        body: '',
      })
    })
  }
}

async function socialLogin(
  page,
  provider,
  email,
  decision = 'Accept verified email',
  screen = 'login',
) {
  await page.goto(`/${screen}`)
  await page
    .getByRole('link', { name: `Continue with ${provider === 'google' ? 'Google' : 'GitHub'}` })
    .click()
  await expect(page.getByRole('heading', { name: `Local fake ${provider}` })).toBeVisible()
  await page.getByLabel('Email', { exact: true }).fill(email)
  await page.getByRole('button', { name: decision, exact: true }).click()
}

test('local fake OAuth signup, verified-email linking, signin, single-use handoff and refresh', async ({
  page,
  browser,
  browserDiagnostics,
}, info) => {
  await fakeProviderBoundary(page)
  const email = `oauth-${Date.now()}-${Math.random().toString(16).slice(2)}@test.dev`
  let handoff
  await page.route('**/api/v1/auth/oauth/complete', async (route) => {
    handoff = (await page.context().cookies()).find(
      (cookie) => cookie.name === 'dbcas_oauth_handoff',
    )
    await route.continue()
  })
  await socialLogin(page, 'google', email, 'Accept verified email', 'register')
  await expect(page).toHaveURL(/\/dashboard$/)
  const account = await page.evaluate(async () =>
    (
      await fetch('/api/v1/auth/me', {
        headers: { authorization: `Bearer ${localStorage.getItem('dbcas_token')}` },
      })
    ).json(),
  )
  expect(account.email).toBe(email)
  expect(account.roles).toEqual(['Learner'])
  expect(await page.evaluate(() => Boolean(localStorage.getItem('dbcas_refresh_token')))).toBe(true)
  expect(handoff?.httpOnly).toBe(true)
  await page.context().addCookies([handoff])
  const replay = await page.request.post('/api/v1/auth/oauth/complete')
  expect(replay.status()).toBe(401)
  for (const provider of ['github', 'google']) {
    // A fresh signed-out client avoids clearing credentials while dashboard
    // requests can still redirect the existing document during navigation.
    const signinContext = await browser.newContext({
      baseURL: info.project.use.baseURL,
      storageState: {
        cookies: [],
        origins: [
          {
            origin: new URL(info.project.use.baseURL).origin,
            localStorage: [{ name: 'dbcas_locale', value: 'en' }],
          },
        ],
      },
    })
    browserDiagnostics.observe(signinContext)
    try {
      const signinPage = await signinContext.newPage()
      await fakeProviderBoundary(signinPage)
      await socialLogin(signinPage, provider, email)
      await expect(signinPage).toHaveURL(/\/dashboard$/)
      const result = await signinPage.evaluate(async () => {
        const response = await fetch('/api/v1/auth/refresh', {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({ refresh_token: localStorage.getItem('dbcas_refresh_token') }),
        })
        const body = await response.json()
        return {
          status: response.status,
          account: body.account,
          hasRefresh: Boolean(body.refresh_token),
        }
      })
      expect(result.status).toBe(200)
      expect(result.account.account_id).toBe(account.account_id)
      expect(result.hasRefresh).toBe(true)
    } finally {
      await signinContext.close()
    }
  }
})

for (const provider of ['google', 'github']) {
  for (const [decision, error] of [
    ['Deny consent', 'denied'],
    ['Use unverified email', 'email_unverified'],
    ['Provider unavailable', 'exchange'],
  ]) {
    test(`local fake ${provider} handles ${decision}`, async ({ page }) => {
      await fakeProviderBoundary(page)
      await socialLogin(page, provider, `rejected-${Date.now()}@test.dev`, decision)
      await expect(page).toHaveURL(new RegExp(`/login\\?oauth_error=${error}$`))
      await expect(page.getByRole('alert')).toBeVisible()
      expect(await page.evaluate(() => localStorage.getItem('dbcas_token'))).toBeNull()
    })
  }
}
