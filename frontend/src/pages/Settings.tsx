import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '../api/client';

export function Settings() {
  const { t } = useTranslation();

  const [importFileLoading, setImportFileLoading] = useState(false);
  const [importFileResult, setImportFileResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [scryfallJson, setScryfallJson] = useState('');
  const [scryfallConfigured, setScryfallConfigured] = useState(false);
  const [scryfallLoading, setScryfallLoading] = useState(false);
  const [scryfallMessage, setScryfallMessage] = useState<string | null>(null);

  const [scryfallEnabled, setScryfallEnabled] = useState(false);
  const [scryfallToggleLoading, setScryfallToggleLoading] = useState(false);

  useEffect(() => {
    api.getScryfallCredentials().then((r) => setScryfallConfigured(r.configured)).catch(() => setScryfallConfigured(false));
    api.getExternalApisSettings().then((r) => setScryfallEnabled(r.scryfall_enabled)).catch(() => {});
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
          setError(t('settings.invalidJson'));
          setScryfallLoading(false);
          return;
        }
      }
      const r = await api.setScryfallCredentials(credentials);
      setScryfallConfigured(r.configured);
      setScryfallMessage(r.configured ? t('settings.credentialsSaved') : t('settings.credentialsCleared'));
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
      setError(t('settings.invalidJsonFile'));
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
      setImportFileResult(t('settings.importedCards', { count: r.imported }));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Import failed');
    } finally {
      setImportFileLoading(false);
      e.target.value = '';
    }
  };

  return (
    <div className="relative min-h-screen">
      <div className="container mx-auto px-4 py-8 max-w-2xl">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t('settings.title')}</h1>
        </div>

        {error && (
          <div role="alert" className="mb-6 bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 p-3 rounded">
            {error}
          </div>
        )}

        <div className="space-y-6">
          {/* Scryfall Credentials */}
          <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="text-base font-semibold mb-3 text-gray-900 dark:text-white">{t('settings.scryfallSection')}</h2>
            <p className="mb-2 text-sm text-gray-600 dark:text-gray-400">
              {t('settings.scryfallDesc')}
            </p>
            <div className="flex flex-col gap-2">
              <label htmlFor="settings-scryfall-json" className="sr-only">{t('settings.scryfallCredentialsLabel')}</label>
              <textarea
                id="settings-scryfall-json"
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
                  {scryfallLoading ? t('settings.saving') : t('settings.saveCredentials')}
                </button>
                {scryfallConfigured && (
                  <button
                    type="button"
                    onClick={async () => {
                      setError(null);
                      try {
                        await api.setScryfallCredentials(null);
                        setScryfallConfigured(false);
                        setScryfallMessage(t('settings.credentialsCleared2'));
                      } catch (e) {
                        setError(e instanceof Error ? e.message : 'Failed to clear credentials');
                      }
                    }}
                    className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-200"
                  >
                    {t('settings.clearCredentials')}
                  </button>
                )}
              </div>
            </div>
            {scryfallConfigured && <p className="mt-2 text-green-700 dark:text-green-400 text-sm">{t('settings.scryfallStored')}</p>}
            {scryfallMessage && <p className="mt-2 text-green-700 dark:text-green-400 text-sm">{scryfallMessage}</p>}
          </section>

          {/* External APIs */}
          <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="text-base font-semibold mb-3 text-gray-900 dark:text-white">{t('settings.externalApis')}</h2>
            <p className="mb-3 text-sm text-gray-600 dark:text-gray-400">
              {t('settings.externalApisDesc')}
            </p>
            <div className="flex items-center justify-between py-2">
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">{t('settings.scryfallToggleLabel')}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {t('settings.scryfallToggleDesc')}
                </p>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={scryfallEnabled}
                disabled={scryfallToggleLoading}
                onClick={async () => {
                  const newVal = !scryfallEnabled;
                  setScryfallEnabled(newVal);
                  setScryfallToggleLoading(true);
                  try {
                    const r = await api.updateExternalApisSettings({ scryfall_enabled: newVal });
                    setScryfallEnabled(r.scryfall_enabled);
                  } catch (e) {
                    setScryfallEnabled(!newVal);
                    setError(e instanceof Error ? e.message : 'Failed to update setting');
                  } finally {
                    setScryfallToggleLoading(false);
                  }
                }}
                className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 ${
                  scryfallEnabled ? 'bg-indigo-600' : 'bg-gray-300 dark:bg-gray-600'
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                    scryfallEnabled ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>
          </section>

          {/* Quick Import */}
          <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="text-base font-semibold mb-3 text-gray-900 dark:text-white">{t('settings.importCollection')}</h2>
            <p className="mb-3 text-sm text-gray-600 dark:text-gray-400">
              {t('settings.importCollectionDesc')}
            </p>
            <p className="mb-2 text-sm text-gray-600 dark:text-gray-400">
              {t('settings.quickImportDesc')}
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
    </div>
  );
}
