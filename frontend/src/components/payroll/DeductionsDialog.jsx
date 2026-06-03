import { useTranslation } from "react-i18next";
import { Calculator, Plus, RefreshCw, Save, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

/**
 * Per-employee Deductions detail dialog.
 *
 * Shows legal deductions (SFS/AFP/ISR) with override inputs and a
 * dynamic list of additional deductions (loans, alimony, etc.).
 *
 * State-free presentational layer — the parent passes:
 *  - ``entry`` (current payroll entry being edited)
 *  - ``form`` + ``setForm`` (controlled values + edits)
 *  - ``newDeduction`` + ``setNewDeduction`` (the "add new" row)
 *  - callbacks: onAdd, onRemove, onSave
 */
export default function DeductionsDialog({
  open,
  onOpenChange,
  entry,
  form,
  setForm,
  newDeduction,
  setNewDeduction,
  formatNumber,
  countryRates,
  getDeductionLabel,
  getDeductionRatePct,
  onAddDeduction,
  onRemoveDeduction,
  onSave,
  saving,
}) {
  const { t } = useTranslation();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[85vh] overflow-y-auto" data-testid="deductions-dialog">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Calculator className="w-5 h-5 text-red-600" />
            {t("payrollV2.deductionsDialog.title")}
          </DialogTitle>
          <DialogDescription>
            {entry?.employee_name} &middot; {t("payrollV2.deductionsDialog.subtitle")}
          </DialogDescription>
        </DialogHeader>

        {entry && (
          <div className="space-y-5">
            {/* Salary reference */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 flex justify-between items-center">
              <span className="text-sm font-medium text-blue-700">
                {t("payrollV2.deductionsDialog.grossSalary")}
              </span>
              <span className="font-mono font-bold text-blue-700">
                {formatNumber(entry.gross_salary)}
              </span>
            </div>

            {/* Legal Deductions */}
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-slate-700">
                {t("payrollV2.deductionsDialog.legalDeductions")}
              </h4>

              <div className="space-y-2">
                <div className="flex items-center justify-between gap-3">
                  <Label className="text-sm w-24" title={countryRates?.labels?.sfs_employee}>
                    {getDeductionLabel("sfs_employee", "payrollV2.sfs")} (
                    {getDeductionRatePct("sfs_employee") || "3.04%"})
                  </Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={form.sfs_override}
                    onChange={(e) => setForm({ ...form, sfs_override: e.target.value })}
                    className="w-40 text-right font-mono"
                    data-testid="deductions-sfs"
                  />
                </div>
                <div className="flex items-center justify-between gap-3">
                  <Label className="text-sm w-24">AFP (2.87%)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={form.afp_override}
                    onChange={(e) => setForm({ ...form, afp_override: e.target.value })}
                    className="w-40 text-right font-mono"
                    data-testid="deductions-afp"
                  />
                </div>
                <div className="flex items-center justify-between gap-3">
                  <Label className="text-sm w-24">ISR</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={form.isr_override}
                    onChange={(e) => setForm({ ...form, isr_override: e.target.value })}
                    className="w-40 text-right font-mono"
                    data-testid="deductions-isr"
                  />
                </div>
              </div>

              <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-2 flex justify-between items-center">
                <span className="text-xs font-medium text-emerald-700">
                  {t("payrollV2.deductionsDialog.subtotalLegal")}
                </span>
                <span className="font-mono font-bold text-emerald-700 text-sm">
                  {formatNumber(
                    (parseFloat(form.sfs_override) || 0) +
                      (parseFloat(form.afp_override) || 0) +
                      (parseFloat(form.isr_override) || 0),
                  )}
                </span>
              </div>
            </div>

            {/* Additional Deductions */}
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-slate-700">
                {t("payrollV2.deductionsDialog.additionalDeductions")}
              </h4>

              {form.additional_deductions.length === 0 ? (
                <p className="text-sm text-slate-400 italic text-center py-2">
                  {t("payrollV2.deductionsDialog.noAdditional")}
                </p>
              ) : (
                <div className="space-y-2">
                  {form.additional_deductions.map((ded, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-2 bg-slate-50 rounded-lg border gap-2"
                    >
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium">{ded.type}</p>
                        {ded.description && (
                          <p className="text-xs text-slate-500">{ded.description}</p>
                        )}
                      </div>
                      <div className="flex items-center gap-1">
                        <Input
                          type="number"
                          step="0.01"
                          value={ded.amount}
                          onChange={(e) => {
                            const updated = [...form.additional_deductions];
                            updated[idx] = {
                              ...updated[idx],
                              amount: parseFloat(e.target.value) || 0,
                            };
                            setForm({ ...form, additional_deductions: updated });
                          }}
                          className="w-28 text-right font-mono text-sm h-8"
                          data-testid={`ded-amount-${idx}`}
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 text-red-500 shrink-0"
                          onClick={() => onRemoveDeduction(idx)}
                        >
                          <X className="w-3.5 h-3.5" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {form.additional_deductions.length > 0 && (
                <div className="bg-orange-50 border border-orange-200 rounded-lg p-2 flex justify-between items-center">
                  <span className="text-xs font-medium text-orange-700">
                    {t("payrollV2.deductionsDialog.subtotalAdditional")}
                  </span>
                  <span className="font-mono font-bold text-orange-700 text-sm">
                    {formatNumber(
                      form.additional_deductions.reduce(
                        (s, d) => s + (d.is_percentage ? 0 : parseFloat(d.amount) || 0),
                        0,
                      ),
                    )}
                  </span>
                </div>
              )}

              {/* Add deduction form */}
              <div className="bg-blue-50 rounded-lg p-3 border border-blue-200 space-y-2">
                <p className="text-xs font-semibold text-blue-700">
                  + {t("payrollV2.deductionsDialog.addDeduction")}
                </p>
                <div className="grid grid-cols-3 gap-2">
                  <Select
                    value={newDeduction.type}
                    onValueChange={(v) => setNewDeduction({ ...newDeduction, type: v })}
                  >
                    <SelectTrigger className="bg-white text-xs h-8">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Préstamo Empresa">Préstamo Empresa</SelectItem>
                      <SelectItem value="Pensión Alimenticia">Pensión Alimenticia</SelectItem>
                      <SelectItem value="Adelanto Salario">Adelanto Salario</SelectItem>
                      <SelectItem value="Seguro Complementario">Seguro Complementario</SelectItem>
                      <SelectItem value="Cooperativa">Cooperativa</SelectItem>
                      <SelectItem value="Otro">Otro</SelectItem>
                    </SelectContent>
                  </Select>
                  <Input
                    placeholder={t("payrollV2.deductionsDialog.descPlaceholder")}
                    value={newDeduction.description}
                    onChange={(e) =>
                      setNewDeduction({ ...newDeduction, description: e.target.value })
                    }
                    className="bg-white text-xs h-8"
                  />
                  <div className="flex gap-1">
                    <Input
                      type="number"
                      step="0.01"
                      placeholder="0.00"
                      value={newDeduction.amount}
                      onChange={(e) =>
                        setNewDeduction({ ...newDeduction, amount: e.target.value })
                      }
                      className="bg-white text-xs h-8"
                    />
                    <Button
                      type="button"
                      size="sm"
                      className="h-8 px-2 bg-blue-600"
                      onClick={onAddDeduction}
                      disabled={!newDeduction.amount}
                    >
                      <Plus className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
              </div>
            </div>

            {/* Grand Total */}
            <div className="bg-red-50 border-2 border-red-200 rounded-lg p-3 flex justify-between items-center">
              <span className="font-semibold text-red-700">
                {t("payrollV2.deductionsDialog.totalDeductions")}
              </span>
              <span className="font-mono font-bold text-red-700 text-lg">
                {formatNumber(
                  (parseFloat(form.sfs_override) || 0) +
                    (parseFloat(form.afp_override) || 0) +
                    (parseFloat(form.isr_override) || 0) +
                    form.additional_deductions.reduce(
                      (s, d) => s + (d.is_percentage ? 0 : parseFloat(d.amount) || 0),
                      0,
                    ),
                )}
              </span>
            </div>
          </div>
        )}

        <DialogFooter className="gap-2 mt-4">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            {t("common.cancel")}
          </Button>
          <Button
            onClick={onSave}
            disabled={saving}
            className="bg-emerald-600 hover:bg-emerald-700"
            data-testid="save-deductions-btn"
          >
            {saving ? (
              <RefreshCw className="w-4 h-4 mr-1 animate-spin" />
            ) : (
              <Save className="w-4 h-4 mr-1" />
            )}
            {t("payrollV2.deductionsDialog.save")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
