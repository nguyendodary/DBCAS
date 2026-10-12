import { createContext, useCallback, useContext, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { applyTheme, applyThemeImmediately, currentSystemTheme, readThemePreference, SYSTEM_COLOR_SCHEME, THEME_KEY, THEME_MODES } from '../theme'

const ThemeContext = createContext({ theme: 'system', resolvedTheme: 'dark', setTheme: () => false })

export function useTheme() {
  return useContext(ThemeContext)
}

export default function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState(readThemePreference)
  const [systemTheme, setSystemTheme] = useState(currentSystemTheme)
  const preferenceRef = useRef(theme)
  const systemThemeRef = useRef(systemTheme)
  const resolvedTheme = theme === 'system' ? systemTheme : theme

  useLayoutEffect(() => {
    applyTheme(document.documentElement, resolvedTheme, theme)
  }, [resolvedTheme, theme])

  useEffect(() => {
    if (typeof window.matchMedia !== 'function') return undefined
    const query = window.matchMedia(SYSTEM_COLOR_SCHEME)
    const update = (event) => {
      const next = event.matches ? 'dark' : 'light'
      systemThemeRef.current = next
      if (preferenceRef.current === 'system') applyThemeImmediately(document.documentElement, next, 'system')
      setSystemTheme(next)
    }
    update(query)
    const modernListener = typeof query.addEventListener === 'function'
    if (modernListener) query.addEventListener('change', update)
    else query.addListener?.(update)
    return () => {
      if (modernListener) query.removeEventListener('change', update)
      else query.removeListener?.(update)
    }
  }, [])

  const setTheme = useCallback((value) => {
    if (!THEME_MODES.includes(value)) return false
    try { globalThis.localStorage?.setItem(THEME_KEY, value) }
    catch { /* Keep the selected mode for this visit if storage is unavailable. */ }
    preferenceRef.current = value
    applyThemeImmediately(document.documentElement, value === 'system' ? systemThemeRef.current : value, value)
    setThemeState(value)
    return true
  }, [])

  const value = useMemo(() => ({ theme, resolvedTheme, setTheme }), [theme, resolvedTheme, setTheme])
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}
