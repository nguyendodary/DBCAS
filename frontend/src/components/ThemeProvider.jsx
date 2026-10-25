import { createContext, useCallback, useContext, useLayoutEffect, useMemo, useState } from 'react'
import { applyTheme, applyThemeImmediately, readThemePreference, THEME_KEY, THEME_MODES } from '../theme'

const ThemeContext = createContext({ theme: 'dark', resolvedTheme: 'dark', setTheme: () => false })

export function useTheme() { return useContext(ThemeContext) }

export default function ThemeProvider({ children, storageKey = THEME_KEY, defaultTheme = 'dark', restoreOnUnmount = false }) {
  const [theme, setThemeState] = useState(() => {
    if (storageKey === THEME_KEY) return readThemePreference()
    try {
      const saved = globalThis.localStorage?.getItem(storageKey)
      return THEME_MODES.includes(saved) ? saved : defaultTheme
    } catch { return defaultTheme }
  })
  useLayoutEffect(() => {
    if (!restoreOnUnmount) return
    const root = document.documentElement
    const previous = readThemePreference()
    return () => applyThemeImmediately(root, previous, previous)
  }, [restoreOnUnmount])
  useLayoutEffect(() => {
    applyTheme(document.documentElement, theme, theme)
  }, [theme])
  const setTheme = useCallback((value) => {
    if (!THEME_MODES.includes(value)) return false
    try { globalThis.localStorage?.setItem(storageKey, value) }
    catch { /* Keep the selected mode for this visit if storage is unavailable. */ }
    applyThemeImmediately(document.documentElement, value, value)
    setThemeState(value)
    return true
  }, [storageKey])
  const value = useMemo(() => ({ theme, resolvedTheme: theme, setTheme }), [theme, setTheme])
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}
