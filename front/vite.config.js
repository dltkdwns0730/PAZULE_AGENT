import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  envDir: '..',
  optimizeDeps: {
    exclude: ['heic2any']
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
      '/get-today-hint': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
    },
    fs: {
      allow: ['..']
    }
  }
})
