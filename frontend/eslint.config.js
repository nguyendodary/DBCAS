import js from '@eslint/js'
import globals from 'globals'

export default [
  { ignores: ['dist/**', 'node_modules/**', 'playwright-report/**', 'test-results/**'] },
  js.configs.recommended,
  {
    files: ['**/*.{js,jsx}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      parserOptions: { ecmaFeatures: { jsx: true } },
      globals: globals.browser,
    },
    rules: {
      'no-unused-vars': ['error', { argsIgnorePattern: '^_', caughtErrors: 'none' }],
    },
  },
  {
    files: ['*.js', 'e2e*/**/*.js', 'src/test/**/*.{js,jsx}'],
    languageOptions: { globals: globals.node },
  },
  {
    files: ['src/test/**/*.{js,jsx}'],
    languageOptions: { globals: globals.vitest },
  },
]
