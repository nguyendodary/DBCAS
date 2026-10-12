import { useId } from 'react'
import { useLocale } from '../i18n'

export default function LanguageSelector({ className = '' }) {
  const id = useId()
  const { locale, setLocale, t } = useLocale()
  return <div className={`language-selector ${className}`}>
    <label htmlFor={id} className="sr-only">{t('common.language')}</label>
    <select id={id} value={locale} onChange={(event) => setLocale(event.target.value)}
      className="min-h-10 max-w-full rounded-lg border border-edge2 bg-panel px-3 py-2 text-xs font-medium text-sub focus:border-accent">
      <option value="en" lang="en">English</option>
      <option value="vi" lang="vi">Tiếng Việt</option>
    </select>
  </div>
}
