import { useCallback, useEffect, useMemo, useState } from 'react';
import { useBuildStamp } from '../lib/useBuildStamp';
import { trackedFetch } from '../lib/fetcher';

const USER_AGENT_MAX_LEN = 160;
const DEBUG_ECHO_TIMEOUT_MS = 1800;

type DebugEchoResult =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; httpStatus: number; body: string }
  | { status: 'error'; error: string };

function truncate(text: string, maxLen: number): string {
  if (text.length <= maxLen) {
    return text;
  }
  return `${text.slice(0, Math.max(0, maxLen - 3))}...`;
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
      if (lower === 'initdata' || lower === 'authorization' || lower === 'cookie' || lower === 'cookies') {
        out[key] = '[redacted]';
        continue;
      }
      out[key] = redact(nested);
    }
    return out;
  }
  return value;
}

function formatMaybeJson(text: string): string {
  const trimmed = text.trim();
  if (!trimmed) {
    return '';
  }

  try {
    return JSON.stringify(redact(JSON.parse(trimmed) as unknown), null, 2);
  } catch {
    return trimmed;
  }
}

async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    // Fallback for older/locked-down WebViews.
    try {
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.setAttribute('readonly', 'true');
      textarea.style.position = 'fixed';
      textarea.style.left = '-9999px';
      textarea.style.top = '0';
      document.body.appendChild(textarea);
      textarea.select();
      const ok = document.execCommand('copy');
      document.body.removeChild(textarea);
      return ok;
    } catch {
      return false;
    }
  }
}

function normalizeApiBaseUrl(value: string): string {
  return value.trim().replace(/\/+$/, '');
}

export function InitDiagnosticsScreen({
  apiBaseUrl,
  onRetry,
}: {
  apiBaseUrl: string;
  onRetry?: () => void;
}) {
  const build = useBuildStamp();
  const userAgent = useMemo(() => truncate(navigator.userAgent ?? '', USER_AGENT_MAX_LEN), []);
  const origin = useMemo(() => document.location.origin, []);

  const hasTelegram = useMemo(() => Boolean((window as { Telegram?: unknown }).Telegram), []);
  const hasTelegramWebApp = useMemo(
    () => Boolean((window as { Telegram?: { WebApp?: unknown } }).Telegram?.WebApp),
    [],
  );
  const isTelegramWebView = hasTelegramWebApp;

  const apiBaseUrlTrimmed = useMemo(() => apiBaseUrl.trim(), [apiBaseUrl]);
  const apiBaseUrlForFetch = useMemo(
    () => (apiBaseUrlTrimmed ? normalizeApiBaseUrl(apiBaseUrlTrimmed) : ''),
    [apiBaseUrlTrimmed],
  );
  const resolvedApiOrigin = useMemo(() => {
    if (!apiBaseUrlForFetch) {
      return '';
    }
    try {
      return new URL(apiBaseUrlForFetch).origin;
    } catch {
      return '';
    }
  }, [apiBaseUrlForFetch]);

  const [echo, setEcho] = useState<DebugEchoResult>({ status: 'idle' });
  const [copyStatus, setCopyStatus] = useState<'idle' | 'ok' | 'error'>('idle');

  useEffect(() => {
    if (!apiBaseUrlForFetch) {
      setEcho({ status: 'error', error: 'VITE_API_PUBLIC_URL is empty' });
      return;
    }

    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), DEBUG_ECHO_TIMEOUT_MS);

    setEcho({ status: 'loading' });

    (async () => {
      try {
        const response = await trackedFetch(`${apiBaseUrlForFetch}/debug/echo`, {
          method: 'GET',
          // Never include cookies or authorization for this diagnostic call.
          credentials: 'omit',
          cache: 'no-store',
          referrerPolicy: 'no-referrer',
          signal: controller.signal,
        });

        const text = await response.text();
        setEcho({ status: 'success', httpStatus: response.status, body: formatMaybeJson(text) });
      } catch (err) {
        let message = err instanceof Error ? err.message : String(err);
        if (err instanceof DOMException && err.name === 'AbortError') {
          message = `Timeout after ${DEBUG_ECHO_TIMEOUT_MS}ms`;
        }
        setEcho({ status: 'error', error: message });
      } finally {
        window.clearTimeout(timeoutId);
      }
    })();

    return () => {
      window.clearTimeout(timeoutId);
      controller.abort();
    };
  }, [apiBaseUrlForFetch]);

  const diagnosticsJson = useMemo(() => {
    const payload: Record<string, unknown> = {
      build,
      userAgent,
      hasTelegram,
      hasTelegramWebApp,
      isTelegramWebView,
      origin,
      apiBaseUrl,
      resolvedApiOrigin,
      debugEcho:
        echo.status === 'success'
          ? { ok: true, status: echo.httpStatus, body: echo.body }
          : echo.status === 'error'
            ? { ok: false, error: echo.error }
            : { ok: false, error: echo.status },
    };

    return JSON.stringify(payload, null, 2);
  }, [apiBaseUrl, build, echo, hasTelegram, hasTelegramWebApp, isTelegramWebView, origin, resolvedApiOrigin, userAgent]);

  const handleCopy = useCallback(async () => {
    setCopyStatus('idle');
    const ok = await copyToClipboard(diagnosticsJson);
    setCopyStatus(ok ? 'ok' : 'error');
    window.setTimeout(() => setCopyStatus('idle'), 2000);
  }, [diagnosticsJson]);

  const handleOpenSelfTest = useCallback(() => {
    const url = new URL(window.location.href);
    url.searchParams.set('selftest', '1');
    window.location.href = url.toString();
  }, []);

  return (
    <div className="error init-diagnostics">
      <div className="init-diagnostics-header">
        <h2 className="init-diagnostics-title">Диагностика</h2>
        <p className="init-diagnostics-subtitle">
          Приложение не завершило первичную инициализацию за ~3 секунды. Ниже безопасные данные для отладки.
        </p>
      </div>

      <div className="init-diagnostics-actions">
        {onRetry && (
          <button className="btn btn-secondary" onClick={onRetry}>
            Retry
          </button>
        )}
        <button className="btn btn-secondary" onClick={handleOpenSelfTest}>
          Open self-test
        </button>
        <button className="btn btn-primary" onClick={handleCopy}>
          Copy diagnostics
        </button>
        {copyStatus !== 'idle' && (
          <span className={`init-diagnostics-copy${copyStatus === 'error' ? ' init-diagnostics-copy-error' : ''}`}>
            {copyStatus === 'ok' ? 'Copied' : 'Copy failed'}
          </span>
        )}
      </div>

      <div className="diagnostics-panel">
        <div className="diagnostics-content">
          <div className="diagnostics-row">
            <span className="diagnostics-key">build</span>
            <span className="diagnostics-value">
              {build.shortSha} <span className="build-stamp-sep">·</span> {build.buildTime}
            </span>
          </div>
          <div className="diagnostics-row">
            <span className="diagnostics-key">userAgent</span>
            <span className="diagnostics-value">{userAgent}</span>
          </div>
          <div className="diagnostics-row">
            <span className="diagnostics-key">window.Telegram</span>
            <span className="diagnostics-value">{hasTelegram ? 'yes' : 'no'}</span>
          </div>
          <div className="diagnostics-row">
            <span className="diagnostics-key">Telegram.WebApp</span>
            <span className="diagnostics-value">{hasTelegramWebApp ? 'yes' : 'no'}</span>
          </div>
          <div className="diagnostics-row">
            <span className="diagnostics-key">isTelegramWebView</span>
            <span className="diagnostics-value">{isTelegramWebView ? 'true' : 'false'}</span>
          </div>
          <div className="diagnostics-row">
            <span className="diagnostics-key">origin</span>
            <span className="diagnostics-value">{origin}</span>
          </div>
          <div className="diagnostics-row">
            <span className="diagnostics-key">apiBaseUrl</span>
            <span className="diagnostics-value">{apiBaseUrl || '-'}</span>
          </div>
          <div className="diagnostics-row">
            <span className="diagnostics-key">resolvedApiOrigin</span>
            <span className="diagnostics-value">{resolvedApiOrigin || '-'}</span>
          </div>
          <div className="diagnostics-row">
            <span className="diagnostics-key">debug.echo</span>
            <div className="diagnostics-value diagnostics-echo">
              {echo.status === 'loading' && <span>Loading...</span>}
              {echo.status === 'success' && (
                <pre className="diagnostics-echo-output">{echo.body || `(HTTP ${echo.httpStatus})`}</pre>
              )}
              {echo.status === 'error' && <pre className="diagnostics-echo-output diagnostics-echo-output-error">{echo.error}</pre>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
