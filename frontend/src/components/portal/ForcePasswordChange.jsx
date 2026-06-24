import { useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { KeyRound, ShieldAlert, LogOut } from "lucide-react";
import { useEmployeeAuth } from "@/components/portal/EmployeeAuthContext";

const API = process.env.REACT_APP_BACKEND_URL ? `${process.env.REACT_APP_BACKEND_URL}/api` : "/api";

export function ForcePasswordChange() {
  const { employee, token, logout, refreshProfile } = useEmployeeAuth();
  const [currentPw, setCurrentPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (newPw.length < 6) {
      toast.error("La nueva contraseña debe tener al menos 6 caracteres");
      return;
    }
    if (newPw !== confirmPw) {
      toast.error("Las contraseñas no coinciden");
      return;
    }
    if (newPw === currentPw) {
      toast.error("La nueva contraseña debe ser distinta a la actual");
      return;
    }
    setSubmitting(true);
    try {
      await axios.post(
        `${API}/employee-portal/change-password`,
        { old_password: currentPw, new_password: newPw },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success("Contraseña actualizada. Bienvenido/a al portal.");
      if (refreshProfile) {
        await refreshProfile();
      }
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Error al actualizar contraseña");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className="min-h-screen bg-slate-100 flex items-center justify-center p-4"
      data-testid="force-password-change-screen"
    >
      <Card className="w-full max-w-md p-6 space-y-5">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-full bg-amber-100">
            <ShieldAlert className="w-5 h-5 text-amber-600" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-800">Debes cambiar tu contraseña</h2>
            <p className="text-sm text-slate-600">
              Hola{employee?.first_name || employee?.name ? `, ${employee.first_name || employee.name}` : ""}.
              Por seguridad, antes de continuar al portal, define una nueva contraseña personal.
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <Label htmlFor="current-pw">Contraseña actual (temporal)</Label>
            <Input
              id="current-pw"
              type="password"
              autoComplete="current-password"
              value={currentPw}
              onChange={(e) => setCurrentPw(e.target.value)}
              required
              data-testid="force-current-password-input"
              placeholder="Tu cédula/pasaporte"
            />
            <p className="text-[11px] text-slate-500 mt-1">
              Es la cédula o pasaporte que te entregaron como contraseña temporal.
            </p>
          </div>
          <div>
            <Label htmlFor="new-pw">Nueva contraseña</Label>
            <Input
              id="new-pw"
              type="password"
              autoComplete="new-password"
              value={newPw}
              onChange={(e) => setNewPw(e.target.value)}
              required
              minLength={6}
              data-testid="force-new-password-input"
            />
            <p className="text-[11px] text-slate-500 mt-1">Mínimo 6 caracteres.</p>
          </div>
          <div>
            <Label htmlFor="confirm-pw">Confirmar nueva contraseña</Label>
            <Input
              id="confirm-pw"
              type="password"
              autoComplete="new-password"
              value={confirmPw}
              onChange={(e) => setConfirmPw(e.target.value)}
              required
              minLength={6}
              data-testid="force-confirm-password-input"
            />
          </div>

          <div className="flex gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={logout}
              className="flex-1"
              data-testid="force-password-logout-btn"
            >
              <LogOut className="w-4 h-4 mr-1" /> Cancelar
            </Button>
            <Button
              type="submit"
              disabled={submitting}
              className="flex-1"
              data-testid="force-password-submit-btn"
            >
              <KeyRound className="w-4 h-4 mr-1" />
              {submitting ? "Guardando..." : "Cambiar contraseña"}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
