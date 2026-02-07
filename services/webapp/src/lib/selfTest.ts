export function isSelfTestEnabled(): boolean {
  const envFlag = String(import.meta.env.VITE_SELF_TEST || '').trim() === '1';
  if (envFlag) {
    return true;
  }

  try {
    return new URLSearchParams(window.location.search).get('selftest') === '1';
  } catch {
    return false;
  }
}

