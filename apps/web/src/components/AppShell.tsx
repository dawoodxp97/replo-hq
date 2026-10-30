import { useEffect } from 'react';
import { Link, Outlet, useNavigate } from '@tanstack/react-router';
import { useSession } from '@/hooks/useSession';

function Header() {
  const { session, signOut } = useSession();
  const navigate = useNavigate();
  return (
    <header className="flex items-center justify-between border-b border-neutral-200 px-6 py-3">
      <Link to="/" className="text-lg font-semibold">Replo</Link>
      <nav className="flex items-center gap-4 text-sm">
        <Link to="/tutorials">Library</Link>
        <Link to="/explore">Explore</Link>
        <Link to="/generate">Generate</Link>
        {session ? (
          <>
            <Link to="/settings">Settings</Link>
            <button
              className="text-neutral-500 hover:text-neutral-900"
              onClick={() => {
                signOut();
                void navigate({ to: '/login' });
              }}

            >
              Sign out
            </button>
          </>
        ) : (
          <Link to="/login" className="font-medium">Sign in</Link>
        )}
      </nav>
    </header>
  );
}

export function AppShell() {
  return (
    <div className="min-h-screen bg-white text-neutral-900">
      <Header />
      <main className="mx-auto max-w-4xl px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}

export function Protected({ children }: { children: React.ReactNode }) {
  const { session } = useSession();
  const navigate = useNavigate();
  useEffect(() => {
    if (!session) void navigate({ to: '/login', replace: true });
  }, [session, navigate]);
  if (!session) return null;
  return <>{children}</>;
}
