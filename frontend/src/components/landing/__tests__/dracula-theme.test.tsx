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
// Hero — bg-dracula-bg
// ---------------------------------------------------------------------------
describe('Hero Dracula theme', () => {
  it('renders the section with bg-dracula-bg class', () => {
    const { container } = render(
      <MemoryRouter>
        <Hero />
      </MemoryRouter>,
    );
    const section = container.querySelector('section');
    expect(section).not.toBeNull();
    expect(section!.className).toContain('bg-dracula-bg');
  });

  it('does not use the old gradient pattern from-dracula-bg/20 via-dracula-purple/10', () => {
    const { container } = render(
      <MemoryRouter>
        <Hero />
      </MemoryRouter>,
    );
    const section = container.querySelector('section');
    expect(section!.className).not.toContain('from-dracula-bg/20');
    expect(section!.className).not.toContain('via-dracula-purple/10');
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
