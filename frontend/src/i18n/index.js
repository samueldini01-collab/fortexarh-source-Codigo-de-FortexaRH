import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import HttpBackend from 'i18next-http-backend';

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

// Get initial language
const getInitialLanguage = () => {
  const storedLang = localStorage.getItem('fortexarh-language');
  if (storedLang && supportedLanguages.includes(storedLang)) {
    return storedLang;
  }
  const browserLang = navigator.language || navigator.userLanguage;
  return mapBrowserLanguage(browserLang);
};

const initialLang = getInitialLanguage();

// Cache version - increment this to force translation reload
const TRANSLATION_VERSION = '1.5.0';

i18n
  .use(HttpBackend)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    lng: initialLang, // Set initial language immediately
    fallbackLng: 'es',
    supportedLngs: supportedLanguages,
    defaultNS: 'translation',
    ns: ['translation'],
    
    backend: {
      // Load translations from public folder
      loadPath: '/locales/{{lng}}.json',
      // Add cache busting with version
      queryStringParams: { v: TRANSLATION_VERSION },
      // Timeout for loading translations
      requestOptions: {
        cache: 'no-store'
      }
    },
    
    detection: {
      // Order of detection: localStorage first (user preference), then browser language
      order: ['localStorage', 'navigator', 'htmlTag', 'querystring', 'cookie'],
      caches: ['localStorage'],
      lookupLocalStorage: 'fortexarh-language',
      lookupQuerystring: 'lang',
      lookupCookie: 'fortexarh-language',
      checkWhitelist: true
    },

    interpolation: {
      escapeValue: false
    },

    react: {
      useSuspense: false // Disable suspense to prevent blank pages
    },
    
    load: 'languageOnly', // Only load 'en' not 'en-US'
    
    // Preload only the detected language (not all languages)
    preload: [initialLang],
    
    // Lazy load other languages when needed
    partialBundledLanguages: true
  });

// Store initial language preference
if (!localStorage.getItem('fortexarh-language')) {
  localStorage.setItem('fortexarh-language', initialLang);
}
document.documentElement.lang = initialLang;

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

// Helper to change language (loads translation if not already loaded)
export const changeLanguage = async (lang) => {
  if (!supportedLanguages.includes(lang)) {
    console.warn(`[i18n] Unsupported language: ${lang}, falling back to 'es'`);
    lang = 'es';
  }
  
  // This will automatically load the language file if not already loaded
  await i18n.changeLanguage(lang);
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

// Preload a specific language (useful for prefetching)
export const preloadLanguage = (lang) => {
  if (supportedLanguages.includes(lang)) {
    i18n.loadLanguages(lang);
  }
};
