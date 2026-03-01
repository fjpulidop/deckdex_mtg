/**
 * Import page — 5-step wizard for importing cards from external apps.
 * Route: /import (ProtectedRoute)
 */
import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useActiveJobs } from '../contexts/ActiveJobsContext';

type Step = 'upload' | 'preview' | 'mode' | 'progress' | 'result';
type Mode = 'merge' | 'replace';
type InputMode = 'file' | 'text';

interface Preview {
  detected_format: string;
  card_count: number;
  sample: string[];
}

interface ImportResult {
  imported: number;
  skipped: number;
  not_found: string[];
  mode: string;
  format: string;
}

const FORMAT_LABELS: Record<string, string> = {
  moxfield: 'Moxfield',
  tappedout: 'TappedOut',
  mtgo: 'MTGO',
  generic: 'CSV genérico',
};

export default function Import() {
  const navigate = useNavigate();
  const { addJob } = useActiveJobs();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [step, setStep] = useState<Step>('upload');
  const [inputMode, setInputMode] = useState<InputMode>('file');
  const [file, setFile] = useState<File | null>(null);
  const [pastedText, setPastedText] = useState('');
  const [preview, setPreview] = useState<Preview | null>(null);
  const [mode, setMode] = useState<Mode>('merge');
  const [result, setResult] = useState<ImportResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showNotFound, setShowNotFound] = useState(false);

  // Step 1 → 2: upload and preview (file)
  const handleFileSelect = async (selected: File) => {
    setFile(selected);
    setError(null);
    setLoading(true);
    try {
      const p = await api.importPreview(selected);
      setPreview(p);
      setStep('preview');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Error parsing file');
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const f = e.dataTransfer.files[0];
    if (f) handleFileSelect(f);
  };

  // Step 1 → 2: preview pasted text
  const handleTextPreview = async () => {
    if (!pastedText.trim()) return;
    setError(null);
    setLoading(true);
    try {
      const p = await api.importPreviewText(pastedText);
      setPreview(p);
      setStep('preview');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Error al analizar el texto');
    } finally {
      setLoading(false);
    }
  };

  // Step 3 → 4 → 5: launch import job
  const handleImport = async () => {
    if (inputMode === 'file' && !file) return;
    if (inputMode === 'text' && !pastedText.trim()) return;
    setLoading(true);
    setError(null);
    setStep('progress');
    try {
      const res = inputMode === 'text'
        ? await api.importExternalText(pastedText, mode)
        : await api.importExternal(file!, mode);
      addJob(res.job_id, `Import (${FORMAT_LABELS[res.format] ?? res.format})`, () => {
        // job finished callback — update step to result
      });
      setResult({ imported: res.card_count, skipped: 0, not_found: [], mode: res.mode, format: res.format });
      setStep('result');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Import failed');
      setStep('mode');
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setStep('upload');
    setFile(null);
    setPastedText('');
    setPreview(null);
    setResult(null);
    setError(null);
    setShowNotFound(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12 px-4">
      <div className="max-w-xl mx-auto">
        <div className="mb-8">
          <button onClick={() => navigate('/dashboard')} className="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
            ← Volver al dashboard
          </button>
          <h1 className="mt-2 text-2xl font-bold text-gray-900 dark:text-white">Importar colección</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">Importa cartas desde Moxfield, TappedOut, MTGO u otros formatos CSV.</p>
        </div>

        {/* Step indicator */}
        <div className="flex items-center gap-2 mb-8">
          {(['upload', 'preview', 'mode', 'progress', 'result'] as Step[]).map((s, i) => (
            <div key={s} className="flex items-center gap-2">
              <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${step === s ? 'bg-blue-600 text-white' : ['result', 'progress', 'mode', 'preview', 'upload'].indexOf(step) < ['result', 'progress', 'mode', 'preview', 'upload'].indexOf(s) ? 'bg-gray-200 dark:bg-gray-700 text-gray-400' : 'bg-green-500 text-white'}`}>
                {i + 1}
              </div>
              {i < 4 && <div className="w-8 h-0.5 bg-gray-200 dark:bg-gray-700" />}
            </div>
          ))}
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-lg text-sm">{error}</div>
        )}

        {/* Step 1: Upload */}
        {step === 'upload' && (
          <div className="space-y-4">
            {/* Tab switcher */}
            <div className="flex rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
              <button
                onClick={() => setInputMode('file')}
                className={`flex-1 py-2 text-sm font-medium transition ${inputMode === 'file' ? 'bg-blue-600 text-white' : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'}`}
              >
                Subir archivo
              </button>
              <button
                onClick={() => setInputMode('text')}
                className={`flex-1 py-2 text-sm font-medium transition ${inputMode === 'text' ? 'bg-blue-600 text-white' : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'}`}
              >
                Pegar texto
              </button>
            </div>

            {inputMode === 'file' ? (
              <div
                onDrop={handleDrop}
                onDragOver={e => e.preventDefault()}
                className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl p-12 text-center hover:border-blue-400 transition"
              >
                <div className="text-4xl mb-4">📁</div>
                <p className="text-gray-600 dark:text-gray-300 mb-4">Arrastra tu archivo aquí o</p>
                <label className="cursor-pointer">
                  <span className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm">
                    {loading ? 'Cargando…' : 'Seleccionar archivo'}
                  </span>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv,.txt"
                    className="sr-only"
                    onChange={e => { const f = e.target.files?.[0]; if (f) handleFileSelect(f); }}
                  />
                </label>
                <p className="mt-4 text-xs text-gray-400">Formatos: Moxfield CSV, TappedOut CSV, MTGO .txt, CSV genérico</p>
              </div>
            ) : (
              <div className="space-y-3">
                <textarea
                  value={pastedText}
                  onChange={e => setPastedText(e.target.value)}
                  placeholder={"Pega tu listado de cartas aquí. Formato:\n4 Lightning Bolt\n2 Black Lotus\n1 Sol Ring"}
                  rows={10}
                  className="w-full rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm text-gray-800 dark:text-gray-100 p-4 font-mono resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-400">Formato: una carta por línea con cantidad. Ej: <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded">4 Lightning Bolt</code></p>
                <button
                  onClick={handleTextPreview}
                  disabled={loading || !pastedText.trim()}
                  className="w-full py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50 transition"
                >
                  {loading ? 'Analizando…' : 'Continuar →'}
                </button>
              </div>
            )}
          </div>
        )}

        {/* Step 2: Preview */}
        {step === 'preview' && preview && (
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-600 p-6 space-y-4">
            <div className="flex items-center gap-3">
              <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 rounded-full text-sm font-medium">
                {FORMAT_LABELS[preview.detected_format] ?? preview.detected_format}
              </span>
              <span className="text-gray-600 dark:text-gray-300 text-sm">{preview.card_count} cartas detectadas</span>
            </div>
            <div>
              <p className="text-xs text-gray-400 mb-2 uppercase tracking-wider">Muestra</p>
              <ul className="space-y-1">
                {preview.sample.map((name, i) => (
                  <li key={i} className="text-sm text-gray-700 dark:text-gray-300">• {name}</li>
                ))}
              </ul>
            </div>
            <p className="text-xs text-gray-400">¿No coincide el formato? Selecciona otro archivo.</p>
            <div className="flex gap-3 pt-2">
              <button onClick={reset} className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700">
                Atrás
              </button>
              <button onClick={() => setStep('mode')} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
                Continuar →
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Mode */}
        {step === 'mode' && (
          <div className="space-y-4">
            {(['merge', 'replace'] as Mode[]).map(m => (
              <label key={m} className={`block border-2 rounded-xl p-5 cursor-pointer transition ${mode === m ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-200 dark:border-gray-600 hover:border-gray-300'}`}>
                <input type="radio" name="mode" value={m} checked={mode === m} onChange={() => setMode(m)} className="sr-only" />
                <div className="font-semibold text-gray-900 dark:text-white capitalize mb-1">
                  {m === 'merge' ? '🔀 Merge (recomendado)' : '🔄 Replace'}
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {m === 'merge'
                    ? 'Añade las cartas importadas a tu colección existente. Las cantidades se suman.'
                    : 'Reemplaza toda tu colección con este archivo. Esta acción no se puede deshacer.'}
                </p>
              </label>
            ))}
            <div className="flex gap-3 pt-2">
              <button onClick={() => setStep('preview')} className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700">
                Atrás
              </button>
              <button
                onClick={handleImport}
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Iniciando…' : 'Importar →'}
              </button>
            </div>
          </div>
        )}

        {/* Step 4: Progress */}
        {step === 'progress' && (
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-600 p-8 text-center space-y-4">
            <div className="flex justify-center">
              <div className="w-10 h-10 border-4 border-gray-200 dark:border-gray-600 border-t-blue-600 rounded-full animate-spin" />
            </div>
            <p className="text-gray-700 dark:text-gray-300">Enriqueciendo cartas vía Scryfall…</p>
            <p className="text-sm text-gray-400">Puedes ver el progreso en la barra de Jobs ↘</p>
          </div>
        )}

        {/* Step 5: Result */}
        {step === 'result' && result && (
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-600 p-6 space-y-4">
            <div className="flex items-center gap-3">
              <span className="text-3xl">✅</span>
              <div>
                <p className="font-semibold text-gray-900 dark:text-white">Importación iniciada</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">{result.card_count ?? result.imported} cartas en proceso — sigue el progreso en Jobs</p>
              </div>
            </div>
            {result.not_found?.length > 0 && (
              <div>
                <button onClick={() => setShowNotFound(s => !s)} className="text-sm text-orange-600 dark:text-orange-400 hover:underline">
                  {result.not_found.length} cartas no encontradas {showNotFound ? '▲' : '▼'}
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
                Ir a colección
              </button>
              <button onClick={reset} className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700">
                Importar otro archivo
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
