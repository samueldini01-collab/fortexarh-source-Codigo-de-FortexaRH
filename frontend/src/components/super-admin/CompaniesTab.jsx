import {
  ArrowUpDown,
  ChevronRight,
  Columns3,
  Power,
  PowerOff,
  Search,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

/**
 * Super Admin → "Companies" tab body.
 *
 * Pure presentational. Owns nothing — search input, visible columns,
 * filtered list, and every callback flow in via props so the parent
 * page keeps controlling everything.
 */
export default function CompaniesTab({
  search,
  onSearchChange,
  companies,
  filtered,
  loading,
  allColumns,
  visibleCols,
  toggleColumn,
  isColVisible,
  getPlanBadge,
  getPaymentBadge,
  onDrillDown,
  onOpenPlanDialog,
  onOpenDeactivate,
  onOpenActivate,
}) {
  return (
    <>
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <Input
            placeholder="Buscar empresa o RNC..."
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-9 bg-slate-900 border-slate-700 text-white"
            data-testid="sa-search"
          />
        </div>
        <Badge variant="outline" className="text-slate-400 border-slate-700">
          {filtered.length} de {companies.length}
        </Badge>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              size="sm"
              variant="ghost"
              className="text-slate-400 hover:text-white"
              data-testid="btn-column-config"
            >
              <Columns3 className="w-4 h-4 mr-1" /> Columnas
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="bg-slate-900 border-slate-700">
            {allColumns.map((col) => (
              <DropdownMenuCheckboxItem
                key={col.key}
                checked={visibleCols.includes(col.key)}
                disabled={col.locked}
                onCheckedChange={() => toggleColumn(col.key)}
                className="text-slate-300"
              >
                {col.label}
              </DropdownMenuCheckboxItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <Card className="bg-slate-900 border-slate-800 overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="border-slate-800 hover:bg-slate-800/50">
              {isColVisible("name") && <TableHead className="text-slate-400">Empresa</TableHead>}
              {isColVisible("status") && <TableHead className="text-slate-400">Estado</TableHead>}
              {isColVisible("plan") && <TableHead className="text-slate-400">Plan</TableHead>}
              {isColVisible("monthly_billing") && (
                <TableHead className="text-slate-400 text-right">Facturación</TableHead>
              )}
              {isColVisible("active_employees") && (
                <TableHead className="text-slate-400 text-center">Empl.</TableHead>
              )}
              {isColVisible("users") && (
                <TableHead className="text-slate-400 text-center">Users</TableHead>
              )}
              {isColVisible("contact") && <TableHead className="text-slate-400">Contacto</TableHead>}
              {isColVisible("payment_method") && (
                <TableHead className="text-slate-400">Método Pago</TableHead>
              )}
              {isColVisible("activation_date") && (
                <TableHead className="text-slate-400">F. Activación</TableHead>
              )}
              {isColVisible("next_payment") && (
                <TableHead className="text-slate-400">Próx. Pago</TableHead>
              )}
              {isColVisible("activity") && (
                <TableHead className="text-slate-400">Actividad</TableHead>
              )}
              {isColVisible("actions") && (
                <TableHead className="text-slate-400 text-right">Acciones</TableHead>
              )}
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i} className="border-slate-800">
                  <TableCell colSpan={visibleCols.length}>
                    <div className="h-8 bg-slate-800 rounded animate-pulse" />
                  </TableCell>
                </TableRow>
              ))
            ) : filtered.length === 0 ? (
              <TableRow className="border-slate-800">
                <TableCell
                  colSpan={visibleCols.length}
                  className="text-center py-8 text-slate-500"
                >
                  No se encontraron empresas
                </TableCell>
              </TableRow>
            ) : (
              filtered.map((c) => (
                <TableRow
                  key={c.company_id}
                  className="border-slate-800 hover:bg-slate-800/30 cursor-pointer"
                  onClick={() => onDrillDown(c)}
                >
                  {isColVisible("name") && (
                    <TableCell className="font-medium text-white max-w-[200px]">
                      <div className="flex items-center gap-1.5">
                        <span className="truncate">{c.name || c.company_id}</span>
                        <ChevronRight className="w-3.5 h-3.5 text-slate-600 flex-shrink-0" />
                      </div>
                      {c.rnc && <p className="text-[10px] text-slate-500 font-mono">{c.rnc}</p>}
                    </TableCell>
                  )}
                  {isColVisible("status") && (
                    <TableCell>
                      {c.status === "active" ? (
                        <Badge className="bg-emerald-500/20 text-emerald-400 border-0">
                          Activa
                        </Badge>
                      ) : (
                        <Badge className="bg-red-500/20 text-red-400 border-0">Inactiva</Badge>
                      )}
                    </TableCell>
                  )}
                  {isColVisible("plan") && (
                    <TableCell>
                      {getPlanBadge(c.subscription_plan || "free", c.monthly_price || 0)}
                    </TableCell>
                  )}
                  {isColVisible("monthly_billing") && (
                    <TableCell className="text-right">
                      <span className="text-emerald-400 font-bold">
                        ${(c.monthly_billing || 0).toFixed(2)}
                      </span>
                      {c.monthly_billing > 0 && (
                        <p className="text-[10px] text-slate-500">/mes</p>
                      )}
                    </TableCell>
                  )}
                  {isColVisible("active_employees") && (
                    <TableCell className="text-center text-slate-300">
                      {c.active_employee_count || 0}
                    </TableCell>
                  )}
                  {isColVisible("users") && (
                    <TableCell className="text-center text-slate-300">{c.user_count}</TableCell>
                  )}
                  {isColVisible("contact") && (
                    <TableCell>
                      {c.contact_name || c.contact_email ? (
                        <div>
                          {c.contact_name && (
                            <p className="text-sm text-slate-300">{c.contact_name}</p>
                          )}
                          {c.contact_email && (
                            <p className="text-[10px] text-slate-500">{c.contact_email}</p>
                          )}
                        </div>
                      ) : (
                        <span className="text-slate-600">—</span>
                      )}
                    </TableCell>
                  )}
                  {isColVisible("payment_method") && (
                    <TableCell>{getPaymentBadge(c.payment_method || "sin_definir")}</TableCell>
                  )}
                  {isColVisible("activation_date") && (
                    <TableCell className="text-sm text-slate-400">
                      {c.activation_date ? c.activation_date.split("T")[0] : "—"}
                    </TableCell>
                  )}
                  {isColVisible("next_payment") && (
                    <TableCell className="text-sm text-slate-400">
                      {c.next_payment_date ? c.next_payment_date.split("T")[0] : "—"}
                    </TableCell>
                  )}
                  {isColVisible("activity") && (
                    <TableCell>
                      <div className="flex items-center gap-1.5">
                        <span className="text-slate-400 text-sm">
                          {(c.last_activity || c.created_at || "").split("T")[0]}
                        </span>
                        {c.days_inactive != null && c.days_inactive >= 30 && (
                          <Badge
                            className={`text-[10px] px-1.5 py-0 border-0 ${
                              c.days_inactive >= 60
                                ? "bg-red-500/20 text-red-400"
                                : "bg-amber-500/20 text-amber-400"
                            }`}
                          >
                            {c.days_inactive}d
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                  )}
                  {isColVisible("actions") && (
                    <TableCell onClick={(e) => e.stopPropagation()}>
                      <div className="flex justify-end gap-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          className="text-indigo-400 hover:text-indigo-300 hover:bg-indigo-500/10"
                          onClick={() => onOpenPlanDialog(c)}
                          data-testid={`btn-plan-${c.company_id}`}
                        >
                          <ArrowUpDown className="w-4 h-4 mr-1" /> Plan
                        </Button>
                        {c.status === "active" ? (
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                            onClick={() => onOpenDeactivate(c)}
                            data-testid={`btn-deactivate-${c.company_id}`}
                          >
                            <PowerOff className="w-4 h-4 mr-1" /> Inactivar
                          </Button>
                        ) : (
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10"
                            onClick={() => onOpenActivate(c)}
                            data-testid={`btn-activate-${c.company_id}`}
                          >
                            <Power className="w-4 h-4 mr-1" /> Activar
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  )}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>
    </>
  );
}
