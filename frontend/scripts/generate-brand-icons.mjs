/**
 * Generate every favicon and home-screen icon from the single canonical mark.
 *
 * Source: public/brand/dbcas-mark.svg
 * Output: favicon.ico and dbcas-16/32/180/192/512.png.
 *
 * Chromium (the Playwright dependency already used by the browser suite) is the
 * SVG rasterizer because the Python environment has PIL 12.2.0 but no
 * cairosvg/svglib. PIL is therefore not required for this build step.
 */
import { chromium } from 'playwright'
import fs from 'node:fs'
import path from 'node:path'

const ROOT = path.resolve(import.meta.dirname, '..')
const PUBLIC_BRAND = path.join(ROOT, 'public', 'brand')
const SOURCE = path.join(PUBLIC_BRAND, 'dbcas-mark.svg')
const BRAND_CYAN = '#22d3ee'
const APP_BACKGROUND = '#070708'

const source = fs.readFileSync(SOURCE, 'utf8')
const rasterSource = source.replaceAll('currentColor', BRAND_CYAN)
const dataUrl = `data:image/svg+xml;base64,${Buffer.from(rasterSource).toString('base64')}`

function html(size, opaque) {
  return `<!doctype html><html><head><style>
    html,body{margin:0;padding:0;width:${size}px;height:${size}px;overflow:hidden;background:${
      opaque ? APP_BACKGROUND : 'transparent'
    }}
    img{display:block;width:${size}px;height:${size}px}
  </style></head><body><img src="${dataUrl}" alt=""></body></html>`
}

async function render(page, size, opaque) {
  await page.setViewportSize({ width: size, height: size })
  await page.setContent(html(size, opaque), { waitUntil: 'load' })
  await page.evaluate(() => globalThis.document?.fonts?.ready)
  return page.screenshot({
    type: 'png',
    omitBackground: !opaque,
    animations: 'disabled',
    caret: 'hide',
  })
}

function ico(entries) {
  const header = Buffer.alloc(6)
  header.writeUInt16LE(0, 0)
  header.writeUInt16LE(1, 2)
  header.writeUInt16LE(entries.length, 4)
  const directory = Buffer.alloc(16 * entries.length)
  let offset = header.length + directory.length
  entries.forEach(({ size, data }, index) => {
    const at = index * 16
    directory.writeUInt8(size >= 256 ? 0 : size, at)
    directory.writeUInt8(size >= 256 ? 0 : size, at + 1)
    directory.writeUInt8(0, at + 2)
    directory.writeUInt8(0, at + 3)
    directory.writeUInt16LE(1, at + 4)
    directory.writeUInt16LE(32, at + 6)
    directory.writeUInt32LE(data.length, at + 8)
    directory.writeUInt32LE(offset, at + 12)
    offset += data.length
  })
  return Buffer.concat([header, directory, ...entries.map((entry) => entry.data)])
}

const browser = await chromium.launch()
const page = await browser.newPage({ deviceScaleFactor: 1 })
const transparent = {}
for (const size of [16, 32, 48]) transparent[size] = await render(page, size, false)
const pngs = {
  16: transparent[16],
  32: transparent[32],
  180: await render(page, 180, true),
  192: await render(page, 192, true),
  512: await render(page, 512, true),
}
await browser.close()

for (const [size, data] of Object.entries(pngs)) {
  fs.writeFileSync(path.join(PUBLIC_BRAND, `dbcas-${size}.png`), data)
}
fs.writeFileSync(
  path.join(PUBLIC_BRAND, 'favicon.ico'),
  ico([16, 32, 48].map((size) => ({ size, data: transparent[size] }))),
)

const expected = ['16', '32', '180', '192', '512']
for (const size of expected) {
  const data = fs.readFileSync(path.join(PUBLIC_BRAND, `dbcas-${size}.png`))
  const width = data.readUInt32BE(16)
  const height = data.readUInt32BE(20)
  if (width !== Number(size) || height !== Number(size)) {
    throw new Error(`dbcas-${size}.png is ${width}x${height}`)
  }
  console.log(`dbcas-${size}.png ${width}x${height} ${data.length} bytes`)
}
console.log(
  `favicon.ico 16/32/48 ${fs.statSync(path.join(PUBLIC_BRAND, 'favicon.ico')).size} bytes`,
)
console.log(`source ${path.relative(ROOT, SOURCE)}`)
