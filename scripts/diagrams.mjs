#!/usr/bin/env node
// DBCAS diagrams-as-code entry point.
//
//   check   Discover every diagram source, re-render it into a scratch directory and report
//           any committed SVG that no longer matches its source. Writes nothing in the repo.
//   render  Discover, validate, then write the committed SVGs and the render manifest.
//   setup   Report pinned versions and prerequisites; fetch the pinned PlantUML jar on
//           demand into the gitignored tools/ directory and verify its SHA-256 digest.
//
// Sources: docs/diagrams/*.dot (Graphviz), ```mermaid fences in project Markdown,
// docs/diagrams/sources/*.mmd and docs/diagrams/sources/*.puml.
// Failures name the source file and exit non-zero. Rendering never downloads a browser and
// never passes a flag that weakens the Chromium sandbox.
import { execFile } from 'node:child_process'
import { createHash } from 'node:crypto'
import { promisify } from 'node:util'
import { existsSync, readdirSync } from 'node:fs'
import { mkdir, mkdtemp, readFile, readdir, rm, writeFile } from 'node:fs/promises'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { pythonCommand, scriptArgs } from './python.mjs'

const run = promisify(execFile)
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const DIAGRAMS = path.join(ROOT, 'docs', 'diagrams')
const RENDERED = path.join(DIAGRAMS, 'rendered')
const SOURCES = path.join(DIAGRAMS, 'sources')
const CACHE = path.join(ROOT, 'node_modules', '.cache', 'dbcas-diagrams')
const MERMAID_CLI = path.join(ROOT, 'node_modules', '@mermaid-js', 'mermaid-cli', 'src', 'cli.js')
const VIZ_MODULE = path.join(ROOT, 'node_modules', '@viz-js', 'viz', 'dist', 'viz.js')
const MANIFEST = path.join(RENDERED, 'manifest.json')

// Last PlantUML line that runs on this machine's JRE 1.8. The jar is never committed;
// this digest is what a fetched jar must match before it is used.
const PLANTUML_VERSION = '1.2023.13'
const PLANTUML_URL = `https://github.com/plantuml/plantuml/releases/download/v${PLANTUML_VERSION}/plantuml-${PLANTUML_VERSION}.jar`
const PLANTUML_SHA256 = 'e68a770f8fd386ca6787589ffd70741303187ee214a075ee85a444fcd8a6da59'
const PLANTUML_JAR = path.join(ROOT, 'tools', `plantuml-${PLANTUML_VERSION}.jar`)

const repoPath = (file) => path.relative(ROOT, file).replaceAll('\\', '/')
const sha256 = (data) => createHash('sha256').update(data).digest('hex')
const readIf = async (file) => { try { return await readFile(file, 'utf8') } catch { return null } }
const tail = (error) => `${error.stderr || ''}${error.stdout || ''}${error.message || ''}`
  .split(/\r?\n/).filter(Boolean).slice(-8).join('\n  ')
// Committed SVGs are compared ignoring line endings and blank lines. Mermaid's ER renderer
// redraws relationship curves with randomised control points on every run, so a non-DOT
// comparison ignores path geometry and matches everything else exactly: element structure,
// identifiers, transforms, styles and all label text. The render manifest keeps the exact
// source-text digest, so a cardinality or wording change is still caught.
const skeleton = (svg) => svg.replace(/ d="[^"]*"/g, ' d="X"')
const matches = (committed, rendered, tolerant = false) => {
  if (committed === null) return false
  const clean = (text) => { const trimmed = text.replace(/\r\n/g, '\n').trim(); return tolerant ? skeleton(trimmed) : trimmed }
  return clean(committed) === clean(rendered)
}

const SKIP_DIRS = new Set(['node_modules', '.git', '__pycache__', 'dist', 'build', 'rendered', 'tools', '_review', 'output'])
async function walk(dir, out = []) {
  let entries = []
  try { entries = await readdir(dir, { withFileTypes: true }) } catch { return out }
  for (const entry of entries) {
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      if (!SKIP_DIRS.has(entry.name) && !entry.name.endsWith('.venv')) await walk(full, out)
    } else out.push(full)
  }
  return out
}

const slug = (value) => value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'diagram'

// Extract fenced Mermaid blocks, attributing each to its file and opening line.
function fences(markdown, origin) {
  const lines = markdown.split(/\r?\n/)
  const found = []
  let open = null
  let heading = 'diagram'
  lines.forEach((line, index) => {
    if (!open && /^\s*```\s*mermaid\s*$/.test(line)) { open = { start: index + 1, body: [] }; return }
    if (open && /^\s*```\s*$/.test(line)) {
      found.push({ kind: 'mermaid', origin: `${origin}:${open.start}`, label: slug(`${path.basename(origin, '.md')}--${heading}`), text: `${open.body.join('\n')}\n` })
      open = null
      return
    }
    if (!open && /^#{1,6}\s+/.test(line)) heading = line.replace(/^#+\s*/, '')
    if (open) open.body.push(line)
  })
  if (open) throw new Error(`${origin}:${open.start} unterminated Mermaid fence`)
  return found
}

function dedupe(sources) {
  const seen = new Map()
  for (const source of sources) {
    seen.set(source.label, (seen.get(source.label) || 0) + 1)
    if (seen.get(source.label) > 1) source.label = `${source.label}-${seen.get(source.label)}`
  }
  if (new Set(sources.map((item) => item.label)).size !== sources.length) throw new Error('duplicate diagram labels after de-duplication')
  return sources
}

async function discover() {
  const markdown = (await walk(path.join(ROOT, 'docs'))).filter((file) => file.endsWith('.md'))
  if (existsSync(path.join(ROOT, 'README.md'))) markdown.push(path.join(ROOT, 'README.md'))
  const mermaid = []
  const problems = []
  for (const file of markdown.sort()) {
    try { mermaid.push(...fences(await readFile(file, 'utf8'), repoPath(file))) } catch (error) { problems.push(error.message) }
  }
  const plantuml = []
  for (const name of (await readdir(SOURCES).catch(() => [])).sort()) {
    const extension = path.extname(name)
    const origin = `docs/diagrams/sources/${name}`
    const text = await readFile(path.join(SOURCES, name), 'utf8')
    if (extension === '.mmd') mermaid.push({ kind: 'mermaid', origin, label: slug(path.basename(name, '.mmd')), text })
    else if (extension === '.puml' || extension === '.iuml') plantuml.push({ kind: 'plantuml', origin, label: slug(path.basename(name, extension)), text })
  }
  const dot = []
  for (const name of (await readdir(DIAGRAMS).catch(() => [])).sort()) {
    if (!name.endsWith('.dot')) continue
    dot.push({ kind: 'dot', origin: `docs/diagrams/${name}`, label: slug(path.basename(name, '.dot')), text: await readFile(path.join(DIAGRAMS, name), 'utf8') })
  }
  return { dot: dedupe(dot), mermaid: dedupe(mermaid), plantuml: dedupe(plantuml), problems }
}

// --- rendering -------------------------------------------------------------

let vizPromise = null
function vizGraph() {
  if (!vizPromise) {
    const custom = process.env.DBCAS_VIZ_MODULE
    const specifier = custom ? (custom.startsWith('file:') ? custom : pathToFileURL(path.resolve(custom)).href) : pathToFileURL(VIZ_MODULE).href
    vizPromise = import(specifier).then((module) => module.instance())
  }
  return vizPromise
}

// Keep DOT decoration byte-identical to the long-standing render_diagrams.mjs output.
const accessible = (svg, label) => /role="img"/.test(svg) ? svg : svg.replace('<svg ', `<svg role="img" aria-label="DBCAS ${label} diagram" `)

async function renderDot(source) {
  const viz = await vizGraph()
  const result = viz.render(source.text, { format: 'svg', engine: 'dot' })
  if (result.status !== 'success' || result.errors.length) throw new Error(`${source.origin}: Graphviz rejected the source: ${JSON.stringify(result.errors)}`)
  return accessible(result.output, source.label)
}

function findBrowser(dir, depth = 6, out = []) {
  if (depth < 0 || out.length > 40) return out
  let entries = []
  try { entries = readdirSync(dir, { withFileTypes: true }) } catch { return out }
  for (const entry of entries) {
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) findBrowser(full, depth - 1, out)
    else if (/^(chrome|chrome-headless-shell|chromium|headless_shell|msedge)(\.exe)?$/i.test(entry.name)) out.push(full)
  }
  return out
}

// An installed Chromium-family browser only: nothing is downloaded and the sandbox
// is never disabled to make rendering work.
function browserPath() {
  const override = process.env.DBCAS_CHROME_PATH
  if (override) {
    if (!existsSync(override)) throw new Error(`DBCAS_CHROME_PATH does not exist: ${override}`)
    return override
  }
  const roots = [process.env['PROGRAMFILES(X86)'], process.env.PROGRAMW6432, process.env.LOCALAPPDATA,
    'C:\\Program Files (x86)', 'C:\\Program Files'].filter(Boolean)
  const candidates = []
  for (const root of roots) candidates.push(path.join(root, 'Microsoft', 'Edge', 'Application', 'msedge.exe'),
    path.join(root, 'Google', 'Chrome', 'Application', 'chrome.exe'))
  candidates.push('/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
  for (const candidate of candidates) if (existsSync(candidate)) return candidate
  for (const base of [path.join(os.homedir(), '.cache', 'puppeteer'), path.join(ROOT, 'node_modules', '.cache', 'puppeteer')]) {
    const found = findBrowser(base)
    if (found.length) return found.sort()[0]
  }
  return null
}

async function puppeteerConfig() {
  const executablePath = browserPath()
  if (!executablePath) throw new Error('no installed Chrome/Edge/Chromium found (set DBCAS_CHROME_PATH); refusing to download a browser or weaken the sandbox')
  await mkdir(CACHE, { recursive: true })
  const file = path.join(CACHE, 'puppeteer-config.json')
  await writeFile(file, `${JSON.stringify({ executablePath, headless: true, args: [] }, null, 2)}\n`)
  return file
}

async function renderMermaid(source, scratch, config) {
  const input = path.join(scratch, `${source.label}.mmd`)
  const output = path.join(scratch, `${source.label}.svg`)
  await writeFile(input, source.text)
  try {
    await run(process.execPath, [MERMAID_CLI, '-i', input, '-o', output, '-p', config],
      { cwd: ROOT, timeout: 240000, maxBuffer: 32 * 1024 * 1024 })
  } catch (error) {
    throw new Error(`${source.origin}: Mermaid could not render\n  ${tail(error)}`)
  }
  const svg = await readIf(output)
  if (svg === null) throw new Error(`${source.origin}: Mermaid produced no SVG output`)
  return svg
}

// PlantUML stamps a generation time into its SVG; drift checks must ignore that line.
const stripTimestamps = (svg) => svg.replace(/<!--\s*Started on[^\n]*-->\s*/g, '').replace(/<dc:date>[^<]*<\/dc:date>/g, '')

async function renderPlantUML(source, scratch) {
  const input = path.join(scratch, `${source.label}.puml`)
  await writeFile(input, source.text)
  try {
    await run('java', ['-jar', PLANTUML_JAR, '-tsvg', `-o${scratch.replaceAll('\\', '/')}`, input],
      { cwd: ROOT, timeout: 240000, maxBuffer: 16 * 1024 * 1024 })
  } catch (error) {
    throw new Error(`${source.origin}: PlantUML could not render\n  ${tail(error)}`)
  }
  const svg = await readIf(path.join(scratch, `${source.label}.svg`))
  if (svg === null) throw new Error(`${source.origin}: PlantUML produced no SVG output`)
  return accessible(stripTimestamps(svg), source.label)
}

async function checkPlantUMLSyntax(source, scratch) {
  const file = path.join(scratch, `${source.label}.checkonly.puml`)
  await writeFile(file, source.text)
  try { await run('java', ['-jar', PLANTUML_JAR, '-checkonly', file], { cwd: ROOT, timeout: 120000 }) }
  catch (error) { throw new Error(`${source.origin}: PlantUML syntax is invalid\n  ${tail(error)}`) }
  finally { await rm(file, { force: true }) }
}

// --- validation of the ledger-backed models ---------------------------------


async function compareAndWrite(svg, committed, source, manifest, write, problems) {
  manifest[repoPath(committed)] = { source: source.origin, sha256: sha256(source.text), generator: source.kind }
  if (write) {
    await mkdir(path.dirname(committed), { recursive: true })
    await writeFile(committed, svg)
    return true
  }
  const existing = await readIf(committed)
  if (existing === null) { problems.push(`${source.origin}: committed SVG is missing (${repoPath(committed)})`); return false }
  if (!matches(existing, svg, source.kind !== 'dot')) {
    problems.push(`${source.origin}: committed SVG no longer matches the source; run npm run diagrams:render`)
    return false
  }
  return true
}

async function gate(write) {
  const { dot, mermaid, plantuml, problems } = await discover()
  const scratch = await mkdtemp(path.join(os.tmpdir(), 'dbcas-diagrams-'))
  const manifest = {}
  let healthy = 0
  try {
    for (const source of dot) {
      try {
        const svg = await renderDot(source)
        if (await compareAndWrite(svg, path.join(DIAGRAMS, `${source.label}.svg`), source, manifest, write, problems)) healthy += 1
      } catch (error) { problems.push(error.message) }
    }

    if (mermaid.length) {
      let config = null
      try { config = await puppeteerConfig() } catch (error) { problems.push(error.message) }
      for (const source of mermaid) {
        if (!config) break
        try {
          const svg = await renderMermaid(source, scratch, config)
          if (await compareAndWrite(svg, path.join(RENDERED, `${source.label}.svg`), source, manifest, write, problems)) healthy += 1
        } catch (error) { problems.push(error.message) }
      }
    }

    if (!plantuml.length) console.log('SKIP: PlantUML - no docs/diagrams/sources/*.puml source exists yet (the gate stays wired for one)')
    else if (!existsSync(PLANTUML_JAR)) problems.push(`PlantUML: ${repoPath(PLANTUML_JAR)} is missing; run npm run diagrams:setup`)
    else {
      for (const source of plantuml) {
        try {
          await checkPlantUMLSyntax(source, scratch)
          const svg = await renderPlantUML(source, scratch)
          const committed = path.join(RENDERED, `${source.label}.svg`)
          if (await compareAndWrite(svg, committed, source, manifest, write, problems)) healthy += 1
        } catch (error) { problems.push(error.message) }
      }
    }
  } finally { await rm(scratch, { recursive: true, force: true }) }

  const rendered = Object.fromEntries(Object.entries(manifest).sort(([a], [b]) => (a < b ? -1 : 1)))
  if (write) {
    await mkdir(RENDERED, { recursive: true })
    await writeFile(MANIFEST, `${JSON.stringify({ note: 'Generated by npm run diagrams:render. Records each committed SVG source and the digest of its source text; counts are evidence, not quality targets.', renders: rendered }, null, 2)}\n`)
  } else {
    const committed = await readIf(MANIFEST)
    if (committed === null) problems.push('docs/diagrams/rendered/manifest.json is missing; run npm run diagrams:render')
    else {
      let parsed = null
      try { parsed = JSON.parse(committed).renders } catch { /* treated as drift below */ }
      if (JSON.stringify(parsed) !== JSON.stringify(rendered)) problems.push('docs/diagrams/rendered/manifest.json does not match the discovered sources; run npm run diagrams:render')
    }
  }

  const python = await pythonCommand()
  if (!python) problems.push('no Python interpreter found for scripts/validate_diagrams.py (set DBCAS_TEST_PYTHON)')
  else {
    try {
      const output = await run(python, scriptArgs(python, path.join(ROOT, 'scripts', 'validate_diagrams.py')), { cwd: ROOT })
      for (const line of output.stdout.trim().split(/\r?\n/)) console.log(line)
      healthy += 1
    } catch (error) { problems.push(`scripts/validate_diagrams.py failed\n  ${tail(error)}`) }
  }

  if (problems.length) {
    for (const problem of problems) console.error(`FAIL: ${problem}`)
    console.error(`${problems.length} problem(s); ${healthy} check(s) healthy`)
    process.exitCode = 1
    return
  }
  console.log(`${write ? 'rendered' : 'checked'} ${dot.length} Graphviz DOT, ${mermaid.length} Mermaid and ${plantuml.length} PlantUML source(s); ledger and DDL validation passed`)
}

// --- setup report ----------------------------------------------------------

async function has(command, args) { try { await run(command, args); return true } catch { return false } }

async function setup() {
  const pinned = JSON.parse(await readFile(path.join(ROOT, 'package.json'), 'utf8')).devDependencies
  const report = [`node ${process.versions.node}  (${process.execPath})`]
  for (const name of Object.keys(pinned).sort()) {
    let installed = null
    try { installed = JSON.parse(await readFile(path.join(ROOT, 'node_modules', name, 'package.json'), 'utf8')).version } catch { /* absent */ }
    report.push(`${name}: pinned ${pinned[name]}, installed ${installed ?? 'NOT INSTALLED - run npm ci'}`)
  }
  report.push(existsSync(path.join(ROOT, 'package-lock.json')) ? 'package-lock.json: present (npm ci reproduces this toolchain)' : 'package-lock.json: MISSING')
  let browser = null
  try { browser = browserPath() } catch (error) { report.push(`browser: ${error.message}`) }
  report.push(browser ? `browser: ${browser} (driven through Puppeteer; sandbox left enabled)` : 'browser: none found - set DBCAS_CHROME_PATH')
  report.push(`graphviz dot: ${await has('dot', ['-V']) ? 'on PATH' : 'not on PATH (not required; @viz-js/viz is a JavaScript Graphviz build)'}`)
  let java = 'not on PATH'
  try { java = (await run('java', ['-version'])).stderr.trim().split(/\r?\n/)[0] } catch { /* absent */ }
  report.push(`java: ${java}`)
  if (existsSync(PLANTUML_JAR)) report.push(`plantuml ${PLANTUML_VERSION}: ${repoPath(PLANTUML_JAR)} (sha256 ${sha256(await readFile(PLANTUML_JAR)).slice(0, 16)}..., gitignored)`)
  else if (java === 'not on PATH') report.push(`plantuml ${PLANTUML_VERSION}: NOT FETCHED - Java is unavailable on this machine`)
  else {
    try {
      await mkdir(path.dirname(PLANTUML_JAR), { recursive: true })
      const response = await fetch(PLANTUML_URL)
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      const jar = Buffer.from(await response.arrayBuffer())
      if (sha256(jar) !== PLANTUML_SHA256) throw new Error(`digest mismatch: ${sha256(jar)}`)
      await writeFile(PLANTUML_JAR, jar)
      report.push(`plantuml ${PLANTUML_VERSION}: fetched to ${repoPath(PLANTUML_JAR)}, SHA-256 verified, never committed`)
    } catch (error) {
      report.push(`plantuml ${PLANTUML_VERSION}: UNAVAILABLE - ${error.message}`)
      report.push('  partial configuration preserved: no jar is committed and the PlantUML gate stays wired for future .puml sources')
    }
  }
  const { dot, mermaid, plantuml } = await discover()
  report.push(`discovered sources: ${dot.length} DOT, ${mermaid.length} Mermaid, ${plantuml.length} PlantUML`)
  const python = await pythonCommand()
  report.push(`python for validate_diagrams.py: ${python ?? 'NOT FOUND - set DBCAS_TEST_PYTHON'}`)
  for (const line of report) console.log(line)
}

const command = process.argv[2]
if (command === 'check') await gate(false)
else if (command === 'render') await gate(true)
else if (command === 'setup') await setup()
else { console.error('usage: node scripts/diagrams.mjs <check|render|setup>'); process.exit(2) }
