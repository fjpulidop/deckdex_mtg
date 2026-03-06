/**
 * Import page — 6-step wizard for importing cards from external apps.
 * Route: /import (ProtectedRoute)
 *
 * Steps: upload → resolve → review → mode → progress → result
 */
import { useState, useRef, useEffect, useCallback } from 'react';
import { useTranslation, Trans } from 'react-i18next';
import { useNavigate, useLocation } from 'react-router-dom';
import { api, ResolvedCardItem, ResolveResponse } from '../api/client';
import { useActiveJobs } from '../contexts/ActiveJobsContext';

type Step = 'upload' | 'resolve' | 'review' | 'mode' | 'progress' | 'result';
type Mode = 'merge' | 'replace';
type InputMode = 'file' | 'text';

const STEPS: Step[] = ['upload', 'resolve', 'review', 'mode', 'progress', 'result'];

interface ImportResult {
  imported: number;
  skipped: number;
  not_found: string[];
  mode: string;
  format: string;
  card_count?: number;
}

// Per-card correction state for the review step
interface CardCorrection {
  action: 'accept_suggestion' | 'manual' | 'skip';
  selectedName: string; // the suggestion or manual name chosen
}

const FORMAT_PROPER_NAMES: Record<string, string> = {
  moxfield: 'Moxfield',
  tappedout: 'TappedOut',
  mtgo: 'MTGO',
};

// ---------------------------------------------------------------------------
// Autocomplete input for manual card name entry
// ---------------------------------------------------------------------------
function AutocompleteInput({
  value,
  onChange,
  placeholder,
}: {
  value: string;
  onChange: (name: string) => void;
  placeholder: string;
}) {
  const [query, setQuery] = useState(value);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [open, setOpen] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout>>();

  const fetchSuggestions = useCallback(async (q: string) => {
    if (q.length < 2) { setSuggestions([]); return; }
    try {
      const results = await api.getCardSuggest(q);
      setSuggestions(results.slice(0, 6));
      setOpen(true);
    } catch { setSuggestions([]); }
  }, []);

  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => fetchSuggestions(query), 300);
    return () => { if (timerRef.current) clearTimeout(timerRef.current); };
  }, [query, fetchSuggestions]);

  return (
    <div className="relative">
      <input
        type="text"
        value={query}
        onChange={e => { setQuery(e.target.value); onChange(e.target.value); }}
        onFocus={() => suggestions.length > 0 && setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 200)}
        placeholder={placeholder}
        className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm text-gray-800 dark:text-gray-100 px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      {open && suggestions.length > 0 && (
        <ul className="absolute z-10 mt-1 w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg shadow-lg max-h-40 overflow-y-auto">
          {suggestions.map(s => (
            <li
              key={s}
              onMouseDown={() => { setQuery(s); onChange(s); setOpen(false); }}
              className="px-3 py-1.5 text-sm text-gray-700 dark:text-gray-200 hover:bg-blue-50 dark:hover:bg-blue-900/30 cursor-pointer"
            >
              {s}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------
export default function Import() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { addJob } = useActiveJobs();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const getFormatLabel = (format: string) =>
    FORMAT_PROPER_NAMES[format] ?? (format === 'generic' ? t('import.formatGeneric') : format);

  // Wizard state
  const [step, setStep] = useState<Step>('upload');
  const [inputMode, setInputMode] = useState<InputMode>('file');
  const [file, setFile] = useState<File | null>(null);
  const [pastedText, setPastedText] = useState('');
  const [resolveData, setResolveData] = useState<ResolveResponse | null>(null);
  const [corrections, setCorrections] = useState<Record<number, CardCorrection>>({});
  const [mode, setMode] = useState<Mode>('merge');
  const [result, setResult] = useState<ImportResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showMatched, setShowMatched] = useState(false);
  const [showNotFound, setShowNotFound] = useState(false);

  // Accept pre-resolved data from route state (e.g. from ImportListModal)
  useEffect(() => {
    const state = location.state as { resolveData?: ResolveResponse } | null;
    if (state?.resolveData) {
      setResolveData(state.resolveData);
      setCorrections({});
      setStep('review');
      window.history.replaceState({}, '');
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Step indicator helper
  const stepIndex = (s: Step) => STEPS.indexOf(s);

  // ---- Step 1 → 2: upload triggers resolve ----
  const handleFileSelect = async (selected: File) => {
    setFile(selected);
    setError(null);
    setLoading(true);
    setStep('resolve');
    try {
      const data = await api.importResolve(selected);
      setResolveData(data);
      setCorrections({});
      setStep('review');
    } catch (e) {
      setError(e instanceof Error ? e.message : t('import.errorParsingFile'));
      setStep('upload');
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const f = e.dataTransfer.files[0];
    if (f) handleFileSelect(f);
  };

  const handleTextResolve = async () => {
    if (!pastedText.trim()) return;
    setError(null);
    setLoading(true);
    setStep('resolve');
    try {
      const data = await api.importResolve(undefined, pastedText);
      setResolveData(data);
      setCorrections({});
      setStep('review');
    } catch (e) {
      setError(e instanceof Error ? e.message : t('import.errorParsingText'));
      setStep('upload');
    } finally {
      setLoading(false);
    }
  };

  // ---- Review step helpers ----
  const unresolvedCards = resolveData?.cards
    .map((c, i) => ({ card: c, index: i }))
    .filter(({ card }) => card.status !== 'matched') ?? [];

  const setCorrection = (index: number, correction: CardCorrection) => {
    setCorrections(prev => ({ ...prev, [index]: correction }));
  };

  const acceptAllSuggestions = () => {
    const next: Record<number, CardCorrection> = { ...corrections };
    for (const { card, index } of unresolvedCards) {
      if (card.suggestions.length > 0) {
        next[index] = { action: 'accept_suggestion', selectedName: card.suggestions[0] };
      }
    }
    setCorrections(next);
  };

  const skipAllUnresolved = () => {
    const next: Record<number, CardCorrection> = { ...corrections };
    for (const { index } of unresolvedCards) {
      next[index] = { action: 'skip', selectedName: '' };
    }
    setCorrections(next);
  };

  // ---- Build final card list from review state ----
  const buildCorrectedCards = (): { name: string; quantity: number; set_name?: string | null }[] => {
    if (!resolveData) return [];
    const result: { name: string; quantity: number; set_name?: string | null }[] = [];
    for (let i = 0; i < resolveData.cards.length; i++) {
      const card = resolveData.cards[i];
      if (card.status === 'matched') {
        result.push({ name: card.resolved_name!, quantity: card.quantity, set_name: card.set_name });
        continue;
      }
      const correction = corrections[i];
      if (!correction || correction.action === 'skip') continue;
      if (correction.selectedName.trim()) {
        result.push({ name: correction.selectedName, quantity: card.quantity, set_name: card.set_name });
      }
    }
    return result;
  };

  // ---- Step 4 → 5 → 6: launch import job ----
  const handleImport = async () => {
    const cards = buildCorrectedCards();
    if (cards.length === 0) return;
    setLoading(true);
    setError(null);
    setStep('progress');
    try {
      const res = await api.importExternalFromCards(cards, mode);
      addJob(res.job_id, `Import (${getFormatLabel(res.format)})`, () => {});
      setResult({ imported: res.card_count, skipped: 0, not_found: [], mode: res.mode, format: res.format, card_count: res.card_count });
      setStep('result');
    } catch (e) {
      setError(e instanceof Error ? e.message : t('import.errorParsingFile'));
      setStep('mode');
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setStep('upload');
    setFile(null);
    setPastedText('');
    setResolveData(null);
    setCorrections({});
    setResult(null);
    setError(null);
    setShowMatched(false);
    setShowNotFound(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="relative min-h-screen py-12 px-4">
      <div className="max-w-xl mx-auto">
        <div className="mb-8">
          <button onClick={() => navigate('/dashboard')} className="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
            {t('import.backToDashboard')}
          </button>
          <h1 className="mt-2 text-2xl font-bold text-gray-900 dark:text-white">{t('import.title')}</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{t('import.subtitle')}</p>
        </div>

        {/* Step indicator */}
        <div className="flex items-center gap-2 mb-8">
          {STEPS.map((s, i) => (
            <div key={s} className="flex items-center gap-2">
              <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
                step === s
                  ? 'bg-blue-600 text-white'
                  : stepIndex(step) > stepIndex(s)
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-400'
              }`}>
                {i + 1}
              </div>
              {i < STEPS.length - 1 && <div className="w-6 h-0.5 bg-gray-200 dark:bg-gray-700" />}
            </div>
          ))}
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-lg text-sm">{error}</div>
        )}

        {/* Step 1: Upload */}
        {step === 'upload' && (
          <div className="space-y-4">
            <div className="flex rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
              <button
                onClick={() => setInputMode('file')}
                className={`flex-1 py-2 text-sm font-medium transition ${inputMode === 'file' ? 'bg-blue-600 text-white' : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'}`}
              >
                {t('import.tabFile')}
              </button>
              <button
                onClick={() => setInputMode('text')}
                className={`flex-1 py-2 text-sm font-medium transition ${inputMode === 'text' ? 'bg-blue-600 text-white' : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'}`}
              >
                {t('import.tabText')}
              </button>
            </div>

            {inputMode === 'file' ? (
              <div
                onDrop={handleDrop}
                onDragOver={e => e.preventDefault()}
                className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl p-12 text-center hover:border-blue-400 transition"
              >
                <div className="text-4xl mb-4">📁</div>
                <p className="text-gray-600 dark:text-gray-300 mb-4">{t('import.dropzone')}</p>
                <label className="cursor-pointer">
                  <span className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm">
                    {loading ? t('common.loading') : t('import.selectFile')}
                  </span>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv,.txt"
                    className="sr-only"
                    onChange={e => { const f = e.target.files?.[0]; if (f) handleFileSelect(f); }}
                  />
                </label>
                <p className="mt-4 text-xs text-gray-400">{t('import.formatHints')}</p>
              </div>
            ) : (
              <div className="space-y-3">
                <textarea
                  value={pastedText}
                  onChange={e => setPastedText(e.target.value)}
                  placeholder={t('import.pastePlaceholder')}
                  rows={10}
                  className="w-full rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm text-gray-800 dark:text-gray-100 p-4 font-mono resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-400">
                  <Trans i18nKey="import.pasteHint" components={{ 1: <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded" /> }} />
                </p>
                <button
                  onClick={handleTextResolve}
                  disabled={loading || !pastedText.trim()}
                  className="w-full py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50 transition"
                >
                  {loading ? t('import.analyzing') : t('import.continue')}
                </button>
              </div>
            )}
          </div>
        )}

        {/* Step 2: Resolve (loading) */}
        {step === 'resolve' && (
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-600 p-8 text-center space-y-4">
            <div className="flex justify-center">
              <div className="w-10 h-10 border-4 border-gray-200 dark:border-gray-600 border-t-blue-600 rounded-full animate-spin" />
            </div>
            <p className="text-gray-700 dark:text-gray-300">{t('import.resolving')}</p>
            <p className="text-sm text-gray-400">{t('import.resolvingHint')}</p>
          </div>
        )}

        {/* Step 3: Review */}
        {step === 'review' && resolveData && (
          <div className="space-y-4">
            {/* Summary */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-600 p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 rounded-full text-sm font-medium">
                    {getFormatLabel(resolveData.format)}
                  </span>
                  <span className="text-sm text-gray-600 dark:text-gray-300">
                    {t('import.cardsDetected', { count: resolveData.total })}
                  </span>
                </div>
              </div>
              <div className="mt-3 flex items-center gap-4 text-sm">
                <span className="text-green-600 dark:text-green-400">
                  {t('import.reviewMatched', { count: resolveData.matched_count })}
                </span>
                {resolveData.unresolved_count > 0 && (
                  <span className="text-orange-600 dark:text-orange-400">
                    {t('import.reviewUnresolved', { count: resolveData.unresolved_count })}
                  </span>
                )}
              </div>
            </div>

            {/* All matched — fast path */}
            {unresolvedCards.length === 0 && (
              <div className="bg-green-50 dark:bg-green-900/20 rounded-xl border border-green-200 dark:border-green-800 p-4 text-sm text-green-700 dark:text-green-300">
                {t('import.reviewAllMatched')}
              </div>
            )}

            {/* Unresolved cards */}
            {unresolvedCards.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl border border-orange-200 dark:border-orange-800 overflow-hidden">
                <div className="px-4 py-3 bg-orange-50 dark:bg-orange-900/20 border-b border-orange-200 dark:border-orange-800 flex items-center justify-between">
                  <span className="text-sm font-medium text-orange-700 dark:text-orange-300">
                    {t('import.reviewNeedsAttention')} ({unresolvedCards.length})
                  </span>
                  <div className="flex gap-2">
                    <button
                      onClick={acceptAllSuggestions}
                      className="text-xs px-2 py-1 bg-orange-100 dark:bg-orange-900/40 text-orange-700 dark:text-orange-300 rounded hover:bg-orange-200 dark:hover:bg-orange-800 transition"
                    >
                      {t('import.reviewAcceptAll')}
                    </button>
                    <button
                      onClick={skipAllUnresolved}
                      className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition"
                    >
                      {t('import.reviewSkipAll')}
                    </button>
                  </div>
                </div>
                <div className="divide-y divide-gray-100 dark:divide-gray-700 max-h-96 overflow-y-auto">
                  {unresolvedCards.map(({ card, index }) => (
                    <UnresolvedCardRow
                      key={index}
                      card={card}
                      correction={corrections[index]}
                      onChange={c => setCorrection(index, c)}
                      t={t}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Matched cards (collapsible) */}
            {resolveData.matched_count > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-600 overflow-hidden">
                <button
                  onClick={() => setShowMatched(v => !v)}
                  className="w-full px-4 py-3 flex items-center justify-between text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition"
                >
                  <span>{t('import.reviewMatchedSection')} ({resolveData.matched_count})</span>
                  <span>{showMatched ? '▲' : '▼'}</span>
                </button>
                {showMatched && (
                  <div className="px-4 pb-3 max-h-48 overflow-y-auto">
                    <div className="flex flex-wrap gap-1.5">
                      {resolveData.cards.filter(c => c.status === 'matched').map((c, i) => (
                        <span key={i} className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 px-2 py-0.5 rounded">
                          {c.resolved_name} {c.quantity > 1 && `x${c.quantity}`}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Navigation */}
            <div className="flex gap-3 pt-2">
              <button onClick={reset} className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700">
                {t('import.back')}
              </button>
              <button
                onClick={() => setStep('mode')}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
              >
                {t('import.continue')}
              </button>
            </div>
          </div>
        )}

        {/* Step 4: Mode */}
        {step === 'mode' && (
          <div className="space-y-4">
            {(['merge', 'replace'] as Mode[]).map(m => (
              <label key={m} className={`block border-2 rounded-xl p-5 cursor-pointer transition ${mode === m ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-200 dark:border-gray-600 hover:border-gray-300'}`}>
                <input type="radio" name="mode" value={m} checked={mode === m} onChange={() => setMode(m)} className="sr-only" />
                <div className="font-semibold text-gray-900 dark:text-white capitalize mb-1">
                  {m === 'merge' ? t('import.mergeRecommended') : t('import.replaceLabel')}
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {m === 'merge' ? t('import.mergeDesc') : t('import.replaceDesc')}
                </p>
              </label>
            ))}
            <div className="flex gap-3 pt-2">
              <button onClick={() => setStep('review')} className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700">
                {t('import.back')}
              </button>
              <button
                onClick={handleImport}
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? t('import.starting') : t('import.importBtn')}
              </button>
            </div>
          </div>
        )}

        {/* Step 5: Progress */}
        {step === 'progress' && (
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-600 p-8 text-center space-y-4">
            <div className="flex justify-center">
              <div className="w-10 h-10 border-4 border-gray-200 dark:border-gray-600 border-t-blue-600 rounded-full animate-spin" />
            </div>
            <p className="text-gray-700 dark:text-gray-300">{t('import.enriching')}</p>
            <p className="text-sm text-gray-400">{t('import.enrichingHint')}</p>
          </div>
        )}

        {/* Step 6: Result */}
        {step === 'result' && result && (
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-600 p-6 space-y-4">
            <div className="flex items-center gap-3">
              <span className="text-3xl">✅</span>
              <div>
                <p className="font-semibold text-gray-900 dark:text-white">{t('import.importStarted')}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">{t('import.importedCards', { count: result.card_count ?? result.imported })}</p>
              </div>
            </div>
            {result.not_found?.length > 0 && (
              <div>
                <button onClick={() => setShowNotFound(s => !s)} className="text-sm text-orange-600 dark:text-orange-400 hover:underline">
                  {t('import.notFound', { count: result.not_found.length })} {showNotFound ? '▲' : '▼'}
                </button>
                {showNotFound && (
                  <ul className="mt-2 text-xs text-gray-500 dark:text-gray-400 space-y-0.5 max-h-32 overflow-y-auto">
                    {result.not_found.map((n, i) => <li key={i}>• {n}</li>)}
                  </ul>
                )}
              </div>
            )}
            <div className="flex gap-3 pt-2">
              <button onClick={() => navigate('/dashboard')} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
                {t('import.goToCollection')}
              </button>
              <button onClick={reset} className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700">
                {t('import.importAnother')}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Unresolved card row — shows suggestions, manual input, skip
// ---------------------------------------------------------------------------
function UnresolvedCardRow({
  card,
  correction,
  onChange,
  t,
}: {
  card: ResolvedCardItem;
  correction?: CardCorrection;
  onChange: (c: CardCorrection) => void;
  t: (key: string) => string;
}) {
  const action = correction?.action;

  return (
    <div className="px-4 py-3 space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-800 dark:text-gray-100">
          "{card.original_name}" {card.quantity > 1 && <span className="text-gray-400">x{card.quantity}</span>}
        </span>
        <button
          onClick={() => onChange({ action: 'skip', selectedName: '' })}
          className={`text-xs px-2 py-0.5 rounded transition ${
            action === 'skip'
              ? 'bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-200'
              : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-200'
          }`}
        >
          {t('import.reviewSkip')}
        </button>
      </div>

      {card.suggestions.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {card.suggestions.map((s, i) => (
            <button
              key={s}
              onClick={() => onChange({ action: 'accept_suggestion', selectedName: s })}
              className={`text-xs px-2.5 py-1 rounded-full border transition ${
                action === 'accept_suggestion' && correction?.selectedName === s
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                  : 'border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:border-blue-300'
              }`}
            >
              {i === 0 && '→ '}{s}
            </button>
          ))}
        </div>
      ) : (
        <p className="text-xs text-gray-400">{t('import.reviewNoSuggestions')}</p>
      )}

      <AutocompleteInput
        value={action === 'manual' ? (correction?.selectedName ?? '') : ''}
        onChange={name => onChange({ action: 'manual', selectedName: name })}
        placeholder={t('import.reviewTypeName')}
      />
    </div>
  );
}
