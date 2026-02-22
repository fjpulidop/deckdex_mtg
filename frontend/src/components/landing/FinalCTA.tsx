import { motion } from 'framer-motion';
import { ArrowRight } from 'lucide-react';

export const FinalCTA = () => {
  return (
    <section className="py-20 md:py-32 bg-gradient-to-r from-slate-900 via-purple-900/50 to-slate-900 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="space-y-6"
        >
          <h2 className="text-4xl md:text-5xl font-bold">
            <span className="bg-gradient-to-r from-purple-300 to-pink-400 bg-clip-text text-transparent">
              Ready to supercharge your collection?
            </span>
          </h2>

          <p className="text-lg text-slate-300 max-w-2xl mx-auto">
            Join thousands of Magic players using DeckDex to organize, analyze, and optimize their collections. Start free today.
          </p>

          <div className="pt-4">
            <a
              href="/login"
              className="inline-flex items-center justify-center px-10 py-4 rounded-lg bg-gradient-to-r from-primary-500 to-accent-500 text-white font-semibold text-lg hover:shadow-2xl hover:shadow-primary-500/50 transition-all duration-300 hover:scale-105"
            >
              Get Started Free <ArrowRight className="ml-3 h-5 w-5" />
            </a>
          </div>
        </motion.div>
      </div>
    </section>
  );
};
