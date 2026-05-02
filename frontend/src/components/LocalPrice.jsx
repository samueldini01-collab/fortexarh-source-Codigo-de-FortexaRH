/**
 * LocalPrice — converts USD prices to the landing country's local currency
 * using live rates from backend's exchange rates integration.
 */
import { useEffect, useState } from "react";
import axios from "axios";

const API = (process.env.REACT_APP_BACKEND_URL || "").replace(/\/$/, "") + "/api";

// Simple module-level cache (persists during session)
let _ratesCache = null;
let _ratesCachePromise = null;

async function fetchRates() {
  if (_ratesCache) return _ratesCache;
  if (_ratesCachePromise) return _ratesCachePromise;
  _ratesCachePromise = axios
    .get(`${API}/exchange-rates/latest?base=USD`)
    .then(({ data }) => {
      _ratesCache = data?.rates || {};
      return _ratesCache;
    })
    .catch(() => {
      _ratesCache = {};
      return _ratesCache;
    })
    .finally(() => { _ratesCachePromise = null; });
  return _ratesCachePromise;
}

export default function LocalPrice({ usdAmount, profile, fallbackSymbol = "$", className = "", showOriginal = true }) {
  const [converted, setConverted] = useState(null);

  useEffect(() => {
    if (!profile) { setConverted(null); return; }
    const targetCur = profile.currency;
    if (!targetCur || targetCur === "USD") { setConverted(null); return; }
    let cancelled = false;
    fetchRates().then((rates) => {
      if (cancelled) return;
      const rate = rates[targetCur];
      if (rate && typeof rate === "number") {
        setConverted(Math.round(usdAmount * rate));
      }
    });
    return () => { cancelled = true; };
  }, [usdAmount, profile]);

  if (!profile || profile.currency === "USD" || converted === null) {
    return <span className={className}>{fallbackSymbol}{usdAmount}</span>;
  }

  const sym = profile.currency_symbol || "";
  const formatted = new Intl.NumberFormat(profile.locale || "es-DO").format(converted);

  return (
    <span className={className} data-testid="local-price">
      <span className="font-bold">{sym}{formatted}</span>
      {showOriginal && (
        <span className="text-xs text-slate-400 ml-1.5 font-normal">(~${usdAmount} USD)</span>
      )}
    </span>
  );
}
