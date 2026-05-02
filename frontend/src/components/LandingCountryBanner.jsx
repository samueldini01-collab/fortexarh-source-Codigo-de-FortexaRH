import { useState, useEffect, useMemo } from "react";
import { useSearchParams, useParams } from "react-router-dom";
import axios from "axios";
import { Globe, ChevronDown, MapPin, X, Check } from "lucide-react";
import CountryFlag from "@/components/CountryFlag";
import { slugToCountry } from "@/components/LandingSEO";

const API = (process.env.REACT_APP_BACKEND_URL || "").replace(/\/$/, "") + "/api";
const STORAGE_KEY = "fortexarh-landing-country";
const DEFAULT_COUNTRY = "DO";

const REGION_LABEL = {
  caribbean: "Caribe",
  central_america: "América Central",
  north_america: "América del Norte",
  south_america: "América del Sur",
  europe: "Europa",
};

/**
 * useLandingCountry — custom hook: reads country from URL ?country=XX, then localStorage, defaults to DO.
 * Syncs changes to URL + localStorage and returns the full country profile.
 */
export function useLandingCountry() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { slug } = useParams();
  const slugCountry = slug ? slugToCountry(slug) : null;
  const urlCountry = slugCountry || (searchParams.get("country") || "").toUpperCase();
  const stored = typeof window !== "undefined" ? localStorage.getItem(STORAGE_KEY) : null;
  const initial = urlCountry || stored || DEFAULT_COUNTRY;

  const [countryCode, setCountryCodeState] = useState(initial);
  const [profile, setProfile] = useState(null);
  const [regions, setRegions] = useState({});
  const [ipDetected, setIpDetected] = useState(null);

  useEffect(() => {
    let cancelled = false;
    axios.get(`${API}/country-config/countries`).then(({ data }) => {
      if (!cancelled) setRegions(data.regions || {});
    }).catch(() => {});
    return () => { cancelled = true; };
  }, []);

  // Sync when URL slug changes (e.g. /pais/mexico → /pais/colombia)
  useEffect(() => {
    if (slugCountry && slugCountry !== countryCode) {
      setCountryCodeState(slugCountry);
      try { localStorage.setItem(STORAGE_KEY, slugCountry); } catch { /* ignore */ }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slugCountry]);

  // IP-based geolocation — only if no URL param, no slug and no localStorage preference
  useEffect(() => {
    if (urlCountry || stored) return; // User preference takes priority
    let cancelled = false;
    (async () => {
      try {
        const { data } = await axios.get("https://ipapi.co/json/", { timeout: 3000 });
        const code = (data?.country_code || "").toUpperCase();
        if (!cancelled && code) {
          setIpDetected(code);
          setCountryCodeState(code);
          try { localStorage.setItem(STORAGE_KEY, code); } catch {}
        }
      } catch {
        // Silent fallback — default DO remains
      }
    })();
    return () => { cancelled = true; };
  }, [urlCountry, stored]);

  useEffect(() => {
    if (!countryCode) return;
    let cancelled = false;
    axios.get(`${API}/country-config/countries/${countryCode}`)
      .then(({ data }) => { if (!cancelled) setProfile(data); })
      .catch(() => { if (!cancelled) setProfile(null); });
    return () => { cancelled = true; };
  }, [countryCode]);

  const setCountry = (code) => {
    const upper = (code || DEFAULT_COUNTRY).toUpperCase();
    setCountryCodeState(upper);
    try { localStorage.setItem(STORAGE_KEY, upper); } catch {}
    // Update URL (preserve other params)
    const params = new URLSearchParams(searchParams);
    if (upper === DEFAULT_COUNTRY) {
      params.delete("country");
    } else {
      params.set("country", upper);
    }
    setSearchParams(params, { replace: true });
  };

  const isDefault = countryCode === DEFAULT_COUNTRY;

  return { countryCode, profile, regions, setCountry, isDefault, ipDetected };
}

/**
 * LandingCountryBanner — full-width banner with country selector.
 * Shown prominently at the top of the landing.
 */
export function LandingCountryBanner({ countryCode, profile, regions, setCountry, isDefault, t }) {
  const [open, setOpen] = useState(false);
  const allCountries = useMemo(() => {
    const list = [];
    Object.entries(regions).forEach(([region, info]) => {
      (info.countries || []).forEach((c) => list.push({ ...c, region }));
    });
    return list;
  }, [regions]);

  const currentName = profile?.name || (allCountries.find((c) => c.code === countryCode)?.name ?? countryCode);
  const currentCurrency = profile?.currency_symbol
    ? `${profile.currency_symbol} ${profile.currency}`
    : "";

  return (
    <div className="relative bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 sm:py-4">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <div className="hidden sm:flex w-10 h-10 rounded-full bg-white/10 items-center justify-center flex-shrink-0">
              <Globe className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <p className="text-xs opacity-80 font-medium">
                {t ? t("landing.countryBanner.label") : "Viendo información de"}
              </p>
              <div className="flex items-center gap-2 min-w-0">
                <CountryFlag code={countryCode} className="w-7 h-auto flex-shrink-0 rounded-sm shadow-sm" />
                <p className="text-base sm:text-lg font-bold truncate" data-testid="landing-country-name">
                  {currentName}
                </p>
                {currentCurrency && (
                  <span className="hidden md:inline text-xs bg-white/20 px-2 py-0.5 rounded-full">
                    {currentCurrency}
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setOpen(true)}
              className="inline-flex items-center gap-2 bg-white text-emerald-700 font-semibold px-3 sm:px-4 py-2 rounded-lg text-xs sm:text-sm hover:bg-emerald-50 transition-colors shadow-md"
              data-testid="landing-country-change-btn"
            >
              <MapPin className="w-4 h-4" />
              <span>{t ? t("landing.countryBanner.change") : "Cambiar país"}</span>
              <ChevronDown className="w-3.5 h-3.5 opacity-70" />
            </button>
          </div>
        </div>
      </div>

      {/* Country Picker Modal */}
      {open && (
        <div
          className="fixed inset-0 z-[100] flex items-start justify-center p-4 bg-slate-900/70 backdrop-blur-sm animate-in fade-in duration-200"
          onClick={() => setOpen(false)}
          data-testid="landing-country-picker"
        >
          <div
            className="bg-white rounded-2xl shadow-2xl max-w-3xl w-full mt-12 max-h-[85vh] overflow-hidden flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-5 sm:px-6 py-4 border-b border-slate-200">
              <div>
                <h3 className="text-lg font-bold text-slate-900">
                  {t ? t("landing.countryBanner.title") : "Selecciona tu país"}
                </h3>
                <p className="text-xs sm:text-sm text-slate-500">
                  {t ? t("landing.countryBanner.subtitle") : "La landing se adaptará con información fiscal nativa de tu país."}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setOpen(false)}
                className="p-1.5 rounded-lg hover:bg-slate-100 transition-colors"
                aria-label="Cerrar"
              >
                <X className="w-5 h-5 text-slate-500" />
              </button>
            </div>

            <div className="overflow-y-auto p-4 sm:p-5 space-y-5">
              {Object.entries(regions).map(([regionCode, info]) => (
                <div key={regionCode}>
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-1 h-4 bg-emerald-500 rounded-full" />
                    <h4 className="text-xs sm:text-sm font-bold text-slate-700 uppercase tracking-wide">
                      {REGION_LABEL[regionCode] || regionCode}
                    </h4>
                    <span className="text-xs text-slate-400">({info.countries.length})</span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                    {info.countries.map((c) => {
                      const selected = c.code === countryCode;
                      return (
                        <button
                          key={c.code}
                          type="button"
                          onClick={() => {
                            setCountry(c.code);
                            setOpen(false);
                          }}
                          className={`flex items-center gap-2 p-2 rounded-lg border transition-all text-left ${
                            selected
                              ? "border-emerald-500 bg-emerald-50 ring-2 ring-emerald-200"
                              : "border-slate-200 hover:border-emerald-300 hover:bg-slate-50"
                          }`}
                          data-testid={`landing-country-option-${c.code}`}
                        >
                          <CountryFlag code={c.code} className="w-6 h-auto flex-shrink-0 rounded-sm" />
                          <div className="min-w-0 flex-1">
                            <p className={`text-xs font-semibold truncate ${selected ? "text-emerald-700" : "text-slate-800"}`}>
                              {c.name}
                            </p>
                            <p className="text-[10px] text-slate-500">
                              {c.currency_symbol} {c.currency}
                            </p>
                          </div>
                          {selected && <Check className="w-4 h-4 text-emerald-600 flex-shrink-0" />}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>

            <div className="px-5 sm:px-6 py-3 border-t border-slate-200 bg-slate-50 text-xs text-slate-500 text-center">
              {t ? t("landing.countryBanner.footer") : "Motor fiscal dinámico · tarifas, ISR y reportes se adaptan al país seleccionado"}
              {!isDefault && (
                <button
                  type="button"
                  onClick={() => { setCountry(DEFAULT_COUNTRY); setOpen(false); }}
                  className="ml-2 text-emerald-600 font-semibold hover:underline"
                >
                  · {t ? t("landing.countryBanner.reset") : "Restablecer a República Dominicana"}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
