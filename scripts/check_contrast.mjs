import { readFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const css = readFileSync(path.join(root, 'frontend/src/index.css'), 'utf8')

function block(selector) {
  const start = css.indexOf(selector)
  if (start < 0) throw new Error(`Missing token block ${selector}`)
  const open = css.indexOf('{', start)
  let depth = 0
  for (let i = open; i < css.length; i += 1) {
    if (css[i] === '{') depth += 1
    if (css[i] === '}') {
      depth -= 1
      if (depth === 0) return css.slice(open + 1, i)
    }
  }
  throw new Error(`Unclosed token block ${selector}`)
}

function tokens(text) {
  return Object.fromEntries(
    [...text.matchAll(/--([\w-]+):\s*(#[0-9a-f]{3,8})\s*;/gi)].map((match) => [
      match[1],
      match[2],
    ]),
  )
}

function rgb(hex) {
  let value = hex.slice(1)
  if (value.length === 3) value = [...value].map((char) => char + char).join('')
  return [0, 2, 4].map((index) => parseInt(value.slice(index, index + 2), 16))
}

function luminance(hex) {
  const channels = rgb(hex).map((value) => {
    const channel = value / 255
    return channel <= 0.03928 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4
  })
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]
}

function contrast(foreground, background) {
  const a = luminance(foreground)
  const b = luminance(background)
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05)
}

const themes = {
  dark: tokens(block(':root {')),
  light: tokens(block(":root[data-theme='light'] {")),
}

const textPairs = [
  ['text', 'bg'],
  ['text', 'surface'],
  ['text', 'surface-elevated'],
  ['text', 'surface-muted'],
  ['text-muted', 'surface'],
  ['text-muted', 'bg'],
  ['text-subtle', 'surface'],
  ['text-faint', 'surface'],
  ['brand-text', 'surface-elevated'],
  ['danger-text', 'danger-surface'],
  ['success-text', 'success-surface'],
  ['warning-text', 'warning-surface'],
  ['primary-foreground', 'primary'],
]

const graphicalPairs = [
  ['chart-label', 'surface'],
  ['chart-1', 'surface'],
  ['chart-2', 'surface'],
  ['chart-3', 'surface'],
  ['chart-4', 'surface'],
  ['chart-5', 'surface'],
  ['chart-6', 'surface'],
  ['chart-7', 'surface'],
  ['chart-8', 'surface'],
  ['chart-9', 'surface'],
  ['chart-10', 'surface'],
  ['chart-target', 'surface'],
]

let failed = 0
for (const [name, values] of Object.entries(themes)) {
  console.log(`\n${name} theme`)
  for (const [foreground, background] of textPairs) {
    if (!values[foreground] || !values[background]) {
      console.log(`  SKIP ${foreground} on ${background} (missing token)`)
      continue
    }
    const ratio = contrast(values[foreground], values[background])
    const pass = ratio >= 4.5
    if (!pass) failed += 1
    console.log(
      `  ${pass ? 'PASS' : 'FAIL'} ${foreground} on ${background}: ${ratio.toFixed(2)}:1`,
    )
  }
  for (const [foreground, background] of graphicalPairs) {
    if (!values[foreground] || !values[background]) continue
    const ratio = contrast(values[foreground], values[background])
    const pass = ratio >= 3
    if (!pass) failed += 1
    console.log(
      `  ${pass ? 'PASS' : 'FAIL'} ${foreground} on ${background}: ${ratio.toFixed(2)}:1 (graphic 3:1)`,
    )
  }
}

if (failed) {
  console.error(`\n${failed} contrast check(s) failed`)
  process.exit(1)
}
console.log('\nAll contrast checks passed')
