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

export default function middleware(req: NextRequest) {
  const token = getAuthToken(req) ?? undefined;
  const hasToken = !!token;
  const expired = hasToken ? isTokenExpired(token) : false;
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

  // 当存在 token 且已过期：根据访问/来源场景决定是否提示“会话过期”
  if (hasToken && expired) {
    // 在私有路径访问时，重定向到登录并显示过期提示
    if (isPrivatePath) {
      const url = new URL('/login', req.url);
      url.searchParams.set('error', 'expired');
      url.searchParams.set('next', pathname + req.nextUrl.search);
      const res = NextResponse.redirect(url);
      res.cookies.set('auth_token', '', { maxAge: 0, path: '/' });
      return res;
    }

    // 当前已在登录页：仅当来源是私有路径时才显示过期提示
    if (pathname === '/login') {
      if (referrerIsPrivate) {
        const loginUrl = new URL('/login', req.url);
        loginUrl.searchParams.set('error', 'expired');
        const res = NextResponse.redirect(loginUrl);
        res.cookies.set('auth_token', '', { maxAge: 0, path: '/' });
        return res;
      }
      const res = NextResponse.next();
      res.cookies.set('auth_token', '', { maxAge: 0, path: '/' });
      return res;
    }

    // 公共路径访问：不显示过期提示，仅清除过期 token 后放行
    const res = NextResponse.next();
    res.cookies.set('auth_token', '', { maxAge: 0, path: '/' });
    return res;
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