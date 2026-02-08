import fs from 'node:fs'
import path from 'node:path'
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load all env vars (not only VITE_) so API_PUBLIC_URL can be reused
  const env = loadEnv(mode, process.cwd(), '')
  const getEnv = (key: string): string => env[key] || process.env[key] || ''

  // Prefer build.json when present so UI stamp matches /build.json.
  let buildJson: { git_sha?: string; build_time?: string; env?: string } | null = null
  try {
    const p = path.join(process.cwd(), 'public', 'build.json')
    const raw = fs.readFileSync(p, 'utf8')
    buildJson = JSON.parse(raw) as { git_sha?: string; build_time?: string; env?: string }
  } catch {
    buildJson = null
  }

  const viteApiPublicUrl = getEnv('VITE_API_PUBLIC_URL')
  const apiPublicUrlFallback = getEnv('API_PUBLIC_URL')
  // Prefer explicit VITE_* envs, then fall back to common CI variables (Vercel, etc).
  const buildSha =
    getEnv('VITE_BUILD_SHA') ||
    getEnv('VITE_GIT_SHA') ||
    getEnv('GIT_SHA') ||
    getEnv('VERCEL_GIT_COMMIT_SHA') ||
    (buildJson?.git_sha || '') ||
    ''
  // Always stamp build time to remove ambiguity in Telegram WebView.
  const buildTime =
    getEnv('VITE_BUILD_TIME') || getEnv('BUILD_TIME') || (buildJson?.build_time || '') || new Date().toISOString()
  const selfTestFlag = getEnv('VITE_SELF_TEST')

  return {
    plugins: [react()],
    // Ensure base path is root for Vercel
    base: '/',
    // Expose fallback for local/monorepo builds.
    // Runtime resolver still applies priority: VITE_API_PUBLIC_URL -> API_PUBLIC_URL.
    define: {
      'import.meta.env.VITE_API_PUBLIC_URL': JSON.stringify(viteApiPublicUrl),
      'import.meta.env.API_PUBLIC_URL': JSON.stringify(apiPublicUrlFallback),
      'import.meta.env.VITE_BUILD_SHA': JSON.stringify(buildSha),
      'import.meta.env.VITE_GIT_SHA': JSON.stringify(buildSha),
      'import.meta.env.VITE_BUILD_TIME': JSON.stringify(buildTime),
      'import.meta.env.VITE_BUILD_ENV': JSON.stringify(buildJson?.env || getEnv('VERCEL_ENV') || ''),
      'import.meta.env.VITE_SELF_TEST': JSON.stringify(selfTestFlag),
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
