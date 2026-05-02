/**
 * AbandonedCartsTab — Super Admin tab showing abandoned-cart metrics +
 * the raw list with "Resend recovery email" action.
 */
import { useEffect, useState } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ShoppingCart, Mail, DollarSign, TrendingUp, RefreshCw, Send } from "lucide-react";
import { toast } from "sonner";

const API = (process.env.REACT_APP_BACKEND_URL || "").replace(/\/$/, "") + "/api";

const money = (v) => `$${Number(v || 0).toFixed(2)}`;
const fmtDate = (iso) => {
  if (!iso) return "—";
  try { return new Date(iso).toLocaleString(); } catch { return iso; }
};

export default function AbandonedCartsTab({ saToken }) {
  const [stats, setStats] = useState(null);
  const [carts, setCarts] = useState([]);
  const [status, setStatus] = useState("open");
  const [loading, setLoading] = useState(true);
  const [resendingId, setResendingId] = useState(null);

  const headers = { Authorization: `Bearer ${saToken}` };

  const load = async () => {
    setLoading(true);
    try {
      const [s, list] = await Promise.all([
        axios.get(`${API}/super-admin/abandoned-carts/stats`, { headers }),
        axios.get(`${API}/super-admin/abandoned-carts?status=${status}`, { headers }),
      ]);
      setStats(s.data);
      setCarts(list.data || []);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Error cargando carritos abandonados");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [status]);

  const resend = async (cartId) => {
    setResendingId(cartId);
    try {
      await axios.post(`${API}/super-admin/abandoned-carts/${cartId}/resend`, {}, { headers });
      toast.success("Email de recuperación enviado");
      load();
    } catch (err) {
      toast.error(err.response?.data?.detail || "No se pudo enviar");
    } finally {
      setResendingId(null);
    }
  };

  return (
    <div className="space-y-4" data-testid="abandoned-carts-tab">
      {/* Stats cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
        <StatCard icon={ShoppingCart} label="Carritos (30d)" value={stats?.total_carts ?? "—"} tone="slate" />
        <StatCard icon={Mail} label="Emails enviados" value={stats?.emails_sent ?? "—"} tone="blue" />
        <StatCard icon={TrendingUp} label="Recuperados" value={stats?.recovered ?? "—"} tone="emerald" />
        <StatCard icon={TrendingUp} label="Tasa recuperación" value={stats ? `${stats.recovery_rate_pct}%` : "—"} tone="emerald" />
        <StatCard icon={DollarSign} label="Revenue perdido" value={stats ? money(stats.abandoned_revenue_usd) : "—"} tone="rose" />
      </div>

      <Card className="bg-slate-900 border-slate-800">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-slate-100 text-base flex items-center gap-2">
            <ShoppingCart className="w-4 h-4" /> Carritos Abandonados
          </CardTitle>
          <div className="flex items-center gap-2">
            <Select value={status} onValueChange={setStatus}>
              <SelectTrigger className="w-[160px] bg-slate-800 border-slate-700 text-slate-200" data-testid="cart-status-filter">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="open">Abiertos</SelectItem>
                <SelectItem value="emailed">Emails enviados</SelectItem>
                <SelectItem value="recovered">Recuperados</SelectItem>
                <SelectItem value="all">Todos</SelectItem>
              </SelectContent>
            </Select>
            <Button size="sm" variant="outline" onClick={load} disabled={loading} data-testid="refresh-carts-btn">
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {carts.length === 0 ? (
            <p className="text-sm text-slate-400 text-center py-8">Sin carritos para este filtro.</p>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent border-slate-800">
                    <TableHead className="text-slate-400">Email</TableHead>
                    <TableHead className="text-slate-400">Plan</TableHead>
                    <TableHead className="text-slate-400 text-right">Emp.</TableHead>
                    <TableHead className="text-slate-400 text-right">Total</TableHead>
                    <TableHead className="text-slate-400">País</TableHead>
                    <TableHead className="text-slate-400">Creado</TableHead>
                    <TableHead className="text-slate-400">Estado</TableHead>
                    <TableHead className="text-slate-400 text-right">Acción</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {carts.map((c) => (
                    <TableRow key={c.cart_id} className="border-slate-800 hover:bg-slate-800/40" data-testid={`cart-row-${c.cart_id}`}>
                      <TableCell className="text-slate-200 font-medium">{c.email}</TableCell>
                      <TableCell className="text-slate-300">{c.plan_name || c.plan_id}</TableCell>
                      <TableCell className="text-right text-slate-300">{c.employee_count}</TableCell>
                      <TableCell className="text-right text-emerald-400 font-semibold">{money(c.amount)}</TableCell>
                      <TableCell className="text-slate-300">{c.country || "—"}</TableCell>
                      <TableCell className="text-xs text-slate-400">{fmtDate(c.created_at)}</TableCell>
                      <TableCell>
                        {c.recovered_at ? (
                          <Badge className="bg-emerald-600">Recuperado</Badge>
                        ) : c.recovery_email_sent_at ? (
                          <Badge className="bg-blue-600">Email enviado</Badge>
                        ) : (
                          <Badge className="bg-slate-600">Abierto</Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        {!c.recovered_at && (
                          <Button
                            size="sm"
                            variant="outline"
                            disabled={resendingId === c.cart_id}
                            onClick={() => resend(c.cart_id)}
                            data-testid={`cart-resend-${c.cart_id}`}
                          >
                            {resendingId === c.cart_id ? (
                              <RefreshCw className="w-3.5 h-3.5 mr-1 animate-spin" />
                            ) : (
                              <Send className="w-3.5 h-3.5 mr-1" />
                            )}
                            Reenviar
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, tone = "slate" }) {
  const tones = {
    slate: "border-slate-700 text-slate-200",
    blue: "border-blue-700/60 text-blue-200",
    emerald: "border-emerald-700/60 text-emerald-200",
    rose: "border-rose-700/60 text-rose-200",
  };
  return (
    <div className={`rounded-xl border bg-slate-900 p-4 ${tones[tone]}`}>
      <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-slate-400 mb-1.5">
        <Icon className="w-3.5 h-3.5" /> {label}
      </div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  );
}
