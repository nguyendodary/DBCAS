const browserAbortReasons = new Set([
  'NS_BINDING_ABORTED',
  'net::ERR_ABORTED',
  'cancelled',
  'Cancelled',
  'Load request cancelled',
])

const optionalAuthReads = new Set([
  '/api/v1/auth/me',
  '/api/v1/auth/oauth/providers',
])

export function isExpectedPendingEvidenceResponse({ path, status, code }) {
  return status === 409 && /^\/api\/v1\/sessions\/\d+\/evidence$/.test(path) && code === 'results_pending'
}

// Vite's HMR client reconnects when Chromium momentarily exhausts socket
// buffers during the long serial tours. The application itself uses no
// WebSocket; every HTTP module/API load is asserted separately.
export function isBenignDevServerSocketError(message) {
  return /^WebSocket connection to 'ws:\/\/127\.0\.0\.1:5174\/\?token=[^']+' failed: Error in connection establishment: net::ERR_NO_BUFFER_SPACE$/.test(message)
}

export function isBenignResolvedCancellation(record, {
  successfulScriptPaths = new Set(),
  successfulReadPaths = new Set(),
  successfulGetPaths = new Set(),
  routeVerified = false,
} = {}) {
  if (!routeVerified || record.isNavigationRequest || !browserAbortReasons.has(record.reason)) return false

  // A GET cancelled mid-flight by a document teardown/navigation is benign when
  // the identical resource demonstrably loaded successfully elsewhere in the
  // tour — this covers static assets (e.g. images re-requested after a full
  // reload) as well as API reads superseded by a refetch.
  if (record.method === 'GET' && successfulGetPaths.has(record.path)) return true

  const isViteModule = record.resourceType === 'script' &&
    (record.path.startsWith('/src/pages/') || record.path.startsWith('/src/components/') ||
      record.path.startsWith('/node_modules/.vite/deps/'))
  if (isViteModule) return successfulScriptPaths.has(record.path)

  // WebKit cancels a bundled font subset mid-flight when a locale switch
  // removes the glyphs that needed it; the page already rendered correctly.
  if (record.resourceType === 'font' && record.method === 'GET' &&
      record.path.startsWith('/node_modules/@fontsource-variable/')) return true

  return record.reason === 'Load request cancelled' && record.method === 'GET' &&
    optionalAuthReads.has(record.path) && successfulReadPaths.has(record.path)
}

export function webkitCancelledAuthPath(error) {
  const message = `${error?.message ?? ''}\n${error?.stack ?? ''}`
  if (!message.includes('XMLHttpRequest cannot load') || !message.includes('due to access control checks.')) return null
  return message.match(/\/api\/v1\/auth\/(?:me|oauth\/providers)/)?.[0] ?? null
}

export function isBenignResolvedWebkitAuthError(error, { successfulReadPaths = new Set(), routeVerified = false } = {}) {
  const path = webkitCancelledAuthPath(error)
  return Boolean(path && routeVerified && optionalAuthReads.has(path) && successfulReadPaths.has(path))
}

export function webkitCancelledXhrPath(error) {
  const message = `${error?.message ?? ''}\n${error?.stack ?? ''}`
  if (!message.includes('XMLHttpRequest cannot load') || !message.includes('due to access control checks.')) return null
  return message.match(/\/api\/v1\/[A-Za-z0-9_/-]+/)?.[0] ?? null
}

// WebKit reports an XHR cancelled by navigation as a page error. Accept it only
// when the identical GET path loaded successfully elsewhere in the same test.
export function isBenignResolvedWebkitCancelledRead(error, { successfulGetPaths = new Set(), routeVerified = false } = {}) {
  const path = webkitCancelledXhrPath(error)
  return Boolean(path && routeVerified && successfulGetPaths.has(path))
}

export function successfulGetPathsFrom(responses) {
  return new Set(responses
    .filter(record => record.method === 'GET' && record.status < 400)
    .map(record => record.path))
}

export function unexpectedWebkitPageErrors(errors, { successfulGetPaths = new Set(), routeVerified = false } = {}) {
  return errors.filter(error => !isBenignResolvedWebkitCancelledRead(error, { successfulGetPaths, routeVerified }))
}
