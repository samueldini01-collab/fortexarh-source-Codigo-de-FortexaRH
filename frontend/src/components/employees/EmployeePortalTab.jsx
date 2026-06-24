/**
 * EmployeePortalTab — Single tab inside EmployeeFormDialog that aggregates
 * data the employee has produced via the Portal del Empleado:
 *   - Permisos (employee_permissions): list + approve/reject + admin-create
 *   - Licencias (vacations): list + approve/reject + create
 *   - Pagos (payroll_entries): historical payslips
 *   - Ausencias (attendance: absent/late records): list + manual entry
 *
 * Designed as read+write (admin can act). Uses the existing backend
 * endpoints under /api/permissions, /api/vacations, /api/payroll,
 * /api/attendance.
 */
import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { toast } from "sonner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from "@/components/ui/dialog";
import { useAuth } from "@/App";
import { Check, X, Plus, AlertCircle, Receipt, Calendar, Clock, FileWarning, KeyRound, Copy } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const STATUS_COLORS = {
  pending: "bg-amber-100 text-amber-700 border-amber-300",
  approved: "bg-emerald-100 text-emerald-700 border-emerald-300",
  rejected: "bg-red-100 text-red-700 border-red-300",
  cancelled: "bg-slate-100 text-slate-600 border-slate-300",
  paid: "bg-blue-100 text-blue-700 border-blue-300",
  present: "bg-emerald-100 text-emerald-700 border-emerald-300",
  late: "bg-amber-100 text-amber-700 border-amber-300",
  absent: "bg-red-100 text-red-700 border-red-300",
};

const fmt = (n) =>
  new Intl.NumberFormat("es-DO", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(n || 0);

export default function EmployeePortalTab({ employeeId, employeeName, documentNumber }) {
  const [activeSub, setActiveSub] = useState("permisos");

  if (!employeeId) {
    return (
      <div className="p-6 text-center text-slate-500 text-sm flex items-center justify-center gap-2">
        <AlertCircle className="w-4 h-4" />
        Guarda el empleado primero para ver su actividad del portal.
      </div>
    );
  }

  return (
    <div className="space-y-3" data-testid="employee-portal-tab">
      <div>
        <h4 className="font-semibold text-slate-700">Portal del Empleado</h4>
        <p className="text-xs text-slate-500">
          Permisos, licencias, pagos y ausencias del empleado en el portal. Puedes crear y aprobar desde aquí.
        </p>
      </div>
      <PortalSecurityPanel
        employeeId={employeeId}
        employeeName={employeeName}
        documentNumber={documentNumber}
      />
      <Tabs value={activeSub} onValueChange={setActiveSub} className="w-full">
        <TabsList className="grid grid-cols-4 w-full mb-4">
          <TabsTrigger value="permisos" className="text-xs flex items-center gap-1" data-testid="sub-tab-permisos">
            <FileWarning className="w-3 h-3" /> Permisos
          </TabsTrigger>
          <TabsTrigger value="licencias" className="text-xs flex items-center gap-1" data-testid="sub-tab-licencias">
            <Calendar className="w-3 h-3" /> Licencias
          </TabsTrigger>
          <TabsTrigger value="pagos" className="text-xs flex items-center gap-1" data-testid="sub-tab-pagos">
            <Receipt className="w-3 h-3" /> Pagos
          </TabsTrigger>
          <TabsTrigger value="ausencias" className="text-xs flex items-center gap-1" data-testid="sub-tab-ausencias">
            <Clock className="w-3 h-3" /> Ausencias
          </TabsTrigger>
        </TabsList>
        <TabsContent value="permisos"><PermissionsPanel employeeId={employeeId} employeeName={employeeName} /></TabsContent>
        <TabsContent value="licencias"><VacationsPanel employeeId={employeeId} employeeName={employeeName} /></TabsContent>
        <TabsContent value="pagos"><PaymentsPanel employeeId={employeeId} /></TabsContent>
        <TabsContent value="ausencias"><AttendancePanel employeeId={employeeId} employeeName={employeeName} /></TabsContent>
      </Tabs>
    </div>
  );
}

// ----------------------------- Permisos --------------------------------

function PermissionsPanel({ employeeId, employeeName }) {
  const { getAuthHeaders } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreate, setShowCreate] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/permissions?employee_id=${employeeId}`, {
        headers: getAuthHeaders(), withCredentials: true,
      });
      setItems(res.data?.permissions || []);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Error cargando permisos");
    } finally {
      setLoading(false);
    }
  }, [employeeId, getAuthHeaders]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleApprove = async (id) => {
    try {
      await axios.put(`${API}/permissions/${id}/approve`, {}, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Permiso aprobado");
      fetchData();
    } catch (e) { toast.error(e?.response?.data?.detail || "Error aprobando"); }
  };
  const handleReject = async (id) => {
    if (!confirm("¿Rechazar este permiso?")) return;
    try {
      await axios.put(`${API}/permissions/${id}/reject`, {}, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Permiso rechazado");
      fetchData();
    } catch (e) { toast.error(e?.response?.data?.detail || "Error rechazando"); }
  };

  return (
    <div className="space-y-2">
      <div className="flex justify-end">
        <Button size="sm" onClick={() => setShowCreate(true)} data-testid="create-permission-btn">
          <Plus className="w-4 h-4 mr-1" /> Nuevo permiso
        </Button>
      </div>
      {loading ? (
        <div className="text-center text-sm text-slate-500 py-6">Cargando...</div>
      ) : items.length === 0 ? (
        <Card className="p-6 text-center text-sm text-slate-500">Sin permisos registrados.</Card>
      ) : (
        <div className="space-y-2 max-h-[500px] overflow-y-auto">
          {items.map((p) => (
            <Card key={p.permission_id} className="p-3" data-testid={`perm-card-${p.permission_id}`}>
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge variant="outline" className="text-xs capitalize">{p.permission_type}</Badge>
                    <Badge variant="outline" className={`text-xs ${STATUS_COLORS[p.status] || ""}`}>
                      {p.status === "pending" ? "Pendiente" : p.status === "approved" ? "Aprobado" : p.status === "rejected" ? "Rechazado" : p.status}
                    </Badge>
                    <span className="text-xs text-slate-500">{p.start_date?.slice(0, 10)} → {p.end_date?.slice(0, 10)} ({p.days} día{p.days === 1 ? "" : "s"})</span>
                  </div>
                  {p.reason && <div className="text-xs text-slate-600 mt-1">Motivo: {p.reason}</div>}
                  {p.notes && <div className="text-[10px] text-slate-500 italic mt-0.5">{p.notes}</div>}
                </div>
                {p.status === "pending" && (
                  <div className="flex gap-1">
                    <Button size="icon" variant="ghost" onClick={() => handleApprove(p.permission_id)} title="Aprobar" data-testid={`approve-perm-${p.permission_id}`}>
                      <Check className="w-4 h-4 text-emerald-600" />
                    </Button>
                    <Button size="icon" variant="ghost" onClick={() => handleReject(p.permission_id)} title="Rechazar">
                      <X className="w-4 h-4 text-red-500" />
                    </Button>
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
      {showCreate && (
        <CreatePermissionDialog
          employeeId={employeeId}
          employeeName={employeeName}
          onClose={() => setShowCreate(false)}
          onCreated={() => { setShowCreate(false); fetchData(); }}
        />
      )}
    </div>
  );
}

function CreatePermissionDialog({ employeeId, employeeName, onClose, onCreated }) {
  const { getAuthHeaders } = useAuth();
  const [permissionType, setPermissionType] = useState("medico");
  const [startDate, setStartDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [endDate, setEndDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [reason, setReason] = useState("");
  const [notes, setNotes] = useState("");
  const [status, setStatus] = useState("approved");
  const [submitting, setSubmitting] = useState(false);

  const submit = async () => {
    setSubmitting(true);
    try {
      await axios.post(`${API}/permissions`, {
        employee_id: employeeId, permission_type: permissionType,
        start_date: startDate, end_date: endDate, reason, notes, status,
      }, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Permiso creado");
      onCreated();
    } catch (e) { toast.error(e?.response?.data?.detail || "Error creando permiso"); }
    finally { setSubmitting(false); }
  };

  return (
    <Dialog open onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-md" data-testid="create-permission-dialog">
        <DialogHeader>
          <DialogTitle>Nuevo permiso — {employeeName}</DialogTitle>
        </DialogHeader>
        <div className="space-y-3">
          <div>
            <Label>Tipo</Label>
            <Select value={permissionType} onValueChange={setPermissionType}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="medico">Médico</SelectItem>
                <SelectItem value="personal">Personal</SelectItem>
                <SelectItem value="duelo">Duelo</SelectItem>
                <SelectItem value="matrimonio">Matrimonio</SelectItem>
                <SelectItem value="paternidad">Paternidad</SelectItem>
                <SelectItem value="maternidad">Maternidad</SelectItem>
                <SelectItem value="otro">Otro</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <Label>Desde</Label>
              <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} data-testid="perm-start-date" />
            </div>
            <div>
              <Label>Hasta</Label>
              <Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} data-testid="perm-end-date" />
            </div>
          </div>
          <div>
            <Label>Motivo</Label>
            <Input value={reason} onChange={(e) => setReason(e.target.value)} data-testid="perm-reason" />
          </div>
          <div>
            <Label>Notas</Label>
            <Textarea rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} />
          </div>
          <div>
            <Label>Estado inicial</Label>
            <Select value={status} onValueChange={setStatus}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="approved">Aprobado</SelectItem>
                <SelectItem value="pending">Pendiente</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancelar</Button>
          <Button onClick={submit} disabled={submitting} data-testid="perm-submit">{submitting ? "Creando..." : "Crear permiso"}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ----------------------------- Licencias / Vacaciones --------------------------------

function VacationsPanel({ employeeId, employeeName }) {
  const { getAuthHeaders } = useAuth();
  const [items, setItems] = useState([]);
  const [balance, setBalance] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [listRes, balRes] = await Promise.all([
        axios.get(`${API}/vacations?employee_id=${employeeId}`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/vacations/balance/${employeeId}`, { headers: getAuthHeaders(), withCredentials: true }).catch(() => ({ data: null })),
      ]);
      setItems(Array.isArray(listRes.data) ? listRes.data : (listRes.data?.requests || []));
      setBalance(balRes.data || null);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Error cargando licencias");
    } finally { setLoading(false); }
  }, [employeeId, getAuthHeaders]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleApprove = async (id) => {
    try {
      await axios.put(`${API}/vacations/${id}/approve`, {}, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Licencia aprobada"); fetchData();
    } catch (e) { toast.error(e?.response?.data?.detail || "Error aprobando"); }
  };
  const handleReject = async (id) => {
    const reason = prompt("Motivo de rechazo:");
    if (!reason) return;
    try {
      await axios.put(`${API}/vacations/${id}/reject`, { rejection_reason: reason }, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Licencia rechazada"); fetchData();
    } catch (e) { toast.error(e?.response?.data?.detail || "Error rechazando"); }
  };

  return (
    <div className="space-y-2">
      {balance && (
        <Card className="p-3 bg-blue-50/50">
          <div className="grid grid-cols-3 gap-3 text-xs">
            <div><div className="text-slate-500">Disponibles</div><div className="font-bold text-blue-700">{balance.available_days ?? balance.days_available ?? 0} días</div></div>
            <div><div className="text-slate-500">Tomados</div><div className="font-bold">{balance.days_taken ?? 0} días</div></div>
            <div><div className="text-slate-500">Pendientes</div><div className="font-bold text-amber-700">{balance.days_pending ?? 0} días</div></div>
          </div>
        </Card>
      )}
      {loading ? (
        <div className="text-center text-sm text-slate-500 py-6">Cargando...</div>
      ) : items.length === 0 ? (
        <Card className="p-6 text-center text-sm text-slate-500">Sin licencias registradas.</Card>
      ) : (
        <div className="space-y-2 max-h-[500px] overflow-y-auto">
          {items.map((v) => (
            <Card key={v.vacation_id || v.request_id} className="p-3">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge variant="outline" className="text-xs capitalize">{v.leave_type || v.type}</Badge>
                    <Badge variant="outline" className={`text-xs ${STATUS_COLORS[v.status] || ""}`}>
                      {v.status === "pending" ? "Pendiente" : v.status === "approved" ? "Aprobada" : v.status === "rejected" ? "Rechazada" : v.status}
                    </Badge>
                    <span className="text-xs text-slate-500">{v.start_date?.slice(0, 10)} → {v.end_date?.slice(0, 10)} ({v.days || 0} día{v.days === 1 ? "" : "s"})</span>
                  </div>
                  {v.reason && <div className="text-xs text-slate-600 mt-1">Motivo: {v.reason}</div>}
                </div>
                {v.status === "pending" && (
                  <div className="flex gap-1">
                    <Button size="icon" variant="ghost" onClick={() => handleApprove(v.vacation_id || v.request_id)} title="Aprobar">
                      <Check className="w-4 h-4 text-emerald-600" />
                    </Button>
                    <Button size="icon" variant="ghost" onClick={() => handleReject(v.vacation_id || v.request_id)} title="Rechazar">
                      <X className="w-4 h-4 text-red-500" />
                    </Button>
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

// ----------------------------- Pagos (payslips) --------------------------------

function PaymentsPanel({ employeeId }) {
  const { getAuthHeaders } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    axios
      .get(`${API}/payroll/employee/${employeeId}/history?limit=50`, { headers: getAuthHeaders(), withCredentials: true })
      .then((r) => setItems(r.data?.entries || r.data || []))
      .catch((e) => toast.error(e?.response?.data?.detail || "Error cargando pagos"))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [employeeId]);

  if (loading) return <div className="text-center text-sm text-slate-500 py-6">Cargando...</div>;
  if (!items.length) return <Card className="p-6 text-center text-sm text-slate-500">Sin pagos registrados aún.</Card>;

  return (
    <div className="border rounded max-h-[500px] overflow-y-auto">
      <table className="w-full text-xs">
        <thead className="bg-slate-100 sticky top-0">
          <tr>
            <th className="p-2 text-left">Período</th>
            <th className="p-2 text-right">Bruto</th>
            <th className="p-2 text-right">SFS</th>
            <th className="p-2 text-right">AFP</th>
            <th className="p-2 text-right">ISR</th>
            <th className="p-2 text-right">Otros</th>
            <th className="p-2 text-right">Neto</th>
            <th className="p-2 text-center">Estado</th>
          </tr>
        </thead>
        <tbody>
          {items.map((e) => (
            <tr key={e.entry_id} className="border-t hover:bg-slate-50">
              <td className="p-2">{e.period_description || e.period_id || ""}</td>
              <td className="p-2 text-right font-mono">{fmt(e.gross_salary)}</td>
              <td className="p-2 text-right font-mono text-red-600">{fmt(e.sfs_employee)}</td>
              <td className="p-2 text-right font-mono text-red-600">{fmt(e.afp_employee)}</td>
              <td className="p-2 text-right font-mono text-red-600">{fmt(e.isr)}</td>
              <td className="p-2 text-right font-mono text-orange-600">{fmt((e.total_additional_deductions || 0) + (e.total_deduction_novelties || 0) + (e.loan_deduction || 0))}</td>
              <td className="p-2 text-right font-mono font-semibold text-emerald-700">{fmt(e.net_salary)}</td>
              <td className="p-2 text-center">
                <Badge variant="outline" className={`text-[10px] ${STATUS_COLORS[e.status] || STATUS_COLORS.paid}`}>{e.status || "—"}</Badge>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ----------------------------- Ausencias (attendance) --------------------------------

function AttendancePanel({ employeeId, employeeName }) {
  const { getAuthHeaders } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const today = new Date();
  const monthStart = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().slice(0, 10);
  const monthEnd = new Date(today.getFullYear(), today.getMonth() + 1, 0).toISOString().slice(0, 10);
  const [fromDate, setFromDate] = useState(monthStart);
  const [toDate, setToDate] = useState(monthEnd);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/attendance/report/employee/${employeeId}?start_date=${fromDate}&end_date=${toDate}`, {
        headers: getAuthHeaders(), withCredentials: true,
      });
      setItems(res.data?.records || res.data?.attendance || res.data || []);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Error cargando ausencias");
    } finally { setLoading(false); }
  }, [employeeId, fromDate, toDate, getAuthHeaders]);

  useEffect(() => { fetchData(); }, [fetchData]);

  return (
    <div className="space-y-2">
      <div className="flex items-end gap-2">
        <div>
          <Label className="text-xs">Desde</Label>
          <Input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} className="h-8 text-xs" />
        </div>
        <div>
          <Label className="text-xs">Hasta</Label>
          <Input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} className="h-8 text-xs" />
        </div>
        <Button size="sm" onClick={fetchData} className="h-8">Aplicar</Button>
      </div>
      {loading ? (
        <div className="text-center text-sm text-slate-500 py-6">Cargando...</div>
      ) : !items.length ? (
        <Card className="p-6 text-center text-sm text-slate-500">Sin registros de asistencia en el rango.</Card>
      ) : (
        <div className="border rounded max-h-[450px] overflow-y-auto">
          <table className="w-full text-xs">
            <thead className="bg-slate-100 sticky top-0">
              <tr>
                <th className="p-2 text-left">Fecha</th>
                <th className="p-2 text-center">Entrada</th>
                <th className="p-2 text-center">Salida</th>
                <th className="p-2 text-right">Horas</th>
                <th className="p-2 text-center">Estado</th>
                <th className="p-2 text-left">Notas</th>
              </tr>
            </thead>
            <tbody>
              {items.map((a) => (
                <tr key={a.attendance_id || a.date} className="border-t hover:bg-slate-50">
                  <td className="p-2">{(a.date || "").slice(0, 10)}</td>
                  <td className="p-2 text-center font-mono">{(a.check_in || "").slice(11, 16) || "—"}</td>
                  <td className="p-2 text-center font-mono">{(a.check_out || "").slice(11, 16) || "—"}</td>
                  <td className="p-2 text-right font-mono">{a.total_hours || a.hours_worked || 0}</td>
                  <td className="p-2 text-center">
                    <Badge variant="outline" className={`text-[10px] ${STATUS_COLORS[a.status] || ""}`}>{a.status || "—"}</Badge>
                  </td>
                  <td className="p-2 text-slate-500">{a.notes || ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}


// ----------------------------- Seguridad del Portal --------------------------------

function PortalSecurityPanel({ employeeId, employeeName, documentNumber }) {
  const { getAuthHeaders } = useAuth();
  const [showConfirm, setShowConfirm] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [result, setResult] = useState(null); // { temporary_password, reset_at }

  const handleReset = async () => {
    setResetting(true);
    try {
      const res = await axios.post(
        `${API}/employees/${employeeId}/reset-portal-password`,
        {},
        { headers: getAuthHeaders(), withCredentials: true }
      );
      setResult(res.data);
      toast.success("Contraseña del portal reiniciada");
      setShowConfirm(false);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Error al reiniciar la contraseña");
    } finally {
      setResetting(false);
    }
  };

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success("Copiado al portapapeles");
    } catch {
      toast.error("No se pudo copiar");
    }
  };

  return (
    <Card className="p-3 bg-amber-50/40 border-amber-200" data-testid="portal-security-panel">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div className="flex items-start gap-2">
          <KeyRound className="w-4 h-4 text-amber-600 mt-0.5" />
          <div>
            <div className="font-semibold text-sm text-slate-700">Acceso al Portal del Empleado</div>
            <div className="text-xs text-slate-600">
              Si el empleado olvidó su contraseña, puedes reiniciarla a su cédula/pasaporte.
              El empleado iniciará sesión con ese valor y podrá cambiarla desde el portal.
            </div>
          </div>
        </div>
        <Button
          size="sm"
          variant="outline"
          className="border-amber-400 text-amber-700 hover:bg-amber-100"
          onClick={() => setShowConfirm(true)}
          data-testid="reset-portal-password-btn"
        >
          <KeyRound className="w-4 h-4 mr-1" /> Reiniciar contraseña
        </Button>
      </div>

      {result && (
        <div
          className="mt-3 p-3 rounded border border-emerald-300 bg-emerald-50"
          data-testid="reset-portal-password-result"
        >
          <div className="text-xs text-emerald-800 font-semibold mb-1">
            Contraseña reiniciada correctamente
          </div>
          <div className="text-xs text-slate-700">
            Comunica al empleado que su contraseña temporal ahora es su cédula/pasaporte:
          </div>
          <div className="flex items-center gap-2 mt-2">
            <code className="flex-1 px-2 py-1 rounded bg-white border text-sm font-mono">
              {result.temporary_password}
            </code>
            <Button
              size="sm"
              variant="outline"
              onClick={() => copyToClipboard(result.temporary_password)}
              data-testid="copy-temporary-password-btn"
            >
              <Copy className="w-3 h-3 mr-1" /> Copiar
            </Button>
          </div>
          <div className="text-[10px] text-slate-500 mt-1">
            Recomienda al empleado cambiarla desde el portal tras iniciar sesión.
          </div>
        </div>
      )}

      {showConfirm && (
        <Dialog open onOpenChange={(o) => !o && setShowConfirm(false)}>
          <DialogContent className="max-w-md" data-testid="reset-portal-password-dialog">
            <DialogHeader>
              <DialogTitle>Reiniciar contraseña del portal</DialogTitle>
            </DialogHeader>
            <div className="space-y-2 text-sm text-slate-700">
              <p>
                Vas a reiniciar la contraseña del Portal del Empleado de{" "}
                <span className="font-semibold">{employeeName}</span>.
              </p>
              <p>
                La nueva contraseña temporal será la cédula/pasaporte del empleado
                {documentNumber ? (
                  <>
                    {" "}(<code className="px-1 bg-slate-100 rounded">{documentNumber}</code>)
                  </>
                ) : null}
                . El empleado deberá cambiarla luego de iniciar sesión.
              </p>
              <p className="text-xs text-amber-700">
                Esta acción invalidará la contraseña actual del empleado.
              </p>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowConfirm(false)} disabled={resetting}>
                Cancelar
              </Button>
              <Button
                onClick={handleReset}
                disabled={resetting}
                data-testid="confirm-reset-portal-password-btn"
              >
                {resetting ? "Reiniciando..." : "Sí, reiniciar"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </Card>
  );
}
