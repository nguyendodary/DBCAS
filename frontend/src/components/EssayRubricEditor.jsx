import { t, useLocale, number } from '../i18n'
import { inputCls } from './SharedComponents'

export const RUBRIC_LEVELS = ['Incomplete', 'Partial', 'Mostly Complete', 'Complete']

export function rubricRows(value, points, redistribute = false) {
  let saved = []
  try { saved = JSON.parse(value || '[]') } catch { /* New forms start empty. */ }
  if (!Array.isArray(saved)) saved = []
  const total = Math.round(Number(points) * 100)
  const valid = Number.isFinite(total) && total >= 3
  return RUBRIC_LEVELS.map((level, index) => {
    const existing = saved.find(row => row.level_name === level)
    const low = valid ? Math.floor((total + 1) * index / 4) / 100 : 0
    const high = valid ? (index === 3 ? total : Math.floor((total + 1) * (index + 1) / 4) - 1) / 100 : 0
    return {
      level_name: level,
      min_score: !redistribute && existing ? existing.min_score : low,
      max_score: !redistribute && existing ? existing.max_score : high,
      criteria: existing?.criteria || '',
    }
  })
}

export default function EssayRubricEditor({ value, points, onChange }) {
  useLocale()
  const rows = rubricRows(value, points)
  return <fieldset className="mt-4 min-w-0 space-y-3">
    <legend className="text-sm font-semibold text-ink">{t('admin.questions.rubricTitle')}</legend>
    <p className="text-sm leading-relaxed text-sub">{t('admin.questions.rubricHelp')}</p>
    <div className="space-y-3">
      {rows.map((row, index) => <div key={row.level_name} className="grid gap-3 rounded-xl border border-edge bg-panel p-4 sm:grid-cols-[10rem_1fr]">
        <div>
          <span className="block text-sm font-semibold text-ink">{t(`admin.questions.rubricLevel${index}`)}</span>
          <span className="mt-1 block text-sm text-sub">{number(Number(row.min_score))} – {number(Number(row.max_score))} {t('common.points')}</span>
        </div>
        <label className="grid gap-2 text-xs font-medium text-sub">
          {t('admin.questions.rubricCriteria', { level: t(`admin.questions.rubricLevel${index}`) })}
          <textarea required rows={3} value={row.criteria} placeholder={t(`admin.questions.rubricHint${index}`)}
            onChange={e => onChange(JSON.stringify(rows.map((item, i) => i === index ? { ...item, criteria: e.target.value } : item)))}
            className={`${inputCls} w-full resize-y !text-sm`} />
        </label>
      </div>)}
    </div>
  </fieldset>
}
