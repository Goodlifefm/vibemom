/**
 * API URL configuration for webapp runtime.
 *
 * Priority:
 * 1. VITE_API_PUBLIC_URL (recommended for Vercel/client builds)
 * 2. API_PUBLIC_URL (fallback for local/monorepo convenience)
 */

function normalizeApiBaseUrl(value: string | undefined): string | null {
  const trimmed = value?.trim();
  if (!trimmed) {
    return null;
  }
  return trimmed.replace(/\/+$/, '');
}

export function getApiBaseUrl(): string | null {
  const viteUrl = normalizeApiBaseUrl(import.meta.env.VITE_API_PUBLIC_URL);
  if (viteUrl) {
    return viteUrl;
  }
  return normalizeApiBaseUrl(import.meta.env.API_PUBLIC_URL);
}

