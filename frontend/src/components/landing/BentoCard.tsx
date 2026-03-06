import { motion } from 'framer-motion';
import { ReactNode } from 'react';

interface BentoCardProps {
  size: 'small' | 'medium' | 'large';
  title: string;
  description: string;
  icon?: ReactNode;
  badge?: string;
  gradientFrom: string;
  gradientTo: string;
  illustrationIcon?: ReactNode;
}

export const BentoCard = ({
  size,
  title,
  description,
  icon,
  badge,
  gradientFrom,
  gradientTo,
  illustrationIcon,
}: BentoCardProps) => {
  const sizeClasses = {
    small: 'lg:col-span-1 lg:row-span-1 h-96',
    medium: 'lg:col-span-2 lg:row-span-1 h-96',
    large: 'lg:col-span-1 lg:row-span-1 h-96 md:h-full',
  };

  return (
    <motion.div
      whileHover={{ y: -4 }}
      transition={{ duration: 0.3 }}
      className={`group relative rounded-xl border border-slate-700/50 overflow-hidden bg-slate-900/50 backdrop-blur-sm hover:border-slate-600 transition-all duration-300 ${sizeClasses[size]}`}
    >
      {/* Gradient Background */}
      <div
        className={`absolute inset-0 bg-gradient-to-br ${gradientFrom} ${gradientTo} opacity-10 group-hover:opacity-15 transition-opacity duration-300`}
      />

      {/* Glow on Hover */}
      <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-500/20 via-transparent to-pink-500/20 blur-2xl" />
      </div>

      {/* Content */}
      <div className="relative h-full flex flex-col p-6 md:p-8">
        {/* Icon and Badge */}
        <div className="flex items-start justify-between mb-4">
          {icon && (
            <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-primary-500/20 to-accent-500/20 flex items-center justify-center text-white">
              {icon}
            </div>
          )}
          {badge && (
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-accent-500/20 text-accent-300 border border-accent-500/50">
              {badge}
            </span>
          )}
        </div>

        {/* Title */}
        <h3 className="text-xl md:text-2xl font-bold text-white mb-2">{title}</h3>

        {/* Description */}
        <p className="text-slate-300 text-sm md:text-base mb-6 flex-grow">
          {description}
        </p>

        {/* Illustration */}
        <div className={`relative w-full ${size === 'large' ? 'h-48' : size === 'medium' ? 'h-40' : 'h-32'} rounded-lg bg-gradient-to-br ${gradientFrom} ${gradientTo} flex items-center justify-center border border-slate-600/30 overflow-hidden`}>
          <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent" />
          {illustrationIcon && (
            <div className="relative text-white/20 group-hover:text-white/30 transition-colors duration-300">
              {illustrationIcon}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};
