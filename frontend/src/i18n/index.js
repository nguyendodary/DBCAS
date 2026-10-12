import i18next from 'i18next'
import { useSyncExternalStore } from 'react'
import en from './en.json'
import vi from './vi.json'

export const LOCALE_KEY = 'dbcas_locale'
export const SUPPORTED_LOCALES = ['en', 'vi']
export const resources = { en: { translation: en }, vi: { translation: vi } }

export function detectLocale(storage, languages) {
  try {
    const saved = storage?.getItem(LOCALE_KEY)
    if (SUPPORTED_LOCALES.includes(saved)) return saved
  } catch { /* Storage can be disabled; an in-memory preference still works. */ }
  const preferred = (languages?.[0] || '').toLowerCase().split('-')[0]
  return SUPPORTED_LOCALES.includes(preferred) ? preferred : 'en'
}

function browserLocale() {
  let storage
  try { storage = globalThis.localStorage } catch { /* restricted browser storage */ }
  return detectLocale(storage, globalThis.navigator?.languages || [globalThis.navigator?.language])
}

export const i18n = i18next.createInstance()
i18n.init({
  resources,
  lng: browserLocale(),
  supportedLngs: SUPPORTED_LOCALES,
  fallbackLng: false,
  initAsync: false,
  interpolation: { escapeValue: false }, // React escapes rendered text.
  returnNull: false,
  returnEmptyString: false,
})

function syncDocument() {
  if (typeof document !== 'undefined') document.documentElement.lang = i18n.language
}
i18n.on('languageChanged', syncDocument)
syncDocument()

export async function setLocale(locale) {
  if (!SUPPORTED_LOCALES.includes(locale)) return false
  try { localStorage.setItem(LOCALE_KEY, locale) } catch { /* keep the selection for this visit */ }
  await i18n.changeLanguage(locale)
  return true
}

const subscribe = (listener) => {
  i18n.on('languageChanged', listener)
  return () => i18n.off('languageChanged', listener)
}
const snapshot = () => i18n.language

// A stable translator avoids changing assessment callbacks or re-fetching data
// when the locale changes. Only rendering subscribes to the language event.
export function useLocale() {
  const locale = useSyncExternalStore(subscribe, snapshot, () => 'en')
  return { locale, setLocale, t, number, percent, dateTime, time, dateOnly }
}

export function t(key, options) {
  if (!i18n.exists(key, options)) {
    if (import.meta.env.DEV) throw new Error(`Missing DBCAS translation: ${key}`)
    return i18n.t('common.missingTranslation')
  }
  return i18n.t(key, options)
}

// Keep asynchronous messages language-neutral until render, so switching
// languages also updates an existing error or success notice.
export const message = (key, values) => ({ translationKey: key, values })
export const resolveMessage = (value) => value?.translationKey ? t(value.translationKey, value.values) : value
export const statusLabel = (value) => {
  const key = typeof value === 'string' ? value.toLowerCase() : ''
  return Object.hasOwn(resources.en.translation.status || {}, key) ? t(`status.${key}`) : t('common.unknown')
}
export const typeLabel = (value) => ['mcq', 'sql', 'essay'].includes(value) ? t(`assessment.type.${value}`) : t('common.unknown')

export const intlLocale = () => i18n.language === 'vi' ? 'vi-VN' : 'en-US'
export function number(value, options = {}) {
  if (value === null || value === undefined || value === '' || !Number.isFinite(Number(value))) return '—'
  return new Intl.NumberFormat(intlLocale(), { maximumFractionDigits: 2, ...options }).format(Number(value))
}
export const percent = (value, options = {}) => value == null ? '—' : number(Number(value) / 100, { style: 'percent', maximumFractionDigits: 2, ...options })
function formatDate(value, options) {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '—' : new Intl.DateTimeFormat(intlLocale(), options).format(date)
}
export const dateTime = (value) => formatDate(value, { dateStyle: 'medium', timeStyle: 'short' })
export const time = (value) => formatDate(value, { timeStyle: 'medium' })
// Daily analytics buckets are calendar dates, not timestamps to shift zones.
export const dateOnly = (value) => formatDate(/^\d{4}-\d{2}-\d{2}$/.test(value || '') ? `${value}T00:00:00Z` : value, { dateStyle: 'medium', timeZone: 'UTC' })
