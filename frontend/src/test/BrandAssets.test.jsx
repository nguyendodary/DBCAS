import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import fs from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'
import BrandLogo, { PRODUCT_NAME } from '../components/BrandLogo'
import en from '../i18n/en.json'
import vi from '../i18n/vi.json'

const FRONTEND = process.cwd()
const PUBLIC = path.join(FRONTEND, 'public')
const BRAND = path.join(PUBLIC, 'brand')
const SRC = path.join(FRONTEND, 'src')

function walk(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const full = path.join(dir, entry.name)
    return entry.isDirectory() ? walk(full) : [full]
  })
}

function read(file) {
  return fs.readFileSync(file, 'utf8')
}

function stripComments(source) {
  return source.replace(/\/\*[\s\S]*?\*\//g, '').replace(/(?<!:)\/\/[^\n]*/g, '')
}

function pngSize(file) {
  const data = fs.readFileSync(file)
  expect(data.subarray(1, 4).toString('ascii')).toBe('PNG')
  return { width: data.readUInt32BE(16), height: data.readUInt32BE(20) }
}

describe('canonical DBCAS brand assets', () => {
  it('keeps exactly one logo source in public/brand', () => {
    const svgs = walk(PUBLIC)
      .filter((file) => file.toLowerCase().endsWith('.svg'))
      .map((file) => path.relative(PUBLIC, file).split(path.sep).join('/'))
    expect(svgs).toEqual(['brand/dbcas-mark.svg'])

    const mark = read(path.join(BRAND, 'dbcas-mark.svg'))
    expect(mark).toContain('viewBox="0 0 48 48"')
    expect(mark).toContain('id="dbcas-database"')
    expect(mark).toContain('fill="currentColor"')
    expect(mark).toContain('aria-labelledby="dbcas-mark-title"')
    // The mark is a database cylinder, not a second D next to the DBCAS wordmark.
    expect(mark).toContain('<ellipse')
    expect(mark).not.toContain('M13 12h9c8.28')
  })

  it('ships every icon generated from that source at the exact size', () => {
    for (const size of [16, 32, 180, 192, 512]) {
      const file = path.join(BRAND, `dbcas-${size}.png`)
      expect(fs.existsSync(file), `${path.basename(file)} exists`).toBe(true)
      expect(pngSize(file)).toEqual({ width: size, height: size })
    }

    const ico = fs.readFileSync(path.join(BRAND, 'favicon.ico'))
    expect(ico.readUInt16LE(0)).toBe(0)
    expect(ico.readUInt16LE(2)).toBe(1)
    const count = ico.readUInt16LE(4)
    const sizes = Array.from({ length: count }, (_, index) => {
      const width = ico.readUInt8(6 + index * 16)
      return width === 0 ? 256 : width
    })
    expect(sizes.sort((a, b) => a - b)).toEqual([16, 32, 48])
  })

  it('links the manifest, apple-touch and generated favicon from index.html', () => {
    const html = read(path.join(FRONTEND, 'index.html'))
    expect(html).toContain('<link rel="icon" href="/brand/favicon.ico"')
    expect(html).toContain('href="/brand/dbcas-32.png"')
    expect(html).toContain('rel="apple-touch-icon"')
    expect(html).toContain('href="/brand/dbcas-180.png"')
    expect(html).toContain('rel="manifest"')
    expect(html).toContain('href="/brand/manifest.webmanifest"')
    expect(html).not.toContain('favicon.svg')
    expect(html).toContain(`<title>${PRODUCT_NAME}</title>`)
  })

  it('names the manifest exactly DBCAS and references the generated PNGs', () => {
    const manifest = JSON.parse(read(path.join(BRAND, 'manifest.webmanifest')))
    expect(manifest.name).toBe(PRODUCT_NAME)
    expect(manifest.short_name).toBe(PRODUCT_NAME)
    expect(manifest.start_url).toBe('/')
    expect(manifest.icons.map((icon) => icon.sizes)).toEqual(['192x192', '512x512'])
    expect(manifest.icons.map((icon) => icon.src)).toEqual([
      '/brand/dbcas-192.png',
      '/brand/dbcas-512.png',
    ])
  })
})

describe('one shared brand lockup', () => {
  it('renders the single mark, wordmark and the nav.engineTagFull tagline', () => {
    render(
      <MemoryRouter>
        <BrandLogo />
      </MemoryRouter>,
    )
    expect(screen.getByRole('link', { name: PRODUCT_NAME })).toHaveAttribute('href', '/')
    expect(screen.getByText(PRODUCT_NAME)).toBeVisible()
    expect(screen.getByText('SKILL ANALYTICS')).toBeVisible()
    expect(document.querySelectorAll('.brand-mark')).toHaveLength(1)
  })

  it('keeps the English and Vietnamese tagline identical', () => {
    expect(en.nav.engineTagFull).toBe('SKILL ANALYTICS')
    expect(vi.nav.engineTagFull).toBe(en.nav.engineTagFull)
  })

  it('uses BrandLogo in the header, auth shell and landing page', () => {
    const layout = read(path.join(SRC, 'components', 'Layout.jsx'))
    const auth = read(path.join(SRC, 'components', 'AuthShell.jsx'))
    const landing = read(path.join(SRC, 'pages', 'LandingPage.jsx'))
    const login = read(path.join(SRC, 'pages', 'LoginPage.jsx'))
    const register = read(path.join(SRC, 'pages', 'RegisterPage.jsx'))

    expect(layout).toContain("import BrandLogo, { BrandWordmark } from './BrandLogo'")
    expect((layout.match(/<BrandLogo /g) || []).length).toBeGreaterThanOrEqual(3)
    expect(auth).toContain("import BrandLogo from './BrandLogo'")
    expect(auth).toContain('<BrandLogo')
    expect(landing).toContain("import BrandLogo from '../components/BrandLogo'")
    expect(landing).toContain('<BrandLogo')
    expect(login).toContain("import AuthShell from '../components/AuthShell'")
    expect(register).toContain("import AuthShell from '../components/AuthShell'")
  })

  it('has no second inline brand SVG or split BCAS wordmark', () => {
    const sources = walk(SRC).filter(
      (file) => /\.(jsx?|css)$/.test(file) && !/[\\/]test[\\/]/.test(file),
    )
    for (const file of sources) {
      const source = read(file)
      expect(source, path.relative(FRONTEND, file)).not.toContain('viewBox="2 2 36 40"')
      expect(source, path.relative(FRONTEND, file)).not.toContain('M7 5h12')
      expect(source, path.relative(FRONTEND, file)).not.toContain('M13 12h9c8.28')
      expect(source, path.relative(FRONTEND, file)).not.toContain('M11 12.5c0-3')
      expect(source, path.relative(FRONTEND, file)).not.toMatch(/>\s*BCAS\s*</)
      expect(source, path.relative(FRONTEND, file)).not.toContain('BrandSymbol')
    }
  })

  it('does not hard-code the product wordmark outside BrandLogo', () => {
    const branded = walk(SRC).filter(
      (file) =>
        /[\\/](components|pages)[\\/].*\.jsx$/.test(file) &&
        !/[\\/]test[\\/]/.test(file) &&
        path.basename(file) !== 'BrandLogo.jsx',
    )
    for (const file of branded) {
      const source = stripComments(read(file))
      expect(source, path.relative(FRONTEND, file)).not.toMatch(/\bDBCAS\b/)
    }
  })
})
