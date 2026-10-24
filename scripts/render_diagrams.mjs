// Optional authoring tool; no application dependency or provider/network calls.
// Install @viz-js/viz separately; set DBCAS_VIZ_MODULE to its dist/viz.js path.
import { readFile, writeFile } from 'node:fs/promises'
import { pathToFileURL } from 'node:url'
import path from 'node:path'

const modulePath = process.env.DBCAS_VIZ_MODULE
const { instance } = await import(modulePath
  ? (modulePath.startsWith('file:') ? modulePath : pathToFileURL(path.resolve(modulePath)).href)
  : '@viz-js/viz')
const viz = await instance()
const root = new URL('../docs/diagrams/', import.meta.url)
const diagrams = ['physical-schema', 'assessment-lifecycle', 'use-cases', 'containers',
  'deployment', 'components', 'modules', 'conceptual-core', 'logical-architecture']
for (const name of diagrams) {
  const source = await readFile(new URL(`${name}.dot`, root), 'utf8')
  const result = viz.render(source, { format: 'svg', engine: 'dot' })
  if (result.status !== 'success' || result.errors.length) {
    throw new Error(`${name}: ${JSON.stringify(result.errors)}`)
  }
  const svg = result.output.replace('<svg ', `<svg role="img" aria-label="DBCAS ${name} diagram" `)
  await writeFile(new URL(`${name}.svg`, root), svg)
  console.log(`${name}: rendered`)
}
// system-context.svg is its editable source; the JSON ledger is validated separately.
