import { useEffect, useState } from "react";
import { ShieldAlert, X } from "lucide-react";

/**
 * Persistent banner shown across the app when a Super Admin has impersonated a
 * customer account (read: support session). Decodes the JWT to compute the
 * remaining lifetime and auto-cleans the support flag once the token expires.
 */
function decodeJwtPayload(token) {
  try {
    const part = token.split(".")[1];
    const padded = part.replace(/-/g, "+").replace(/_/g, "/");
    const json = decodeURIComponent(
      atob(padded)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
    return JSON.parse(json);
  } catch {
    return null;
  }
}

export default function SupportSessionBanner() {
  const [active, setActive] = useState(false);
  const [companyName, setCompanyName] = useState("");
  const [remaining, setRemaining] = useState(0);

  useEffect(() => {
    const compute = () => {
      const flag = localStorage.getItem("fortexa_support_session") === "1";
      const token = localStorage.getItem("token");
      if (!flag || !token) {
        setActive(false);
        return;
      }
      const payload = decodeJwtPayload(token);
      if (!payload || !payload.support_session) {
        setActive(false);
        return;
      }
      const now = Math.floor(Date.now() / 1000);
      const exp = payload.exp || 0;
      const left = Math.max(0, exp - now);
      if (left <= 0) {
        // Expired — clean up.
        localStorage.removeItem("fortexa_support_session");
        localStorage.removeItem("fortexa_support_company");
        setActive(false);
        return;
      }
      setActive(true);
      setRemaining(left);
      setCompanyName(localStorage.getItem("fortexa_support_company") || "");
    };
    compute();
    const id = setInterval(compute, 30000); // tick every 30s
    return () => clearInterval(id);
  }, []);

  if (!active) return null;

  const mins = Math.floor(remaining / 60);
  const handleExit = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    localStorage.removeItem("fortexa_support_session");
    localStorage.removeItem("fortexa_support_company");
    window.location.href = "/admin";
  };

  return (
    <div
      className="fixed top-0 inset-x-0 z-[60] bg-amber-500 text-amber-950 px-4 py-2 flex flex-wrap items-center justify-center gap-3 text-sm font-medium shadow-lg"
      data-testid="support-session-banner"
    >
      <ShieldAlert className="w-4 h-4 shrink-0" />
      <span>
        Sesión de soporte activa
        {companyName ? <> en <b>{companyName}</b></> : null}
        {" — "}finaliza en <b>{mins} min</b>
      </span>
      <button
        onClick={handleExit}
        className="inline-flex items-center gap-1 bg-amber-950 text-amber-100 hover:bg-black px-2 py-0.5 rounded text-xs font-semibold"
        data-testid="support-session-exit-btn"
      >
        <X className="w-3.5 h-3.5" /> Salir de soporte
      </button>
    </div>
  );
}
