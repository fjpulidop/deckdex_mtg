import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
const apiOrigin = process.env.VITE_API_URL || 'http://localhost:8000'
const wsOrigin = apiOrigin.replace(/^http/, 'ws')

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
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
