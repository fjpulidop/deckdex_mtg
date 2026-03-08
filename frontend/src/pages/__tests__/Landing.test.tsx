import { render, screen, fireEvent } from '@testing-library/react';
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
