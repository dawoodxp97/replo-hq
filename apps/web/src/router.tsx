import { useEffect } from 'react';
import { createRootRoute, createRoute, createRouter } from '@tanstack/react-router';
import { AppShell, Protected } from '@/components/AppShell';
import { useSession } from '@/hooks/useSession';
import { LoginPage, SignupPage } from '@/routes/login';
import { OAuthLandingPage } from '@/routes/oauth-landing';
import { GeneratePage } from '@/routes/generate';
import { GenerationPage } from '@/routes/generation';
import { LibraryPage } from '@/routes/library';
import { ExplorePage } from '@/routes/explore';
import { TutorialPlayerPage } from '@/routes/player';
import { SettingsPage } from '@/routes/settings';

const rootRoute = createRootRoute({
  component: () => <AppShell />,
});

const loginRoute = createRoute({ getParentRoute: () => rootRoute, path: '/login', component: LoginPage });
const signupRoute = createRoute({ getParentRoute: () => rootRoute, path: '/signup', component: SignupPage });
// The provider's redirect_uri lands here on the app origin.
const oauthLandingRoute = createRoute({ getParentRoute: () => rootRoute, path: '/api/user/oauth/$provider/callback', component: OAuthLandingPage });
const exploreRoute = createRoute({ getParentRoute: () => rootRoute, path: '/explore', component: ExplorePage });

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: function Home() {
    const { session } = useSession();
    useEffect(() => {
      void router.navigate({ to: session ? '/tutorials' : '/login', replace: true });
    }, [session]);
    return null;
  },
});

const libraryRoute = createRoute({ getParentRoute: () => rootRoute, path: '/tutorials', component: () => <Protected><LibraryPage /></Protected> });
const generateRoute = createRoute({ getParentRoute: () => rootRoute, path: '/generate', component: () => <Protected><GeneratePage /></Protected> });
const generationRoute = createRoute({ getParentRoute: () => rootRoute, path: '/generation/$instanceId', component: () => <Protected><GenerationPage /></Protected> });
const playerRoute = createRoute({ getParentRoute: () => rootRoute, path: '/tutorials/$tutorialId', component: () => <Protected><TutorialPlayerPage /></Protected> });
const settingsRoute = createRoute({ getParentRoute: () => rootRoute, path: '/settings', component: () => <Protected><SettingsPage /></Protected> });

const routeTree = rootRoute.addChildren([
  indexRoute, loginRoute, signupRoute, oauthLandingRoute, exploreRoute,
  libraryRoute, generateRoute, generationRoute, playerRoute, settingsRoute,
]);

export const router = createRouter({ routeTree });

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}
