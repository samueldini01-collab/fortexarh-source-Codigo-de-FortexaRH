import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import es from './locales/es.json';
import en from './locales/en.json';
import fr from './locales/fr.json';

const resources = {
  es: { translation: es },
  en: { translation: en },
  fr: { translation: fr }
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'es',
    defaultNS: 'translation',
    
    detection: {
      order: ['localStorage', 'navigator', 'htmlTag'],
      caches: ['localStorage'],
      lookupLocalStorage: 'fortexarh-language'
    },

    interpolation: {
      escapeValue: false
    },

    react: {
      useSuspense: false
    }
  });

export default i18n;

// Language options for UI
export const languages = [
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' }
];

// Helper to get current language
export const getCurrentLanguage = () => {
  return i18n.language?.split('-')[0] || 'es';
};

// Helper to change language
export const changeLanguage = (lang) => {
  i18n.changeLanguage(lang);
  localStorage.setItem('fortexarh-language', lang);
  document.documentElement.lang = lang;
};
