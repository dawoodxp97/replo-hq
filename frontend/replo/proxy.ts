import { NextResponse } from 'next/server';

export function proxy(request: import('next/server').NextRequest) {
  // 1. Get the token from the user's cookies
  const token = request.cookies.get('auth_token')?.value;
  const { pathname } = request.nextUrl;

  // Bypass middleware for well-known paths (Chrome DevTools, browser manifests, etc.)
  if (pathname.startsWith('/.well-known')) {
    return NextResponse.next();
  }

  // Define public paths that are accessible without a token
  const publicPaths = ['/login', '/register', '/.well-known'];

  // Check if the current path is one of the public paths
  const isPublicPath = publicPaths.some(path => pathname.startsWith(path));

  // RULE 2: If the user has a token and tries to access a public path...
  if (token && isPublicPath) {
    // ...redirect them to the dashboard.
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  // RULE 1: If the user does NOT have a token and is trying to access a private path...
  if (!token && !isPublicPath) {
    console.log("No token found, redirecting to login", pathname, isPublicPath, token, request);
    // ...redirect them to the login page.
    // return NextResponse.redirect(new URL('/login', request.url));
  }

  // If none of the above, allow the request to continue
  // return NextResponse.next();
}

// Config: Specifies which paths the middleware should run on.
// This avoids running it on static files or API routes.
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - .well-known (browser/devtools special paths)
     */
    '/((?!api|_next/static|_next/image|favicon.ico|\\.well-known).*)',
  ],
};