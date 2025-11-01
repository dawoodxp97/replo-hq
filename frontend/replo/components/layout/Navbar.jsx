// ./frontend/src/components/layout/Navbar.jsx
'use client';

import { useGlobalStore } from '@/store/useGlobalStore';
import { useTheme } from '@/providers/theme/ThemeProvider';
import Link from 'next/link';

export default function Navbar() {
  // 1. Get the state and actions you need from the store
  const { isAuthenticated, user, logout, toggleSidebar } = useGlobalStore();
  const { theme, setTheme, isDark } = useTheme();

  return (
    <nav
      className={`flex items-center justify-between p-4 ${
        isDark ? 'bg-[var(--background-soft)]' : 'bg-[var(--background-soft)]'
      } shadow-sm border-b-[#ececec] border-b border-solid`}
    >
      <div className="flex items-center gap-4">
        <button onClick={toggleSidebar} className="p-1">
          {/* A simple hamburger icon */}
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-6 w-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 6h16M4 12h16m-7 6h7"
            />
          </svg>
        </button>
        <Link href="/dashboard" className="text-xl font-bold">
          AI Tutorials
        </Link>
      </div>

      <div className="flex items-center gap-4">
        {isAuthenticated ? (
          <>
            <span>Welcome, {user.username}</span>
            <button onClick={logout} className="px-4 py-2 bg-red-600 rounded">
              Logout
            </button>
          </>
        ) : (
          <Link href="/login" className="px-4 py-2 bg-blue-600 rounded">
            Login
          </Link>
        )}
      </div>
    </nav>
  );
}
