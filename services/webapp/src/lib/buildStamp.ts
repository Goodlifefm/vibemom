export interface BuildStamp {
  sha: string;
  shortSha: string;
  buildTime: string;
}

function normalize(value: unknown): string {
  return typeof value === 'string' ? value.trim() : '';
}

export function getBuildStamp(): BuildStamp {
  const sha =
    normalize(import.meta.env.VITE_BUILD_SHA) ||
    normalize((import.meta.env as Record<string, unknown>)['VITE_GIT_SHA']) ||
    normalize((import.meta.env as Record<string, unknown>)['VITE_VERCEL_GIT_COMMIT_SHA']) ||
    'unknown';

  const buildTime =
    normalize((import.meta.env as Record<string, unknown>)['VITE_BUILD_TIME']) ||
    normalize((import.meta.env as Record<string, unknown>)['VITE_BUILD_AT']) ||
    'unknown';

  const shortSha = sha !== 'unknown' && sha.length >= 7 ? sha.slice(0, 7) : sha;

  return { sha, shortSha, buildTime };
}

