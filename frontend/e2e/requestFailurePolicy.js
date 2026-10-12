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

export function isBenignResolvedCancellation(record, {
  successfulScriptPaths = new Set(),
  successfulReadPaths = new Set(),
  routeVerified = false,
} = {}) {
  if (!routeVerified || record.isNavigationRequest || !browserAbortReasons.has(record.reason)) return false

  const isViteModule = record.resourceType === 'script' &&
    (record.path.startsWith('/src/pages/') || record.path.startsWith('/node_modules/.vite/deps/'))
  if (isViteModule) return successfulScriptPaths.has(record.path)

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
