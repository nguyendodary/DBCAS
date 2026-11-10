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

// Every text token is checked on every generic reading surface. Semantic text is
// additionally checked on its own tinted surface. Disabled text is checked at
// 3:1 because WCAG 2.2 SC 1.4.3 exempts inactive controls, but we still require
// it to be perceivable.
const textTokens = [
  'text',
  'text-muted',
  'text-subtle',
  'text-faint',
  'brand-text',
  'brand-soft',
  'primary',
  'success-text',
  'warning-text',
  'danger-text',
  'info-text',
  'secondary-text',
  'neutral-status-text',
]
const surfaces = ['bg', 'surface', 'surface-elevated', 'surface-muted', 'surface-sidebar']
const semanticOwn = [
  ['success-text', 'success-surface'],
  ['warning-text', 'warning-surface'],
  ['danger-text', 'danger-surface'],
  ['primary-foreground', 'primary'],
]

const graphicalPairs = [
  'chart-1',
  'chart-2',
  'chart-3',
  'chart-4',
  'chart-5',
  'chart-6',
  'chart-7',
  'chart-8',
  'chart-9',
  'chart-10',
  'chart-target',
]

let failed = 0
let checked = 0
for (const [name, values] of Object.entries(themes)) {
  console.log(`\n${name} theme`)
  for (const foreground of textTokens) {
    for (const background of surfaces) {
      if (!values[foreground] || !values[background]) continue
      checked += 1
      const ratio = contrast(values[foreground], values[background])
      const pass = ratio >= 4.5
      if (!pass) failed += 1
      console.log(
        `  ${pass ? 'PASS' : 'FAIL'} ${foreground} on ${background}: ${ratio.toFixed(2)}:1`,
      )
    }
  }
  if (values['text-disabled']) {
    for (const background of ['surface', 'surface-muted']) {
      if (!values[background]) continue
      checked += 1
      const ratio = contrast(values['text-disabled'], values[background])
      const pass = ratio >= 3
      if (!pass) failed += 1
      console.log(
        `  ${pass ? 'PASS' : 'FAIL'} text-disabled on ${background}: ${ratio.toFixed(2)}:1 (inactive 3:1)`,
      )
    }
  }
  for (const [foreground, background] of semanticOwn) {
    if (!values[foreground] || !values[background]) continue
    checked += 1
    const ratio = contrast(values[foreground], values[background])
    const pass = ratio >= 4.5
    if (!pass) failed += 1
    console.log(
      `  ${pass ? 'PASS' : 'FAIL'} ${foreground} on ${background}: ${ratio.toFixed(2)}:1`,
    )
  }
  for (const foreground of graphicalPairs) {
    for (const background of ['surface', 'bg']) {
      if (!values[foreground] || !values[background]) continue
      checked += 1
      const ratio = contrast(values[foreground], values[background])
      const pass = ratio >= 3
      if (!pass) failed += 1
      console.log(
        `  ${pass ? 'PASS' : 'FAIL'} ${foreground} on ${background}: ${ratio.toFixed(2)}:1 (graphic 3:1)`,
      )
    }
  }
}

console.log(`\n${checked} contrast pairs checked`)
if (failed) {
  console.error(`${failed} contrast check(s) failed`)
  process.exit(1)
}
console.log('All contrast checks passed')
