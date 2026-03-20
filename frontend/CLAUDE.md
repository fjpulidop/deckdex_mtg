# frontend/

React 19 dashboard. TypeScript strict. REST via TanStack Query + WebSockets for real-time job progress.

## Commands

| Task    | Command           |
|---------|-------------------|
| Install | `npm install`     |
| Dev     | `npm run dev`     |
| Build   | `npm run build`   |
| Lint    | `npm run lint`    |
| Preview | `npm run preview` |

## File map

```
frontend/src/
  api/
    client.ts         → Typed API client (all backend calls)
  components/         → CardTable, Filters, JobLogModal, ActiveJobs...
  contexts/           → ThemeContext
  hooks/              → useApi
  pages/              → Dashboard, Settings
  App.tsx             → Root component, routing
  main.tsx            → Entrypoint
```

## Conventions

- All backend calls through `api/client.ts` + `useApi` hook. No raw `fetch` elsewhere.
- Functional components only; hooks for state and side effects.
- Tailwind v4 for styling; theme from `ThemeContext`. Custom color tokens (Dracula, primary, accent) are declared in `src/index.css` inside the `@theme { }` block — `tailwind.config.js` is inert under v4.
- TypeScript strict — no `any`.
- WebSockets only for real-time job progress; all other data via REST.
