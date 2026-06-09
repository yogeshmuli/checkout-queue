function publicAppUrl() {
  const configuredUrl = import.meta.env.VITE_PUBLIC_APP_URL?.trim();
  const fallbackUrl = typeof window !== 'undefined' ? window.location.origin : '';
  return (configuredUrl || fallbackUrl).replace(/\/+$/, '');
}

export function buildPublicAppUrl(path, params = {}) {
  const url = new URL(path, publicAppUrl());
  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined && value !== '') {
      url.searchParams.set(key, String(value));
    }
  }
  return url.href;
}
