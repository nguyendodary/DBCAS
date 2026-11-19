// Reach the QA provider through the listener inside its own container.
// The published host port can stop forwarding mid-suite, and resolving the
// service alias from inside the app container can fail with EAI_AGAIN while
// the provider stays Healthy. The control POST is fixture setup, so use the
// provider's loopback listener directly: both paths above are indirect.
import { spawnSync } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = fileURLToPath(new URL('..', import.meta.url))

function dockerCommand() {
  if (process.platform !== 'win32') return { executable: 'docker', prefix: [] }
  const resolved =
    spawnSync('where.exe', ['docker'], {
      encoding: 'utf8',
      windowsHide: true,
    }).stdout?.split(/\r?\n/)[0] || ''
  if (resolved.toLowerCase().endsWith('.exe')) return { executable: resolved, prefix: [] }
  return { executable: 'wsl.exe', prefix: ['-e', 'docker'] }
}

function composeArgs(project) {
  return ['compose', '-p', project, '-f', 'docker-compose.local.yml', '-f', 'docker-compose.qa.yml']
}

function probe({ executable, prefix }, args, timeout = 3000) {
  return spawnSync(executable, [...prefix, ...args], {
    cwd: root,
    env: process.env,
    encoding: 'utf8',
    windowsHide: true,
    timeout,
  })
}

function describe(result) {
  return [
    result.error?.message,
    (result.stdout || '').trim() && `stdout: ${result.stdout.trim()}`,
    (result.stderr || '').trim() && `stderr: ${result.stderr.trim()}`,
  ].filter(Boolean).join(' | ') || `exit ${result.status}`
}

// Runs only after a failed control POST. Never touches the success path, so a
// healthy suite pays no extra cost. Every probe is bounded and failure of a
// probe is reported, never allowed to replace the original error.
function collectDiagnostics(project, docker, argv) {
  const lines = []
  const add = (label, result) => lines.push(`${label}: ${describe(result)}`)
  lines.push(`failing compose argv: ${JSON.stringify([docker.executable, ...argv])}`)
  const now = Date.now()
  const since = new Date(now - 5 * 60_000).toISOString()
  const until = new Date(now + 2_000).toISOString()
  try {
    add(
      'docker events (last 5m)',
      probe(docker, [
        'events', '--since', since, '--until', until,
        '--format', '{{.Time}} {{.Type}} {{.Action}} {{.Actor.Attributes.name}}',
      ]),
    )
    add(
      'app /etc/resolv.conf',
      probe(docker, [...composeArgs(project), 'exec', '-T', 'app', 'cat', '/etc/resolv.conf']),
    )
    add(
      "getaddrinfo('qa-ai') from app",
      probe(docker, [
        ...composeArgs(project), 'exec', '-T', 'app', 'python', '-c',
        'import socket; print(socket.getaddrinfo("qa-ai", 8080))',
      ]),
    )
    const appId = probe(docker, [...composeArgs(project), 'ps', '-q', 'app'])
    const providerId = probe(docker, [...composeArgs(project), 'ps', '-q', 'qa-ai'])
    for (const [label, idResult] of [['app', appId], ['qa-ai', providerId]]) {
      const id = (idResult.stdout || '').trim()
      if (id) add(`${label} networks`, probe(docker, ['inspect', '-f', '{{json .NetworkSettings.Networks}}', id]))
      else add(`${label} container id`, idResult)
    }
    const provider = (providerId.stdout || '').trim()
    if (provider) add('qa-ai logs (tail 50, by id)', probe(docker, ['logs', '--tail', '50', provider]))

    // Raw Docker view (no Compose service lookup) and inspection by the real
    // container name distinguish "not running" from "Compose cannot see it".
    const psFormat = '{{.ID}}\t{{.Names}}\t{{.Status}}\t{{.CreatedAt}}\t{{.Ports}}'
    add(
      `docker ps -a --filter name=${project}-qa-ai-1`,
      probe(docker, ['ps', '-a', '--no-trunc', '--filter', `name=${project}-qa-ai-1`, '--format', psFormat]),
    )
    add(
      `docker ps -a --filter name=${project}-app-1`,
      probe(docker, ['ps', '-a', '--no-trunc', '--filter', `name=${project}-app-1`, '--format', psFormat]),
    )
    const inspectFormat = [
      'status={{.State.Status}}',
      'started={{.State.StartedAt}}',
      'finished={{.State.FinishedAt}}',
      'exit={{.State.ExitCode}}',
      'oom={{.State.OOMKilled}}',
      'restarts={{.RestartCount}}',
      'labels={{json .Config.Labels}}',
    ].join(' ')
    add(
      `docker inspect ${project}-qa-ai-1`,
      probe(docker, ['inspect', '-f', inspectFormat, `${project}-qa-ai-1`]),
    )
    add(
      `docker logs --tail 50 ${project}-qa-ai-1`,
      probe(docker, ['logs', '--tail', '50', `${project}-qa-ai-1`]),
    )

    // Compare the exact -p/-f set used by the failing exec with the base-only
    // set, so an orphan/overlay mismatch cannot be mistaken for a dead provider.
    const fullCompose = composeArgs(project)
    const baseCompose = ['compose', '-p', project, '-f', 'docker-compose.local.yml']
    lines.push(`compose argv used by failing exec: ${JSON.stringify([docker.executable, ...argv])}`)
    lines.push(`compose argv base-only comparison: ${JSON.stringify([docker.executable, ...baseCompose, 'ps', '-a'])}`)
    const fullPs = probe(docker, [...fullCompose, 'ps', '-a'])
    const basePs = probe(docker, [...baseCompose, 'ps', '-a'])
    add('compose ps -a (full -p/-f set)', fullPs)
    add('compose ps -a (base-only -f set)', basePs)
    const fullText = `${fullPs.stdout || ''}${fullPs.stderr || ''}`
    const baseText = `${basePs.stdout || ''}${basePs.stderr || ''}`
    lines.push(
      `qa-ai visible: full-set=${/qa-ai/.test(fullText)} base-only=${/qa-ai/.test(baseText)} ` +
        `outputs-differ=${fullText !== baseText}`,
    )
  } catch (error) {
    lines.push(`diagnostics incomplete: ${error.message}`)
  }
  return lines
}

// Execute one POST inside the qa-ai container against its loopback listener.
// The payload is passed as a single argv element (no shell interpolation) and
// the provider's JSON response is returned to the caller.
export function postProviderControl(payload) {
  const project = process.env.DBCAS_LOCAL_PROJECT || 'dbcas-local'
  const docker = dockerCommand()
  const code = [
    'import sys,urllib.request',
    'req=urllib.request.Request("http://127.0.0.1:8080/control",',
    '  data=sys.argv[1].encode(), headers={"Content-Type":"application/json"})',
    'print(urllib.request.urlopen(req, timeout=15).read().decode())',
  ].join('\n')
  const args = [
    ...docker.prefix,
    ...composeArgs(project),
    'exec',
    '-T',
    'qa-ai',
    'python',
    '-c',
    code,
    JSON.stringify(payload),
  ]
  const result = spawnSync(docker.executable, args, {
    cwd: root,
    env: process.env,
    encoding: 'utf8',
    windowsHide: true,
  })
  if (result.error || result.status !== 0) {
    const detail = result.error?.message || result.stderr?.trim() || result.status
    const diagnostics = collectDiagnostics(project, docker, args)
    throw new Error(
      `Provider control via Compose failed: ${detail}` +
        (diagnostics.length
          ? `\n--- provider-control diagnostics (error-only) ---\n${diagnostics.join('\n')}`
          : ''),
    )
  }
  return JSON.parse(result.stdout.trim())
}
