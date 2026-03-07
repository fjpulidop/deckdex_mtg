import { useTranslation } from 'react-i18next';

interface ErrorFallbackProps {
  error: Error | null;
  onReset: () => void;
}

export function ErrorFallback({ error, onReset }: ErrorFallbackProps) {
  const { t } = useTranslation();
  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 flex items-center justify-center">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 max-w-lg">
        <h1 className="text-2xl font-bold text-red-600 dark:text-red-400 mb-4">{t('errorBoundary.title')}</h1>
        <p className="text-gray-700 dark:text-gray-300 mb-4">
          {t('errorBoundary.description')}
        </p>
        {error && (
          <pre className="bg-red-50 dark:bg-red-900/30 p-4 rounded text-sm text-red-800 dark:text-red-200 overflow-auto">
            {error.toString()}
          </pre>
        )}
        <button
          onClick={onReset}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
        >
          {t('errorBoundary.refresh')}
        </button>
      </div>
    </div>
  );
}
