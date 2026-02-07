import { useCallback, useEffect, useMemo, useState } from 'react';
import './index.css';
import { InitDiagnosticsScreen } from './components/InitDiagnosticsScreen';
import { getApiBaseUrl } from './config/api';
import {
  ApiError,
  clearToken,
  authenticate,
  createDraft,
  getApiErrorInfo,
  getProjects,
  getToken,
  type ApiErrorInfo,
  type Project,
} from './lib/api';

type ProjectStatus = 'draft' | 'pending' | 'needs_fix' | 'approved' | 'rejected';

const BOOT_WATCHDOG_TIMEOUT_MS = 2800;

const DEMO_PROJECTS: Project[] = [
  {
    id: '1',
    title_short: 'AI-помощник для стартапов',
    status: 'draft',
    revision: 0,
    completion_percent: 45,
    next_action: { action: 'continue', label: 'Продолжить', cta_enabled: true },
    can_edit: true,
    can_submit: false,
    can_archive: true,
    can_delete: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    submitted_at: null,
    has_fix_request: false,
    fix_request_preview: null,
    current_step: 'description',
    missing_fields: ['description', 'price'],
  },
  {
    id: '2',
    title_short: 'Telegram-бот для учёта финансов',
    status: 'pending',
    revision: 1,
    completion_percent: 100,
    next_action: { action: 'wait', label: 'Ожидание', cta_enabled: false },
    can_edit: false,
    can_submit: false,
    can_archive: false,
    can_delete: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    submitted_at: new Date().toISOString(),
    has_fix_request: false,
    fix_request_preview: null,
    current_step: null,
    missing_fields: [],
  },
  {
    id: '3',
    title_short: 'Генератор контента на GPT-4',
    status: 'approved',
    revision: 2,
    completion_percent: 100,
    next_action: { action: 'view', label: 'Просмотр', cta_enabled: true },
    can_edit: false,
    can_submit: false,
    can_archive: true,
    can_delete: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    submitted_at: new Date().toISOString(),
    has_fix_request: false,
    fix_request_preview: null,
    current_step: null,
    missing_fields: [],
  },
];

const STATUS_LABELS: Record<ProjectStatus, { label: string; className: string }> = {
  draft: { label: 'Черновик', className: 'badge-draft' },
  pending: { label: 'На модерации', className: 'badge-pending' },
  needs_fix: { label: 'Требует правок', className: 'badge-needs-fix' },
  approved: { label: 'Одобрен', className: 'badge-approved' },
  rejected: { label: 'Отклонён', className: 'badge-rejected' },
};

function isApiUnavailableError(error: ApiErrorInfo): boolean {
  if (error.kind === 'network' || error.kind === 'cors') {
    return true;
  }
  return error.kind === 'http' && typeof error.status === 'number' && error.status >= 500;
}

function ProjectCard({ project }: { project: Project }) {
  const statusInfo = STATUS_LABELS[project.status] || STATUS_LABELS.draft;

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">{project.title_short || 'Без названия'}</h3>
        <span className={`badge ${statusInfo.className}`}>{statusInfo.label}</span>
      </div>
      <div className="card-body">
        <div className="progress-bar">
          <div className="progress-bar-fill" style={{ width: `${project.completion_percent}%` }} />
        </div>
        <p className="progress-text">{project.completion_percent}% заполнено</p>
        {project.has_fix_request && project.fix_request_preview && (
          <p className="fix-request">⚠️ {project.fix_request_preview}</p>
        )}
      </div>
    </div>
  );
}

function LoadingSpinner() {
  return (
    <div className="loading">
      <div className="spinner" />
      <p>Загрузка...</p>
    </div>
  );
}

function ErrorMessage({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="error">
      <p>❌ {message}</p>
      {onRetry && (
        <button className="btn btn-secondary" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}

function ApiUnavailablePanel({
  apiBaseUrl,
  errorInfo,
  onRetry,
}: {
  apiBaseUrl: string;
  errorInfo: ApiErrorInfo;
  onRetry: () => void;
}) {
  const [echoOriginResult, setEchoOriginResult] = useState<string | null>(null);
  const [echoOriginIsError, setEchoOriginIsError] = useState(false);
  const [echoOriginLoading, setEchoOriginLoading] = useState(false);

  const formatEchoOriginResponse = useCallback((text: string): string => {
    const trimmed = text.trim();
    if (!trimmed) {
      return '';
    }

    try {
      const parsed = JSON.parse(trimmed) as unknown;

      const redact = (value: unknown): unknown => {
        if (Array.isArray(value)) {
          return value.map((item) => redact(item));
        }
        if (value && typeof value === 'object') {
          const obj = value as Record<string, unknown>;
          const out: Record<string, unknown> = {};

          for (const [key, nested] of Object.entries(obj)) {
            const lower = key.toLowerCase();
            if (lower === 'initdata' || lower === 'authorization' || lower === 'cookie' || lower === 'cookies') {
              out[key] = '[redacted]';
              continue;
            }
            out[key] = redact(nested);
          }

          return out;
        }
        return value;
      };

      return JSON.stringify(redact(parsed), null, 2);
    } catch {
      return text;
    }
  }, []);

  const handleEchoOrigin = useCallback(async () => {
    if (echoOriginLoading) {
      return;
    }

    setEchoOriginLoading(true);
    setEchoOriginResult(null);
    setEchoOriginIsError(false);

    try {
      const response = await fetch(`${apiBaseUrl}/debug/echo`, {
        method: 'GET',
        // Never include cookies or authorization for this diagnostic call.
        credentials: 'omit',
        cache: 'no-store',
      });

      const text = await response.text();
      setEchoOriginResult(formatEchoOriginResponse(text));
      setEchoOriginIsError(false);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setEchoOriginResult(message);
      setEchoOriginIsError(true);
    } finally {
      setEchoOriginLoading(false);
    }
  }, [apiBaseUrl, echoOriginLoading, formatEchoOriginResponse]);

  return (
    <div className="error api-unavailable">
      <p>API недоступен. Попробуйте ещё раз.</p>
      <button className="btn btn-secondary" onClick={onRetry}>
        Retry
      </button>
      <details className="diagnostics-panel">
        <summary>Диагностика</summary>
        <div className="diagnostics-content">
          <div className="diagnostics-row">
            <span className="diagnostics-key">apiBaseUrl</span>
            <span className="diagnostics-value">{apiBaseUrl}</span>
          </div>
          <div className="diagnostics-row">
            <span className="diagnostics-key">error.kind</span>
            <span className="diagnostics-value">{errorInfo.kind}</span>
          </div>
          <div className="diagnostics-row">
            <span className="diagnostics-key">error.status</span>
            <span className="diagnostics-value">{errorInfo.status ?? '-'}</span>
          </div>
          <div className="diagnostics-row">
            <span className="diagnostics-key">error.message</span>
            <span className="diagnostics-value">{errorInfo.message}</span>
          </div>
          <div className="diagnostics-row">
            <span className="diagnostics-key">debug.echo</span>
            <div className="diagnostics-value diagnostics-echo">
              <button className="btn btn-secondary diagnostics-btn" onClick={handleEchoOrigin} disabled={echoOriginLoading}>
                Echo origin
              </button>
              {echoOriginResult !== null && (
                <pre className={`diagnostics-echo-output${echoOriginIsError ? ' diagnostics-echo-output-error' : ''}`}>
                  {echoOriginResult}
                </pre>
              )}
            </div>
          </div>
        </div>
      </details>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="empty-state">
      <p>📂 У вас пока нет проектов</p>
      <p className="empty-hint">Создайте первый проект, чтобы начать</p>
    </div>
  );
}

function App() {
  const apiBaseUrl = useMemo(() => getApiBaseUrl(), []);
  const isDemo = apiBaseUrl === null;

  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [initAttempt, setInitAttempt] = useState(0);
  const [bootCompleted, setBootCompleted] = useState(false);
  const [bootWatchdogFired, setBootWatchdogFired] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [apiUnavailable, setApiUnavailable] = useState<ApiErrorInfo | null>(null);

  useEffect(() => {
    if (!loading) {
      setBootCompleted(true);
    }
  }, [loading]);

  useEffect(() => {
    if (bootCompleted || !loading) {
      setBootWatchdogFired(false);
      return;
    }

    const timerId = window.setTimeout(() => {
      setBootWatchdogFired(true);
    }, BOOT_WATCHDOG_TIMEOUT_MS);

    return () => {
      window.clearTimeout(timerId);
    };
  }, [bootCompleted, initAttempt, loading]);

  const handleApiFailure = useCallback((err: unknown, fallbackMessage: string) => {
    const info = getApiErrorInfo(err);
    if (isApiUnavailableError(info)) {
      setApiUnavailable(info);
      setError(null);
      return;
    }
    setApiUnavailable(null);
    setError(info.message || fallbackMessage);
  }, []);

  const tryAuth = useCallback(async (): Promise<void> => {
    const tg = (window as { Telegram?: { WebApp?: { initData?: string } } }).Telegram?.WebApp;
    const initData = tg?.initData;

    if (!initData) {
      throw new ApiError({
        kind: 'unknown',
        code: 'INIT_DATA_MISSING',
        message: 'Telegram initData не найден. Откройте Mini App из Telegram.',
      });
    }

    await authenticate(initData);
    setAuthError(null);
  }, []);

  const loadProjects = useCallback(async () => {
    setInitAttempt((value) => value + 1);
    setBootWatchdogFired(false);

    if (isDemo) {
      setProjects(DEMO_PROJECTS);
      setApiUnavailable(null);
      setError(null);
      setAuthError(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    setApiUnavailable(null);

    try {
      if (!getToken()) {
        await tryAuth();
      }

      const data = await getProjects();
      setProjects(data);
      setAuthError(null);
    } catch (err) {
      if (err instanceof ApiError && err.kind === 'http' && err.status === 401) {
        clearToken();
        try {
          await tryAuth();
          const retriedData = await getProjects();
          setProjects(retriedData);
          setAuthError(null);
          setError(null);
          setApiUnavailable(null);
          setLoading(false);
          return;
        } catch (retryErr) {
          const retryInfo = getApiErrorInfo(retryErr);
          if (isApiUnavailableError(retryInfo)) {
            setApiUnavailable(retryInfo);
            setError(null);
            setAuthError(null);
          } else {
            setApiUnavailable(null);
            setAuthError(retryInfo.message);
            setError('Не удалось загрузить проекты');
          }
          setProjects([]);
          setLoading(false);
          return;
        }
      }

      handleApiFailure(err, 'Не удалось загрузить проекты');
      const errInfo = getApiErrorInfo(err);
      if (!isApiUnavailableError(errInfo) && errInfo.message) {
        setAuthError(errInfo.message);
      } else {
        setAuthError(null);
      }
      setProjects([]);
    } finally {
      setLoading(false);
    }
  }, [handleApiFailure, isDemo, tryAuth]);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  const handleCreateProject = async () => {
    if (isDemo) {
      alert('Создание проекта будет доступно после подключения API');
      return;
    }

    if (apiUnavailable) {
      alert('API недоступен. Нажмите Retry и попробуйте снова.');
      return;
    }

    setCreating(true);
    try {
      await createDraft();
      await loadProjects();
    } catch (err) {
      const info = getApiErrorInfo(err);
      if (isApiUnavailableError(info)) {
        setApiUnavailable(info);
      } else {
        alert(`Ошибка: ${info.message || 'Не удалось создать проект'}`);
      }
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="container">
      {isDemo && <div className="demo-banner">⚠️ DEMO MODE — API не подключён, данные тестовые</div>}

      <header className="header">
        <h1 className="header-title">Мои проекты</h1>
        <p className="header-subtitle">
          {isDemo ? 'Подключите API для работы с реальными данными' : 'Управление проектами'}
        </p>
        {authError && <p className="auth-error">{authError}</p>}
      </header>

      <main className="main">
        <section className="projects">
          <h2 className="section-title">Мои проекты</h2>

          {loading ? (
            bootWatchdogFired ? (
              <InitDiagnosticsScreen apiBaseUrl={import.meta.env.VITE_API_PUBLIC_URL || ''} onRetry={loadProjects} />
            ) : (
              <LoadingSpinner />
            )
          ) : apiUnavailable && apiBaseUrl ? (
            <ApiUnavailablePanel apiBaseUrl={apiBaseUrl} errorInfo={apiUnavailable} onRetry={loadProjects} />
          ) : error ? (
            <ErrorMessage message={error} onRetry={loadProjects} />
          ) : projects.length === 0 ? (
            <EmptyState />
          ) : (
            projects.map((project) => <ProjectCard key={project.id} project={project} />)
          )}
        </section>

        <button className="btn btn-primary btn-full" onClick={handleCreateProject} disabled={creating || loading}>
          {creating ? '⏳ Создание...' : '➕ Создать проект'}
        </button>
      </main>
    </div>
  );
}

export default App;
