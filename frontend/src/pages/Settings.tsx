import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import { ThemeToggle } from '../components/ThemeToggle';

export function Settings() {
  const [importFileLoading, setImportFileLoading] = useState(false);
  const [importFileResult, setImportFileResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [scryfallJson, setScryfallJson] = useState('');
  const [scryfallConfigured, setScryfallConfigured] = useState(false);
  const [scryfallLoading, setScryfallLoading] = useState(false);
  const [scryfallMessage, setScryfallMessage] = useState<string | null>(null);

  useEffect(() => {
    api.getScryfallCredentials().then((r) => setScryfallConfigured(r.configured)).catch(() => setScryfallConfigured(false));
  }, []);

  const handleSaveScryfallCredentials = async () => {
    setError(null);
    setScryfallMessage(null);
    setScryfallLoading(true);
    try {
      let credentials: object | null = null;
      const raw = scryfallJson.trim();
      if (raw) {
        try {
          credentials = JSON.parse(raw) as object;
        } catch {
          setError('Invalid JSON. Paste a valid Scryfall credentials JSON.');
          setScryfallLoading(false);
          return;
        }
      }
      const r = await api.setScryfallCredentials(credentials);
      setScryfallConfigured(r.configured);
      setScryfallMessage(r.configured ? 'Scryfall credentials saved. The backend will use them next time.' : 'Scryfall credentials cleared.');
      if (r.configured) setScryfallJson('');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save Scryfall credentials');
    } finally {
      setScryfallLoading(false);
    }
  };

  const handleScryfallFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError(null);
    try {
      const text = await file.text();
      const parsed = JSON.parse(text) as object;
      setScryfallJson(JSON.stringify(parsed, null, 2));
    } catch {
      setError('The selected file is not valid JSON.');
    }
    e.target.value = '';
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError(null);
    setImportFileResult(null);
    setImportFileLoading(true);
    try {
      const r = await api.importFromFile(file);
      setImportFileResult(`Imported ${r.imported} cards.`);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Import failed');
    } finally {
      setImportFileLoading(false);
      e.target.value = '';
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      <nav className="bg-white dark:bg-gray-800 shadow flex gap-4 p-4 items-center">
        <Link to="/" className="text-blue-600 dark:text-blue-400 hover:underline">Dashboard</Link>
        <span className="text-gray-600 dark:text-gray-400">Settings</span>
        <ThemeToggle />
      </nav>
      <div className="max-w-2xl mx-auto p-6 space-y-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Settings</h1>
        {error && (
          <div className="bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 p-3 rounded">{error}</div>
        )}

        <section className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Scryfall API credentials</h2>
          <p className="mb-2 text-gray-600 dark:text-gray-400">
            Paste the Scryfall credentials JSON below or upload a .json file. The backend stores it internally and will use it the next time you run price updates. If not set, you may see &quot;Scryfall credentials not configured&quot;.
          </p>
          <div className="flex flex-col gap-2">
            <textarea
              value={scryfallJson}
              onChange={(e) => setScryfallJson(e.target.value)}
              placeholder='{"type": "service_account", ...}'
              rows={6}
              className="border border-gray-300 dark:border-gray-600 rounded px-3 py-2 text-sm font-mono bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
            />
            <div className="flex flex-wrap gap-2 items-center">
              <input
                type="file"
                accept=".json"
                onChange={handleScryfallFileChange}
                className="text-sm text-gray-500 dark:text-gray-400 file:mr-2 file:py-1.5 file:px-3 file:rounded file:border file:bg-gray-100 dark:file:bg-gray-600 dark:file:text-gray-200 file:border-gray-300 dark:file:border-gray-500"
              />
              <button
                type="button"
                onClick={handleSaveScryfallCredentials}
                disabled={scryfallLoading}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 dark:bg-blue-500 dark:hover:bg-blue-600"
              >
                {scryfallLoading ? 'Saving…' : 'Save credentials'}
              </button>
              {scryfallConfigured && (
                <button
                  type="button"
                  onClick={async () => {
                    setError(null);
                    try {
                      await api.setScryfallCredentials(null);
                      setScryfallConfigured(false);
                      setScryfallMessage('Credentials cleared.');
                    } catch (e) {
                      setError(e instanceof Error ? e.message : 'Failed to clear credentials');
                    }
                  }}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-200"
                >
                  Clear
                </button>
              )}
            </div>
          </div>
          {scryfallConfigured && <p className="mt-2 text-green-700 dark:text-green-400 text-sm">Scryfall credentials are stored and will be used by the backend.</p>}
          {scryfallMessage && <p className="mt-2 text-green-700 dark:text-green-400 text-sm">{scryfallMessage}</p>}
        </section>

        <section className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Import from file</h2>
          <p className="mb-2 text-gray-600 dark:text-gray-400">
            Upload a CSV or JSON file to replace your current collection. CSV must have a header row (e.g. Name, Type, Price).
          </p>
          <input
            type="file"
            accept=".csv,.json"
            onChange={handleFileChange}
            disabled={importFileLoading}
            className="block w-full text-sm text-gray-500 dark:text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:bg-blue-50 dark:file:bg-blue-900/50 file:text-blue-700 dark:file:text-blue-300"
          />
          {importFileResult && (
            <p className="mt-2 text-green-700 dark:text-green-400">{importFileResult}</p>
          )}
        </section>
      </div>
    </div>
  );
}
