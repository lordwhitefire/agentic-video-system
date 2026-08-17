import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The React workspace frontend is served by FastAPI under /workspace.
// - base: built asset URLs are rooted at /workspace/assets
// - build.outDir: ../static/react — FastAPI serves this directory
// - server.proxy: in dev (vite dev), /api calls reach the FastAPI backend
export default defineConfig({
  plugins: [react()],
  base: '/workspace/',
  build: {
    outDir: '../static/react',
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})