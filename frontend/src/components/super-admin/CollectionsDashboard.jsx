import { useEffect, useState, useCallback } from "react";
import axios from "axios";
import { API } from "@/App";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Loader2, TrendingDown, DollarSign, AlertTriangle, MailCheck, RefreshCw, Trophy } from "lucide-react";
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid, Legend,
  BarChart, Bar, Cell,
} from "recharts";

const SEVERITY_COLORS = ["#10b981", "#f59e0b", "#ef4444", "#7f1d1d"];

function fmt(n) {
  return `$${(Number(n) || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export default function CollectionsDashboard({ token }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [windowDays, setWindowDays] = useState(90);

  const headers = { Authorization: `Bearer ${token}` };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/super-admin/collections/dashboard?days=${windowDays}`, { headers });
      setData(res.data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [windowDays, token]);

  useEffect(() => { load(); }, [load]);

  if (!data) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="w-6 h-6 animate-spin text-emerald-400" />
      </div>
    );
  }

  const k = data.kpis;
  const aging = data.aging_buckets || [];
  const curve = (data.daily_curve || []).map(r => ({
    ...r,
    label: r.date.slice(5), // MM-DD
  }));
  const top = data.top_offenders || [];

  return (
    <div className="space-y-4" data-testid="collections-dashboard">
      <Card className="bg-slate-900 border-slate-800">
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <CardTitle className="flex items-center gap-2 text-slate-100">
                <DollarSign className="w-5 h-5 text-emerald-400" />
                Dashboard de cobranza
              </CardTitle>
              <CardDescription className="text-slate-400">
                Ventana: últimos {data.window_days} días. Curva, recuperación tras emails y ranking de morosos.
              </CardDescription>
            </div>
            <div className="flex gap-2 items-center">
              {[30, 90, 180, 365].map(d => (
                <Button
                  key={d}
                  size="sm"
                  variant={windowDays === d ? "default" : "outline"}
                  className={windowDays === d ? "bg-emerald-600 hover:bg-emerald-700" : "bg-slate-800 border-slate-700 text-slate-300"}
                  onClick={() => setWindowDays(d)}
                  data-testid={`collections-window-${d}`}
                >
                  {d}d
                </Button>
              ))}
              <Button size="sm" variant="outline" className="bg-slate-800 border-slate-700 text-slate-300" onClick={load} disabled={loading} data-testid="collections-refresh-btn">
                <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* KPI cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3" data-testid="collections-kpis">
        <Card className="bg-slate-900 border-slate-800">
          <CardContent className="p-4">
            <p className="text-xs uppercase text-slate-500 mb-1">Saldo pendiente</p>
            <p className="text-2xl font-bold text-amber-400">{fmt(k.outstanding_amount)}</p>
            <p className="text-xs text-slate-500 mt-0.5">{k.pending_count} factura(s)</p>
          </CardContent>
        </Card>
        <Card className="bg-slate-900 border-slate-800">
          <CardContent className="p-4">
            <p className="text-xs uppercase text-slate-500 mb-1">Suspendidos</p>
            <p className="text-2xl font-bold text-red-400">{k.suspended_count}</p>
            <p className="text-xs text-slate-500 mt-0.5">{k.past_due_count} en mora</p>
          </CardContent>
        </Card>
        <Card className="bg-slate-900 border-slate-800">
          <CardContent className="p-4">
            <p className="text-xs uppercase text-slate-500 mb-1 flex items-center gap-1"><MailCheck className="w-3 h-3" /> Recup. tras email "vencida"</p>
            <p className="text-2xl font-bold text-emerald-400">{k.recovery_rate_due}%</p>
            <p className="text-xs text-slate-500 mt-0.5">{k.due_emails_recovered} / {k.due_emails_sent}</p>
          </CardContent>
        </Card>
        <Card className="bg-slate-900 border-slate-800">
          <CardContent className="p-4">
            <p className="text-xs uppercase text-slate-500 mb-1 flex items-center gap-1"><AlertTriangle className="w-3 h-3" /> Recup. tras último aviso</p>
            <p className="text-2xl font-bold text-emerald-400">{k.recovery_rate_final}%</p>
            <p className="text-xs text-slate-500 mt-0.5">{k.final_emails_recovered} / {k.final_emails_sent}</p>
          </CardContent>
        </Card>
      </div>

      {/* Curve */}
      <Card className="bg-slate-900 border-slate-800">
        <CardHeader>
          <CardTitle className="text-base text-slate-100 flex items-center gap-2">
            <TrendingDown className="w-4 h-4 text-amber-400" /> Curva diaria de pagos pendientes vs cobrados
          </CardTitle>
        </CardHeader>
        <CardContent>
          {curve.length === 0 ? (
            <p className="text-slate-500 text-sm py-8 text-center">Sin datos en esta ventana.</p>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={curve}>
                <defs>
                  <linearGradient id="colPending" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.6} />
                    <stop offset="100%" stopColor="#f59e0b" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colPaid" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#10b981" stopOpacity={0.6} />
                    <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="label" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 6, color: "#e2e8f0" }}
                  formatter={(v) => fmt(v)}
                />
                <Legend wrapperStyle={{ color: "#cbd5e1", fontSize: 12 }} />
                <Area type="monotone" dataKey="created_amount" name="Pendiente creada" stroke="#f59e0b" fill="url(#colPending)" />
                <Area type="monotone" dataKey="paid_amount" name="Cobrada" stroke="#10b981" fill="url(#colPaid)" />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      {/* Aging buckets */}
      <Card className="bg-slate-900 border-slate-800">
        <CardHeader>
          <CardTitle className="text-base text-slate-100">Antigüedad de saldo pendiente</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={aging}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="label" stroke="#64748b" fontSize={11} />
              <YAxis stroke="#64748b" fontSize={11} />
              <Tooltip
                contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 6, color: "#e2e8f0" }}
                formatter={(v, name) => name === "amount" ? fmt(v) : v}
              />
              <Bar dataKey="amount" name="Monto" radius={[6, 6, 0, 0]}>
                {aging.map((_, i) => (<Cell key={i} fill={SEVERITY_COLORS[i]} />))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Top offenders */}
      <Card className="bg-slate-900 border-slate-800">
        <CardHeader>
          <CardTitle className="text-base text-slate-100 flex items-center gap-2">
            <Trophy className="w-4 h-4 text-amber-400" /> Top 10 clientes con más recurrencia de impago
          </CardTitle>
          <CardDescription className="text-slate-400">Cuenta de facturas (pendientes + pagadas) en la ventana.</CardDescription>
        </CardHeader>
        <CardContent className="px-0">
          {top.length === 0 ? (
            <p className="text-slate-500 text-sm py-8 text-center">Sin clientes con recurrencia de impago.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-xs uppercase text-slate-500 border-b border-slate-800">
                  <tr>
                    <th className="text-left px-4 py-2">Empresa</th>
                    <th className="text-right px-4 py-2">Facturas</th>
                    <th className="text-right px-4 py-2">Saldo pendiente</th>
                    <th className="text-right px-4 py-2">Pagado</th>
                    <th className="text-left px-4 py-2">Estado sub.</th>
                  </tr>
                </thead>
                <tbody>
                  {top.map((o) => (
                    <tr key={o.company_id} className="border-b border-slate-800/50 hover:bg-slate-800/30" data-testid={`offender-${o.company_id}`}>
                      <td className="px-4 py-2 text-slate-200">{o.company_name}</td>
                      <td className="px-4 py-2 text-right text-slate-300">{o.invoice_count}</td>
                      <td className="px-4 py-2 text-right text-amber-400 font-bold">{fmt(o.outstanding)}</td>
                      <td className="px-4 py-2 text-right text-emerald-400">{fmt(o.paid_total)}</td>
                      <td className="px-4 py-2">
                        <Badge className={`border-0 text-[10px] ${
                          o.subscription_status === "suspended" ? "bg-red-500/20 text-red-400" :
                          o.subscription_status === "past_due"  ? "bg-amber-500/20 text-amber-400" :
                          o.subscription_status === "active"    ? "bg-emerald-500/20 text-emerald-400" :
                          "bg-slate-500/20 text-slate-300"
                        }`}>
                          {o.subscription_status}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
