import { CheckCircle, Loader2, LogIn } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

/**
 * Super Admin → "Support Actions" tab body.
 *
 * Audit log of every mutation (POST/PUT/PATCH/DELETE) performed during a
 * Support impersonation session. Pure presentational; parent owns refresh.
 */
export default function SupportActionsTab({ actions, loading, onRefresh }) {
  return (
    <Card className="bg-slate-900 border-slate-800">
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <CardTitle className="flex items-center gap-2">
              <LogIn className="w-5 h-5 text-orange-400" />
              Acciones de soporte
            </CardTitle>
            <CardDescription className="text-slate-400">
              Auditoría de todas las mutaciones (POST/PUT/PATCH/DELETE) realizadas durante una sesión de soporte impersonada.
            </CardDescription>
          </div>
          <Button
            size="sm"
            variant="outline"
            className="bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700"
            onClick={onRefresh}
            disabled={loading}
            data-testid="support-actions-refresh-btn"
          >
            <Loader2 className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : "hidden"}`} />
            Cargar
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {actions.length === 0 ? (
          <div className="text-center py-12 text-slate-500" data-testid="no-support-actions">
            <CheckCircle className="w-12 h-12 mx-auto mb-3 text-emerald-500/50" />
            <p className="text-lg font-medium text-emerald-400">Sin acciones registradas</p>
            <p className="text-sm mt-1">Haz click en "Cargar" para consultar el log más reciente.</p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow className="border-slate-800 hover:bg-transparent">
                <TableHead className="text-slate-400">Fecha</TableHead>
                <TableHead className="text-slate-400">Soporte como</TableHead>
                <TableHead className="text-slate-400">Método</TableHead>
                <TableHead className="text-slate-400">Endpoint</TableHead>
                <TableHead className="text-slate-400 text-center">Estado</TableHead>
                <TableHead className="text-slate-400">IP</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {actions.map((row) => (
                <TableRow key={row.id} className="border-slate-800" data-testid={`support-action-${row.id}`}>
                  <TableCell className="text-slate-300 text-sm whitespace-nowrap">
                    {new Date(row.created_at).toLocaleString()}
                  </TableCell>
                  <TableCell className="text-indigo-400 text-sm">{row.email}</TableCell>
                  <TableCell>
                    <Badge
                      className={`border-0 text-[10px] ${
                        row.method === "DELETE"
                          ? "bg-red-500/20 text-red-400"
                          : row.method === "POST"
                          ? "bg-emerald-500/20 text-emerald-400"
                          : "bg-amber-500/20 text-amber-400"
                      }`}
                    >
                      {row.method}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-slate-300 font-mono text-xs">
                    {row.path}
                    {row.query ? `?${row.query}` : ""}
                  </TableCell>
                  <TableCell className="text-center">
                    <Badge
                      className={`border-0 text-[10px] ${
                        row.status_code < 300
                          ? "bg-emerald-500/20 text-emerald-400"
                          : row.status_code < 400
                          ? "bg-blue-500/20 text-blue-400"
                          : "bg-red-500/20 text-red-400"
                      }`}
                    >
                      {row.status_code}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-slate-500 font-mono text-xs">{row.ip || "—"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
