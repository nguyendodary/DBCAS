export const THEME_KEY = 'dbcas_theme'
export const THEME_MODES = ['light', 'dark', 'system']
export const SYSTEM_COLOR_SCHEME = '(prefers-color-scheme: dark)'

export function normalizeTheme(value) {
  return THEME_MODES.includes(value) ? value : 'system'
}

export function readThemePreference(storage) {
  try {
    const source = storage === undefined ? globalThis.localStorage : storage
    return normalizeTheme(source?.getItem(THEME_KEY))
  }
  catch { return 'system' }
}

export function resolveTheme(preference, systemTheme) {
  const mode = normalizeTheme(preference)
  return mode === 'system' ? (systemTheme === 'dark' ? 'dark' : 'light') : mode
}

export function currentSystemTheme(matchMedia = globalThis.window?.matchMedia) {
  try { return matchMedia?.call(globalThis.window, SYSTEM_COLOR_SCHEME).matches ? 'dark' : 'light' }
  catch { return 'light' }
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
