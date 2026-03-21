import { useTranslation } from 'react-i18next';
import { ManaText } from './ManaText';
import { CHART_COLORS } from './analytics/constants';
import type { OverlapCard, DeckComparisonStats } from '../api/client';

interface OverlapCardListProps {
  cards: OverlapCard[];
  decks: DeckComparisonStats[];
}

export function OverlapCardList({ cards, decks }: OverlapCardListProps) {
  const { t } = useTranslation();

  const deckNameById = Object.fromEntries(decks.map(d => [d.deck_id, d.deck_name]));

  if (cards.length === 0) {
    return (
      <p className="text-sm text-gray-500 dark:text-gray-400 mt-4">
        {t('deckComparison.noOverlap')}
      </p>
    );
  }

  return (
    <div className="mt-4">
      <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
        {t('deckComparison.overlapTitle')}
      </h3>
      <ul className="space-y-1">
        {cards.map((card, idx) => (
          <li
            key={`${card.name}-${idx}`}
            className="bg-indigo-50 dark:bg-indigo-900/20 rounded px-3 py-2 flex items-center gap-2 flex-wrap"
          >
            <span className="font-medium text-sm text-gray-900 dark:text-white truncate max-w-[160px]">
              {card.name}
            </span>
            {card.mana_cost && (
              <ManaText text={card.mana_cost} className="text-sm" />
            )}
            {card.price && (
              <span className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded-full px-2 py-0.5">
                €{card.price}
              </span>
            )}
            <div className="flex gap-1 flex-wrap">
              {card.deck_ids.map((deckId, badgeIdx) => (
                <span
                  key={deckId}
                  className="text-xs rounded-full px-2 py-0.5 text-white font-medium"
                  style={{ backgroundColor: CHART_COLORS[badgeIdx % CHART_COLORS.length] }}
                >
                  {deckNameById[deckId] ?? `Deck ${deckId}`}
                </span>
              ))}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
