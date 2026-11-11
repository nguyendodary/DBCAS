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

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try { await waitForFrontend(process.argv[2]) }
  catch (error) { console.error(error.message); process.exitCode = 1 }
}
