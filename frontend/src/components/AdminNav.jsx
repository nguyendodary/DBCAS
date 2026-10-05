import { NavLink } from 'react-router-dom'

const TABS = [
  { to: '/admin', label: 'Cohort', end: true },
  { to: '/admin/curriculum', label: 'Curriculum' },
  { to: '/admin/questions', label: 'Question Bank' },
  { to: '/admin/candidates', label: 'AI Candidates' },
  { to: '/admin/assessments', label: 'Assessments' },
  { to: '/admin/accounts', label: 'Accounts' },
]

// Sub-navigation shared by every admin management screen.
export default function AdminNav() {
  return (
    <nav className="mb-6 flex flex-wrap gap-1 border-b text-sm" aria-label="Admin sections">
      {TABS.map((t) => (
        <NavLink
          key={t.to}
          to={t.to}
          end={t.end}
          className={({ isActive }) =>
            `-mb-px border-b-2 px-3 py-2 ${
              isActive
                ? 'border-blue-600 font-medium text-blue-700'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`
          }
        >
          {t.label}
        </NavLink>
      ))}
    </nav>
  )
}
