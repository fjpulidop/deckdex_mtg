import { render } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { Hero } from '@/components/landing/Hero';
import { BentoGrid } from '@/components/landing/BentoGrid';
import { FinalCTA } from '@/components/landing/FinalCTA';
import { LandingNavbar } from '@/components/landing/LandingNavbar';

// ---------------------------------------------------------------------------
// Shared mocks
// ---------------------------------------------------------------------------
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

// LanguageSwitcher depends on i18n internals not relevant to theme tests
vi.mock('@/components/LanguageSwitcher', () => ({
  LanguageSwitcher: () => <div data-testid="language-switcher" />,
}));

// framer-motion: skip animations so elements render synchronously in jsdom
vi.mock('framer-motion', () => ({
  motion: new Proxy(
    {},
    {
      get: (_target, tag: string) =>
        ({ children, ...rest }: React.HTMLAttributes<HTMLElement> & { children?: React.ReactNode }) => {
          const Tag = tag as React.ElementType;
          return <Tag {...rest}>{children}</Tag>;
        },
    },
  ),
}));

beforeEach(() => {
  vi.clearAllMocks();
});

// ---------------------------------------------------------------------------
// Hero — transparent gradient (reveals CardMatrix canvas behind)
// ---------------------------------------------------------------------------
describe('Hero Dracula theme', () => {
  it('renders the section with bg-gradient-to-b class', () => {
    const { container } = render(
      <MemoryRouter>
        <Hero />
      </MemoryRouter>,
    );
    const section = container.querySelector('section');
    expect(section).not.toBeNull();
    expect(section!.className).toContain('bg-gradient-to-b');
  });

  it('uses from-dracula-bg/20 via-transparent to-transparent gradient stops', () => {
    const { container } = render(
      <MemoryRouter>
        <Hero />
      </MemoryRouter>,
    );
    const section = container.querySelector('section');
    expect(section!.className).toContain('from-dracula-bg/20');
    expect(section!.className).toContain('via-transparent');
    expect(section!.className).toContain('to-transparent');
  });

  it('does not use solid bg-dracula-bg (no transparency) on the section', () => {
    const { container } = render(
      <MemoryRouter>
        <Hero />
      </MemoryRouter>,
    );
    const section = container.querySelector('section');
    // The section must not carry the opaque solid background — it should be
    // transparent so the CardMatrix canvas behind it remains visible.
    // "bg-dracula-bg " (trailing space) avoids a false match on "bg-dracula-bg/20".
    expect(section!.className).not.toContain('bg-dracula-bg ');
    expect(section!.className).not.toMatch(/\bbg-dracula-bg\b(?!\/)/);
  });
});

// ---------------------------------------------------------------------------
// BentoGrid — bg-dracula-current/20
// ---------------------------------------------------------------------------
describe('BentoGrid Dracula theme', () => {
  it('renders the section with bg-dracula-current/20 class', () => {
    const { container } = render(
      <MemoryRouter>
        <BentoGrid />
      </MemoryRouter>,
    );
    const section = container.querySelector('section');
    expect(section).not.toBeNull();
    expect(section!.className).toContain('bg-dracula-current/20');
  });

  it('does not use the old semi-transparent gradient from-dracula-bg/80', () => {
    const { container } = render(
      <MemoryRouter>
        <BentoGrid />
      </MemoryRouter>,
    );
    const section = container.querySelector('section');
    expect(section!.className).not.toContain('from-dracula-bg/80');
    expect(section!.className).not.toContain('to-dracula-bg/80');
  });
});

// ---------------------------------------------------------------------------
// FinalCTA — bg-gradient-to-r from-dracula-bg via-dracula-purple/20 to-dracula-bg
// ---------------------------------------------------------------------------
describe('FinalCTA Dracula theme', () => {
  it('renders the section with bg-gradient-to-r class', () => {
    const { container } = render(
      <MemoryRouter>
        <FinalCTA />
      </MemoryRouter>,
    );
    const section = container.querySelector('section');
    expect(section).not.toBeNull();
    expect(section!.className).toContain('bg-gradient-to-r');
  });

  it('uses from-dracula-bg as the solid gradient start endpoint', () => {
    const { container } = render(
      <MemoryRouter>
        <FinalCTA />
      </MemoryRouter>,
    );
    const section = container.querySelector('section');
    expect(section!.className).toContain('from-dracula-bg');
  });

  it('uses via-dracula-purple/20 as the gradient midpoint', () => {
    const { container } = render(
      <MemoryRouter>
        <FinalCTA />
      </MemoryRouter>,
    );
    const section = container.querySelector('section');
    expect(section!.className).toContain('via-dracula-purple/20');
  });

  it('uses to-dracula-bg as the solid gradient end endpoint', () => {
    const { container } = render(
      <MemoryRouter>
        <FinalCTA />
      </MemoryRouter>,
    );
    const section = container.querySelector('section');
    expect(section!.className).toContain('to-dracula-bg');
  });

  it('uses from-dracula-bg/80 and to-dracula-bg/80 (80% opacity) for partial transparency', () => {
    const { container } = render(
      <MemoryRouter>
        <FinalCTA />
      </MemoryRouter>,
    );
    const section = container.querySelector('section');
    // Pinning the /80 opacity suffix ensures the gradient retains the
    // semi-transparent look introduced in this fix — a fully opaque
    // "from-dracula-bg" would also satisfy the substring check above but
    // would break the visual design.
    expect(section!.className).toContain('from-dracula-bg/80');
    expect(section!.className).toContain('to-dracula-bg/80');
  });
});

// ---------------------------------------------------------------------------
// LandingNavbar — renders the nav element
// ---------------------------------------------------------------------------
describe('LandingNavbar', () => {
  it('renders a nav landmark', () => {
    const { container } = render(
      <MemoryRouter>
        <LandingNavbar />
      </MemoryRouter>,
    );
    const nav = container.querySelector('nav');
    expect(nav).not.toBeNull();
  });

  it('renders the DeckDex logo button', () => {
    const { getByText } = render(
      <MemoryRouter>
        <LandingNavbar />
      </MemoryRouter>,
    );
    expect(getByText('DeckDex')).toBeInTheDocument();
  });
});
