import { defineConfig, mergeConfig } from 'vite'
import base from './vite.config.js'
import http from 'node:http'

export default mergeConfig(base, defineConfig({
  server: { host: '127.0.0.1', port: 5174, strictPort: true, proxy: {
    '/api': { target: 'http://127.0.0.1:8100', agent: new http.Agent({ keepAlive: false }) },
  } },
}))
