import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    exclude: ['heic2any']
  },
  server: {
    proxy: {
      '/api': 'http://localhost:8080',
      '/get-today-hint': 'http://localhost:8080',
    },
    fs: {
      allow: ['..']
    }
  }
})
