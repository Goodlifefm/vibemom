/**
 * API client for Vibe Market Mini App
 */

import type { AuthResponse, ProjectDetails, ProjectListItem, ApiError } from './types';

// Get API URL from env - optional in demo mode
const API_BASE_URL = import.meta.env.VITE_API_PUBLIC_URL || '';

// Demo mode: enabled when API URL is not set OR explicitly via env
const DEMO_MODE = !API_BASE_URL || import.meta.env.VITE_DEMO_MODE === 'true';

// Diagnostic info for debugging
export const diagnosticInfo = {
  apiBaseUrl: API_BASE_URL || '(not set)',
  demoMode: DEMO_MODE,
  initDataPresent: (): boolean => !!window.Telegram?.WebApp?.initData,
  lastError: null as string | null,
};

// Check if API URL is configured
export function isApiConfigured(): boolean {
  return !!API_BASE_URL && API_BASE_URL.trim().length > 0;
}

// Check if we're in demo mode
export function isDemoMode(): boolean {
  return DEMO_MODE;
}

// ============================================
// DEMO DATA - Mock data for standalone mode
// ============================================

const DEMO_USER = {
  telegram_id: 123456789,
  username: 'demo_user',
  full_name: 'Demo User',
  is_admin: false,
};

const DEMO_PROJECTS: ProjectListItem[] = [
  {
    id: 'demo-1',
    status: 'draft',
    revision: 0,
    title_short: 'AI-помощник для стартапов',
    completion_percent: 45,
    next_action: { action: 'continue', label: 'Продолжить заполнение', cta_enabled: true },
    can_edit: true,
    can_submit: false,
    can_archive: false,
    can_delete: true,
    created_at: new Date(Date.now() - 86400000 * 2).toISOString(),
    updated_at: new Date(Date.now() - 3600000).toISOString(),
    submitted_at: null,
    has_fix_request: false,
    fix_request_preview: null,
    current_step: 'description',
    missing_fields: ['stack_tech', 'price_display', 'author_contact'],
  },
  {
    id: 'demo-2',
    status: 'pending',
    revision: 1,
    title_short: 'Telegram-бот для учёта финансов',
    completion_percent: 100,
    next_action: { action: 'wait', label: 'Ожидает модерации', cta_enabled: false },
    can_edit: false,
    can_submit: false,
    can_archive: false,
    can_delete: false,
    created_at: new Date(Date.now() - 86400000 * 5).toISOString(),
    updated_at: new Date(Date.now() - 86400000).toISOString(),
    submitted_at: new Date(Date.now() - 86400000).toISOString(),
    has_fix_request: false,
    fix_request_preview: null,
    current_step: null,
    missing_fields: [],
  },
  {
    id: 'demo-3',
    status: 'approved',
    revision: 2,
    title_short: 'Генератор контента на GPT-4',
    completion_percent: 100,
    next_action: { action: 'view', label: 'Опубликован', cta_enabled: false },
    can_edit: false,
    can_submit: false,
    can_archive: true,
    can_delete: false,
    created_at: new Date(Date.now() - 86400000 * 14).toISOString(),
    updated_at: new Date(Date.now() - 86400000 * 7).toISOString(),
    submitted_at: new Date(Date.now() - 86400000 * 10).toISOString(),
    has_fix_request: false,
    fix_request_preview: null,
    current_step: null,
    missing_fields: [],
  },
];

const DEMO_PROJECT_DETAILS: Record<string, ProjectDetails> = {
  'demo-1': {
    id: 'demo-1',
    status: 'draft',
    revision: 0,
    current_step: 'description',
    answers: {},
    fields: {
      author_name: 'Иван Петров',
      author_contact: null,
      author_role: 'Разработчик',
      project_title: 'AI-помощник для стартапов',
      project_subtitle: 'Ваш персональный ассистент для запуска бизнеса',
      problem: 'Стартаперам сложно структурировать идеи',
      audience_type: 'B2B',
      niche: 'AI / Стартапы',
      what_done: 'MVP с базовым функционалом',
      project_status: 'В разработке',
      stack_ai: 'GPT-4, LangChain',
      stack_tech: null,
      stack_infra: 'Vercel, Supabase',
      stack_reason: 'Быстрый старт и масштабирование',
      dev_time: '2 недели',
      price_display: null,
      monetization: 'Подписка',
      potential: 'Высокий',
      goal: 'Найти первых пользователей',
      inbound_ready: 'Да',
      links: ['https://example.com'],
      cool_part: 'Умная генерация документов',
      hardest_part: 'Интеграция с внешними API',
    },
    preview_html: '<b>🚀 AI-помощник для стартапов</b>\n\nВаш персональный ассистент для запуска бизнеса.\n\n<b>Что сделано:</b> MVP с базовым функционалом\n\n<b>Стек:</b> GPT-4, LangChain, Vercel',
    completion_percent: 45,
    missing_fields: ['stack_tech', 'price_display', 'author_contact'],
    filled_fields: ['author_name', 'project_title', 'project_subtitle', 'problem', 'niche'],
    next_action: { action: 'continue', label: 'Продолжить заполнение', cta_enabled: true },
    can_edit: true,
    can_submit: false,
    can_archive: false,
    can_delete: true,
    fix_request: null,
    moderated_at: null,
    created_at: new Date(Date.now() - 86400000 * 2).toISOString(),
    updated_at: new Date(Date.now() - 3600000).toISOString(),
    submitted_at: null,
  },
  'demo-2': {
    id: 'demo-2',
    status: 'pending',
    revision: 1,
    current_step: null,
    answers: {},
    fields: {
      author_name: 'Мария Сидорова',
      author_contact: '@maria_dev',
      author_role: 'Full-stack разработчик',
      project_title: 'Telegram-бот для учёта финансов',
      project_subtitle: 'Простой способ вести бюджет',
      problem: 'Люди забывают записывать расходы',
      audience_type: 'B2C',
      niche: 'FinTech',
      what_done: 'Полностью готовый продукт',
      project_status: 'Готов к продаже',
      stack_ai: null,
      stack_tech: 'Python, aiogram, PostgreSQL',
      stack_infra: 'Docker, VPS',
      stack_reason: 'Надёжность и простота',
      dev_time: '1 месяц',
      price_display: '$500',
      monetization: 'Разовая покупка',
      potential: 'Средний',
      goal: 'Продать проект',
      inbound_ready: 'Да',
      links: ['https://t.me/finance_bot_demo'],
      cool_part: 'Автоматическая категоризация',
      hardest_part: 'Распознавание чеков',
    },
    preview_html: '<b>💰 Telegram-бот для учёта финансов</b>\n\nПростой способ вести бюджет.\n\n<b>Что сделано:</b> Полностью готовый продукт\n\n<b>Стек:</b> Python, aiogram, PostgreSQL\n\n<b>Цена:</b> $500',
    completion_percent: 100,
    missing_fields: [],
    filled_fields: ['author_name', 'author_contact', 'project_title', 'project_subtitle', 'problem', 'niche', 'stack_tech', 'price_display'],
    next_action: { action: 'wait', label: 'Ожидает модерации', cta_enabled: false },
    can_edit: false,
    can_submit: false,
    can_archive: false,
    can_delete: false,
    fix_request: null,
    moderated_at: null,
    created_at: new Date(Date.now() - 86400000 * 5).toISOString(),
    updated_at: new Date(Date.now() - 86400000).toISOString(),
    submitted_at: new Date(Date.now() - 86400000).toISOString(),
  },
  'demo-3': {
    id: 'demo-3',
    status: 'approved',
    revision: 2,
    current_step: null,
    answers: {},
    fields: {
      author_name: 'Алексей Козлов',
      author_contact: '@alex_builder',
      author_role: 'Indie-разработчик',
      project_title: 'Генератор контента на GPT-4',
      project_subtitle: 'Создавайте уникальный контент за минуты',
      problem: 'Создание контента занимает много времени',
      audience_type: 'B2B',
      niche: 'AI / Контент',
      what_done: 'SaaS-платформа с 50+ пользователями',
      project_status: 'Активный бизнес',
      stack_ai: 'GPT-4, DALL-E',
      stack_tech: 'Next.js, TypeScript, Prisma',
      stack_infra: 'Vercel, PlanetScale',
      stack_reason: 'Современный стек для быстрой итерации',
      dev_time: '3 месяца',
      price_display: '$2,000',
      monetization: 'SaaS + разовая',
      potential: 'Высокий',
      goal: 'Привлечь инвестиции',
      inbound_ready: 'Да',
      links: ['https://contentgen.example.com'],
      cool_part: 'Мультимодальная генерация',
      hardest_part: 'Оптимизация затрат на API',
    },
    preview_html: '<b>✨ Генератор контента на GPT-4</b>\n\nСоздавайте уникальный контент за минуты.\n\n<b>Что сделано:</b> SaaS-платформа с 50+ пользователями\n\n<b>Стек:</b> GPT-4, Next.js, TypeScript\n\n<b>Цена:</b> $2,000',
    completion_percent: 100,
    missing_fields: [],
    filled_fields: ['author_name', 'author_contact', 'project_title', 'project_subtitle', 'problem', 'niche', 'stack_tech', 'stack_ai', 'price_display'],
    next_action: { action: 'view', label: 'Опубликован', cta_enabled: false },
    can_edit: false,
    can_submit: false,
    can_archive: true,
    can_delete: false,
    fix_request: null,
    moderated_at: new Date(Date.now() - 86400000 * 7).toISOString(),
    created_at: new Date(Date.now() - 86400000 * 14).toISOString(),
    updated_at: new Date(Date.now() - 86400000 * 7).toISOString(),
    submitted_at: new Date(Date.now() - 86400000 * 10).toISOString(),
  },
};

// Demo API client that returns mock data
class DemoApiClient {
  private fakeToken = 'demo-token';

  async authenticate(): Promise<AuthResponse> {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 300));
    return {
      access_token: this.fakeToken,
      token_type: 'bearer',
      expires_in: 86400,
      user: DEMO_USER,
    };
  }

  isAuthenticated(): boolean {
    return true;
  }

  async getMyProjects(): Promise<ProjectListItem[]> {
    await new Promise(resolve => setTimeout(resolve, 200));
    return [...DEMO_PROJECTS];
  }

  async getProject(id: string): Promise<ProjectDetails> {
    await new Promise(resolve => setTimeout(resolve, 200));
    const project = DEMO_PROJECT_DETAILS[id];
    if (!project) {
      throw new Error('Project not found');
    }
    return { ...project };
  }

  async createDraft(): Promise<ProjectDetails> {
    await new Promise(resolve => setTimeout(resolve, 300));
    const newId = `demo-${Date.now()}`;
    const newProject: ProjectDetails = {
      id: newId,
      status: 'draft',
      revision: 0,
      current_step: 'project_title',
      answers: {},
      fields: {
        author_name: DEMO_USER.full_name,
        author_contact: null,
        author_role: null,
        project_title: null,
        project_subtitle: null,
        problem: null,
        audience_type: null,
        niche: null,
        what_done: null,
        project_status: null,
        stack_ai: null,
        stack_tech: null,
        stack_infra: null,
        stack_reason: null,
        dev_time: null,
        price_display: null,
        monetization: null,
        potential: null,
        goal: null,
        inbound_ready: null,
        links: [],
        cool_part: null,
        hardest_part: null,
      },
      preview_html: null,
      completion_percent: 5,
      missing_fields: ['project_title', 'description', 'stack', 'price', 'contact'],
      filled_fields: ['author_name'],
      next_action: { action: 'continue', label: 'Начать заполнение', cta_enabled: true },
      can_edit: true,
      can_submit: false,
      can_archive: false,
      can_delete: true,
      fix_request: null,
      moderated_at: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      submitted_at: null,
    };
    // Add to demo data for subsequent fetches
    DEMO_PROJECTS.unshift({
      id: newId,
      status: 'draft',
      revision: 0,
      title_short: 'Новый проект',
      completion_percent: 5,
      next_action: newProject.next_action,
      can_edit: true,
      can_submit: false,
      can_archive: false,
      can_delete: true,
      created_at: newProject.created_at,
      updated_at: newProject.updated_at,
      submitted_at: null,
      has_fix_request: false,
      fix_request_preview: null,
      current_step: 'project_title',
      missing_fields: newProject.missing_fields,
    });
    DEMO_PROJECT_DETAILS[newId] = newProject;
    return newProject;
  }
}

// Real API client - used when API URL is configured
class RealApiClient {
  private accessToken: string | null = null;

  /**
   * Get Telegram WebApp initData
   */
  private getInitData(): string {
    return window.Telegram?.WebApp?.initData || '';
  }

  /**
   * Make authenticated API request
   */
  private async request<T>(
    method: string,
    path: string,
    body?: unknown
  ): Promise<T> {
    // Check if API URL is configured
    if (!isApiConfigured()) {
      const error = 'VITE_API_PUBLIC_URL is not set. Configure it in Vercel environment variables.';
      diagnosticInfo.lastError = error;
      throw new Error(error);
    }

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    // Add auth token if available
    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    const url = `${API_BASE_URL}${path}`;
    
    try {
      const response = await fetch(url, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
      });

      if (!response.ok) {
        let error: ApiError;
        try {
          error = await response.json();
        } catch {
          error = { detail: `HTTP ${response.status}: ${response.statusText}` };
        }
        const errorMsg = error.detail || 'API request failed';
        diagnosticInfo.lastError = errorMsg;
        throw new Error(errorMsg);
      }

      return response.json();
    } catch (err) {
      if (err instanceof Error) {
        diagnosticInfo.lastError = err.message;
      }
      throw err;
    }
  }

  /**
   * Authenticate with Telegram initData
   */
  async authenticate(): Promise<AuthResponse> {
    const initData = this.getInitData();
    
    if (!initData) {
      throw new Error('Telegram WebApp initData not available');
    }

    const response = await this.request<AuthResponse>(
      'POST',
      '/api/v1/auth/telegram',
      { initData }
    );

    this.accessToken = response.access_token;
    return response;
  }

  /**
   * Check if authenticated
   */
  isAuthenticated(): boolean {
    return this.accessToken !== null;
  }

  /**
   * Get current user's projects
   */
  async getMyProjects(): Promise<ProjectListItem[]> {
    return this.request<ProjectListItem[]>('GET', '/api/v1/projects/my');
  }

  /**
   * Get project details by ID
   */
  async getProject(id: string): Promise<ProjectDetails> {
    return this.request<ProjectDetails>('GET', `/api/v1/projects/${id}`);
  }

  /**
   * Create a new draft project
   */
  async createDraft(): Promise<ProjectDetails> {
    return this.request<ProjectDetails>('POST', '/api/v1/projects/create_draft');
  }
}

// Export the appropriate client based on mode
// In demo mode, use DemoApiClient; otherwise use RealApiClient
export const api = DEMO_MODE ? new DemoApiClient() : new RealApiClient();
