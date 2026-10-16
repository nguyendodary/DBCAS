import { useEffect } from 'react'
import { i18n, t } from './index'

// Keep native constraint validation and focus behavior, but use the selected
// application locale rather than the browser installation's language.
export function constraintMessage(control) {
  const v = control.validity
  if (v.valueMissing) return t('validation.required')
  if (v.typeMismatch) return t(control.type === 'email' ? 'validation.email' : 'validation.format')
  if (v.rangeUnderflow) return t('validation.minimum', { value: control.min })
  if (v.rangeOverflow) return t('validation.maximum', { value: control.max })
  if (v.tooShort) return t('validation.minLength', { count: control.minLength })
  if (v.tooLong) return t('validation.maxLength', { count: control.maxLength })
  if (v.badInput || v.stepMismatch) return t('validation.number')
  if (v.patternMismatch) return t('validation.format')
  return ''
}

export function useLocalizedValidation() {
  useEffect(() => {
    const managed = new WeakSet()
    const update = (control) => {
      if (!control?.validity || !control.form) return
      if (managed.has(control)) control.setCustomValidity('')
      if (control.validity.customError) return // Respect an independently supplied domain validation.
      const text = constraintMessage(control)
      control.setCustomValidity(text)
      managed.add(control)
    }
    const invalid = (event) => update(event.target)
    const input = (event) => {
      if (managed.has(event.target)) event.target.setCustomValidity('')
    }
    const language = () => document.querySelectorAll('input, select, textarea').forEach(control => {
      if (managed.has(control)) update(control)
    })
    document.addEventListener('invalid', invalid, true)
    document.addEventListener('input', input, true)
    document.addEventListener('change', input, true)
    i18n.on('languageChanged', language)
    return () => {
      document.removeEventListener('invalid', invalid, true)
      document.removeEventListener('input', input, true)
      document.removeEventListener('change', input, true)
      i18n.off('languageChanged', language)
    }
  }, [])
}
