// Compatibility entry point: the documented `node scripts/render_diagrams.mjs` command now
// delegates to scripts/diagrams.mjs so there is exactly one DOT/SVG implementation to keep
// honest. Forward an argument to choose the mode; the default stays "render".
import { spawnSync } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const mode = process.argv[2] ?? 'render'
const result = spawnSync(process.execPath, [path.join(root, 'scripts', 'diagrams.mjs'), mode],
  { cwd: root, stdio: 'inherit' })
process.exit(result.status ?? 1)
