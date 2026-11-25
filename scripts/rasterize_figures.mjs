// Rasterise every SVG in docs/submission/final/assets/figures at 300+ dpi.
// Usage: node scripts/rasterize_figures.mjs [--scale 2]
import fs from 'node:fs'
import path from 'node:path'
import { pathToFileURL } from 'node:url'
import puppeteer from 'puppeteer'

const ROOT = path.resolve(import.meta.dirname, '..')
const dirArg = process.argv.indexOf('--dir')
const DIR = dirArg >= 0
  ? path.resolve(ROOT, process.argv[dirArg + 1])
  : path.join(ROOT, 'docs', 'submission', 'final', 'assets', 'figures')
const outArg = process.argv.indexOf('--out')
const OUT = outArg >= 0 ? path.resolve(ROOT, process.argv[outArg + 1]) : DIR
const scaleArg = process.argv.indexOf('--scale')
const scale = scaleArg >= 0 ? Number(process.argv[scaleArg + 1]) : 2
fs.mkdirSync(OUT, { recursive: true })

const browser = await puppeteer.launch({
  headless: true,
  executablePath: await puppeteer.executablePath(),
  args: ['--no-sandbox', '--disable-dev-shm-usage', '--allow-file-access-from-files'],
})
try {
  for (const file of fs.readdirSync(DIR).filter((name) => name.endsWith('.svg')).sort()) {
    const source = path.join(DIR, file)
    const svg = fs.readFileSync(source, 'utf8')
    const viewBox = svg.match(/\bviewBox="([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)"/)
    const width = Math.ceil(viewBox ? Number(viewBox[3]) : 1800)
    const height = Math.ceil(viewBox ? Number(viewBox[4]) : 1200)
    const page = await browser.newPage()
    await page.setViewport({ width, height, deviceScaleFactor: scale })
    await page.goto(pathToFileURL(source).href, { waitUntil: 'load' })
    const target = path.join(OUT, file.replace(/\.svg$/, '.png'))
    await page.screenshot({ path: target, type: 'png', fullPage: true })
    await page.close()
    console.log(`${path.basename(target)} ${width * scale}x${height * scale}`)
  }
} finally {
  await browser.close()
}
