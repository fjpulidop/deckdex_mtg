import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import en from './locales/en.json';
import es from './locales/es.json';

const stored = localStorage.getItem('lang');
const browserLang = navigator.language.split('-')[0];
const supported = ['en', 'es'];
const defaultLang =
  stored && supported.includes(stored)
    ? stored
    : supported.includes(browserLang)
      ? browserLang
      : 'en';

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    es: { translation: es },
  },
  lng: defaultLang,
  fallbackLng: 'en',
  interpolation: {
    escapeValue: false,
  },
});

export default i18n;
