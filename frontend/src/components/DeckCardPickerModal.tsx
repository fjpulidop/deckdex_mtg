import { useState, useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { api, Card } from '../api/client';
import { ManaText } from './ManaText';
import { AccessibleModal } from './AccessibleModal';

const COLOR_IDS = ['W', 'U', 'B', 'R', 'G'] as const;

interface DeckCardPickerModalProps {
  deckId: number;
  onClose: () => void;
  onAdded: () => void;
}

type SortBy = 'name' | 'cmc_asc' | 'cmc_desc';

export function DeckCardPickerModal({ deckId, onClose, onAdded }: DeckCardPickerModalProps) {
  const { t } = useTranslation();
  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState('');
  const [filterColors, setFilterColors] = useState<Set<string>>(new Set());
  const [sortBy, setSortBy] = useState<SortBy>('name');
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [addPending, setAddPending] = useState(false);

  const TYPE_OPTIONS = [
    { value: '', label: t('deckCardPicker.anyType') },
    { value: 'Creature', label: t('deckCardPicker.types.creature') },
    { value: 'Instant', label: t('deckCardPicker.types.instant') },
    { value: 'Sorcery', label: t('deckCardPicker.types.sorcery') },
    { value: 'Enchantment', label: t('deckCardPicker.types.enchantment') },
    { value: 'Artifact', label: t('deckCardPicker.types.artifact') },
    { value: 'Planeswalker', label: t('deckCardPicker.types.planeswalker') },
    { value: 'Land', label: t('deckCardPicker.types.land') },
  ];

  const colorIdentityParam =
    filterColors.size > 0 ? Array.from(filterColors).sort().join(',') : undefined;

  const { data: cardsRaw = [], isLoading } = useQuery({
    queryKey: ['cards', 'picker', search, filterType, colorIdentityParam],
    queryFn: () =>
      api.getCards({
        search: search.trim() || undefined,
        type: filterType || undefined,
        color_identity: colorIdentityParam,
        limit: 200,
      }),
  });

  const cards = useMemo(() => {
    const list = [...cardsRaw];
    if (sortBy === 'name') {
      list.sort((a, b) => (a.name ?? '').localeCompare(b.name ?? ''));
    } else if (sortBy === 'cmc_asc') {
      list.sort((a, b) => (a.cmc ?? 0) - (b.cmc ?? 0));
    } else {
      list.sort((a, b) => (b.cmc ?? 0) - (a.cmc ?? 0));
    }
    return list;
  }, [cardsRaw, sortBy]);

  const toggleColor = useCallback((id: string) => {
    setFilterColors((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const toggle = useCallback((id: number) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const handleAdd = useCallback(async () => {
    if (selected.size === 0) return;
    setAddPending(true);
    try {
      for (const cardId of selected) {
        await api.addCardToDeck(deckId, cardId);
      }
      onAdded();
    } catch {
      // could toast
    } finally {
      setAddPending(false);
    }
  }, [deckId, selected, onAdded]);

  return (
    <AccessibleModal isOpen titleId="deck-card-picker-title" onClose={onClose} className="z-[60]" showCloseButton>
      <div
        className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-2xl w-full max-h-[80vh] flex flex-col overflow-hidden"
      >
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between gap-4">
          <h2 id="deck-card-picker-title" className="text-lg font-semibold text-gray-900 dark:text-white">
            {t('deckCardPicker.title')}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1.5 rounded border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            {t('deckCardPicker.cancel')}
          </button>
        </div>
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 space-y-3">
          <input
            type="text"
            placeholder={t('deckCardPicker.searchPlaceholder')}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full border border-gray-300 dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          />
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              <label htmlFor="picker-type" className="text-sm font-medium text-gray-600 dark:text-gray-400">
                {t('deckCardPicker.typeLabel')}
              </label>
              <select
                id="picker-type"
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="border border-gray-300 dark:border-gray-600 rounded px-2 py-1.5 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm min-w-[140px]"
              >
                {TYPE_OPTIONS.map((opt) => (
                  <option key={opt.value || 'any'} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">{t('deckCardPicker.colorsLabel')}</span>
              <div className="picker-color-symbols flex items-center gap-1">
                {COLOR_IDS.map((id) => {
                  const active = filterColors.has(id);
                  return (
                    <button
                      key={id}
                      type="button"
                      title={t(`filters.colors.${id}`)}
                      onClick={() => toggleColor(id)}
                      className={`inline-flex items-center justify-center p-0.5 rounded transition-opacity cursor-pointer focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                        active ? 'opacity-100 ring-2 ring-gray-800 dark:ring-gray-200' : 'opacity-50 hover:opacity-75'
                      }`}
                      aria-pressed={active}
                    >
                      <ManaText text={`{${id}}`} />
                    </button>
                  );
                })}
              </div>
              {filterColors.size > 0 && (
                <button
                  type="button"
                  onClick={() => setFilterColors(new Set())}
                  className="text-xs text-gray-500 dark:text-gray-400 hover:underline"
                >
                  {t('deckCardPicker.clear')}
                </button>
              )}
            </div>
            <div className="flex items-center gap-2">
              <label htmlFor="picker-sort" className="text-sm font-medium text-gray-600 dark:text-gray-400">
                {t('deckCardPicker.sortLabel')}
              </label>
              <select
                id="picker-sort"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as SortBy)}
                className="border border-gray-300 dark:border-gray-600 rounded px-2 py-1.5 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
              >
                <option value="name">{t('deckCardPicker.sortOptions.name')}</option>
                <option value="cmc_asc">{t('deckCardPicker.sortOptions.manaCostAsc')}</option>
                <option value="cmc_desc">{t('deckCardPicker.sortOptions.manaCostDesc')}</option>
              </select>
            </div>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-4 min-h-0">
          {isLoading && <p className="text-gray-500 dark:text-gray-400">{t('deckCardPicker.loading')}</p>}
          <ul className="space-y-1">
            {cards.map((card: Card) => {
              const id = card.id ?? 0;
              const isSelected = selected.has(id);
              return (
                <li key={id}>
                  <button
                    type="button"
                    onClick={() => toggle(id)}
                    className={`w-full flex items-center gap-2 py-2 px-3 rounded text-left ${
                      isSelected
                        ? 'bg-indigo-100 dark:bg-indigo-900/40 text-indigo-900 dark:text-indigo-100'
                        : 'hover:bg-gray-100 dark:hover:bg-gray-700/50 text-gray-900 dark:text-white'
                    }`}
                  >
                    <span className="flex-shrink-0 w-5 h-5 rounded border border-gray-400 dark:border-gray-500 flex items-center justify-center">
                      {isSelected ? '✓' : ''}
                    </span>
                    <span className="truncate min-w-0 flex-1">{card.name}</span>
                    {card.type && (
                      <span className="text-sm text-gray-500 dark:text-gray-400 truncate hidden sm:inline flex-shrink-0">
                        {card.type}
                      </span>
                    )}
                    {card.mana_cost != null && card.mana_cost !== '' && (
                      <span className="flex-shrink-0 inline-flex items-center [&_.card-symbol]:cursor-default ml-auto pl-2">
                        <ManaText text={card.mana_cost} className="text-sm" />
                      </span>
                    )}
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {t('deckCardPicker.selected', { count: selected.size })}
          </span>
          <button
            type="button"
            onClick={handleAdd}
            disabled={selected.size === 0 || addPending}
            className="px-4 py-2 rounded bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed dark:bg-indigo-500 dark:hover:bg-indigo-600"
          >
            {addPending ? t('deckCardPicker.adding') : t('deckCardPicker.addToDeck')}
          </button>
        </div>
      </div>
    </AccessibleModal>
  );
}
