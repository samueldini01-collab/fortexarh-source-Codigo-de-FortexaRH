import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { API } from "@/App";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { CreditCard, AlertCircle, LogOut, ShieldCheck, Loader2, RefreshCw, Calendar, Info } from "lucide-react";
import { toast } from "sonner";

function authHeaders() {
  const t = localStorage.getItem("token");
  return t ? { Authorization: `Bearer ${t}` } : {};
}

export default function BillingRequiredPage() {
  const navigate = useNavigate();
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [paying, setPaying] = useState(false);
  const [authorizedRecurring, setAuthorizedRecurring] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await axios.get(`${API}/billing/status`, { headers: authHeaders() });
        setStatus(res.data);
        // If everything is fine, send them back to the dashboard.
        if (!res.data.has_pending && !res.data.is_blocked) {
          navigate("/dashboard", { replace: true });
        }
      } catch {
        // ignore — show generic error state
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [navigate]);

  const handleActivateAutoRenewal = async () => {
    if (!status?.pending_invoice?.invoice_id) return;
    if (!authorizedRecurring) {
      toast.error("Debes autorizar los cargos periódicos para continuar.");
      return;
    }
    setPaying(true);
    try {
      const res = await axios.post(
        `${API}/billing/setup-auto-renewal`,
        {
          invoice_id: status.pending_invoice.invoice_id,
          origin_url: window.location.origin,
          authorized_recurring: true,
        },
        { headers: authHeaders() }
      );
      window.location.href = res.data.checkout_url;
    } catch (err) {
      toast.error(err.response?.data?.detail || "No se pudo iniciar el pago");
      setPaying(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.href = "/login";
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
      </div>
    );
  }

  const inv = status?.pending_invoice;
  const blocked = status?.is_blocked;
  const grace = status?.grace_days_left ?? 0;
  const monthlyAmount = inv ? Number(inv.total).toFixed(2) : "0.00";
  const currency = inv?.currency || "USD";

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-100 to-slate-200 dark:from-slate-900 dark:to-slate-950 px-4 py-10">
      <Card
        className={`max-w-xl w-full border-2 ${blocked ? "border-red-300" : "border-amber-300"}`}
        data-testid="billing-required-card"
      >
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className={`rounded-full p-3 ${blocked ? "bg-red-100 text-red-600" : "bg-amber-100 text-amber-600"}`}>
              <AlertCircle className="w-7 h-7" />
            </div>
            <div>
              <CardTitle className="text-xl">
                {blocked ? "Suscripción suspendida" : "Pago pendiente"}
              </CardTitle>
              <CardDescription>
                {blocked
                  ? "Tu suscripción fue suspendida por falta de pago. Regulariza el pago para reanudar el acceso."
                  : `Tu próximo período está pendiente de pago. ${grace > 0 ? `Tienes ${grace} día(s) antes de la suspensión.` : "El acceso será suspendido pronto."}`}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-5">
          {inv && (
            <div className="rounded-lg border bg-slate-50 dark:bg-slate-900/50 p-4" data-testid="billing-required-invoice">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs uppercase text-slate-500 font-semibold">Factura</p>
                <p className="text-sm font-mono text-slate-700 dark:text-slate-300">{inv.invoice_number}</p>
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-xs text-slate-500">Plan</p>
                  <p className="font-medium text-slate-800 dark:text-slate-200">{inv.plan_name}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Empleados</p>
                  <p className="font-medium text-slate-800 dark:text-slate-200">{inv.employee_count}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Período</p>
                  <p className="font-medium text-slate-800 dark:text-slate-200">{inv.period_start} → {inv.period_end}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Monto</p>
                  <p className="text-xl font-bold text-emerald-600">
                    ${monthlyAmount} <span className="text-xs text-slate-400">{currency}</span>
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Auto-renewal consent panel */}
          <div
            className="rounded-lg border-2 border-blue-300 bg-blue-50 dark:bg-blue-950/40 p-4 space-y-3"
            data-testid="auto-renewal-consent-panel"
          >
            <div className="flex items-start gap-2">
              <RefreshCw className="w-5 h-5 text-blue-600 mt-0.5" />
              <div className="flex-1">
                <p className="font-semibold text-slate-800 dark:text-slate-100 text-sm">
                  Activación de renovación automática
                </p>
                <p className="text-xs text-slate-600 dark:text-slate-300 mt-1">
                  Al continuar, tu tarjeta será cobrada hoy por el monto pendiente y
                  quedará guardada de forma segura por Stripe para cobros mensuales
                  futuros. Ya no tendrás que ingresar manualmente al pagar cada mes.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs bg-white dark:bg-slate-800 rounded p-3">
              <div className="flex items-center gap-2">
                <CreditCard className="w-4 h-4 text-slate-500" />
                <div>
                  <p className="text-slate-500">Monto recurrente</p>
                  <p className="font-semibold text-slate-800 dark:text-slate-100">
                    ${monthlyAmount} {currency}/mes
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-slate-500" />
                <div>
                  <p className="text-slate-500">Frecuencia</p>
                  <p className="font-semibold text-slate-800 dark:text-slate-100">Mensual</p>
                </div>
              </div>
            </div>

            <label className="flex items-start gap-2 cursor-pointer" data-testid="auto-renewal-consent-label">
              <Checkbox
                checked={authorizedRecurring}
                onCheckedChange={(v) => setAuthorizedRecurring(Boolean(v))}
                data-testid="auto-renewal-consent-checkbox"
                className="mt-0.5"
              />
              <span className="text-xs text-slate-700 dark:text-slate-200 leading-relaxed">
                <strong>Autorizo a FortexaRH</strong> a cobrar{" "}
                <strong>${monthlyAmount} {currency}</strong> mensualmente en mi método de pago
                a partir de hoy, hasta que cancele la suscripción desde el portal.
              </span>
            </label>

            <div className="flex items-start gap-1 text-[10px] text-slate-500">
              <Info className="w-3 h-3 mt-0.5 flex-shrink-0" />
              <span>
                Puedes cancelar la suscripción en cualquier momento desde
                <em> Suscripción → Cancelar</em>. No hay penalidades.
              </span>
            </div>
          </div>

          <Button
            className="w-full bg-emerald-600 hover:bg-emerald-700 text-white py-6 text-base"
            onClick={handleActivateAutoRenewal}
            disabled={paying || !inv || !authorizedRecurring}
            data-testid="billing-pay-now-btn"
          >
            {paying ? (
              <Loader2 className="w-5 h-5 mr-2 animate-spin" />
            ) : (
              <CreditCard className="w-5 h-5 mr-2" />
            )}
            Pagar y activar renovación automática
          </Button>

          <div className="flex items-center justify-center gap-2 text-xs text-slate-500">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>Pago seguro procesado por Stripe. No guardamos tus datos de tarjeta.</span>
          </div>

          <button
            onClick={handleLogout}
            className="w-full text-center text-sm text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 flex items-center justify-center gap-1 mt-2"
            data-testid="billing-logout-btn"
          >
            <LogOut className="w-3.5 h-3.5" />
            Cerrar sesión
          </button>
        </CardContent>
      </Card>
    </div>
  );
}
