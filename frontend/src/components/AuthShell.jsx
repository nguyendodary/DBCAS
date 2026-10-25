import { t, useLocale } from '../i18n'
import { Link } from 'react-router-dom'
import { Icon } from './ui'
import LanguageSelector from './LanguageSelector'
import ThemeSelector from './ThemeSelector'

const FEATURES = [
  { icon: '⚡', tint: 'rgba(76,215,246,.1) rgba(76,215,246,.3)', title: 'auth.sandboxTitle', body: 'auth.sandboxBody' },
  { icon: '✨', tint: 'rgba(78,222,163,.1) rgba(78,222,163,.3)', title: 'auth.adaptiveTitle', body: 'auth.adaptiveBody' },
  { icon: '📊', tint: 'rgba(192,193,255,.1) rgba(192,193,255,.3)', title: 'auth.analyticsTitle', body: 'auth.analyticsBody' },
]

// Auth surface — exact port of the frontend-branch Dang_nhap/Dang_ky shell:
// photo backdrop, slim top bar (back link + brand), two-column layout with the
// marketing panel left and the bordered form card right, fixed bottom bar.
// `title`/`subtitle` render inside the form card like the source headings.
export default function AuthShell({ title, subtitle, children, headingClassName, className = '' }) {
  useLocale()
  return (
    <div className={`auth-shell font-sans ${className}`}>
      <header className="auth-topnav">
        <div className="flex h-14 items-center justify-between gap-3 px-6">
          <div className="flex items-center gap-3">
            <Link to="/" className="auth-backlink">
              <Icon name="arrowLeft" className="h-4 w-4" />
              {t('auth.back')}
            </Link>
            <LanguageSelector />
            <ThemeSelector />
          </div>
          <span className="flex items-center gap-2">
            <span className="text-[17px] font-bold text-accent">DBCAS</span>
            <span className="hidden text-[17px] font-bold text-ink sm:inline">{t('nav.engineTagFull')}</span>
          </span>
        </div>
      </header>

      <main className="grid min-h-screen w-full grid-cols-1 items-center gap-8 px-4 pb-16 pt-24 md:grid-cols-2 md:gap-8 md:px-12 lg:px-16">
        <aside className="auth-panel mx-auto hidden w-full max-w-[580px] md:block">
          <h2 className="mb-4 text-[32px] font-bold leading-10 tracking-[-0.7px]">
            <span className="text-ink">{t('auth.introTitle')}</span>
            <br />
            <span className="text-accent">{t('auth.introAccent')}</span>
          </h2>
          <p className="mb-6 text-sm leading-[22px] text-sub">{t('auth.introBody')}</p>
          <ul className="flex flex-col gap-3">
            {FEATURES.map((f) => (
              <li key={f.title} className="auth-feature">
                <span
                  aria-hidden="true"
                  className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border text-base"
                  style={{ background: f.tint.split(' ')[0], borderColor: f.tint.split(' ')[1] }}
                >
                  {f.icon}
                </span>
                <span>
                  <span className="block text-[13px] font-medium leading-[18px] text-ink">{t(f.title)}</span>
                  <span className="block text-xs leading-4 text-sub">{t(f.body)}</span>
                </span>
              </li>
            ))}
          </ul>
        </aside>

        <div className="mx-auto flex w-full max-w-[580px] justify-center md:max-w-none">
          <div className="auth-card auth-enter">
            <div className={headingClassName}>
              <h1 className="text-xl font-bold tracking-[-0.45px] text-ink">{title}</h1>
              <p className="mt-1 text-xs text-sub">{subtitle}</p>
            </div>
            {children}
          </div>
        </div>
      </main>

      <footer className="auth-bottombar">
        {t('auth.footer', { year: new Date().getFullYear() })}
      </footer>
    </div>
  )
}
