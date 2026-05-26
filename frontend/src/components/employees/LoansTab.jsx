/**
 * LoansTab — Slim view inside EmployeeFormDialog.
 *
 * Per product decision, loan management lives in the dedicated `/loans`
 * module ("Préstamos a Empleados"). This tab only shows a compact summary
 * of the employee's loans and a single CTA that navigates to the global
 * loans page pre-filtered by this employee.
 */
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/App";
import { ExternalLink, AlertCircle } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const STATUS_COLORS = {
  active: "bg-emerald-100 text-emerald-700 border-emerald-300",
  paused: "bg-amber-100 text-amber-700 border-amber-300",
  paid: "bg-blue-100 text-blue-700 border-blue-300",
  paid_off: "bg-blue-100 text-blue-700 border-blue-300",
  cancelled: "bg-red-100 text-red-700 border-red-300",
};
const STATUS_LABELS = {
  active: "Activo", paused: "Pausado", paid: "Pagado",
  paid_off: "Pagado", cancelled: "Cancelado",
};
const fmt = (n) =>
  new Intl.NumberFormat("es-DO", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(n || 0);

export default function LoansTab({ employeeId, employeeName }) {
  const { t } = useTranslation();
  const { getAuthHeaders } = useAuth();
  const navigate = useNavigate();
  const [loans, setLoans] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!employeeId) return;
    setLoading(true);
    axios
      .get(`${API}/loans?employee_id=${employeeId}`, { headers: getAuthHeaders(), withCredentials: true })
      .then((r) => setLoans(r.data || []))
      .catch((e) => toast.error(e?.response?.data?.detail || "Error cargando préstamos"))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [employeeId]);

  if (!employeeId) {
    return (
      <div className="p-6 text-center text-slate-500 text-sm flex items-center justify-center gap-2">
        <AlertCircle className="w-4 h-4" />
        Guarda el empleado primero para poder gestionar préstamos.
      </div>
    );
  }

  const goToLoansPage = () => navigate(`/loans?employee_id=${employeeId}`);

  const active = loans.filter((l) => l.status === "active");
  const totalBalance = active.reduce((s, l) => s + (l.remaining_balance || 0), 0);
  const totalMonthlyDeduction = active.reduce((s, l) => s + (l.monthly_payment || 0), 0);

  return (
    <div className="space-y-4" data-testid="loans-tab">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h4 className="font-semibold text-slate-700">Préstamos del empleado</h4>
          <p className="text-xs text-slate-500">
            Resumen de los préstamos. Para crear, pausar o ver el detalle completo, gestiona desde el módulo Préstamos a Empleados.
          </p>
        </div>
        <Button onClick={goToLoansPage} data-testid="go-to-loans-page">
          <ExternalLink className="w-4 h-4 mr-1" /> Gestionar en módulo Préstamos
        </Button>
      </div>

      {!loading && loans.length > 0 && (
        <div className="grid grid-cols-3 gap-3">
          <Card className="p-3">
            <div className="text-xs text-slate-500">Préstamos activos</div>
            <div className="text-xl font-bold text-emerald-700">{active.length}</div>
          </Card>
          <Card className="p-3">
            <div className="text-xs text-slate-500">Cuota mensual total</div>
            <div className="text-xl font-bold text-blue-700">RD${fmt(totalMonthlyDeduction)}</div>
          </Card>
          <Card className="p-3">
            <div className="text-xs text-slate-500">Saldo total pendiente</div>
            <div className="text-xl font-bold text-red-700">RD${fmt(totalBalance)}</div>
          </Card>
        </div>
      )}

      {loading ? (
        <div className="py-8 text-center text-slate-500 text-sm">Cargando...</div>
      ) : loans.length === 0 ? (
        <Card className="p-6 text-center text-slate-500 text-sm">
          Sin préstamos registrados. Crea uno desde el módulo <button onClick={goToLoansPage} className="text-blue-600 underline">Préstamos a Empleados</button>.
        </Card>
      ) : (
        <div className="space-y-2">
          {loans.map((loan) => (
            <Card key={loan.loan_id} className="p-3 cursor-pointer hover:shadow-sm" onClick={goToLoansPage} data-testid={`loan-row-${loan.loan_id}`}>
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <span className="font-mono text-xs text-slate-400">{loan.loan_id.slice(0, 12)}</span>
                  <Badge className={`text-xs ${STATUS_COLORS[loan.status] || ""}`} variant="outline">
                    {STATUS_LABELS[loan.status] || loan.status}
                  </Badge>
                  {loan.description && (
                    <span className="text-xs text-slate-500 italic truncate">{loan.description}</span>
                  )}
                </div>
                <div className="grid grid-cols-4 gap-3 text-xs">
                  <div className="text-right">
                    <div className="text-slate-500">Capital</div>
                    <div className="font-semibold">RD${fmt(loan.amount)}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-slate-500">Cuota</div>
                    <div className="font-semibold">RD${fmt(loan.monthly_payment)}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-slate-500">Pagado</div>
                    <div className="font-semibold text-emerald-700">RD${fmt(loan.total_paid)}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-slate-500">Saldo</div>
                    <div className="font-semibold text-red-700">RD${fmt(loan.remaining_balance)}</div>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
