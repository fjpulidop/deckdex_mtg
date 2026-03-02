import { motion } from 'framer-motion';
import { useTranslation, Trans } from 'react-i18next';
import { BentoCard } from './BentoCard';
import { Zap, Wand2, TrendingUp, Gauge } from 'lucide-react';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.6,
    },
  },
};

export const BentoGrid = () => {
  const { t } = useTranslation();
  return (
    <section id="features" className="py-20 md:py-32 bg-gradient-to-b from-slate-900 to-slate-950 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="text-center mb-16 md:mb-24">
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            <span className="bg-gradient-to-r from-purple-300 to-pink-400 bg-clip-text text-transparent">
              {t('bento.sectionTitle')}
            </span>
          </h2>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto mb-6">
            {t('bento.sectionSubtitle')}
          </p>
          <p className="text-slate-500 text-sm max-w-2xl mx-auto">
            <Trans
              i18nKey="bento.contribute"
              components={{
                1: <a href="https://github.com/yourusername/deckdex-mtg/fork" target="_blank" rel="noopener noreferrer" className="text-accent-400 hover:text-accent-300 transition-colors" />,
                2: <a href="https://github.com/yourusername/deckdex-mtg/pulls" target="_blank" rel="noopener noreferrer" className="text-accent-400 hover:text-accent-300 transition-colors" />,
              }}
            />
          </p>
        </div>

        {/* Bento Grid */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-100px' }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8"
        >
          {/* Collection Management - Large */}
          <motion.div variants={itemVariants} className="md:col-span-1 lg:col-span-1">
            <BentoCard
              size="large"
              title={t('bento.cards.collection.title')}
              description={t('bento.cards.collection.desc')}
              icon={<Zap className="h-6 w-6" />}
              gradientFrom="from-blue-500/20"
              gradientTo="to-blue-600/20"
              label="Collection View (600x500px)"
            />
          </motion.div>

          {/* Deck Builder - Large */}
          <motion.div variants={itemVariants} className="md:col-span-1 lg:col-span-1">
            <BentoCard
              size="large"
              title={t('bento.cards.deckBuilder.title')}
              description={t('bento.cards.deckBuilder.desc')}
              icon={<Wand2 className="h-6 w-6" />}
              badge="ALPHA"
              gradientFrom="from-purple-500/20"
              gradientTo="to-purple-600/20"
              label="Deck Builder (600x500px)"
            />
          </motion.div>

          {/* AI Insights - Medium */}
          <motion.div variants={itemVariants} className="md:col-span-2 lg:col-span-1">
            <BentoCard
              size="medium"
              title={t('bento.cards.aiInsights.title')}
              description={t('bento.cards.aiInsights.desc')}
              icon={<Wand2 className="h-6 w-6" />}
              gradientFrom="from-pink-500/20"
              gradientTo="to-rose-600/20"
              label="AI Insights (600x400px)"
            />
          </motion.div>

          {/* Real-time Progress - Small */}
          <motion.div variants={itemVariants} className="md:col-span-1 lg:col-span-1">
            <BentoCard
              size="small"
              title={t('bento.cards.realtime.title')}
              description={t('bento.cards.realtime.desc')}
              icon={<Gauge className="h-6 w-6" />}
              gradientFrom="from-amber-500/20"
              gradientTo="to-orange-600/20"
              label="Real-time (500x400px)"
            />
          </motion.div>

          {/* Pricing Analytics - Medium */}
          <motion.div variants={itemVariants} className="md:col-span-1 lg:col-span-2">
            <BentoCard
              size="medium"
              title={t('bento.cards.priceTracking.title')}
              description={t('bento.cards.priceTracking.desc')}
              icon={<TrendingUp className="h-6 w-6" />}
              gradientFrom="from-green-500/20"
              gradientTo="to-emerald-600/20"
              label="Analytics Dashboard (600x400px)"
            />
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
};
