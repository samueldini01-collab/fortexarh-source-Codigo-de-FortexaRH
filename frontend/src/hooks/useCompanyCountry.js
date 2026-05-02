/**
 * useCompanyCountry — fetches the logged-in company's country code from
 * /api/country-config/company. Result is cached at the module level so that
 * multiple consumers (DashboardLayout, DGIIReportsPage, …) share a single
 * network request per session.
 *
 * Returns { countryCode, profile, loading } where countryCode defaults to
 * "DO" if the profile cannot be loaded (safe default for the legacy DR
 * behavior).
 */
import { useEffect, useState } from "react";
import axios from "axios";
import { useAuth, API } from "@/App";

let _cache = null;
let _inflight = null;

export function invalidateCompanyCountry() {
  _cache = null;
  _inflight = null;
}

export default function useCompanyCountry() {
  const { user, getAuthHeaders } = useAuth();
  const [state, setState] = useState(() => ({
    countryCode: _cache?.code || null,
    profile: _cache || null,
    loading: !_cache && !!user,
  }));

  useEffect(() => {
    if (!user) {
      setState({ countryCode: null, profile: null, loading: false });
      return;
    }

    if (_cache) {
      setState({ countryCode: _cache.code, profile: _cache, loading: false });
      return;
    }

    let cancelled = false;
    const run = async () => {
      try {
        if (!_inflight) {
          _inflight = axios
            .get(`${API}/country-config/company`, {
              headers: getAuthHeaders(),
              withCredentials: true,
            })
            .then(({ data }) => {
              // API returns { country_code, profile } — normalize to profile shape
              _cache = data?.profile ? { ...data.profile, code: data.country_code || data.profile.code } : data;
              return _cache;
            })
            .catch(() => {
              _cache = null;
              return null;
            })
            .finally(() => {
              _inflight = null;
            });
        }
        const profile = await _inflight;
        if (!cancelled) {
          setState({
            countryCode: profile?.code || "DO",
            profile,
            loading: false,
          });
        }
      } catch {
        if (!cancelled) {
          setState({ countryCode: "DO", profile: null, loading: false });
        }
      }
    };
    run();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id]);

  return state;
}
