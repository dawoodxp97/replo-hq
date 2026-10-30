import { useCallback, useSyncExternalStore } from 'react';
import {
  adoptSession,
  currentSession,
  dropSession,
  subscribeSession,
} from '@/lib/api';
import type { TokenWithUser } from '@replo/api-client';

/** The one auth-state hook. Components read the session; services change it. */
export function useSession(): { session: TokenWithUser | null; signIn: (t: TokenWithUser) => void; signOut: () => void } {
  const session = useSyncExternalStore(subscribeSession, currentSession, currentSession);
  const signIn = useCallback((t: TokenWithUser) => adoptSession(t), []);
  const signOut = useCallback(() => dropSession(), []);
  return { session, signIn, signOut };
}
