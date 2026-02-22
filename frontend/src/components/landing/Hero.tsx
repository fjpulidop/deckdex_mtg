import { motion } from 'framer-motion';
import { ArrowRight } from 'lucide-react';

const handleGoogleLogin = () => {
  window.location.href = 'http://localhost:8000/api/auth/google';
};

export const Hero = ({ onDemoClick }: { onDemoClick: () => void }) => {
  return (
    <section className="min-h-screen pt-20 pb-16 bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* Left Column - Text */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: 'easeOut' }}
            className="space-y-6"
          >
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent-500/20 border border-accent-500/50 text-accent-300 text-sm font-semibold mb-4">
              <span>✨</span>
              <span>Open Source MTG Collection Tool</span>
            </div>

            {/* Main Headline */}
            <h1 className="text-5xl md:text-6xl font-bold leading-tight">
              <span className="bg-gradient-to-r from-purple-300 via-purple-400 to-pink-500 bg-clip-text text-transparent">
                Your MTG Collection, Supercharged
              </span>
            </h1>

            {/* Subheadline */}
            <p className="text-xl text-slate-300 leading-relaxed max-w-xl">
              Track prices in real-time, build competitive decks with AI insights, and manage your collection with ease. Community-driven, always evolving.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 pt-4">
              <button
                onClick={handleGoogleLogin}
                className="inline-flex items-center justify-center px-8 py-3 rounded-lg bg-gradient-to-r from-primary-500 to-accent-500 text-white font-semibold hover:shadow-lg hover:shadow-primary-500/50 transition-all duration-300 hover:scale-105"
              >
                <svg
                  className="w-5 h-5 mr-2"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="white" />
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="white" />
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="white" />
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="white" />
                </svg>
                Get Started
              </button>
              <button
                onClick={onDemoClick}
                className="inline-flex items-center justify-center px-8 py-3 rounded-lg border-2 border-slate-600 text-white font-semibold hover:bg-slate-800/50 hover:border-slate-500 transition-all duration-300"
              >
                Try Demo <ArrowRight className="ml-2 h-5 w-5" />
              </button>
            </div>
          </motion.div>

          {/* Right Column - Dashboard Preview */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2, ease: 'easeOut' }}
            className="flex justify-center"
          >
            <div className="relative w-full max-w-xl aspect-[3/2] rounded-lg overflow-hidden shadow-2xl shadow-purple-500/20 border border-slate-700/50">
              {/* Gradient Placeholder */}
              <div className="absolute inset-0 bg-gradient-to-br from-purple-600/20 via-slate-900 to-slate-900 flex items-center justify-center">
                <div className="text-center space-y-3">
                  <div className="h-32 w-32 mx-auto rounded-lg bg-gradient-to-br from-purple-500/30 to-pink-500/30 blur-xl" />
                  <p className="text-slate-400 text-sm font-medium">Dashboard Preview (1200x800px)</p>
                  <p className="text-slate-500 text-xs">Replace with actual screenshot</p>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
};
