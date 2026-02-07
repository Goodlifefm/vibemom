export interface LastRequestEntry {
  id: string;
  url: string;
  method: string;
  startTs: number;
  endTs: number | null;
  ok: boolean | null;
  status: number | null;
  errorMessage: string | null;
}

export interface LastErrorEntry {
  id: string;
  ts: number;
  type: 'error' | 'unhandledrejection';
  name: string | null;
  message: string;
  stack: string | null;
  filename: string | null;
  lineno: number | null;
  colno: number | null;
}

const MAX_LAST_REQUESTS = 25;
const MAX_LAST_ERRORS = 25;

const lastRequests: LastRequestEntry[] = [];
const lastErrors: LastErrorEntry[] = [];

let globalHandlersInstalled = false;
let seq = 0;

function nextId(prefix: string): string {
  seq += 1;
  return `${prefix}-${Date.now()}-${seq}`;
}

function pushRing<T>(arr: T[], item: T, max: number): void {
  arr.unshift(item);
  if (arr.length > max) {
    arr.length = max;
  }
}

function asUrlString(input: RequestInfo | URL): string {
  if (typeof input === 'string') {
    return input;
  }
  if (input instanceof URL) {
    return input.toString();
  }
  // Request
  return input.url;
}

function asMethod(input: RequestInfo | URL, init?: RequestInit): string {
  if (init?.method) {
    return init.method.toUpperCase();
  }
  if (typeof input !== 'string' && !(input instanceof URL) && typeof input.method === 'string') {
    return input.method.toUpperCase();
  }
  return 'GET';
}

export function getLastRequests(): LastRequestEntry[] {
  return [...lastRequests];
}

export function getLastRequest(): LastRequestEntry | null {
  return lastRequests[0] ?? null;
}

export function getLastErrors(): LastErrorEntry[] {
  return [...lastErrors];
}

export function installGlobalErrorTracking(): void {
  if (typeof window === 'undefined') {
    return;
  }
  if (globalHandlersInstalled) {
    return;
  }
  globalHandlersInstalled = true;

  window.addEventListener('error', (event) => {
    try {
      const err = (event as ErrorEvent).error;
      const error = err instanceof Error ? err : null;
      pushRing(
        lastErrors,
        {
          id: nextId('err'),
          ts: Date.now(),
          type: 'error',
          name: error?.name ?? null,
          message: error?.message ?? (event as ErrorEvent).message ?? 'Unknown error',
          stack: error?.stack ?? null,
          filename: (event as ErrorEvent).filename ?? null,
          lineno: (event as ErrorEvent).lineno ?? null,
          colno: (event as ErrorEvent).colno ?? null,
        },
        MAX_LAST_ERRORS,
      );
    } catch {
      // ignore
    }
  });

  window.addEventListener('unhandledrejection', (event) => {
    try {
      const reason = (event as PromiseRejectionEvent).reason;
      const error = reason instanceof Error ? reason : null;
      const message = error?.message ?? (typeof reason === 'string' ? reason : JSON.stringify(reason));

      pushRing(
        lastErrors,
        {
          id: nextId('rej'),
          ts: Date.now(),
          type: 'unhandledrejection',
          name: error?.name ?? null,
          message: message || 'Unhandled rejection',
          stack: error?.stack ?? null,
          filename: null,
          lineno: null,
          colno: null,
        },
        MAX_LAST_ERRORS,
      );
    } catch {
      // ignore
    }
  });
}

export async function trackedFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const startTs = Date.now();
  const entry: LastRequestEntry = {
    id: nextId('req'),
    url: asUrlString(input),
    method: asMethod(input, init),
    startTs,
    endTs: null,
    ok: null,
    status: null,
    errorMessage: null,
  };

  pushRing(lastRequests, entry, MAX_LAST_REQUESTS);

  try {
    const response = await fetch(input, init);
    entry.endTs = Date.now();
    entry.ok = response.ok;
    entry.status = response.status;
    return response;
  } catch (err) {
    entry.endTs = Date.now();
    entry.ok = false;
    entry.status = null;
    entry.errorMessage = err instanceof Error ? `${err.name}: ${err.message}` : String(err);
    throw err;
  }
}

