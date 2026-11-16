import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { setTimeout as sleep } from 'node:timers/promises'

// Compose can retain an old healthy flag while Nginx resolves a replaced API.
// Probe the actual public path before reporting startup complete or opening a browser.
export async function waitForFrontend(url, { timeoutMs = 45000, requestTimeoutMs = 2500, pollMs = 200 } = {}) {
  const deadline = performance.now() + timeoutMs
  while (performance.now() < deadline) {
    try {
      const remaining = Math.max(1, Math.ceil(deadline - performance.now()))
      const response = await fetch(url, { cache: 'no-store', signal: AbortSignal.timeout(Math.min(requestTimeoutMs, remaining)) })
      if (response.status === 200) {
        const data = await response.json()
        const dependencies = data?.dependencies && Object.values(data.dependencies)
        if (data?.status === 'ready' && dependencies?.length && dependencies.every(value => value === true)) return
      } else await response.body?.cancel()
    } catch { /* A stale upstream, incomplete body or connection failure is not readiness. */ }
    const remaining = deadline - performance.now()
    if (remaining > 0) await sleep(Math.min(pollMs, remaining))
  }
  throw new Error('Ứng dụng chưa sẵn sàng qua proxy. Kiểm tra Docker rồi chạy lại npm start.')
}

// The QA provider's Compose healthcheck probes 127.0.0.1:8080 *inside* the
// container and can pass before the published host port accepts connections.
// Verify the public path before any browser client (or the control POST) uses it.
export async function waitForProvider(url, { timeoutMs = 45000, requestTimeoutMs = 2500, pollMs = 200 } = {}) {
  const deadline = performance.now() + timeoutMs
  while (performance.now() < deadline) {
    try {
      const remaining = Math.max(1, Math.ceil(deadline - performance.now()))
      const response = await fetch(`${url}/health`, { cache: 'no-store', signal: AbortSignal.timeout(Math.min(requestTimeoutMs, remaining)) })
      if (response.ok) {
        const data = await response.json()
        if (data && typeof data.calls === 'number' && 'peak_active' in data) return data
      } else await response.body?.cancel()
    } catch { /* A refused host port or incomplete body is not readiness. */ }
    const remaining = deadline - performance.now()
    if (remaining > 0) await sleep(Math.min(pollMs, remaining))
  }
  throw new Error(`QA provider chưa sẵn sàng qua cổng host: ${url}`)
}

// Bounded retry for the launcher's own control command. The provider stays up
// for the whole suite; this covers only the transient host-port race above.
export async function postWithRetry(url, body, { attempts = 5, retryMs = 250, requestTimeoutMs = 5000 } = {}) {
  let lastError
  for (let attempt = 1; attempt <= attempts; attempt++) {
    try {
      const response = await fetch(url, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body), signal: AbortSignal.timeout(requestTimeoutMs),
      })
      if (response.ok) return response
      lastError = new Error(`HTTP ${response.status}`)
      await response.body?.cancel()
    } catch (error) { lastError = error }
    if (attempt < attempts) await sleep(retryMs)
  }
  throw new Error(`Không gửi được lệnh điều khiển tới QA provider: ${lastError?.message || 'unknown'}`)
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try { await waitForFrontend(process.argv[2]) }
  catch (error) { console.error(error.message); process.exitCode = 1 }
}
