import { defineConfig } from 'vite'

// Machine convention: fixed localhost:5173 (strictPort); dev proxy /api -> backend.
export default defineConfig({
  server: {
    host: 'localhost',
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
