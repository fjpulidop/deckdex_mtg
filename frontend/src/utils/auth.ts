/**
 * Build the backend origin URL for OAuth redirects.
 *
 * OAuth must go directly to the backend (not through Vite proxy) so the
 * backend can read its own public Host header and build correct redirect URIs.
 */
export function getBackendOrigin(): string {
  const { protocol, hostname } = window.location;
  if (hostname.includes('.app.github.dev')) {
    // Codespaces: port is encoded in the hostname
    return `${protocol}//${hostname.replace('-5173.', '-8000.')}`;
  }
  // Local dev: backend on port 8000
  return `${protocol}//${hostname}:8000`;
}

/** Redirect the browser to the Google OAuth login endpoint on the backend. */
export function redirectToGoogleLogin(): void {
  window.location.href = `${getBackendOrigin()}/api/auth/google`;
}
