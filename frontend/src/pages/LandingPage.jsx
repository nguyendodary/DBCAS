import { t, useLocale } from '../i18n'
import { Link } from 'react-router-dom'
import LanguageSelector from '../components/LanguageSelector'

const PILLARS = [
  { tag: 'landing.pillarTag1', icon: '📖', title: 'landing.pillarAdaptive', body: 'landing.pillarAdaptiveBody', foot: 'landing.pillarAdaptiveFoot' },
  { tag: 'landing.pillarTag2', icon: '💻', title: 'landing.pillarSandbox', body: 'landing.pillarSandboxBody', foot: 'landing.pillarSandboxFoot' },
  { tag: 'landing.pillarTag3', icon: '🤖', title: 'landing.pillarEvidence', body: 'landing.pillarEvidenceBody', foot: 'landing.pillarEvidenceFoot' },
]

const STATS = [
  { value: '3', label: 'landing.statTypes', sub: 'landing.statTypesSub', cls: '' },
  { value: '60', label: 'landing.statMinutes', sub: 'landing.statMinutesSub', cls: 'landing-stat-green' },
  { value: '13', label: 'landing.statQuestions', sub: 'landing.statQuestionsSub', cls: 'landing-stat-blue' },
]

// Public entry page — exact port of the frontend-branch landing screen
// (Pages/Home): poster-backed dark hero, centered glass cards, pill CTAs.
// Marketing copy uses real product facts; every string runs through i18n.
export default function LandingPage() {
  useLocale()
  return (
    <div className="landing font-sans">
      <div className="mx-auto flex min-h-screen w-full max-w-[1200px] flex-col px-4 py-10 sm:px-6 lg:px-16">
        <header className="mb-10 flex items-center justify-between gap-4 sm:mb-16">
          <span className="flex flex-col">
            <span className="flex items-baseline gap-2">
              <span className="font-mono text-2xl font-bold text-white">DBCAS</span>
              <span className="text-xs font-semibold tracking-wide text-cyan-400">{t('landing.brandTag')}</span>
            </span>
            <span className="font-mono text-[10px] tracking-[.05em] text-slate-500">{t('landing.brandDesc')}</span>
          </span>
          <nav className="flex items-center gap-3 sm:gap-4" aria-label={t('nav.primary')}>
            <LanguageSelector />
            <Link
              to="/login"
              className="rounded-lg border border-transparent px-4 py-2 text-sm font-medium text-slate-200 transition hover:-translate-y-0.5 hover:border-cyan-400/40 hover:bg-cyan-400/5 hover:text-cyan-300 motion-reduce:transform-none"
            >
              {t('auth.signIn')}
            </Link>
            <Link
              to="/register"
              className="rounded-lg border border-transparent px-4 py-2 text-sm font-medium text-slate-200 transition hover:-translate-y-0.5 hover:border-cyan-400/40 hover:bg-cyan-400/5 hover:text-cyan-300 motion-reduce:transform-none"
            >
              {t('auth.registerLearner')}
            </Link>
          </nav>
        </header>

        <main className="flex flex-1 flex-col justify-center">
          <section className="mx-auto mb-16 flex max-w-[900px] flex-col items-center text-center sm:mb-20" aria-labelledby="landing-title">
            <p className="mb-6 inline-flex items-center gap-2.5 rounded-full border border-cyan-500/20 bg-cyan-500/[0.08] px-4 py-1.5 text-xs font-semibold text-cyan-200 shadow-[0_0_15px_rgba(6,182,212,.15)]">
              <span className="flex gap-1" aria-hidden="true">
                <i className="h-2 w-2 rounded-full bg-cyan-400 opacity-75" />
                <i className="h-2 w-2 rounded-full bg-cyan-600" />
              </span>
              {t('landing.badge')}
            </p>
            <h1 id="landing-title" className="landing-title">{t('landing.title')}</h1>
            <p className="mb-9 mt-6 max-w-[760px] text-base leading-relaxed text-slate-400 sm:text-lg">
              {t('landing.desc')}
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link
                to="/register"
                className="rounded-xl bg-gradient-to-br from-cyan-400 to-teal-300 px-7 py-3.5 text-base font-semibold text-slate-950 shadow-[0_0_25px_rgba(6,182,212,.45)] transition hover:-translate-y-0.5 hover:opacity-90 motion-reduce:transform-none"
              >
                🚀 {t('landing.ctaRegister')}
              </Link>
              <Link
                to="/login"
                className="rounded-xl border border-white/10 bg-slate-900/80 px-7 py-3.5 text-base font-semibold text-slate-200 transition hover:-translate-y-0.5 hover:border-cyan-400 hover:text-white motion-reduce:transform-none"
              >
                📊 {t('landing.ctaSignIn')}
              </Link>
            </div>
          </section>

          <section className="mx-auto mb-20 grid w-full max-w-[1200px] gap-6 sm:mb-24 sm:grid-cols-3" aria-label={t('landing.statsLabel')}>
            {STATS.map((s) => (
              <div key={s.label} className="landing-card p-6 text-center sm:p-8">
                <p className={`landing-stat ${s.cls}`}>{s.value}</p>
                <p className="mt-2 text-sm font-medium text-slate-300">{t(s.label)}</p>
                <p className="mt-3 font-mono text-[11px] text-slate-500">{t(s.sub)}</p>
              </div>
            ))}
          </section>

          <section className="mx-auto w-full max-w-[1200px] pb-14" aria-labelledby="landing-pillars">
            <div className="mb-10 text-center sm:mb-12">
              <p className="inline-block rounded-full border border-cyan-500/30 bg-cyan-950/70 px-3.5 py-1 text-xs font-semibold text-cyan-200">
                🛡️ {t('landing.pillarsBadge')}
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
                      <span className="rounded bg-cyan-950/60 px-2.5 py-1 font-mono text-[11px] font-bold text-cyan-300">{t(p.tag)}</span>
                      <span className="flex h-9 w-9 items-center justify-center rounded-[10px] bg-cyan-500/10 text-base" aria-hidden="true">{p.icon}</span>
                    </div>
                    <h3 className="text-lg font-bold uppercase text-white">{t(p.title)}</h3>
                    <p className="mb-6 mt-3 text-sm leading-relaxed text-slate-400">{t(p.body)}</p>
                  </div>
                  <div className="flex items-center justify-between border-t border-white/5 pt-4 text-xs">
                    <span className="text-slate-300">{t(p.foot)}</span>
                  </div>
                </article>
              ))}
            </div>
          </section>
        </main>

        <footer className="mx-auto w-full max-w-[1200px] border-t border-white/5 py-8 text-center text-[13px] text-slate-500">
          {t('landing.footer', { year: new Date().getFullYear() })}
        </footer>
      </div>
    </div>
  )
}
