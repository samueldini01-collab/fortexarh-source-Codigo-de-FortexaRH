import { useTranslation } from "react-i18next";
import { AlertCircle, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

/**
 * ACH bank file generation dialog.
 *
 * Used by PayrollV2Page to produce the bank's ACH payroll file
 * (Banreservas TXT/XLSX, Banco Popular, BHD León). Owns no state;
 * everything flows in through props so the parent keeps controlling
 * preview refresh + downloads + the "fix bank info" drill-down.
 */
export default function AchBankDialog({
  open,
  onOpenChange,
  selectedPeriod,
  achBank,
  achFormat,
  achLoading,
  achPreview,
  onBankChange,
  onFormatChange,
  onFixMissingEmployee,
  onDownload,
}) {
  const { t: _t } = useTranslation();
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg" data-testid="ach-bank-dialog">
        <DialogHeader>
          <DialogTitle>Generar Archivo ACH</DialogTitle>
          <DialogDescription>
            {selectedPeriod?.description || "Período seleccionado"} - Archivo de pago bancario
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label>Banco</Label>
            <Select value={achBank} onValueChange={onBankChange}>
              <SelectTrigger data-testid="ach-bank-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="banreservas">Banreservas</SelectItem>
                <SelectItem value="popular">Banco Popular Dominicano</SelectItem>
                <SelectItem value="bhd">BHD León</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {achBank === "banreservas" && (
            <div data-testid="ach-format-group">
              <Label>Formato</Label>
              <div className="grid grid-cols-2 gap-2 mt-1">
                <button
                  type="button"
                  onClick={() => onFormatChange("txt")}
                  data-testid="ach-format-txt"
                  className={`text-left rounded-lg border p-3 transition ${
                    achFormat === "txt"
                      ? "border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20 ring-2 ring-emerald-500/20"
                      : "border-slate-200 dark:border-slate-700 hover:border-slate-300"
                  }`}
                >
                  <p className="text-sm font-semibold">TXT (ACH delimitado)</p>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Formato clásico Banreservas, CC,DOP,...,Monto,Concepto
                  </p>
                </button>
                <button
                  type="button"
                  onClick={() => onFormatChange("xlsx")}
                  data-testid="ach-format-xlsx"
                  className={`text-left rounded-lg border p-3 transition ${
                    achFormat === "xlsx"
                      ? "border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20 ring-2 ring-emerald-500/20"
                      : "border-slate-200 dark:border-slate-700 hover:border-slate-300"
                  }`}
                >
                  <p className="text-sm font-semibold">Excel oficial</p>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Plantilla Nómina Electrónica V1.2 de Banreservas
                  </p>
                </button>
              </div>
            </div>
          )}

          {achLoading ? (
            <div className="py-6 text-center text-sm text-slate-500">Cargando vista previa...</div>
          ) : achPreview ? (
            <div className="space-y-3">
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-emerald-50 dark:bg-emerald-900/20 rounded-lg p-3 text-center">
                  <p className="text-xs text-slate-500">Listos</p>
                  <p className="text-lg font-bold text-emerald-700" data-testid="ach-ready-count">
                    {achPreview.ready_count}
                  </p>
                </div>
                <div className="bg-amber-50 dark:bg-amber-900/20 rounded-lg p-3 text-center">
                  <p className="text-xs text-slate-500">Sin banco</p>
                  <p className="text-lg font-bold text-amber-700" data-testid="ach-missing-count">
                    {achPreview.missing_count}
                  </p>
                </div>
                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 text-center">
                  <p className="text-xs text-slate-500">Total</p>
                  <p className="text-sm font-bold text-blue-700" data-testid="ach-total-amount">
                    RD${achPreview.total_amount?.toLocaleString("es-DO", { minimumFractionDigits: 2 })}
                  </p>
                </div>
              </div>

              {achPreview.missing_count > 0 && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                  <p className="text-xs font-medium text-amber-800 mb-1 flex items-center gap-1">
                    <AlertCircle className="w-3.5 h-3.5" /> Empleados sin datos bancarios:
                  </p>
                  <div className="space-y-0.5">
                    {achPreview.missing?.slice(0, 8).map((m, i) => (
                      <button
                        key={i}
                        type="button"
                        onClick={() => onFixMissingEmployee?.(m)}
                        data-testid={`fix-bank-${m.employee_id}`}
                        className="w-full text-left text-xs text-amber-700 hover:bg-amber-100 rounded px-2 py-1 flex items-center justify-between group transition"
                      >
                        <span>
                          <span className="font-medium underline-offset-2 group-hover:underline">
                            {m.employee_name}
                          </span>
                          <span className="text-amber-600">
                            {" "}
                            · RD${m.amount?.toLocaleString("es-DO", { minimumFractionDigits: 2 })}
                          </span>
                        </span>
                        <span className="text-amber-600 group-hover:text-amber-800 text-[10px] font-semibold opacity-70 group-hover:opacity-100">
                          Agregar cuenta →
                        </span>
                      </button>
                    ))}
                  </div>
                  <p className="text-[10px] text-amber-600 mt-1">
                    Haz click en un empleado para añadir su cuenta sin salir de esta pantalla.
                  </p>
                </div>
              )}

              {achPreview.ready_count > 0 && (
                <div className="max-h-[150px] overflow-y-auto border rounded-lg">
                  <table className="w-full text-xs">
                    <thead className="bg-slate-50 sticky top-0">
                      <tr>
                        <th className="text-left px-2 py-1.5 font-medium text-slate-500">Empleado</th>
                        <th className="text-left px-2 py-1.5 font-medium text-slate-500">Cuenta</th>
                        <th className="text-right px-2 py-1.5 font-medium text-slate-500">Monto</th>
                      </tr>
                    </thead>
                    <tbody>
                      {achPreview.ready?.map((r, i) => (
                        <tr key={i} className="border-t">
                          <td className="px-2 py-1 text-slate-700">{r.employee_name}</td>
                          <td className="px-2 py-1 text-slate-500 font-mono text-[10px]">
                            {r.account}
                          </td>
                          <td className="px-2 py-1 text-right text-emerald-700 font-medium">
                            RD${r.amount?.toLocaleString("es-DO", { minimumFractionDigits: 2 })}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {!achPreview.company_account && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                  <p className="text-xs text-red-700 flex items-center gap-1">
                    <AlertCircle className="w-3.5 h-3.5" />
                    No hay cuenta bancaria de empresa configurada para {achBank}. Ve a Configuración para agregarla.
                  </p>
                </div>
              )}
            </div>
          ) : null}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button
            onClick={onDownload}
            disabled={!achPreview || achPreview.ready_count === 0}
            className="bg-emerald-600 hover:bg-emerald-700 text-white"
            data-testid="btn-download-ach"
          >
            <Download className="w-4 h-4 mr-2" />
            Descargar ACH ({achPreview?.ready_count || 0} registros)
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
