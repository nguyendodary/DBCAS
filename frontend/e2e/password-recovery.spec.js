import { test, expect, request as apiRequest } from './browser-fixture.js'

const API = 'http://127.0.0.1:8100'
const MAILPIT = process.env.DBCAS_MAILPIT_API ?? 'http://127.0.0.1:8026'
const FRONTEND_ORIGIN = 'http://127.0.0.1:5174'
const PASSWORD = 'ReleaseTest123!'
const NEW_PASSWORD = 'Recovered-456!'

// Real end-to-end recovery: the backend under test sends through the compose
// Mailpit service, so the link used here is the one a learner actually receives.
test('password recovery delivers a real Mailpit email, resets, and rejects replay', async ({ page }) => {
  const api = await apiRequest.newContext()
  const email = `recovery-${Date.now()}-${Math.random().toString(16).slice(2)}@test.dev`
  try {
    const registered = await api.post(`${API}/api/v1/auth/register`, {
      data: { name: 'Recovery Learner', email, password: PASSWORD, password_confirm: PASSWORD },
    })
    expect(registered.ok(), await registered.text()).toBeTruthy()
    expect((await api.delete(`${MAILPIT}/api/v1/messages`)).ok()).toBeTruthy()

    await page.addInitScript(() => localStorage.setItem('dbcas_locale', 'en'))
    await page.goto('/login')
    await page.getByRole('link', { name: 'Forgot password?', exact: true }).click()
    await expect(page).toHaveURL(/\/forgot-password$/)
    // The address bar updates before React commits the new page; wait for the
    // heading so the fill cannot land on the still-mounted sign-in field.
    await expect(page.getByRole('heading', { name: 'Reset your password' })).toBeVisible()
    await page.getByLabel('Email', { exact: true }).fill(email)
    await page.getByRole('button', { name: 'Send reset link', exact: true }).click()
    await expect(page.getByText('Check your email')).toBeVisible()

    // Capture the actual delivered message instead of assuming a URL shape.
    let detail
    await expect.poll(async () => {
      const list = await (await api.get(`${MAILPIT}/api/v1/messages`)).json()
      const summary = (list.messages ?? []).find(message =>
        (message.To ?? []).some(to => String(to.Address ?? to) === email))
      if (!summary) return false
      const response = await api.get(`${MAILPIT}/api/v1/message/${summary.ID}`)
      detail = await response.json()
      return true
    }, { timeout: 20_000 }).toBe(true)

    expect(detail.Subject).toContain('password reset')
    expect((detail.To ?? []).some(to => String(to.Address ?? to) === email)).toBe(true)
    const body = detail.Text ?? ''
    const link = body.match(/http:\/\/127\.0\.0\.1:5174\/reset-password\?token=[A-Za-z0-9_-]+/)?.[0]
    expect(link, body).toBeTruthy()
    expect(new URL(link).origin).toBe(FRONTEND_ORIGIN)

    await page.goto(link)
    await expect(page.getByRole('heading', { name: 'Choose a new password' })).toBeVisible()
    await page.getByLabel('New password', { exact: true }).fill(NEW_PASSWORD)
    await page.getByLabel('Confirm password', { exact: true }).fill(NEW_PASSWORD)
    await page.getByRole('button', { name: 'Set new password', exact: true }).click()
    await expect(page.getByText('Password updated')).toBeVisible()

    const oldLogin = await api.post(`${API}/api/v1/auth/login`, {
      data: { email, password: PASSWORD },
    })
    expect(oldLogin.status()).toBe(401)

    // The same link must not be usable a second time.
    await page.goto(link)
    await expect(page.getByRole('heading', { name: 'Choose a new password' })).toBeVisible()
    await page.getByLabel('New password', { exact: true }).fill('Another-789!')
    await page.getByLabel('Confirm password', { exact: true }).fill('Another-789!')
    await page.getByRole('button', { name: 'Set new password', exact: true }).click()
    await expect(page.getByRole('heading', { name: 'This link is not valid' })).toBeVisible()

    // The new password signs in through the real UI.
    await page.goto('/login')
    await page.getByLabel('Email', { exact: true }).fill(email)
    await page.getByLabel('Password', { exact: true }).fill(NEW_PASSWORD)
    await page.getByRole('button', { name: 'Sign in', exact: true }).click()
    await expect(page).toHaveURL(/\/dashboard$/)
  } finally {
    await api.dispose()
  }
})

test('unknown addresses get the same neutral answer and no email', async ({ page }) => {
  const api = await apiRequest.newContext()
  try {
    expect((await api.delete(`${MAILPIT}/api/v1/messages`)).ok()).toBeTruthy()
    await page.goto('/forgot-password')
    await page.getByLabel('Email', { exact: true }).fill('missing-account@test.dev')
    await page.getByRole('button', { name: 'Send reset link', exact: true }).click()
    await expect(page.getByText('Check your email')).toBeVisible()
    await expect(page.getByText(/if an account exists for that email/i)).toBeVisible()

    // Allow the background task a bounded window; a real account would have
    // delivered well before this in the previous test.
    await page.waitForTimeout(2_000)
    const inbox = await (await api.get(`${MAILPIT}/api/v1/messages`)).json()
    expect(inbox.messages ?? []).toHaveLength(0)
  } finally {
    await api.dispose()
  }
})
