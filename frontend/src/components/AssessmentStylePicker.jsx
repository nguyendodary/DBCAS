import { t, useLocale } from '../i18n'
import { ADAPTIVE, FIXED } from '../assessmentStyle'

const OPTIONS = [
  {
    value: FIXED,
    title: 'ui.mode.bankTitle',
    description: 'ui.mode.bankDescription',
  },
  {
    value: ADAPTIVE,
    title: 'ui.mode.aiTitle',
    description: 'ui.mode.aiDescription',
  },
]

export default function AssessmentStylePicker({
  value,
  onChange,
  disabled = false,
  allowAi = true,
}) {
  useLocale()
  const options = allowAi ? OPTIONS : OPTIONS.filter((option) => option.value === FIXED)
  return (
    <fieldset disabled={disabled} className="min-w-0">
      <legend className="mb-3 text-lg font-semibold">{t('assessmentStyle.title')}</legend>
      <div
        className="grid gap-3 sm:grid-cols-2"
        role="radiogroup"
        aria-label={t('assessmentStyle.title')}
      >
        {options.map((option) => {
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
          <p className="font-semibold text-ink">{t('ui.mode.aiConstraintsTitle')}</p>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            <li>{t('ui.mode.aiConstraintConcept')}</li>
            <li>{t('ui.mode.aiConstraintBand')}</li>
            <li>{t('ui.mode.aiConstraintLive')}</li>
            <li>{t('ui.mode.aiConstraintFallback')}</li>
          </ul>
        </div>
      )}
    </fieldset>
  )
}
