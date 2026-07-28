import { CheckCircle, Eye, FileWarning, RefreshCw, Hand } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

/**
 * Super Admin → "Facturas Pendientes" tab body.
 *
 * Pure presentational. Mutations are routed through callbacks so the parent
 * keeps owning the data + refetch logic.
 */
export default function InvoicesPendingTab({
  pendingInvoices,
  onMarkPaid,
  onViewCompany,
}) {
  return (
    <div className="space-y-4">
      <Card className="bg-slate-900 border-slate-800">
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <CardTitle className="flex items-center gap-2">
                <FileWarning className="w-5 h-5 text-red-400" />
                Facturas pendientes
              </CardTitle>
              <CardDescription className="text-slate-400">
                Empresas con suscripción vencida — agrupadas por antigüedad de la deuda.
              </CardDescription>
            </div>
            {pendingInvoices.count > 0 && (
              <div className="flex gap-4 text-right">
                <div>
                  <p className="text-[10px] uppercase text-slate-500">Facturas</p>
                  <p className="text-2xl font-bold text-red-400">{pendingInvoices.count}</p>
                </div>
                <div>
                  <p className="text-[10px] uppercase text-slate-500">Monto total</p>
                  <p className="text-2xl font-bold text-amber-400">${pendingInvoices.total_amount.toFixed(2)}</p>
                </div>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {pendingInvoices.count === 0 ? (
            <div className="text-center py-12 text-slate-500" data-testid="no-pending-invoices">
              <CheckCircle className="w-12 h-12 mx-auto mb-3 text-emerald-500/50" />
              <p className="text-lg font-medium text-emerald-400">Sin facturas pendientes</p>
              <p className="text-sm mt-1">Todas las suscripciones están al día</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-slate-800 hover:bg-transparent">
                  <TableHead className="text-slate-400">Empresa</TableHead>
                  <TableHead className="text-slate-400">Plan</TableHead>
                  <TableHead className="text-slate-400 text-right">Monto</TableHead>
                  <TableHead className="text-slate-400">Fin período</TableHead>
                  <TableHead className="text-slate-400">Vencida</TableHead>
                  <TableHead className="text-slate-400">Renovación</TableHead>
                  <TableHead className="text-slate-400 text-right">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {pendingInvoices.items.map((inv) => (
                  <TableRow key={inv.invoice_id} className="border-slate-800" data-testid={`invoice-row-${inv.invoice_id}`}>
                    <TableCell>
                      <div>
                        <p className="font-medium">{inv.company_name}</p>
                        <p className="text-xs text-slate-500 font-mono">{inv.invoice_id}</p>
                      </div>
                    </TableCell>
                    <TableCell className="text-slate-300 text-sm">{inv.plan_id}</TableCell>
                    <TableCell className="text-right text-emerald-400 font-bold">${inv.amount.toFixed(2)} {inv.currency}</TableCell>
                    <TableCell className="text-sm text-slate-400">{new Date(inv.period_end).toLocaleDateString()}</TableCell>
                    <TableCell>
                      <Badge
                        className={`border-0 ${
                          inv.severity === "high"
                            ? "bg-red-500/20 text-red-400"
                            : inv.severity === "medium"
                            ? "bg-amber-500/20 text-amber-400"
                            : "bg-slate-500/20 text-slate-300"
                        }`}
                      >
                        {inv.days_overdue}d
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {inv.auto_renewal_active ? (
                        <Badge
                          className="border-0 bg-emerald-500/20 text-emerald-300 gap-1"
                          data-testid={`auto-renew-badge-${inv.invoice_id}`}
                        >
                          <RefreshCw className="w-3 h-3" /> Auto
                        </Badge>
                      ) : (
                        <Badge
                          className="border-0 bg-slate-500/20 text-slate-400 gap-1"
                          data-testid={`manual-renew-badge-${inv.invoice_id}`}
                        >
                          <Hand className="w-3 h-3" /> Manual
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          className="text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10"
                          onClick={() => onMarkPaid?.(inv.company_id)}
                          data-testid={`mark-paid-${inv.invoice_id}`}
                        >
                          <CheckCircle className="w-4 h-4 mr-1" /> Marcar pagada
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="text-indigo-400 hover:text-indigo-300 hover:bg-indigo-500/10"
                          onClick={() => onViewCompany?.(inv.company_id)}
                          data-testid={`view-company-${inv.invoice_id}`}
                        >
                          <Eye className="w-4 h-4 mr-1" /> Ver
                        </Button>
                      </div>
                    </TableCell>
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
