import { useCallback, useEffect, useMemo, useState } from 'react';
import { getProject, getProjects, getResolvedApiBaseUrl, postClientLog, type Project } from '../lib/api';
import { getBuildStamp } from '../lib/buildStamp';
import { getLastErrors, getLastRequest, getLastRequests, trackedFetch } from '../lib/fetcher';
import { getLastTap } from '../lib/tapTracker';

function normalize(value: unknown): string {
  return typeof value === 'string' ? value.trim() : '';
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
        lower.includes('token') ||
        lower.includes('cookie')
      ) {
        out[key] = '[redacted]';
        continue;
      }
      out[key] = redact(nested);
    }
    return out;
  }
  return value;
}

function toPrettyJson(value: unknown): string {
  try {
    return JSON.stringify(redact(value), null, 2);
  } catch {
    return String(value);
  }
}

function getTelegramInfo(): {
  hasWindowTelegram: boolean;
  hasWebApp: boolean;
  initDataLen: number | null;
} {
  const tg = (window as { Telegram?: { WebApp?: { initData?: string } } }).Telegram;
  const initData = tg?.WebApp?.initData;
  return {
    hasWindowTelegram: Boolean(tg),
    hasWebApp: Boolean(tg?.WebApp),
    initDataLen: typeof initData === 'string' ? initData.length : null,
  };
}

function safeApiBaseUrl(value: string | null): string | null {
  if (!value) {
    return null;
  }
  const trimmed = value.trim().replace(/\/+$/, '');
  return trimmed || null;
}

export function SelfTestPanel({
  onOpenProject,
  onClose,
  defaultOpen = true,
}: {
  onOpenProject?: (id: string) => void;
  onClose?: () => void;
  defaultOpen?: boolean;
}) {
  const build = useMemo(() => getBuildStamp(), []);
  const buildEnv = useMemo(
    () => normalize((import.meta.env as Record<string, unknown>)['VITE_BUILD_ENV']),
    [],
  );
  const apiBaseUrl = useMemo(() => safeApiBaseUrl(getResolvedApiBaseUrl()), []);
  const origin = useMemo(() => window.location.origin, []);
  const telegram = useMemo(() => getTelegramInfo(), []);

  const [open, setOpen] = useState(defaultOpen);
  const [busy, setBusy] = useState(false);
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [error, setError] = useState<string>('');
  const [output, setOutput] = useState<string>('');
  const [logAck, setLogAck] = useState<string>('');

  const [lastTap, setLastTap] = useState(() => getLastTap());
  const [lastRequest, setLastRequest] = useState(() => getLastRequest());

  useEffect(() => {
    if (!open) {
      return;
    }
    const sync = () => {
      setLastTap(getLastTap());
      setLastRequest(getLastRequest());
    };
    sync();
    const id = window.setInterval(sync, 450);
    return () => window.clearInterval(id);
  }, [open]);

  const run = useCallback(async (label: string, fn: () => Promise<unknown>) => {
    if (busy) {
      return;
    }
    setBusy(true);
    setError('');
    setOutput('');
    setLogAck('');
    try {
      const value = await fn();
      setOutput(toPrettyJson({ ok: true, action: label, result: value }));
    } catch (err) {
      const e = err instanceof Error ? err : new Error(String(err));
      setError(`Error in "${label}": ${e.name} ${e.message}`);
      setOutput(
        toPrettyJson({
          ok: false,
          action: label,
          error: { name: e.name, message: e.message, stack: e.stack ?? null },
          lastRequest: getLastRequest(),
          lastErrors: getLastErrors().slice(0, 5),
        }),
      );
    } finally {
      setBusy(false);
    }
  }, [busy]);

  const handlePingEcho = useCallback(() => {
    return run('Ping echo', async () => {
      if (!apiBaseUrl) {
        throw new Error('API base URL is not configured');
      }
      const response = await trackedFetch(`${apiBaseUrl}/debug/echo`, {
        method: 'GET',
        credentials: 'omit',
        cache: 'no-store',
        referrerPolicy: 'no-referrer',
      });
      const text = await response.text();
      let body: unknown = text;
      try {
        body = JSON.parse(text);
      } catch {
        // ignore
      }
      return { status: response.status, ok: response.ok, body };
    });
  }, [apiBaseUrl, run]);

  const handlePingHealthz = useCallback(() => {
    return run('Ping healthz', async () => {
      if (!apiBaseUrl) {
        throw new Error('API base URL is not configured');
      }
      const response = await trackedFetch(`${apiBaseUrl}/healthz`, {
        method: 'GET',
        credentials: 'omit',
        cache: 'no-store',
        referrerPolicy: 'no-referrer',
      });
      const text = await response.text();
      return { status: response.status, ok: response.ok, body: text.slice(0, 4000) };
    });
  }, [apiBaseUrl, run]);

  const handleListProjects = useCallback(() => {
    return run('List projects', async () => {
      const data = await getProjects();
      setProjects(data);
      const firstId = data[0]?.id ?? null;
      return { count: data.length, firstId, sample: data.slice(0, 3) };
    });
  }, [run]);

  const handleOpenFirstProject = useCallback(() => {
    return run('Open first project', async () => {
      const list = projects ?? (await getProjects());
      setProjects(list);
      const first = list[0];
      if (!first) {
        return { message: 'No projects in list' };
      }

      if (onOpenProject) {
        onOpenProject(first.id);
        return { id: first.id, openedVia: 'handleOpenProject' };
      }

      // Fallback: open via direct API call.
      const details = await getProject(first.id);
      return { id: first.id, openedVia: 'getProject', details };
    });
  }, [onOpenProject, projects, run]);

  const handleLogToServer = useCallback(() => {
    return run('Log to server', async () => {
      const payload = {
        ts: new Date().toISOString(),
        type: 'selftest',
        build_sha: build.sha,
        build_time: build.buildTime,
        build,
        env: buildEnv || null,
        location: {
          href: window.location.href,
          origin,
          pathname: window.location.pathname,
          search: window.location.search,
        },
        userAgent: String(navigator.userAgent || '').slice(0, 200),
        telegram,
        apiBaseUrl: apiBaseUrl ?? '(not configured)',
        lastTap: getLastTap(),
        lastRequest: getLastRequest(),
        lastRequests: getLastRequests().slice(0, 15),
        lastErrors: getLastErrors().slice(0, 15),
      };

      const res = await postClientLog(payload);
      const requestId = normalize(res.request_id);
      setLogAck(requestId ? `Logged OK (id=${requestId})` : 'Logged OK');
      return res;
    });
  }, [apiBaseUrl, build, buildEnv, origin, run, telegram]);

  const handleClose = useCallback(() => {
    try {
      const url = new URL(window.location.href);
      url.searchParams.delete('selftest');
      window.history.replaceState({}, '', url.toString());
    } catch {
      // ignore
    }
    onClose?.();
  }, [onClose]);

  return (
    <div className="selftest-panel-wrap" aria-live="polite">
      <div className={`selftest-panel${open ? ' selftest-panel-open' : ''}`}>
        <div className="selftest-panel-bar">
          <button
            type="button"
            className="selftest-panel-toggle"
            onClick={() => setOpen((v) => !v)}
            disabled={busy}
          >
            Self-test {open ? 'Hide' : 'Show'}
          </button>
          <div className="selftest-panel-meta">
            <span>build {build.shortSha}</span>
            <span className="selftest-panel-meta-sep">В·</span>
            <span className="selftest-panel-meta-muted">{build.buildTime}</span>
          </div>
          <button type="button" className="selftest-panel-close" onClick={handleClose} disabled={busy}>
            Close
          </button>
        </div>

        {open && (
          <div className="selftest-panel-body">
            <div className="selftest-panel-info">
              <div className="selftest-panel-info-row">
                <span className="selftest-k">build sha</span>
                <span className="selftest-v">{build.sha}</span>
              </div>
              <div className="selftest-panel-info-row">
                <span className="selftest-k">build env</span>
                <span className="selftest-v">{buildEnv || '-'}</span>
              </div>
              <div className="selftest-panel-info-row">
                <span className="selftest-k">origin</span>
                <span className="selftest-v">{origin}</span>
              </div>
              <div className="selftest-panel-info-row">
                <span className="selftest-k">apiBaseUrl</span>
                <span className="selftest-v">{apiBaseUrl ?? '(not configured)'}</span>
              </div>
              <div className="selftest-panel-info-row">
                <span className="selftest-k">telegram</span>
                <span className="selftest-v">
                  window.Telegram={telegram.hasWindowTelegram ? 'yes' : 'no'}, WebApp={telegram.hasWebApp ? 'yes' : 'no'}, initDataLen=
                  {telegram.initDataLen ?? '-'}
                </span>
              </div>
              <div className="selftest-panel-info-row">
                <span className="selftest-k">last tap</span>
                <span className="selftest-v">
                  {lastTap
                    ? `${new Date(lastTap.ts).toLocaleTimeString()} ${lastTap.type} x=${lastTap.x ?? '-'} y=${lastTap.y ?? '-'} target=${lastTap.targetTag ?? '-'}#${lastTap.targetId ?? '-'}`
                    : '-'}
                </span>
              </div>
              <div className="selftest-panel-info-row">
                <span className="selftest-k">last req</span>
                <span className="selftest-v">
                  {lastRequest ? `${lastRequest.method} ${lastRequest.url} status=${lastRequest.status ?? '-'} ok=${String(lastRequest.ok)}` : '-'}
                </span>
              </div>
            </div>

            <div className="selftest-panel-actions">
              <button type="button" className="btn btn-secondary" onClick={handlePingEcho} disabled={busy}>
                Ping echo
              </button>
              <button type="button" className="btn btn-secondary" onClick={handlePingHealthz} disabled={busy}>
                Ping healthz
              </button>
              <button type="button" className="btn btn-primary" onClick={handleListProjects} disabled={busy}>
                List projects
              </button>
              <button type="button" className="btn btn-primary" onClick={handleOpenFirstProject} disabled={busy}>
                Open first project
              </button>
              <button type="button" className="btn btn-secondary" onClick={handleLogToServer} disabled={busy}>
                Log to server
              </button>
            </div>

            {logAck && <div className="selftest-panel-ack">{logAck}</div>}

            {error && <div className="selftest-panel-error">{error}</div>}

            <details className="selftest-panel-details">
              <summary>Show lastRequests / lastErrors</summary>
              <pre className="selftest-panel-pre">
                {toPrettyJson({ lastRequests: getLastRequests(), lastErrors: getLastErrors() })}
              </pre>
            </details>

            {output && <pre className="selftest-panel-pre">{output}</pre>}
          </div>
        )}
      </div>
    </div>
  );
}
