/**
 * Shared fetch wrapper for the Fridge Pal API.
 *
 * Every request includes session credentials. A 401 from any endpoint outside
 * `/api/auth/*` means the session expired or was invalidated server-side; the
 * registered handler (wired once in App.vue) clears auth state and returns the
 * user to the login screen instead of leaving them on a broken "logged in"
 * page. The auth endpoints own their own 401 semantics (bad credentials,
 * `/auth/me` probe) and are excluded.
 */
let unauthorizedHandler: (() => void) | null = null

export function setUnauthorizedHandler(handler: (() => void) | null): void {
  unauthorizedHandler = handler
}

function isAuthPath(path: string): boolean {
  return path.startsWith('/api/auth/')
}

export async function apiFetch(input: string, init?: RequestInit): Promise<Response> {
  const response = await fetch(input, { credentials: 'include', ...init })
  if (response.status === 401 && !isAuthPath(input)) {
    unauthorizedHandler?.()
  }
  return response
}
