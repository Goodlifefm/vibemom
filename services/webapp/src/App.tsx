import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import './index.css';
import { InitDiagnosticsScreen } from './components/InitDiagnosticsScreen';
import { SelfTestPanel } from './components/SelfTestPanel';
import { getApiBaseUrl } from './config/api';
import {
  ApiError,
  clearToken,
  authenticate,
  createDraft,
  getApiErrorInfo,
  getProject,
  getProjects,
  getPublicProjects,
  getToken,
  type PublicProjectListItem,
  type ApiErrorInfo,
  type Project,
  type ProjectDetails,
} from './lib/api';
import { WizardScreen } from './components/WizardScreen';
import { PublicProjectScreen } from './components/PublicProjectScreen';
import { calcMvpPercentFromListItem } from './lib/mvpWizard';
import { useBuildStamp } from './lib/useBuildStamp';
import { getLastErrors, getLastRequest, installGlobalErrorTracking } from './lib/fetcher';
import { isSelfTestEnabled } from './lib/selfTest';
import { installGlobalTapTracking, recordTapFromReactEvent } from './lib/tapTracker';

type ProjectStatus = 'draft' | 'pending' | 'needs_fix' | 'approved' | 'rejected';
type RouteState = { kind: 'app' } | { kind: 'public'; idOrSlug: string };
type FeedTab = 'my' | 'public';

function parseRouteFromPathname(pathname: string): RouteState {
  const parts = String(pathname || '/')
    .split('/')
    .filter((p) => p.length > 0);
  if (parts[0] !== 'p' || parts.length < 2) {
    return { kind: 'app' };
  }
  try {
    const idOrSlug = decodeURIComponent(parts[1] || '').trim();
    return idOrSlug ? { kind: 'public', idOrSlug } : { kind: 'app' };
  } catch {
    return { kind: 'app' };
  }
}

function parseRouteFromLocation(): RouteState {
  if (typeof window === 'undefined') return { kind: 'app' };
  return parseRouteFromPathname(window.location.pathname || '/');
}

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

function Toast({ message, onDismiss }: { message: string; onDismiss: () => void }) {
  useEffect(() => {
    const timer = window.setTimeout(onDismiss, 3000);
    return () => window.clearTimeout(timer);
  }, [onDismiss]);

  return (
    <div className="toast" onClick={onDismiss} role="status">
      {message}
    </div>
  );
}

function ProjectCard({
  project,
  onOpen,
  onContinue,
}: {
  project: Project;
  onOpen: (id: string) => void;
  onContinue: (id: string) => void;
}) {
  const statusInfo = STATUS_LABELS[project.status] || STATUS_LABELS.draft;
  const mvpPercent = calcMvpPercentFromListItem(project);
  const canContinue = (project.status === 'draft' || project.status === 'needs_fix') && mvpPercent < 100;
  const ctaLabel = canContinue
    ? '\u041F\u0440\u043E\u0434\u043E\u043B\u0436\u0438\u0442\u044C \u0437\u0430\u043F\u043E\u043B\u043D\u0435\u043D\u0438\u0435'
    : '\u041E\u0442\u043A\u0440\u044B\u0442\u044C';

  const lastFireRef = useRef(0);
  const fireOpen = useCallback(
    (source: string) => {
      const now = Date.now();
      // Touch events in mobile WebViews can trigger multiple synthetic events (touchend + click).
      if (now - lastFireRef.current < 350) {
        return;
      }
      lastFireRef.current = now;

      console.log(
        `[DEBUG] open project source=${source} id=${project.id}, status=${project.status}, title="${project.title_short || '\\u0411\\u0435\\u0437 \\u043D\\u0430\\u0437\\u0432\\u0430\\u043D\\u0438\\u044F'}"`,
      );
      onOpen(project.id);
    },
    [onOpen, project.id, project.status, project.title_short],
  );

  return (
    <div
      role="button"
      tabIndex={0}
      className="card card-clickable"
      onPointerUp={() => fireOpen('pointerup')}
      onTouchEnd={() => fireOpen('touchend')}
      onClick={() => fireOpen('click')}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          fireOpen('keydown');
        }
      }}
    >
      <div className="card-header">
        <h3 className="card-title">
          {project.title_short || '\u0411\u0435\u0437 \u043D\u0430\u0437\u0432\u0430\u043D\u0438\u044F'}
        </h3>
        <span className={`badge ${statusInfo.className}`}>{statusInfo.label}</span>
      </div>
      <div className="card-body">
        <div className="progress-bar">
          <div className="progress-bar-fill" style={{ width: `${mvpPercent}%` }} />
        </div>
        <p className="progress-text">
          {mvpPercent}% \u0437\u0430\u043F\u043E\u043B\u043D\u0435\u043D\u043E (MVP)
        </p>
        {project.has_fix_request && project.fix_request_preview && (
          <p className="fix-request">! {project.fix_request_preview}</p>
        )}
      </div>
      <div className="card-footer">
        <button
          type="button"
          className="btn btn-primary btn-compact"
          onPointerUp={(e) => e.stopPropagation()}
          onTouchEnd={(e) => e.stopPropagation()}
          onClick={(e) => {
            e.stopPropagation();
            if (canContinue) {
              onContinue(project.id);
            } else {
              onOpen(project.id);
            }
          }}
        >
          {ctaLabel}
        </button>
        <svg className="card-chevron" width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
          <path
            d="M7.5 4L13.5 10L7.5 16"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>
    </div>
  );
}

function PublicProjectCard({
  project,
  onOpen,
}: {
  project: PublicProjectListItem;
  onOpen: (idOrSlug: string) => void;
}) {
  const lastFireRef = useRef(0);
  const fireOpen = useCallback(
    (source: string) => {
      const now = Date.now();
      // Touch events in mobile WebViews can trigger multiple synthetic events (touchend + click).
      if (now - lastFireRef.current < 350) {
        return;
      }
      lastFireRef.current = now;

      console.log(`[DEBUG] open public project source=${source} id_or_slug=${project.public_id}`);
      onOpen(project.public_id);
    },
    [onOpen, project.public_id],
  );

  return (
    <div
      role="button"
      tabIndex={0}
      className="card card-clickable"
      onPointerUp={() => fireOpen('pointerup')}
      onTouchEnd={() => fireOpen('touchend')}
      onClick={() => fireOpen('click')}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          fireOpen('keydown');
        }
      }}
    >
      <div className="card-header">
        <h3 className="card-title">{project.title || 'Без названия'}</h3>
        <span className="badge badge-approved">Опубликовано</span>
      </div>
      <div className="card-body">
        {(project.problem || project.audience_type) && (
          <p style={{ marginTop: 6 }}>
            {[project.problem, project.audience_type].filter((v) => Boolean(v && String(v).trim())).join(' · ')}
          </p>
        )}
        {project.niche ? <p className="progress-text">Ниша: {project.niche}</p> : null}
      </div>
      <div className="card-footer">
        <button
          type="button"
          className="btn btn-primary btn-compact"
          onPointerUp={(e) => e.stopPropagation()}
          onTouchEnd={(e) => e.stopPropagation()}
          onClick={(e) => {
            e.stopPropagation();
            onOpen(project.public_id);
          }}
        >
          Открыть
        </button>
        <svg className="card-chevron" width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
          <path d="M7.5 4L13.5 10L7.5 16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
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

function ErrorMessage({
  message,
  details,
  fetchInfo,
  onRetry,
}: {
  message: string;
  details?: string | null;
  fetchInfo?: ApiErrorInfo | null;
  onRetry?: () => void;
}) {
  const req = fetchInfo?.request ?? null;
  const dur = req?.durationMs ?? (req?.endTs && req?.startTs ? Math.max(0, req.endTs - req.startTs) : null);
  const startedAt = req?.startTs ? new Date(req.startTs).toLocaleString('ru') : null;

  return (
    <div className="error">
      <p>{message}</p>
      {req && (
        <p className="error-meta">
          <span className="diagnostics-key">request</span>{' '}
          <span className="diagnostics-value">
            {req.method} {req.url} at {startedAt || '-'} dur={dur ?? '-'}ms status={fetchInfo?.status ?? '-'}
          </span>
        </p>
      )}
      {fetchInfo?.errorReportRequestId ? (
        <p className="error-meta">
          <span className="diagnostics-key">error_report_id</span>{' '}
          <span className="diagnostics-value">{fetchInfo.errorReportRequestId}</span>
        </p>
      ) : null}
      {onRetry && (
        <button className="btn btn-secondary" onClick={onRetry}>
          Retry
        </button>
      )}
      {details ? (
        <details className="diagnostics-panel">
          <summary>Details</summary>
          <pre className="diagnostics-echo-output">{details}</pre>
        </details>
      ) : null}
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
        referrerPolicy: 'no-referrer',
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
            <span className="diagnostics-key">lastRequest</span>
            <pre className="diagnostics-echo-output">{JSON.stringify(getLastRequest(), null, 2) || '-'}</pre>
          </div>
          <div className="diagnostics-row">
            <span className="diagnostics-key">lastErrors</span>
            <pre className="diagnostics-echo-output">{JSON.stringify(getLastErrors().slice(0, 5), null, 2) || '-'}</pre>
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
      <p>У вас пока нет проектов</p>
      <p className="empty-hint">Создайте первый проект, чтобы начать</p>
    </div>
  );
}

function ProjectDetailScreen({
  details,
  loading,
  error,
  errorDetails,
  fetchInfo,
  onBack,
  onRetry,
}: {
  details: ProjectDetails | null;
  loading: boolean;
  error: string | null;
  errorDetails: string | null;
  fetchInfo?: ApiErrorInfo | null;
  onBack: () => void;
  onRetry: () => void;
}) {
  if (loading) {
    return (
      <div className="detail-screen">
        <button className="btn-back" onClick={onBack}>
          ← Назад к проектам
        </button>
        <LoadingSpinner />
      </div>
    );
  }

  if (error || !details) {
    return (
      <div className="detail-screen">
        <button className="btn-back" onClick={onBack}>
          ← Назад к проектам
        </button>
        <ErrorMessage message={error || 'Проект не найден'} details={errorDetails} fetchInfo={fetchInfo} onRetry={onRetry} />
      </div>
    );
  }

  const statusInfo = STATUS_LABELS[details.status] || STATUS_LABELS.draft;
  const rawTitle = details.fields?.['project_title'];
  const title = typeof rawTitle === 'string' && rawTitle.length > 0 ? rawTitle : 'Без названия';

  return (
    <div className="detail-screen">
      <button className="btn-back" onClick={onBack}>
        ← Назад к проектам
      </button>

      <div className="detail-card">
        <div className="detail-header">
          <h2 className="detail-title">{title}</h2>
          <span className={`badge ${statusInfo.className}`}>{statusInfo.label}</span>
        </div>

        <div className="detail-progress">
          <div className="progress-bar">
            <div className="progress-bar-fill" style={{ width: `${details.completion_percent}%` }} />
          </div>
          <p className="progress-text">{details.completion_percent}% заполнено</p>
        </div>

        {details.fix_request && <div className="fix-request">! {details.fix_request}</div>}

        {details.missing_fields.length > 0 && (
          <div className="detail-section">
            <h3 className="detail-section-title">Незаполненные поля</h3>
            <ul className="detail-missing-list">
              {details.missing_fields.map((field) => (
                <li key={field}>{field}</li>
              ))}
            </ul>
          </div>
        )}

        {details.preview_html && (
          <div className="detail-section">
            <h3 className="detail-section-title">Превью</h3>
            <div className="detail-preview-html" dangerouslySetInnerHTML={{ __html: details.preview_html }} />
          </div>
        )}

        <div className="detail-meta">
          <div className="detail-meta-row">
            <span className="detail-meta-key">ID</span>
            <span className="detail-meta-value">{details.id.slice(0, 8)}…</span>
          </div>
          <div className="detail-meta-row">
            <span className="detail-meta-key">Ревизия</span>
            <span className="detail-meta-value">{details.revision}</span>
          </div>
          <div className="detail-meta-row">
            <span className="detail-meta-key">Создан</span>
            <span className="detail-meta-value">{new Date(details.created_at).toLocaleString('ru')}</span>
          </div>
          <div className="detail-meta-row">
            <span className="detail-meta-key">Обновлён</span>
            <span className="detail-meta-value">{new Date(details.updated_at).toLocaleString('ru')}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function App() {
  const apiBaseUrl = useMemo(() => getApiBaseUrl(), []);
  const isDemo = apiBaseUrl === null;
  const build = useBuildStamp();
  const selfTestAutoOpen = useMemo(() => isSelfTestEnabled(), []);
  const [selfTestVisible, setSelfTestVisible] = useState(selfTestAutoOpen);

  useEffect(() => {
    installGlobalErrorTracking();
    installGlobalTapTracking();
  }, []);

  const [route, setRoute] = useState<RouteState>(() => parseRouteFromLocation());
  const [feed, setFeed] = useState<FeedTab>('my');

  useEffect(() => {
    const onPopState = () => setRoute(parseRouteFromLocation());
    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  }, []);

  const navigate = useCallback((path: string) => {
    if (typeof window === 'undefined') return;
    window.history.pushState({}, '', path);
    setRoute(parseRouteFromPathname(path));
  }, []);

  const openPublicProject = useCallback(
    (idOrSlug: string) => {
      const clean = String(idOrSlug || '').trim();
      if (!clean) return;
      navigate(`/p/${encodeURIComponent(clean)}`);
    },
    [navigate],
  );

  const handlePublicBack = useCallback(() => {
    window.history.back();
  }, []);

  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [initAttempt, setInitAttempt] = useState(0);
  const [bootCompleted, setBootCompleted] = useState(false);
  const [bootWatchdogFired, setBootWatchdogFired] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errorDetails, setErrorDetails] = useState<string | null>(null);
  const [lastFetchErrorInfo, setLastFetchErrorInfo] = useState<ApiErrorInfo | null>(null);
  const [creating, setCreating] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [apiUnavailable, setApiUnavailable] = useState<ApiErrorInfo | null>(null);

  const [screen, setScreen] = useState<'list' | 'detail' | 'wizard'>('list');
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [projectDetails, setProjectDetails] = useState<ProjectDetails | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [detailErrorDetails, setDetailErrorDetails] = useState<string | null>(null);
  const [detailFetchErrorInfo, setDetailFetchErrorInfo] = useState<ApiErrorInfo | null>(null);

  const [publicProjects, setPublicProjects] = useState<PublicProjectListItem[]>([]);
  const [publicLoading, setPublicLoading] = useState(false);
  const [publicError, setPublicError] = useState<string | null>(null);
  const [publicErrorDetails, setPublicErrorDetails] = useState<string | null>(null);
  const [publicFetchErrorInfo, setPublicFetchErrorInfo] = useState<ApiErrorInfo | null>(null);

  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const dismissToast = useCallback(() => setToastMessage(null), []);

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
      setErrorDetails(null);
      setLastFetchErrorInfo(null);
      return;
    }
    setApiUnavailable(null);
    setLastFetchErrorInfo(info);
    const e = err instanceof Error ? err : new Error(String(err));
    setError(`Network error: ${e.name} ${e.message || info.message || fallbackMessage}`);
    setErrorDetails(
      JSON.stringify(
        {
          status: info.status ?? null,
          message: info.message || fallbackMessage,
          request: info.request ?? null,
          error_report_id: info.errorReportRequestId ?? null,
          stack: e.stack ?? null,
          lastRequest: getLastRequest(),
        },
        null,
        2,
      ),
    );
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
      setErrorDetails(null);
      setLastFetchErrorInfo(null);
      setAuthError(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    setErrorDetails(null);
    setLastFetchErrorInfo(null);
    setApiUnavailable(null);

    try {
      if (!getToken()) {
        await tryAuth();
      }

      const data = await getProjects();
      setProjects(data);
      setAuthError(null);
      setLastFetchErrorInfo(null);
    } catch (err) {
      if (err instanceof ApiError && err.kind === 'http' && err.status === 401) {
        clearToken();
        try {
          await tryAuth();
          const retriedData = await getProjects();
          setProjects(retriedData);
          setAuthError(null);
          setError(null);
          setErrorDetails(null);
          setLastFetchErrorInfo(null);
          setApiUnavailable(null);
          setLoading(false);
          return;
        } catch (retryErr) {
          const retryInfo = getApiErrorInfo(retryErr);
          if (isApiUnavailableError(retryInfo)) {
            setApiUnavailable(retryInfo);
            setError(null);
            setErrorDetails(null);
            setLastFetchErrorInfo(null);
            setAuthError(null);
          } else {
            setApiUnavailable(null);
            setLastFetchErrorInfo(retryInfo);
            setAuthError(retryInfo.message);
            const e = retryErr instanceof Error ? retryErr : new Error(String(retryErr));
            setError(`Network error: ${e.name} ${e.message || retryInfo.message || 'Request failed'}`);
            setErrorDetails(
              JSON.stringify(
                {
                  status: retryInfo.status ?? null,
                  message: retryInfo.message || null,
                  request: retryInfo.request ?? null,
                  error_report_id: retryInfo.errorReportRequestId ?? null,
                  stack: e.stack ?? null,
                  lastRequest: getLastRequest(),
                },
                null,
                2,
              ),
            );
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

  const loadPublicProjects = useCallback(async () => {
    if (isDemo) {
      setPublicProjects([]);
      setPublicError('Подключите API для просмотра публичных проектов');
      setPublicErrorDetails(null);
      setPublicFetchErrorInfo(null);
      return;
    }

    setPublicLoading(true);
    setPublicError(null);
    setPublicErrorDetails(null);
    setPublicFetchErrorInfo(null);

    try {
      const data = await getPublicProjects({ limit: 50, offset: 0 });
      setPublicProjects(data);
    } catch (err) {
      const info = getApiErrorInfo(err);
      const e = err instanceof Error ? err : new Error(String(err));
      setPublicFetchErrorInfo(info);
      setPublicError(`Network error: ${e.name} ${e.message || info.message || 'Request failed'}`);
      setPublicErrorDetails(
        JSON.stringify(
          {
            status: info.status ?? null,
            message: info.message || null,
            request: info.request ?? null,
            error_report_id: info.errorReportRequestId ?? null,
            stack: e.stack ?? null,
            lastRequest: getLastRequest(),
          },
          null,
          2,
        ),
      );
      setPublicProjects([]);
    } finally {
      setPublicLoading(false);
    }
  }, [isDemo]);

  useEffect(() => {
    if (route.kind !== 'app') {
      return;
    }
    loadProjects();
  }, [loadProjects, route.kind]);

  const handleCreateProject = useCallback(async () => {
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
      if (!getToken()) {
        await tryAuth();
      }

      const created = await createDraft();

      // Jump directly into the newly created project to avoid a dead-end empty UX.
      setScreen('detail');
      setSelectedProjectId(created.id);
      setProjectDetails(created);
      setDetailError(null);
      setDetailErrorDetails(null);
      setDetailFetchErrorInfo(null);
      setDetailLoading(false);

      setToastMessage(`Проект создан: ${created.id.slice(0, 8)}...`);

      // Refresh list in background (safe even while user is on detail screen).
      await loadProjects();
    } catch (err) {
      const info = getApiErrorInfo(err);
      if (isApiUnavailableError(info)) {
        setApiUnavailable(info);
      } else {
        handleApiFailure(err, 'Не удалось создать проект');
      }
    } finally {
      setCreating(false);
    }
  }, [apiUnavailable, handleApiFailure, isDemo, loadProjects, tryAuth]);

  const handleOpenProject = useCallback(
    async (id: string) => {
      console.log(`[DEBUG] open project id=${id}`);
      setToastMessage(`Tap captured: ${id.slice(0, 8)}...`);

      if (isDemo) {
        return;
      }

      if (apiUnavailable) {
        return;
      }

      setScreen('detail');
      setSelectedProjectId(id);
      setDetailLoading(true);
      setDetailError(null);
      setDetailErrorDetails(null);
      setDetailFetchErrorInfo(null);
      setProjectDetails(null);

      try {
        const details = await getProject(id);
        setProjectDetails(details);
        setDetailFetchErrorInfo(null);
        console.log(`[DEBUG] loaded project details id=${id}`, details);
      } catch (err) {
        const info = getApiErrorInfo(err);
        const e = err instanceof Error ? err : new Error(String(err));
        console.error(`[DEBUG] failed to load project id=${id}`, info);
        setDetailFetchErrorInfo(info);
        setDetailError(`Network error: ${e.name} ${e.message || info.message || 'Request failed'}`);
        setDetailErrorDetails(
          JSON.stringify(
            {
              status: info.status ?? null,
              message: info.message || null,
              request: info.request ?? null,
              error_report_id: info.errorReportRequestId ?? null,
              stack: e.stack ?? null,
              lastRequest: getLastRequest(),
            },
            null,
            2,
          ),
        );
      } finally {
        setDetailLoading(false);
      }
    },
    [apiUnavailable, isDemo],
  );

  const handleOpenPublicProject = useCallback(
    (idOrSlug: string) => {
      openPublicProject(idOrSlug);
    },
    [openPublicProject],
  );

  const handleOpenWizard = useCallback(
    (id: string) => {
      if (isDemo) {
        return;
      }
      if (apiUnavailable) {
        return;
      }
      setScreen('wizard');
      setSelectedProjectId(id);
    },
    [apiUnavailable, isDemo],
  );

  const handleBack = useCallback(() => {
    setScreen('list');
    setSelectedProjectId(null);
    setProjectDetails(null);
    setDetailError(null);
    setDetailErrorDetails(null);
    setDetailFetchErrorInfo(null);
  }, []);

  return (
    <div className={`container${selfTestVisible ? ' selftest-enabled' : ''}`}>
      {toastMessage && <Toast message={toastMessage} onDismiss={dismissToast} />}

      {route.kind === 'public' ? (
        <PublicProjectScreen idOrSlug={route.idOrSlug} onBack={handlePublicBack} />
      ) : screen === 'detail' ? (
        <ProjectDetailScreen
          details={projectDetails}
          loading={detailLoading}
          error={detailError}
          errorDetails={detailErrorDetails}
          fetchInfo={detailFetchErrorInfo}
          onBack={handleBack}
          onRetry={() => selectedProjectId && handleOpenProject(selectedProjectId)}
        />
      ) : screen === 'wizard' ? (
        selectedProjectId ? (
          <WizardScreen
            projectId={selectedProjectId}
            onBack={handleBack}
            onOpenDetails={(id) => void handleOpenProject(id)}
            onOpenPublic={(idOrSlug) => handleOpenPublicProject(idOrSlug)}
            onAfterSave={() => loadProjects()}
          />
        ) : (
          <ErrorMessage message="Project ID is missing" onRetry={handleBack} />
        )
      ) : (
        <>
          <header className="header">
            <h1 className="header-title">{feed === 'my' ? 'Мои проекты' : 'Публичные'}</h1>
            <p className="header-subtitle">{isDemo ? 'Подключите API для работы с реальными данными' : 'Управление проектами'}</p>
            {authError && <p className="auth-error">{authError}</p>}
          </header>

          <main className="main">
            <section className="projects">
              <h2 className="section-title">{feed === 'my' ? 'Мои проекты' : 'Публичные'}</h2>

              <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
                <button
                  type="button"
                  className={`btn ${feed === 'my' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ flex: 1, padding: '0.6rem 0.75rem' }}
                  onClick={() => setFeed('my')}
                >
                  Мои проекты
                </button>
                <button
                  type="button"
                  className={`btn ${feed === 'public' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ flex: 1, padding: '0.6rem 0.75rem' }}
                  onClick={() => {
                    setFeed('public');
                    void loadPublicProjects();
                  }}
                >
                  Публичные
                </button>
              </div>

              {feed === 'my' ? (
                loading ? (
                bootWatchdogFired ? (
                  <InitDiagnosticsScreen apiBaseUrl={import.meta.env.VITE_API_PUBLIC_URL || ''} onRetry={loadProjects} />
                ) : (
                  <LoadingSpinner />
                )
              ) : apiUnavailable && apiBaseUrl ? (
                <ApiUnavailablePanel apiBaseUrl={apiBaseUrl} errorInfo={apiUnavailable} onRetry={loadProjects} />
              ) : error ? (
                <ErrorMessage message={error} details={errorDetails} fetchInfo={lastFetchErrorInfo} onRetry={loadProjects} />
              ) : projects.length === 0 ? (
                <EmptyState />
              ) : (
                <div
                  className="projects-list"
                  onPointerDownCapture={(e) => {
                    recordTapFromReactEvent('pointerdown', (e as any).nativeEvent);
                    const t = e.target as HTMLElement | null;
                    console.log(
                      `[DEBUG] pointerdown capture target=${t?.tagName?.toLowerCase() || '-'} class=${String((t as any)?.className || '-')} x=${(e as any).clientX ?? '-'} y=${(e as any).clientY ?? '-'}`,
                    );
                  }}
                  onClickCapture={(e) => {
                    recordTapFromReactEvent('click', (e as any).nativeEvent);
                    const t = e.target as HTMLElement | null;
                    console.log(
                      `[DEBUG] click capture target=${t?.tagName?.toLowerCase() || '-'} class=${String((t as any)?.className || '-')} x=${(e as any).clientX ?? '-'} y=${(e as any).clientY ?? '-'}`,
                    );
                  }}
                  onTouchEndCapture={(e) => {
                    const native = (e as any).nativeEvent as TouchEvent | undefined;
                    const touch = native?.changedTouches?.[0];
                    recordTapFromReactEvent('touchend', {
                      clientX: touch?.clientX,
                      clientY: touch?.clientY,
                      target: (e as any).target,
                    });
                    const t = e.target as HTMLElement | null;
                    console.log(`[DEBUG] touchend capture target=${t?.tagName?.toLowerCase() || '-'} class=${String((t as any)?.className || '-')}`);
                  }}
                >
                  {projects.map((project) => (
                    <ProjectCard key={project.id} project={project} onOpen={handleOpenProject} onContinue={handleOpenWizard} />
                  ))}
                </div>
              )
              ) : publicLoading ? (
                <LoadingSpinner />
              ) : publicError ? (
                <ErrorMessage message={publicError} details={publicErrorDetails} fetchInfo={publicFetchErrorInfo} onRetry={loadPublicProjects} />
              ) : publicProjects.length === 0 ? (
                <div className="empty-state">
                  <p>Пока нет опубликованных проектов</p>
                </div>
              ) : (
                <div
                  className="projects-list"
                  onPointerDownCapture={(e) => {
                    recordTapFromReactEvent('pointerdown', (e as any).nativeEvent);
                    const t = e.target as HTMLElement | null;
                    console.log(
                      `[DEBUG] pointerdown capture target=${t?.tagName?.toLowerCase() || '-'} class=${String((t as any)?.className || '-')} x=${(e as any).clientX ?? '-'} y=${(e as any).clientY ?? '-'}`,
                    );
                  }}
                  onClickCapture={(e) => {
                    recordTapFromReactEvent('click', (e as any).nativeEvent);
                    const t = e.target as HTMLElement | null;
                    console.log(
                      `[DEBUG] click capture target=${t?.tagName?.toLowerCase() || '-'} class=${String((t as any)?.className || '-')} x=${(e as any).clientX ?? '-'} y=${(e as any).clientY ?? '-'}`,
                    );
                  }}
                  onTouchEndCapture={(e) => {
                    const native = (e as any).nativeEvent as TouchEvent | undefined;
                    const touch = native?.changedTouches?.[0];
                    recordTapFromReactEvent('touchend', {
                      clientX: touch?.clientX,
                      clientY: touch?.clientY,
                      target: (e as any).target,
                    });
                    const t = e.target as HTMLElement | null;
                    console.log(
                      `[DEBUG] touchend capture target=${t?.tagName?.toLowerCase() || '-'} class=${String((t as any)?.className || '-')}`,
                    );
                  }}
                >
                  {publicProjects.map((project) => (
                    <PublicProjectCard key={project.id} project={project} onOpen={handleOpenPublicProject} />
                  ))}
                </div>
              )}
            </section>

            <button className="btn btn-primary btn-full" onClick={handleCreateProject} disabled={creating || loading}>
              {creating ? 'Создание...' : 'Создать проект'}
            </button>
          </main>
        </>
      )}

      {selfTestVisible && (
        <SelfTestPanel
          onOpenProject={handleOpenProject}
          onClose={() => setSelfTestVisible(false)}
          defaultOpen={true}
        />
      )}

      <div className="build-stamp">
        build {build.shortSha} <span className="build-stamp-sep">·</span> {build.buildTime}
        <button
          type="button"
          className="build-stamp-btn"
          onClick={() => setSelfTestVisible((v) => !v)}
          aria-label="Toggle self-test"
        >
          ⚙︎
        </button>
      </div>
    </div>
  );
}

export default App;
