import { useCallback, useEffect, useState } from 'react';
import './index.css';
import {
  ApiError,
  authenticate,
  createDraft,
  getProjects,
  getToken,
  isApiEnabled,
  type Project,
} from './lib/api';

type ProjectStatus = 'draft' | 'pending' | 'needs_fix' | 'approved' | 'rejected';

// Demo projects for fallback mode
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
          <div
            className="progress-bar-fill"
            style={{ width: `${project.completion_percent}%` }}
          />
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
          Попробовать снова
        </button>
      )}
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
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [isDemo, setIsDemo] = useState(!isApiEnabled());
  const [authError, setAuthError] = useState<string | null>(null);

  // Try to authenticate with Telegram WebApp
  const tryAuth = useCallback(async (): Promise<boolean> => {
    // Check if Telegram WebApp is available
    const tg = (window as { Telegram?: { WebApp?: { initData?: string } } }).Telegram?.WebApp;
    const initData = tg?.initData;

    if (!initData) {
      // No Telegram context - can't authenticate
      return false;
    }

    try {
      await authenticate(initData);
      return true;
    } catch (err) {
      console.error('Auth failed:', err);
      if (err instanceof ApiError) {
        setAuthError(`Ошибка авторизации: ${err.message}`);
      }
      return false;
    }
  }, []);

  // Load projects from API or use demo data
  const loadProjects = useCallback(async () => {
    if (!isApiEnabled()) {
      // Demo mode
      setProjects(DEMO_PROJECTS);
      setLoading(false);
      setIsDemo(true);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Check if we have a token, if not try to authenticate
      if (!getToken()) {
        const authenticated = await tryAuth();
        if (!authenticated) {
          // Fall back to demo mode if auth fails
          setProjects(DEMO_PROJECTS);
          setIsDemo(true);
          setLoading(false);
          return;
        }
      }

      const data = await getProjects();
      setProjects(data);
      setIsDemo(false);
    } catch (err) {
      console.error('Failed to load projects:', err);
      if (err instanceof ApiError) {
        if (err.status === 401) {
          // Token expired, try to re-authenticate
          const authenticated = await tryAuth();
          if (authenticated) {
            try {
              const data = await getProjects();
              setProjects(data);
              setIsDemo(false);
              setError(null);
              return;
            } catch (retryErr) {
              console.error('Retry failed:', retryErr);
            }
          }
          // Fall back to demo mode
          setProjects(DEMO_PROJECTS);
          setIsDemo(true);
        } else {
          setError(err.message);
        }
      } else {
        setError('Не удалось загрузить проекты');
      }
    } finally {
      setLoading(false);
    }
  }, [tryAuth]);

  // Initial load
  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  // Handle create project
  const handleCreateProject = async () => {
    if (isDemo) {
      alert('Создание проекта будет доступно после подключения API');
      return;
    }

    setCreating(true);
    try {
      await createDraft();
      // Refresh project list
      await loadProjects();
    } catch (err) {
      console.error('Failed to create project:', err);
      if (err instanceof ApiError) {
        alert(`Ошибка: ${err.message}`);
      } else {
        alert('Не удалось создать проект');
      }
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="container">
      {isDemo && (
        <div className="demo-banner">
          ⚠️ DEMO MODE — API не подключён, данные тестовые
        </div>
      )}
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
          ) : error ? (
            <ErrorMessage message={error} onRetry={loadProjects} />
          ) : projects.length === 0 ? (
            <EmptyState />
          ) : (
            projects.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))
          )}
        </section>

        <button
          className="btn btn-primary btn-full"
          onClick={handleCreateProject}
          disabled={creating || loading}
        >
          {creating ? '⏳ Создание...' : '➕ Создать проект'}
        </button>
      </main>
    </div>
  );
}

export default App;
