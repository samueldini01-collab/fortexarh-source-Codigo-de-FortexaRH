import { AlertTriangle, CheckCircle, CreditCard } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

/**
 * Super Admin → "Revenue" tab body.
 *
 * Pure presentational component. All data comes from the parent's already-
 * fetched ``revenue`` object; ``getPaymentBadge`` is reused from the parent.
 */
export default function RevenueTab({ revenue, getPaymentBadge }) {
  return (
    <div className="space-y-4">
      {/* Revenue KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-emerald-900/40 to-slate-900 border-emerald-800">
          <CardContent className="p-4">
            <p className="text-xs text-emerald-400 uppercase tracking-wider">MRR</p>
            <p className="text-2xl font-bold text-emerald-300 mt-1">${(revenue.mrr || 0).toLocaleString()}</p>
            <p className="text-[10px] text-slate-500 mt-1">Monthly Recurring Revenue</p>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-sky-900/40 to-slate-900 border-sky-800">
          <CardContent className="p-4">
            <p className="text-xs text-sky-400 uppercase tracking-wider">ARR</p>
            <p className="text-2xl font-bold text-sky-300 mt-1">${(revenue.arr || 0).toLocaleString()}</p>
            <p className="text-[10px] text-slate-500 mt-1">Annual Recurring Revenue</p>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-purple-900/40 to-slate-900 border-purple-800">
          <CardContent className="p-4">
            <p className="text-xs text-purple-400 uppercase tracking-wider">Partners</p>
            <p className="text-2xl font-bold text-purple-300 mt-1">{revenue.partner_companies || 0}</p>
            <p className="text-[10px] text-slate-500 mt-1">MRR: ${(revenue.partner_mrr || 0).toLocaleString()}</p>
          </CardContent>
        </Card>
        <Card className={`bg-gradient-to-br ${(revenue.overdue_count || 0) > 0 ? 'from-red-900/40 border-red-800' : 'from-slate-800/40 border-slate-700'} to-slate-900`}>
          <CardContent className="p-4">
            <p className={`text-xs uppercase tracking-wider ${(revenue.overdue_count || 0) > 0 ? 'text-red-400' : 'text-slate-400'}`}>Vencidos</p>
            <p className={`text-2xl font-bold mt-1 ${(revenue.overdue_count || 0) > 0 ? 'text-red-300' : 'text-slate-300'}`}>{revenue.overdue_count || 0}</p>
            <p className="text-[10px] text-slate-500 mt-1">Pagos pendientes</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Plan Distribution */}
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader className="pb-3">
            <CardTitle className="text-base text-white">Distribucion por Plan</CardTitle>
            <CardDescription className="text-slate-500">Empresas por tipo de plan</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {Object.entries(revenue.plan_distribution || {}).map(([key, val]) => (
              <div key={key} className="flex items-center justify-between p-2 rounded-lg bg-slate-800/50">
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${val.type === 'partner' ? 'bg-purple-400' : val.type === 'trial' || val.type === 'free' ? 'bg-slate-500' : 'bg-emerald-400'}`} />
                  <span className="text-sm text-white">{val.plan_name}</span>
                  {val.type === "partner" && <Badge className="bg-purple-500/20 text-purple-400 border-0 text-[10px]">Partner</Badge>}
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-sm text-slate-400">{val.count} empresas</span>
                  <span className="text-sm font-medium text-emerald-400 w-28 text-right">${val.mrr.toLocaleString()}/mes</span>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Overdue Alerts */}
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader className="pb-3">
            <CardTitle className="text-base text-white flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-400" /> Alertas de Pago
            </CardTitle>
            <CardDescription className="text-slate-500">Empresas con pago vencido</CardDescription>
          </CardHeader>
          <CardContent>
            {(revenue.overdue_alerts || []).length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                <CheckCircle className="w-8 h-8 mx-auto mb-2 text-emerald-600" />
                <p className="text-sm">No hay pagos vencidos</p>
              </div>
            ) : (
              <div className="space-y-2">
                {revenue.overdue_alerts.map((alert, i) => (
                  <div key={i} className="p-3 rounded-lg bg-red-500/10 border border-red-800/50">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-white">{alert.company_name || alert.company_id}</span>
                      <Badge className="bg-red-500/20 text-red-400 border-0">{alert.days_overdue}d vencido</Badge>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">{alert.plan} - ${(alert.monthly || 0).toLocaleString()}/mes</p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Payment History */}
      <Card className="bg-slate-900 border-slate-800">
        <CardHeader className="pb-3">
          <CardTitle className="text-base text-white flex items-center gap-2">
            <CreditCard className="w-5 h-5 text-indigo-400" /> Historial de Activaciones / Pagos
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {(revenue.payment_history || []).length === 0 ? (
            <div className="text-center py-8 text-slate-500">No hay registros de pago</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-slate-800">
                  <TableHead className="text-slate-400">Fecha</TableHead>
                  <TableHead className="text-slate-400">Empresa</TableHead>
                  <TableHead className="text-slate-400">Modalidad</TableHead>
                  <TableHead className="text-slate-400 text-right">Monto</TableHead>
                  <TableHead className="text-slate-400">Notas</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(revenue.payment_history || []).map((p, i) => (
                  <TableRow key={p.activation_id || i} className="border-slate-800">
                    <TableCell className="text-slate-300 text-sm">{(p.created_at || "").split("T")[0]}</TableCell>
                    <TableCell className="text-white text-sm">{p.company_name || p.company_id}</TableCell>
                    <TableCell>{getPaymentBadge(p.payment_method || "sin_definir")}</TableCell>
                    <TableCell className="text-right text-emerald-400 font-mono">${(p.amount || 0).toLocaleString()}</TableCell>
                    <TableCell className="text-slate-500 text-sm max-w-[200px] truncate">{p.notes || "-"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
