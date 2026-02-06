import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load all env vars (not only VITE_) so API_PUBLIC_URL can be reused
  const env = loadEnv(mode, process.cwd(), '')
  const viteApiPublicUrl = env.VITE_API_PUBLIC_URL || ''
  const apiPublicUrlFallback = env.API_PUBLIC_URL || ''

  return {
    plugins: [react()],
    // Ensure base path is root for Vercel
    base: '/',
    // Expose fallback for local/monorepo builds.
    // Runtime resolver still applies priority: VITE_API_PUBLIC_URL -> API_PUBLIC_URL.
    define: {
      'import.meta.env.VITE_API_PUBLIC_URL': JSON.stringify(viteApiPublicUrl),
      'import.meta.env.API_PUBLIC_URL': JSON.stringify(apiPublicUrlFallback),
    },
    build: {
      // Output to dist for Vercel
      outDir: 'dist',
      // Generate sourcemaps for debugging
      sourcemap: false,
    },
    server: {
      host: '0.0.0.0',
      port: 5173,
    },
    preview: {
      host: '0.0.0.0',
      port: 3000,
    },
  }
})
