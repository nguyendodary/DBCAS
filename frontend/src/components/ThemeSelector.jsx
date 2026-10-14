import { useLocale } from '../i18n'
import { useTheme } from './ThemeProvider'
import { Icon } from './ui'

export default function ThemeSelector({ className = '' }) {
  const { t } = useLocale()
  const { theme, setTheme } = useTheme()
  const next = theme === 'dark' ? 'light' : 'dark'
  const label = t(next === 'light' ? 'theme.switchToLight' : 'theme.switchToDark')
  return <button type="button" className={`header-icon-button theme-selector ${className}`}
    aria-label={label} title={label} onClick={() => setTheme(next)}>
    <Icon name={next === 'light' ? 'sun' : 'moon'} className="h-5 w-5" />
  </button>
}
