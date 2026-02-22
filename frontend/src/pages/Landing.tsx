import { useRef } from 'react';
import { LandingNavbar } from '@/components/landing/LandingNavbar';
import { Hero } from '@/components/landing/Hero';
import { BentoGrid } from '@/components/landing/BentoGrid';
import { InteractiveDemo } from '@/components/landing/InteractiveDemo';
import { FinalCTA } from '@/components/landing/FinalCTA';

export const Landing = () => {
  const demoRef = useRef<HTMLDivElement>(null);

  const handleDemoClick = () => {
    demoRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-purple-900/20 to-slate-900">
      <LandingNavbar />
      <Hero onDemoClick={handleDemoClick} />
      <BentoGrid />
      <div ref={demoRef}>
        <InteractiveDemo />
      </div>
      <FinalCTA />
    </div>
  );
};
