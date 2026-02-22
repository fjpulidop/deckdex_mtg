import { useState, useEffect } from 'react';
import { Menu, X } from 'lucide-react';
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
              href="#docs"
              className="text-slate-100 hover:text-white transition-colors"
            >
              Docs
            </a>
          </div>

          {/* Auth Buttons - Desktop */}
          <div className="hidden md:flex items-center gap-4">
            {isAuthenticated ? (
              <a
                href="/dashboard"
                className="px-4 py-2 rounded-lg bg-gradient-to-r from-primary-500 to-accent-500 text-white font-medium hover:shadow-lg hover:shadow-primary-500/50 transition-shadow"
              >
                Go to Dashboard
              </a>
            ) : (
              <>
                <a
                  href="/login"
                  className="px-4 py-2 text-white hover:text-slate-100 transition-colors"
                >
                  Login
                </a>
                <a
                  href="/login"
                  className="px-4 py-2 rounded-lg bg-gradient-to-r from-primary-500 to-accent-500 text-white font-medium hover:shadow-lg hover:shadow-primary-500/50 transition-shadow"
                >
                  Sign Up
                </a>
              </>
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
              href="#docs"
              className="block px-3 py-2 rounded-md text-slate-100 hover:text-white hover:bg-slate-700 transition-colors"
            >
              Docs
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
              <>
                <a
                  href="/login"
                  className="block px-3 py-2 rounded-md text-slate-100 hover:text-white hover:bg-slate-700 transition-colors"
                >
                  Login
                </a>
                <a
                  href="/login"
                  className="block px-3 py-2 rounded-md bg-gradient-to-r from-primary-500 to-accent-500 text-white font-medium"
                >
                  Sign Up
                </a>
              </>
            )}
          </div>
        </div>
      )}
    </nav>
  );
};
