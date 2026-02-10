import { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Globe, Check, ChevronDown } from 'lucide-react';
import { languages, changeLanguage, getCurrentLanguage } from '@/i18n';

export default function LanguageSelector({ variant = 'default', className = '' }) {
  const { t } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const [currentLang, setCurrentLang] = useState(getCurrentLanguage());
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLanguageChange = (langCode) => {
    changeLanguage(langCode);
    setCurrentLang(langCode);
    setIsOpen(false);
  };

  const currentLanguage = languages.find(l => l.code === currentLang) || languages[0];

  // Compact variant for header
  if (variant === 'compact') {
    return (
      <div className={`relative ${className}`} ref={dropdownRef}>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-1.5 px-2 py-1.5 text-sm rounded-lg transition-colors hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300"
          data-testid="language-selector"
        >
          <Globe className="w-4 h-4" />
          <span className="hidden sm:inline">{currentLanguage.code.toUpperCase()}</span>
          <ChevronDown className={`w-3 h-3 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </button>

        {isOpen && (
          <div className="absolute right-0 mt-1 w-40 bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-slate-200 dark:border-slate-700 py-1 z-50 animate-in fade-in slide-in-from-top-2 duration-200">
            {languages.map((lang) => (
              <button
                key={lang.code}
                onClick={() => handleLanguageChange(lang.code)}
                className={`w-full flex items-center gap-2 px-3 py-2 text-sm transition-colors ${
                  currentLang === lang.code
                    ? 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400'
                    : 'text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700'
                }`}
                data-testid={`lang-${lang.code}`}
              >
                <span className="text-base">{lang.flag}</span>
                <span className="flex-1 text-left">{lang.name}</span>
                {currentLang === lang.code && <Check className="w-4 h-4" />}
              </button>
            ))}
          </div>
        )}
      </div>
    );
  }

  // Landing page variant (light on dark background)
  if (variant === 'landing') {
    return (
      <div className={`relative ${className}`} ref={dropdownRef}>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-1.5 px-3 py-2 text-sm rounded-lg transition-colors hover:bg-slate-800 text-white"
          data-testid="language-selector-landing"
        >
          <Globe className="w-4 h-4" />
          <span>{currentLanguage.code.toUpperCase()}</span>
          <ChevronDown className={`w-3 h-3 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </button>

        {isOpen && (
          <div className="absolute right-0 mt-1 w-40 bg-white rounded-lg shadow-lg border border-slate-200 py-1 z-50 animate-in fade-in slide-in-from-top-2 duration-200">
            {languages.map((lang) => (
              <button
                key={lang.code}
                onClick={() => handleLanguageChange(lang.code)}
                className={`w-full flex items-center gap-2 px-3 py-2 text-sm transition-colors ${
                  currentLang === lang.code
                    ? 'bg-emerald-50 text-emerald-700'
                    : 'text-slate-700 hover:bg-slate-50'
                }`}
                data-testid={`lang-landing-${lang.code}`}
              >
                <span className="text-base">{lang.flag}</span>
                <span className="flex-1 text-left">{lang.name}</span>
                {currentLang === lang.code && <Check className="w-4 h-4" />}
              </button>
            ))}
          </div>
        )}
      </div>
    );
  }

  // Default full variant
  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors text-slate-700 dark:text-slate-300"
        data-testid="language-selector-full"
      >
        <span className="text-lg">{currentLanguage.flag}</span>
        <span>{currentLanguage.name}</span>
        <ChevronDown className={`w-4 h-4 ml-auto transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute left-0 right-0 mt-1 bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-slate-200 dark:border-slate-700 py-1 z-50 animate-in fade-in slide-in-from-top-2 duration-200">
          {languages.map((lang) => (
            <button
              key={lang.code}
              onClick={() => handleLanguageChange(lang.code)}
              className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
                currentLang === lang.code
                  ? 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400'
                  : 'text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700'
              }`}
            >
              <span className="text-lg">{lang.flag}</span>
              <span className="flex-1 text-left">{lang.name}</span>
              {currentLang === lang.code && <Check className="w-4 h-4" />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
