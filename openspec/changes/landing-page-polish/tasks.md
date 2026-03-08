# Tasks: Landing Page Polish

Ordered implementation tasks. All tasks are in the Frontend layer. Execute in sequence — the test task depends on the BentoCard prop change being complete so types are resolvable.

---

## Task 1: Add `iconColor` prop to `BentoCard`

**File:** `frontend/src/components/landing/BentoCard.tsx`

**What to do:**

1. Add `iconColor?: string` to the `BentoCardProps` interface (after `illustrationIcon?: ReactNode`).

2. Destructure `iconColor` from the component props alongside the existing props.

3. In the illustration section (lines 72–79), find the inner wrapper `<div>` that holds the `illustrationIcon`. Its current className is:
   ```
   "relative text-white/20 group-hover:text-white/30 transition-colors duration-300"
   ```
   Replace it with a dynamic class that uses `iconColor` when provided, falling back to a more visible default:
   ```tsx
   className={`relative transition-colors duration-300 ${iconColor ?? 'text-white/40 group-hover:text-white/60'}`}
   ```

**Acceptance criteria:**
- `BentoCardProps` includes `iconColor?: string`
- The illustration icon wrapper uses the `iconColor` class when provided
- When `iconColor` is omitted, the fallback produces `text-white/40` at rest and `text-white/60` on hover
- TypeScript compiles without errors (`npm run build` or `npm run lint` passes)
- No raw dimension text (strings matching `\d+x\d+px`) exists anywhere in this file

---

## Task 2: Pass per-card `iconColor` in `BentoGrid`

**File:** `frontend/src/components/landing/BentoGrid.tsx`

**What to do:**

Add the `iconColor` prop to each `BentoCard` usage in the grid. The color family is derived from the existing `gradientFrom` values already on each card:

| `BentoCard` (by title key) | `gradientFrom` | `iconColor` to add |
|---|---|---|
| `bento.cards.collection.title` | `from-blue-500/20` | `"text-blue-400/60 group-hover:text-blue-300/80"` |
| `bento.cards.deckBuilder.title` | `from-purple-500/20` | `"text-purple-400/60 group-hover:text-purple-300/80"` |
| `bento.cards.aiInsights.title` | `from-pink-500/20` | `"text-pink-400/60 group-hover:text-pink-300/80"` |
| `bento.cards.realtime.title` | `from-amber-500/20` | `"text-amber-400/60 group-hover:text-amber-300/80"` |
| `bento.cards.priceTracking.title` | `from-green-500/20` | `"text-green-400/60 group-hover:text-green-300/80"` |

Each card currently has a `<BentoCard ... />` JSX element. Add `iconColor="text-<color>-400/60 group-hover:text-<color>-300/80"` as a new prop on each.

**Example — Collection card after change:**
```tsx
<BentoCard
  size="large"
  title={t('bento.cards.collection.title')}
  description={t('bento.cards.collection.desc')}
  icon={<Zap className="h-6 w-6" />}
  gradientFrom="from-blue-500/20"
  gradientTo="to-blue-600/20"
  illustrationIcon={<LayoutGrid className="h-20 w-20" strokeWidth={1} />}
  iconColor="text-blue-400/60 group-hover:text-blue-300/80"
/>
```

Apply the same pattern to all 5 cards.

**Acceptance criteria:**
- All 5 BentoCard instances in `BentoGrid.tsx` have an `iconColor` prop
- Each `iconColor` value uses a color matching the card's gradient family
- TypeScript compiles without errors
- No raw dimension text exists anywhere in this file

---

## Task 3: Create `Landing.test.tsx` with hero fallback and footer tests

**File:** `frontend/src/pages/__tests__/Landing.test.tsx` (create new file)

**What to do:**

Create a new test file at `frontend/src/pages/__tests__/Landing.test.tsx`. This file tests two independent concerns in separate `describe` blocks.

### Mocks required (top of file, before any describe blocks):

```ts
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(() => ({
    user: null,
    isAuthenticated: false,
    isLoading: false,
    logout: vi.fn(),
    refreshUser: vi.fn(),
  })),
}));

vi.mock('@/utils/auth', () => ({
  redirectToGoogleLogin: vi.fn(),
}));
```

These mocks apply globally to the file. Individual tests that need `isAuthenticated: true` must call `vi.mocked(useAuth).mockReturnValue({ ... isAuthenticated: true ... })` inside that test's `beforeEach` or at the start of the test.

Import `useAuth` from `@/contexts/AuthContext` at the top of the file so it can be accessed via `vi.mocked(useAuth)`.

### Suite 1: Hero image fallback

```ts
describe('Hero image fallback', () => {
  it('renders the hero image initially', () => {
    render(
      <MemoryRouter>
        <Hero />
      </MemoryRouter>
    );
    const img = screen.getByAltText('DeckDex dashboard preview');
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute('src', '/dashboard-preview.png');
  });

  it('hides the image and shows fallback on error', () => {
    render(
      <MemoryRouter>
        <Hero />
      </MemoryRouter>
    );
    const img = screen.getByAltText('DeckDex dashboard preview');
    fireEvent.error(img);
    expect(img.style.display).toBe('none');
    // The fallback is the img's next sibling div
    const fallback = img.nextElementSibling as HTMLElement;
    expect(fallback).not.toBeNull();
    expect(fallback.style.display).toBe('flex');
  });
});
```

**Key detail:** `fireEvent.error(img)` triggers React's synthetic `onError` handler synchronously. No `waitFor` needed.

**Key detail:** The fallback `div` is identified as `img.nextElementSibling`. This is the correct stable selector because the Hero renders `<img>` immediately followed by the fallback `<div>` as siblings inside the container.

### Suite 2: Footer rendering

```ts
describe('Footer rendering', () => {
  describe('when unauthenticated', () => {
    it('renders the footer element', () => {
      render(<MemoryRouter><Footer /></MemoryRouter>);
      expect(screen.getByRole('contentinfo')).toBeInTheDocument();
    });

    it('renders the copyright notice with the current year', () => {
      render(<MemoryRouter><Footer /></MemoryRouter>);
      const year = new Date().getFullYear().toString();
      expect(screen.getByText(new RegExp(year))).toBeInTheDocument();
    });

    it('renders GitHub, Twitter, and Discord social links', () => {
      render(<MemoryRouter><Footer /></MemoryRouter>);
      expect(screen.getByRole('link', { name: /github/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /twitter/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /discord/i })).toBeInTheDocument();
    });
  });

  describe('when authenticated', () => {
    beforeEach(() => {
      vi.mocked(useAuth).mockReturnValue({
        user: { id: 1, email: 'test@example.com', display_name: 'Test User' },
        isAuthenticated: true,
        isLoading: false,
        logout: vi.fn(),
        refreshUser: vi.fn(),
      });
    });

    it('renders the footer element', () => {
      render(<MemoryRouter><Footer /></MemoryRouter>);
      expect(screen.getByRole('contentinfo')).toBeInTheDocument();
    });

    it('renders the copyright notice with the current year', () => {
      render(<MemoryRouter><Footer /></MemoryRouter>);
      const year = new Date().getFullYear().toString();
      expect(screen.getByText(new RegExp(year))).toBeInTheDocument();
    });

    it('renders GitHub, Twitter, and Discord social links', () => {
      render(<MemoryRouter><Footer /></MemoryRouter>);
      expect(screen.getByRole('link', { name: /github/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /twitter/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /discord/i })).toBeInTheDocument();
    });
  });
});
```

### Required imports at top of file:

```ts
import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { Hero } from '@/components/landing/Hero';
import { Footer } from '@/components/landing/Footer';
import { useAuth } from '@/contexts/AuthContext';
```

### Fixture scope

All fixtures use `scope="function"` (the default in Vitest). Do NOT use `scope="module"` for any mock that involves `vi.mocked(...).mockReturnValue(...)` — this causes cross-test pollution (a known project-wide pitfall documented in MEMORY.md).

**Acceptance criteria:**
- File is created at `frontend/src/pages/__tests__/Landing.test.tsx`
- All 8 tests pass when running `npm test` (or `npx vitest run`)
- No test uses `scope="module"` on fixtures with mocked dependencies
- The hero fallback test does not use `waitFor` (the handler is synchronous)
- The footer tests work in both auth states and make assertions against the `contentinfo` role, copyright year, and social link aria-labels
- All previously passing tests continue to pass (zero regressions)

---

## Verification checklist

After implementing all three tasks:

- [ ] `npm run lint` passes with no new errors
- [ ] `npm run build` completes with no TypeScript errors
- [ ] `npx vitest run` shows all tests green including the 8 new Landing tests
- [ ] Visual check: open the landing page in dev mode; BentoCard illustration icons are visibly colored (blue, purple, pink, amber, green) and not near-invisible
- [ ] Visual check: no raw dimension strings ("600x500px" etc.) appear on the page
