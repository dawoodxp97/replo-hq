import { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from '@tanstack/react-router';
import { oauthComplete } from '@/services/auth';
import { adoptSession } from '@/lib/api';
import { ErrorState, Loading } from '@/components/states';
import type { OAuthProvider } from '@replo/api-client';

/**
 * The provider's redirect target. The authorize URL's redirect_uri is
 * `<app-origin>/api/user/oauth/:provider/callback`, so this route owns that
 * path on the app origin: it takes code+state from the query string and
 * exchanges them through the API's JSON callback endpoint.
 */
export function OAuthLandingPage() {
  const navigate = useNavigate();
  const { provider = '' } = useParams({ strict: false }) as { provider?: string };
  const [error, setError] = useState<unknown>(null);
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const state = params.get('state');
    if (!provider || !code || !state) {
      setError(new Error('Missing OAuth callback parameters'));
      return;
    }
    void oauthComplete(provider as OAuthProvider, { code, state })
      .then((session) => {
        adoptSession(session);
        void navigate({ to: '/tutorials', replace: true });
      })
      .catch(setError);
  }, [navigate, provider]);

  if (error) return <ErrorState error={error} />;
  return <Loading label="Completing sign-in…" />;
}
