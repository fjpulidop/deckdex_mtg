import { InsightComparisonData } from '../../api/client';

interface Props {
  data: InsightComparisonData;
  answerText: string;
}

export function InsightComparisonRenderer({ data, answerText }: Props) {
  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-600 dark:text-gray-400">{answerText}</p>

      <div className="flex flex-wrap gap-3">
        {data.items.map((item, i) => {
          // Detect MTG color symbols: White, Blue, Black, Red, Green
          const COLOR_SYMBOL: Record<string, string> = {
            White: 'W', Blue: 'U', Black: 'B', Red: 'R', Green: 'G',
          };
          const symbol = COLOR_SYMBOL[item.label];

          return (
            <div
              key={item.label}
              className="flex flex-col items-center gap-1.5 p-3 rounded-xl border-2 min-w-[80px]"
              style={{
                borderColor: item.present ? '#22c55e' : '#ef4444',
                backgroundColor: item.present ? 'rgb(240 253 244 / 0.5)' : 'rgb(254 242 242 / 0.5)',
                opacity: 0,
                animation: `scaleBounce 300ms cubic-bezier(0.34, 1.56, 0.64, 1) forwards`,
                animationDelay: `${i * 80}ms`,
              }}
            >
              {/* Mana symbol if it's a color, else plain label */}
              {symbol ? (
                <span className={`card-symbol card-symbol-${symbol} text-xl`} aria-hidden="true" />
              ) : null}

              <span className="text-xs font-medium text-gray-700 dark:text-gray-300 text-center">
                {item.label}
              </span>

              {/* Check or cross */}
              <span
                className="text-lg font-bold"
                style={{ color: item.present ? '#16a34a' : '#dc2626' }}
                aria-label={item.present ? 'Present' : 'Missing'}
              >
                {item.present ? '✓' : '✗'}
              </span>

              {item.detail && (
                <span className="text-[10px] text-gray-500 dark:text-gray-400 text-center leading-tight">
                  {item.detail}
                </span>
              )}
            </div>
          );
        })}
      </div>

      <style>{`
        @keyframes scaleBounce {
          from { opacity: 0; transform: scale(0.7); }
          to { opacity: 1; transform: scale(1); }
        }
        /* Dark mode background overrides */
        @media (prefers-color-scheme: dark) {
          .dark .comparison-item-present { background-color: rgb(20 83 45 / 0.3); }
          .dark .comparison-item-absent { background-color: rgb(127 29 29 / 0.3); }
        }
      `}</style>
    </div>
  );
}
