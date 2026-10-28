import { describe, expect, it } from 'vitest'
import { isBenignResolvedCancellation, isBenignResolvedWebkitAuthError, isBenignResolvedWebkitCancelledRead, isExpectedPendingEvidenceResponse, successfulGetPathsFrom, unexpectedWebkitPageErrors, webkitCancelledAuthPath, webkitCancelledXhrPath } from '../../e2e/requestFailurePolicy'

describe('browser request cancellation policy', () => {
  const successfulScriptPaths = new Set(['/src/pages/DashboardPage.jsx', '/src/components/CompetencyCharts.jsx'])
  const successfulReadPaths = new Set(['/api/v1/auth/me', '/api/v1/auth/oauth/providers'])
  const evidence = { successfulScriptPaths, successfulReadPaths, routeVerified: true }

  it('allows a cancelled Vite module only after the same module loaded and its route passed', () => {
    for (const path of ['/src/pages/DashboardPage.jsx', '/src/components/CompetencyCharts.jsx']) {
      expect(isBenignResolvedCancellation({ path, reason: 'Load request cancelled',
        resourceType: 'script', method: 'GET', isNavigationRequest: false }, evidence)).toBe(true)
    }
    expect(isBenignResolvedCancellation({ path: '/src/pages/HistoryPage.jsx', reason: 'Load request cancelled',
      resourceType: 'script', method: 'GET', isNavigationRequest: false }, evidence)).toBe(false)
  })

  it('allows a cancelled bundled font only after its route passed', () => {
    const font = { path: '/node_modules/@fontsource-variable/plus-jakarta-sans/files/plus-jakarta-sans-vietnamese-wght-normal.woff2',
      reason: 'Load request cancelled', resourceType: 'font', method: 'GET', isNavigationRequest: false }
    expect(isBenignResolvedCancellation(font, evidence)).toBe(true)
    expect(isBenignResolvedCancellation(font, { ...evidence, routeVerified: false })).toBe(false)
    expect(isBenignResolvedCancellation({ ...font, path: '/api/v1/admin/accounts' }, evidence)).toBe(false)
  })

  it('allows only a repeated optional auth read with a successful response', () => {
    expect(isBenignResolvedCancellation({ path: '/api/v1/auth/me', reason: 'Load request cancelled',
      resourceType: 'xhr', method: 'GET', isNavigationRequest: false }, evidence)).toBe(true)
    expect(isBenignResolvedCancellation({ path: '/api/v1/admin/accounts', reason: 'Load request cancelled',
      resourceType: 'xhr', method: 'GET', isNavigationRequest: false }, evidence)).toBe(false)
  })

  it('keeps unresolved, non-read, and top-level navigation failures fatal', () => {
    expect(isBenignResolvedCancellation({ path: '/src/pages/DashboardPage.jsx', reason: 'Load request cancelled',
      resourceType: 'script', method: 'GET', isNavigationRequest: false }, {
      ...evidence, successfulScriptPaths: new Set(),
    })).toBe(false)
    for (const record of [
      { path: '/api/v1/auth/me', reason: 'Load request cancelled', resourceType: 'xhr', method: 'POST', isNavigationRequest: false },
      { path: '/src/pages/DashboardPage.jsx', reason: 'net::ERR_CONNECTION_RESET', resourceType: 'script', method: 'GET', isNavigationRequest: false },
      { path: '/src/pages/DashboardPage.jsx', reason: 'Load request cancelled', resourceType: 'document', method: 'GET', isNavigationRequest: true },
    ]) expect(isBenignResolvedCancellation(record, evidence)).toBe(false)
    expect(isBenignResolvedCancellation({ path: '/src/components/CompetencyCharts.jsx', reason: 'Load request cancelled',
      resourceType: 'script', method: 'GET', isNavigationRequest: false }, { ...evidence, routeVerified: false })).toBe(false)
  })

  it('identifies only WebKit XHR abort errors for the two optional auth reads', () => {
    expect(webkitCancelledAuthPath({ message: '/127.0.0.1/api/v1/auth/me due to access control checks.',
      stack: 'XMLHttpRequest cannot load http://127.0.0.1/api/v1/auth/me due to access control checks.' })).toBe('/api/v1/auth/me')
    expect(webkitCancelledAuthPath({ message: 'TypeError: Failed to fetch', stack: 'fetch failed' })).toBeNull()
    expect(webkitCancelledAuthPath({ message: 'XMLHttpRequest cannot load /api/v1/admin/accounts due to access control checks.' })).toBeNull()
  })

  it('allows the matching WebKit auth page error only after the optional read and route both succeed', () => {
    const error = { message: '/127.0.0.1/api/v1/auth/oauth/providers due to access control checks.',
      stack: 'XMLHttpRequest cannot load http://127.0.0.1/api/v1/auth/oauth/providers due to access control checks.' }
    expect(isBenignResolvedWebkitAuthError(error, evidence)).toBe(true)
    expect(isBenignResolvedWebkitAuthError(error, { ...evidence, successfulReadPaths: new Set() })).toBe(false)
    expect(isBenignResolvedWebkitAuthError(error, { ...evidence, routeVerified: false })).toBe(false)
  })

  it('allows a navigation-cancelled WebKit read only after the same GET succeeded', () => {
    const error = { message: '/127.0.0.1/api/v1/sessions due to access control checks.',
      stack: 'XMLHttpRequest cannot load http://127.0.0.1/api/v1/sessions due to access control checks.' }
    expect(webkitCancelledXhrPath(error)).toBe('/api/v1/sessions')
    expect(isBenignResolvedWebkitCancelledRead(error, { successfulGetPaths: new Set(['/api/v1/sessions']), routeVerified: true })).toBe(true)
    expect(isBenignResolvedWebkitCancelledRead(error, { successfulGetPaths: new Set(['/api/v1/auth/me']), routeVerified: true })).toBe(false)
    expect(isBenignResolvedWebkitCancelledRead(error, { successfulGetPaths: new Set(['/api/v1/sessions']), routeVerified: false })).toBe(false)
    expect(isBenignResolvedWebkitCancelledRead({ message: 'TypeError: Failed to fetch', stack: '' },
      { successfulGetPaths: new Set(['/api/v1/sessions']), routeVerified: true })).toBe(false)
  })

  it('derives successful GET paths from diagnostics and filters only resolved cancellations', () => {
    const paths = successfulGetPathsFrom([
      { method: 'GET', path: '/api/v1/sessions', status: 200 },
      { method: 'POST', path: '/api/v1/sessions', status: 201 },
      { method: 'GET', path: '/api/v1/admin/accounts', status: 403 },
    ])
    expect([...paths]).toEqual(['/api/v1/sessions'])
    const artifact = { message: '/127.0.0.1/api/v1/sessions due to access control checks.',
      stack: 'XMLHttpRequest cannot load http://127.0.0.1/api/v1/sessions due to access control checks.' }
    expect(unexpectedWebkitPageErrors([artifact], { successfulGetPaths: paths, routeVerified: true })).toEqual([])
    expect(unexpectedWebkitPageErrors([artifact], { successfulGetPaths: paths, routeVerified: false })).toHaveLength(1)
    expect(unexpectedWebkitPageErrors([{ message: 'TypeError: x is undefined', stack: '' }],
      { successfulGetPaths: paths, routeVerified: true })).toHaveLength(1)
  })

  it('recognizes only the learner evidence pending-result privacy response', () => {
    expect(isExpectedPendingEvidenceResponse({ path: '/api/v1/sessions/42/evidence', status: 409, code: 'results_pending' })).toBe(true)
    expect(isExpectedPendingEvidenceResponse({ path: '/api/v1/sessions/42/evidence', status: 409, code: 'session_conflict' })).toBe(false)
    expect(isExpectedPendingEvidenceResponse({ path: '/api/v1/sessions/42/evidence', status: 500, code: 'results_pending' })).toBe(false)
    expect(isExpectedPendingEvidenceResponse({ path: '/api/v1/sessions/current/evidence', status: 409, code: 'results_pending' })).toBe(false)
    expect(isExpectedPendingEvidenceResponse({ path: '/api/v1/sessions/42/evidence/extra', status: 409, code: 'results_pending' })).toBe(false)
  })
})
