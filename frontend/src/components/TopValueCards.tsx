import { useState } from 'react';
import { api, Card } from '../api/client';

interface TopValueCardsProps {
  cards: Card[];
  onCardClick: (card: Card) => void;
}

const RARITY_BADGE: Record<string, string> = {
  common:   'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  uncommon: 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300',
  rare:     'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300',
  mythic:   'bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-300',
};

function CardSlot({ card, onClick }: { card: Card; onClick: () => void }) {
  const [imgError, setImgError] = useState(false);
  const imageUrl = card.id != null ? api.getCardImageUrl(card.id) : null;
  const rarityKey = (card.rarity ?? '').toLowerCase();
  const badgeClass = RARITY_BADGE[rarityKey] ?? RARITY_BADGE.common;
  const price = parseFloat(card.price ?? '');
  const formattedPrice = new Intl.NumberFormat('es-ES', {
    style: 'currency',
    currency: 'EUR',
  }).format(price);

  return (
    <button
      type="button"
      onClick={onClick}
      className="flex flex-col items-center gap-2 p-2 rounded-lg cursor-pointer hover:ring-2 hover:ring-blue-400 dark:hover:ring-blue-500 transition focus:outline-none focus:ring-2 focus:ring-blue-400 w-[120px] shrink-0"
    >
      {/* Image */}
      <div className="w-[90px] h-[120px] rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
        {imageUrl && !imgError ? (
          <img
            src={imageUrl}
            alt={card.name ?? 'Card'}
            loading="lazy"
            onError={() => setImgError(true)}
            className="w-full h-full object-contain"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400 dark:text-gray-500 text-xs text-center px-1">
            {card.name ?? '—'}
          </div>
        )}
      </div>

      {/* Name */}
      <p className="text-xs font-medium text-gray-900 dark:text-white text-center leading-tight line-clamp-2 w-full">
        {card.name ?? '—'}
      </p>

      {/* Set */}
      {card.set_name && (
        <p className="text-[10px] text-gray-500 dark:text-gray-400 text-center truncate w-full">
          {card.set_name}
        </p>
      )}

      {/* Rarity badge */}
      {card.rarity && (
        <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full capitalize ${badgeClass}`}>
          {card.rarity}
        </span>
      )}

      {/* Price */}
      <p className="text-sm font-bold text-green-600 dark:text-green-400">
        {formattedPrice}
      </p>
    </button>
  );
}

export function TopValueCards({ cards, onCardClick }: TopValueCardsProps) {
  const top5 = cards
    .filter(c => {
      const p = parseFloat(c.price ?? '');
      return Number.isFinite(p) && p > 0;
    })
    .sort((a, b) => parseFloat(b.price!) - parseFloat(a.price!))
    .slice(0, 5);

  if (top5.length === 0) return null;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 mb-6">
      <h2 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">
        Top 5 más valiosas
      </h2>
      <div className="flex flex-wrap gap-3">
        {top5.map(card => (
          <CardSlot
            key={card.id ?? card.name}
            card={card}
            onClick={() => onCardClick(card)}
          />
        ))}
      </div>
    </div>
  );
}
