/**
 * The ONE transport + session module for the product frontend.
 *
 * Responsibilities (each has exactly one owner — this file):
 *  - point the generated client at the API,
 *  - attach the access token,
 *  - refresh once on 401 with a single-flight queue, then replay,
 *  - surface backend AppError payloads as typed ApiError.
 *
 * Routes/pages never touch fetch or the raw client; they call services.
 */
import { client } from '@replo/api-client';
import { refreshApiUserRefreshPost } from '@replo/api-client';
import type { TokenWithUser } from '@replo/api-client';

export const API_BASE_URL: string =
  import.meta.env?.VITE_API_URL ?? 'http://localhost:8000';

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: unknown;

  constructor(status: number, message: string, code = 'unknown', details: unknown = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }

  get isUnauthorized(): boolean {
    return this.status === 401;
  }
}

type SessionTokens = { accessToken: string; refreshToken: string };

/** Session persistence lives here, not in components or services. */
const STORAGE_KEY = 'replo.session';
export function loadSession(): TokenWithUser | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as TokenWithUser) : null;
  } catch {
    return null;
  }
}
export function saveSession(session: TokenWithUser): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
}
export function clearSession(): void {
  localStorage.removeItem(STORAGE_KEY);
}

function readBody(error: Response, body: unknown): { message: string; code: string; details: unknown } {
  if (body && typeof body === 'object' && 'detail' in (body as Record<string, unknown>)) {
    const detail = (body as Record<string, unknown>)['detail'];
    if (typeof detail === 'string') return { message: detail, code: 'error', details: null };
    if (detail && typeof detail === 'object') {
      const d = detail as Record<string, unknown>;
      return {
        message: typeof d.message === 'string' ? d.message : 'Request failed',
        code: typeof d.code === 'string' ? d.code : 'error',
        details: d,
      };
    }
  }
  return { message: `Request failed (${error.status})`, code: 'error', details: body ?? null };
}

let session: TokenWithUser | null = loadSession();

/** Single-flight refresh: concurrent 401s share one refresh call. */
let refreshInFlight: Promise<TokenWithUser | null> | null = null;

async function refreshSession(): Promise<TokenWithUser | null> {
  const current = session;
  if (!current?.refresh_token) return null;
  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      try {
        const { data, error } = await refreshApiUserRefreshPost({
          body: { refresh_token: current.refresh_token },
        });
        if (error || !data) return null;
        saveSession(data);
        session = data;
        notify();
        return data;
      } catch {
        return null;
      } finally {
        refreshInFlight = null;
      }
    })();
  }
  return refreshInFlight;
}

client.setConfig({
  baseUrl: API_BASE_URL,
  fetch: async (request) => {
    const headers = new Headers(request.headers);
    if (session?.access_token) headers.set('Authorization', `Bearer ${session.access_token}`);
    const authed = new Request(request, { headers });
    const response = await fetch(authed);
    if (response.status === 401 && session && !authed.url.includes('/api/user/refresh')) {
      const renewed = await refreshSession();
      if (renewed) {
        const retryHeaders = new Headers(request.headers);
        retryHeaders.set('Authorization', `Bearer ${renewed.access_token}`);
        return fetch(new Request(request, { headers: retryHeaders }));
      }
      // Refresh failed: the session is over. Listeners route to login.
      clearSession();
      session = null;
      notify();
    }
    return response;
  },
});

/** Maps a failed generated-client call ({ data, error } tuple) to ApiError. */
export function toApiError(error: unknown, status = 0): ApiError {
  if (error instanceof ApiError) return error;
  if (error && typeof error === 'object' && 'detail' in (error as Record<string, unknown>)) {
    const { message, code, details } = readBody({ status } as Response, error);
    return new ApiError(status, message, code, details);
  }
  return new ApiError(status, error instanceof Error ? error.message : 'Request failed');
}

export function currentSession(): TokenWithUser | null {
  return session;
}

export function adoptSession(next: TokenWithUser): void {
  session = next;
  saveSession(next);
  notify();
}

export function dropSession(): void {
  session = null;
  clearSession();
  notify();
}

/* ---- minimal external store (no extra dependency) ---- */
type Listener = () => void;
const listeners = new Set<Listener>();
function notify(): void {
  for (const l of listeners) l();
}
export function subscribeSession(listener: Listener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export type { SessionTokens };
