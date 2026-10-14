import { createContext, useCallback, useContext, useLayoutEffect, useMemo, useState } from 'react'
import { applyTheme, applyThemeImmediately, readThemePreference, THEME_KEY, THEME_MODES } from '../theme'

const ThemeContext = createContext({ theme: 'dark', resolvedTheme: 'dark', setTheme: () => false })

export function useTheme() { return useContext(ThemeContext) }

export default function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState(readThemePreference)
  useLayoutEffect(() => {
    applyTheme(document.documentElement, theme, theme)
  }, [theme])
  const setTheme = useCallback((value) => {
    if (!THEME_MODES.includes(value)) return false
    try { globalThis.localStorage?.setItem(THEME_KEY, value) }
    catch { /* Keep the selected mode for this visit if storage is unavailable. */ }
    applyThemeImmediately(document.documentElement, value, value)
    setThemeState(value)
    return true
  }, [])
  const value = useMemo(() => ({ theme, resolvedTheme: theme, setTheme }), [theme, setTheme])
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}
