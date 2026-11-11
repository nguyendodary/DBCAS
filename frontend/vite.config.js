import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: { assetsInlineLimit: 0 },
  server: {
    proxy: {
      // The Compose stack publishes the API on 18000; a host-run backend uses
      // 8000. Override only for local UI review.
      '/api': process.env.VITE_API_PROXY || 'http://localhost:8000',
    },
  },
})
