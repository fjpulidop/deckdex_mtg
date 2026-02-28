import { useEffect, useState } from 'react';
import { InsightDistributionData } from '../../api/client';

interface Props {
  data: InsightDistributionData;
  answerText: string;
}

const COLOR_BAR_CLASSES: Record<string, string> = {
  W: 'bg-yellow-300 dark:bg-yellow-500',
  U: 'bg-blue-500 dark:bg-blue-600',
  B: 'bg-gray-700 dark:bg-gray-600',
  R: 'bg-red-500 dark:bg-red-600',
  G: 'bg-green-500 dark:bg-green-600',
  C: 'bg-gray-400 dark:bg-gray-500',
};

const DEFAULT_BAR_CLASS = 'bg-indigo-500 dark:bg-indigo-600';

export function InsightDistributionRenderer({ data, answerText }: Props) {
  const [animated, setAnimated] = useState(false);

  useEffect(() => {
    // Trigger bar growth after mount
    const t = setTimeout(() => setAnimated(true), 50);
    return () => clearTimeout(t);
  }, []);

  const maxPercentage = Math.max(...data.items.map(i => i.percentage), 1);

  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-600 dark:text-gray-400">{answerText}</p>

      <div className="space-y-2">
        {data.items.map((item, i) => {
          const barColor = item.color
            ? COLOR_BAR_CLASSES[item.color] ?? DEFAULT_BAR_CLASS
            : DEFAULT_BAR_CLASS;
          const widthPct = animated ? (item.percentage / maxPercentage) * 100 : 0;

          return (
            <div key={item.label} className="flex items-center gap-3">
              {/* Label with optional mana symbol */}
              <div className="w-24 flex items-center gap-1 shrink-0">
                {item.color && ['W', 'U', 'B', 'R', 'G'].includes(item.color) && (
                  <span className={`card-symbol card-symbol-${item.color}`} aria-hidden="true" />
                )}
                <span className="text-sm text-gray-700 dark:text-gray-300 truncate">{item.label}</span>
              </div>

              {/* Bar */}
              <div className="flex-1 h-5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  className={`h-full ${barColor} rounded-full transition-all`}
                  style={{
                    width: `${widthPct}%`,
                    transitionProperty: 'width',
                    transitionDuration: '400ms',
                    transitionTimingFunction: 'ease-out',
                    transitionDelay: `${i * 80}ms`,
                  }}
                />
              </div>

              {/* Stats */}
              <div className="flex items-center gap-2 w-28 shrink-0 text-right justify-end">
                <span className="text-sm font-medium text-gray-800 dark:text-gray-200 tabular-nums">
                  {item.value ?? item.count.toLocaleString('es-ES')}
                </span>
                <span className="text-xs text-gray-400 dark:text-gray-500 tabular-nums">
                  {item.percentage.toFixed(1)}%
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
