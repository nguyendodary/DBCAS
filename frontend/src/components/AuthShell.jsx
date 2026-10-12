import { t, useLocale } from '../i18n'
import { Icon } from './ui'
import LanguageSelector from './LanguageSelector'
import ThemeSelector from './ThemeSelector'

const FEATURES = [
  {
    icon: 'database',
    title: 'auth.sandboxTitle',
    body: 'auth.sandboxBody',
  },
  {
    icon: 'spark',
    title: 'auth.adaptiveTitle',
    body: 'auth.adaptiveBody',
  },
  {
    icon: 'chart',
    title: 'auth.analyticsTitle',
    body: 'auth.analyticsBody',
  },
]

// A quiet two-column entry point: context on the left, one clear form on the right.
export default function AuthShell({ children }) {
  useLocale()
  return (
    <div className="auth-shell relative flex min-h-screen flex-col bg-abyss text-ink">
      <header className="flex items-center justify-between gap-2 border-b border-edge px-4 py-4 sm:gap-4 sm:px-8">
        <span className="flex items-center gap-2.5 font-bold tracking-tight"><Icon name="database" className="h-6 w-6 text-accent" />DBCAS</span>
        <div className="flex items-center gap-1.5">
          <LanguageSelector />
          <ThemeSelector />
        </div>
      </header>
      <main className="relative flex flex-1 items-center justify-center px-4 py-8 sm:px-6 sm:py-12">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            'radial-gradient(55% 50% at 15% 10%, rgba(34,211,238,0.055), transparent 70%)',
        }}
      />
      <div className="auth-enter relative grid w-full max-w-5xl items-center gap-8 md:grid-cols-[1fr_1fr] lg:gap-12">
        <aside className="hidden flex-col justify-between rounded-2xl border border-edge bg-panel p-8 md:flex">
          <div>
            <div className="flex items-center gap-2.5">
              <span className="flex h-9 w-9 items-center justify-center rounded-lg border border-cyan-400/20 bg-cyan-400/[0.08] text-cyan-300">
                <Icon name="database" className="h-5 w-5" />
              </span>
              <span className="text-base font-bold tracking-tight text-ink">DBCAS</span>
            </div>
            <h2 className="mt-8 max-w-sm text-3xl font-semibold leading-tight tracking-tight text-accent2">{t('auth.introTitle')}</h2>
            <p className="mt-4 max-w-xs text-sm leading-6 text-sub">{t('auth.introBody')}</p>
          </div>
          <ul className="mt-8 space-y-3">
            {FEATURES.map((f) => (
              <li
                key={f.title}
                className="flex gap-3 rounded-lg border border-edge bg-abyss/60 p-3.5"
              >
                <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-cyan-400/[0.07] text-cyan-300">
                  <Icon name={f.icon} className="h-4 w-4" />
                </span>
                <span>
                  <span className="block text-sm font-medium text-ink">{t(f.title)}</span>
                  <span className="mt-0.5 block text-xs leading-relaxed text-mute">{t(f.body)}</span>
                </span>
              </li>
            ))}
          </ul>
        </aside>
        <div className="auth-form-panel flex items-center rounded-2xl border border-edge2 bg-panel px-6 py-8 sm:px-9 sm:py-10">
          <div className="mx-auto w-full max-w-sm">{children}</div>
        </div>
      </div>
      </main>
    </div>
  )
}
