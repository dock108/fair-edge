import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Load env file from parent directory (monorepo root)
  const env = loadEnv(mode, path.resolve(process.cwd(), '..'), ['VITE_'])
  
  const config = {
    plugins: [react()],
    envDir: '../', // Look for env files in parent directory
    server: {
      host: '0.0.0.0', // Allow external connections (needed for Docker)
      port: 5173,
      watch: {
        usePolling: true, // Fix for file watching in Docker
      },
      proxy: {
        '/api': {
          target: env.VITE_API_URL || 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
        }
      }
    }
  }
  
  // Production build optimizations
  if (mode === 'production') {
    config.build = {
      outDir: 'dist',
      sourcemap: false,
      minify: 'terser',
      rollupOptions: {
        output: {
          // Cache busting with timestamp
          entryFileNames: `assets/[name]-[hash]-${Date.now()}.js`,
          chunkFileNames: `assets/[name]-[hash]-${Date.now()}.js`,
          assetFileNames: `assets/[name]-[hash]-${Date.now()}.[ext]`,
        }
      }
    }
  }
  
  return config
})
