import { execSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

function normalize(value) {
  return typeof value === 'string' ? value.trim() : '';
}

function coerceEnv(value) {
  return value === 'production' ? 'production' : 'preview';
}

function safeExec(cmd) {
  try {
    return String(execSync(cmd, { stdio: ['ignore', 'pipe', 'ignore'] })).trim();
  } catch {
    return '';
  }
}

function resolveGitSha() {
  const envSha =
    normalize(process.env.VITE_BUILD_SHA) ||
    normalize(process.env.VITE_GIT_SHA) ||
    normalize(process.env.GIT_SHA) ||
    normalize(process.env.VERCEL_GIT_COMMIT_SHA) ||
    normalize(process.env.GITHUB_SHA);

  if (envSha) {
    return envSha;
  }

  // Fallback for local builds.
  return safeExec('git rev-parse HEAD');
}

const gitSha = resolveGitSha() || 'unknown';
const buildTime = normalize(process.env.VITE_BUILD_TIME) || normalize(process.env.BUILD_TIME) || new Date().toISOString();
const env = coerceEnv(normalize(process.env.VERCEL_ENV) || normalize(process.env.NODE_ENV));

const payload = {
  git_sha: gitSha,
  build_time: buildTime,
  env,
};

const publicDir = path.join(process.cwd(), 'public');
fs.mkdirSync(publicDir, { recursive: true });
fs.writeFileSync(path.join(publicDir, 'build.json'), JSON.stringify(payload, null, 2) + '\n', 'utf8');

// eslint-disable-next-line no-console
console.log(`[build] wrote public/build.json sha=${gitSha.slice(0, 7)} time=${buildTime} env=${env}`);

