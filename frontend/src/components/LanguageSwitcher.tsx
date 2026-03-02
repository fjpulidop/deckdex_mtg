import { useTranslation } from 'react-i18next';

const LANGUAGES = ['en', 'es'] as const;

export const LanguageSwitcher = () => {
  const { i18n } = useTranslation();
  const current = i18n.language.split('-')[0];

  const toggle = () => {
    const next = current === 'en' ? 'es' : 'en';
    i18n.changeLanguage(next);
    localStorage.setItem('lang', next);
  };

  return (
    <button
      onClick={toggle}
      title={i18n.t('navbar.switchLanguage')}
      className="flex items-center gap-1 text-sm font-medium text-slate-300 hover:text-white transition-colors"
    >
      {LANGUAGES.map((lang, idx) => (
        <span key={lang}>
          {idx > 0 && <span className="text-slate-500 mx-0.5">|</span>}
          <span className={lang === current ? 'text-white font-semibold' : 'text-slate-400'}>
            {lang.toUpperCase()}
          </span>
        </span>
      ))}
    </button>
  );
};
