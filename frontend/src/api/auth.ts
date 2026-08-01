import { i18n } from '../i18n'
import { apiFetch } from './client'

export interface AuthUser {
  username: string
  isDemo: boolean
  isAdmin: boolean
}

function toAuthUser(body: { username: string; isDemo?: boolean; isAdmin?: boolean }): AuthUser {
  return {
    username: body.username,
    isDemo: body.isDemo ?? false,
    isAdmin: body.isAdmin ?? false,
  }
}

/** Stable backend error codes mapped to i18n keys. */
const AUTH_ERROR_I18N: Record<string, string> = {
  AUTH_USERNAME_TAKEN: 'auth.usernameTaken',
  AUTH_INVALID_CREDENTIALS: 'auth.invalidCredentials',
  AUTH_RATE_LIMITED: 'auth.rateLimited',
  AUTH_PASSWORD_TOO_SHORT: 'auth.passwordTooShort',
  AUTH_PASSWORD_TOO_LONG: 'auth.passwordTooLong',
}

async function authErrorMessage(response: Response, fallback: string): Promise<string> {
  const body = await response.json().catch(() => null)
  const detail: unknown = body?.detail
  if (typeof detail === 'string' && AUTH_ERROR_I18N[detail]) {
    return i18n.global.t(AUTH_ERROR_I18N[detail])
  }
  if (typeof detail === 'string' && detail.startsWith('AUTH_')) {
    return i18n.global.t('auth.invalidInput')
  }
  if (typeof detail === 'string') {
    return detail
  }
  // FastAPI validation errors (422) carry an array detail; never stringify it.
  if (Array.isArray(detail)) {
    return i18n.global.t('auth.invalidInput')
  }
  return fallback
}

export async function register(username: string, password: string): Promise<AuthUser> {
  const res = await apiFetch('/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (!res.ok) {
    throw new Error(await authErrorMessage(res, i18n.global.t('auth.registerFailed')))
  }
  return toAuthUser(await res.json())
}

export async function login(username: string, password: string): Promise<AuthUser> {
  const res = await apiFetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (!res.ok) {
    throw new Error(await authErrorMessage(res, i18n.global.t('auth.loginFailed')))
  }
  return toAuthUser(await res.json())
}

export async function logout(): Promise<void> {
  await apiFetch('/api/auth/logout', { method: 'POST' })
}

export async function fetchCurrentUser(): Promise<AuthUser | null> {
  const res = await apiFetch('/api/auth/me')
  if (res.status === 401) return null
  if (!res.ok) throw new Error('Failed to fetch user')
  return toAuthUser(await res.json())
}
