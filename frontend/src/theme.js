export const THEME_KEY = 'dbcas_theme'
export const THEME_MODES = ['dark', 'light']

export function normalizeTheme(value) {
  return THEME_MODES.includes(value) ? value : 'dark'
}

export function readThemePreference(storage) {
  try {
    const source = storage === undefined ? globalThis.localStorage : storage
    const saved = source?.getItem(THEME_KEY)
    const theme = normalizeTheme(saved)
    if (saved != null && saved !== theme) source?.setItem?.(THEME_KEY, theme)
    return theme
  }
  catch { return 'dark' }
}

export function resolveTheme(preference) {
  return normalizeTheme(preference)
}

export function applyTheme(root, resolvedTheme, preference) {
  if (!root) return
  root.dataset.theme = resolvedTheme
  root.dataset.themeMode = normalizeTheme(preference)
  root.style.colorScheme = resolvedTheme
}

export function applyThemeImmediately(root, resolvedTheme, preference, requestFrame = globalThis.requestAnimationFrame) {
  if (!root) return
  root.dataset.themeTransitioning = 'true'
  applyTheme(root, resolvedTheme, preference)
  if (typeof requestFrame !== 'function') {
    root.removeAttribute('data-theme-transitioning')
    return
  }
  requestFrame(() => requestFrame(() => root.removeAttribute('data-theme-transitioning')))
}
