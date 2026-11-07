// Rasterise the generated SVG diagrams to high-resolution PNG (and PDF pages).
// Usage:
//   node scripts/render_svg_png.mjs                 (all generated SVGs)
//   node scripts/render_svg_png.mjs --pdf file.pdf out-dir [pages]
import fs from 'node:fs'
import path from 'node:path'
import { pathToFileURL } from 'node:url'
import puppeteer from 'puppeteer'

const ROOT = path.resolve(import.meta.dirname, '..')
const GEN = path.join(ROOT, 'docs', 'diagrams', 'generated')

async function launch() {
  return puppeteer.launch({ headless: true, executablePath: await puppeteer.executablePath(),
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--allow-file-access-from-files'] })
}

async function svgToPng(browser, svgPath, pngPath, scale) {
  const svg = fs.readFileSync(svgPath, 'utf8')
  const vb = svg.match(/<svg[^>]*\bviewBox="([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)"/)
  const wAttr = svg.match(/<svg[^>]*\bwidth="([\d.]+)(pt|px)?"/)
  const hAttr = svg.match(/<svg[^>]*\bheight="([\d.]+)(pt|px)?"/)
  // Graphviz emits pt with a viewBox; use viewBox units as CSS pixels so the
  // whole diagram is captured (a 1600x1000 fallback would crop it).
  let w = vb ? Number(vb[3]) - Number(vb[1]) : Number(wAttr?.[1] || 1600)
  let h = vb ? Number(vb[4]) - Number(vb[2]) : Number(hAttr?.[1] || 1000)
  if (!vb && wAttr?.[2] === 'pt') w = Math.ceil(w * 4 / 3)
  if (!vb && hAttr?.[2] === 'pt') h = Math.ceil(h * 4 / 3)
  w = Math.ceil(w); h = Math.ceil(h)
  const page = await browser.newPage()
  await page.setViewport({ width: w, height: h, deviceScaleFactor: scale })
  await page.goto(pathToFileURL(svgPath).href, { waitUntil: 'load' })
  await page.screenshot({ path: pngPath, fullPage: true, type: 'png' })
  await page.close()
  console.log(`${path.basename(pngPath)} ${Math.round(w*scale)}x${Math.round(h*scale)} (scale ${scale})`)
}

async function pdfToPng(browser, pdfPath, outDir, maxPages) {
  fs.mkdirSync(outDir, { recursive: true })
  const page = await browser.newPage()
  await page.setViewport({ width: 1400, height: 1900, deviceScaleFactor: 1 })
  await page.goto(pathToFileURL(pdfPath).href + '#toolbar=0', { waitUntil: 'load' })
  await new Promise((r) => setTimeout(r, 1500))
  for (let i = 1; i <= maxPages; i++) {
    await page.evaluate((n) => {
      const viewer = document.querySelector('embed, iframe')
      if (viewer && viewer.contentWindow) viewer.contentWindow.postMessage({ page: n }, '*')
    }, i).catch(() => {})
    await page.goto(pathToFileURL(pdfPath).href + `#toolbar=0&page=${i}`, { waitUntil: 'load' })
    await new Promise((r) => setTimeout(r, 900))
    await page.screenshot({ path: path.join(outDir, `page-${String(i).padStart(2, '0')}.png`), type: 'png' })
  }
  await page.close()
  console.log(`rendered ${maxPages} PDF pages to ${outDir}`)
}

const args = process.argv.slice(2)
const browser = await launch()
try {
  if (args[0] === '--pdf') {
    await pdfToPng(browser, path.resolve(args[1]), path.resolve(args[2]), Number(args[3] || 1))
  } else {
    for (const name of ['system-context', 'erd', 'table-relationships']) {
      const scale = name === 'table-relationships' ? 1 : (name === 'erd' ? 1.6 : 2)
      await svgToPng(browser, path.join(GEN, `${name}.svg`), path.join(GEN, `${name}.png`), scale)
    }
  }
} finally {
  await browser.close()
}
