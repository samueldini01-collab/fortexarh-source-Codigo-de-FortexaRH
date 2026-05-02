/**
 * ExitIntentModal
 * Captures the visitor's email when they show intent to leave /checkout
 * without completing payment. Feeds directly into the abandoned-cart
 * tracking endpoint so the recovery cron can email them later.
 *
 * Trigger heuristics:
 *   - Desktop: mouseleave near the top edge (mouse heading to tab/close).
 *   - Mobile:  visibilitychange → "hidden" on touch devices (app switch / back).
 *   - Only fires once per session (sessionStorage flag).
 */
import { useEffect, useRef, useState } from "react";
import axios from "axios";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Mail, Gift, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useTranslation } from "react-i18next";

const API = (process.env.REACT_APP_BACKEND_URL || "").replace(/\/$/, "") + "/api";
const SESSION_FLAG = "fortexarh_exit_intent_shown";

const isValidEmail = (v) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);

export default function ExitIntentModal({
  planId,
  employeeCount,
  amount,
  currency = "usd",
  currentEmail = "",
  enabled = true,
  onCaptured,
}) {
  const { t, i18n } = useTranslation();
  const [open, setOpen] = useState(false);
  const [email, setEmail] = useState(currentEmail || "");
  const [sending, setSending] = useState(false);
  const alreadyShown = useRef(false);

  useEffect(() => {
    if (!enabled) return;
    if (sessionStorage.getItem(SESSION_FLAG) === "1") {
      alreadyShown.current = true;
      return;
    }

    // Desktop: mouseleave from the top of the viewport
    const handleMouseLeave = (e) => {
      if (alreadyShown.current) return;
      if (e.clientY > 8) return;           // must be heading up
      if ((e.relatedTarget || e.toElement) !== null) return;
      triggerModal();
    };

    // Mobile fallback: tab switch / background
    const handleVisibility = () => {
      if (document.visibilityState === "hidden" && !alreadyShown.current) {
        // Delay so it only shows when the user comes back
        setTimeout(() => {
          if (!alreadyShown.current) triggerModal();
        }, 300);
      }
    };

    const triggerModal = () => {
      alreadyShown.current = true;
      sessionStorage.setItem(SESSION_FLAG, "1");
      setOpen(true);
    };

    document.addEventListener("mouseleave", handleMouseLeave);
    document.addEventListener("visibilitychange", handleVisibility);
    return () => {
      document.removeEventListener("mouseleave", handleMouseLeave);
      document.removeEventListener("visibilitychange", handleVisibility);
    };
  }, [enabled]);

  // Keep prefilled email in sync if parent updates it
  useEffect(() => {
    if (currentEmail) setEmail(currentEmail);
  }, [currentEmail]);

  const handleSubmit = async () => {
    if (!isValidEmail(email)) {
      toast.error(t("checkout.exitIntent.invalidEmail", "Ingresa un email válido"));
      return;
    }
    setSending(true);
    try {
      const { data } = await axios.post(`${API}/public/abandoned-carts`, {
        email,
        plan_id: planId,
        employee_count: employeeCount,
        origin_url: window.location.origin,
        country: (localStorage.getItem("fortexarh-landing-country") || "").toUpperCase() || null,
        language: i18n.language?.split("-")[0] || "es",
      });
      toast.success(t("checkout.exitIntent.success", "¡Te enviamos el link para retomarlo!"));
      if (onCaptured) onCaptured({ email, cart_id: data?.cart_id });
      setOpen(false);
    } catch (err) {
      toast.error(err.response?.data?.detail || t("common.error", "Algo salió mal"));
    } finally {
      setSending(false);
    }
  };

  const fmtAmount = typeof amount === "number"
    ? new Intl.NumberFormat("en-US", { style: "currency", currency: (currency || "USD").toUpperCase() }).format(amount)
    : null;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="sm:max-w-md" data-testid="exit-intent-modal">
        <DialogHeader>
          <div className="flex items-start gap-3">
            <div className="w-12 h-12 rounded-xl bg-emerald-100 flex items-center justify-center flex-shrink-0">
              <Gift className="w-6 h-6 text-emerald-600" />
            </div>
            <div>
              <DialogTitle className="text-left text-lg">
                {t("checkout.exitIntent.title", "¿Te ayudo a completar?")}
              </DialogTitle>
              <DialogDescription className="text-left mt-1.5">
                {t(
                  "checkout.exitIntent.description",
                  "Déjanos tu email y te enviamos el link para terminar tu suscripción cuando quieras. Sin compromiso.",
                )}
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        {fmtAmount && (
          <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm">
            <div className="flex justify-between text-slate-600">
              <span>{t("checkout.exitIntent.yourCart", "Tu carrito")}</span>
              <span className="font-semibold text-slate-800">{fmtAmount}/mo</span>
            </div>
            <div className="text-xs text-slate-500 mt-1">
              {employeeCount} {t("landing.pricing.features.employees", "empleados")}
            </div>
          </div>
        )}

        <div className="space-y-2 mt-2">
          <Label htmlFor="exit-email" className="flex items-center gap-2 text-slate-700 font-medium text-sm">
            <Mail className="w-4 h-4" />
            {t("checkout.email.label", "Tu email")}
          </Label>
          <Input
            id="exit-email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder={t("checkout.email.placeholder", "tu@empresa.com")}
            data-testid="exit-intent-email-input"
            onKeyDown={(e) => { if (e.key === "Enter" && isValidEmail(email)) handleSubmit(); }}
          />
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            variant="ghost"
            onClick={() => setOpen(false)}
            disabled={sending}
            data-testid="exit-intent-dismiss"
          >
            {t("checkout.exitIntent.dismiss", "Ahora no")}
          </Button>
          <Button
            className="bg-emerald-600 hover:bg-emerald-700"
            disabled={sending || !isValidEmail(email)}
            onClick={handleSubmit}
            data-testid="exit-intent-submit"
          >
            {sending ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                {t("checkout.buttons.processing", "Procesando...")}
              </>
            ) : (
              <>
                <Mail className="w-4 h-4 mr-2" />
                {t("checkout.exitIntent.sendLink", "Enviarme el link")}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
