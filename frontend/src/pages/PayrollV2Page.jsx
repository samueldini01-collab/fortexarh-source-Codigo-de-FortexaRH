import { useState, useEffect, useCallback } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Plus, 
  Calendar,
  Users,
  DollarSign,
  Calculator,
  Check,
  CreditCard,
  FileText,
  Edit,
  Trash2,
  RefreshCw,
  Download,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  ChevronRight,
  Building2
} from "lucide-react";
import { toast } from "sonner";

const months = [
  { value: 1, label: "Enero" },
  { value: 2, label: "Febrero" },
  { value: 3, label: "Marzo" },
  { value: 4, label: "Abril" },
  { value: 5, label: "Mayo" },
  { value: 6, label: "Junio" },
  { value: 7, label: "Julio" },
  { value: 8, label: "Agosto" },
  { value: 9, label: "Septiembre" },
  { value: 10, label: "Octubre" },
  { value: 11, label: "Noviembre" },
  { value: 12, label: "Diciembre" }
];

const periodTypes = [
  { value: "quincenal_1", label: "Quincenal (1-15)" },
  { value: "quincenal_2", label: "Quincenal (16-30/31)" },
  { value: "mensual", label: "Mensual" }
];

export default function PayrollV2Page() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [periods, setPeriods] = useState([]);
  const [selectedPeriod, setSelectedPeriod] = useState(null);
  const [periodEntries, setPeriodEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showNewPeriod, setShowNewPeriod] = useState(false);
  const [showEditEntry, setShowEditEntry] = useState(false);
  const [selectedEntry, setSelectedEntry] = useState(null);
  
  // Form states
  const [newPeriodForm, setNewPeriodForm] = useState({
    period_type: "quincenal_1",
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1,
    start_date: "",
    end_date: "",
    description: ""
  });
  
  const [editEntryForm, setEditEntryForm] = useState({
    base_salary: 0,
    overtime_day_hours: 0,
    overtime_night_hours: 0,
    overtime_weekend_hours: 0,
    overtime_holiday_hours: 0,
    bonuses: 0,
    commissions: 0,
    additional_deductions: []
  });

  const { getAuthHeaders } = useAuth();

  useEffect(() => {
    fetchPeriods();
  }, []);

  useEffect(() => {
    if (selectedPeriod) {
      fetchPeriodDetails(selectedPeriod.period_id);
    }
  }, [selectedPeriod]);

  // Auto-set dates based on period type
  useEffect(() => {
    const { period_type, year, month } = newPeriodForm;
    let start_date = "", end_date = "";
    
    if (period_type === "quincenal_1") {
      start_date = `${year}-${String(month).padStart(2, '0')}-01`;
      end_date = `${year}-${String(month).padStart(2, '0')}-15`;
    } else if (period_type === "quincenal_2") {
      const lastDay = new Date(year, month, 0).getDate();
      start_date = `${year}-${String(month).padStart(2, '0')}-16`;
      end_date = `${year}-${String(month).padStart(2, '0')}-${lastDay}`;
    } else if (period_type === "mensual") {
      const lastDay = new Date(year, month, 0).getDate();
      start_date = `${year}-${String(month).padStart(2, '0')}-01`;
      end_date = `${year}-${String(month).padStart(2, '0')}-${lastDay}`;
    }
    
    setNewPeriodForm(prev => ({ ...prev, start_date, end_date }));
  }, [newPeriodForm.period_type, newPeriodForm.year, newPeriodForm.month]);

  const fetchPeriods = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/payroll-v2/periods`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setPeriods(response.data);
    } catch (error) {
      console.error("Error fetching periods:", error);
      toast.error("Error al cargar períodos");
    } finally {
      setLoading(false);
    }
  };

  const fetchPeriodDetails = async (periodId) => {
    try {
      const response = await axios.get(`${API}/payroll-v2/periods/${periodId}`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setPeriodEntries(response.data.entries || []);
    } catch (error) {
      console.error("Error fetching period details:", error);
    }
  };

  const handleCreatePeriod = async () => {
    try {
      await axios.post(`${API}/payroll-v2/periods`, newPeriodForm, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success("Período creado correctamente");
      setShowNewPeriod(false);
      fetchPeriods();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al crear período");
    }
  };

  const handleAddEmployees = async (periodId) => {
    try {
      const response = await axios.post(`${API}/payroll-v2/periods/${periodId}/add-employees`, {}, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success(response.data.message);
      fetchPeriodDetails(periodId);
      fetchPeriods();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al agregar empleados");
    }
  };

  const handleCalculatePeriod = async (periodId) => {
    try {
      await axios.post(`${API}/payroll-v2/periods/${periodId}/calculate`, {}, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success("Nóminas calculadas correctamente");
      fetchPeriodDetails(periodId);
      fetchPeriods();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al calcular");
    }
  };

  const handleApprovePeriod = async (periodId) => {
    try {
      await axios.post(`${API}/payroll-v2/periods/${periodId}/approve`, {}, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success("Período aprobado");
      fetchPeriods();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al aprobar");
    }
  };

  const handlePayPeriod = async (periodId) => {
    if (!confirm("¿Está seguro de pagar este período? Se generará el asiento contable automáticamente.")) return;
    
    try {
      const response = await axios.post(`${API}/payroll-v2/periods/${periodId}/pay`, {}, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success(`Nómina pagada. Asiento #${response.data.entry_number} generado.`);
      fetchPeriods();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al pagar");
    }
  };

  const handleDeletePeriod = async (periodId) => {
    if (!confirm("¿Está seguro de eliminar este período? También se eliminará el asiento contable asociado.")) return;
    
    try {
      await axios.delete(`${API}/payroll-v2/periods/${periodId}`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success("Período eliminado");
      setSelectedPeriod(null);
      fetchPeriods();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al eliminar");
    }
  };

  const openEditEntry = (entry) => {
    setSelectedEntry(entry);
    setEditEntryForm({
      base_salary: entry.base_salary || 0,
      overtime_day_hours: entry.overtime_day_hours || 0,
      overtime_night_hours: entry.overtime_night_hours || 0,
      overtime_weekend_hours: entry.overtime_weekend_hours || 0,
      overtime_holiday_hours: entry.overtime_holiday_hours || 0,
      bonuses: entry.bonuses || 0,
      commissions: entry.commissions || 0,
      additional_deductions: entry.additional_deductions || []
    });
    setShowEditEntry(true);
  };

  const handleUpdateEntry = async () => {
    try {
      await axios.put(`${API}/payroll-v2/entries/${selectedEntry.entry_id}`, {
        ...editEntryForm,
        period_id: selectedEntry.period_id,
        employee_id: selectedEntry.employee_id
      }, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success("Entrada actualizada");
      setShowEditEntry(false);
      fetchPeriodDetails(selectedEntry.period_id);
      fetchPeriods();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al actualizar");
    }
  };

  const handleDeleteEntry = async (entryId, periodId) => {
    if (!confirm("¿Eliminar esta entrada de nómina?")) return;
    
    try {
      await axios.delete(`${API}/payroll-v2/entries/${entryId}`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success("Entrada eliminada");
      fetchPeriodDetails(periodId);
      fetchPeriods();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al eliminar");
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-DO', {
      style: 'currency',
      currency: 'DOP',
      minimumFractionDigits: 2
    }).format(value || 0);
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'open':
        return <Badge variant="outline" className="border-blue-500 text-blue-600">Abierto</Badge>;
      case 'calculated':
        return <Badge className="bg-amber-100 text-amber-700">Calculado</Badge>;
      case 'approved':
        return <Badge className="bg-emerald-100 text-emerald-700">Aprobado</Badge>;
      case 'paid':
        return <Badge className="bg-purple-100 text-purple-700">Pagado</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  // Dashboard stats
  const stats = {
    openPeriods: periods.filter(p => p.status === 'open').length,
    pendingPayrolls: periods.filter(p => ['calculated', 'approved'].includes(p.status)).length,
    approvedPayrolls: periods.filter(p => p.status === 'approved').length,
    totalPaid: periods.filter(p => p.status === 'paid').reduce((sum, p) => sum + (p.total_net || 0), 0)
  };

  return (
    <DashboardLayout title="Nómina">
      <div className="space-y-6" data-testid="payroll-v2-page">
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Nómina</h1>
            <p className="text-slate-500">Gestión de pagos, períodos y cálculos salariales.</p>
          </div>
          <Button onClick={fetchPeriods} variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Actualizar
          </Button>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid grid-cols-5 w-full max-w-2xl">
            <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
            <TabsTrigger value="periodos">Períodos ({periods.length})</TabsTrigger>
            <TabsTrigger value="calculo">Cálculo</TabsTrigger>
            <TabsTrigger value="aprobacion">Aprobación</TabsTrigger>
            <TabsTrigger value="reportes">Reportes</TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card className="border-l-4 border-l-blue-500">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-500">Períodos Abiertos</p>
                      <p className="text-2xl font-bold text-blue-600">{stats.openPeriods}</p>
                    </div>
                    <Calendar className="w-8 h-8 text-blue-300" />
                  </div>
                </CardContent>
              </Card>
              <Card className="border-l-4 border-l-orange-500">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-500">Nóminas Pendientes</p>
                      <p className="text-2xl font-bold text-orange-600">{stats.pendingPayrolls}</p>
                    </div>
                    <AlertCircle className="w-8 h-8 text-orange-300" />
                  </div>
                </CardContent>
              </Card>
              <Card className="border-l-4 border-l-emerald-500">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-500">Nóminas Aprobadas</p>
                      <p className="text-2xl font-bold text-emerald-600">{stats.approvedPayrolls}</p>
                    </div>
                    <CheckCircle className="w-8 h-8 text-emerald-300" />
                  </div>
                </CardContent>
              </Card>
              <Card className="border-l-4 border-l-purple-500">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-500">Total Pagado (Neto)</p>
                      <p className="text-xl font-bold text-purple-600">{formatCurrency(stats.totalPaid)}</p>
                    </div>
                    <DollarSign className="w-8 h-8 text-purple-300" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Clock className="w-5 h-5 text-blue-500" />
                    Estado de Nóminas
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                    <span className="text-slate-600">Borrador</span>
                    <span className="bg-slate-200 text-slate-700 px-3 py-1 rounded-full text-sm">
                      {periods.filter(p => p.status === 'open').length}
                    </span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                    <span className="text-blue-700">Calculadas (Pendientes)</span>
                    <span className="bg-blue-200 text-blue-800 px-3 py-1 rounded-full text-sm">
                      {periods.filter(p => p.status === 'calculated').length}
                    </span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-emerald-50 rounded-lg">
                    <span className="text-emerald-700">Aprobadas</span>
                    <span className="bg-emerald-200 text-emerald-800 px-3 py-1 rounded-full text-sm">
                      {periods.filter(p => p.status === 'approved').length}
                    </span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <DollarSign className="w-5 h-5 text-emerald-500" />
                    Resumen Financiero (Aprobado)
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center justify-between p-3 border-b">
                    <span className="text-slate-600">Salario Bruto</span>
                    <span className="font-mono">
                      {formatCurrency(periods.filter(p => p.status === 'approved').reduce((s, p) => s + (p.total_gross || 0), 0))}
                    </span>
                  </div>
                  <div className="flex items-center justify-between p-3 border-b">
                    <span className="text-red-600">Descuentos</span>
                    <span className="font-mono text-red-600">
                      - {formatCurrency(periods.filter(p => p.status === 'approved').reduce((s, p) => s + (p.total_deductions || 0), 0))}
                    </span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-emerald-50 rounded-lg">
                    <span className="font-semibold text-emerald-700">Total Neto</span>
                    <span className="font-mono font-bold text-emerald-700">
                      {formatCurrency(periods.filter(p => p.status === 'approved').reduce((s, p) => s + (p.total_net || 0), 0))}
                    </span>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Períodos Tab */}
          <TabsContent value="periodos" className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold">Períodos de Nómina</h3>
              <Button onClick={() => setShowNewPeriod(true)} data-testid="new-period-btn">
                <Plus className="w-4 h-4 mr-2" />
                Nuevo Período
              </Button>
            </div>

            {loading ? (
              <div className="space-y-4">
                {[1, 2, 3].map(i => (
                  <div key={i} className="h-20 bg-slate-100 rounded-lg animate-pulse" />
                ))}
              </div>
            ) : periods.length === 0 ? (
              <Card className="py-12">
                <CardContent className="text-center">
                  <Calendar className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                  <p className="text-slate-500 mb-4">No hay períodos de nómina</p>
                  <Button onClick={() => setShowNewPeriod(true)}>Crear Primer Período</Button>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {periods.map(period => (
                  <Card 
                    key={period.period_id} 
                    className={`cursor-pointer transition-all ${selectedPeriod?.period_id === period.period_id ? 'ring-2 ring-blue-500' : 'hover:shadow-md'}`}
                    onClick={() => setSelectedPeriod(period)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                            <Calendar className="w-6 h-6 text-blue-600" />
                          </div>
                          <div>
                            <h4 className="font-semibold">{period.description}</h4>
                            <p className="text-sm text-slate-500">
                              {period.start_date} - {period.end_date} • {period.employee_count} empleados
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="text-right">
                            <p className="text-sm text-slate-500">Total Neto</p>
                            <p className="font-mono font-semibold">{formatCurrency(period.total_net)}</p>
                          </div>
                          {getStatusBadge(period.status)}
                          <ChevronRight className="w-5 h-5 text-slate-400" />
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {/* Period Details Panel */}
            {selectedPeriod && (
              <Card className="mt-6">
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle>{selectedPeriod.description}</CardTitle>
                    <CardDescription>
                      {selectedPeriod.start_date} - {selectedPeriod.end_date}
                    </CardDescription>
                  </div>
                  <div className="flex gap-2">
                    {selectedPeriod.status === 'open' && (
                      <>
                        <Button size="sm" variant="outline" onClick={() => handleAddEmployees(selectedPeriod.period_id)}>
                          <Users className="w-4 h-4 mr-1" />
                          Agregar Empleados
                        </Button>
                        <Button size="sm" onClick={() => handleCalculatePeriod(selectedPeriod.period_id)}>
                          <Calculator className="w-4 h-4 mr-1" />
                          Calcular
                        </Button>
                      </>
                    )}
                    {selectedPeriod.status === 'calculated' && (
                      <Button size="sm" onClick={() => handleApprovePeriod(selectedPeriod.period_id)}>
                        <Check className="w-4 h-4 mr-1" />
                        Aprobar
                      </Button>
                    )}
                    {['calculated', 'approved'].includes(selectedPeriod.status) && (
                      <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700" onClick={() => handlePayPeriod(selectedPeriod.period_id)}>
                        <CreditCard className="w-4 h-4 mr-1" />
                        Pagar
                      </Button>
                    )}
                    {selectedPeriod.status !== 'paid' && (
                      <Button size="sm" variant="destructive" onClick={() => handleDeletePeriod(selectedPeriod.period_id)}>
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  {periodEntries.length === 0 ? (
                    <div className="text-center py-8 text-slate-500">
                      <Users className="w-10 h-10 mx-auto mb-2 text-slate-300" />
                      <p>No hay empleados en este período</p>
                      <Button variant="link" onClick={() => handleAddEmployees(selectedPeriod.period_id)}>
                        Agregar empleados activos
                      </Button>
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Empleado</TableHead>
                            <TableHead>Departamento</TableHead>
                            <TableHead className="text-right">Salario Base</TableHead>
                            <TableHead className="text-right">H. Extras</TableHead>
                            <TableHead className="text-right">Bonos</TableHead>
                            <TableHead className="text-right">Bruto</TableHead>
                            <TableHead className="text-right">Deducciones</TableHead>
                            <TableHead className="text-right">Neto</TableHead>
                            <TableHead></TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {periodEntries.map(entry => (
                            <TableRow key={entry.entry_id}>
                              <TableCell>
                                <div>
                                  <p className="font-medium">{entry.employee_name}</p>
                                  <p className="text-xs text-slate-500">{entry.position}</p>
                                </div>
                              </TableCell>
                              <TableCell>{entry.department}</TableCell>
                              <TableCell className="text-right font-mono">{formatCurrency(entry.base_salary)}</TableCell>
                              <TableCell className="text-right font-mono text-blue-600">
                                {formatCurrency(
                                  (entry.overtime_day_amount || 0) +
                                  (entry.overtime_night_amount || 0) +
                                  (entry.overtime_weekend_amount || 0) +
                                  (entry.overtime_holiday_amount || 0)
                                )}
                              </TableCell>
                              <TableCell className="text-right font-mono text-emerald-600">
                                {formatCurrency(entry.bonuses + entry.commissions)}
                              </TableCell>
                              <TableCell className="text-right font-mono font-semibold">
                                {formatCurrency(entry.gross_salary)}
                              </TableCell>
                              <TableCell className="text-right font-mono text-red-600">
                                -{formatCurrency(entry.total_deductions)}
                              </TableCell>
                              <TableCell className="text-right font-mono font-bold text-emerald-700">
                                {formatCurrency(entry.net_salary)}
                              </TableCell>
                              <TableCell>
                                {selectedPeriod.status !== 'paid' && (
                                  <div className="flex gap-1">
                                    <Button size="icon" variant="ghost" onClick={() => openEditEntry(entry)}>
                                      <Edit className="w-4 h-4" />
                                    </Button>
                                    <Button size="icon" variant="ghost" className="text-red-500" onClick={() => handleDeleteEntry(entry.entry_id, selectedPeriod.period_id)}>
                                      <Trash2 className="w-4 h-4" />
                                    </Button>
                                  </div>
                                )}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  )}

                  {/* Period Totals */}
                  {periodEntries.length > 0 && (
                    <div className="mt-4 p-4 bg-slate-50 rounded-lg">
                      <div className="grid grid-cols-4 gap-4 text-center">
                        <div>
                          <p className="text-sm text-slate-500">Total Bruto</p>
                          <p className="font-mono font-bold">{formatCurrency(selectedPeriod.total_gross)}</p>
                        </div>
                        <div>
                          <p className="text-sm text-slate-500">Total Deducciones</p>
                          <p className="font-mono font-bold text-red-600">-{formatCurrency(selectedPeriod.total_deductions)}</p>
                        </div>
                        <div>
                          <p className="text-sm text-slate-500">Total Neto</p>
                          <p className="font-mono font-bold text-emerald-600">{formatCurrency(selectedPeriod.total_net)}</p>
                        </div>
                        <div>
                          <p className="text-sm text-slate-500">Empleados</p>
                          <p className="font-mono font-bold">{selectedPeriod.employee_count}</p>
                        </div>
                      </div>
                      {selectedPeriod.journal_entry_id && (
                        <div className="mt-4 p-3 bg-purple-50 rounded-lg flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <FileText className="w-5 h-5 text-purple-600" />
                            <span className="text-purple-700">Asiento Contable Generado</span>
                          </div>
                          <Badge className="bg-purple-200 text-purple-800">
                            {selectedPeriod.journal_entry_id}
                          </Badge>
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Cálculo Tab */}
          <TabsContent value="calculo" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Cálculo de Nóminas</CardTitle>
                <CardDescription>Períodos pendientes de cálculo o recálculo</CardDescription>
              </CardHeader>
              <CardContent>
                {periods.filter(p => ['open', 'calculated'].includes(p.status)).length === 0 ? (
                  <div className="text-center py-8 text-slate-500">
                    <Calculator className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                    <p>No hay períodos pendientes de cálculo</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {periods.filter(p => ['open', 'calculated'].includes(p.status)).map(period => (
                      <div key={period.period_id} className="flex items-center justify-between p-4 border rounded-lg">
                        <div>
                          <h4 className="font-semibold">{period.description}</h4>
                          <p className="text-sm text-slate-500">{period.employee_count} empleados</p>
                        </div>
                        <div className="flex items-center gap-4">
                          {getStatusBadge(period.status)}
                          <Button onClick={() => { setSelectedPeriod(period); handleCalculatePeriod(period.period_id); }}>
                            <Calculator className="w-4 h-4 mr-2" />
                            {period.status === 'calculated' ? 'Recalcular' : 'Calcular'}
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Aprobación Tab */}
          <TabsContent value="aprobacion" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Aprobación de Nóminas</CardTitle>
                <CardDescription>Períodos calculados pendientes de aprobación</CardDescription>
              </CardHeader>
              <CardContent>
                {periods.filter(p => p.status === 'calculated').length === 0 ? (
                  <div className="text-center py-8 text-slate-500">
                    <Check className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                    <p>No hay períodos pendientes de aprobación</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {periods.filter(p => p.status === 'calculated').map(period => (
                      <div key={period.period_id} className="flex items-center justify-between p-4 border rounded-lg">
                        <div>
                          <h4 className="font-semibold">{period.description}</h4>
                          <p className="text-sm text-slate-500">
                            {period.employee_count} empleados • Total: {formatCurrency(period.total_net)}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <Button variant="outline" onClick={() => { setSelectedPeriod(period); setActiveTab('periodos'); }}>
                            Ver Detalle
                          </Button>
                          <Button onClick={() => handleApprovePeriod(period.period_id)}>
                            <Check className="w-4 h-4 mr-2" />
                            Aprobar
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Períodos Aprobados - Listos para Pagar */}
            <Card>
              <CardHeader>
                <CardTitle className="text-emerald-700">Listos para Pagar</CardTitle>
                <CardDescription>Períodos aprobados que pueden ser pagados</CardDescription>
              </CardHeader>
              <CardContent>
                {periods.filter(p => p.status === 'approved').length === 0 ? (
                  <div className="text-center py-8 text-slate-500">
                    <CreditCard className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                    <p>No hay períodos aprobados</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {periods.filter(p => p.status === 'approved').map(period => (
                      <div key={period.period_id} className="flex items-center justify-between p-4 border border-emerald-200 bg-emerald-50 rounded-lg">
                        <div>
                          <h4 className="font-semibold text-emerald-800">{period.description}</h4>
                          <p className="text-sm text-emerald-600">
                            {period.employee_count} empleados • Total Neto: {formatCurrency(period.total_net)}
                          </p>
                        </div>
                        <Button className="bg-emerald-600 hover:bg-emerald-700" onClick={() => handlePayPeriod(period.period_id)}>
                          <CreditCard className="w-4 h-4 mr-2" />
                          Pagar y Generar Asiento
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Reportes Tab */}
          <TabsContent value="reportes" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Reportes de Nómina</CardTitle>
                <CardDescription>Exportar información de nóminas pagadas</CardDescription>
              </CardHeader>
              <CardContent>
                {periods.filter(p => p.status === 'paid').length === 0 ? (
                  <div className="text-center py-8 text-slate-500">
                    <FileText className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                    <p>No hay nóminas pagadas para reportar</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {periods.filter(p => p.status === 'paid').map(period => (
                      <div key={period.period_id} className="flex items-center justify-between p-4 border rounded-lg">
                        <div>
                          <h4 className="font-semibold">{period.description}</h4>
                          <p className="text-sm text-slate-500">
                            {period.employee_count} empleados • Pagado: {formatCurrency(period.total_net)}
                          </p>
                          {period.journal_entry_id && (
                            <p className="text-xs text-purple-600">Asiento: {period.journal_entry_id}</p>
                          )}
                        </div>
                        <div className="flex gap-2">
                          <Button variant="outline" size="sm">
                            <Download className="w-4 h-4 mr-1" />
                            Excel
                          </Button>
                          <Button variant="outline" size="sm">
                            <Download className="w-4 h-4 mr-1" />
                            PDF
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* New Period Dialog */}
        <Dialog open={showNewPeriod} onOpenChange={setShowNewPeriod}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Crear Nuevo Período de Nómina</DialogTitle>
              <DialogDescription>Define el período para procesar la nómina</DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Tipo de Período</Label>
                <Select 
                  value={newPeriodForm.period_type} 
                  onValueChange={(v) => setNewPeriodForm({...newPeriodForm, period_type: v})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {periodTypes.map(type => (
                      <SelectItem key={type.value} value={type.value}>{type.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Año</Label>
                  <Select 
                    value={String(newPeriodForm.year)} 
                    onValueChange={(v) => setNewPeriodForm({...newPeriodForm, year: parseInt(v)})}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {[2024, 2025, 2026, 2027].map(year => (
                        <SelectItem key={year} value={String(year)}>{year}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Mes</Label>
                  <Select 
                    value={String(newPeriodForm.month)} 
                    onValueChange={(v) => setNewPeriodForm({...newPeriodForm, month: parseInt(v)})}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {months.map(m => (
                        <SelectItem key={m.value} value={String(m.value)}>{m.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Fecha Inicio</Label>
                  <Input 
                    type="date" 
                    value={newPeriodForm.start_date}
                    onChange={(e) => setNewPeriodForm({...newPeriodForm, start_date: e.target.value})}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Fecha Fin</Label>
                  <Input 
                    type="date" 
                    value={newPeriodForm.end_date}
                    onChange={(e) => setNewPeriodForm({...newPeriodForm, end_date: e.target.value})}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Descripción (Opcional)</Label>
                <Input 
                  value={newPeriodForm.description}
                  onChange={(e) => setNewPeriodForm({...newPeriodForm, description: e.target.value})}
                  placeholder={`Nómina ${periodTypes.find(t => t.value === newPeriodForm.period_type)?.label} - ${months.find(m => m.value === newPeriodForm.month)?.label} ${newPeriodForm.year}`}
                />
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setShowNewPeriod(false)}>Cancelar</Button>
              <Button onClick={handleCreatePeriod}>Crear Período</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Edit Entry Dialog */}
        <Dialog open={showEditEntry} onOpenChange={setShowEditEntry}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Editar Nómina - {selectedEntry?.employee_name}</DialogTitle>
              <DialogDescription>Modificar valores de la nómina del empleado</DialogDescription>
            </DialogHeader>
            
            <div className="space-y-6">
              <div className="space-y-2">
                <Label>Salario Base</Label>
                <Input 
                  type="number" 
                  step="0.01"
                  value={editEntryForm.base_salary}
                  onChange={(e) => setEditEntryForm({...editEntryForm, base_salary: parseFloat(e.target.value) || 0})}
                />
              </div>

              <div className="space-y-3">
                <Label className="font-semibold">Horas Extras</Label>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-sm text-slate-500">Horas Extras Diurnas (35%)</Label>
                    <Input 
                      type="number" 
                      step="0.5"
                      value={editEntryForm.overtime_day_hours}
                      onChange={(e) => setEditEntryForm({...editEntryForm, overtime_day_hours: parseFloat(e.target.value) || 0})}
                      placeholder="0"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-sm text-slate-500">Horas Extras Nocturnas (15%)</Label>
                    <Input 
                      type="number" 
                      step="0.5"
                      value={editEntryForm.overtime_night_hours}
                      onChange={(e) => setEditEntryForm({...editEntryForm, overtime_night_hours: parseFloat(e.target.value) || 0})}
                      placeholder="0"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-sm text-slate-500">Horas Extras Fin de Semana (100%)</Label>
                    <Input 
                      type="number" 
                      step="0.5"
                      value={editEntryForm.overtime_weekend_hours}
                      onChange={(e) => setEditEntryForm({...editEntryForm, overtime_weekend_hours: parseFloat(e.target.value) || 0})}
                      placeholder="0"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-sm text-slate-500">Horas Extras Días Feriados (100%)</Label>
                    <Input 
                      type="number" 
                      step="0.5"
                      value={editEntryForm.overtime_holiday_hours}
                      onChange={(e) => setEditEntryForm({...editEntryForm, overtime_holiday_hours: parseFloat(e.target.value) || 0})}
                      placeholder="0"
                    />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Bonificaciones</Label>
                  <Input 
                    type="number" 
                    step="0.01"
                    value={editEntryForm.bonuses}
                    onChange={(e) => setEditEntryForm({...editEntryForm, bonuses: parseFloat(e.target.value) || 0})}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Comisiones</Label>
                  <Input 
                    type="number" 
                    step="0.01"
                    value={editEntryForm.commissions}
                    onChange={(e) => setEditEntryForm({...editEntryForm, commissions: parseFloat(e.target.value) || 0})}
                  />
                </div>
              </div>

              <div className="p-4 bg-slate-50 rounded-lg">
                <p className="text-sm text-slate-500 mb-2">Las deducciones de ley (SFS, AFP, ISR) se calculan automáticamente sobre el salario bruto.</p>
                {selectedEntry && (
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <p className="text-slate-500">SFS (3.04%)</p>
                      <p className="font-mono">{formatCurrency(selectedEntry.sfs_employee)}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">AFP (2.87%)</p>
                      <p className="font-mono">{formatCurrency(selectedEntry.afp_employee)}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">ISR</p>
                      <p className="font-mono">{formatCurrency(selectedEntry.isr)}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setShowEditEntry(false)}>Cancelar</Button>
              <Button onClick={handleUpdateEntry}>Guardar Cambios</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
