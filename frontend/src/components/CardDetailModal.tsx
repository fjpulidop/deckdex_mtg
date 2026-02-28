import { useState, useEffect } from 'react';
import { Card, api } from '../api/client';
import { useCardImage } from '../hooks/useCardImage';
import { useActiveJobs } from '../contexts/ActiveJobsContext';
import { ManaText } from './ManaText';
import { ConfirmModal } from './ConfirmModal';

interface CardDetailModalProps {
  card: Card;
  onClose: () => void;
  onPriceUpdateJobComplete?: () => void;
  onCardUpdated?: (card: Card) => void;
  onCardDeleted?: () => void;
}

type EditForm = {
  name: string;
  type: string;
  mana_cost: string;
  description: string;
  power: string;
  toughness: string;
  set_name: string;
  number: string;
  rarity: string;
  price: string;
};

function cardToEditForm(c: Card): EditForm {
  return {
    name: c.name ?? '',
    type: c.type ?? '',
    mana_cost: c.mana_cost ?? '',
    description: c.description ?? '',
    power: c.power ?? '',
    toughness: c.toughness ?? '',
    set_name: c.set_name ?? '',
    number: c.number ?? '',
    rarity: c.rarity ?? '',
    price: c.price ?? '',
  };
}

export function CardDetailModal({
  card,
  onClose,
  onPriceUpdateJobComplete,
  onCardUpdated,
  onCardDeleted,
}: CardDetailModalProps) {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [updatePricePending, setUpdatePricePending] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState<EditForm>(() => cardToEditForm(card));
  const [savePending, setSavePending] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [deletePending, setDeletePending] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [imageLightboxOpen, setImageLightboxOpen] = useState(false);
  const { addJob } = useActiveJobs();

  const cardId = card.id != null ? card.id : null;
  const { src: imageUrl, loading: imageLoading, error: imageError } = useCardImage(cardId);

  useEffect(() => {
    setEditForm(cardToEditForm(card));
  }, [card]);

  useEffect(() => {
    if (!imageLightboxOpen) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.stopPropagation();
        setImageLightboxOpen(false);
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [imageLightboxOpen]);

  const pt = [card.power, card.toughness].filter(Boolean).join('/');
  const priceStr = card.price && card.price !== 'N/A' ? `€${card.price}` : 'N/A';

  const displayCard = isEditing ? { ...card, ...editForm } : card;
  const displayName = displayCard.name || 'Unknown';
  const displayPriceStr = isEditing
    ? (editForm.price !== '' && editForm.price !== 'N/A' ? `€${editForm.price}` : 'N/A')
    : priceStr;

  const handleSave = async () => {
    if (card.id == null) return;
    setSaveError(null);
    setSavePending(true);
    try {
      const payload: Partial<Card> = {
        name: editForm.name || undefined,
        type: editForm.type || undefined,
        mana_cost: editForm.mana_cost || undefined,
        description: editForm.description || undefined,
        power: editForm.power || undefined,
        toughness: editForm.toughness || undefined,
        set_name: editForm.set_name || undefined,
        number: editForm.number || undefined,
        rarity: editForm.rarity || undefined,
        price: editForm.price || undefined,
      };
      const updated = await api.updateCard(card.id, payload);
      onCardUpdated?.(updated);
      setIsEditing(false);
    } catch (e) {
      setSaveError(e instanceof Error ? e.message : 'Update failed');
    } finally {
      setSavePending(false);
    }
  };

  const handleCancel = () => {
    setEditForm(cardToEditForm(card));
    setSaveError(null);
    setIsEditing(false);
  };

  const handleDelete = () => {
    if (card.id == null) return;
    setDeleteConfirmOpen(true);
  };

  const handleDeleteConfirmed = async () => {
    if (card.id == null) return;
    setDeleteConfirmOpen(false);
    setDeletePending(true);
    try {
      await api.deleteCard(card.id);
      onCardDeleted?.();
      onClose();
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Delete failed');
    } finally {
      setDeletePending(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div
        className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col md:flex-row"
        onClick={e => e.stopPropagation()}
      >
        {/* Left: image */}
        <div className="relative flex-shrink-0 p-4 flex items-center justify-center bg-gray-100 dark:bg-gray-900 min-h-[200px] md:min-w-[280px]">
          {imageError ? (
            <div className="text-center text-gray-500 dark:text-gray-400 text-sm p-4">
              Image unavailable
            </div>
          ) : imageUrl ? (
            <>
              {!imageLoaded && (
                <div className="absolute w-[280px] h-[390px] rounded-lg bg-gray-200 dark:bg-gray-700 animate-pulse" aria-hidden />
              )}
              <div
                role="button"
                tabIndex={0}
                onClick={() => imageLoaded && setImageLightboxOpen(true)}
                onKeyDown={e => e.key === 'Enter' && imageLoaded && setImageLightboxOpen(true)}
                className="cursor-zoom-in inline-block"
                aria-label="View image larger"
              >
                <img
                  src={imageUrl}
                  alt={displayName}
                  className={`max-w-[280px] max-h-[390px] w-auto h-auto object-contain rounded-lg shadow-md ${!imageLoaded ? 'invisible' : ''}`}
                  onLoad={() => setImageLoaded(true)}
                />
              </div>
            </>
          ) : imageLoading ? (
            <div className="absolute w-[280px] h-[390px] rounded-lg bg-gray-200 dark:bg-gray-700 animate-pulse" aria-hidden />
          ) : (
            <div className="text-center text-gray-500 dark:text-gray-400 text-sm p-4">
              Image not available
            </div>
          )}
        </div>

        {/* Right: structured text (Scryfall-like) or edit form */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="flex justify-between items-start gap-2 mb-4">
            {isEditing ? (
              <input
                type="text"
                value={editForm.name}
                onChange={e => setEditForm(f => ({ ...f, name: e.target.value }))}
                className="flex-1 text-xl font-bold bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white rounded px-2 py-1 border border-gray-300 dark:border-gray-600"
              />
            ) : (
              <h2 className="text-xl font-bold text-gray-900 dark:text-white leading-tight">
                {displayName}
              </h2>
            )}
            <button
              type="button"
              onClick={onClose}
              className="flex-shrink-0 p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300"
              aria-label="Close"
            >
              <span className="text-xl leading-none">×</span>
            </button>
          </div>

          {isEditing ? (
            <>
              <div className="space-y-3 text-sm">
                <div>
                  <label className="block font-medium text-gray-700 dark:text-gray-300 mb-1">Type</label>
                  <input
                    type="text"
                    value={editForm.type}
                    onChange={e => setEditForm(f => ({ ...f, type: e.target.value }))}
                    className="w-full bg-gray-100 dark:bg-gray-700 rounded px-2 py-1.5 border border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block font-medium text-gray-700 dark:text-gray-300 mb-1">Mana cost</label>
                  <input
                    type="text"
                    value={editForm.mana_cost}
                    onChange={e => setEditForm(f => ({ ...f, mana_cost: e.target.value }))}
                    className="w-full bg-gray-100 dark:bg-gray-700 rounded px-2 py-1.5 border border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white font-mono"
                  />
                </div>
                <div>
                  <label className="block font-medium text-gray-700 dark:text-gray-300 mb-1">Description</label>
                  <textarea
                    value={editForm.description}
                    onChange={e => setEditForm(f => ({ ...f, description: e.target.value }))}
                    rows={3}
                    className="w-full bg-gray-100 dark:bg-gray-700 rounded px-2 py-1.5 border border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white resize-y"
                  />
                </div>
                <div className="flex gap-4">
                  <div>
                    <label className="block font-medium text-gray-700 dark:text-gray-300 mb-1">Power</label>
                    <input
                      type="text"
                      value={editForm.power}
                      onChange={e => setEditForm(f => ({ ...f, power: e.target.value }))}
                      className="w-20 bg-gray-100 dark:bg-gray-700 rounded px-2 py-1.5 border border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block font-medium text-gray-700 dark:text-gray-300 mb-1">Toughness</label>
                    <input
                      type="text"
                      value={editForm.toughness}
                      onChange={e => setEditForm(f => ({ ...f, toughness: e.target.value }))}
                      className="w-20 bg-gray-100 dark:bg-gray-700 rounded px-2 py-1.5 border border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white"
                    />
                  </div>
                </div>
                <div>
                  <label className="block font-medium text-gray-700 dark:text-gray-300 mb-1">Set</label>
                  <input
                    type="text"
                    value={editForm.set_name}
                    onChange={e => setEditForm(f => ({ ...f, set_name: e.target.value }))}
                    className="w-full bg-gray-100 dark:bg-gray-700 rounded px-2 py-1.5 border border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block font-medium text-gray-700 dark:text-gray-300 mb-1">Set number</label>
                  <input
                    type="text"
                    value={editForm.number}
                    onChange={e => setEditForm(f => ({ ...f, number: e.target.value }))}
                    className="w-full bg-gray-100 dark:bg-gray-700 rounded px-2 py-1.5 border border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block font-medium text-gray-700 dark:text-gray-300 mb-1">Rarity</label>
                  <input
                    type="text"
                    value={editForm.rarity}
                    onChange={e => setEditForm(f => ({ ...f, rarity: e.target.value }))}
                    className="w-full bg-gray-100 dark:bg-gray-700 rounded px-2 py-1.5 border border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block font-medium text-gray-700 dark:text-gray-300 mb-1">Price</label>
                  <input
                    type="text"
                    value={editForm.price}
                    onChange={e => setEditForm(f => ({ ...f, price: e.target.value }))}
                    className="w-full bg-gray-100 dark:bg-gray-700 rounded px-2 py-1.5 border border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white"
                  />
                </div>
              </div>
              {saveError && (
                <p className="mt-3 text-sm text-red-600 dark:text-red-400" role="alert">
                  {saveError}
                </p>
              )}
            </>
          ) : (
            <>
              {(displayCard.mana_cost || displayCard.type) && (
                <div className="flex flex-wrap items-center gap-2 mb-2 text-gray-700 dark:text-gray-300">
                  {displayCard.mana_cost && (
                    <ManaText text={displayCard.mana_cost} className="font-mono text-sm inline-flex flex-wrap items-center gap-0.5" />
                  )}
                  {displayCard.type && (
                    <span className="text-sm italic">{displayCard.type}</span>
                  )}
                </div>
              )}

              {displayCard.description && (
                <div className="mb-4">
                  <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">
                    <ManaText text={displayCard.description} />
                  </p>
                </div>
              )}

              {(displayCard.power || displayCard.toughness) && (
                <div className="mb-4 text-sm font-medium text-gray-700 dark:text-gray-300">
                  {[displayCard.power, displayCard.toughness].filter(Boolean).join('/')}
                </div>
              )}

              <div className="space-y-1 text-sm text-gray-600 dark:text-gray-400 border-t border-gray-200 dark:border-gray-600 pt-4 mt-4">
                {displayCard.set_name && (
                  <p><span className="font-medium text-gray-700 dark:text-gray-300">Set:</span> {displayCard.set_name}{displayCard.number ? ` #${displayCard.number}` : ''}</p>
                )}
                {displayCard.rarity && (
                  <p><span className="font-medium text-gray-700 dark:text-gray-300">Rarity:</span> {displayCard.rarity}</p>
                )}
                <p><span className="font-medium text-gray-700 dark:text-gray-300">Price:</span> {displayPriceStr}</p>
              </div>
            </>
          )}

          {cardId != null && (
            <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-600 flex flex-wrap items-center gap-2">
              {isEditing ? (
                <>
                  <button
                    type="button"
                    disabled={savePending}
                    onClick={handleSave}
                    className="px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium"
                  >
                    {savePending ? 'Saving…' : 'Save'}
                  </button>
                  <button
                    type="button"
                    disabled={savePending}
                    onClick={handleCancel}
                    className="px-4 py-2 rounded-lg bg-gray-500 hover:bg-gray-600 disabled:opacity-50 text-white text-sm font-medium"
                  >
                    Cancel
                  </button>
                </>
              ) : (
                <>
                  <button
                    type="button"
                    onClick={() => setIsEditing(true)}
                    className="px-4 py-2 rounded-lg bg-gray-600 hover:bg-gray-700 text-white text-sm font-medium"
                  >
                    Edit
                  </button>
                  <button
                    type="button"
                    disabled={deletePending}
                    onClick={handleDelete}
                    className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium"
                  >
                    {deletePending ? 'Deleting…' : 'Delete'}
                  </button>
                  <button
                    type="button"
                    disabled={updatePricePending}
                    onClick={async () => {
                      if (card.id == null) return;
                      setUpdatePricePending(true);
                      try {
                        const result = await api.triggerSingleCardPriceUpdate(card.id);
                        addJob(result.job_id, 'Update price', onPriceUpdateJobComplete);
                      } catch (err) {
                        console.error('Failed to start price update:', err);
                      } finally {
                        setUpdatePricePending(false);
                      }
                    }}
                    className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium"
                  >
                    {updatePricePending ? 'Starting…' : 'Update price'}
                  </button>
                </>
              )}
            </div>
          )}
        </div>
      </div>

      <ConfirmModal
        isOpen={deleteConfirmOpen}
        title="Delete card"
        message="Are you sure you want to delete this card? This cannot be undone."
        confirmLabel="Delete"
        destructive
        onConfirm={handleDeleteConfirmed}
        onCancel={() => setDeleteConfirmOpen(false)}
      />

      {/* Lightbox: larger image, click or Escape to close */}
      {imageLightboxOpen && imageUrl && (
        <div
          className="fixed inset-0 z-[60] flex items-center justify-center bg-black/70 cursor-zoom-out p-4"
          onClick={e => {
            e.stopPropagation();
            setImageLightboxOpen(false);
          }}
          role="button"
          tabIndex={0}
          aria-label="Close enlarged image"
          onKeyDown={e => e.key === 'Enter' && setImageLightboxOpen(false)}
        >
          <img
            src={imageUrl}
            alt={displayName}
            className="max-w-[488px] max-h-[680px] w-auto h-auto object-contain rounded-lg shadow-2xl pointer-events-none"
            aria-hidden
          />
        </div>
      )}
    </div>
  );
}
