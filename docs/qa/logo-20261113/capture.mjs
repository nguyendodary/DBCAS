/**
 * Capture the logo QA matrix and fail on any brand/nav overlap.
 *
 * Usage (from the repository root, with the local demo API on :18000):
 *   node docs/qa/logo-20261113/capture.mjs docs/qa/logo-20261113/after
 *
 * The frontend dev server must be running on :5180 with
 * VITE_API_PROXY=http://localhost:18000.
 */
import { createRequire } from 'node:module'
import fs from 'node:fs'
import path from 'node:path'

const require = createRequire(import.meta.url)
const { chromium } = require('../../../frontend/node_modules/playwright')

const OUT = process.argv[2] || 'docs/qa/logo-20261113/after'
const BASE = process.env.BASE_URL || 'http://127.0.0.1:5180'
const API = process.env.API_URL || 'http://localhost:18000'
fs.mkdirSync(OUT, { recursive: true })

async function token(email) {
  const response = await fetch(`${API}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password: process.env.DEMO_PASSWORD || 'Demo12345!' }),
  })
  if (!response.ok) throw new Error(`login ${email} ${response.status}`)
  return (await response.json()).access_token
}

function assertNoBrandOverlap(report) {
  const failures = [...report.issues]
  for (const box of [report.brand, report.nav, report.controls]) {
    if (!box) continue
    if (box.left < -1 || box.right > report.viewport.width + 1) {
      failures.push(`${box.name} leaves the viewport: ${JSON.stringify(box)}`)
    }
  }
  if (report.scrollWidth > report.clientWidth + 1) {
    failures.push(`page scrolls horizontally: ${report.scrollWidth} > ${report.clientWidth}`)
  }
  if (failures.length) throw new Error(`${report.page} ${report.size} ${report.theme}\n${failures.join('\n')}`)
}

const tokens = {
  learner: await token('learner@dbcas.local'),
  admin: await token('admin@dbcas.local'),
}
// W1's real browser audit used a long generated learner email. Mock only the
// profile response so the header is measured with that exact account shape.
const LONG_ACCOUNT = {
  account_id: 999999,
  full_name: 'WW1 Locale Learner',
  email: 'w1-locale-1794382816554@dbcas.local',
  roles: ['Learner'],
  status: 'active',
}
const browser = await chromium.launch()
const sizes = [
  { label: '1280', width: 1280, height: 900 },
  { label: '390', width: 390, height: 844 },
]
const themes = ['light', 'dark']
const scenarios = [
  { name: 'landing', path: '/', ready: '.brand-logo', token: null },
  { name: 'login', path: '/login', ready: 'h1', token: null },
  { name: 'register', path: '/register', ready: 'h1', token: null },
  { name: 'learner-header', path: '/dashboard', ready: 'header .brand-logo', token: 'learner' },
  {
    name: 'learner-long-email',
    path: '/dashboard',
    ready: 'header .brand-logo',
    token: 'learner',
    mockAccount: true,
  },
  { name: 'admin-sidebar', path: '/admin', ready: 'aside .brand-logo, header', token: 'admin' },
]
const report = []

for (const scenario of scenarios) {
  for (const size of sizes) {
    if (scenario.name === 'admin-sidebar' && size.label !== '1280') continue
    for (const theme of themes) {
      const context = await browser.newContext({
        viewport: { width: size.width, height: size.height },
        deviceScaleFactor: 1,
        colorScheme: theme,
      })
      await context.addInitScript(
        ({ theme, token }) => {
          localStorage.setItem('dbcas_theme', theme)
          localStorage.setItem('dbcas_locale', 'en')
          if (token) localStorage.setItem('dbcas_token', token)
        },
        { theme, token: scenario.token ? tokens[scenario.token] : null },
      )
      const page = await context.newPage()
      const errors = []
      page.on('pageerror', (error) => errors.push(String(error)))
      if (scenario.mockAccount) {
        await page.route('**/api/v1/auth/me', (route) =>
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(LONG_ACCOUNT),
          }),
        )
      }
      const response = await page.goto(BASE + scenario.path, { waitUntil: 'networkidle' })
      await page.waitForSelector(scenario.ready, { timeout: 15000 })
      await page.waitForTimeout(300)

      const audit = await page.evaluate(() => {
        const visible = (element) => {
          const style = getComputedStyle(element)
          const rect = element.getBoundingClientRect()
          return style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0 && rect.height > 0
        }
        const box = (element, name) => {
          if (!element) return null
          const rect = element.getBoundingClientRect()
          return {
            name,
            left: Math.round(rect.left * 10) / 10,
            top: Math.round(rect.top * 10) / 10,
            right: Math.round(rect.right * 10) / 10,
            bottom: Math.round(rect.bottom * 10) / 10,
            width: Math.round(rect.width * 10) / 10,
            height: Math.round(rect.height * 10) / 10,
          }
        }
        const overlaps = (a, b) =>
          a.left < b.right - 0.5 &&
          b.left < a.right - 0.5 &&
          a.top < b.bottom - 0.5 &&
          b.top < a.bottom - 0.5

        const issues = []
        const containers = [...document.querySelectorAll('header')]
        const sidebar = [...document.querySelectorAll('aside')].find((element) =>
          element.querySelector('.brand-logo'),
        )
        if (sidebar) containers.push(sidebar)
        let brand = null
        let nav = null
        let controls = null
        let brandNavGap = null

        for (const container of containers) {
          const lockup = container.querySelector('.brand-logo')
          if (!lockup || !visible(lockup)) continue
          brand = box(lockup, 'brand')
          nav = box(container.querySelector('.nav-group'), 'nav')
          controls = box(container.querySelector('.ml-auto.flex.items-center'), 'controls')
          if (nav && nav.width > 0) brandNavGap = Math.round((nav.left - brand.right) * 10) / 10

          if (container.scrollWidth > container.clientWidth + 1) {
            issues.push(
              `${container.tagName.toLowerCase()} scrolls horizontally: ${container.scrollWidth} > ${container.clientWidth}`,
            )
          }
          if (lockup.scrollWidth > lockup.clientWidth + 1) {
            issues.push(`brand content is clipped: ${lockup.scrollWidth} > ${lockup.clientWidth}`)
          }
          for (const part of lockup.querySelectorAll('.brand-mark, .brand-wordmark, .brand-logo-tagline')) {
            if (!visible(part)) continue
            const partBox = box(part, part.className)
            if (partBox.right > brand.right + 1 || partBox.left < brand.left - 1) {
              issues.push(`brand part leaves lockup: ${JSON.stringify(partBox)}`)
            }
          }
          const candidates = [...container.querySelectorAll('a, button, nav, [role="button"]')].filter(
            (element) => !lockup.contains(element) && visible(element),
          )
          for (const candidate of candidates) {
            const candidateBox = box(
              candidate,
              `${candidate.tagName.toLowerCase()}.${String(candidate.className).split(' ')[0]}`,
            )
            if (overlaps(brand, candidateBox)) {
              issues.push(`brand overlaps ${candidateBox.name}: ${JSON.stringify({ brand, candidate: candidateBox })}`)
            }
          }
        }

        return {
          viewport: { width: innerWidth, height: innerHeight },
          scrollWidth: document.documentElement.scrollWidth,
          clientWidth: document.documentElement.clientWidth,
          brand,
          nav,
          controls,
          brandNavGap,
          issues,
        }
      })

      const record = {
        page: scenario.name,
        size: size.label,
        theme,
        status: response?.status(),
        errors,
        ...audit,
      }
      report.push(record)
      if (!record.brand) throw new Error(`${scenario.name} ${size.label} ${theme}: no brand lockup measured`)
      if (record.brandNavGap !== null && record.brandNavGap < 0) {
        throw new Error(`${scenario.name} ${size.label} ${theme}: brand/nav gap ${record.brandNavGap}px`)
      }
      assertNoBrandOverlap(record)
      await page.screenshot({ path: path.join(OUT, `${scenario.name}-${size.label}-${theme}.png`), fullPage: true })
      console.log(
        `${scenario.name} ${size.label} ${theme} scrollWidth=${record.scrollWidth}/${record.clientWidth} brand=${record.brand?.width}px nav=${record.nav?.width || 0}px controls=${record.controls?.width || 0}px gap=${record.brandNavGap ?? 'n/a'}px`,
      )
      await context.close()
    }
  }
}

await browser.close()

const assets = {}
for (const asset of [
  '/brand/favicon.ico',
  '/brand/dbcas-16.png',
  '/brand/dbcas-32.png',
  '/brand/dbcas-180.png',
  '/brand/manifest.webmanifest',
]) {
  const response = await fetch(BASE + asset)
  if (response.status !== 200) throw new Error(`${asset} returned ${response.status}`)
  const bytes = (await response.arrayBuffer()).byteLength
  assets[asset] = { status: response.status, contentType: response.headers.get('content-type'), bytes }
  console.log(`${asset} ${response.status} ${assets[asset].contentType} ${bytes} bytes`)
}

fs.writeFileSync(path.join(OUT, 'capture.json'), JSON.stringify({ assets, captures: report }, null, 2))
console.log(`wrote ${report.length} captures to ${OUT}`)
