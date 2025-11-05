import type { RequestCookies } from 'next/dist/compiled/@edge-runtime/cookies';

export function isAuthenticatedFromCookies(cookies: RequestCookies | Record<string, string>) {
  try {
    const token = typeof cookies.get === 'function' ? (cookies as any).get('auth_token')?.value : (cookies as Record<string, string>)['auth_token'];
    return Boolean(token);
  } catch {
    return false;
  }
}

export async function getUserFromToken(token: string) {
  return null as unknown as { id: string; email: string } | null;
}