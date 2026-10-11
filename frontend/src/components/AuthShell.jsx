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

// A quiet two-column entry point: context on the left, one clear form on the right.
export default function AuthShell({ children }) {
  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-abyss px-4 py-8 text-ink sm:px-6">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            'radial-gradient(55% 50% at 15% 10%, rgba(34,211,238,0.055), transparent 70%)',
        }}
      />
      <div className="auth-enter relative grid w-full max-w-4xl overflow-hidden rounded-2xl border border-edge2/70 bg-panel shadow-xl shadow-black/20 md:grid-cols-[.95fr_1fr]">
        <aside className="hidden flex-col justify-between border-r border-edge bg-elev/35 p-8 md:flex lg:p-10">
          <div>
            <div className="flex items-center gap-2.5">
              <span className="flex h-9 w-9 items-center justify-center rounded-lg border border-cyan-400/20 bg-cyan-400/[0.08] text-cyan-300">
                <Icon name="database" className="h-5 w-5" />
              </span>
              <span className="text-base font-bold tracking-tight text-ink">DBCAS</span>
            </div>
            <h2 className="mt-14 max-w-xs text-3xl font-semibold leading-tight tracking-tight text-ink">
              Understand what you know. See what to learn next.
            </h2>
            <p className="mt-4 max-w-xs text-sm leading-6 text-sub">
              Adaptive database assessments combine multiple choice, SQL, and written answers with clear competency evidence.
            </p>
          </div>
          <ul className="mt-10 divide-y divide-edge/70">
            {FEATURES.map((f) => (
              <li
                key={f.title}
                className="flex gap-3 py-3.5"
              >
                <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-cyan-400/[0.07] text-cyan-300">
                  <Icon name={f.icon} className="h-4 w-4" />
                </span>
                <span>
                  <span className="block text-sm font-medium text-ink">{f.title}</span>
                  <span className="mt-0.5 block text-xs leading-relaxed text-mute">{f.body}</span>
                </span>
              </li>
            ))}
          </ul>
        </aside>
        <div className="flex items-center px-6 py-8 sm:px-9 sm:py-10 lg:px-11">
          <div className="mx-auto w-full max-w-sm">{children}</div>
        </div>
      </div>
    </div>
  )
}
