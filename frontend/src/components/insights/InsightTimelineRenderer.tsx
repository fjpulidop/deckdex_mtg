import { useEffect, useState } from 'react';
import { InsightTimelineData } from '../../api/client';

interface Props {
  data: InsightTimelineData;
  answerText: string;
}

export function InsightTimelineRenderer({ data, answerText }: Props) {
  const [animated, setAnimated] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setAnimated(true), 50);
    return () => clearTimeout(t);
  }, []);

  const maxCount = Math.max(...data.items.map(i => i.count), 1);

  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-600 dark:text-gray-400">{answerText}</p>

      {data.items.length === 0 ? (
        <p className="text-sm text-gray-400 dark:text-gray-500 italic">No timeline data available</p>
      ) : (
        <div className="space-y-2">
          {data.items.map((item, i) => {
            const widthPct = animated ? (item.count / maxCount) * 100 : 0;
            return (
              <div key={item.period} className="flex items-center gap-3">
                {/* Period label */}
                <div className="w-20 shrink-0 text-right">
                  <span className="text-xs text-gray-600 dark:text-gray-400">{item.period}</span>
                </div>

                {/* Bar */}
                <div className="flex-1 h-5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-indigo-500 dark:bg-indigo-600 rounded-full transition-all"
                    style={{
                      width: `${widthPct}%`,
                      transitionProperty: 'width',
                      transitionDuration: '400ms',
                      transitionTimingFunction: 'ease-out',
                      transitionDelay: `${i * 80}ms`,
                    }}
                  />
                </div>

                {/* Count + value */}
                <div className="flex items-center gap-1.5 w-32 shrink-0">
                  <span className="text-sm font-medium text-gray-800 dark:text-gray-200 tabular-nums">
                    {item.count} cards
                  </span>
                  {item.value && (
                    <span className="text-xs text-gray-400 dark:text-gray-500 tabular-nums">
                      {item.value}
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
