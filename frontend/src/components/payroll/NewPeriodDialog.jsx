import { useTranslation } from "react-i18next";
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

const YEARS = [2024, 2025, 2026, 2027];

/**
 * New Payroll Period dialog.
 *
 * Controlled by the parent (PayrollV2Page) — receives the in-progress
 * ``form`` and a setter, plus the static catalog props (payrollTypes,
 * periodTypes, departments, months) needed to render the dropdowns.
 */
export default function NewPeriodDialog({
  open,
  onOpenChange,
  form,
  setForm,
  payrollTypes,
  periodTypes,
  departments,
  months,
  onCreate,
}) {
  const { t } = useTranslation();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg" data-testid="new-period-dialog">
        <DialogHeader>
          <DialogTitle>{t("payrollV2.crearNuevaNomina")}</DialogTitle>
          <DialogDescription>{t("payrollV2.defineElTipoY")}</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>{t("payrollV2.tipoDeNomina")}</Label>
            <div className="grid grid-cols-3 gap-2">
              {payrollTypes.map((pt) => (
                <Button
                  key={pt.value}
                  variant={form.payroll_type === pt.value ? "default" : "outline"}
                  className={`h-auto py-2 flex flex-col items-center ${
                    form.payroll_type === pt.value ? "" : "hover:bg-slate-50"
                  }`}
                  onClick={() => setForm({ ...form, payroll_type: pt.value })}
                >
                  <pt.icon className="w-4 h-4 mb-1" />
                  <span className="text-xs">{pt.label}</span>
                </Button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>{t("payrollV2.periodo")}</Label>
              <Select
                value={form.period_type}
                onValueChange={(v) => setForm({ ...form, period_type: v })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {periodTypes.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>{t("payrollV2.departamentoOpcional")}</Label>
              <Select
                value={form.department_filter}
                onValueChange={(v) => setForm({ ...form, department_filter: v })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Todos" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">{t("payrollV2.todosLosDepartamentos")}</SelectItem>
                  {departments.map((d) => (
                    <SelectItem key={d} value={d}>
                      {d}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>{t("payrollV2.ano")}</Label>
              <Select
                value={String(form.year)}
                onValueChange={(v) => setForm({ ...form, year: parseInt(v) })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {YEARS.map((year) => (
                    <SelectItem key={year} value={String(year)}>
                      {year}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>{t("payrollV2.mes")}</Label>
              <Select
                value={String(form.month)}
                onValueChange={(v) => setForm({ ...form, month: parseInt(v) })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {months.map((m) => (
                    <SelectItem key={m.value} value={String(m.value)}>
                      {m.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>{t("payrollV2.fechaInicio")}</Label>
              <Input
                type="date"
                value={form.start_date}
                onChange={(e) => setForm({ ...form, start_date: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>{t("payrollV2.fechaFin")}</Label>
              <Input
                type="date"
                value={form.end_date}
                onChange={(e) => setForm({ ...form, end_date: e.target.value })}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>{t("payrollV2.descripcion")}</Label>
            <Input
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="Ej: Nómina Quincenal Enero 2026"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            {t("payrollV2.cancelar")}
          </Button>
          <Button onClick={onCreate}>{t("payrollV2.crearNomina")}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
