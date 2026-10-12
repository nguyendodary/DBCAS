import { describe, expect, it } from 'vitest'
import { isBenignResolvedCancellation, isBenignResolvedWebkitAuthError, webkitCancelledAuthPath } from '../../e2e/requestFailurePolicy'

describe('WebKit request cancellation classification', () => {
  const successfulScriptPaths = new Set(['/src/pages/DashboardPage.jsx'])
  const successfulReadPaths = new Set(['/api/v1/auth/me', '/api/v1/auth/oauth/providers'])
  const evidence = { successfulScriptPaths, successfulReadPaths, routeVerified: true }

  it('allows a cancelled Vite module only after the same module loaded and its route passed', () => {
    expect(isBenignResolvedCancellation({ path: '/src/pages/DashboardPage.jsx', reason: 'Load request cancelled',
      resourceType: 'script', method: 'GET', isNavigationRequest: false }, evidence)).toBe(true)
    expect(isBenignResolvedCancellation({ path: '/src/pages/HistoryPage.jsx', reason: 'Load request cancelled',
      resourceType: 'script', method: 'GET', isNavigationRequest: false }, evidence)).toBe(false)
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
      successfulScriptPaths: new Set(), successfulReadPaths, routeVerified: true,
    })).toBe(false)
    for (const record of [
      { path: '/api/v1/auth/me', reason: 'Load request cancelled', resourceType: 'xhr', method: 'POST', isNavigationRequest: false },
      { path: '/src/pages/DashboardPage.jsx', reason: 'net::ERR_CONNECTION_RESET', resourceType: 'script', method: 'GET', isNavigationRequest: false },
      { path: '/src/pages/DashboardPage.jsx', reason: 'Load request cancelled', resourceType: 'document', method: 'GET', isNavigationRequest: true },
    ]) expect(isBenignResolvedCancellation(record, evidence)).toBe(false)
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
})
