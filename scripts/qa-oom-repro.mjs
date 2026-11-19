// Fast, focused reproduction for the qa-ai OOM.
// Starts ONLY the deterministic provider container at the requested memory
// limit, drives the same request shapes the AI-grading browser tests use, and
// samples cgroup memory.current / memory.peak every 5 s. Diagnostic only: it
// never touches the app stack, the test suite, an assertion or a CI gate.
import { spawnSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = fileURLToPath(new URL('..', import.meta.url))
const image = process.env.OOM_REPRO_IMAGE || 'dbcas-local-api:local'
const name = process.env.OOM_REPRO_NAME || 'dbcas-oom-repro'
const limit = process.env.OOM_REPRO_LIMIT || '128m'
const port = process.env.OOM_REPRO_PORT || '18099'
const minutes = Number(process.env.OOM_REPRO_MINUTES || '5')
const workers = Number(process.env.OOM_REPRO_WORKERS || '32')
const output = path.join(root, '_review', 'qa-oom-repro.log')
const base = `http://127.0.0.1:${port}`

fs.mkdirSync(path.dirname(output), { recursive: true })
const fd = fs.openSync(output, 'w')
const write = (text) => { try { fs.writeSync(fd, `${text}\n`) } catch { /* best effort */ } }

function docker(args, { allowFail = false } = {}) {
  const r = spawnSync('docker', args, { cwd: root, encoding: 'utf8', windowsHide: true, timeout: 120000 })
  if (!allowFail && (r.error || r.status !== 0)) {
    throw new Error(`docker ${args[0]} failed: ${r.error?.message || r.stderr?.trim() || r.status}`)
  }
  return r
}

function cgroup() {
  const script = [
    'def rd(p):',
    '    try: return open(p).read().strip()',
    '    except Exception: return "NA"',
    'rss="NA"',
    'try:',
    '    for line in open("/proc/1/status"):',
    '        if line.startswith("VmRSS:"): rss=line.split()[1]',
    'except Exception: pass',
    'print("current=%s peak=%s max=%s VmRSS_kB=%s" % (',
    '    rd("/sys/fs/cgroup/memory.current"), rd("/sys/fs/cgroup/memory.peak"),',
    '    rd("/sys/fs/cgroup/memory.max"), rss))',
  ].join('\n')
  const r = docker(['exec', name, 'python', '-c', script], { allowFail: true })
  return `${r.stdout || ''}${r.stderr || ''}`.trim().replace(/\s+/g, ' ') || 'unavailable'
}

function state() {
  const r = docker(['inspect', '-f', '{{.State.Status}} oom={{.State.OOMKilled}} exit={{.State.ExitCode}}', name], { allowFail: true })
  return `${r.stdout || ''}${r.stderr || ''}`.trim()
}

// Same shapes the browser QA suite sends: 13-question AI generation for the
// four practice concepts, a full bank-practice evaluation snapshot, and an
// essay grading prompt. Sizes are representative, not minimal.
const concepts = [{
  id: '3f1c4a52-1f7e-4c1e-9c3a-000000000001', code: 'ER',
  name: 'ER modeling', description: 'Entities, relationships and cardinality',
}]
const items = Array.from({ length: 13 }, (_, index) => ({
  attempt_id: `attempt-${index}`, question_id: `question-${index}`,
  type: ['mcq', 'sql', 'essay'][index % 3], points: 1, score: index % 4 === 0 ? 0.25 : 1,
  clo: ['CLO1'], topics: ['ER modeling'], difficulty: 'HARD',
  answer_text: `learner answer ${index} `.repeat(200),
}))
const evaluationData = JSON.stringify({
  items, attempt_count: 3,
  history: [{ percentage: 40 }, { percentage: 50 }, { percentage: 60 }],
  dimensions: {
    clo: [{ label: 'CLO1', earned: '5', possible: '13', percentage: 38.5 }],
    topic: [{ label: 'ER modeling', earned: '5', possible: '13', percentage: 38.5 }],
    difficulty: [{ label: 'HARD', earned: '5', possible: '13', percentage: 38.5 }],
  },
  recurring_weaknesses: [],
})
const payloads = {
  evaluation: {
    response_format: { json_schema: { name: 'evaluation' } },
    messages: [{ role: 'user', content: `## DỮ LIỆU\n${evaluationData}\n## KHÁI NIỆM\n[]\n## RUBRIC\n` }],
  },
  practice_questions: {
    response_format: { json_schema: { name: 'practice_questions' } },
    messages: [{ role: 'user', content: JSON.stringify({
      concepts, difficulty_levels: [4], count: 3,
      type_counts: { mcq: 1, sql: 1, essay: 1 },
    }) }],
  },
  essay_grade: {
    response_format: { json_schema: { name: 'essay_grade' } },
    messages: [{ role: 'user', content: `- Complete: score 0.70 to 0.80\nSTUDENT ANSWER (identifiers redacted):\n${'repro answer '.repeat(400)}\n\nReturn JSON:` }],
  },
}
const kinds = Object.keys(payloads)

let stop = false
const statusCounts = {}
async function worker(index) {
  while (!stop) {
    const kind = kinds[index % kinds.length]
    try {
      const response = await fetch(`${base}/v1/chat/completions`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payloads[kind]), signal: AbortSignal.timeout(10000),
      })
      await response.arrayBuffer()
      const key = `${kind}:${response.status}`
      statusCounts[key] = (statusCounts[key] || 0) + 1
    } catch {
      statusCounts[`${kind}:error`] = (statusCounts[`${kind}:error`] || 0) + 1
    }
    await new Promise((resolve) => setTimeout(resolve, 5))
  }
}

write(`# start ${new Date().toISOString()} image=${image} limit=${limit} workers=${workers} minutes=${minutes}`)
docker(['rm', '-f', name], { allowFail: true })
docker(['build', '-f', 'backend/Dockerfile', '-t', image, '.'])
docker([
  'run', '-d', '--name', name, '--memory', limit,
  '-p', `127.0.0.1:${port}:8080`,
  '-e', 'PYTHONPATH=/srv/DBCAS/backend',
  '-v', `${path.join(root, 'backend/tests/qa_provider.py')}:/qa/provider.py:ro`,
  image, 'python', '/qa/provider.py',
])

const deadline = Date.now() + minutes * 60_000
let healthy = false
for (let i = 0; i < 60 && !healthy; i++) {
  try {
    const r = await fetch(`${base}/health`, { signal: AbortSignal.timeout(1500) })
    healthy = r.ok
  } catch { /* not up yet */ }
  if (!healthy) await new Promise((resolve) => setTimeout(resolve, 500))
}
write(`# health ${healthy ? 'ready' : 'timeout'} at ${new Date().toISOString()}`)
try {
  await fetch(`${base}/control`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ delay_seconds: 0.02, failure: false, hold: false }),
  })
} catch { /* recorded through health */ }

const loops = Array.from({ length: workers }, (_, i) => worker(i))
let oom = false
while (Date.now() < deadline && !oom) {
  write(`${new Date().toISOString()}\tstate=${state()}\tcgroup=${cgroup()}`)
  const s = state()
  if (s.includes('exited') || s.includes('dead')) {
    oom = s.includes('oom=true')
    write(`# container stopped: ${s}`)
    break
  }
  await new Promise((resolve) => setTimeout(resolve, 5000))
}
stop = true
await Promise.allSettled(loops)
write(`# responses ${JSON.stringify(statusCounts)}`)
write(`# end ${new Date().toISOString()} oom=${oom}`)
try { fs.closeSync(fd) } catch { /* best effort */ }
docker(['rm', '-f', name], { allowFail: true })
console.log(`qa-oom-repro: limit=${limit} oom=${oom} output=${output}`)
