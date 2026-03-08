# Common Fixes

## Sprint 2026-03-08
- Bilingual card component causes `getByText` to find multiple elements: When a component renders the same translated text in both EN and ES panels (because `i18next.getFixedT('es')` falls back to English in the test environment), `screen.getByText(...)` throws "multiple elements found". Fixed by changing `getByText` to `getAllByText(...).length >= 1`. File: `frontend/src/pages/__tests__/Landing.test.tsx`.
