import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
const root = fileURLToPath(new URL('..', import.meta.url))
let executable = 'docker', prefix = [], mount = path.join(root, 'ai')
if (process.platform === 'win32') {
  const resolved = spawnSync('where.exe', ['docker'], { encoding: 'utf8', windowsHide: true }).stdout?.split(/\r?\n/)[0] || ''
  if (resolved.toLowerCase().endsWith('.exe')) executable = resolved
  else {
    executable = 'wsl.exe'
    prefix = ['-e', 'docker']
    const converted = spawnSync('wsl.exe', ['-e', 'wslpath', '-a', mount], { encoding: 'utf8', windowsHide: true })
    if (converted.status !== 0) process.exit(1)
    mount = converted.stdout.trim()
  }
}
function run(args) {
  const r = spawnSync(executable, [...prefix, ...args], { cwd: root, stdio: 'inherit', windowsHide: true })
  if (r.error || r.status !== 0) process.exit(r.status || 1)
}
run(['build', '-t', 'dbcas-ai-training:local', '-f', 'ai/Dockerfile', '.'])
run(['run', '--rm', '-v', `${mount}:/workspace/ai`, 'dbcas-ai-training:local', 'all', ...process.argv.slice(2)])
