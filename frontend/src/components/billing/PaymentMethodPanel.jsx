import { useEffect, useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  CreditCard,
  ExternalLink,
  Loader2,
  RefreshCw,
  Receipt,
  Calendar,
  ShieldCheck,
} from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL
  ? `${process.env.REACT_APP_BACKEND_URL}/api`
  : "/api";

function authHeaders() {
  const t = localStorage.getItem("token");
  return t ? { Authorization: `Bearer ${t}` } : {};
}

/**
 * PaymentMethodPanel
 * Shows the current default card + button to open Stripe Customer Portal
 * (change card, cancel subscription) + list of past renewals.
 */
export function PaymentMethodPanel() {
  const [pm, setPm] = useState(null);
  const [renewals, setRenewals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openingPortal, setOpeningPortal] = useState(false);

  const load = async () => {
    try {
      const [pmRes, histRes] = await Promise.all([
        axios.get(`${API}/checkout/payment-method`, { headers: authHeaders() }),
        axios.get(`${API}/billing/renewal-history`, { headers: authHeaders() }),
      ]);
      setPm(pmRes.data);
      setRenewals(histRes.data?.items || []);
    } catch (e) {
      // silent — nothing to show
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const openStripePortal = async () => {
    setOpeningPortal(true);
    try {
      const res = await axios.post(
        `${API}/billing/customer-portal`,
        { return_url: window.location.href },
        { headers: authHeaders() }
      );
      window.location.href = res.data.portal_url;
    } catch (err) {
      toast.error(err?.response?.data?.detail || "No se pudo abrir el portal de Stripe");
      setOpeningPortal(false);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="py-8 flex items-center justify-center">
          <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
        </CardContent>
      </Card>
    );
  }

  const hasCard = pm?.has_payment_method;

  return (
    <div className="space-y-4" data-testid="payment-method-panel">
      {/* Current payment method card */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              <CreditCard className="w-5 h-5 text-blue-600" />
              Método de pago
            </CardTitle>
            <ShieldCheck className="w-4 h-4 text-emerald-500" title="Procesado por Stripe" />
          </div>
        </CardHeader>
        <CardContent>
          {hasCard ? (
            <div
              className="flex items-center justify-between gap-4 flex-wrap"
              data-testid="current-payment-method"
            >
              <div className="flex items-center gap-3">
                <div className="bg-gradient-to-br from-slate-800 to-slate-900 text-white rounded-lg px-4 py-3 min-w-[220px]">
                  <div className="text-[10px] uppercase tracking-wide opacity-70">
                    {pm.payment_method.brand}
                  </div>
                  <div className="text-lg font-mono tracking-widest mt-1">
                    •••• •••• •••• {pm.payment_method.last4}
                  </div>
                  <div className="text-xs opacity-70 mt-1">
                    Vence {String(pm.payment_method.exp_month).padStart(2, "0")}/
                    {String(pm.payment_method.exp_year).slice(-2)}
                  </div>
                </div>
                <div className="text-xs text-slate-500">
                  Se usa para los cobros mensuales automáticos.
                </div>
              </div>
              <Button
                variant="outline"
                onClick={openStripePortal}
                disabled={openingPortal}
                data-testid="open-stripe-portal-btn"
              >
                {openingPortal ? (
                  <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                ) : (
                  <ExternalLink className="w-4 h-4 mr-1" />
                )}
                Cambiar tarjeta
              </Button>
            </div>
          ) : (
            <div className="text-sm text-slate-500 py-3">
              Todavía no hay un método de pago guardado. Activa la renovación
              automática al pagar tu próxima factura para guardar tu tarjeta.
            </div>
          )}
        </CardContent>
      </Card>

      {/* Renewal history */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <RefreshCw className="w-5 h-5 text-blue-600" />
            Historial de renovaciones
          </CardTitle>
        </CardHeader>
        <CardContent>
          {renewals.length === 0 ? (
            <div className="text-sm text-slate-500 py-3">
              Aún no hay renovaciones registradas.
            </div>
          ) : (
            <div className="divide-y" data-testid="renewal-history-list">
              {renewals.map((r) => (
                <div
                  key={r.invoice_id}
                  className="py-3 flex items-center justify-between gap-2 flex-wrap"
                  data-testid={`renewal-row-${r.invoice_id}`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <Receipt className="w-4 h-4 text-slate-400 flex-shrink-0" />
                    <div className="min-w-0">
                      <div className="text-sm font-medium text-slate-800 dark:text-slate-200 truncate">
                        {r.plan_name || "Suscripción"}
                      </div>
                      <div className="text-[11px] text-slate-500 flex items-center gap-1 flex-wrap">
                        <Calendar className="w-3 h-3" />
                        {r.paid_at || (r.paid_at_iso ? new Date(r.paid_at_iso).toLocaleDateString() : "—")}
                        {r.source === "stripe_auto_renewal" ? (
                          <Badge
                            variant="outline"
                            className="text-[10px] px-1 py-0 border-emerald-300 text-emerald-700 ml-1"
                          >
                            Auto
                          </Badge>
                        ) : null}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold text-slate-800 dark:text-slate-200">
                      ${Number(r.total).toFixed(2)}
                      <span className="text-xs text-slate-500 ml-1">
                        {r.currency}
                      </span>
                    </div>
                    <div className="text-[10px] text-slate-400 font-mono">
                      {r.invoice_number}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
