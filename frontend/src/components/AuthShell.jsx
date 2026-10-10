import { Icon } from './ui'

const FEATURES = [
  'Adaptive assessment sessions',
  'Real PostgreSQL answer sandbox',
  'Per-concept competency analytics',
]

// Two-panel auth layout — the static mockups' hero split, rebuilt as a
// CSS-only brand panel (no image assets).
export default function AuthShell({ children }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100 px-4 py-8">
      <div className="flex w-full max-w-3xl overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-lg">
        <aside className="hidden w-2/5 flex-col justify-between bg-gradient-to-b from-blue-700 to-blue-950 p-8 text-white md:flex">
          <div>
            <div className="flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-md bg-white/15 text-sm font-bold">
                DB
              </span>
              <span className="text-lg font-semibold">DBCAS</span>
            </div>
            <h2 className="mt-8 text-xl font-semibold leading-snug">
              Database Competency Assessment System
            </h2>
            <p className="mt-2 text-sm text-blue-100">
              Measure real PostgreSQL skill, not just memorized answers.
            </p>
          </div>
          <ul className="space-y-3">
            {FEATURES.map((f) => (
              <li key={f} className="flex items-center gap-2 text-sm text-blue-100">
                <Icon name="check" className="h-4 w-4 text-blue-300" />
                {f}
              </li>
            ))}
          </ul>
        </aside>
        <div className="flex-1 p-6 sm:p-8">{children}</div>
      </div>
    </div>
  )
}
