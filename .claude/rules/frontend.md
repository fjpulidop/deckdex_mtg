---
paths:
  - "frontend/**"
---

# Frontend Conventions (React + TypeScript)

- All backend calls through `api/client.ts` + `useApi` hook. No raw `fetch` elsewhere.
- Functional components only; hooks for state and side effects. No class components.
- TypeScript strict — no `any`. Define proper types/interfaces for all data.
- Tailwind for styling; theme via `ThemeContext`. No inline style objects unless dynamic values require it.
- TanStack Query for all server state. Use `useQuery` for reads, `useMutation` for writes.
- WebSockets only for real-time job progress; all other data via REST.
- Components go in `frontend/src/components/`. Pages go in `frontend/src/pages/`.
- Hooks go in `frontend/src/hooks/`. Contexts go in `frontend/src/contexts/`.
