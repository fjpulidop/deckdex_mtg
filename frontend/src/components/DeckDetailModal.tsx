import { useState, useCallback, useMemo, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell } from 'recharts';
import { api, DeckCard, DeckImportResponse } from '../api/client';
import { useCardImage } from '../hooks/useCardImage';
import { DeckCardPickerModal } from './DeckCardPickerModal';
import { CardDetailModal } from './CardDetailModal';
import { ConfirmModal } from './ConfirmModal';
import { ManaText } from './ManaText';
import { DeckImportModal } from './DeckImportModal';
import { AccessibleModal } from './AccessibleModal';

function parsePrice(price: string | undefined): number {
  if (price == null || price === '' || price === 'N/A') return 0;
  const s = String(price).replace(/,/g, '.').trim();
  const n = parseFloat(s);
  return Number.isFinite(n) ? n : 0;
}

function formatDeckCurrency(value: number): string {
  return new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', minimumFractionDigits: 2 }).format(value);
}

function cmcBucket(cmc: number | undefined): number {
  if (cmc == null || !Number.isFinite(cmc)) return 0;
  const n = Math.floor(Number(cmc));
  return n >= 7 ? 7 : Math.max(0, n);
}

function isLegendaryCreature(card: DeckCard): boolean {
  const t = (card.type ?? '').toLowerCase();
  return t.includes('legendary') && t.includes('creature');
}

const SECTION_ORDER = [
  'Commander',
  'Creature',
  'Sorcery',
  'Instant',
  'Enchantment',
  'Artifact',
  'Planeswalker',
  'Land',
  'Other',
];

function sectionFromType(type: string | undefined, isCommander: boolean): string {
  if (isCommander) return 'Commander';
  if (!type || !type.trim()) return 'Other';
  const first = type.split('—')[0].trim();
  if (/Creature/i.test(first)) return 'Creature';
  if (/Sorcery/i.test(first)) return 'Sorcery';
  if (/Instant/i.test(first)) return 'Instant';
  if (/Enchantment/i.test(first)) return 'Enchantment';
  if (/Artifact/i.test(first)) return 'Artifact';
  if (/Planeswalker/i.test(first)) return 'Planeswalker';
  if (/Land/i.test(first)) return 'Land';
  return 'Other';
}

function groupCardsBySection(cards: DeckCard[]): Map<string, DeckCard[]> {
  const map = new Map<string, DeckCard[]>();
  for (const card of cards) {
    const section = sectionFromType(card.type, !!card.is_commander);
    if (!map.has(section)) map.set(section, []);
    map.get(section)!.push(card);
  }
  return map;
}

interface DeckDetailModalProps {
  deckId: number;
  onClose: () => void;
  onDeleted: () => void;
}

export function DeckDetailModal({ deckId, onClose, onDeleted }: DeckDetailModalProps) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [pickerOpen, setPickerOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [copyFeedback, setCopyFeedback] = useState(false);
  const [deleteDeckConfirmOpen, setDeleteDeckConfirmOpen] = useState(false);
  const [hoverCardId, setHoverCardId] = useState<number | null>(null);
  const [detailCard, setDetailCard] = useState<DeckCard | null>(null);
  const [nameEdit, setNameEdit] = useState<string | null>(null);
  const [saveNamePending, setSaveNamePending] = useState(false);
  const [setCommanderPending, setSetCommanderPending] = useState<number | null>(null);
  const [imageLightboxOpen, setImageLightboxOpen] = useState(false);
  const [filterByCmc, setFilterByCmc] = useState<number | null>(null);

  const { data: deck, isLoading, error, refetch } = useQuery({
    queryKey: ['deck', deckId],
    queryFn: () => api.getDeck(deckId),
  });

  const totalDeckValue = useMemo(() => {
    if (!deck?.cards) return 0;
    return deck.cards.reduce((sum, c) => sum + parsePrice(c.price) * (c.quantity ?? 1), 0);
  }, [deck?.cards]);

  const manaCurveData = useMemo(() => {
    if (!deck?.cards) return [];
    const counts: Record<number, number> = { 0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0 };
    for (const c of deck.cards) {
      const bucket = cmcBucket(c.cmc);
      counts[bucket] = (counts[bucket] ?? 0) + (c.quantity ?? 1);
    }
    return [0, 1, 2, 3, 4, 5, 6, 7].map((cmc) => ({
      cmc: cmc === 7 ? '7+' : String(cmc),
      cmcKey: cmc,
      count: counts[cmc] ?? 0,
    }));
  }, [deck?.cards]);

  const filteredCards = useMemo(() => {
    if (!deck?.cards) return [];
    if (filterByCmc == null) return deck.cards;
    return deck.cards.filter((c) => cmcBucket(c.cmc) === filterByCmc);
  }, [deck?.cards, filterByCmc]);

  const sections = useMemo(() => {
    if (filteredCards.length === 0) return [];
    const grouped = groupCardsBySection(filteredCards);
    return SECTION_ORDER.filter((s) => grouped.has(s)).map((s) => ({
      title: s,
      cards: grouped.get(s)!,
    }));
  }, [filteredCards]);

  const displayName = nameEdit !== null ? nameEdit : deck?.name ?? '';
  const commanderOrFirst = deck?.cards?.find((c) => c.is_commander) ?? deck?.cards?.[0]; // use full list for preview
  const hoverCard = deck?.cards?.find((c) => c.id === hoverCardId);
  const previewCard = hoverCard ?? commanderOrFirst;
  const bigImageCardId = previewCard?.id ?? null;
  const { src: bigImageUrl } = useCardImage(bigImageCardId);
  const bigImagePrice = previewCard
    ? (previewCard.price != null && previewCard.price !== 'N/A' ? `€${previewCard.price}` : 'N/A')
    : null;

  const handleDelete = useCallback(() => {
    setDeleteDeckConfirmOpen(true);
  }, []);

  const handleDeleteDeckConfirmed = useCallback(async () => {
    setDeleteDeckConfirmOpen(false);
    try {
      await api.deleteDeck(deckId);
      onDeleted();
    } catch {
      // could toast
    }
  }, [deckId, onDeleted]);

  const handleRemoveCard = useCallback(
    async (cardId: number) => {
      try {
        await api.removeCardFromDeck(deckId, cardId);
        await queryClient.invalidateQueries({ queryKey: ['deck', deckId] });
      } catch {
        // could toast
      }
    },
    [deckId, queryClient]
  );

  const handleSaveName = useCallback(async () => {
    if (nameEdit === null || nameEdit === deck?.name) {
      setNameEdit(null);
      return;
    }
    setSaveNamePending(true);
    try {
      await api.updateDeck(deckId, { name: nameEdit });
      await queryClient.invalidateQueries({ queryKey: ['deck', deckId] });
      await queryClient.invalidateQueries({ queryKey: ['decks'] });
      setNameEdit(null);
    } catch {
      // could toast
    } finally {
      setSaveNamePending(false);
    }
  }, [deckId, deck?.name, nameEdit, queryClient]);

  const handleCardsAdded = useCallback(() => {
    setPickerOpen(false);
    refetch();
  }, [refetch]);

  const handleExport = useCallback(() => {
    if (!deck?.cards) return;

    const commanders = deck.cards.filter((c) => c.is_commander);
    const mainboard = deck.cards.filter((c) => !c.is_commander);

    const lines: string[] = [];
    if (commanders.length > 0) {
      lines.push('//Commander');
      for (const c of commanders) {
        lines.push(`${c.quantity ?? 1} ${c.name}`);
      }
      lines.push('');
    }
    if (mainboard.length > 0) {
      lines.push('//Mainboard');
      for (const c of mainboard) {
        lines.push(`${c.quantity ?? 1} ${c.name}`);
      }
    }

    const text = lines.join('\n');
    navigator.clipboard.writeText(text).then(() => {
      setCopyFeedback(true);
      setTimeout(() => setCopyFeedback(false), 2000);
    });
  }, [deck?.cards]);

  const handleImported = useCallback(
    (result: DeckImportResponse) => {
      // Update the deck detail cache immediately with the returned data
      queryClient.setQueryData(['deck', deckId], result.deck);
      // Refresh the deck list to update card counts
      queryClient.invalidateQueries({ queryKey: ['decks'] });
      setImportOpen(false);
    },
    [deckId, queryClient]
  );

  const handleSetCommander = useCallback(
    async (e: React.MouseEvent, cardId: number) => {
      e.stopPropagation();
      setSetCommanderPending(cardId);
      try {
        await api.setDeckCardCommander(deckId, cardId);
        await queryClient.invalidateQueries({ queryKey: ['deck', deckId] });
      } catch {
        // could toast
      } finally {
        setSetCommanderPending(null);
      }
    },
    [deckId, queryClient]
  );

  const handleCardDetailClose = useCallback(() => {
    setDetailCard(null);
    refetch();
  }, [refetch]);

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

  if (error) {
    return (
      <AccessibleModal isOpen titleId="deck-detail-error-title" onClose={onClose} className="z-50">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md shadow-xl">
          <p id="deck-detail-error-title" role="alert" className="text-red-600 dark:text-red-400">{error instanceof Error ? error.message : t('deckDetail.failedToLoad')}</p>
          <button type="button" onClick={onClose} className="mt-4 text-blue-600 dark:text-blue-400 hover:underline">
            {t('deckDetail.close')}
          </button>
        </div>
      </AccessibleModal>
    );
  }

  return (
    <>
      <AccessibleModal isOpen titleId="deck-detail-modal-title" onClose={onClose} className="z-50">
        <div
          className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden"
        >
          <div className="border-b border-gray-200 dark:border-gray-700 p-4">
            <div className="flex flex-wrap items-center gap-3 sm:gap-4">
              {/* Title */}
              <div className="flex items-center gap-2 min-w-0 shrink-0">
                {nameEdit !== null ? (
                  <input
                    id="deck-detail-modal-title"
                    type="text"
                    value={nameEdit}
                    onChange={(e) => setNameEdit(e.target.value)}
                    onBlur={handleSaveName}
                    onKeyDown={(e) => e.key === 'Enter' && handleSaveName()}
                    className="border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-lg font-semibold"
                    autoFocus
                  />
                ) : (
                  <button
                    id="deck-detail-modal-title"
                    type="button"
                    onClick={() => deck && setNameEdit(deck.name)}
                    className="text-lg font-semibold text-gray-900 dark:text-white hover:underline truncate"
                  >
                    {displayName}
                  </button>
                )}
                {saveNamePending && <span className="text-sm text-gray-500">{t('deckDetail.saving')}</span>}
              </div>
              {/* Total value */}
              <div className="flex items-center shrink-0">
                <span className="text-sm font-medium text-gray-500 dark:text-gray-400">{t('deckDetail.total')}</span>
                <span className="ml-1.5 text-base font-bold text-green-600 dark:text-green-400">
                  {formatDeckCurrency(totalDeckValue)}
                </span>
              </div>
              {/* Mana curve — wrapper + CSS ensure axis labels visible in dark mode */}
              <div className="deck-detail-mana-curve flex items-center gap-1.5 flex-1 min-w-[140px] h-8 shrink-0 text-gray-600 dark:text-gray-200">
                <div className="flex-1 min-w-0 h-full max-w-[200px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={manaCurveData} margin={{ top: 0, right: 2, bottom: 0, left: 2 }}>
                      <XAxis
                        dataKey="cmc"
                        tick={{ fontSize: 9, fill: 'currentColor' }}
                        tickLine={false}
                      />
                      <YAxis hide domain={[0, 'auto']} />
                      <Bar
                        dataKey="count"
                        radius={[3, 3, 0, 0]}
                        cursor="pointer"
                        onClick={(_, idx) => {
                          const entry = manaCurveData[idx];
                          if (entry) {
                            const next = filterByCmc === entry.cmcKey ? null : entry.cmcKey;
                            setFilterByCmc(next);
                          }
                        }}
                      >
                        {manaCurveData.map((entry, idx) => (
                          <Cell
                            key={idx}
                            fill={filterByCmc == null || filterByCmc === entry.cmcKey ? '#6366f1' : '#94a3b8'}
                            opacity={filterByCmc != null && filterByCmc !== entry.cmcKey ? 0.4 : 1}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <span className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">{t('deckDetail.cmc')}</span>
              </div>
              {/* CMC filter chip */}
              {filterByCmc != null && (
                <button
                  type="button"
                  onClick={() => setFilterByCmc(null)}
                  className="shrink-0 text-xs px-2 py-1 rounded bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-500"
                >
                  CMC {filterByCmc === 7 ? '7+' : filterByCmc} ×
                </button>
              )}
              {/* Buttons */}
              <div className="flex items-center gap-2 shrink-0 ml-auto">
                <button
                  type="button"
                  onClick={handleExport}
                  className="px-3 py-1.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600 text-sm font-medium"
                >
                  {copyFeedback ? t('deckDetail.copied') : t('deckDetail.export')}
                </button>
                <button
                  type="button"
                  onClick={() => setImportOpen(true)}
                  className="px-3 py-1.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600 text-sm font-medium"
                >
                  {t('deckDetail.import')}
                </button>
                <button
                  type="button"
                  onClick={() => setPickerOpen(true)}
                  className="px-3 py-1.5 rounded bg-indigo-600 text-white hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600 text-sm font-medium"
                >
                  {t('deckDetail.addCard')}
                </button>
                <button
                  type="button"
                  onClick={handleDelete}
                  className="px-3 py-1.5 rounded bg-red-600 text-white hover:bg-red-700 dark:bg-red-500 dark:hover:bg-red-600 text-sm font-medium"
                >
                  {t('deckDetail.deleteDeck')}
                </button>
              </div>
            </div>
          </div>

          <div className="flex flex-1 overflow-hidden min-h-0">
            <div className="w-64 flex-shrink-0 border-r border-gray-200 dark:border-gray-700 flex flex-col items-center justify-start bg-gray-50 dark:bg-gray-900/50 p-4 overflow-visible">
              {bigImageUrl ? (
                <>
                  <div
                    role="button"
                    tabIndex={0}
                    onClick={() => setImageLightboxOpen(true)}
                    onKeyDown={(e) => e.key === 'Enter' && setImageLightboxOpen(true)}
                    className="cursor-zoom-in inline-block"
                    aria-label={t('deckDetail.hoverCard')}
                  >
                    <img
                      src={bigImageUrl}
                      alt="Card"
                      className="max-w-full max-h-[280px] object-contain rounded-lg shadow"
                    />
                  </div>
                  {bigImagePrice != null && (
                    <p className="mt-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                      {bigImagePrice}
                    </p>
                  )}
                </>
              ) : (
                <div className="text-gray-400 dark:text-gray-500 text-sm text-center">
                  {isLoading ? t('deckDetail.loading') : t('deckDetail.hoverCard')}
                </div>
              )}
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              {isLoading && <p className="text-gray-500 dark:text-gray-400">{t('deckDetail.loading')}</p>}
              {!isLoading && sections.length === 0 && (
                <p className="text-gray-500 dark:text-gray-400">{t('deckDetail.noCards')}</p>
              )}
              {sections.map(({ title, cards: sectionCards }) => (
                <div key={title} className="mb-6">
                  <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">
                    {title} ({sectionCards.length})
                  </h3>
                  <ul className="space-y-1">
                    {sectionCards.map((card) => {
                      const qty = card.quantity ?? 1;
                      const showSetCommander =
                        isLegendaryCreature(card) && !card.is_commander && card.id != null;
                      return (
                        <li
                          key={card.id}
                          onMouseEnter={() => card.id != null && setHoverCardId(card.id)}
                          onMouseLeave={() => setHoverCardId(null)}
                          className="flex items-center gap-2 py-1 px-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700/50 group"
                        >
                          <span className="w-6 text-right text-gray-500 dark:text-gray-400 text-sm tabular-nums flex-shrink-0">
                            {qty}
                          </span>
                          <button
                            type="button"
                            onClick={() => card && setDetailCard(card)}
                            className="flex-1 min-w-0 text-left truncate text-gray-900 dark:text-white hover:underline"
                          >
                            {card.name}
                          </button>
                          {card.mana_cost && (
                            <span className="flex-shrink-0 card-symbols-inline">
                              <ManaText text={card.mana_cost} className="text-sm" />
                            </span>
                          )}
                          {showSetCommander && (
                            <button
                              type="button"
                              onClick={(e) => card.id != null && handleSetCommander(e, card.id)}
                              disabled={setCommanderPending === card.id}
                              className="flex-shrink-0 px-2 py-0.5 text-xs rounded bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-200 hover:bg-amber-200 dark:hover:bg-amber-800/50 disabled:opacity-50"
                            >
                              {setCommanderPending === card.id ? '…' : t('deckDetail.setAsCommander')}
                            </button>
                          )}
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              if (card.id != null) handleRemoveCard(card.id);
                            }}
                            className="opacity-0 group-hover:opacity-100 text-red-600 hover:text-red-700 dark:text-red-400 p-1 rounded flex-shrink-0"
                            aria-label={`Remove ${card.name}`}
                          >
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </div>
      </AccessibleModal>

      {/* Lightbox: image large, click or Escape to close */}
      {imageLightboxOpen && bigImageUrl && (
        <div
          className="fixed inset-0 z-[60] flex items-center justify-center bg-black/70 cursor-zoom-out p-4"
          onClick={() => setImageLightboxOpen(false)}
          role="button"
          tabIndex={0}
          aria-label={t('deckDetail.close')}
          onKeyDown={(e) => e.key === 'Enter' && setImageLightboxOpen(false)}
        >
          <img
            src={bigImageUrl}
            alt="Card"
            className="max-w-[90vw] max-h-[90vh] w-auto h-auto object-contain rounded-lg shadow-2xl pointer-events-none"
            aria-hidden
          />
        </div>
      )}

      {pickerOpen && (
        <DeckCardPickerModal
          deckId={deckId}
          onClose={() => setPickerOpen(false)}
          onAdded={handleCardsAdded}
        />
      )}

      {importOpen && (
        <DeckImportModal
          deckId={deckId}
          onClose={() => setImportOpen(false)}
          onImported={handleImported}
        />
      )}

      {detailCard && (
        <CardDetailModal
          card={detailCard}
          onClose={handleCardDetailClose}
          onCardUpdated={(updated) => {
            refetch();
            setDetailCard((prev) => (prev?.id === updated.id ? { ...prev, ...updated } as DeckCard : prev));
          }}
          onCardDeleted={handleCardDetailClose}
        />
      )}

      <ConfirmModal
        isOpen={deleteDeckConfirmOpen}
        title={t('deckDetail.deleteConfirmTitle')}
        message={t('deckDetail.deleteConfirmMessage', { name: displayName })}
        confirmLabel={t('deckDetail.deleteConfirm')}
        destructive
        onConfirm={handleDeleteDeckConfirmed}
        onCancel={() => setDeleteDeckConfirmOpen(false)}
      />
    </>
  );
}
