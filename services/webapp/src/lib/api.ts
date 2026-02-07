/**
 * API client for Vibe Market Mini App.
 *
 * Demo mode is enabled only when API URL is not configured.
 */

import { getApiBaseUrl } from '../config/api';

const API_BASE_URL = getApiBaseUrl();
const TOKEN_KEY = 'vibe_market_token';

export type ApiErrorKind = 'network' | 'http' | 'cors' | 'unknown';

export interface ApiErrorInfo {
  kind: ApiErrorKind;
  status?: number;
  message: string;
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

  constructor(params: { kind: ApiErrorKind; message: string; status?: number; code?: string }) {
    super(params.message);
    this.name = 'ApiError';
    this.kind = params.kind;
    this.status = params.status;
    this.code = params.code || 'API_ERROR';
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
  };

  if (body !== undefined) {
    init.body = JSON.stringify(body);
  }

  let response: Response;
  try {
    response = await fetch(url, init);
  } catch (error) {
    throw classifyFetchError(error, url);
  }

  if (!response.ok) {
    let errorData: { detail?: string; code?: string } = {};
    try {
      errorData = (await response.json()) as { detail?: string; code?: string };
    } catch {
      errorData = {};
    }

    throw new ApiError({
      kind: 'http',
      status: response.status,
      code: errorData.code || `HTTP_${response.status}`,
      message: errorData.detail || `Request failed with status ${response.status}`,
    });
  }

  const text = await response.text();
  if (!text) {
    return {} as T;
  }

  try {
    return JSON.parse(text) as T;
  } catch {
    throw new ApiError({
      kind: 'unknown',
      code: 'INVALID_JSON',
      message: 'Invalid JSON response',
    });
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
