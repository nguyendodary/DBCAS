import { Icon } from './ui'

const FEATURES = [
  {
    icon: 'database',
    title: 'Sandboxed PostgreSQL execution',
    body: 'Real SQL graded safely inside an isolated Docker sandbox.',
  },
  {
    icon: 'spark',
    title: 'Adaptive, AI-assisted grading',
    body: 'Difficulty adapts to your answers; essays scored against rubrics.',
  },
  {
    icon: 'chart',
    title: 'Skill-gap analytics',
    body: 'Per-concept competency profiles with a prioritized study path.',
  },
]

// Two-panel auth layout — the prototype login's hero split rebuilt on the
// dark token set: ambient glows, a feature rail, and a translucent card.
// CSS-only (no image assets).
export default function AuthShell({ children }) {
  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-abyss px-4 py-10 text-ink">
      {/* restrained ambient glow — the prototypes' radial accents */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            'radial-gradient(45% 40% at 30% 20%, rgba(6,182,212,0.10) 0%, transparent 60%),' +
            'radial-gradient(40% 35% at 75% 75%, rgba(34,211,238,0.07) 0%, transparent 60%),' +
            'radial-gradient(30% 30% at 80% 15%, rgba(99,102,241,0.08) 0%, transparent 60%)',
        }}
      />
      <div className="relative grid w-full max-w-4xl overflow-hidden rounded-2xl border border-edge bg-panel/80 shadow-2xl shadow-black/50 backdrop-blur md:grid-cols-[1.05fr_1fr]">
        <aside className="hidden flex-col justify-between border-r border-edge bg-white/[0.02] p-8 md:flex">
          <div>
            <div className="flex items-center gap-2.5">
              <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-400/15 text-cyan-300">
                <Icon name="database" className="h-5 w-5" />
              </span>
              <span className="text-lg font-bold tracking-tight text-ink">DBCAS</span>
            </div>
            <h2 className="mt-8 text-2xl font-bold leading-snug text-ink">
              Database competency,
              <br />
              <span className="text-cyan-300">assessed by real execution.</span>
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-sub">
              Surveys, hands-on SQL work, and project analysis scored against
              academic and industry rubrics.
            </p>
          </div>
          <ul className="mt-8 space-y-3">
            {FEATURES.map((f) => (
              <li
                key={f.title}
                className="flex gap-3 rounded-xl border border-edge bg-white/[0.03] p-3"
              >
                <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-cyan-400/10 text-cyan-300">
                  <Icon name={f.icon} className="h-4 w-4" />
                </span>
                <span>
                  <span className="block text-sm font-medium text-ink">{f.title}</span>
                  <span className="block text-xs leading-relaxed text-mute">{f.body}</span>
                </span>
              </li>
            ))}
          </ul>
        </aside>
        <div className="p-6 sm:p-8">{children}</div>
      </div>
    </div>
  )
}
