import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Globe, X, Sparkles } from 'lucide-react';
import { languages, changeLanguage, getCurrentLanguage } from '@/i18n';
import CountryFlag from '@/components/CountryFlag';

/**
 * Maps a browser locale (BCP-47) to a suggested FortexaRH country + language + currency.
 * Only includes the 29 supported countries. Order matters: specific > generic.
 */
const BROWSER_LOCALE_MAP = {
  // Caribbean
  'es-do': { country: 'DO', name: 'República Dominicana', language: 'es', currency: 'DOP', symbol: 'RD$' },
  'es-cu': { country: 'CU', name: 'Cuba', language: 'es', currency: 'CUP', symbol: '$' },
  'es-pr': { country: 'PR', name: 'Puerto Rico', language: 'es', currency: 'USD', symbol: '$' },
  'fr-ht': { country: 'HT', name: 'Haití', language: 'fr', currency: 'HTG', symbol: 'G' },
  'ht': { country: 'HT', name: 'Haití', language: 'fr', currency: 'HTG', symbol: 'G' },
  // North America
  'es-mx': { country: 'MX', name: 'México', language: 'es', currency: 'MXN', symbol: '$' },
  'en-us': { country: 'US', name: 'Estados Unidos', language: 'en', currency: 'USD', symbol: '$' },
  'en-ca': { country: 'CA', name: 'Canadá', language: 'en', currency: 'CAD', symbol: 'C$' },
  'fr-ca': { country: 'CA', name: 'Canadá', language: 'fr', currency: 'CAD', symbol: 'C$' },
  // Central America
  'es-cr': { country: 'CR', name: 'Costa Rica', language: 'es', currency: 'CRC', symbol: '₡' },
  'es-sv': { country: 'SV', name: 'El Salvador', language: 'es', currency: 'USD', symbol: '$' },
  'es-gt': { country: 'GT', name: 'Guatemala', language: 'es', currency: 'GTQ', symbol: 'Q' },
  'es-hn': { country: 'HN', name: 'Honduras', language: 'es', currency: 'HNL', symbol: 'L' },
  'es-ni': { country: 'NI', name: 'Nicaragua', language: 'es', currency: 'NIO', symbol: 'C$' },
  'es-pa': { country: 'PA', name: 'Panamá', language: 'es', currency: 'PAB', symbol: 'B/.' },
  // South America
  'es-co': { country: 'CO', name: 'Colombia', language: 'es', currency: 'COP', symbol: '$' },
  'es-ar': { country: 'AR', name: 'Argentina', language: 'es', currency: 'ARS', symbol: '$' },
  'es-cl': { country: 'CL', name: 'Chile', language: 'es', currency: 'CLP', symbol: '$' },
  'es-pe': { country: 'PE', name: 'Perú', language: 'es', currency: 'PEN', symbol: 'S/.' },
  'es-ec': { country: 'EC', name: 'Ecuador', language: 'es', currency: 'USD', symbol: '$' },
  'es-ve': { country: 'VE', name: 'Venezuela', language: 'es', currency: 'VES', symbol: 'Bs.' },
  'es-bo': { country: 'BO', name: 'Bolivia', language: 'es', currency: 'BOB', symbol: 'Bs' },
  'es-py': { country: 'PY', name: 'Paraguay', language: 'es', currency: 'PYG', symbol: '₲' },
  'es-uy': { country: 'UY', name: 'Uruguay', language: 'es', currency: 'UYU', symbol: '$' },
  'en-gy': { country: 'GY', name: 'Guyana', language: 'en', currency: 'GYD', symbol: 'G$' },
  'nl-sr': { country: 'SR', name: 'Surinam', language: 'en', currency: 'SRD', symbol: '$' },
  'pt-br': { country: 'BR', name: 'Brasil', language: 'pt', currency: 'BRL', symbol: 'R$' },
  // Europe
  'es-es': { country: 'ES', name: 'España', language: 'es', currency: 'EUR', symbol: '€' },
  'en-gb': { country: 'GB', name: 'Reino Unido', language: 'en', currency: 'GBP', symbol: '£' },
  'fr-fr': { country: 'FR', name: 'Francia', language: 'fr', currency: 'EUR', symbol: '€' },
  'fr-be': { country: 'BE', name: 'Bélgica', language: 'fr', currency: 'EUR', symbol: '€' },
  'nl-be': { country: 'BE', name: 'Bélgica', language: 'fr', currency: 'EUR', symbol: '€' },
};

// Fallback mapping by base language when locale region isn't specified
const BASE_LANGUAGE_FALLBACK = {
  'pt': { country: 'BR', name: 'Brasil', language: 'pt', currency: 'BRL', symbol: 'R$' },
};

function detectSuggestion() {
  const langs = navigator.languages && navigator.languages.length
    ? navigator.languages
    : [navigator.language || 'en-US'];

  for (const raw of langs) {
    const lower = raw.toLowerCase();
    if (BROWSER_LOCALE_MAP[lower]) return BROWSER_LOCALE_MAP[lower];
    const base = lower.split('-')[0];
    if (BASE_LANGUAGE_FALLBACK[base]) return BASE_LANGUAGE_FALLBACK[base];
  }
  return null;
}

// i18n-free copy per language (kept local to avoid expanding locale files)
const COPY = {
  es: {
    banner: (country) => `¿Estás en ${country}? FortexaRH soporta nómina nativa para ${country}.`,
    currency: (symbol, code) => `Moneda: ${symbol} (${code})`,
    primary: 'Activar',
    calculator: 'Probar calculadora',
    dismiss: 'Cerrar',
  },
  en: {
    banner: (country) => `Based in ${country}? FortexaRH has native payroll support for ${country}.`,
    currency: (symbol, code) => `Currency: ${symbol} (${code})`,
    primary: 'Switch',
    calculator: 'Try calculator',
    dismiss: 'Dismiss',
  },
  fr: {
    banner: (country) => `Basé en ${country} ? FortexaRH prend en charge la paie native pour ${country}.`,
    currency: (symbol, code) => `Devise : ${symbol} (${code})`,
    primary: 'Activer',
    calculator: 'Essayer la calculatrice',
    dismiss: 'Fermer',
  },
  pt: {
    banner: (country) => `Está no ${country}? FortexaRH tem suporte nativo de folha para ${country}.`,
    currency: (symbol, code) => `Moeda: ${symbol} (${code})`,
    primary: 'Ativar',
    calculator: 'Testar calculadora',
    dismiss: 'Fechar',
  },
};

const DISMISS_KEY = 'fortexarh-locale-banner-dismissed-v2';

export default function LanguageBanner() {
  const navigate = useNavigate();
  const [show, setShow] = useState(false);
  const [suggestion, setSuggestion] = useState(null);

  useEffect(() => {
    // Skip if already dismissed in this session or explicitly set
    if (sessionStorage.getItem(DISMISS_KEY)) return;

    const suggested = detectSuggestion();
    if (!suggested) return;

    const currentLang = getCurrentLanguage();
    // Only show if language OR country-awareness differs from defaults
    // (show whenever we have a geo match different from es-DO default view)
    const isAlreadyDefault = suggested.language === currentLang && suggested.country === 'DO';
    if (isAlreadyDefault) return;

    setSuggestion(suggested);
    const timer = setTimeout(() => setShow(true), 1500);
    return () => clearTimeout(timer);
  }, []);

  const handleSwitch = async () => {
    if (!suggestion) return;
    await changeLanguage(suggestion.language);
    sessionStorage.setItem(DISMISS_KEY, 'true');
    setShow(false);
  };

  const handleTryCalculator = async () => {
    if (!suggestion) return;
    await changeLanguage(suggestion.language);
    sessionStorage.setItem(DISMISS_KEY, 'true');
    setShow(false);
    navigate(`/calculator?country=${suggestion.country}`);
  };

  const handleDismiss = () => {
    sessionStorage.setItem(DISMISS_KEY, 'true');
    setShow(false);
  };

  if (!show || !suggestion) return null;

  const copy = COPY[suggestion.language] || COPY.en;
  const langInfo = languages.find(l => l.code === suggestion.language);

  return (
    <div
      className="fixed bottom-4 left-1/2 -translate-x-1/2 z-[60] animate-in slide-in-from-bottom-4 fade-in duration-500 w-[95%] max-w-xl"
      data-testid="locale-banner"
    >
      <div className="bg-slate-900 text-white rounded-2xl shadow-2xl border border-slate-700 px-5 py-4 flex items-center gap-4">
        <div className="flex-shrink-0">
          <div className="relative">
            <CountryFlag code={suggestion.country} className="w-10 h-auto rounded shadow-md" />
            <span className="absolute -top-1 -right-1 w-4 h-4 bg-emerald-500 rounded-full flex items-center justify-center">
              <Sparkles className="w-2.5 h-2.5 text-white" />
            </span>
          </div>
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm text-white leading-snug font-medium" data-testid="locale-banner-text">
            {copy.banner(suggestion.name)}
          </p>
          <p className="text-xs text-slate-400 mt-0.5 flex items-center gap-1.5">
            <Globe className="w-3 h-3" />
            {copy.currency(suggestion.symbol, suggestion.currency)}
            {langInfo && langInfo.code !== getCurrentLanguage() && (
              <>
                <span className="text-slate-600">·</span>
                <span>{langInfo.nativeName}</span>
              </>
            )}
          </p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <button
            onClick={handleTryCalculator}
            className="hidden sm:inline-flex bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-semibold px-3 py-2 rounded-lg transition-colors whitespace-nowrap"
            data-testid="locale-banner-calculator"
          >
            {copy.calculator}
          </button>
          <button
            onClick={handleSwitch}
            className="bg-white hover:bg-slate-100 text-slate-900 text-xs font-semibold px-3 py-2 rounded-lg transition-colors whitespace-nowrap"
            data-testid="locale-banner-switch"
          >
            {copy.primary}
          </button>
          <button
            onClick={handleDismiss}
            className="text-slate-400 hover:text-white transition-colors p-1"
            data-testid="locale-banner-dismiss"
            aria-label={copy.dismiss}
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
