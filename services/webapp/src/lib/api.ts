/**
 * API client for Vibe Market Mini App.
 *
 * Demo mode is enabled only when API URL is not configured.
 */

import { getApiBaseUrl } from '../config/api';
import { getLastErrors, getLastRequest, getLastRequests, trackedFetch } from './fetcher';
import { getBuildStampCached } from './buildStamp';

const API_BASE_URL = getApiBaseUrl();
const TOKEN_KEY = 'vibe_market_token';

export type ApiErrorKind = 'network' | 'http' | 'cors' | 'unknown';

export interface ApiRequestMeta {
  url: string;
  method: string;
  startTs: number;
  endTs: number | null;
  durationMs: number | null;
}

export interface ApiErrorInfo {
  kind: ApiErrorKind;
  status?: number;
  message: string;
  request?: ApiRequestMeta;
  errorReportRequestId?: string;
}

/**
 * Check if API mode is enabled.
 */
export function isApiEnabled(): boolean {
  return API_BASE_URL !== null;
}

/**
 * Return resolved API base URL used by requests.
 */
export function getResolvedApiBaseUrl(): string | null {
  return API_BASE_URL;
}

/**
 * Get stored auth token.
 */
export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * Store auth token.
 */
export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

/**
 * Clear auth token.
 */
export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

/**
 * API error class.
 */
export class ApiError extends Error {
  readonly kind: ApiErrorKind;
  readonly status?: number;
  readonly code: string;
  readonly request?: ApiRequestMeta;
  readonly errorReportRequestId?: string;

  constructor(params: {
    kind: ApiErrorKind;
    message: string;
    status?: number;
    code?: string;
    request?: ApiRequestMeta;
    errorReportRequestId?: string;
  }) {
    super(params.message);
    this.name = 'ApiError';
    this.kind = params.kind;
    this.status = params.status;
    this.code = params.code || 'API_ERROR';
    this.request = params.request;
    this.errorReportRequestId = params.errorReportRequestId;
  }
}

/**
 * Convert unknown errors into safe diagnostics object.
 */
export function getApiErrorInfo(error: unknown): ApiErrorInfo {
  if (error instanceof ApiError) {
    return {
      kind: error.kind,
      status: error.status,
      message: error.message,
      request: error.request,
      errorReportRequestId: error.errorReportRequestId,
    };
  }
  if (error instanceof Error) {
    return {
      kind: 'unknown',
      message: error.message,
    };
  }
  return {
    kind: 'unknown',
    message: 'Unknown error',
  };
}

function isCrossOriginUrl(requestUrl: string): boolean {
  if (typeof window === 'undefined') {
    return false;
  }
  try {
    const targetOrigin = new URL(requestUrl).origin;
    return targetOrigin !== window.location.origin;
  } catch {
    return false;
  }
}

function classifyFetchError(error: unknown, requestUrl: string): ApiError {
  if (error instanceof ApiError) {
    return error;
  }

  if (error instanceof TypeError) {
    const message = error.message || 'Request failed';
    const failedToFetch = message.toLowerCase().includes('failed to fetch');
    const likelyCors = failedToFetch && isCrossOriginUrl(requestUrl);

    return new ApiError({
      kind: likelyCors ? 'cors' : 'network',
      code: likelyCors ? 'CORS_OR_NETWORK' : 'NETWORK_ERROR',
      message: message,
    });
  }

  if (error instanceof Error) {
    return new ApiError({
      kind: 'unknown',
      code: 'UNKNOWN_ERROR',
      message: error.message,
    });
  }

  return new ApiError({
    kind: 'unknown',
    code: 'UNKNOWN_ERROR',
    message: 'Unknown error',
  });
}

const CLIENT_LOG_PATH = '/debug/client-log';
const CLIENT_LOG_TIMEOUT_MS = 1200;

function safeLocationSnapshot(): {
  href: string;
  origin: string;
  pathname: string;
  search: string;
  hadHash: boolean;
  hadTgWebAppData: boolean;
} {
  if (typeof window === 'undefined') {
    return { href: '', origin: '', pathname: '', search: '', hadHash: false, hadTgWebAppData: false };
  }
  const origin = window.location.origin;
  const pathname = window.location.pathname;
  const search = window.location.search;
  const hash = String(window.location.hash || '');
  const hadHash = hash.length > 0;
  const hadTgWebAppData = hash.toLowerCase().includes('tgwebappdata=');
  return { href: `${origin}${pathname}${search}`, origin, pathname, search, hadHash, hadTgWebAppData };
}

function redact(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map((item) => redact(item));
  }
  if (value && typeof value === 'object') {
    const obj = value as Record<string, unknown>;
    const out: Record<string, unknown> = {};
    for (const [key, nested] of Object.entries(obj)) {
      const lower = key.toLowerCase();
      if (
        lower.includes('initdata') ||
        lower.includes('authorization') ||
        lower.includes('bearer') ||
        lower.includes('token') ||
        lower.includes('cookie') ||
        lower.includes('password') ||
        lower.includes('secret')
      ) {
        out[key] = '[redacted]';
        continue;
      }
      out[key] = redact(nested);
    }
    return out;
  }
  if (typeof value === 'string') {
    const lower = value.toLowerCase();
    if (
      lower.includes('tgwebappdata=') ||
      lower.includes('auth_date=') ||
      lower.includes('signature=') ||
      lower.includes('hash=') ||
      lower.includes('bearer ')
    ) {
      return '[redacted]';
    }
  }
  return value;
}

async function postClientLogRaw(payload: unknown): Promise<{ requestId: string | null } | null> {
  if (!API_BASE_URL) {
    return null;
  }

  const url = `${API_BASE_URL}${CLIENT_LOG_PATH}`;
  const controller = typeof AbortController !== 'undefined' ? new AbortController() : null;
  const timeoutId =
    controller && typeof window !== 'undefined'
      ? window.setTimeout(() => controller.abort(), CLIENT_LOG_TIMEOUT_MS)
      : null;

  try {
    const response = await trackedFetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(redact(payload)),
      credentials: 'omit',
      cache: 'no-store',
      referrerPolicy: 'no-referrer',
      signal: controller?.signal,
    });

    const text = await response.text();
    try {
      const parsed = JSON.parse(text) as { request_id?: unknown };
      const requestId = typeof parsed?.request_id === 'string' ? parsed.request_id.trim() : null;
      return { requestId: requestId || null };
    } catch {
      return { requestId: null };
    }
  } catch {
    return null;
  } finally {
    if (timeoutId !== null) {
      window.clearTimeout(timeoutId);
    }
  }
}

function shouldReportHttpStatus(status: number): boolean {
  return status >= 500;
}

async function maybeReportApiError(params: {
  error: ApiError;
  request: ApiRequestMeta;
  phase: 'fetch' | 'http' | 'parse';
}): Promise<string | null> {
  // Never recurse.
  try {
    const path = new URL(params.request.url).pathname;
    if (path === CLIENT_LOG_PATH) {
      return null;
    }
  } catch {
    // ignore
  }

  const payload = {
    ts: new Date().toISOString(),
    type: 'auto-error-report',
    phase: params.phase,
    build: getBuildStampCached(),
    location: safeLocationSnapshot(),
    userAgent: String(typeof navigator !== 'undefined' ? navigator.userAgent || '' : '').slice(0, 220),
    request: params.request,
    error: {
      name: params.error.name,
      kind: params.error.kind,
      code: params.error.code,
      status: params.error.status ?? null,
      message: params.error.message,
      stack: params.error.stack ? String(params.error.stack).slice(0, 6000) : null,
    },
    lastRequest: getLastRequest(),
    lastRequests: getLastRequests().slice(0, 10),
    lastErrors: getLastErrors().slice(0, 10),
  };

  const res = await postClientLogRaw(payload);
  return res?.requestId || null;
}

/**
 * Request options.
 */
interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  body?: unknown;
  headers?: Record<string, string>;
  skipAuth?: boolean;
}

/**
 * Make an API request.
 */
export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  if (!API_BASE_URL) {
    throw new ApiError({
      kind: 'unknown',
      code: 'API_NOT_CONFIGURED',
      message: 'API URL is not configured',
    });
  }

  const { method = 'GET', body, headers = {}, skipAuth = false } = options;

  // Only send Content-Type when we actually send a JSON body.
  // This reduces noisy preflights in constrained WebViews.
  const requestHeaders: Record<string, string> = { ...headers };
  if (body !== undefined && requestHeaders['Content-Type'] === undefined) {
    requestHeaders['Content-Type'] = 'application/json';
  }

  if (!skipAuth) {
    const token = getToken();
    if (token) {
      requestHeaders.Authorization = `Bearer ${token}`;
    }
  }

  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  const url = `${API_BASE_URL}${normalizedPath}`;
  const init: RequestInit = {
    method,
    headers: requestHeaders,
    // Telegram Mini App should never rely on cookies/credentials.
    // These defaults also reduce cross-site noise and help with deterministic debugging.
    credentials: 'omit',
    cache: 'no-store',
    referrerPolicy: 'no-referrer',
  };

  if (body !== undefined) {
    init.body = JSON.stringify(body);
  }

  const startTs = Date.now();
  const baseMeta: ApiRequestMeta = {
    url,
    method,
    startTs,
    endTs: null,
    durationMs: null,
  };

  let response: Response;
  try {
    response = await trackedFetch(url, init);
  } catch (error) {
    const endTs = Date.now();
    const requestMeta: ApiRequestMeta = {
      ...baseMeta,
      endTs,
      durationMs: Math.max(0, endTs - startTs),
    };

    const classified = classifyFetchError(error, url);
    const apiError = new ApiError({
      kind: classified.kind,
      status: classified.status,
      code: classified.code,
      message: classified.message,
      request: requestMeta,
    });

    const reportId = await maybeReportApiError({ error: apiError, request: requestMeta, phase: 'fetch' });
    if (reportId) {
      throw new ApiError({
        kind: apiError.kind,
        status: apiError.status,
        code: apiError.code,
        message: apiError.message,
        request: requestMeta,
        errorReportRequestId: reportId,
      });
    }

    throw apiError;
  }

  const endTs = Date.now();
  const requestMeta: ApiRequestMeta = {
    ...baseMeta,
    endTs,
    durationMs: Math.max(0, endTs - startTs),
  };

  if (!response.ok) {
    let errorData: { detail?: string; code?: string } = {};
    try {
      errorData = (await response.json()) as { detail?: string; code?: string };
    } catch {
      errorData = {};
    }

    const apiError = new ApiError({
      kind: 'http',
      status: response.status,
      code: errorData.code || `HTTP_${response.status}`,
      message: errorData.detail || `Request failed with status ${response.status}`,
      request: requestMeta,
    });

    if (shouldReportHttpStatus(response.status)) {
      const reportId = await maybeReportApiError({ error: apiError, request: requestMeta, phase: 'http' });
      if (reportId) {
        throw new ApiError({
          kind: apiError.kind,
          status: apiError.status,
          code: apiError.code,
          message: apiError.message,
          request: requestMeta,
          errorReportRequestId: reportId,
        });
      }
    }

    throw apiError;
  }

  const text = await response.text();
  if (!text) {
    return {} as T;
  }

  try {
    return JSON.parse(text) as T;
  } catch {
    const apiError = new ApiError({
      kind: 'unknown',
      code: 'INVALID_JSON',
      message: 'Invalid JSON response',
      request: requestMeta,
    });

    const reportId = await maybeReportApiError({ error: apiError, request: requestMeta, phase: 'parse' });
    if (reportId) {
      throw new ApiError({
        kind: apiError.kind,
        status: apiError.status,
        code: apiError.code,
        message: apiError.message,
        request: requestMeta,
        errorReportRequestId: reportId,
      });
    }

    throw apiError;
  }
}

// =============================================================================
// Auth API
// =============================================================================

interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: {
    telegram_id: number;
    username: string | null;
    full_name: string | null;
    is_admin: boolean;
  };
}

/**
 * Authenticate with Telegram initData.
 */
export async function authenticate(initData: string): Promise<AuthResponse> {
  const response = await request<AuthResponse>('/auth/telegram', {
    method: 'POST',
    body: { initData },
    skipAuth: true,
  });

  setToken(response.access_token);
  return response;
}

// =============================================================================
// Projects API
// =============================================================================

export interface Project {
  id: string;
  status: 'draft' | 'pending' | 'needs_fix' | 'approved' | 'rejected';
  revision: number;
  title_short: string;
  completion_percent: number;
  next_action: {
    action: string;
    label: string;
    cta_enabled: boolean;
  };
  can_edit: boolean;
  can_submit: boolean;
  can_archive: boolean;
  can_delete: boolean;
  created_at: string;
  updated_at: string;
  submitted_at: string | null;
  has_fix_request: boolean;
  fix_request_preview: string | null;
  current_step: string | null;
  missing_fields: string[];
}

export interface ProjectDetails {
  id: string;
  status: 'draft' | 'pending' | 'needs_fix' | 'approved' | 'rejected';
  revision: number;
  current_step: string | null;
  answers: Record<string, unknown> | null;
  fields: Record<string, unknown>;
  preview_html: string | null;
  completion_percent: number;
  missing_fields: string[];
  filled_fields: string[];
  next_action: {
    action: string;
    label: string;
    cta_enabled: boolean;
  };
  can_edit: boolean;
  can_submit: boolean;
  can_archive: boolean;
  can_delete: boolean;
  fix_request: string | null;
  moderated_at: string | null;
  created_at: string;
  updated_at: string;
  submitted_at: string | null;
}

/**
 * Get current user's projects.
 */
export async function getProjects(): Promise<Project[]> {
  return request<Project[]>('/projects/my');
}

/**
 * Create a new draft project.
 */
export async function createDraft(): Promise<ProjectDetails> {
  return request<ProjectDetails>('/projects/create_draft', {
    method: 'POST',
  });
}

/**
 * Get project details by ID.
 */
export async function getProject(id: string): Promise<ProjectDetails> {
  return request<ProjectDetails>(`/projects/${id}`);
}

// =============================================================================
// Debug API (no-auth endpoints)
// =============================================================================

export interface ClientLogResponse {
  ok: true;
  request_id: string;
  received_at: string;
}

/**
 * Send client-side logs/diagnostics to the server for debugging.
 * Must NOT include secrets (initData, tokens, cookies).
 */
export async function postClientLog(payload: unknown): Promise<ClientLogResponse> {
  return request<ClientLogResponse>('/debug/client-log', {
    method: 'POST',
    body: payload,
    skipAuth: true,
  });
}
