import { useState, useEffect } from 'react';
import { Menu, X, Github } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

export const LandingNavbar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [hasScrolled, setHasScrolled] = useState(false);
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    const handleScroll = () => {
      setHasScrolled(window.scrollY > 10);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleSmoothScroll = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
      setIsOpen(false);
    }
  };

  const handleGoogleLogin = () => {
    window.location.href = 'http://localhost:8000/api/auth/google';
  };

  const handleLogoClick = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <nav
      className={`fixed top-0 w-full z-50 transition-all duration-300 ${
        hasScrolled
          ? 'bg-slate-950/80 backdrop-blur-md border-b border-slate-700/50'
          : 'bg-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex-shrink-0">
            <button
              onClick={handleLogoClick}
              className="text-2xl font-bold bg-gradient-to-r from-primary-400 to-accent-500 bg-clip-text text-transparent hover:opacity-80 transition-opacity"
            >
              DeckDex
            </button>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-8">
            <button
              onClick={() => handleSmoothScroll('features')}
              className="text-slate-100 hover:text-white transition-colors"
            >
              Features
            </button>
            <a
              href="https://github.com/yourusername/deckdex-mtg"
              target="_blank"
              rel="noopener noreferrer"
              className="text-slate-100 hover:text-white transition-colors flex items-center gap-2"
            >
              <Github className="h-5 w-5" />
              <span>Source Code</span>
            </a>
          </div>

          {/* Auth Button - Desktop */}
          <div className="hidden md:flex items-center gap-4">
            {isAuthenticated ? (
              <a
                href="/dashboard"
                className="px-4 py-2 rounded-lg bg-gradient-to-r from-primary-500 to-accent-500 text-white font-medium hover:shadow-lg hover:shadow-primary-500/50 transition-shadow"
              >
                Go to Dashboard
              </a>
            ) : (
              <button
                onClick={handleGoogleLogin}
                className="px-4 py-2 rounded-lg bg-gradient-to-r from-primary-500 to-accent-500 text-white font-medium hover:shadow-lg hover:shadow-primary-500/50 transition-shadow flex items-center gap-2"
              >
                <svg
                  className="w-4 h-4"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="white" />
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="white" />
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="white" />
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="white" />
                </svg>
                Sign in
              </button>
            )}
          </div>

          {/* Mobile Menu Button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="inline-flex items-center justify-center p-2 rounded-md text-slate-100 hover:text-white hover:bg-slate-700 focus:outline-none"
            >
              {isOpen ? (
                <X className="h-6 w-6" />
              ) : (
                <Menu className="h-6 w-6" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      {isOpen && (
        <div className="md:hidden bg-slate-950/95 backdrop-blur-md border-b border-slate-700/50">
          <div className="px-2 pt-2 pb-3 space-y-1">
            <button
              onClick={() => handleSmoothScroll('features')}
              className="block w-full text-left px-3 py-2 rounded-md text-slate-100 hover:text-white hover:bg-slate-700 transition-colors"
            >
              Features
            </button>
            <a
              href="https://github.com/yourusername/deckdex-mtg"
              target="_blank"
              rel="noopener noreferrer"
              className="block px-3 py-2 rounded-md text-slate-100 hover:text-white hover:bg-slate-700 transition-colors flex items-center gap-2"
            >
              <Github className="h-5 w-5" />
              <span>Source Code</span>
            </a>
            <hr className="border-slate-700 my-2" />
            {isAuthenticated ? (
              <a
                href="/dashboard"
                className="block px-3 py-2 rounded-md bg-gradient-to-r from-primary-500 to-accent-500 text-white font-medium"
              >
                Go to Dashboard
              </a>
            ) : (
              <button
                onClick={() => {
                  handleGoogleLogin();
                  setIsOpen(false);
                }}
                className="block w-full text-left px-3 py-2 rounded-md bg-gradient-to-r from-primary-500 to-accent-500 text-white font-medium flex items-center gap-2"
              >
                <svg
                  className="w-4 h-4"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="white" />
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="white" />
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="white" />
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="white" />
                </svg>
                Sign in
              </button>
            )}
          </div>
        </div>
      )}
    </nav>
  );
};
