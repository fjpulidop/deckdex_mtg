import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import i18next from 'i18next';
import { ArrowRight } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { redirectToGoogleLogin } from '@/utils/auth';

const handleGoogleLogin = () => {
  redirectToGoogleLogin();
};

export const Hero = () => {
  const { t } = useTranslation();
  const { isAuthenticated } = useAuth();
  return (
    <section className="min-h-screen pt-20 pb-16 bg-gradient-to-br from-slate-900/20 via-purple-900/10 to-slate-900/20 flex items-center">
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
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-accent-500/10 to-primary-500/10 text-slate-300 text-sm font-medium mb-6">
              <span className="text-lg">✨</span>
              <span>{t('hero.badge')}</span>
            </div>

            {/* Main Headline */}
            <h1 className="text-5xl md:text-6xl font-bold leading-tight">
              <span className="bg-gradient-to-r from-purple-300 via-purple-400 to-pink-500 bg-clip-text text-transparent">
                {t('hero.headline')}
              </span>
            </h1>

            {/* Subheadline */}
            <p className="text-xl text-slate-300 leading-relaxed max-w-xl">
              {t('hero.subtitle')}
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 pt-4">
              {isAuthenticated ? (
                <a
                  href="/dashboard"
                  className="inline-flex items-center justify-center px-8 py-3 rounded-lg bg-gradient-to-r from-primary-500 to-accent-500 text-white font-semibold hover:shadow-lg hover:shadow-primary-500/50 transition-all duration-300 hover:scale-105"
                >
                  {t('hero.goToDashboard')} <ArrowRight className="ml-2 h-5 w-5" />
                </a>
              ) : (
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
                  {t('hero.signIn')}
                </button>
              )}
              {!isAuthenticated && (
                <a
                  href="/demo"
                  className="inline-flex items-center justify-center px-8 py-3 rounded-lg border-2 border-slate-600 text-white font-semibold hover:bg-slate-800/50 hover:border-slate-500 transition-all duration-300"
                >
                  {t('hero.tryLiveDemo')} <ArrowRight className="ml-2 h-5 w-5" />
                </a>
              )}
            </div>
          </motion.div>

          {/* Right Column - App Description Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2, ease: 'easeOut' }}
            className="flex justify-center"
          >
            <div className="relative w-full max-w-xl rounded-2xl overflow-hidden shadow-2xl shadow-purple-500/20 border border-slate-700/50 bg-slate-900/60 backdrop-blur-sm p-6">
              <div className="flex gap-4">
                {/* English panel */}
                <div className="flex-1 border-r border-slate-700/30 pr-4">
                  <p className="text-xs font-bold text-purple-400/70 uppercase tracking-widest mb-3">EN</p>
                  <p className="text-purple-300 font-semibold text-sm mb-3">
                    {i18next.getFixedT('en')('hero.descCard.title')}
                  </p>
                  <ul className="space-y-2 mb-4">
                    {(['feature1', 'feature2', 'feature3', 'feature4'] as const).map((key) => (
                      <li key={key} className="text-slate-300 text-sm flex gap-2">
                        <span className="text-purple-400 shrink-0">✦</span>
                        {i18next.getFixedT('en')(`hero.descCard.${key}`)}
                      </li>
                    ))}
                  </ul>
                  <p className="text-slate-400 text-xs italic">{i18next.getFixedT('en')('hero.descCard.tagline')}</p>
                </div>
                {/* Spanish panel */}
                <div className="flex-1 pl-0">
                  <p className="text-xs font-bold text-purple-400/70 uppercase tracking-widest mb-3">ES</p>
                  <p className="text-purple-300 font-semibold text-sm mb-3">
                    {i18next.getFixedT('es')('hero.descCard.title')}
                  </p>
                  <ul className="space-y-2 mb-4">
                    {(['feature1', 'feature2', 'feature3', 'feature4'] as const).map((key) => (
                      <li key={key} className="text-slate-300 text-sm flex gap-2">
                        <span className="text-purple-400 shrink-0">✦</span>
                        {i18next.getFixedT('es')(`hero.descCard.${key}`)}
                      </li>
                    ))}
                  </ul>
                  <p className="text-slate-400 text-xs italic">{i18next.getFixedT('es')('hero.descCard.tagline')}</p>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
};
