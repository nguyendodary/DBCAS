import { useId } from 'react'
import { useLocale } from '../i18n'
import { useTheme } from './ThemeProvider'
import { Icon } from './ui'

const MODE_ICON = { light: 'sun', dark: 'moon', system: 'monitor' }

export default function ThemeSelector({ className = '' }) {
  const id = useId()
  const { t } = useLocale()
  const { theme, setTheme } = useTheme()
  return <div className={`theme-selector inline-flex min-w-0 items-center gap-1.5 ${className}`}>
    <Icon name={MODE_ICON[theme]} className="h-4 w-4 shrink-0 text-mute" />
    <label htmlFor={id} className="sr-only">{t('theme.select')}</label>
    <select
      id={id}
      value={theme}
      onChange={(event) => setTheme(event.target.value)}
      className="min-h-10 max-w-32 rounded-lg border border-edge2 bg-panel px-2.5 py-2 text-xs font-medium text-sub focus:border-accent"
    >
      <option value="light">{t('theme.light')}</option>
      <option value="dark">{t('theme.dark')}</option>
      <option value="system">{t('theme.system')}</option>
    </select>
  </div>
}
