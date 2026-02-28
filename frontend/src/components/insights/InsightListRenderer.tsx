import { InsightListData } from '../../api/client';
import { Card } from '../../api/client';
import { useCardImage } from '../../hooks/useCardImage';

interface Props {
  data: InsightListData;
  answerText: string;
  onCardClick?: (card: Card) => void;
}

function CardThumbnail({ cardId }: { cardId: number }) {
  const { src, error } = useCardImage(cardId);
  if (error) return null;
  return (
    <img
      src={src ?? undefined}
      alt=""
      className="w-8 h-10 object-contain rounded"
    />
  );
}

export function InsightListRenderer({ data, answerText, onCardClick }: Props) {
  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-600 dark:text-gray-400">{answerText}</p>

      {data.items.length === 0 ? (
        <p className="text-sm text-gray-400 dark:text-gray-500 italic">No items to display</p>
      ) : (
        <ol className="space-y-1.5">
          {data.items.map((item, i) => {
            const clickable = item.card_id != null && onCardClick != null;
            const content = (
              <div className="flex items-center gap-3 w-full">
                {/* Rank */}
                <span className="w-6 text-xs font-bold text-gray-400 dark:text-gray-500 shrink-0 text-right">
                  {i + 1}.
                </span>

                {/* Thumbnail */}
                {item.card_id != null && (
                  <CardThumbnail cardId={item.card_id} />
                )}

                {/* Name + detail */}
                <div className="flex-1 min-w-0">
                  <span className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate block">
                    {item.name}
                  </span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">{item.detail}</span>
                </div>
              </div>
            );

            const baseClass = `flex items-center rounded-lg px-2 py-1.5 transition-all`
              + (clickable
                ? ' cursor-pointer hover:bg-indigo-50 dark:hover:bg-indigo-900/30'
                : '');

            return (
              <li
                key={`${item.card_id ?? ''}-${item.name}-${i}`}
                className={baseClass}
                style={{
                  opacity: 0,
                  animation: `slideIn 200ms ease forwards`,
                  animationDelay: `${i * 60}ms`,
                }}
                onClick={clickable ? () => onCardClick!({ id: item.card_id!, name: item.name } as Card) : undefined}
                role={clickable ? 'button' : undefined}
                tabIndex={clickable ? 0 : undefined}
                onKeyDown={clickable ? (e) => { if (e.key === 'Enter') onCardClick!({ id: item.card_id!, name: item.name } as Card); } : undefined}
              >
                {content}
              </li>
            );
          })}
        </ol>
      )}

      <style>{`
        @keyframes slideIn { from { opacity: 0; transform: translateX(-8px); } to { opacity: 1; transform: translateX(0); } }
      `}</style>
    </div>
  );
}
