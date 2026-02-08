export interface LastTapEntry {
  ts: number;
  type: 'pointerdown' | 'pointerup' | 'click' | 'touchend';
  x: number | null;
  y: number | null;
  targetTag: string | null;
  targetId: string | null;
  targetClass: string | null;
}

let installed = false;
let lastTap: LastTapEntry | null = null;

function safeTrim(value: unknown, maxLen: number): string | null {
  if (typeof value !== 'string') {
    return null;
  }
  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }
  return trimmed.length > maxLen ? trimmed.slice(0, maxLen) : trimmed;
}

function describeTarget(target: EventTarget | null): Pick<LastTapEntry, 'targetTag' | 'targetId' | 'targetClass'> {
  if (!target || !(target instanceof Element)) {
    return { targetTag: null, targetId: null, targetClass: null };
  }
  return {
    targetTag: safeTrim(target.tagName?.toLowerCase(), 32),
    targetId: safeTrim((target as HTMLElement).id, 64),
    targetClass: safeTrim((target as HTMLElement).className, 180),
  };
}

function record(type: LastTapEntry['type'], x: number | null, y: number | null, target: EventTarget | null): void {
  const desc = describeTarget(target);
  lastTap = {
    ts: Date.now(),
    type,
    x,
    y,
    ...desc,
  };
}

export function getLastTap(): LastTapEntry | null {
  return lastTap;
}

export function recordTapFromReactEvent(
  type: LastTapEntry['type'],
  e: { clientX?: number; clientY?: number; target?: EventTarget | null },
): void {
  const x = typeof e.clientX === 'number' ? e.clientX : null;
  const y = typeof e.clientY === 'number' ? e.clientY : null;
  record(type, x, y, e.target ?? null);
}

export function installGlobalTapTracking(): void {
  if (typeof window === 'undefined') {
    return;
  }
  if (installed) {
    return;
  }
  installed = true;

  window.addEventListener(
    'pointerdown',
    (event) => {
      record('pointerdown', event.clientX, event.clientY, event.target);
    },
    { capture: true },
  );

  window.addEventListener(
    'pointerup',
    (event) => {
      record('pointerup', event.clientX, event.clientY, event.target);
    },
    { capture: true },
  );

  window.addEventListener(
    'click',
    (event) => {
      record('click', (event as MouseEvent).clientX, (event as MouseEvent).clientY, event.target);
    },
    { capture: true },
  );

  window.addEventListener(
    'touchend',
    (event) => {
      const touch = (event as TouchEvent).changedTouches?.[0];
      record('touchend', touch ? touch.clientX : null, touch ? touch.clientY : null, event.target);
    },
    { capture: true },
  );
}

