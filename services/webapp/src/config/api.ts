/**
 * API URL configuration for webapp runtime.
 *
 * Priority:
 * 1. VITE_API_PUBLIC_URL (recommended for Vercel/client builds)
 * 2. API_PUBLIC_URL (fallback for local/monorepo convenience)
 * 3. Inferred production fallback when hosted on app.vibemom.ru
 */

function normalizeApiBaseUrl(value: string | undefined): string | null {
  const trimmed = value?.trim();
  if (!trimmed) {
    return null;
  }
  return trimmed.replace(/\/+$/, '');
}

function inferApiBaseUrlFromLocation(): string | null {
  if (typeof window === 'undefined') {
    return null;
  }

  const host = String(window.location.hostname || '').toLowerCase();
  if (!host) {
    return null;
  }

  // Never auto-target production API for Vercel previews unless explicitly configured.
  if (host.endsWith('.vercel.app')) {
    return null;
  }

  // Vibemom production mapping: app.vibemom.ru -> api.vibemom.ru
  if (host === 'app.vibemom.ru') {
    return 'https://api.vibemom.ru';
  }

  // Also allow root domain hosts to infer the API.
  if (host === 'vibemom.ru' || host === 'www.vibemom.ru') {
    return 'https://api.vibemom.ru';
  }

  return null;
}

export function getApiBaseUrl(): string | null {
  const viteUrl = normalizeApiBaseUrl(import.meta.env.VITE_API_PUBLIC_URL);
  if (viteUrl) {
    return viteUrl;
  }
  const fallback = normalizeApiBaseUrl(import.meta.env.API_PUBLIC_URL);
  if (fallback) {
    return fallback;
  }
  return inferApiBaseUrlFromLocation();
}
