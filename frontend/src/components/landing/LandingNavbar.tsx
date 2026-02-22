import { useState, useEffect } from 'react';
import { Menu, X, Github, Sparkles } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

export const LandingNavbar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [hasScrolled, setHasScrolled] = useState(false);
  const [showGithubModal, setShowGithubModal] = useState(false);
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
              className="text-slate-100 hover:text-white transition-colors flex items-center gap-2"
            >
              <Sparkles className="h-5 w-5" />
              <span>Features</span>
            </button>
            <button
              onClick={() => setShowGithubModal(true)}
              className="text-slate-100 hover:text-white transition-colors flex items-center gap-2"
            >
              <Github className="h-5 w-5" />
              <span>Source Code</span>
            </button>
          </div>

          {/* Auth Button - Desktop */}
          {/* Removed Go to Dashboard button - redundant with Hero and Final CTA sections */}

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
              className="block w-full text-left px-3 py-2 rounded-md text-slate-100 hover:text-white hover:bg-slate-700 transition-colors flex items-center gap-2"
            >
              <Sparkles className="h-5 w-5" />
              <span>Features</span>
            </button>
            <button
              onClick={() => {
                setShowGithubModal(true);
                setIsOpen(false);
              }}
              className="block w-full text-left px-3 py-2 rounded-md text-slate-100 hover:text-white hover:bg-slate-700 transition-colors flex items-center gap-2"
            >
              <Github className="h-5 w-5" />
              <span>Source Code</span>
            </button>
          </div>
        </div>
      )}

      {/* GitHub Modal */}
      {showGithubModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={() => setShowGithubModal(false)}
          />
          <div className="relative bg-slate-900 rounded-lg border border-slate-700 p-8 max-w-md w-full shadow-xl">
            <button
              onClick={() => setShowGithubModal(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white"
            >
              <X className="h-6 w-6" />
            </button>
            <div className="flex items-center gap-3 mb-4">
              <Github className="h-8 w-8 text-white" />
              <h3 className="text-2xl font-bold text-white">DeckDex MTG</h3>
            </div>
            <p className="text-slate-300 mb-6">
              Check out the source code on GitHub. We welcome contributions, forks, and community improvements!
            </p>
            <a
              href="https://github.com/fjpulidop/deckdex_mtg"
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => setShowGithubModal(false)}
              className="inline-flex items-center justify-center w-full px-6 py-3 rounded-lg bg-gradient-to-r from-primary-500 to-accent-500 text-white font-semibold hover:shadow-lg hover:shadow-primary-500/50 transition-all duration-300 hover:scale-105"
            >
              <Github className="h-5 w-5 mr-2" />
              Open GitHub Repository
            </a>
          </div>
        </div>
      )}
    </nav>
  );
};
