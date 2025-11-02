import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';


const PUBLIC_PATHS = ['/', '/login', '/signup', '/about'];

const PRIVATE_PATHS = ['/dashboard', '/my-tutorials', '/settings', '/repo', '/tutorial', '/edit'];

const isInPaths = (pathname: string, paths: string[]) =>
  paths.some(p => pathname === p || pathname.startsWith(p + '/'));

function isTokenExpired(token: string | undefined): boolean {
  if (!token) return true;
  try {
    const base64Url = token.split('.')[1];
    if (!base64Url) return true;
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    const payload = JSON.parse(jsonPayload);
    const exp = payload?.exp;
    if (!exp) return false;
    const nowInSeconds = Math.floor(Date.now() / 1000);
    return nowInSeconds >= exp;
  } catch {
    return true;
  }
}

function getAuthToken(req: NextRequest) {
  return req.cookies.get('auth_token')?.value ?? null;
}

function getRefreshToken(req: NextRequest) {
  return req.cookies.get('refresh_token')?.value ?? null;
}

function isRefreshTokenExpired(token: string | undefined): boolean {
  if (!token) return true;
  try {
    const base64Url = token.split('.')[1];
    if (!base64Url) return true;
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    const payload = JSON.parse(jsonPayload);
    const exp = payload?.exp;
    if (!exp) return false;
    const nowInSeconds = Math.floor(Date.now() / 1000);
    return nowInSeconds >= exp;
  } catch {
    return true;
  }
}

export default function middleware(req: NextRequest) {
  const token = getAuthToken(req) ?? undefined;
  const refreshToken = getRefreshToken(req) ?? undefined;
  const hasToken = !!token;
  const hasRefreshToken = !!refreshToken;
  const expired = hasToken ? isTokenExpired(token) : false;
  const refreshExpired = hasRefreshToken ? isRefreshTokenExpired(refreshToken) : true;
  const { pathname } = req.nextUrl;

  // Bypass for static, api, and public assets
  if (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/api') ||
    pathname.startsWith('/static') ||
    pathname.startsWith('/.well-known')
  ) {
    return NextResponse.next();
  }

  const isPublicPath = isInPaths(pathname, PUBLIC_PATHS);
  const isPrivatePath = isInPaths(pathname, PRIVATE_PATHS);

  // 解析 referrer，用于判断来源路径是否为私有路径
  const referer = req.headers.get('referer');
  let refererPathname: string | null = null;
  if (referer) {
    try {
      refererPathname = new URL(referer).pathname;
    } catch {}
  }
  const referrerIsPrivate = refererPathname ? isInPaths(refererPathname, PRIVATE_PATHS) : false;

  // If access token is expired but refresh token is valid, allow the request
  // The apiClient will handle token refresh automatically
  // Only redirect if BOTH tokens are expired/missing
  if (expired && (!hasRefreshToken || refreshExpired)) {
    // Both tokens expired or missing - redirect to login
    if (isPrivatePath) {
      const url = new URL('/login', req.url);
      url.searchParams.set('error', 'expired');
      url.searchParams.set('next', pathname + req.nextUrl.search);
      const res = NextResponse.redirect(url);
      res.cookies.set('auth_token', '', { maxAge: 0, path: '/' });
      res.cookies.set('refresh_token', '', { maxAge: 0, path: '/' });
      return res;
    }

    // Current on login page: only show expired message if coming from private path
    if (pathname === '/login') {
      if (referrerIsPrivate) {
        const loginUrl = new URL('/login', req.url);
        loginUrl.searchParams.set('error', 'expired');
        const res = NextResponse.redirect(loginUrl);
        res.cookies.set('auth_token', '', { maxAge: 0, path: '/' });
        res.cookies.set('refresh_token', '', { maxAge: 0, path: '/' });
        return res;
      }
      const res = NextResponse.next();
      res.cookies.set('auth_token', '', { maxAge: 0, path: '/' });
      res.cookies.set('refresh_token', '', { maxAge: 0, path: '/' });
      return res;
    }

    // Public path: clear tokens and allow
    const res = NextResponse.next();
    res.cookies.set('auth_token', '', { maxAge: 0, path: '/' });
    res.cookies.set('refresh_token', '', { maxAge: 0, path: '/' });
    return res;
  }

  // Access token expired but refresh token valid - allow request through
  // apiClient will handle the refresh automatically
  if (expired && !refreshExpired) {
    // Just allow the request - apiClient will refresh the token
    return NextResponse.next();
  }

  // 已登录且未过期，访问登录/注册 -> 重定向到仪表盘
  if (hasToken && !expired && (pathname === '/login' || pathname === '/signup')) {
    return NextResponse.redirect(new URL('/dashboard', req.url));
  }

  // 未登录访问私有路径 -> 重定向到登录（不显示过期提示）
  if (!hasToken && isPrivatePath && !isPublicPath) {
    const url = new URL('/login', req.url);
    url.searchParams.set('next', pathname + req.nextUrl.search);
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/login', '/dashboard', '/my-tutorials', '/settings', '/repo/:path*', '/tutorial/:path*', '/edit/:path*'],
};