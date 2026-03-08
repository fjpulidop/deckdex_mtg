import { render, screen } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { Hero } from '@/components/landing/Hero';
import { Footer } from '@/components/landing/Footer';
import { useAuth } from '@/contexts/AuthContext';

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

describe('Hero bilingual description card', () => {
  it('renders EN and ES language labels', () => {
    render(
      <MemoryRouter>
        <Hero />
      </MemoryRouter>
    );
    expect(screen.getByText('EN')).toBeInTheDocument();
    expect(screen.getByText('ES')).toBeInTheDocument();
  });

  it('renders the English description card title', () => {
    render(
      <MemoryRouter>
        <Hero />
      </MemoryRouter>
    );
    // The bilingual card renders the title in both EN and ES panels;
    // in the test environment both may resolve to the same English text.
    expect(screen.getAllByText('What is DeckDex?').length).toBeGreaterThanOrEqual(1);
  });
});

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
