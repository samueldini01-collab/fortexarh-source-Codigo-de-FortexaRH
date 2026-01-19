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
import { Checkbox } from "@/components/ui/checkbox";
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
  Building2,
  Save,
  X,
  Printer,
  FileSpreadsheet,
  Wallet
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
  const [showPayDialog, setShowPayDialog] = useState(false);
  const [bankAccounts, setBankAccounts] = useState([]);
  const [selectedBankAccount, setSelectedBankAccount] = useState("");
  const [companyName, setCompanyName] = useState("NOMBRE DE LA EMPRESA");
  
  // Inline editing states
  const [editingCell, setEditingCell] = useState(null);
  const [editValue, setEditValue] = useState("");
  
  // Form states
  const [newPeriodForm, setNewPeriodForm] = useState({
    period_type: "quincenal_1",
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1,
    start_date: "",
    end_date: "",
    description: ""
  });

  const { getAuthHeaders, user } = useAuth();

  useEffect(() => {
    fetchPeriods();
    fetchBankAccounts();
    if (user?.company_name) {
      setCompanyName(user.company_name);
    }
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

  const fetchBankAccounts = async () => {
    try {
      const response = await axios.get(`${API}/accounting/accounts`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      // Filter bank accounts (code starts with 1101 or type is asset with "banco" in name)
      const banks = response.data.filter(acc => 
        acc.code.startsWith('1101') || 
        (acc.account_type === 'asset' && acc.name.toLowerCase().includes('banco'))
      );
      setBankAccounts(banks);
      if (banks.length > 0) {
        setSelectedBankAccount(banks[0].code);
      }
    } catch (error) {
      console.error("Error fetching bank accounts:", error);
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

  const openPayDialog = (period) => {
    setSelectedPeriod(period);
    setShowPayDialog(true);
  };

  const handlePayPeriod = async () => {
    if (!selectedPeriod) return;
    
    try {
      const response = await axios.post(`${API}/payroll-v2/periods/${selectedPeriod.period_id}/pay`, 
        { bank_account_code: selectedBankAccount },
        {
          headers: getAuthHeaders(),
          withCredentials: true
        }
      );
      toast.success(`Nómina pagada. Asiento #${response.data.entry_number} generado.`);
      setShowPayDialog(false);
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

  // Inline editing handlers
  const startEditing = (entryId, field, currentValue) => {
    if (selectedPeriod?.status === 'paid') return;
    setEditingCell({ entryId, field });
    setEditValue(String(currentValue || 0));
  };

  const cancelEditing = () => {
    setEditingCell(null);
    setEditValue("");
  };

  const saveInlineEdit = async () => {
    if (!editingCell) return;
    
    const entry = periodEntries.find(e => e.entry_id === editingCell.entryId);
    if (!entry) return;

    try {
      const updateData = {
        period_id: entry.period_id,
        employee_id: entry.employee_id,
        base_salary: entry.base_salary,
        overtime_day_hours: entry.overtime_day_hours || 0,
        overtime_night_hours: entry.overtime_night_hours || 0,
        overtime_weekend_hours: entry.overtime_weekend_hours || 0,
        overtime_holiday_hours: entry.overtime_holiday_hours || 0,
        bonuses: entry.bonuses || 0,
        commissions: entry.commissions || 0,
        additional_deductions: entry.additional_deductions || []
      };

      // Update the specific field
      const numValue = parseFloat(editValue) || 0;
      if (editingCell.field === 'base_salary') updateData.base_salary = numValue;
      else if (editingCell.field === 'bonuses') updateData.bonuses = numValue;
      else if (editingCell.field === 'commissions') updateData.commissions = numValue;
      else if (editingCell.field === 'overtime_day_hours') updateData.overtime_day_hours = numValue;
      else if (editingCell.field === 'overtime_night_hours') updateData.overtime_night_hours = numValue;
      else if (editingCell.field === 'overtime_weekend_hours') updateData.overtime_weekend_hours = numValue;
      else if (editingCell.field === 'overtime_holiday_hours') updateData.overtime_holiday_hours = numValue;

      await axios.put(`${API}/payroll-v2/entries/${entry.entry_id}`, updateData, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      
      toast.success("Valor actualizado");
      fetchPeriodDetails(entry.period_id);
      fetchPeriods();
    } catch (error) {
      toast.error("Error al actualizar");
    } finally {
      cancelEditing();
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

  const formatNumber = (value) => {
    return new Intl.NumberFormat('es-DO', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
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

  // Render editable cell
  const renderEditableCell = (entry, field, value, isCurrency = true) => {
    const isEditing = editingCell?.entryId === entry.entry_id && editingCell?.field === field;
    const canEdit = selectedPeriod?.status !== 'paid';
    
    if (isEditing) {
      return (
        <div className="flex items-center gap-1">
          <Input
            type="number"
            step="0.01"
            className="w-24 h-7 text-right text-xs"
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') saveInlineEdit();
              if (e.key === 'Escape') cancelEditing();
            }}
            autoFocus
          />
          <Button size="icon" variant="ghost" className="h-6 w-6" onClick={saveInlineEdit}>
            <Check className="w-3 h-3 text-emerald-600" />
          </Button>
          <Button size="icon" variant="ghost" className="h-6 w-6" onClick={cancelEditing}>
            <X className="w-3 h-3 text-red-500" />
          </Button>
        </div>
      );
    }
    
    return (
      <span 
        className={`font-mono text-xs ${canEdit ? 'cursor-pointer hover:bg-blue-50 px-1 rounded' : ''}`}
        onClick={() => canEdit && startEditing(entry.entry_id, field, value)}
        title={canEdit ? "Clic para editar" : ""}
      >
        {isCurrency ? formatCurrency(value) : formatNumber(value)}
      </span>
    );
  };

  // Calculate totals for the period
  const calculateTotals = () => {
    return periodEntries.reduce((acc, e) => ({
      baseSalary: acc.baseSalary + (e.base_salary || 0),
      bonuses: acc.bonuses + (e.bonuses || 0),
      commissions: acc.commissions + (e.commissions || 0),
      overtimeDay: acc.overtimeDay + (e.overtime_day_amount || 0),
      overtimeNight: acc.overtimeNight + (e.overtime_night_amount || 0),
      overtimeWeekend: acc.overtimeWeekend + (e.overtime_weekend_amount || 0),
      overtimeHoliday: acc.overtimeHoliday + (e.overtime_holiday_amount || 0),
      grossSalary: acc.grossSalary + (e.gross_salary || 0),
      sfsEmployee: acc.sfsEmployee + (e.sfs_employee || 0),
      afpEmployee: acc.afpEmployee + (e.afp_employee || 0),
      isr: acc.isr + (e.isr || 0),
      additionalDeductions: acc.additionalDeductions + (e.total_additional_deductions || 0),
      totalDeductions: acc.totalDeductions + (e.total_deductions || 0),
      netSalary: acc.netSalary + (e.net_salary || 0),
      sfsEmployer: acc.sfsEmployer + (e.sfs_employer || 0),
      afpEmployer: acc.afpEmployer + (e.afp_employer || 0),
      srlEmployer: acc.srlEmployer + (e.srl_employer || 0),
      infotepEmployer: acc.infotepEmployer + (e.infotep_employer || 0),
      totalEmployerContributions: acc.totalEmployerContributions + (e.total_employer_contributions || 0)
    }), {
      baseSalary: 0, bonuses: 0, commissions: 0, overtimeDay: 0, overtimeNight: 0,
      overtimeWeekend: 0, overtimeHoliday: 0, grossSalary: 0, sfsEmployee: 0,
      afpEmployee: 0, isr: 0, additionalDeductions: 0, totalDeductions: 0,
      netSalary: 0, sfsEmployer: 0, afpEmployer: 0, srlEmployer: 0,
      infotepEmployer: 0, totalEmployerContributions: 0
    });
  };

  // Dashboard stats
  const stats = {
    openPeriods: periods.filter(p => p.status === 'open').length,
    pendingPayrolls: periods.filter(p => ['calculated', 'approved'].includes(p.status)).length,
    approvedPayrolls: periods.filter(p => p.status === 'approved').length,
    totalPaid: periods.filter(p => p.status === 'paid').reduce((sum, p) => sum + (p.total_net || 0), 0)
  };

  const totals = calculateTotals();

  return (
    <DashboardLayout title="Nómina">
      <div className="space-y-6" data-testid="payroll-v2-page">
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Nómina de Pago</h1>
            <p className="text-slate-500">Gestión de pagos, períodos y cálculos salariales.</p>
          </div>
          <div className="flex gap-2">
            <Button onClick={fetchPeriods} variant="outline" size="sm">
              <RefreshCw className="w-4 h-4 mr-2" />
              Actualizar
            </Button>
            <Button onClick={() => setShowNewPeriod(true)} size="sm">
              <Plus className="w-4 h-4 mr-2" />
              Nuevo Período
            </Button>
          </div>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid grid-cols-5 w-full max-w-2xl">
            <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
            <TabsTrigger value="periodos">Períodos ({periods.length})</TabsTrigger>
            <TabsTrigger value="nomina">Hoja de Nómina</TabsTrigger>
            <TabsTrigger value="aprobacion">Aprobación</TabsTrigger>
            <TabsTrigger value="reportes">Reportes</TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
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

            {/* Recent Periods */}
            <Card>
              <CardHeader>
                <CardTitle>Períodos Recientes</CardTitle>
              </CardHeader>
              <CardContent>
                {periods.length === 0 ? (
                  <div className="text-center py-8 text-slate-500">
                    <Calendar className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                    <p>No hay períodos de nómina</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {periods.slice(0, 5).map(period => (
                      <div key={period.period_id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-slate-50">
                        <div>
                          <p className="font-medium">{period.description}</p>
                          <p className="text-sm text-slate-500">{period.employee_count} empleados</p>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="font-mono">{formatCurrency(period.total_net)}</span>
                          {getStatusBadge(period.status)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Períodos Tab */}
          <TabsContent value="periodos" className="space-y-4">
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
                    onClick={() => { setSelectedPeriod(period); setActiveTab('nomina'); }}
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
          </TabsContent>

          {/* Hoja de Nómina Tab - Excel-like format */}
          <TabsContent value="nomina" className="space-y-4">
            {!selectedPeriod ? (
              <Card className="py-12">
                <CardContent className="text-center">
                  <FileSpreadsheet className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                  <p className="text-slate-500">Seleccione un período para ver la hoja de nómina</p>
                  <Button variant="link" onClick={() => setActiveTab('periodos')}>
                    Ver períodos disponibles
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <>
                {/* Header with company info */}
                <Card className="bg-gradient-to-r from-slate-800 to-slate-700 text-white">
                  <CardContent className="p-6">
                    <div className="flex justify-between items-start">
                      <div>
                        <h2 className="text-2xl font-bold">{companyName}</h2>
                        <p className="text-slate-300 mt-1">NÓMINA DE PAGO</p>
                        <p className="text-sm text-slate-400 mt-2">
                          Período: {selectedPeriod.description}
                        </p>
                        <p className="text-sm text-slate-400">
                          {selectedPeriod.start_date} al {selectedPeriod.end_date}
                        </p>
                      </div>
                      <div className="text-right">
                        {getStatusBadge(selectedPeriod.status)}
                        <div className="mt-3 flex gap-2">
                          {selectedPeriod.status === 'open' && (
                            <>
                              <Button size="sm" variant="secondary" onClick={() => handleAddEmployees(selectedPeriod.period_id)}>
                                <Users className="w-4 h-4 mr-1" />
                                Agregar
                              </Button>
                              <Button size="sm" variant="secondary" onClick={() => handleCalculatePeriod(selectedPeriod.period_id)}>
                                <Calculator className="w-4 h-4 mr-1" />
                                Calcular
                              </Button>
                            </>
                          )}
                          {selectedPeriod.status === 'calculated' && (
                            <Button size="sm" variant="secondary" onClick={() => handleApprovePeriod(selectedPeriod.period_id)}>
                              <Check className="w-4 h-4 mr-1" />
                              Aprobar
                            </Button>
                          )}
                          {['calculated', 'approved'].includes(selectedPeriod.status) && (
                            <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700" onClick={() => openPayDialog(selectedPeriod)}>
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
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Excel-like Payroll Sheet */}
                {periodEntries.length === 0 ? (
                  <Card className="py-12">
                    <CardContent className="text-center">
                      <Users className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                      <p className="text-slate-500">No hay empleados en este período</p>
                      <Button variant="link" onClick={() => handleAddEmployees(selectedPeriod.period_id)}>
                        Agregar empleados activos
                      </Button>
                    </CardContent>
                  </Card>
                ) : (
                  <Card>
                    <CardContent className="p-0 overflow-x-auto">
                      <Table className="text-xs">
                        <TableHeader>
                          <TableRow className="bg-slate-100">
                            <TableHead className="font-bold text-center border-r" rowSpan={2}>NO.</TableHead>
                            <TableHead className="font-bold border-r min-w-[180px]" rowSpan={2}>NOMBRES EMPLEADOS</TableHead>
                            <TableHead className="font-bold text-center border-r min-w-[100px]" rowSpan={2}>CÉDULA</TableHead>
                            <TableHead className="font-bold border-r min-w-[120px]" rowSpan={2}>CARGO</TableHead>
                            <TableHead className="font-bold text-right border-r bg-blue-50" rowSpan={2}>SALARIO BRUTO</TableHead>
                            <TableHead className="font-bold text-center border-r bg-emerald-50" colSpan={3}>INGRESOS ADICIONALES</TableHead>
                            <TableHead className="font-bold text-right border-r bg-slate-200" rowSpan={2}>TOTAL INGRESOS</TableHead>
                            <TableHead className="font-bold text-center border-r bg-red-50" colSpan={4}>DEDUCCIONES EMPLEADO</TableHead>
                            <TableHead className="font-bold text-right border-r bg-red-100" rowSpan={2}>TOTAL DEDUCCIONES</TableHead>
                            <TableHead className="font-bold text-right bg-emerald-100" rowSpan={2}>NETO A PAGAR</TableHead>
                            {selectedPeriod.status !== 'paid' && (
                              <TableHead className="w-12" rowSpan={2}></TableHead>
                            )}
                          </TableRow>
                          <TableRow className="bg-slate-50">
                            <TableHead className="text-center text-[10px] border-r bg-emerald-50">Bonos</TableHead>
                            <TableHead className="text-center text-[10px] border-r bg-emerald-50">Comisiones</TableHead>
                            <TableHead className="text-center text-[10px] border-r bg-emerald-50">H. Extras</TableHead>
                            <TableHead className="text-center text-[10px] border-r bg-red-50">SFS 3.04%</TableHead>
                            <TableHead className="text-center text-[10px] border-r bg-red-50">AFP 2.87%</TableHead>
                            <TableHead className="text-center text-[10px] border-r bg-red-50">ISR</TableHead>
                            <TableHead className="text-center text-[10px] border-r bg-red-50">Otros</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {periodEntries.map((entry, index) => {
                            const totalOvertime = (entry.overtime_day_amount || 0) + 
                              (entry.overtime_night_amount || 0) + 
                              (entry.overtime_weekend_amount || 0) + 
                              (entry.overtime_holiday_amount || 0);
                            
                            return (
                              <TableRow key={entry.entry_id} className="hover:bg-slate-50">
                                <TableCell className="text-center border-r font-medium">{index + 1}</TableCell>
                                <TableCell className="border-r">
                                  <div>
                                    <p className="font-medium">{entry.employee_name}</p>
                                  </div>
                                </TableCell>
                                <TableCell className="text-center border-r font-mono text-[10px]">{entry.employee_document}</TableCell>
                                <TableCell className="border-r text-[10px]">{entry.position}</TableCell>
                                <TableCell className="text-right border-r bg-blue-50/50">
                                  {renderEditableCell(entry, 'base_salary', entry.base_salary)}
                                </TableCell>
                                <TableCell className="text-right border-r bg-emerald-50/50">
                                  {renderEditableCell(entry, 'bonuses', entry.bonuses)}
                                </TableCell>
                                <TableCell className="text-right border-r bg-emerald-50/50">
                                  {renderEditableCell(entry, 'commissions', entry.commissions)}
                                </TableCell>
                                <TableCell className="text-right border-r bg-emerald-50/50">
                                  <span className="font-mono text-xs text-emerald-600">
                                    {formatCurrency(totalOvertime)}
                                  </span>
                                </TableCell>
                                <TableCell className="text-right border-r bg-slate-100 font-bold">
                                  <span className="font-mono text-xs">
                                    {formatCurrency(entry.gross_salary)}
                                  </span>
                                </TableCell>
                                <TableCell className="text-right border-r bg-red-50/50">
                                  <span className="font-mono text-xs text-red-600">
                                    {formatCurrency(entry.sfs_employee)}
                                  </span>
                                </TableCell>
                                <TableCell className="text-right border-r bg-red-50/50">
                                  <span className="font-mono text-xs text-red-600">
                                    {formatCurrency(entry.afp_employee)}
                                  </span>
                                </TableCell>
                                <TableCell className="text-right border-r bg-red-50/50">
                                  <span className="font-mono text-xs text-red-600">
                                    {formatCurrency(entry.isr)}
                                  </span>
                                </TableCell>
                                <TableCell className="text-right border-r bg-red-50/50">
                                  <span className="font-mono text-xs text-red-600">
                                    {formatCurrency(entry.total_additional_deductions)}
                                  </span>
                                </TableCell>
                                <TableCell className="text-right border-r bg-red-100/50 font-bold">
                                  <span className="font-mono text-xs text-red-700">
                                    {formatCurrency(entry.total_deductions)}
                                  </span>
                                </TableCell>
                                <TableCell className="text-right bg-emerald-100/50 font-bold">
                                  <span className="font-mono text-xs text-emerald-700">
                                    {formatCurrency(entry.net_salary)}
                                  </span>
                                </TableCell>
                                {selectedPeriod.status !== 'paid' && (
                                  <TableCell>
                                    <Button 
                                      size="icon" 
                                      variant="ghost" 
                                      className="h-6 w-6 text-red-500"
                                      onClick={() => handleDeleteEntry(entry.entry_id, selectedPeriod.period_id)}
                                    >
                                      <Trash2 className="w-3 h-3" />
                                    </Button>
                                  </TableCell>
                                )}
                              </TableRow>
                            );
                          })}
                          {/* Totals Row */}
                          <TableRow className="bg-slate-200 font-bold">
                            <TableCell colSpan={4} className="text-right border-r">TOTALES:</TableCell>
                            <TableCell className="text-right border-r font-mono">{formatCurrency(totals.baseSalary)}</TableCell>
                            <TableCell className="text-right border-r font-mono">{formatCurrency(totals.bonuses)}</TableCell>
                            <TableCell className="text-right border-r font-mono">{formatCurrency(totals.commissions)}</TableCell>
                            <TableCell className="text-right border-r font-mono">{formatCurrency(totals.overtimeDay + totals.overtimeNight + totals.overtimeWeekend + totals.overtimeHoliday)}</TableCell>
                            <TableCell className="text-right border-r font-mono">{formatCurrency(totals.grossSalary)}</TableCell>
                            <TableCell className="text-right border-r font-mono text-red-600">{formatCurrency(totals.sfsEmployee)}</TableCell>
                            <TableCell className="text-right border-r font-mono text-red-600">{formatCurrency(totals.afpEmployee)}</TableCell>
                            <TableCell className="text-right border-r font-mono text-red-600">{formatCurrency(totals.isr)}</TableCell>
                            <TableCell className="text-right border-r font-mono text-red-600">{formatCurrency(totals.additionalDeductions)}</TableCell>
                            <TableCell className="text-right border-r font-mono text-red-700">{formatCurrency(totals.totalDeductions)}</TableCell>
                            <TableCell className="text-right font-mono text-emerald-700">{formatCurrency(totals.netSalary)}</TableCell>
                            {selectedPeriod.status !== 'paid' && <TableCell></TableCell>}
                          </TableRow>
                        </TableBody>
                      </Table>
                    </CardContent>
                  </Card>
                )}

                {/* Employer Contributions Summary */}
                {periodEntries.length > 0 && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm">Aportes del Empleador (TSS y otros)</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <Table className="text-xs">
                          <TableHeader>
                            <TableRow>
                              <TableHead>Concepto</TableHead>
                              <TableHead className="text-right">Porcentaje</TableHead>
                              <TableHead className="text-right">Valor</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            <TableRow>
                              <TableCell>SFS (Empleador)</TableCell>
                              <TableCell className="text-right font-mono">7.09%</TableCell>
                              <TableCell className="text-right font-mono">{formatCurrency(totals.sfsEmployer)}</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>AFP (Empleador)</TableCell>
                              <TableCell className="text-right font-mono">7.10%</TableCell>
                              <TableCell className="text-right font-mono">{formatCurrency(totals.afpEmployer)}</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>SRL</TableCell>
                              <TableCell className="text-right font-mono">1.00%</TableCell>
                              <TableCell className="text-right font-mono">{formatCurrency(totals.srlEmployer)}</TableCell>
                            </TableRow>
                            <TableRow>
                              <TableCell>INFOTEP</TableCell>
                              <TableCell className="text-right font-mono">1.00%</TableCell>
                              <TableCell className="text-right font-mono">{formatCurrency(totals.infotepEmployer)}</TableCell>
                            </TableRow>
                            <TableRow className="font-bold bg-slate-100">
                              <TableCell>TOTAL</TableCell>
                              <TableCell className="text-right font-mono">16.19%</TableCell>
                              <TableCell className="text-right font-mono">{formatCurrency(totals.totalEmployerContributions)}</TableCell>
                            </TableRow>
                          </TableBody>
                        </Table>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm">Resumen de la Nómina</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-2">
                        <div className="flex justify-between p-2 bg-slate-50 rounded">
                          <span>Total Ingresos Brutos:</span>
                          <span className="font-mono font-bold">{formatCurrency(totals.grossSalary)}</span>
                        </div>
                        <div className="flex justify-between p-2 bg-red-50 rounded">
                          <span>Total Deducciones Empleado:</span>
                          <span className="font-mono font-bold text-red-600">- {formatCurrency(totals.totalDeductions)}</span>
                        </div>
                        <div className="flex justify-between p-2 bg-emerald-100 rounded">
                          <span className="font-bold">Neto a Pagar:</span>
                          <span className="font-mono font-bold text-emerald-700">{formatCurrency(totals.netSalary)}</span>
                        </div>
                        <div className="flex justify-between p-2 bg-blue-50 rounded mt-4">
                          <span>Costo Total Empleador:</span>
                          <span className="font-mono font-bold text-blue-700">
                            {formatCurrency(totals.grossSalary + totals.totalEmployerContributions)}
                          </span>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                )}
              </>
            )}
          </TabsContent>

          {/* Aprobación Tab */}
          <TabsContent value="aprobacion" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Nóminas Pendientes de Aprobación</CardTitle>
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
                          <Button variant="outline" onClick={() => { setSelectedPeriod(period); setActiveTab('nomina'); }}>
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

            {/* Ready to Pay */}
            <Card>
              <CardHeader>
                <CardTitle className="text-emerald-700">Listos para Pagar</CardTitle>
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
                        <Button className="bg-emerald-600 hover:bg-emerald-700" onClick={() => openPayDialog(period)}>
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
                          <Button variant="outline" size="sm" onClick={() => { setSelectedPeriod(period); setActiveTab('nomina'); }}>
                            <FileSpreadsheet className="w-4 h-4 mr-1" />
                            Ver
                          </Button>
                          <Button variant="outline" size="sm">
                            <Download className="w-4 h-4 mr-1" />
                            Excel
                          </Button>
                          <Button variant="outline" size="sm">
                            <Printer className="w-4 h-4 mr-1" />
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

        {/* Pay Period Dialog - Select Bank Account */}
        <Dialog open={showPayDialog} onOpenChange={setShowPayDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Wallet className="w-5 h-5 text-emerald-600" />
                Pagar Nómina
              </DialogTitle>
              <DialogDescription>
                Seleccione la cuenta bancaria para realizar el pago de la nómina
              </DialogDescription>
            </DialogHeader>
            
            {selectedPeriod && (
              <div className="space-y-4">
                <div className="p-4 bg-slate-50 rounded-lg">
                  <p className="font-semibold">{selectedPeriod.description}</p>
                  <p className="text-sm text-slate-500 mt-1">
                    {selectedPeriod.employee_count} empleados
                  </p>
                  <div className="mt-3 p-3 bg-emerald-100 rounded-lg">
                    <p className="text-sm text-emerald-700">Total a Pagar (Neto)</p>
                    <p className="text-2xl font-bold text-emerald-800">
                      {formatCurrency(selectedPeriod.total_net)}
                    </p>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Cuenta Bancaria para el Pago</Label>
                  <Select value={selectedBankAccount} onValueChange={setSelectedBankAccount}>
                    <SelectTrigger>
                      <SelectValue placeholder="Seleccione cuenta bancaria" />
                    </SelectTrigger>
                    <SelectContent>
                      {bankAccounts.map(acc => (
                        <SelectItem key={acc.code} value={acc.code}>
                          {acc.code} - {acc.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-slate-500">
                    Esta cuenta se acreditará en el asiento contable generado
                  </p>
                </div>

                <div className="p-3 bg-blue-50 rounded-lg">
                  <p className="text-sm text-blue-700">
                    <strong>Nota:</strong> Al confirmar, se generará automáticamente un asiento contable 
                    con el débito a gastos de nómina y crédito a las cuentas de pasivo y banco seleccionado.
                  </p>
                </div>
              </div>
            )}

            <DialogFooter>
              <Button variant="outline" onClick={() => setShowPayDialog(false)}>Cancelar</Button>
              <Button 
                className="bg-emerald-600 hover:bg-emerald-700" 
                onClick={handlePayPeriod}
                disabled={!selectedBankAccount}
              >
                <CreditCard className="w-4 h-4 mr-2" />
                Confirmar Pago
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
