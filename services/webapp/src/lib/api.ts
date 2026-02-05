/**
 * API client for Vibe Market Mini App.
 *
 * When VITE_API_PUBLIC_URL is not set, falls back to demo mode.
 */

// API base URL from environment
const API_BASE = import.meta.env.VITE_API_PUBLIC_URL || '';

// Token storage key
const TOKEN_KEY = 'vibe_market_token';

/**
 * Check if API mode is enabled (VITE_API_PUBLIC_URL is set)
 */
export function isApiEnabled(): boolean {
  return !!API_BASE;
}

/**
 * Get stored auth token
 */
export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * Store auth token
 */
export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

/**
 * Clear auth token
 */
export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

/**
 * API error class
 */
export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Request options
 */
interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  body?: unknown;
  headers?: Record<string, string>;
  skipAuth?: boolean;
}

/**
 * Make an API request
 */
export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  if (!API_BASE) {
    throw new ApiError(0, 'API_NOT_CONFIGURED', 'API URL is not configured');
  }

  const { method = 'GET', body, headers = {}, skipAuth = false } = options;

  // Build headers
  const requestHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    ...headers,
  };

  // Add auth token if available and not skipped
  if (!skipAuth) {
    const token = getToken();
    if (token) {
      requestHeaders['Authorization'] = `Bearer ${token}`;
    }
  }

  // Build request
  const url = `${API_BASE}${path}`;
  const init: RequestInit = {
    method,
    headers: requestHeaders,
  };

  if (body !== undefined) {
    init.body = JSON.stringify(body);
  }

  // Make request
  const response = await fetch(url, init);

  // Handle response
  if (!response.ok) {
    let errorData: { detail?: string; code?: string } = {};
    try {
      errorData = await response.json();
    } catch {
      // Response may not be JSON
    }
    throw new ApiError(
      response.status,
      errorData.code || `HTTP_${response.status}`,
      errorData.detail || `Request failed with status ${response.status}`
    );
  }

  // Parse response (handle empty responses)
  const text = await response.text();
  if (!text) {
    return {} as T;
  }
  return JSON.parse(text) as T;
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
 * Authenticate with Telegram initData
 */
export async function authenticate(initData: string): Promise<AuthResponse> {
  const response = await request<AuthResponse>('/auth/telegram', {
    method: 'POST',
    body: { initData },
    skipAuth: true,
  });

  // Store token
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
 * Get current user's projects
 */
export async function getProjects(): Promise<Project[]> {
  return request<Project[]>('/projects/my');
}

/**
 * Create a new draft project
 */
export async function createDraft(): Promise<ProjectDetails> {
  return request<ProjectDetails>('/projects/create_draft', {
    method: 'POST',
  });
}

/**
 * Get project details by ID
 */
export async function getProject(id: string): Promise<ProjectDetails> {
  return request<ProjectDetails>(`/projects/${id}`);
}
