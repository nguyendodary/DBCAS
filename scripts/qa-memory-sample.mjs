// Diagnostic-only sampler for the QA provider container.
// Samples cgroup memory.current / memory.peak and PID 1 VmRSS every 5 s from
// before the suite starts until the launcher kills it. Never touches a test,
// an assertion, a timeout or a retry; all output goes to a separate file.
import { spawnSync } from 'node:child_process'
import fs from 'node:fs'

const [outFile, project, dockerJson] = process.argv.slice(2)
if (!outFile || !project || !dockerJson) throw new Error('usage: qa-memory-sample.mjs <out> <project> <docker-json>')
const { executable, prefix } = JSON.parse(dockerJson)

const fd = fs.openSync(outFile, 'w')
const write = (text) => { try { fs.writeSync(fd, `${text}\n`) } catch { /* best effort */ } }
write(`# start ${new Date().toISOString()} project=${project} interval_ms=5000`)

const compose = ['compose', '-p', project, '-f', 'docker-compose.local.yml', '-f', 'docker-compose.qa.yml']
const python = [
  'import os',
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

function run(args) {
  const r = spawnSync(executable, args, { encoding: 'utf8', windowsHide: true, timeout: 4000 })
  const text = `${r.stdout || ''}${r.stderr || ''}`.trim().replace(/\s+/g, ' ')
  return r.status === 0 ? text : `error(status=${r.status}) ${text}`
}

let timer = null
function sample() {
  const stamp = new Date().toISOString()
  const stats = run([...prefix, 'stats', '--no-stream',
    '--format', '{{.Name}}|{{.MemUsage}}|{{.MemPerc}}'])
  const cgroup = run([...compose, 'exec', '-T', 'qa-ai', 'python', '-c', python])
  write(`${stamp}\tstats=${stats}\tcgroup=${cgroup}`)
  timer = setTimeout(sample, 5000)
}

process.on('SIGTERM', () => {
  if (timer) clearTimeout(timer)
  write(`# end ${new Date().toISOString()}`)
  try { fs.closeSync(fd) } catch { /* best effort */ }
  process.exit(0)
})
sample()
