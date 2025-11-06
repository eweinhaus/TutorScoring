import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { readFileSync, writeFileSync } from 'fs'
import { resolve } from 'path'

// Plugin to remove crossorigin from stylesheet links
const removeCrossoriginPlugin = () => {
  return {
    name: 'remove-crossorigin',
    closeBundle() {
      const htmlPath = resolve(__dirname, 'dist/index.html')
      try {
        let html = readFileSync(htmlPath, 'utf-8')
        // Remove crossorigin from stylesheet links (not from scripts)
        html = html.replace(/<link([^>]*)\s+crossorigin([^>]*)>/g, (match, before, after) => {
          if (match.includes('stylesheet')) {
            return `<link${before}${after}>`
          }
          return match
        })
        writeFileSync(htmlPath, html)
      } catch (err) {
        // Ignore if file doesn't exist
      }
    }
  }
}

export default defineConfig({
  plugins: [react(), removeCrossoriginPlugin()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
})

