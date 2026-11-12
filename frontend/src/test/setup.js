import '@testing-library/jest-dom/vitest'
import { beforeEach } from 'vitest'
import { setLocale } from '../i18n'

// Existing component assertions deliberately exercise the English translation.
// Locale detection and the Compose smoke separately verify the Vietnamese default.
beforeEach(async () => {
  await setLocale('en')
})
