import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    // Bound jsdom memory/CPU use on the shared Windows/WSL development host.
    maxWorkers: 4,
    globals: true,
    include: ['src/test/**/*.test.{js,jsx}'],
    setupFiles: './src/test/setup.js',
  },
})
