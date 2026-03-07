import { useState } from 'react';
import { X } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { DemoProvider } from '../contexts/DemoContext';
import { Dashboard } from './Dashboard';
import { redirectToGoogleLogin } from '../utils/auth';

export function Demo() {
  const { t } = useTranslation();
  const [bannerDismissed, setBannerDismissed] = useState(false);

  return (
    <DemoProvider>
      {!bannerDismissed && (
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-4 py-3 flex items-center justify-between gap-4">
          <p className="text-sm font-medium text-center flex-1">
            {t('demo.bannerText')}{' '}
            <button
              onClick={() => redirectToGoogleLogin()}
              className="underline font-semibold hover:no-underline"
            >
              {t('demo.bannerSignIn')}
            </button>{' '}
            to manage your real collection.
          </p>
          <button
            onClick={() => setBannerDismissed(true)}
            aria-label={t('demo.bannerDismiss')}
            className="shrink-0 p-1 rounded hover:bg-white/20 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}
      <Dashboard />
    </DemoProvider>
  );
}
