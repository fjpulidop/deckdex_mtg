import { motion } from 'framer-motion';
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
  return (
    <section id="features" className="py-20 md:py-32 bg-gradient-to-b from-slate-900 to-slate-950 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <div className="text-center mb-16 md:mb-24">
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            <span className="bg-gradient-to-r from-purple-300 to-pink-400 bg-clip-text text-transparent">
              Powerful Features
            </span>
          </h2>
          <p className="text-slate-400 text-lg max-w-2xl mx-auto mb-6">
            Everything you need to manage, analyze, and optimize your Magic: The Gathering collection.
          </p>
          <p className="text-slate-500 text-sm max-w-2xl mx-auto">
            🤝 Missing a feature? <a href="https://github.com/yourusername/deckdex-mtg/fork" target="_blank" rel="noopener noreferrer" className="text-accent-400 hover:text-accent-300 transition-colors">Fork us</a> or submit a <a href="https://github.com/yourusername/deckdex-mtg/pulls" target="_blank" rel="noopener noreferrer" className="text-accent-400 hover:text-accent-300 transition-colors">Pull Request</a> to help us improve!
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
              title="Collection Management"
              description="Organize your cards by set, rarity, and condition. Track quantities and organize your collection with powerful filtering and search."
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
              title="Deck Builder"
              description="Design and test competitive decks with instant syntax validation. Create multiple deck versions and track your brewing progress."
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
              title="AI Insights"
              description="Get intelligent recommendations for card combinations, deck optimization suggestions, and meta-game analysis powered by advanced AI."
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
              title="Real-time Updates"
              description="Price alerts, job progress tracking, and instant notifications keep you informed about your collection changes."
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
              title="Price Tracking & Analytics"
              description="Monitor card prices across multiple vendors, track portfolio value trends, and receive alerts when prices spike or drop."
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
