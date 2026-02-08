import { useState } from 'react';
import { Card, api } from '../api/client';

interface CardDetailModalProps {
  card: Card;
  onClose: () => void;
}

export function CardDetailModal({ card, onClose }: CardDetailModalProps) {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

  const cardId = card.id != null ? card.id : null;
  const imageUrl = cardId != null ? api.getCardImageUrl(cardId) : null;

  const pt = [card.power, card.toughness].filter(Boolean).join('/');
  const priceStr = card.price && card.price !== 'N/A' ? `€${card.price}` : 'N/A';

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div
        className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col md:flex-row"
        onClick={e => e.stopPropagation()}
      >
        {/* Left: image */}
        <div className="relative flex-shrink-0 p-4 flex items-center justify-center bg-gray-100 dark:bg-gray-900 min-h-[200px] md:min-w-[280px]">
          {imageUrl ? (
            <>
              {!imageLoaded && !imageError && (
                <div className="absolute w-[244px] h-[340px] rounded-lg bg-gray-200 dark:bg-gray-700 animate-pulse" aria-hidden />
              )}
              {imageError && (
                <div className="text-center text-gray-500 dark:text-gray-400 text-sm p-4">
                  Image unavailable
                </div>
              )}
              <img
                src={imageUrl}
                alt={card.name || 'Card'}
                className={`max-w-[244px] max-h-[340px] w-auto h-auto object-contain rounded-lg shadow-md ${!imageLoaded && !imageError ? 'invisible' : ''}`}
                onLoad={() => { setImageLoaded(true); setImageError(false); }}
                onError={() => setImageError(true)}
              />
            </>
          ) : (
            <div className="text-center text-gray-500 dark:text-gray-400 text-sm p-4">
              Image not available
            </div>
          )}
        </div>

        {/* Right: structured text (Scryfall-like) */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="flex justify-between items-start gap-2 mb-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white leading-tight">
              {card.name || 'Unknown'}
            </h2>
            <button
              type="button"
              onClick={onClose}
              className="flex-shrink-0 p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300"
              aria-label="Close"
            >
              <span className="text-xl leading-none">×</span>
            </button>
          </div>

          {(card.mana_cost || card.type) && (
            <div className="flex flex-wrap items-center gap-2 mb-2 text-gray-700 dark:text-gray-300">
              {card.mana_cost && (
                <span className="font-mono text-sm">{card.mana_cost}</span>
              )}
              {card.type && (
                <span className="text-sm italic">{card.type}</span>
              )}
            </div>
          )}

          {card.description && (
            <div className="mb-4">
              <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">
                {card.description}
              </p>
            </div>
          )}

          {(card.power || card.toughness) && (
            <div className="mb-4 text-sm font-medium text-gray-700 dark:text-gray-300">
              {pt}
            </div>
          )}

          <div className="space-y-1 text-sm text-gray-600 dark:text-gray-400 border-t border-gray-200 dark:border-gray-600 pt-4 mt-4">
            {card.set_name && (
              <p><span className="font-medium text-gray-700 dark:text-gray-300">Set:</span> {card.set_name}{card.number ? ` #${card.number}` : ''}</p>
            )}
            {card.rarity && (
              <p><span className="font-medium text-gray-700 dark:text-gray-300">Rarity:</span> {card.rarity}</p>
            )}
            <p><span className="font-medium text-gray-700 dark:text-gray-300">Price:</span> {priceStr}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
