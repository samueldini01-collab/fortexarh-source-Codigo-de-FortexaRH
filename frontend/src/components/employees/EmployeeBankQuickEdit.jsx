import { useEffect, useState } from "react";
import axios from "axios";
import { API } from "@/App";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Landmark, Loader2, ExternalLink } from "lucide-react";
import { toast } from "sonner";
import BankCombobox from "./BankCombobox";
import useCompanyCountry from "@/hooks/useCompanyCountry";

function authHeaders() {
  const t = localStorage.getItem("token");
  return t ? { Authorization: `Bearer ${t}` } : {};
}

/**
 * Lightweight drill-down to add/edit bank information for one employee from the
 * ACH dialog. Calls PATCH /api/employees/{id}/bank-info so it doesn't require
 * the full employee payload. After saving, fires onSaved() so the parent can
 * refresh the ACH preview.
 */
export default function EmployeeBankQuickEdit({ open, onOpenChange, employee, onSaved }) {
  const { countryCode: companyCountry } = useCompanyCountry();
  const [bankName, setBankName] = useState("");
  const [accountNumber, setAccountNumber] = useState("");
  const [accountType, setAccountType] = useState("CC");
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open || !employee?.employee_id) return;
    setLoading(true);
    axios
      .get(`${API}/employees/${employee.employee_id}`, { headers: authHeaders() })
      .then((res) => {
        setBankName(res.data?.bank_name || "");
        setAccountNumber(res.data?.account_number || "");
        setAccountType(res.data?.account_type || "CC");
      })
      .catch(() => {
        // Fallback with blank fields
        setBankName(""); setAccountNumber(""); setAccountType("CC");
      })
      .finally(() => setLoading(false));
  }, [open, employee?.employee_id]);

  const handleSave = async () => {
    if (!accountNumber.trim()) {
      toast.error("La cuenta bancaria es obligatoria");
      return;
    }
    setSaving(true);
    try {
      await axios.patch(
        `${API}/employees/${employee.employee_id}/bank-info`,
        {
          bank_name: bankName.trim(),
          account_number: accountNumber.trim(),
          account_type: accountType,
        },
        { headers: authHeaders() }
      );
      toast.success("Datos bancarios guardados");
      onSaved?.();
      onOpenChange(false);
    } catch (err) {
      toast.error(err.response?.data?.detail || "No se pudo guardar");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md" data-testid="employee-bank-quick-edit">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Landmark className="w-5 h-5 text-emerald-600" />
            Datos bancarios
          </DialogTitle>
          <DialogDescription>
            <span className="font-medium text-slate-700">{employee?.employee_name || "Empleado"}</span>
            {employee?.amount > 0 && (
              <> · Pago pendiente: <b>RD${Number(employee.amount).toLocaleString("es-DO", { minimumFractionDigits: 2 })}</b></>
            )}
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-5 h-5 animate-spin text-emerald-600" />
          </div>
        ) : (
          <div className="space-y-3 py-2">
            <div>
              <Label>Banco</Label>
              <BankCombobox
                value={bankName}
                onChange={setBankName}
                countryCode={companyCountry}
                testId="bank-quick-bankname"
                placeholder="Selecciona el banco"
              />
            </div>
            <div>
              <Label>Tipo de cuenta</Label>
              <Select value={accountType} onValueChange={setAccountType}>
                <SelectTrigger data-testid="bank-quick-accounttype"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="CC">Corriente (CC)</SelectItem>
                  <SelectItem value="CA">Ahorro (CA)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Número de cuenta</Label>
              <Input
                value={accountNumber}
                onChange={(e) => setAccountNumber(e.target.value.replace(/\D/g, ""))}
                placeholder="Ej. 9608649339"
                data-testid="bank-quick-accountnumber"
                autoFocus
              />
              <p className="text-xs text-slate-500 mt-1">Solo dígitos. Lo necesita el banco para el pago.</p>
            </div>

            <div className="flex items-center justify-between pt-1">
              <button
                onClick={() => window.open(`/employees?focus=${employee.employee_id}`, "_blank")}
                className="text-xs text-slate-500 hover:text-slate-800 flex items-center gap-1"
                data-testid="bank-quick-open-profile"
              >
                <ExternalLink className="w-3 h-3" /> Abrir perfil completo
              </button>
            </div>
          </div>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={saving} data-testid="bank-quick-cancel">
            Cancelar
          </Button>
          <Button
            className="bg-emerald-600 hover:bg-emerald-700"
            onClick={handleSave}
            disabled={saving || loading}
            data-testid="bank-quick-save"
          >
            {saving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
            Guardar y volver
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
