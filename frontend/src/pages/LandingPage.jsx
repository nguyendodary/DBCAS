import { t, useLocale } from '../i18n'
import { Link } from 'react-router-dom'
import ThemeSelector from '../components/ThemeSelector'
import LanguageSelector from '../components/LanguageSelector'
import BackgroundVideo from '../components/BackgroundVideo'
import landingVideo from '../assets/brand/landing-background.mp4'
import landingPoster from '../assets/brand/landing-background.jpg'

const PILLARS = [
  { tag: 'landing.pillarTag1', icon: 'adaptive', title: 'landing.pillarAdaptive', body: 'landing.pillarAdaptiveBody', foot: 'landing.pillarAdaptiveFoot' },
  { tag: 'landing.pillarTag2', icon: 'code', title: 'landing.pillarSandbox', body: 'landing.pillarSandboxBody', foot: 'landing.pillarSandboxFoot' },
  { tag: 'landing.pillarTag3', icon: 'evidence', title: 'landing.pillarEvidence', body: 'landing.pillarEvidenceBody', foot: 'landing.pillarEvidenceFoot' },
]

const STATS = [
  { value: '3', label: 'landing.statTypes', sub: 'landing.statTypesSub', cls: '' },
  { value: '60', label: 'landing.statMinutes', sub: 'landing.statMinutesSub', cls: 'landing-stat-green' },
  { value: '13', label: 'landing.statQuestions', sub: 'landing.statQuestionsSub', cls: 'landing-stat-blue' },
]

function FeatureIcon({ type }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {type === 'adaptive' ? <><path d="M4 5h6a3 3 0 0 1 3 3v12a4 4 0 0 0-4-2H4z" /><path d="M20 5h-4a3 3 0 0 0-3 3m7 2v8h-3" /></> : type === 'code' ? <><path d="m8 7-5 5 5 5m8-10 5 5-5 5m-3-13-2 20" /></> : <><path d="m12 3 8 4v5c0 5-8 9-8 9s-8-4-8-9V7z" /><path d="m8 12 3 3 5-6" /></>}
    </svg>
  )
}

function FeaturePreview({ type }) {
  return (
    <div className={`landing-feature-preview landing-preview-${type}`} aria-hidden="true">
      {type === 'adaptive' ? <>
        <div className="landing-preview-question"><span>01</span><i /><i /></div>
        <div className="landing-preview-options"><span>A<i /></span><span className="is-selected">B<i /><b>&#10003;</b></span><span>C<i /></span></div>
      </> : type === 'code' ? <>
        <div className="landing-preview-query"><b>SELECT</b> * <b>FROM</b> skills;</div>
        <div className="landing-preview-table">{Array.from({ length: 9 }, (_, i) => <i key={i} />)}</div>
        <span className="landing-preview-run">&#9654;</span>
      </> : <>
        <div className="landing-preview-pie" />
        <div className="landing-pie-legend"><span><i /><b /></span><span><i /><b /></span><span><i /><b /></span></div>
      </>}
    </div>
  )
}

// Public entry page. Product copy follows the selected locale.
export default function LandingPage() {
  useLocale()
  return (
    <div className="landing font-sans">
      <BackgroundVideo className="landing-video" src={landingVideo} poster={landingPoster} />
      <div className="landing-container">
        <header className="landing-header">
          <span className="landing-brand"><span className="flex flex-col">
            <span className="flex items-baseline gap-2">
              <span className="font-mono text-2xl font-bold text-ink">DBCAS</span>
              <span className="text-xs font-semibold tracking-wide text-cyan-400">{t('landing.brandTag')}</span>
            </span>
            <span className="font-mono text-[10px] tracking-[.05em] text-mute">{t('landing.brandDesc')}</span>
          </span></span>
          <nav className="flex flex-wrap items-center gap-2 sm:gap-4" aria-label={t('nav.primary')}>
            <LanguageSelector /><ThemeSelector />
            <div className="landing-auth-links">
            <Link
              to="/login"
              className="rounded-lg border border-transparent px-4 py-2 text-sm font-medium text-sub transition hover:-translate-y-0.5 hover:border-cyan-400/40 hover:bg-cyan-400/5 hover:text-cyan-300 motion-reduce:transform-none"
            >
              {t('auth.signIn')}
            </Link>
            <Link
              to="/register"
              className="rounded-lg border border-transparent px-4 py-2 text-sm font-medium text-sub transition hover:-translate-y-0.5 hover:border-cyan-400/40 hover:bg-cyan-400/5 hover:text-cyan-300 motion-reduce:transform-none"
            >
              {t('auth.register')}
            </Link>
            </div>
          </nav>
        </header>

        <main>
          <div className="landing-hero">
          <section className="landing-intro" aria-labelledby="landing-title">
            <p className="landing-badge">
              <span className="flex gap-1" aria-hidden="true">
                <i className="h-2 w-2 rounded-full bg-cyan-400 opacity-75" />
                <i className="h-2 w-2 rounded-full bg-cyan-600" />
              </span>
              {t('landing.badge')}
            </p>
            <h1 id="landing-title" className="landing-title">{t('landing.title')}</h1>
            <p className="mb-9 mt-6 max-w-[760px] text-base leading-relaxed text-mute sm:text-lg">
              {t('landing.desc')}
            </p>
            <div className="landing-actions">
              <Link
                to="/register"
                className="landing-cta landing-cta-primary"
              >
                <span className="landing-cta-label">{t('landing.ctaRegister')}</span><svg className="landing-button-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M5 12h14m-6-6 6 6-6 6" /></svg>
              </Link>
              <Link
                to="/login"
                className="landing-cta landing-cta-secondary"
              >
                <span className="landing-cta-label">{t('landing.ctaSignIn')}</span>
              </Link>
            </div>
          </section>

          <div className="landing-showcase">
            <div className="landing-code-preview" aria-hidden="true">
              <div className="landing-code-toolbar"><span className="landing-window-dots"><i /><i /><i /></span><span>workspace.sql</span><span className="landing-code-engine">PostgreSQL</span></div>
              <div className="landing-code-content">
                <span className="landing-code-line"><em>01</em><span><b>SELECT</b> skills, potential</span></span>
                <span className="landing-code-line"><em>02</em><span><b>FROM</b> your_journey</span></span>
                <span className="landing-code-line"><em>03</em><span><b>WHERE</b> curiosity = <strong>TRUE</strong></span></span>
                <span className="landing-code-line"><em>04</em><span><b>ORDER BY</b> growth <b>DESC</b>;</span></span>
              </div>
              <div className="landing-code-output"><span>&gt;</span><span>Learn. Practice. Grow.</span><span className="landing-code-cursor" /></div>
            </div>
          <section className="landing-stats" aria-label={t('landing.statsLabel')}>
            {STATS.map((s) => (
              <div key={s.label} className="landing-stat-card">
                <p className={`landing-stat ${s.cls}`}>{s.value}</p>
                <div><p className="text-sm font-semibold text-ink">{t(s.label)}</p>
                <p className="mt-2 text-xs leading-relaxed text-mute">{t(s.sub)}</p></div>
              </div>
            ))}
          </section>
          </div>

          </div>

          <section className="landing-pillars" aria-labelledby="landing-pillars">
            <div className="mb-10 text-center sm:mb-12">
              <p className="inline-block rounded-full border border-cyan-500/30 bg-accent/10 px-3.5 py-1 text-xs font-semibold text-cyan-200">
                {t('landing.pillarsBadge')}
              </p>
              <h2 id="landing-pillars" className="mt-4 text-2xl font-extrabold text-ink sm:text-4xl">
                {t('landing.pillarsTitle')}
              </h2>
              <p className="mx-auto mt-4 max-w-[700px] text-sm leading-relaxed text-mute sm:text-base">
                {t('landing.pillarsDesc')}
              </p>
            </div>
            <div className="landing-feature-grid">
              {PILLARS.map((p, index) => (
                <article key={p.tag} className="landing-card flex flex-col justify-between p-6 transition hover:-translate-y-1 hover:border-cyan-400/30 sm:p-8 motion-reduce:transform-none">
                  <div>
                    <div className="mb-5 flex items-center justify-between gap-2">
                      <span className="landing-step-number" aria-hidden="true">0{index + 1}</span>
                      <span className="rounded bg-accent/10 px-2.5 py-1 font-mono text-[11px] font-bold text-cyan-300">{t(p.tag)}</span>
                      <span className="landing-feature-icon" aria-hidden="true"><FeatureIcon type={p.icon} /></span>
                    </div>
                    <FeaturePreview type={p.icon} />
                    <h3 className="text-lg font-bold text-ink">{t(p.title)}</h3>
                    <p className="mb-6 mt-3 text-sm leading-relaxed text-mute">{t(p.body)}</p>
                  </div>
                  <div className="flex items-center justify-between border-t border-edge pt-4 text-xs">
                    <span className="text-sub">{t(p.foot)}</span><span className="landing-feature-check" aria-hidden="true">&#10003;</span>
                  </div>
                </article>
              ))}
            </div>
            <div className="landing-outcomes">
              <div className="landing-outcomes-heading"><span className="landing-start-spark" aria-hidden="true">&#10022;</span><h3>{t('landing.outcomesTitle')}</h3></div>
              <div className="landing-outcomes-flow">
                {['Strength', 'Gap', 'Path'].map((item, index) => (
                  <div className="landing-outcome" key={item}><span aria-hidden="true">0{index + 1}</span><div><h4>{t(`landing.outcome${item}`)}</h4><p>{t(`landing.outcome${item}Body`)}</p></div></div>
                ))}
              </div>
            </div>
          </section>
        </main>

        <footer className="mx-auto w-full max-w-[1200px] border-t border-edge py-8 text-center text-[13px] text-mute">
          {t('landing.footer', { year: new Date().getFullYear() })}
        </footer>
      </div>
    </div>
  )
}
