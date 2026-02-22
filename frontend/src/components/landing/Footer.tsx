import { Github, Twitter, MessageCircle } from 'lucide-react';

export const Footer = () => {
  return (
    <footer className="bg-slate-950 border-t border-slate-800 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto py-12 md:py-16">
        {/* Footer Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 md:gap-12 mb-8">
          {/* Product Column */}
          <div>
            <h3 className="text-white font-semibold text-sm uppercase tracking-wider mb-4">
              Product
            </h3>
            <ul className="space-y-3">
              <li>
                <a href="#" className="text-slate-400 hover:text-white transition-colors text-sm">
                  Features
                </a>
              </li>
              <li>
                <a href="#" className="text-slate-400 hover:text-white transition-colors text-sm">
                  Pricing
                </a>
              </li>
              <li>
                <a href="#" className="text-slate-400 hover:text-white transition-colors text-sm">
                  Roadmap
                </a>
              </li>
              <li>
                <a href="#" className="text-slate-400 hover:text-white transition-colors text-sm">
                  Changelog
                </a>
              </li>
            </ul>
          </div>

          {/* Company Column */}
          <div>
            <h3 className="text-white font-semibold text-sm uppercase tracking-wider mb-4">
              Company
            </h3>
            <ul className="space-y-3">
              <li>
                <a href="#" className="text-slate-400 hover:text-white transition-colors text-sm">
                  About
                </a>
              </li>
              <li>
                <a href="#" className="text-slate-400 hover:text-white transition-colors text-sm">
                  Blog
                </a>
              </li>
              <li>
                <a href="#" className="text-slate-400 hover:text-white transition-colors text-sm">
                  Careers
                </a>
              </li>
              <li>
                <a href="#" className="text-slate-400 hover:text-white transition-colors text-sm">
                  Press Kit
                </a>
              </li>
            </ul>
          </div>

          {/* Resources Column */}
          <div>
            <h3 className="text-white font-semibold text-sm uppercase tracking-wider mb-4">
              Resources
            </h3>
            <ul className="space-y-3">
              <li>
                <a href="#" className="text-slate-400 hover:text-white transition-colors text-sm">
                  Documentation
                </a>
              </li>
              <li>
                <a href="#" className="text-slate-400 hover:text-white transition-colors text-sm">
                  API Reference
                </a>
              </li>
              <li>
                <a href="#" className="text-slate-400 hover:text-white transition-colors text-sm">
                  Community
                </a>
              </li>
              <li>
                <a href="#" className="text-slate-400 hover:text-white transition-colors text-sm">
                  Support
                </a>
              </li>
            </ul>
          </div>

          {/* Legal Column */}
          <div>
            <h3 className="text-white font-semibold text-sm uppercase tracking-wider mb-4">
              Legal
            </h3>
            <ul className="space-y-3">
              <li>
                <a href="#" className="text-slate-400 hover:text-white transition-colors text-sm">
                  Privacy Policy
                </a>
              </li>
              <li>
                <a href="#" className="text-slate-400 hover:text-white transition-colors text-sm">
                  Terms of Service
                </a>
              </li>
              <li>
                <a href="#" className="text-slate-400 hover:text-white transition-colors text-sm">
                  Cookie Policy
                </a>
              </li>
              <li>
                <a href="#" className="text-slate-400 hover:text-white transition-colors text-sm">
                  Disclaimer
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Divider */}
        <div className="border-t border-slate-800 pt-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            {/* Copyright */}
            <p className="text-slate-500 text-sm">
              © 2026 DeckDex MTG. All rights reserved.
            </p>

            {/* Social Links */}
            <div className="flex items-center gap-4">
              <a
                href="https://twitter.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-slate-400 hover:text-white transition-colors p-2 hover:bg-slate-900 rounded-lg"
              >
                <Twitter className="h-5 w-5" />
              </a>
              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-slate-400 hover:text-white transition-colors p-2 hover:bg-slate-900 rounded-lg"
              >
                <Github className="h-5 w-5" />
              </a>
              <a
                href="https://discord.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-slate-400 hover:text-white transition-colors p-2 hover:bg-slate-900 rounded-lg"
              >
                <MessageCircle className="h-5 w-5" />
              </a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};
