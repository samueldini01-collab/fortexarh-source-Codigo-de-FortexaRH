import { AlertCircle, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

/**
 * Pre-approval warning dialog: lists employees missing bank info so the
 * user can decide whether to approve the payroll anyway or fix the data
 * first.
 */
export default function BankWarningDialog({
  open,
  onOpenChange,
  warning,
  onApproveAnyway,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md" data-testid="bank-warning-dialog">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-amber-700">
            <AlertCircle className="w-5 h-5" /> Empleados sin Datos Bancarios
          </DialogTitle>
          <DialogDescription>
            {warning?.missing_count} de {warning?.total} empleados no tienen cuenta bancaria
            configurada. No se podrá generar archivo ACH para estos empleados.
          </DialogDescription>
        </DialogHeader>
        {warning?.missing?.length > 0 && (
          <div className="max-h-[200px] overflow-y-auto border rounded-lg">
            <table className="w-full text-xs">
              <thead className="bg-amber-50 sticky top-0">
                <tr>
                  <th className="text-left px-3 py-2 font-medium text-amber-800">Empleado</th>
                  <th className="text-right px-3 py-2 font-medium text-amber-800">Neto a Pagar</th>
                </tr>
              </thead>
              <tbody>
                {warning.missing.map((emp, i) => (
                  <tr key={i} className="border-t border-amber-100">
                    <td className="px-3 py-1.5 text-slate-700">{emp.name}</td>
                    <td className="px-3 py-1.5 text-right font-medium text-slate-700">
                      RD${emp.amount?.toLocaleString("es-DO", { minimumFractionDigits: 2 })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <p className="text-xs text-slate-500">
          Puedes configurar los datos bancarios en el perfil de cada empleado (sección Datos
          Bancarios).
        </p>
        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button
            onClick={onApproveAnyway}
            className="bg-amber-600 hover:bg-amber-700 text-white"
            data-testid="btn-approve-with-warning"
          >
            <Check className="w-4 h-4 mr-1" /> Aprobar de todos modos
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
