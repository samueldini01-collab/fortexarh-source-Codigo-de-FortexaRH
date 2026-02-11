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

// Supported languages
const supportedLanguages = ['es', 'en', 'fr'];

// Custom language detector that maps browser languages to supported ones
const mapBrowserLanguage = (browserLang) => {
  if (!browserLang) return 'es';
  
  // Get the base language code (e.g., 'en-US' -> 'en')
  const baseLang = browserLang.split('-')[0].toLowerCase();
  
  // Direct match
  if (supportedLanguages.includes(baseLang)) {
    return baseLang;
  }
  
  // Map similar languages
  const languageMap = {
    // Spanish variants
    'es': 'es', 'es-mx': 'es', 'es-ar': 'es', 'es-co': 'es', 'es-cl': 'es',
    // English variants
    'en': 'en', 'en-us': 'en', 'en-gb': 'en', 'en-au': 'en', 'en-ca': 'en',
    // French variants
    'fr': 'fr', 'fr-ca': 'fr', 'fr-be': 'fr', 'fr-ch': 'fr',
    // Portuguese -> Spanish (similar)
    'pt': 'es', 'pt-br': 'es',
    // Italian -> Spanish (similar)
    'it': 'es',
    // German -> English
    'de': 'en',
    // Dutch -> English
    'nl': 'en',
  };
  
  return languageMap[browserLang.toLowerCase()] || languageMap[baseLang] || 'es';
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'es',
    supportedLngs: supportedLanguages,
    defaultNS: 'translation',
    
    detection: {
      // Order of detection: localStorage first (user preference), then browser language
      order: ['localStorage', 'navigator', 'htmlTag', 'querystring', 'cookie'],
      caches: ['localStorage'],
      lookupLocalStorage: 'fortexarh-language',
      lookupQuerystring: 'lang',
      lookupCookie: 'fortexarh-language',
      
      // Check if stored language is valid
      checkWhitelist: true
    },

    interpolation: {
      escapeValue: false
    },

    react: {
      useSuspense: false
    },
    
    // Post-process detected language to map to supported ones
    load: 'languageOnly', // Only load 'en' not 'en-US'
  });

// If no language was stored, detect and store browser language
const initializeLanguage = () => {
  const storedLang = localStorage.getItem('fortexarh-language');
  
  if (!storedLang) {
    // Get browser language
    const browserLang = navigator.language || navigator.userLanguage;
    const mappedLang = mapBrowserLanguage(browserLang);
    
    // Set the detected language
    i18n.changeLanguage(mappedLang);
    localStorage.setItem('fortexarh-language', mappedLang);
    document.documentElement.lang = mappedLang;
    
    console.log(`[i18n] Auto-detected language: ${browserLang} -> ${mappedLang}`);
  } else {
    // Ensure document lang attribute matches stored preference
    document.documentElement.lang = storedLang;
  }
};

// Initialize on load
initializeLanguage();

export default i18n;

// Language options for UI
export const languages = [
  { code: 'es', name: 'Español', flag: '🇪🇸', nativeName: 'Español' },
  { code: 'en', name: 'English', flag: '🇺🇸', nativeName: 'English' },
  { code: 'fr', name: 'Français', flag: '🇫🇷', nativeName: 'Français' }
];

// Helper to get current language
export const getCurrentLanguage = () => {
  return i18n.language?.split('-')[0] || 'es';
};

// Helper to change language
export const changeLanguage = (lang) => {
  if (!supportedLanguages.includes(lang)) {
    console.warn(`[i18n] Unsupported language: ${lang}, falling back to 'es'`);
    lang = 'es';
  }
  i18n.changeLanguage(lang);
  localStorage.setItem('fortexarh-language', lang);
  document.documentElement.lang = lang;
};

// Helper to get browser's preferred language (mapped to supported)
export const getBrowserLanguage = () => {
  const browserLang = navigator.language || navigator.userLanguage;
  return mapBrowserLanguage(browserLang);
};

// Check if user has explicitly set a language preference
export const hasLanguagePreference = () => {
  return localStorage.getItem('fortexarh-language') !== null;
};
