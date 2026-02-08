import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
const apiOrigin = process.env.VITE_API_URL || 'http://localhost:8000'
const wsOrigin = apiOrigin.replace(/^http/, 'ws')

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: apiOrigin,
        changeOrigin: true,
      },
      '/ws': {
        target: wsOrigin,
        ws: true,
      },
    },
  },
})
