import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Globe, X } from 'lucide-react';
import { languages, changeLanguage, getCurrentLanguage, getBrowserLanguage, hasLanguagePreference } from '@/i18n';

export default function LanguageBanner() {
  const { t } = useTranslation();
  const [show, setShow] = useState(false);
  const [suggestedLang, setSuggestedLang] = useState(null);

  useEffect(() => {
    // Don't show if user already dismissed or explicitly set a preference
    const dismissed = sessionStorage.getItem('lang-banner-dismissed');
    if (dismissed) return;

    const currentLang = getCurrentLanguage();
    const browserLang = getBrowserLanguage();

    // Only suggest if browser language differs from current
    if (browserLang !== currentLang) {
      const langInfo = languages.find(l => l.code === browserLang);
      if (langInfo) {
        setSuggestedLang(langInfo);
        // Small delay so it doesn't flash on initial load
        const timer = setTimeout(() => setShow(true), 1500);
        return () => clearTimeout(timer);
      }
    }
  }, []);

  const handleSwitch = () => {
    if (suggestedLang) {
      changeLanguage(suggestedLang.code);
    }
    setShow(false);
    sessionStorage.setItem('lang-banner-dismissed', 'true');
  };

  const handleDismiss = () => {
    setShow(false);
    sessionStorage.setItem('lang-banner-dismissed', 'true');
  };

  if (!show || !suggestedLang) return null;

  // Get message based on suggested language
  const messages = {
    es: { text: `Detectamos que tu navegador est\u00e1 en ${suggestedLang.nativeName}.`, action: 'Cambiar idioma' },
    en: { text: `We detected your browser is in ${suggestedLang.nativeName}.`, action: 'Switch language' },
    fr: { text: `Nous avons d\u00e9tect\u00e9 que votre navigateur est en ${suggestedLang.nativeName}.`, action: 'Changer de langue' }
  };

  const msg = messages[suggestedLang.code] || messages.en;

  return (
    <div
      className="fixed bottom-4 left-1/2 -translate-x-1/2 z-[60] animate-in slide-in-from-bottom-4 fade-in duration-500 w-[95%] max-w-md"
      data-testid="language-banner"
    >
      <div className="bg-slate-900 dark:bg-slate-800 text-white rounded-xl shadow-2xl border border-slate-700 px-4 py-3 flex items-center gap-3">
        <div className="flex-shrink-0 w-9 h-9 bg-emerald-500/20 rounded-full flex items-center justify-center">
          <Globe className="w-5 h-5 text-emerald-400" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm text-slate-200 leading-snug">
            {msg.text}
          </p>
        </div>
        <button
          onClick={handleSwitch}
          className="flex-shrink-0 bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-medium px-3 py-1.5 rounded-lg transition-colors"
          data-testid="language-banner-switch"
        >
          {suggestedLang.flag} {msg.action}
        </button>
        <button
          onClick={handleDismiss}
          className="flex-shrink-0 text-slate-400 hover:text-white transition-colors p-1"
          data-testid="language-banner-dismiss"
          aria-label="Dismiss"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
