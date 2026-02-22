import { useRef, useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X } from 'lucide-react';
import { ThemeToggle } from './ThemeToggle';

export function Navbar() {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const isActive = (path: string) => location.pathname === path;

  // Close mobile menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setMobileMenuOpen(false);
      }
    }

    if (mobileMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [mobileMenuOpen]);

  // Close mobile menu on ESC key
  useEffect(() => {
    function handleEscKey(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setMobileMenuOpen(false);
      }
    }

    if (mobileMenuOpen) {
      document.addEventListener('keydown', handleEscKey);
      return () => document.removeEventListener('keydown', handleEscKey);
    }
  }, [mobileMenuOpen]);

  const navLinks = [
    { path: '/', label: 'Dashboard' },
    { path: '/decks', label: 'Decks', badge: 'alpha' },
    { path: '/analytics', label: 'Analytics', badge: 'beta' },
    { path: '/settings', label: 'Settings' },
  ];

  const LinkItem = ({ path, label, badge }: { path: string; label: string; badge?: string }) => {
    const active = isActive(path);
    return (
      <Link
        to={path}
        onClick={() => setMobileMenuOpen(false)}
        className={`flex items-center gap-1.5 pb-1 px-1 transition-all duration-200 ${
          active
            ? 'text-indigo-600 dark:text-indigo-400 font-semibold border-b-2 border-indigo-600 dark:border-indigo-400'
            : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
        }`}
      >
        {label}
        {badge && (
          <span className={`text-xs px-1.5 py-0.5 rounded-full ${
            badge === 'alpha'
              ? 'bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300'
              : 'bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-300'
          }`}>
            {badge}
          </span>
        )}
      </Link>
    );
  };

  return (
    <>
      {/* Desktop and Mobile Navbar */}
      <nav className="sticky top-0 z-40 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <Link
              to="/"
              className="text-2xl font-bold text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 transition-colors"
            >
              DeckDex
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center gap-8">
              {navLinks.map((link) => (
                <LinkItem key={link.path} path={link.path} label={link.label} badge={link.badge} />
              ))}
            </div>

            {/* Right side: Theme toggle and mobile menu button */}
            <div className="flex items-center gap-4">
              <ThemeToggle />
              
              {/* Mobile Menu Button */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="md:hidden p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
                aria-label="Toggle mobile menu"
                aria-expanded={mobileMenuOpen}
              >
                {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
              </button>
            </div>
          </div>

          {/* Mobile Menu Overlay */}
          {mobileMenuOpen && (
            <div
              ref={menuRef}
              className="md:hidden mt-4 pb-4 border-t border-gray-200 dark:border-gray-700 pt-4"
            >
              <div className="flex flex-col gap-2">
                {navLinks.map((link) => (
                  <div key={link.path} className="py-2">
                    <LinkItem path={link.path} label={link.label} badge={link.badge} />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </nav>

      {/* Mobile menu overlay backdrop (optional, for better UX) */}
      {mobileMenuOpen && (
        <div
          className="md:hidden fixed inset-0 bg-black/20 z-30 top-[calc(100%+4rem)]"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}
    </>
  );
}
