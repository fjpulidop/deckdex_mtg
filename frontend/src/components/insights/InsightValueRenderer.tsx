import { useEffect, useState } from 'react';
import { InsightValueData } from '../../api/client';

interface Props {
  data: InsightValueData;
  answerText: string;
}

function useCountUp(target: number, duration = 800): number {
  const [value, setValue] = useState(0);
  useEffect(() => {
    if (target === 0) { setValue(0); return; }
    let start: number | null = null;
    const step = (ts: number) => {
      if (!start) start = ts;
      const progress = Math.min((ts - start) / duration, 1);
      // Ease out
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(eased * target);
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [target, duration]);
  return value;
}

export function InsightValueRenderer({ data, answerText }: Props) {
  // Extract numeric value for count-up animation
  const numericStr = data.primary_value.replace(/[^0-9.,]/g, '').replace(',', '.');
  const numericTarget = parseFloat(numericStr) || 0;
  const animated = useCountUp(numericTarget);

  // Reconstruct the animated display string
  const isEuro = data.primary_value.startsWith('€');
  const displayValue = isEuro
    ? `€${animated.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    : Math.round(animated).toLocaleString('es-ES');

  return (
    <div className="space-y-4">
      {/* Answer text */}
      <p className="text-sm text-gray-600 dark:text-gray-400">{answerText}</p>

      {/* Big primary value */}
      <div className="flex items-baseline gap-2">
        <span className="text-4xl font-bold text-gray-900 dark:text-white tabular-nums">
          {displayValue}
        </span>
        {data.unit && (
          <span className="text-lg text-gray-500 dark:text-gray-400">{data.unit}</span>
        )}
      </div>

      {/* Breakdown with staggered fade-in */}
      {data.breakdown && data.breakdown.length > 0 && (
        <div className="flex flex-wrap gap-3 pt-2">
          {data.breakdown.map((item, i) => (
            <div
              key={item.label}
              className="flex flex-col px-3 py-2 bg-gray-50 dark:bg-gray-700 rounded-lg"
              style={{
                opacity: 0,
                animation: `fadeIn 200ms ease forwards`,
                animationDelay: `${i * 50}ms`,
              }}
            >
              <span className="text-xs text-gray-500 dark:text-gray-400">{item.label}</span>
              <span className="text-sm font-semibold text-gray-800 dark:text-gray-200">{item.value}</span>
            </div>
          ))}
        </div>
      )}

      <style>{`
        @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
    </div>
  );
}
