import { t, useLocale } from '../i18n'
import { ADAPTIVE, ADAPTIVE_MAX_QUESTIONS, ADAPTIVE_MIN_QUESTIONS, FIXED } from '../assessmentStyle'

const OPTIONS = [
  {
    value: FIXED,
    title: 'assessmentStyle.fixed.title',
    description: 'assessmentStyle.fixed.description',
  },
  {
    value: ADAPTIVE,
    title: 'assessmentStyle.adaptive.title',
    description: 'assessmentStyle.adaptive.description',
  },
]

export default function AssessmentStylePicker({ value, onChange, disabled = false }) {
  useLocale()
  return (
    <fieldset disabled={disabled} className="min-w-0">
      <legend className="mb-3 text-lg font-semibold">{t('assessmentStyle.title')}</legend>
      <div
        className="grid gap-3 sm:grid-cols-2"
        role="radiogroup"
        aria-label={t('assessmentStyle.title')}
      >
        {OPTIONS.map((option) => {
          const selected = value === option.value
          return (
            <label
              key={option.value}
              className={`flex cursor-pointer flex-col gap-1 rounded-xl border p-4 ${
                selected ? 'border-cyan-400 bg-cyan-400/10' : 'border-edge'
              }`}
            >
              <span className="flex items-center gap-3">
                <input
                  type="radio"
                  name="assessment-style"
                  value={option.value}
                  checked={selected}
                  aria-label={t(option.title)}
                  onChange={() => onChange(option.value)}
                />
                <span className="font-semibold text-ink">{t(option.title)}</span>
              </span>
              <span className="text-sm text-sub">{t(option.description)}</span>
            </label>
          )
        })}
      </div>
      {value === FIXED && (
        <div
          role="status"
          className="mt-3 rounded-lg border border-cyan-400/40 bg-cyan-400/10 p-3 text-sm text-sub"
        >
          <p className="font-semibold text-ink">{t('assessmentStyle.fixed.constraintsTitle')}</p>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            <li>{t('assessmentStyle.fixed.constraintBank')}</li>
            <li>{t('assessmentStyle.fixed.constraintBand')}</li>
            <li>{t('assessmentStyle.fixed.constraintScore')}</li>
          </ul>
        </div>
      )}
      {value === ADAPTIVE && (
        <div
          role="status"
          className="mt-3 rounded-lg border border-cyan-400/40 bg-cyan-400/10 p-3 text-sm text-sub"
        >
          <p className="font-semibold text-ink">{t('assessmentStyle.adaptive.constraintsTitle')}</p>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            <li>{t('assessmentStyle.adaptive.constraintBank')}</li>
            <li>{t('assessmentStyle.adaptive.constraintConcept')}</li>
            <li>{t('assessmentStyle.adaptive.constraintMcq')}</li>
            <li>
              {t('assessmentStyle.adaptive.constraintRange', {
                min: ADAPTIVE_MIN_QUESTIONS,
                max: ADAPTIVE_MAX_QUESTIONS,
              })}
            </li>
          </ul>
        </div>
      )}
    </fieldset>
  )
}
