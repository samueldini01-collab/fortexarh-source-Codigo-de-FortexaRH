/**
 * LoansTab — Employee Loans management inside EmployeeFormDialog.
 *
 * Shows the employee's loans (active / paused / paid / cancelled) and lets
 * the user create a new loan with live cuota calculation, pause / resume /
 * cancel an existing loan, and review the amortization schedule.
 */
import React, { useState, useEffect, useMemo } from "react";
import axios from "axios";
import { toast } from "sonner";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { useAuth } from "@/App";
import { Plus, Pause, Play, X, Eye, AlertCircle } from "lucide-react";

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
  active: "Activo",
  paused: "Pausado",
  paid: "Pagado",
  paid_off: "Pagado",
  cancelled: "Cancelado",
};

const SCHEDULE_LABELS = {
  all_periods: "Todos los períodos (quincenal ÷ 2)",
  monthly_only: "Solo en nómina mensual",
  biweekly_second_only: "Solo en 2da quincena",
};

const fmt = (n) =>
  new Intl.NumberFormat("es-DO", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(n || 0);

export default function LoansTab({ employeeId, employeeName }) {
  const { t } = useTranslation();
  const { getAuthHeaders } = useAuth();
  const [loans, setLoans] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [viewLoan, setViewLoan] = useState(null);

  const fetchLoans = async () => {
    if (!employeeId) return;
    setLoading(true);
    try {
      const res = await axios.get(`${API}/loans?employee_id=${employeeId}`, {
        headers: getAuthHeaders(),
        withCredentials: true,
      });
      setLoans(res.data || []);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Error cargando préstamos");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLoans();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [employeeId]);

  const handleStatus = async (loan, action) => {
    if (!confirm(`¿${action === "pause" ? "Pausar" : action === "resume" ? "Reanudar" : "Cancelar"} este préstamo?`)) return;
    try {
      await axios.post(`${API}/loans/${loan.loan_id}/${action}`, {}, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Préstamo actualizado");
      fetchLoans();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Error actualizando préstamo");
    }
  };

  if (!employeeId) {
    return (
      <div className="p-6 text-center text-slate-500 text-sm flex items-center justify-center gap-2">
        <AlertCircle className="w-4 h-4" />
        Guarda el empleado primero para poder crear préstamos.
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="loans-tab">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="font-semibold text-slate-700">Préstamos del empleado</h4>
          <p className="text-xs text-slate-500">
            Los préstamos activos se descuentan automáticamente al procesar la nómina según el calendario configurado.
          </p>
        </div>
        <Button onClick={() => setShowCreate(true)} data-testid="new-loan-btn">
          <Plus className="w-4 h-4 mr-1" /> Nuevo préstamo
        </Button>
      </div>

      {loading ? (
        <div className="py-8 text-center text-slate-500 text-sm">Cargando...</div>
      ) : loans.length === 0 ? (
        <Card className="p-6 text-center text-slate-500 text-sm">
          Sin préstamos registrados. Crea uno con el botón de arriba.
        </Card>
      ) : (
        <div className="space-y-2">
          {loans.map((loan) => (
            <Card key={loan.loan_id} className="p-3" data-testid={`loan-card-${loan.loan_id}`}>
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-xs text-slate-400">{loan.loan_id.slice(0, 12)}</span>
                    <Badge className={`text-xs ${STATUS_COLORS[loan.status] || ""}`} variant="outline">
                      {STATUS_LABELS[loan.status] || loan.status}
                    </Badge>
                    <span className="text-xs text-slate-500">{SCHEDULE_LABELS[loan.schedule_type] || ""}</span>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                    <div>
                      <div className="text-slate-500">Capital</div>
                      <div className="font-semibold">RD${fmt(loan.amount)}</div>
                    </div>
                    <div>
                      <div className="text-slate-500">Cuota mensual</div>
                      <div className="font-semibold">RD${fmt(loan.monthly_payment)}</div>
                    </div>
                    <div>
                      <div className="text-slate-500">Pagado</div>
                      <div className="font-semibold text-emerald-700">RD${fmt(loan.total_paid)}</div>
                    </div>
                    <div>
                      <div className="text-slate-500">Saldo</div>
                      <div className="font-semibold text-red-700">RD${fmt(loan.remaining_balance)}</div>
                    </div>
                  </div>
                  {loan.description && <div className="text-xs text-slate-500 mt-2 italic">{loan.description}</div>}
                </div>
                <div className="flex flex-col gap-1">
                  <Button size="icon" variant="ghost" onClick={() => setViewLoan(loan)} title="Ver detalle">
                    <Eye className="w-4 h-4" />
                  </Button>
                  {loan.status === "active" && (
                    <Button size="icon" variant="ghost" onClick={() => handleStatus(loan, "pause")} title="Pausar" data-testid={`pause-${loan.loan_id}`}>
                      <Pause className="w-4 h-4 text-amber-600" />
                    </Button>
                  )}
                  {loan.status === "paused" && (
                    <Button size="icon" variant="ghost" onClick={() => handleStatus(loan, "resume")} title="Reanudar" data-testid={`resume-${loan.loan_id}`}>
                      <Play className="w-4 h-4 text-emerald-600" />
                    </Button>
                  )}
                  {(loan.status === "active" || loan.status === "paused") && (
                    <Button size="icon" variant="ghost" onClick={() => handleStatus(loan, "cancel")} title="Cancelar" data-testid={`cancel-${loan.loan_id}`}>
                      <X className="w-4 h-4 text-red-500" />
                    </Button>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {showCreate && (
        <LoanFormDialog
          employeeId={employeeId}
          employeeName={employeeName}
          onClose={() => setShowCreate(false)}
          onCreated={() => {
            setShowCreate(false);
            fetchLoans();
          }}
        />
      )}

      {viewLoan && <LoanDetailDialog loan={viewLoan} onClose={() => setViewLoan(null)} />}
    </div>
  );
}

function LoanFormDialog({ employeeId, employeeName, onClose, onCreated }) {
  const { getAuthHeaders } = useAuth();
  const [amount, setAmount] = useState("");
  const [interestRate, setInterestRate] = useState("0");
  const [interestMethod, setInterestMethod] = useState("linear");
  const [termMonths, setTermMonths] = useState("12");
  const [scheduleType, setScheduleType] = useState("all_periods");
  const [startDate, setStartDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const preview = useMemo(() => {
    const A = parseFloat(amount) || 0;
    const r = parseFloat(interestRate) || 0;
    const n = parseInt(termMonths, 10) || 0;
    if (A <= 0 || n <= 0) return { cuota: 0, total: 0, interest: 0 };
    if (r === 0) {
      return { cuota: A / n, total: A, interest: 0 };
    }
    if (interestMethod === "french") {
      const i = r / 100 / 12;
      const cuota = (A * i * Math.pow(1 + i, n)) / (Math.pow(1 + i, n) - 1);
      return { cuota, total: cuota * n, interest: cuota * n - A };
    }
    // linear simple
    const interest = A * (r / 100) * (n / 12);
    const total = A + interest;
    return { cuota: total / n, total, interest };
  }, [amount, interestRate, interestMethod, termMonths]);

  const handleSubmit = async () => {
    if (parseFloat(amount) <= 0 || parseInt(termMonths, 10) <= 0) {
      toast.error("Capital y plazo deben ser positivos");
      return;
    }
    setSubmitting(true);
    try {
      await axios.post(
        `${API}/loans`,
        {
          employee_id: employeeId,
          amount: parseFloat(amount),
          interest_rate: parseFloat(interestRate) || 0,
          interest_method: interestMethod,
          term_months: parseInt(termMonths, 10),
          schedule_type: scheduleType,
          start_date: startDate,
          description,
          deduct_from_payroll: true,
        },
        { headers: getAuthHeaders(), withCredentials: true }
      );
      toast.success("Préstamo creado");
      onCreated();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Error creando préstamo");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-xl" data-testid="loan-form-dialog">
        <DialogHeader>
          <DialogTitle>Nuevo préstamo — {employeeName}</DialogTitle>
        </DialogHeader>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <Label>Capital (RD$)</Label>
            <Input
              type="number"
              step="0.01"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              data-testid="loan-amount-input"
            />
          </div>
          <div>
            <Label>Plazo (meses)</Label>
            <Input
              type="number"
              value={termMonths}
              onChange={(e) => setTermMonths(e.target.value)}
              data-testid="loan-term-input"
            />
          </div>
          <div>
            <Label>Tasa de interés anual (%)</Label>
            <Input
              type="number"
              step="0.01"
              value={interestRate}
              onChange={(e) => setInterestRate(e.target.value)}
              data-testid="loan-interest-input"
            />
            <p className="text-[10px] text-slate-500 mt-0.5">0 = sin interés</p>
          </div>
          <div>
            <Label>Método de interés</Label>
            <Select value={interestMethod} onValueChange={setInterestMethod}>
              <SelectTrigger data-testid="loan-method-select"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="linear">Lineal (interés simple)</SelectItem>
                <SelectItem value="french">Francesa (amortización)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="col-span-2">
            <Label>Cuándo descontar</Label>
            <Select value={scheduleType} onValueChange={setScheduleType}>
              <SelectTrigger data-testid="loan-schedule-select"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all_periods">{SCHEDULE_LABELS.all_periods}</SelectItem>
                <SelectItem value="monthly_only">{SCHEDULE_LABELS.monthly_only}</SelectItem>
                <SelectItem value="biweekly_second_only">{SCHEDULE_LABELS.biweekly_second_only}</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>Fecha de inicio</Label>
            <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
          </div>
          <div>
            <Label>Descripción</Label>
            <Input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Préstamo personal, anticipo, etc."
            />
          </div>
        </div>

        <Card className="p-3 bg-slate-50">
          <div className="text-xs font-semibold text-slate-700 mb-1">Previsualización</div>
          <div className="grid grid-cols-3 gap-2 text-xs">
            <div>
              <div className="text-slate-500">Cuota mensual</div>
              <div className="font-semibold text-blue-700">RD${fmt(preview.cuota)}</div>
            </div>
            <div>
              <div className="text-slate-500">Interés total</div>
              <div className="font-semibold">RD${fmt(preview.interest)}</div>
            </div>
            <div>
              <div className="text-slate-500">Total a pagar</div>
              <div className="font-semibold">RD${fmt(preview.total)}</div>
            </div>
          </div>
        </Card>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancelar</Button>
          <Button onClick={handleSubmit} disabled={submitting} data-testid="loan-submit-btn">
            {submitting ? "Creando..." : "Crear préstamo"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function LoanDetailDialog({ loan, onClose }) {
  const schedule = loan.payment_schedule || [];
  return (
    <Dialog open onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Detalle del préstamo</DialogTitle>
        </DialogHeader>
        <div className="grid grid-cols-4 gap-3 mb-3 text-xs">
          <div>
            <div className="text-slate-500">Capital</div>
            <div className="font-semibold">RD${fmt(loan.amount)}</div>
          </div>
          <div>
            <div className="text-slate-500">Cuota</div>
            <div className="font-semibold">RD${fmt(loan.monthly_payment)}</div>
          </div>
          <div>
            <div className="text-slate-500">Total a pagar</div>
            <div className="font-semibold">RD${fmt(loan.total_to_pay)}</div>
          </div>
          <div>
            <div className="text-slate-500">Saldo</div>
            <div className="font-semibold text-red-700">RD${fmt(loan.remaining_balance)}</div>
          </div>
        </div>
        <div className="border rounded max-h-96 overflow-y-auto">
          <table className="w-full text-xs">
            <thead className="bg-slate-100 sticky top-0">
              <tr>
                <th className="p-2 text-left">#</th>
                <th className="p-2 text-left">Fecha</th>
                <th className="p-2 text-right">Cuota</th>
                <th className="p-2 text-right">Capital</th>
                <th className="p-2 text-right">Interés</th>
                <th className="p-2 text-right">Saldo</th>
                <th className="p-2 text-center">Estado</th>
              </tr>
            </thead>
            <tbody>
              {schedule.map((s) => (
                <tr key={s.installment_number} className="border-t">
                  <td className="p-2 font-mono">{s.installment_number}</td>
                  <td className="p-2">{s.due_date}</td>
                  <td className="p-2 text-right font-mono">{fmt(s.amount)}</td>
                  <td className="p-2 text-right font-mono">{fmt(s.principal)}</td>
                  <td className="p-2 text-right font-mono text-slate-500">{fmt(s.interest)}</td>
                  <td className="p-2 text-right font-mono">{fmt(s.remaining_balance)}</td>
                  <td className="p-2 text-center">
                    <Badge variant="outline" className={`text-[10px] ${s.status === "paid" ? "bg-emerald-50 text-emerald-700" : "bg-slate-50 text-slate-500"}`}>
                      {s.status === "paid" ? "Pagada" : "Pendiente"}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <DialogFooter>
          <Button onClick={onClose}>Cerrar</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
