import { motion } from 'framer-motion';
import { ArrowRight } from 'lucide-react';

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
            {/* Main Headline */}
            <h1 className="text-5xl md:text-6xl font-bold leading-tight">
              <span className="bg-gradient-to-r from-purple-300 via-purple-400 to-pink-500 bg-clip-text text-transparent">
                Your MTG Collection, Supercharged
              </span>
            </h1>

            {/* Subheadline */}
            <p className="text-xl text-slate-300 leading-relaxed max-w-xl">
              Track prices in real-time, build competitive decks with AI insights, and manage your collection with ease. All in one powerful platform.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 pt-4">
              <a
                href="/login"
                className="inline-flex items-center justify-center px-8 py-3 rounded-lg bg-gradient-to-r from-primary-500 to-accent-500 text-white font-semibold hover:shadow-lg hover:shadow-primary-500/50 transition-all duration-300 hover:scale-105"
              >
                Get Started <ArrowRight className="ml-2 h-5 w-5" />
              </a>
              <button
                onClick={onDemoClick}
                className="inline-flex items-center justify-center px-8 py-3 rounded-lg border-2 border-slate-600 text-white font-semibold hover:bg-slate-800/50 hover:border-slate-500 transition-all duration-300"
              >
                Watch Demo
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
