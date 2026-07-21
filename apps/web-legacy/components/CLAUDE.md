# components/

Five competing organizational schemes coexist here. Pick one before adding more.

| Dir | Intent | Reality |
|-----|--------|---------|
| `ui/` | Primitives | `button/Button.jsx` (untyped), `input/Input.tsx` (596 LOC), `loader/`, `error/`, `empty-state/`, `tabs/`. Not a design system — these are big bespoke components, not primitives. |
| `features/` | Feature modules | The real app: `dashboard/`, `tutorial/`, `settings/`, `progress/`, `search/`, `repo/`, `my-tutorials/`, `authoring/`, `figma/`. |
| `core/` | App chrome | `Header`, `Sidebar`, `AntdStyledComponentsRegistry`. |
| `layout/` | App chrome (again) | `Navbar.jsx`, `Sidebar.tsx` — **duplicates `core/`**. |
| `author/` | Authoring editors | `TutorialEditor` (661), `QuizEditor`, `ModuleEditor` — **overlaps `features/authoring/`**. |
| `landing/` | Marketing page sections | Hero, Nav, FeaturesGrid, Testimonials, DemoSplit, CTA, Footer. Self-contained, fine. |
| `shared/`, `common/`, `modals/`, `tutorial/` | One-offs | `common/notification/Notification.tsx` is 531 LOC. |

## Notable components

- `features/tutorial/TutorialPlayer.tsx` (498) — the core reading experience.
- `features/tutorial/CodeSandbox.tsx` — Sandpack embed.
- `features/tutorial/MarkdownRenderer.tsx` (285) — hand-rolled; no `react-markdown` dep,
  worth checking how it sanitizes LLM-generated HTML.
- `features/tutorial/DiagramViewer.jsx` — mermaid renderer, untyped.
- `shared/tutorial-generating-ui/` — the polling progress UI.

## Conventions

Mostly `'use client'`. Tailwind classes inline, with some `var(--...)` CSS custom
properties for theming (`bg-[var(--background-soft)]`, hardcoded hexes like `#FBFCFF`
appear alongside them). `class-variance-authority` + `tailwind-merge` are installed but
inconsistently applied.

## Rules for new work

1. New feature UI goes in `features/<domain>/`.
2. Do not add to `core/` **or** `layout/` until they are merged.
3. New files are `.tsx`, never `.jsx`.
4. Anything over ~250 LOC should be split before it lands.
