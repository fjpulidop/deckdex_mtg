import { Hero } from '@/components/landing/Hero';
import { BentoGrid } from '@/components/landing/BentoGrid';
import { FinalCTA } from '@/components/landing/FinalCTA';
import { Footer } from '@/components/landing/Footer';

export const Landing = () => {
  return (
    <div className="relative z-10 min-h-screen bg-gradient-to-b from-slate-900/90 via-purple-900/20 to-slate-900/90">
      <Hero />
      <BentoGrid />
      <FinalCTA />
      <Footer />
    </div>
  );
};
