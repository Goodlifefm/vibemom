export interface BuildStamp {
  sha: string;
  shortSha: string;
  buildTime: string;
}

function normalize(value: unknown): string {
  return typeof value === 'string' ? value.trim() : '';
}

function toStamp(params: { sha: string; buildTime: string }): BuildStamp {
  const sha = params.sha || 'unknown';
  const buildTime = params.buildTime || 'unknown';
  const shortSha = sha !== 'unknown' && sha.length >= 7 ? sha.slice(0, 7) : sha;
  return { sha, shortSha, buildTime };
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

  return toStamp({ sha, buildTime });
}

type BuildJsonPayload = {
  git_sha?: string;
  build_time?: string;
  env?: string;
};

let cachedFromBuildJson: BuildStamp | null = null;

export function getBuildStampCached(): BuildStamp {
  return cachedFromBuildJson || getBuildStamp();
}

export async function loadBuildStampFromBuildJson(): Promise<BuildStamp | null> {
  if (typeof window === 'undefined') {
    return null;
  }

  try {
    const res = await fetch('/build.json', { cache: 'no-store', credentials: 'omit' });
    if (!res.ok) {
      return null;
    }
    const data = (await res.json()) as BuildJsonPayload;
    const sha = normalize(data?.git_sha) || 'unknown';
    const buildTime = normalize(data?.build_time) || 'unknown';
    const stamp = toStamp({ sha, buildTime });
    cachedFromBuildJson = stamp;
    return stamp;
  } catch {
    return null;
  }
}

