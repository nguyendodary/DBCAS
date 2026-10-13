import { t, useLocale } from '../i18n'
import { Link } from 'react-router-dom'
import LanguageSelector from '../components/LanguageSelector'
import { Icon } from '../components/ui'

const PILLARS = [
  { tag: 'ADAPTIVE', icon: 'target', title: 'landing.pillarAdaptive', body: 'landing.pillarAdaptiveBody', foot: 'landing.pillarAdaptiveFoot' },
  { tag: 'SANDBOX', icon: 'code', title: 'landing.pillarSandbox', body: 'landing.pillarSandboxBody', foot: 'landing.pillarSandboxFoot' },
  { tag: 'EVIDENCE', icon: 'chart', title: 'landing.pillarEvidence', body: 'landing.pillarEvidenceBody', foot: 'landing.pillarEvidenceFoot' },
]

const STATS = [
  { value: '3', label: 'landing.statTypes', sub: 'landing.statTypesSub', cls: '' },
  { value: '60', label: 'landing.statMinutes', sub: 'landing.statMinutesSub', cls: 'landing-stat-green' },
  { value: '13', label: 'landing.statQuestions', sub: 'landing.statQuestionsSub', cls: 'landing-stat-violet' },
]

// Public entry page ported from the frontend-branch landing screen
// (Pages/Home): dark cinematic hero, product-fact stat cards and the
// three capability pillars — every string through i18n, no mock assets.
export default function LandingPage() {
  useLocale()
  return (
    <div className="landing font-sans">
      <div className="mx-auto flex min-h-screen w-full max-w-[1200px] flex-col px-4 py-8 sm:px-6 lg:px-10 lg:py-10">
        <header className="flex items-center justify-between gap-4">
          <span className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-400/10 text-cyan-300 ring-1 ring-inset ring-cyan-400/25">
              <Icon name="database" className="h-5 w-5" />
            </span>
            <span className="leading-tight">
              <span className="block font-mono text-xl font-bold text-white">DBCAS</span>
              <span className="block font-mono text-[10px] font-semibold tracking-[.18em] text-cyan-300">{t('landing.brandTag')}</span>
            </span>
          </span>
          <nav className="flex items-center gap-2 sm:gap-3" aria-label={t('nav.primary')}>
            <LanguageSelector />
            <Link
              to="/login"
              className="rounded-lg px-4 py-2 text-sm font-medium text-slate-200 transition hover:-translate-y-0.5 hover:text-cyan-300 motion-reduce:transform-none"
            >
              {t('auth.signIn')}
            </Link>
            <Link
              to="/register"
              className="rounded-lg border border-cyan-400/40 bg-cyan-400/10 px-4 py-2 text-sm font-semibold text-cyan-200 transition hover:-translate-y-0.5 hover:bg-cyan-400/20 motion-reduce:transform-none"
            >
              {t('auth.registerLearner')}
            </Link>
          </nav>
        </header>

        <main className="flex flex-1 flex-col justify-center py-14 sm:py-20">
          <section className="mx-auto flex max-w-[900px] flex-col items-center text-center" aria-labelledby="landing-title">
            <p className="mb-6 inline-flex items-center gap-2.5 rounded-full border border-cyan-500/20 bg-cyan-500/[0.08] px-4 py-1.5 text-xs font-semibold text-cyan-200 shadow-[0_0_15px_rgba(6,182,212,.15)]">
              <span className="flex gap-1" aria-hidden="true">
                <i className="h-2 w-2 rounded-full bg-cyan-300 opacity-75" />
                <i className="h-2 w-2 rounded-full bg-cyan-500" />
              </span>
              {t('landing.badge')}
            </p>
            <h1 id="landing-title" className="landing-title">{t('landing.title')}</h1>
            <p className="mt-6 max-w-[760px] text-base leading-relaxed text-slate-400 sm:text-lg">
              {t('landing.desc')}
            </p>
            <div className="mt-9 flex flex-wrap justify-center gap-4">
              <Link
                to="/register"
                className="rounded-xl bg-gradient-to-br from-cyan-400 to-teal-300 px-7 py-3.5 text-base font-semibold text-slate-950 shadow-[0_0_25px_rgba(6,182,212,.45)] transition hover:-translate-y-0.5 hover:opacity-90 motion-reduce:transform-none"
              >
                {t('landing.ctaRegister')}
              </Link>
              <Link
                to="/login"
                className="rounded-xl border border-white/10 bg-slate-900/80 px-7 py-3.5 text-base font-semibold text-slate-200 transition hover:-translate-y-0.5 hover:border-cyan-400 hover:text-white motion-reduce:transform-none"
              >
                {t('auth.signIn')}
              </Link>
            </div>
          </section>

          <section className="mx-auto mt-16 grid w-full max-w-[1100px] gap-6 sm:mt-20 sm:grid-cols-3" aria-label={t('landing.statsLabel')}>
            {STATS.map((s) => (
              <div key={s.label} className="landing-card p-6 text-center sm:p-8">
                <p className={`landing-stat ${s.cls}`}>{s.value}</p>
                <p className="mt-2 text-sm font-medium text-slate-300">{t(s.label)}</p>
                <p className="mt-1.5 font-mono text-[11px] text-slate-500">{t(s.sub)}</p>
              </div>
            ))}
          </section>

          <section className="mx-auto mt-16 w-full max-w-[1100px] sm:mt-24" aria-labelledby="landing-pillars">
            <div className="mb-10 text-center sm:mb-12">
              <p className="inline-block rounded-full border border-cyan-500/30 bg-cyan-950/70 px-4 py-1 text-xs font-semibold text-cyan-200">
                {t('landing.pillarsBadge')}
              </p>
              <h2 id="landing-pillars" className="mt-4 text-2xl font-extrabold text-white sm:text-4xl">
                {t('landing.pillarsTitle')}
              </h2>
              <p className="mx-auto mt-4 max-w-[700px] text-sm leading-relaxed text-slate-400 sm:text-base">
                {t('landing.pillarsDesc')}
              </p>
            </div>
            <div className="grid gap-6 md:grid-cols-3">
              {PILLARS.map((p) => (
                <article key={p.tag} className="landing-card flex flex-col justify-between p-6 transition hover:-translate-y-1 hover:border-cyan-400/30 sm:p-8 motion-reduce:transform-none">
                  <div>
                    <div className="mb-5 flex items-center justify-between gap-2">
                      <span className="rounded bg-cyan-950/70 px-2.5 py-1 font-mono text-[11px] font-bold text-cyan-300">{p.tag}</span>
                      <span className="flex h-9 w-9 items-center justify-center rounded-[10px] bg-cyan-500/10 text-cyan-300">
                        <Icon name={p.icon} className="h-4 w-4" />
                      </span>
                    </div>
                    <h3 className="text-lg font-bold text-white">{t(p.title)}</h3>
                    <p className="mt-3 text-sm leading-relaxed text-slate-400">{t(p.body)}</p>
                  </div>
                  <div className="mt-6 flex items-center justify-between border-t border-white/5 pt-4 text-xs">
                    <span className="text-slate-300">{t('landing.pillarLearn')}</span>
                    <span className="font-mono font-bold text-cyan-300">{t(p.foot)}</span>
                  </div>
                </article>
              ))}
            </div>
          </section>
        </main>

        <footer className="border-t border-white/5 pt-8 text-center text-[13px] text-slate-500">
          {t('landing.footer')}
        </footer>
      </div>
    </div>
  )
}
