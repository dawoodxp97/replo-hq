# frontend/replo/ — Next.js 16 App Router

~14.3k LOC TS/TSX. React 19, Tailwind v4, TypeScript strict-ish.

## Stack

Next 16 · React 19 · Zustand (auth) · TanStack Query (mounted, barely used) · axios ·
Ant Design 5 **and** Radix **and** lucide + custom UI dir (three overlapping UI systems) ·
framer-motion · Monaco + Sandpack (code editing) · mermaid (diagrams) · recharts · zod
(installed, almost unused) · sonner.

## Route groups

```
app/(public)/    /  /login  /signup  /demo/input
app/(private)/   /dashboard /my-tutorials /settings /progress /authoring
                 /repo  /repo/[repoId]  /tutorial/[tutorialId]
                 /tutorial/[tutorialId]/quiz/[quizId]  /edit/[tutorialId]
app/api/subscribe/route.ts   — the only route handler
```

Every page is a thin shell that renders one big client component from `components/features/`.
**Almost everything is `'use client'`** — Server Components, streaming, and server-side data
fetching are unused. `middleware.ts` is the only server-side logic.

## Directories

| Path | Role |
|------|------|
| `lib/apiClient.ts` | axios instance, bearer injection from cookie, 401 refresh queue. Unwraps `response.data` in the interceptor — so every call site's TS type is a lie and gets `as unknown as T` casts. |
| `lib/auth.ts` | Two helpers; `getUserFromToken` is a stub that returns `null`. |
| `services/*.ts` | Per-domain API wrappers. Thin, consistent — the healthiest layer. |
| `store/useGlobalStore.ts` | Zustand + persist. Holds user + isAuthenticated; tokens live in cookies. |
| `hooks/` | `useTokenRefresh`, `useUrlLocation` (385 LOC — oversized for a hook). |
| `constants/apiEndpoints.ts` | Endpoint registry + `BASE_URL`. |
| `components/` | See `components/CLAUDE.md`. |
| `providers/` | react-query + theme providers. |

## Auth flow — the biggest tangle

JWT expiry is decoded by hand (base64 → atob → JSON) in **three** places:
`middleware.ts` (twice, `isTokenExpired` and `isRefreshTokenExpired` are byte-identical),
`app/(private)/layout.tsx`, and `hooks/useTokenRefresh.ts`.

Tokens are in **JS-readable cookies** (`js-cookie`, not httpOnly) — any XSS exfiltrates the
session. `sameSite: 'strict'` and `secure` in prod are set, which helps CSRF but not XSS.

Auth is enforced in two layers that can disagree: `middleware.ts` (matcher-based, cookie
inspection) and `(private)/layout.tsx` (client-side effect that redirects and shows
`InitialLoader`). The layout's `useEffect` has `[]` deps with a `hasInitialized` ref guard
and a `setTimeout(0)` to wait for Zustand hydration — fragile.

`getCurrentUser()` fakes a user object from the **settings** endpoint and leaves
`id: undefined`. There is no `/api/user/me`.

## Duplication to clean up

- `components/core/{Header,Sidebar}` vs `components/layout/{Navbar,Sidebar}` — Navbar is `.jsx`.
- `components/author/*` vs `components/features/authoring/*`.
- `.jsx` files mixed into a TS codebase: `Navbar.jsx`, `Button.jsx`, `DiagramViewer.jsx`.
- Oversized components: `TutorialEditor` 661, `ProgressTracker` 643, `ProfileSettings` 615,
  `Input` 596, `EmptyState` 581, `Notification` 531, `Dashboard` 518.

## Missing for SaaS

No error boundaries, no test setup at all, no analytics, no loading/error conventions,
no design tokens beyond a few CSS vars, no a11y pass, no i18n. `next.config.js` is minimal.
Generation status is fetched by **polling**, not SSE/websocket.
