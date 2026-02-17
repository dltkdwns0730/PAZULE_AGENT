import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    exclude: ['heic2any']
  },
  server: {
    fs: {
      allow: ['..']
    }
  }
})
