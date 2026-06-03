import { useTranslation } from "react-i18next";
import { MinusCircle, Plus, PlusCircle } from "lucide-react";
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
 * Add / edit novelty (income or deduction) dialog for the Payroll module.
 *
 * Owns no state — the parent PayrollV2Page passes the controlled
 * ``form`` + a ``setForm`` updater so editing flows feel identical to
 * the inline version.
 */
export default function NoveltyDialog({
  open,
  onOpenChange,
  editingNoveltyId,
  selectedEntry,
  noveltyTypes,
  form,
  setForm,
  onSave,
}) {
  const { t } = useTranslation();
  const isIncome = form.novelty_type === "income";
  const types = isIncome ? noveltyTypes.income : noveltyTypes.deduction;

  return (
    <Dialog
      open={open}
      onOpenChange={(v) => {
        onOpenChange(v);
      }}
    >
      <DialogContent data-testid="novelty-dialog">
        <DialogHeader>
          <DialogTitle>
            {editingNoveltyId
              ? t("payrollV2.editarNovedad", { defaultValue: "Editar Novedad" })
              : t("payrollV2.agregarNovedad")}
          </DialogTitle>
          <DialogDescription>
            {t("payrollV2.agregueUnIngresoODeduccion", { name: selectedEntry?.employee_name })}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Button
              variant={isIncome ? "default" : "outline"}
              className="h-auto py-3 flex flex-col"
              onClick={() => setForm({ ...form, novelty_type: "income", code: "", name: "" })}
            >
              <PlusCircle className="w-5 h-5 mb-1 text-emerald-500" />
              <span>{t("payrollV2.ingreso")}</span>
            </Button>
            <Button
              variant={!isIncome ? "default" : "outline"}
              className="h-auto py-3 flex flex-col"
              onClick={() => setForm({ ...form, novelty_type: "deduction", code: "", name: "" })}
            >
              <MinusCircle className="w-5 h-5 mb-1 text-red-500" />
              <span>{t("payrollV2.deduccion")}</span>
            </Button>
          </div>
          <div className="space-y-2">
            <Label>Tipo de {isIncome ? "Ingreso" : "Deducción"}</Label>
            <Select
              value={form.code}
              onValueChange={(v) => {
                const selected = types.find((x) => x.code === v);
                setForm({
                  ...form,
                  code: v,
                  name: selected?.name || "",
                  description: selected?.description || "",
                });
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Seleccione" />
              </SelectTrigger>
              <SelectContent>
                {types.map((x) => (
                  <SelectItem key={x.code} value={x.code}>
                    {x.code} - {x.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>{t("payrollV2.montoRd")}</Label>
            <Input
              type="number"
              step="0.01"
              value={form.amount}
              onChange={(e) => setForm({ ...form, amount: e.target.value })}
              placeholder="0.00"
            />
          </div>
          <div className="space-y-2">
            <Label>{t("payrollV2.descripcionOpcional")}</Label>
            <Input
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="Ej: Comisión ventas enero"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            {t("payrollV2.cancelar")}
          </Button>
          <Button onClick={onSave} data-testid="save-novelty-btn">
            <Plus className="w-4 h-4 mr-2" />
            {editingNoveltyId
              ? t("payrollV2.actualizarNovedad", { defaultValue: "Actualizar Novedad" })
              : t("payrollV2.agregarNovedad")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
