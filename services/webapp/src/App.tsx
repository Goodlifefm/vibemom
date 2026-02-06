import { useCallback, useEffect, useMemo, useState } from 'react';
import './index.css';
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
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [apiUnavailable, setApiUnavailable] = useState<ApiErrorInfo | null>(null);

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
            <LoadingSpinner />
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

