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

async function svgSlices(browser, svgPath, name, slices, scale) {
  const svg = fs.readFileSync(svgPath, 'utf8')
  const vb = svg.match(/<svg[^>]*\bviewBox="([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)"/)
  const w = Math.ceil(vb ? Number(vb[3]) - Number(vb[1]) : 1870)
  const h = Math.ceil(vb ? Number(vb[4]) - Number(vb[2]) : 4049)
  const sliceH = Math.ceil(h / slices)
  const page = await browser.newPage()
  await page.setViewport({ width: w, height: sliceH, deviceScaleFactor: scale })
  await page.goto(pathToFileURL(svgPath).href, { waitUntil: 'load' })
  for (let i = 0; i < slices; i++) {
    const y = i * sliceH
    await page.screenshot({ path: path.join(GEN, `${name}-${i + 1}.png`), type: 'png',
      clip: { x: 0, y, width: w, height: Math.min(sliceH, h - y) } })
    console.log(`${name}-${i + 1}.png slice y=${y}..${y + sliceH} @scale ${scale}`)
  }
  await page.close()
}

async function pdfToPng(browser, pdfPath, outDir, maxPages) {
  fs.mkdirSync(outDir, { recursive: true })
  const page = await browser.newPage()
  await page.setViewport({ width: 1400, height: 1900, deviceScaleFactor: 1 })
  const url = pathToFileURL(pdfPath).href
  await page.goto(url + '#toolbar=0&page=1', { waitUntil: 'load' })
  await new Promise((r) => setTimeout(r, 2000))
  for (let i = 1; i <= maxPages; i++) {
    // Changing the hash scrolls Chrome's built-in PDF viewer without reloading.
    await page.evaluate((n) => { location.hash = `#toolbar=0&page=${n}` }, i).catch(() => {})
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
  } else if (args[0] === '--slices') {
    await svgSlices(browser, path.join(GEN, `${args[1]}.svg`), args[1], Number(args[2] || 3), Number(args[3] || 1.6))
  } else {
    // Full master diagrams (for docs:check / archiving)
    for (const name of ['system-context', 'erd', 'table-relationships']) {
      const scale = name === 'table-relationships' ? 1 : (name === 'erd' ? 1.6 : 2)
      await svgToPng(browser, path.join(GEN, `${name}.svg`), path.join(GEN, `${name}.png`), scale)
    }
    // Page-aligned SVGs: each is already a whole page, so no slicing/cropping.
    for (const f of fs.readdirSync(GEN).filter((n) => /^erd-\d+\.svg$/.test(n)).sort(
      (a, b) => Number(a.match(/\d+/)[0]) - Number(b.match(/\d+/)[0]))) {
      await svgToPng(browser, path.join(GEN, f), path.join(GEN, f.replace('.svg', '.png')), 1.6)
    }
    for (const f of fs.readdirSync(GEN).filter((n) => /^table-relationships-\d+\.svg$/.test(n)).sort(
      (a, b) => Number(a.match(/\d+/)[0]) - Number(b.match(/\d+/)[0]))) {
      await svgToPng(browser, path.join(GEN, f), path.join(GEN, f.replace('.svg', '.png')), 1.3)
    }
  }
} finally {
  await browser.close()
}
