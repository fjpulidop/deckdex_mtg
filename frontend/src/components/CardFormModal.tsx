import { useState, useEffect, useRef, useCallback } from 'react';
import { Card, api } from '../api/client';

const DEBOUNCE_MS = 280;
const MIN_QUERY_LENGTH = 2;

interface CardFormModalProps {
  title: string;
  mode: 'add' | 'edit';
  initial?: Partial<Card>;
  onSubmit: (payload: Partial<Card>) => Promise<void>;
  onClose: () => void;
}

type SuggestionSource = 'collection' | 'catalog';

interface SuggestionItem {
  source: SuggestionSource;
  name: string;
  card?: Card;
}

export function CardFormModal({ title, mode, initial, onSubmit, onClose }: CardFormModalProps) {
  const isAdd = mode === 'add';

  const [name, setName] = useState(initial?.name ?? '');
  const [type, setType] = useState(initial?.type ?? '');
  const [rarity, setRarity] = useState(initial?.rarity ?? '');
  const [price, setPrice] = useState(initial?.price ?? '');
  const [setNameVal, setSetNameVal] = useState(initial?.set_name ?? '');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Add-mode: autocomplete state
  const [query, setQuery] = useState('');
  const [collectionCards, setCollectionCards] = useState<Card[]>([]);
  const [catalogNames, setCatalogNames] = useState<string[]>([]);
  const [showCatalogSection, setShowCatalogSection] = useState(false);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const [selectedCardForAdd, setSelectedCardForAdd] = useState<Card | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setName(initial?.name ?? '');
    setType(initial?.type ?? '');
    setRarity(initial?.rarity ?? '');
    setPrice(initial?.price ?? '');
    setSetNameVal(initial?.set_name ?? '');
  }, [initial]);

  // Build flat list of suggestions for keyboard nav
  const collectionSuggestions: SuggestionItem[] = (collectionCards || []).map(c => ({
    source: 'collection',
    name: c.name ?? '',
    card: c,
  }));
  const catalogSuggestions: SuggestionItem[] = (catalogNames || [])
    .filter(n => !collectionSuggestions.some(s => s.name.toLowerCase() === n.toLowerCase()))
    .map(n => ({ source: 'catalog', name: n }));
  const allSuggestions = [...collectionSuggestions, ...catalogSuggestions];
  const showCatalog = showCatalogSection && catalogSuggestions.length > 0;

  const fetchCatalog = useCallback(async (q: string) => {
    if (q.trim().length < MIN_QUERY_LENGTH) {
      setCatalogNames([]);
      return;
    }
    try {
      const names = await api.getCardSuggest(q.trim());
      setCatalogNames(names);
    } catch {
      setCatalogNames([]);
    }
  }, []);

  useEffect(() => {
    if (!isAdd) return;
    const q = query.trim();
    setLoadingSuggestions(true);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      try {
        const list = q ? await api.getCards({ search: q, limit: 10 }) : [];
        setCollectionCards(list);
        if (q.length >= MIN_QUERY_LENGTH && (list.length === 0 || showCatalogSection)) {
          await fetchCatalog(q);
        } else {
          setCatalogNames([]);
        }
      } catch {
        setCollectionCards([]);
        setCatalogNames([]);
      }
      setLoadingSuggestions(false);
      debounceRef.current = null;
    }, DEBOUNCE_MS);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query, isAdd, showCatalogSection, fetchCatalog]);

  const handleSearchCatalog = useCallback(() => {
    setShowCatalogSection(true);
    const q = query.trim();
    if (q.length >= MIN_QUERY_LENGTH) {
      setLoadingSuggestions(true);
      api.getCardSuggest(q).then(names => {
        setCatalogNames(names);
        setLoadingSuggestions(false);
      }).catch(() => setLoadingSuggestions(false));
    }
  }, [query]);

  const selectSuggestion = useCallback(async (item: SuggestionItem) => {
    if (item.source === 'collection' && item.card) {
      setSelectedCardForAdd(item.card);
      setName(item.name);
      setDropdownOpen(false);
      setHighlightedIndex(-1);
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const resolved = await api.resolveCardByName(item.name);
      setSelectedCardForAdd(resolved);
      setName(resolved.name ?? item.name);
      setDropdownOpen(false);
      setHighlightedIndex(-1);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not resolve card');
    } finally {
      setSaving(false);
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      if (isAdd && selectedCardForAdd) {
        await onSubmit(selectedCardForAdd);
      } else if (isAdd && name.trim()) {
        const resolved = await api.resolveCardByName(name.trim());
        await onSubmit(resolved);
      } else if (!isAdd) {
        await onSubmit({
          name: name.trim() || undefined,
          type: type.trim() || undefined,
          rarity: rarity.trim() || undefined,
          price: price.trim() || undefined,
          set_name: setNameVal.trim() || undefined,
        });
      } else {
        setError('Select a card or enter a name and try again');
        setSaving(false);
        return;
      }
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed');
    } finally {
      setSaving(false);
    }
  };

  const onNameChange = (value: string) => {
    setName(value);
    if (isAdd) {
      setQuery(value);
      setDropdownOpen(true);
      setSelectedCardForAdd(null);
      setHighlightedIndex(-1);
    }
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (!isAdd || !dropdownOpen) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlightedIndex(i => (i < allSuggestions.length - 1 ? i + 1 : i));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlightedIndex(i => (i > 0 ? i - 1 : -1));
    } else if (e.key === 'Enter' && highlightedIndex >= 0 && allSuggestions[highlightedIndex]) {
      e.preventDefault();
      selectSuggestion(allSuggestions[highlightedIndex]);
    } else if (e.key === 'Escape') {
      setDropdownOpen(false);
      setHighlightedIndex(-1);
    }
  };

  useEffect(() => {
    const handleClickOutside = (ev: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(ev.target as Node) && inputRef.current && !inputRef.current.contains(ev.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4 p-6" onClick={e => e.stopPropagation()}>
        <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">{title}</h2>
        {error && <div className="mb-4 text-red-600 dark:text-red-400 text-sm">{error}</div>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div ref={dropdownRef} className="relative">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name *</label>
            <input
              ref={inputRef}
              type="text"
              value={name}
              onChange={e => onNameChange(e.target.value)}
              onFocus={() => isAdd && (query.trim() || allSuggestions.length > 0) && setDropdownOpen(true)}
              onKeyDown={onKeyDown}
              className="w-full border border-gray-300 dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              required
              autoComplete="off"
              role="combobox"
              aria-expanded={dropdownOpen}
              aria-autocomplete="list"
              aria-controls="card-suggestions-list"
              aria-activedescendant={highlightedIndex >= 0 && allSuggestions[highlightedIndex] ? `suggestion-${highlightedIndex}` : undefined}
            />
            {isAdd && dropdownOpen && (query.trim() || allSuggestions.length > 0) && (
              <ul
                id="card-suggestions-list"
                role="listbox"
                className="absolute z-10 left-0 right-0 mt-1 max-h-60 overflow-auto rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 shadow-lg"
              >
                {loadingSuggestions && allSuggestions.length === 0 && (
                  <li className="px-3 py-2 text-gray-500 dark:text-gray-400 text-sm">Loading…</li>
                )}
                {collectionSuggestions.length > 0 && (
                  <>
                    <li className="px-3 py-1.5 text-xs font-medium text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-600 sticky top-0">In your collection</li>
                    {collectionSuggestions.map((item, i) => {
                      const idx = allSuggestions.indexOf(item);
                      return (
                        <li
                          key={`c-${item.name}`}
                          id={idx === highlightedIndex ? `suggestion-${idx}` : undefined}
                          role="option"
                          aria-selected={idx === highlightedIndex}
                          className={`px-3 py-2 cursor-pointer text-gray-900 dark:text-white ${idx === highlightedIndex ? 'bg-blue-100 dark:bg-blue-900' : 'hover:bg-gray-100 dark:hover:bg-gray-600'}`}
                          onMouseDown={e => { e.preventDefault(); selectSuggestion(item); }}
                        >
                          {item.name}
                        </li>
                      );
                    })}
                  </>
                )}
                {(showCatalog || catalogSuggestions.length > 0) && (
                  <>
                    <li className="px-3 py-1.5 text-xs font-medium text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-600 sticky top-0">Other cards</li>
                    {catalogSuggestions.map((item, i) => {
                      const idx = allSuggestions.indexOf(item);
                      return (
                        <li
                          key={`s-${item.name}`}
                          id={idx === highlightedIndex ? `suggestion-${idx}` : undefined}
                          role="option"
                          aria-selected={idx === highlightedIndex}
                          className={`px-3 py-2 cursor-pointer text-gray-900 dark:text-white ${idx === highlightedIndex ? 'bg-blue-100 dark:bg-blue-900' : 'hover:bg-gray-100 dark:hover:bg-gray-600'}`}
                          onMouseDown={e => { e.preventDefault(); selectSuggestion(item); }}
                        >
                          {item.name}
                        </li>
                      );
                    })}
                  </>
                )}
                {!loadingSuggestions && query.trim().length >= MIN_QUERY_LENGTH && collectionSuggestions.length > 0 && !showCatalog && (
                  <li className="border-t border-gray-200 dark:border-gray-600">
                    <button
                      type="button"
                      className="w-full text-left px-3 py-2 text-sm text-blue-600 dark:text-blue-400 hover:bg-gray-100 dark:hover:bg-gray-600"
                      onMouseDown={e => { e.preventDefault(); handleSearchCatalog(); }}
                    >
                      Search catalog for “{query.trim()}”
                    </button>
                  </li>
                )}
              </ul>
            )}
          </div>

          {!isAdd && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Type</label>
                <input
                  type="text"
                  value={type}
                  onChange={e => setType(e.target.value)}
                  className="w-full border border-gray-300 dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Rarity</label>
                <input
                  type="text"
                  value={rarity}
                  onChange={e => setRarity(e.target.value)}
                  className="w-full border border-gray-300 dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Price</label>
                <input
                  type="text"
                  value={price}
                  onChange={e => setPrice(e.target.value)}
                  className="w-full border border-gray-300 dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Set</label>
                <input
                  type="text"
                  value={setNameVal}
                  onChange={e => setSetNameVal(e.target.value)}
                  className="w-full border border-gray-300 dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
            </>
          )}

          <div className="flex gap-2 justify-end pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-200">
              Cancel
            </button>
            <button type="submit" disabled={saving} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 dark:bg-blue-500 dark:hover:bg-blue-600">
              {saving ? 'Saving…' : isAdd ? 'Add' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
