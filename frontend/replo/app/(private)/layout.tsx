'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';

import { useTokenRefresh } from '@/hooks/useTokenRefresh';
import { useGlobalStore } from '@/store/useGlobalStore';
import { getCurrentUser } from '@/services/authService';

import GenerateTutorialButton from '@/components/tutorial/GenerateTutorialButton';
import { Header } from '@/components/core/Header';
import { Sidebar } from '@/components/core/Sidebar';
import InitialLoader from '@/components/ui/loader/InitialLoader';

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

export default function PrivateLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { user, setUser, logout } = useGlobalStore();
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthorized, setIsAuthorized] = useState(false);
  const hasInitialized = useRef(false);

  // Automatically refresh tokens before they expire
  useTokenRefresh();

  useEffect(() => {
    // Prevent multiple initializations
    if (hasInitialized.current) return;

    const initializeUser = async () => {
      hasInitialized.current = true;

      try {
        // Check if we have a token
        const token = Cookies.get('auth_token');
        const refreshToken = Cookies.get('refresh_token');

        // If no tokens at all, redirect to login
        if (!token && !refreshToken) {
          router.push('/login');
          return;
        }

        // Check if token is expired
        const tokenExpired = isTokenExpired(token);
        const refreshTokenExpired = isTokenExpired(refreshToken);

        // If both tokens are expired, redirect to login
        if (tokenExpired && (!refreshToken || refreshTokenExpired)) {
          logout();
          router.push('/login?error=expired');
          return;
        }

        // Get current user from store (might be hydrated from persistence)
        const currentUser = useGlobalStore.getState().user;

        // If we already have user data, we're good
        if (currentUser && currentUser.email) {
          setIsAuthorized(true);
          setIsLoading(false);
          return;
        }

        // Try to fetch user data
        try {
          const userData = await getCurrentUser();
          if (userData && userData.email) {
            setUser(userData);
            setIsAuthorized(true);
          } else {
            // No valid user data, redirect to login
            logout();
            router.push('/login?error=expired');
            return;
          }
        } catch (error) {
          logout();
          router.push('/login?error=expired');
          return;
        }
      } catch (error) {
        logout();
        router.push('/login?error=expired');
      } finally {
        setIsLoading(false);
      }
    };

    // Small delay to allow zustand persist to hydrate
    const timer = setTimeout(() => {
      initializeUser();
    }, 0);

    return () => clearTimeout(timer);
  }, []); // Only run once on mount

  // Show loader while checking authorization and loading user
  if (isLoading || !isAuthorized) {
    return <InitialLoader message="Loading your workspace..." />;
  }

  return (
    <div className="app-private-root flex flex-col h-screen bg-[var(--background-soft)]">
      <Header />
      <div className="private-grid flex flex-1">
        <Sidebar />
        <main className="flex-1 shadow-md bg-[#FBFCFF]">{children}</main>
      </div>

      <GenerateTutorialButton />
    </div>
  );
}
