# AGENTS.md — frontend

## Overview

Web dashboard for DeckDex MTG: React 19, TypeScript, Vite 7, Tailwind CSS. Talks to the backend API and WebSockets for job progress. Builds to static assets for production.

## Commands

| Task | Command | Notes |
|------|---------|-------|
| Install | `npm install` | From frontend/ |
| Dev server | `npm run dev` | Vite dev server |
| Build | `npm run build` | TypeScript check + Vite build |
| Lint | `npm run lint` | ESLint |
| Preview | `npm run preview` | Preview production build |

See root `AGENTS.md` for project-wide skills and workflow.

## File map

```
frontend/
  src/
    api/          → API client (client.ts)
    components/   → Reusable UI (CardTable, Filters, JobLogModal, etc.)
    contexts/     → ThemeContext
    hooks/        → useApi
    pages/        → Dashboard, Settings
    App.tsx       → Root component, routing
    main.tsx      → Entrypoint
  index.html      → HTML shell
  vite.config.ts  → Vite config
  package.json    → Scripts and dependencies
```

## Conventions

- Functional components and hooks; TypeScript strict.
- Use `useApi` and `api/client.ts` for backend calls; WebSockets for job progress where needed.
- Styling: Tailwind; theme via ThemeContext.
- Check root AGENTS.md for project-wide conventions and OpenSpec workflow.
