import { AlertTriangle, CheckCircle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

/**
 * Super Admin → "Alerts" tab body.
 *
 * Lists tenants with no activity for +30 days so the commercial team can
 * follow up. Risk badge is computed upstream and passed through.
 */
export default function AlertsTab({ alerts, getPlanBadge }) {
  return (
    <Card className="bg-slate-900 border-slate-800">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-amber-400" />
          Empresas Inactivas (+30 días)
        </CardTitle>
        <CardDescription className="text-slate-400">
          Empresas sin actividad reciente que podrían necesitar seguimiento comercial
        </CardDescription>
      </CardHeader>
      <CardContent>
        {alerts.length === 0 ? (
          <div className="text-center py-12 text-slate-500">
            <CheckCircle className="w-12 h-12 mx-auto mb-3 text-emerald-500/50" />
            <p className="text-lg font-medium text-emerald-400">Sin alertas</p>
            <p className="text-sm mt-1">Todas las empresas tienen actividad reciente</p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow className="border-slate-800 hover:bg-transparent">
                <TableHead className="text-slate-400">Empresa</TableHead>
                <TableHead className="text-slate-400">Plan</TableHead>
                <TableHead className="text-slate-400 text-center">Empleados</TableHead>
                <TableHead className="text-slate-400 text-center">Usuarios</TableHead>
                <TableHead className="text-slate-400">Días Inactivo</TableHead>
                <TableHead className="text-slate-400">Riesgo</TableHead>
                <TableHead className="text-slate-400">Última Actividad</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {alerts.map((a, idx) => (
                <TableRow key={idx} className="border-slate-800" data-testid={`alert-row-${idx}`}>
                  <TableCell>
                    <div>
                      <p className="font-medium">{a.name}</p>
                      <p className="text-xs text-slate-500 font-mono">{a.company_id}</p>
                    </div>
                  </TableCell>
                  <TableCell>{getPlanBadge(a.subscription_plan || "free", 0)}</TableCell>
                  <TableCell className="text-center">{a.employee_count}</TableCell>
                  <TableCell className="text-center">{a.user_count}</TableCell>
                  <TableCell>
                    <span className={`text-lg font-bold ${a.days_inactive >= 60 ? 'text-red-400' : 'text-amber-400'}`}>
                      {a.days_inactive}d
                    </span>
                  </TableCell>
                  <TableCell>
                    {a.risk === "high" ? (
                      <Badge className="bg-red-500/20 text-red-400 border-0">Alto</Badge>
                    ) : (
                      <Badge className="bg-amber-500/20 text-amber-400 border-0">Medio</Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-sm text-slate-400">
                    {a.last_activity ? new Date(a.last_activity).toLocaleDateString() : "—"}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
