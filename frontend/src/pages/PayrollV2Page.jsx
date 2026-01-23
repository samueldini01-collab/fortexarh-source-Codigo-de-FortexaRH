import { useState, useEffect } from "react";
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
  CheckCircle,
  AlertCircle,
  ChevronRight,
  Save,
  X,
  Printer,
  FileSpreadsheet,
  Wallet,
  PlusCircle,
  MinusCircle,
  Gift,
  Briefcase
} from "lucide-react";
import { toast } from "sonner";

const months = [
  { value: 1, label: "Enero" }, { value: 2, label: "Febrero" }, { value: 3, label: "Marzo" },
  { value: 4, label: "Abril" }, { value: 5, label: "Mayo" }, { value: 6, label: "Junio" },
  { value: 7, label: "Julio" }, { value: 8, label: "Agosto" }, { value: 9, label: "Septiembre" },
  { value: 10, label: "Octubre" }, { value: 11, label: "Noviembre" }, { value: 12, label: "Diciembre" }
];

const periodTypes = [
  { value: "quincenal_1", label: "Quincenal (1-15)" },
  { value: "quincenal_2", label: "Quincenal (16-30/31)" },
  { value: "mensual", label: "Mensual" }
];

const payrollTypes = [
  { value: "REG", label: "Regular", icon: Calendar, color: "blue" },
  { value: "TEMP", label: "Temporal", icon: Briefcase, color: "orange" },
  { value: "BONO", label: "Bono/Extraordinaria", icon: Gift, color: "purple" },
  { value: "REG13", label: "Regalía Pascual", icon: Gift, color: "emerald" },
  { value: "VAC", label: "Vacaciones", icon: Calendar, color: "cyan" },
  { value: "LIQ", label: "Liquidación", icon: FileText, color: "red" },
];

const departments = ["Administración", "Ventas", "Marketing", "TI", "Recursos Humanos", "Finanzas", "Operaciones", "Legal", "Producción", "Logística"];

export default function PayrollV2Page() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [periods, setPeriods] = useState([]);
  const [selectedPeriod, setSelectedPeriod] = useState(null);
  const [periodEntries, setPeriodEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showNewPeriod, setShowNewPeriod] = useState(false);
  const [showPayDialog, setShowPayDialog] = useState(false);
  const [showNoveltyDialog, setShowNoveltyDialog] = useState(false);
  const [selectedEntry, setSelectedEntry] = useState(null);
  const [bankAccounts, setBankAccounts] = useState([]);
  const [selectedBankAccount, setSelectedBankAccount] = useState("");
  const [noveltyTypes, setNoveltyTypes] = useState({ income: [], deduction: [] });
  const [companyName, setCompanyName] = useState("NOMBRE DE LA EMPRESA");
  
  // Bank file generation states
  const [selectedPaymentBank, setSelectedPaymentBank] = useState("");
  const [generateBankFile, setGenerateBankFile] = useState(true);
  const [paymentBanks] = useState([
    { id: "popular", name: "Banco Popular Dominicano", format: "TXT" },
    { id: "bhd", name: "BHD León", format: "TXT" },
    { id: "banreservas", name: "Banreservas", format: "CSV" }
  ]);
  
  // Inline editing states
  const [editingCell, setEditingCell] = useState(null);
  const [editValue, setEditValue] = useState("");
  
  // Quick filter states
  const [quickFilter, setQuickFilter] = useState(null);
  const [departmentFilter, setDepartmentFilter] = useState("all");
  
  // Form states
  const [newPeriodForm, setNewPeriodForm] = useState({
    period_type: "quincenal_1",
    payroll_type: "REG",
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1,
    start_date: "",
    end_date: "",
    description: "",
    department_filter: "all"
  });

  // Novelty form
  const [noveltyForm, setNoveltyForm] = useState({
    novelty_type: "income",
    code: "",
    name: "",
    description: "",
    amount: "",
    is_percentage: false
  });

  const { getAuthHeaders, user } = useAuth();

  useEffect(() => {
    fetchPeriods();
    fetchBankAccounts();
    fetchNoveltyTypes();
    if (user?.company_name) setCompanyName(user.company_name);
  }, []);

  useEffect(() => {
    if (selectedPeriod) fetchPeriodDetails(selectedPeriod.period_id);
  }, [selectedPeriod]);

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
      const response = await axios.get(`${API}/payroll-v2/periods`, { headers: getAuthHeaders(), withCredentials: true });
      setPeriods(response.data);
    } catch (error) {
      toast.error("Error al cargar períodos");
    } finally {
      setLoading(false);
    }
  };

  const fetchPeriodDetails = async (periodId) => {
    try {
      const response = await axios.get(`${API}/payroll-v2/periods/${periodId}`, { headers: getAuthHeaders(), withCredentials: true });
      setPeriodEntries(response.data.entries || []);
    } catch (error) {
      console.error("Error:", error);
    }
  };

  const fetchBankAccounts = async () => {
    try {
      const response = await axios.get(`${API}/accounting/accounts`, { headers: getAuthHeaders(), withCredentials: true });
      const banks = response.data.filter(acc => acc.code.startsWith('1101') || (acc.account_type === 'asset' && acc.name.toLowerCase().includes('banco')));
      setBankAccounts(banks);
      if (banks.length > 0) setSelectedBankAccount(banks[0].code);
    } catch (error) {
      console.error("Error:", error);
    }
  };

  const fetchNoveltyTypes = async () => {
    try {
      const response = await axios.get(`${API}/payroll-v2/novelty-types`, { headers: getAuthHeaders(), withCredentials: true });
      setNoveltyTypes(response.data);
    } catch (error) {
      console.error("Error:", error);
    }
  };

  const handleCreatePeriod = async () => {
    try {
      const dataToSend = {
        ...newPeriodForm,
        department_filter: newPeriodForm.department_filter === "all" ? null : newPeriodForm.department_filter
      };
      await axios.post(`${API}/payroll-v2/periods`, dataToSend, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Período creado correctamente");
      setShowNewPeriod(false);
      fetchPeriods();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al crear período");
    }
  };

  const handleAddEmployees = async (periodId) => {
    try {
      const response = await axios.post(`${API}/payroll-v2/periods/${periodId}/add-employees`, {}, { headers: getAuthHeaders(), withCredentials: true });
      toast.success(response.data.message);
      fetchPeriodDetails(periodId);
      fetchPeriods();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error");
    }
  };

  const handleCalculatePeriod = async (periodId) => {
    try {
      await axios.post(`${API}/payroll-v2/periods/${periodId}/calculate`, {}, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Nóminas calculadas");
      fetchPeriodDetails(periodId);
      fetchPeriods();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error");
    }
  };

  const handleApprovePeriod = async (periodId) => {
    try {
      await axios.post(`${API}/payroll-v2/periods/${periodId}/approve`, {}, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Período aprobado");
      fetchPeriods();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error");
    }
  };

  const openPayDialog = (period) => { setSelectedPeriod(period); setShowPayDialog(true); };

  const handlePayPeriod = async () => {
    if (!selectedPeriod) return;
    try {
      const response = await axios.post(`${API}/payroll-v2/periods/${selectedPeriod.period_id}/pay`, 
        { bank_account_code: selectedBankAccount },
        { headers: getAuthHeaders(), withCredentials: true }
      );
      toast.success(`Nómina pagada. Asiento #${response.data.entry_number} generado.`);
      
      // Generate and download bank file if selected
      if (generateBankFile && selectedPaymentBank) {
        try {
          const bankResponse = await axios.get(
            `${API}/bank-files/generate/${selectedPeriod.period_id}/${selectedPaymentBank}`,
            { headers: getAuthHeaders(), withCredentials: true, responseType: 'blob' }
          );
          
          const bank = paymentBanks.find(b => b.id === selectedPaymentBank);
          const ext = bank?.format === 'CSV' ? 'csv' : 'txt';
          const blob = new Blob([bankResponse.data]);
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = `nomina_${selectedPaymentBank}_${selectedPeriod.period_id}.${ext}`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          
          toast.success(`Archivo bancario ${bank?.name} descargado`);
        } catch (bankError) {
          toast.error("Error al generar archivo bancario");
        }
      }
      
      setShowPayDialog(false);
      setSelectedPaymentBank("");
      fetchPeriods();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error");
    }
  };

  const handleDeletePeriod = async (periodId) => {
    if (!confirm("¿Eliminar este período y su asiento asociado?")) return;
    try {
      await axios.delete(`${API}/payroll-v2/periods/${periodId}`, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Período eliminado");
      setSelectedPeriod(null);
      fetchPeriods();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error");
    }
  };

  // Inline editing
  const startEditing = (entryId, field, currentValue) => {
    if (selectedPeriod?.status === 'paid') return;
    setEditingCell({ entryId, field });
    setEditValue(String(currentValue || 0));
  };

  const cancelEditing = () => { setEditingCell(null); setEditValue(""); };

  const saveInlineEdit = async () => {
    if (!editingCell) return;
    const entry = periodEntries.find(e => e.entry_id === editingCell.entryId);
    if (!entry) return;

    try {
      const updateData = {
        period_id: entry.period_id, employee_id: entry.employee_id,
        base_salary: entry.base_salary, overtime_day_hours: entry.overtime_day_hours || 0,
        overtime_night_hours: entry.overtime_night_hours || 0, overtime_weekend_hours: entry.overtime_weekend_hours || 0,
        overtime_holiday_hours: entry.overtime_holiday_hours || 0, bonuses: entry.bonuses || 0,
        commissions: entry.commissions || 0, additional_deductions: entry.additional_deductions || []
      };
      const numValue = parseFloat(editValue) || 0;
      updateData[editingCell.field] = numValue;

      await axios.put(`${API}/payroll-v2/entries/${entry.entry_id}`, updateData, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Actualizado");
      fetchPeriodDetails(entry.period_id);
      fetchPeriods();
    } catch (error) {
      toast.error("Error");
    } finally {
      cancelEditing();
    }
  };

  const handleDeleteEntry = async (entryId, periodId) => {
    if (!confirm("¿Eliminar esta entrada?")) return;
    try {
      await axios.delete(`${API}/payroll-v2/entries/${entryId}`, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Eliminado");
      fetchPeriodDetails(periodId);
      fetchPeriods();
    } catch (error) {
      toast.error("Error");
    }
  };

  // Novelty handlers
  const openNoveltyDialog = (entry) => {
    setSelectedEntry(entry);
    setNoveltyForm({ novelty_type: "income", code: "", name: "", description: "", amount: "", is_percentage: false });
    setShowNoveltyDialog(true);
  };

  const handleAddNovelty = async () => {
    if (!selectedEntry || !noveltyForm.code || !noveltyForm.amount) {
      toast.error("Complete todos los campos requeridos");
      return;
    }

    try {
      await axios.post(`${API}/payroll-v2/entries/${selectedEntry.entry_id}/novelties`, {
        entry_id: selectedEntry.entry_id,
        ...noveltyForm,
        amount: parseFloat(noveltyForm.amount) || 0
      }, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Novedad agregada");
      setShowNoveltyDialog(false);
      fetchPeriodDetails(selectedEntry.period_id);
      fetchPeriods();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error");
    }
  };

  const handleDeleteNovelty = async (entryId, noveltyId, periodId) => {
    try {
      await axios.delete(`${API}/payroll-v2/entries/${entryId}/novelties/${noveltyId}`, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Novedad eliminada");
      fetchPeriodDetails(periodId);
      fetchPeriods();
    } catch (error) {
      toast.error("Error");
    }
  };

  // Export handlers
  const handleExportExcel = async (periodId) => {
    try {
      const response = await axios.get(`${API}/payroll-v2/periods/${periodId}/export/excel`, { headers: getAuthHeaders(), withCredentials: true });
      const data = response.data;
      
      // Create CSV content
      let csv = `${companyName}\n`;
      csv += `Nómina: ${data.period.description}\n`;
      csv += `Período: ${data.period.start_date} - ${data.period.end_date}\n\n`;
      csv += data.columns.join(",") + "\n";
      
      data.rows.forEach(row => {
        csv += `${row.no},"${row.cedula}","${row.nombre}","${row.cargo}","${row.departamento}",`;
        csv += `${row.salario_base},${row.comisiones},${row.bonos},${row.he_diurnas},${row.he_nocturnas},`;
        csv += `${row.he_finsemana},${row.he_feriados},${row.otros_ingresos},${row.total_ingresos},`;
        csv += `${row.sfs},${row.afp},${row.isr},${row.otros_descuentos},${row.total_descuentos},${row.neto}\n`;
      });
      
      csv += `\nTOTALES,,,,`;
      csv += `${data.totals.salario_base},${data.totals.comisiones},${data.totals.bonos},0,0,0,0,0,`;
      csv += `${data.totals.total_ingresos},${data.totals.sfs},${data.totals.afp},${data.totals.isr},0,`;
      csv += `${data.totals.total_descuentos},${data.totals.neto}\n`;

      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `nomina_${data.period.period_id}.csv`;
      link.click();
      toast.success("Excel exportado");
    } catch (error) {
      toast.error("Error al exportar");
    }
  };

  // Download TSS Autodeterminación Excel file
  const handleDownloadTSSAutodeterminacion = async (periodId) => {
    try {
      const response = await axios.get(`${API}/payroll-v2/periods/${periodId}/export/tss-autodeterminacion`, {
        headers: getAuthHeaders(),
        withCredentials: true,
        responseType: 'blob'
      });
      const blob = new Blob([response.data], { type: 'application/vnd.ms-excel' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `TSS_Autodeterminacion.xls`;
      link.click();
      toast.success("TSS Autodeterminación descargado");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al descargar TSS Autodeterminación");
    }
  };

  // Download TSS Novedades Excel file
  const handleDownloadTSSNovedades = async (periodId) => {
    try {
      const response = await axios.get(`${API}/payroll-v2/periods/${periodId}/export/tss-novedades`, {
        headers: getAuthHeaders(),
        withCredentials: true,
        responseType: 'blob'
      });
      const blob = new Blob([response.data], { type: 'application/vnd.ms-excel' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `TSS_Novedades.xls`;
      link.click();
      toast.success("TSS Novedades descargado");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al descargar TSS Novedades");
    }
  };

  // Download IR-3 Excel file
  const handleDownloadIR3 = async (periodId) => {
    try {
      const response = await axios.get(`${API}/payroll-v2/periods/${periodId}/export/ir3`, {
        headers: getAuthHeaders(),
        withCredentials: true,
        responseType: 'blob'
      });
      const blob = new Blob([response.data], { type: 'application/vnd.ms-excel' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `IR3_Retenciones.xls`;
      link.click();
      toast.success("IR-3 descargado");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al descargar IR-3");
    }
  };

  // Download IR-17 Excel file
  const handleDownloadIR17 = async (periodId) => {
    try {
      const response = await axios.get(`${API}/payroll-v2/periods/${periodId}/export/ir17`, {
        headers: getAuthHeaders(),
        withCredentials: true,
        responseType: 'blob'
      });
      const blob = new Blob([response.data], { type: 'application/vnd.ms-excel' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `IR17_Declaracion.xls`;
      link.click();
      toast.success("IR-17 descargado");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al descargar IR-17");
    }
  };

  // Legacy TSS export (JSON/CSV)
  const handleExportTSS = async (periodId) => {
    try {
      const response = await axios.get(`${API}/payroll-v2/periods/${periodId}/export/tss`, { headers: getAuthHeaders(), withCredentials: true });
      const data = response.data;
      
      // Create TSS format file
      let tss = `RNC/Cédula,${data.header.rnc_cedula}\n`;
      tss += `Período,${data.header.periodo}\n`;
      tss += `Versión,${data.header.version}\n`;
      tss += `Empleados,${data.header.num_empleados}\n\n`;
      tss += `Clave,Tipo Doc,Número,Nombres,Primer Apellido,Segundo Apellido,Sexo,Salario Cotizable,ISR\n`;
      
      data.employees.forEach(emp => {
        tss += `${emp.clave_nomina},${emp.tipo_doc},${emp.numero_doc},${emp.nombres},${emp.primer_apellido},`;
        tss += `${emp.segundo_apellido},${emp.sexo},${emp.salario_cotizable_sdss},${emp.salario_isr}\n`;
      });

      const blob = new Blob([tss], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `tss_autodeterminacion_${data.header.periodo}.csv`;
      link.click();
      toast.success("TSS exportado");
    } catch (error) {
      toast.error("Error al exportar TSS");
    }
  };

  const formatCurrency = (value) => new Intl.NumberFormat('es-DO', { style: 'currency', currency: 'DOP', minimumFractionDigits: 2 }).format(value || 0);
  const formatNumber = (value) => new Intl.NumberFormat('es-DO', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(value || 0);

  const getStatusBadge = (status) => {
    const badges = {
      'open': <Badge variant="outline" className="border-blue-500 text-blue-600">Abierto</Badge>,
      'calculated': <Badge className="bg-amber-100 text-amber-700">Calculado</Badge>,
      'approved': <Badge className="bg-emerald-100 text-emerald-700">Aprobado</Badge>,
      'paid': <Badge className="bg-purple-100 text-purple-700">Pagado</Badge>,
    };
    return badges[status] || <Badge variant="secondary">{status}</Badge>;
  };

  const getPayrollTypeBadge = (type) => {
    const pt = payrollTypes.find(p => p.value === type);
    if (!pt) return null;
    return <Badge className={`bg-${pt.color}-100 text-${pt.color}-700`}>{pt.label}</Badge>;
  };

  // Render editable cell
  const renderEditableCell = (entry, field, value, isCurrency = true) => {
    const isEditing = editingCell?.entryId === entry.entry_id && editingCell?.field === field;
    const canEdit = selectedPeriod?.status !== 'paid';
    
    if (isEditing) {
      return (
        <div className="flex items-center gap-1">
          <Input type="number" step="0.01" className="w-20 h-6 text-right text-xs" value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') saveInlineEdit(); if (e.key === 'Escape') cancelEditing(); }}
            autoFocus
          />
          <Button size="icon" variant="ghost" className="h-5 w-5" onClick={saveInlineEdit}><Check className="w-3 h-3 text-emerald-600" /></Button>
          <Button size="icon" variant="ghost" className="h-5 w-5" onClick={cancelEditing}><X className="w-3 h-3 text-red-500" /></Button>
        </div>
      );
    }
    return (
      <span className={`font-mono text-[10px] ${canEdit ? 'cursor-pointer hover:bg-blue-50 px-1 rounded' : ''}`}
        onClick={() => canEdit && startEditing(entry.entry_id, field, value)} title={canEdit ? "Clic para editar" : ""}>
        {isCurrency ? formatNumber(value) : value}
      </span>
    );
  };

  // Calculate totals
  const totals = periodEntries.reduce((acc, e) => ({
    baseSalary: acc.baseSalary + (e.base_salary || 0),
    bonuses: acc.bonuses + (e.bonuses || 0),
    commissions: acc.commissions + (e.commissions || 0),
    overtimeDay: acc.overtimeDay + (e.overtime_day_amount || 0),
    overtimeNight: acc.overtimeNight + (e.overtime_night_amount || 0),
    overtimeWeekend: acc.overtimeWeekend + (e.overtime_weekend_amount || 0),
    overtimeHoliday: acc.overtimeHoliday + (e.overtime_holiday_amount || 0),
    incomeNovelties: acc.incomeNovelties + (e.total_income_novelties || 0),
    grossSalary: acc.grossSalary + (e.gross_salary || 0),
    sfsEmployee: acc.sfsEmployee + (e.sfs_employee || 0),
    afpEmployee: acc.afpEmployee + (e.afp_employee || 0),
    isr: acc.isr + (e.isr || 0),
    deductionNovelties: acc.deductionNovelties + (e.total_deduction_novelties || 0),
    additionalDeductions: acc.additionalDeductions + (e.total_additional_deductions || 0),
    totalDeductions: acc.totalDeductions + (e.total_deductions || 0),
    netSalary: acc.netSalary + (e.net_salary || 0),
  }), { baseSalary: 0, bonuses: 0, commissions: 0, overtimeDay: 0, overtimeNight: 0, overtimeWeekend: 0, overtimeHoliday: 0, incomeNovelties: 0, grossSalary: 0, sfsEmployee: 0, afpEmployee: 0, isr: 0, deductionNovelties: 0, additionalDeductions: 0, totalDeductions: 0, netSalary: 0 });

  const stats = {
    openPeriods: periods.filter(p => p.status === 'open').length,
    pendingPayrolls: periods.filter(p => ['calculated', 'approved'].includes(p.status)).length,
    totalPaid: periods.filter(p => p.status === 'paid').reduce((sum, p) => sum + (p.total_net || 0), 0)
  };

  return (
    <DashboardLayout title="Nómina">
      <div className="space-y-6" data-testid="payroll-v2-page">
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Nómina de Pago</h1>
            <p className="text-slate-500">Procesa nóminas por tipo, período o grupos</p>
          </div>
          <div className="flex gap-2">
            <Button onClick={fetchPeriods} variant="outline" size="sm"><RefreshCw className="w-4 h-4 mr-2" />Actualizar</Button>
            <Button onClick={() => setShowNewPeriod(true)} size="sm"><Plus className="w-4 h-4 mr-2" />Nueva Nómina</Button>
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
              <Card 
                className={`border-l-4 border-l-blue-500 cursor-pointer transition-all hover:shadow-md ${quickFilter === 'open' ? 'ring-2 ring-blue-400' : ''}`}
                onClick={() => setQuickFilter(quickFilter === 'open' ? null : 'open')}
              >
                <CardContent className="p-4">
                  <p className="text-sm text-slate-500">Períodos Abiertos</p>
                  <p className="text-2xl font-bold text-blue-600">{stats.openPeriods}</p>
                </CardContent>
              </Card>
              <Card 
                className={`border-l-4 border-l-orange-500 cursor-pointer transition-all hover:shadow-md ${quickFilter === 'pending' ? 'ring-2 ring-orange-400' : ''}`}
                onClick={() => setQuickFilter(quickFilter === 'pending' ? null : 'pending')}
              >
                <CardContent className="p-4">
                  <p className="text-sm text-slate-500">Nóminas Pendientes</p>
                  <p className="text-2xl font-bold text-orange-600">{stats.pendingPayrolls}</p>
                </CardContent>
              </Card>
              <Card 
                className={`border-l-4 border-l-purple-500 cursor-pointer transition-all hover:shadow-md ${quickFilter === 'paid' ? 'ring-2 ring-purple-400' : ''}`}
                onClick={() => setQuickFilter(quickFilter === 'paid' ? null : 'paid')}
              >
                <CardContent className="p-4">
                  <p className="text-sm text-slate-500">Total Pagado</p>
                  <p className="text-xl font-bold text-purple-600">{formatCurrency(stats.totalPaid)}</p>
                </CardContent>
              </Card>
              <Card className="border-l-4 border-l-emerald-500">
                <CardContent className="p-4">
                  <p className="text-sm text-slate-500">Tipos de Nómina</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {payrollTypes.slice(0, 3).map(pt => (
                      <Badge key={pt.value} variant="outline" className="text-[10px]">{pt.label}</Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
            
            {/* Filter indicator for Dashboard */}
            {quickFilter && (
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="px-3 py-1">
                  Filtro: {quickFilter === 'open' ? 'Períodos Abiertos' : quickFilter === 'pending' ? 'Pendientes' : 'Pagados'}
                  <button onClick={() => setQuickFilter(null)} className="ml-2 hover:text-red-500">×</button>
                </Badge>
              </div>
            )}
          </TabsContent>

          {/* Períodos Tab */}
          <TabsContent value="periodos" className="space-y-4">
            {/* Filter controls */}
            <div className="flex flex-wrap items-center gap-4">
              <Select value={departmentFilter} onValueChange={setDepartmentFilter}>
                <SelectTrigger className="w-52">
                  <SelectValue placeholder="Todos los departamentos" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos los departamentos</SelectItem>
                  {departments.map(dept => (
                    <SelectItem key={dept} value={dept}>{dept}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              
              {quickFilter && (
                <Badge variant="outline" className="px-3 py-1">
                  Filtro: {quickFilter === 'open' ? 'Abiertos' : quickFilter === 'pending' ? 'Pendientes' : 'Pagados'}
                  <button onClick={() => setQuickFilter(null)} className="ml-2 hover:text-red-500">×</button>
                </Badge>
              )}
            </div>
            
            {periods.length === 0 ? (
              <Card className="py-12"><CardContent className="text-center">
                <Calendar className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                <p className="text-slate-500 mb-4">No hay períodos de nómina</p>
                <Button onClick={() => setShowNewPeriod(true)}>Crear Primera Nómina</Button>
              </CardContent></Card>
            ) : (
              <div className="space-y-3">
                {periods
                  .filter(period => {
                    if (quickFilter === 'open') return period.status === 'open';
                    if (quickFilter === 'pending') return ['calculated', 'approved'].includes(period.status);
                    if (quickFilter === 'paid') return period.status === 'paid';
                    return true;
                  })
                  .map(period => (
                  <Card key={period.period_id} className={`cursor-pointer transition-all ${selectedPeriod?.period_id === period.period_id ? 'ring-2 ring-blue-500' : 'hover:shadow-md'}`}
                    onClick={() => { setSelectedPeriod(period); setActiveTab('nomina'); }}>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                            <Calendar className="w-6 h-6 text-blue-600" />
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <h4 className="font-semibold">{period.description}</h4>
                              {getPayrollTypeBadge(period.payroll_type)}
                            </div>
                            <p className="text-sm text-slate-500">{period.start_date} - {period.end_date} • {period.employee_count} empleados</p>
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

          {/* Hoja de Nómina Tab */}
          <TabsContent value="nomina" className="space-y-4">
            {!selectedPeriod ? (
              <Card className="py-12"><CardContent className="text-center">
                <FileSpreadsheet className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                <p className="text-slate-500">Seleccione un período</p>
                <Button variant="link" onClick={() => setActiveTab('periodos')}>Ver períodos</Button>
              </CardContent></Card>
            ) : (
              <>
                {/* Header */}
                <Card className="bg-gradient-to-r from-slate-800 to-slate-700 text-white">
                  <CardContent className="p-6">
                    <div className="flex justify-between items-start">
                      <div>
                        <h2 className="text-2xl font-bold">{companyName}</h2>
                        <div className="text-slate-300 mt-1 flex items-center gap-2">NÓMINA DE PAGO {getPayrollTypeBadge(selectedPeriod.payroll_type)}</div>
                        <p className="text-sm text-slate-400 mt-2">{selectedPeriod.description} • {selectedPeriod.start_date} al {selectedPeriod.end_date}</p>
                      </div>
                      <div className="text-right">
                        {getStatusBadge(selectedPeriod.status)}
                        <div className="mt-3 flex gap-2 flex-wrap justify-end">
                          {selectedPeriod.status === 'open' && (
                            <>
                              <Button size="sm" variant="secondary" onClick={() => handleAddEmployees(selectedPeriod.period_id)}><Users className="w-4 h-4 mr-1" />Agregar</Button>
                              <Button size="sm" variant="secondary" onClick={() => handleCalculatePeriod(selectedPeriod.period_id)}><Calculator className="w-4 h-4 mr-1" />Calcular</Button>
                            </>
                          )}
                          {selectedPeriod.status === 'calculated' && (
                            <Button size="sm" variant="secondary" onClick={() => handleApprovePeriod(selectedPeriod.period_id)}><Check className="w-4 h-4 mr-1" />Aprobar</Button>
                          )}
                          {['calculated', 'approved'].includes(selectedPeriod.status) && (
                            <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700" onClick={() => openPayDialog(selectedPeriod)}><CreditCard className="w-4 h-4 mr-1" />Pagar</Button>
                          )}
                          <Button size="sm" variant="secondary" onClick={() => handleExportExcel(selectedPeriod.period_id)}><Download className="w-4 h-4 mr-1" />Excel</Button>
                          {selectedPeriod.status !== 'paid' && (
                            <Button size="sm" variant="destructive" onClick={() => handleDeletePeriod(selectedPeriod.period_id)}><Trash2 className="w-4 h-4" /></Button>
                          )}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Payroll Sheet */}
                {periodEntries.length === 0 ? (
                  <Card className="py-12"><CardContent className="text-center">
                    <Users className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                    <p className="text-slate-500">No hay empleados</p>
                    <Button variant="link" onClick={() => handleAddEmployees(selectedPeriod.period_id)}>Agregar empleados</Button>
                  </CardContent></Card>
                ) : (
                  <Card>
                    <CardContent className="p-0 overflow-x-auto">
                      <Table className="text-[10px]">
                        <TableHeader>
                          <TableRow className="bg-slate-100">
                            <TableHead className="font-bold text-center border-r w-8">NO.</TableHead>
                            <TableHead className="font-bold border-r min-w-[150px]">EMPLEADO</TableHead>
                            <TableHead className="font-bold text-center border-r w-24">CÉDULA</TableHead>
                            <TableHead className="font-bold text-right border-r bg-blue-50 w-24">SALARIO</TableHead>
                            <TableHead className="font-bold text-right border-r bg-emerald-50 w-20">COMIS.</TableHead>
                            <TableHead className="font-bold text-right border-r bg-emerald-50 w-20">BONOS</TableHead>
                            <TableHead className="font-bold text-right border-r bg-emerald-50 w-20">H.EXTRAS</TableHead>
                            <TableHead className="font-bold text-right border-r bg-amber-50 w-20">NOVEDADES+</TableHead>
                            <TableHead className="font-bold text-right border-r bg-slate-200 w-24">BRUTO</TableHead>
                            <TableHead className="font-bold text-right border-r bg-red-50 w-20">SFS</TableHead>
                            <TableHead className="font-bold text-right border-r bg-red-50 w-20">AFP</TableHead>
                            <TableHead className="font-bold text-right border-r bg-red-50 w-20">ISR</TableHead>
                            <TableHead className="font-bold text-right border-r bg-orange-50 w-20">NOVEDADES-</TableHead>
                            <TableHead className="font-bold text-right border-r bg-red-100 w-24">DEDUCCIONES</TableHead>
                            <TableHead className="font-bold text-right bg-emerald-100 w-24">NETO</TableHead>
                            {selectedPeriod.status !== 'paid' && <TableHead className="w-16"></TableHead>}
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {periodEntries.map((entry, index) => {
                            const totalOvertime = (entry.overtime_day_amount || 0) + (entry.overtime_night_amount || 0) + 
                              (entry.overtime_weekend_amount || 0) + (entry.overtime_holiday_amount || 0);
                            const novelties = entry.novelties || [];
                            
                            return (
                              <TableRow key={entry.entry_id} className="hover:bg-slate-50">
                                <TableCell className="text-center border-r font-medium">{index + 1}</TableCell>
                                <TableCell className="border-r">
                                  <div><p className="font-medium text-[11px]">{entry.employee_name}</p>
                                    <p className="text-slate-500">{entry.position}</p>
                                    {novelties.length > 0 && (
                                      <div className="flex gap-1 mt-1 flex-wrap">
                                        {novelties.map(n => (
                                          <Badge key={n.novelty_id} variant="outline" className={`text-[8px] ${n.novelty_type === 'income' ? 'border-emerald-300 text-emerald-600' : 'border-red-300 text-red-600'}`}>
                                            {n.code}: {formatNumber(n.amount)}
                                            {selectedPeriod.status !== 'paid' && (
                                              <X className="w-2 h-2 ml-1 cursor-pointer" onClick={(e) => { e.stopPropagation(); handleDeleteNovelty(entry.entry_id, n.novelty_id, selectedPeriod.period_id); }} />
                                            )}
                                          </Badge>
                                        ))}
                                      </div>
                                    )}
                                  </div>
                                </TableCell>
                                <TableCell className="text-center border-r font-mono">{entry.employee_document}</TableCell>
                                <TableCell className="text-right border-r bg-blue-50/50">{renderEditableCell(entry, 'base_salary', entry.base_salary)}</TableCell>
                                <TableCell className="text-right border-r bg-emerald-50/50">{renderEditableCell(entry, 'commissions', entry.commissions)}</TableCell>
                                <TableCell className="text-right border-r bg-emerald-50/50">{renderEditableCell(entry, 'bonuses', entry.bonuses)}</TableCell>
                                <TableCell className="text-right border-r bg-emerald-50/50 text-emerald-600">{formatNumber(totalOvertime)}</TableCell>
                                <TableCell className="text-right border-r bg-amber-50/50 text-amber-600">{formatNumber(entry.total_income_novelties || 0)}</TableCell>
                                <TableCell className="text-right border-r bg-slate-100 font-bold">{formatNumber(entry.gross_salary)}</TableCell>
                                <TableCell className="text-right border-r bg-red-50/50 text-red-600">{formatNumber(entry.sfs_employee)}</TableCell>
                                <TableCell className="text-right border-r bg-red-50/50 text-red-600">{formatNumber(entry.afp_employee)}</TableCell>
                                <TableCell className="text-right border-r bg-red-50/50 text-red-600">{formatNumber(entry.isr)}</TableCell>
                                <TableCell className="text-right border-r bg-orange-50/50 text-orange-600">{formatNumber(entry.total_deduction_novelties || 0)}</TableCell>
                                <TableCell className="text-right border-r bg-red-100/50 font-bold text-red-700">{formatNumber(entry.total_deductions)}</TableCell>
                                <TableCell className="text-right bg-emerald-100/50 font-bold text-emerald-700">{formatNumber(entry.net_salary)}</TableCell>
                                {selectedPeriod.status !== 'paid' && (
                                  <TableCell>
                                    <div className="flex gap-1">
                                      <Button size="icon" variant="ghost" className="h-6 w-6" onClick={() => openNoveltyDialog(entry)} title="Agregar novedad">
                                        <PlusCircle className="w-3 h-3 text-blue-500" />
                                      </Button>
                                      <Button size="icon" variant="ghost" className="h-6 w-6 text-red-500" onClick={() => handleDeleteEntry(entry.entry_id, selectedPeriod.period_id)}>
                                        <Trash2 className="w-3 h-3" />
                                      </Button>
                                    </div>
                                  </TableCell>
                                )}
                              </TableRow>
                            );
                          })}
                          {/* Totals */}
                          <TableRow className="bg-slate-200 font-bold text-[11px]">
                            <TableCell colSpan={3} className="text-right border-r">TOTALES:</TableCell>
                            <TableCell className="text-right border-r font-mono">{formatNumber(totals.baseSalary)}</TableCell>
                            <TableCell className="text-right border-r font-mono">{formatNumber(totals.commissions)}</TableCell>
                            <TableCell className="text-right border-r font-mono">{formatNumber(totals.bonuses)}</TableCell>
                            <TableCell className="text-right border-r font-mono">{formatNumber(totals.overtimeDay + totals.overtimeNight + totals.overtimeWeekend + totals.overtimeHoliday)}</TableCell>
                            <TableCell className="text-right border-r font-mono text-amber-600">{formatNumber(totals.incomeNovelties)}</TableCell>
                            <TableCell className="text-right border-r font-mono">{formatNumber(totals.grossSalary)}</TableCell>
                            <TableCell className="text-right border-r font-mono text-red-600">{formatNumber(totals.sfsEmployee)}</TableCell>
                            <TableCell className="text-right border-r font-mono text-red-600">{formatNumber(totals.afpEmployee)}</TableCell>
                            <TableCell className="text-right border-r font-mono text-red-600">{formatNumber(totals.isr)}</TableCell>
                            <TableCell className="text-right border-r font-mono text-orange-600">{formatNumber(totals.deductionNovelties)}</TableCell>
                            <TableCell className="text-right border-r font-mono text-red-700">{formatNumber(totals.totalDeductions)}</TableCell>
                            <TableCell className="text-right font-mono text-emerald-700">{formatNumber(totals.netSalary)}</TableCell>
                            {selectedPeriod.status !== 'paid' && <TableCell></TableCell>}
                          </TableRow>
                        </TableBody>
                      </Table>
                    </CardContent>
                  </Card>
                )}
              </>
            )}
          </TabsContent>

          {/* Aprobación Tab */}
          <TabsContent value="aprobacion" className="space-y-4">
            <Card>
              <CardHeader><CardTitle>Nóminas Pendientes de Aprobación</CardTitle></CardHeader>
              <CardContent>
                {periods.filter(p => p.status === 'calculated').length === 0 ? (
                  <div className="text-center py-8 text-slate-500"><Check className="w-12 h-12 mx-auto mb-4 text-slate-300" /><p>No hay pendientes</p></div>
                ) : (
                  <div className="space-y-3">
                    {periods.filter(p => p.status === 'calculated').map(period => (
                      <div key={period.period_id} className="flex items-center justify-between p-4 border rounded-lg">
                        <div><h4 className="font-semibold">{period.description}</h4><p className="text-sm text-slate-500">{period.employee_count} empleados • {formatCurrency(period.total_net)}</p></div>
                        <div className="flex gap-2">
                          <Button variant="outline" onClick={() => { setSelectedPeriod(period); setActiveTab('nomina'); }}>Ver</Button>
                          <Button onClick={() => handleApprovePeriod(period.period_id)}><Check className="w-4 h-4 mr-2" />Aprobar</Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle className="text-emerald-700">Listos para Pagar</CardTitle></CardHeader>
              <CardContent>
                {periods.filter(p => p.status === 'approved').length === 0 ? (
                  <div className="text-center py-8 text-slate-500"><CreditCard className="w-12 h-12 mx-auto mb-4 text-slate-300" /><p>No hay aprobados</p></div>
                ) : (
                  <div className="space-y-3">
                    {periods.filter(p => p.status === 'approved').map(period => (
                      <div key={period.period_id} className="flex items-center justify-between p-4 border border-emerald-200 bg-emerald-50 rounded-lg">
                        <div><h4 className="font-semibold text-emerald-800">{period.description}</h4><p className="text-sm text-emerald-600">{period.employee_count} empleados • {formatCurrency(period.total_net)}</p></div>
                        <Button className="bg-emerald-600 hover:bg-emerald-700" onClick={() => openPayDialog(period)}><CreditCard className="w-4 h-4 mr-2" />Pagar</Button>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Reportes Tab */}
          <TabsContent value="reportes" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <CardHeader><CardTitle>Exportar Nóminas</CardTitle><CardDescription>Descarga en formato Excel o CSV</CardDescription></CardHeader>
                <CardContent>
                  {periods.filter(p => ['calculated', 'approved', 'paid'].includes(p.status)).length === 0 ? (
                    <p className="text-slate-500 text-center py-4">No hay nóminas para exportar</p>
                  ) : (
                    <div className="space-y-2">
                      {periods.filter(p => ['calculated', 'approved', 'paid'].includes(p.status)).map(period => (
                        <div key={period.period_id} className="flex items-center justify-between p-3 border rounded-lg">
                          <div><p className="font-medium">{period.description}</p>{getStatusBadge(period.status)}</div>
                          <div className="flex gap-2">
                            <Button variant="outline" size="sm" onClick={() => handleExportExcel(period.period_id)}><FileSpreadsheet className="w-4 h-4 mr-1" />CSV</Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
              
              {/* TSS Files Section */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="w-5 h-5 text-blue-600" />
                    Archivos TSS
                  </CardTitle>
                  <CardDescription>Tesorería de la Seguridad Social (v5.3 / v5.1)</CardDescription>
                </CardHeader>
                <CardContent>
                  {periods.filter(p => p.status === 'paid').length === 0 ? (
                    <p className="text-slate-500 text-center py-4">Pague una nómina para generar archivos TSS</p>
                  ) : (
                    <div className="space-y-3">
                      {periods.filter(p => p.status === 'paid').map(period => (
                        <div key={period.period_id} className="p-3 border rounded-lg bg-slate-50">
                          <div className="flex items-center justify-between mb-2">
                            <div>
                              <p className="font-medium">{period.description}</p>
                              <p className="text-xs text-slate-500">{period.month}/{period.year} • {period.employee_count} empleados</p>
                            </div>
                            {getPayrollTypeBadge(period.payroll_type)}
                          </div>
                          <div className="flex gap-2 flex-wrap">
                            <Button variant="outline" size="sm" className="text-blue-600 border-blue-200 hover:bg-blue-50" 
                              onClick={() => handleDownloadTSSAutodeterminacion(period.period_id)}>
                              <Download className="w-4 h-4 mr-1" />Autodeterminación
                            </Button>
                            <Button variant="outline" size="sm" className="text-purple-600 border-purple-200 hover:bg-purple-50"
                              onClick={() => handleDownloadTSSNovedades(period.period_id)}>
                              <Download className="w-4 h-4 mr-1" />Novedades
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* DGII Tax Reports Section */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5 text-emerald-600" />
                  Reportes DGII - Impuestos
                </CardTitle>
                <CardDescription>Formularios IR-3 e IR-17 para Dirección General de Impuestos Internos</CardDescription>
              </CardHeader>
              <CardContent>
                {periods.filter(p => p.status === 'paid').length === 0 ? (
                  <p className="text-slate-500 text-center py-4">Pague una nómina para generar reportes de impuestos</p>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {periods.filter(p => p.status === 'paid').map(period => (
                      <div key={period.period_id} className="p-4 border rounded-lg bg-gradient-to-br from-emerald-50 to-white">
                        <div className="mb-3">
                          <p className="font-semibold text-emerald-800">{period.description}</p>
                          <p className="text-xs text-emerald-600">{formatCurrency(period.total_net)} pagado</p>
                        </div>
                        <div className="space-y-2">
                          <Button variant="outline" size="sm" className="w-full justify-start text-emerald-700 border-emerald-200 hover:bg-emerald-100"
                            onClick={() => handleDownloadIR3(period.period_id)}>
                            <Download className="w-4 h-4 mr-2" />
                            <span>IR-3</span>
                            <span className="ml-auto text-xs text-emerald-500">Retenciones</span>
                          </Button>
                          <Button variant="outline" size="sm" className="w-full justify-start text-emerald-700 border-emerald-200 hover:bg-emerald-100"
                            onClick={() => handleDownloadIR17(period.period_id)}>
                            <Download className="w-4 h-4 mr-2" />
                            <span>IR-17</span>
                            <span className="ml-auto text-xs text-emerald-500">Declaración</span>
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
          <DialogContent className="max-w-lg">
            <DialogHeader><DialogTitle>Crear Nueva Nómina</DialogTitle><DialogDescription>Define el tipo y período de la nómina</DialogDescription></DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Tipo de Nómina</Label>
                <div className="grid grid-cols-3 gap-2">
                  {payrollTypes.map(pt => (
                    <Button key={pt.value} variant={newPeriodForm.payroll_type === pt.value ? "default" : "outline"}
                      className={`h-auto py-2 flex flex-col items-center ${newPeriodForm.payroll_type === pt.value ? '' : 'hover:bg-slate-50'}`}
                      onClick={() => setNewPeriodForm({...newPeriodForm, payroll_type: pt.value})}>
                      <pt.icon className="w-4 h-4 mb-1" /><span className="text-xs">{pt.label}</span>
                    </Button>
                  ))}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2"><Label>Período</Label>
                  <Select value={newPeriodForm.period_type} onValueChange={(v) => setNewPeriodForm({...newPeriodForm, period_type: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>{periodTypes.map(type => (<SelectItem key={type.value} value={type.value}>{type.label}</SelectItem>))}</SelectContent>
                  </Select>
                </div>
                <div className="space-y-2"><Label>Departamento (Opcional)</Label>
                  <Select value={newPeriodForm.department_filter} onValueChange={(v) => setNewPeriodForm({...newPeriodForm, department_filter: v})}>
                    <SelectTrigger><SelectValue placeholder="Todos" /></SelectTrigger>
                    <SelectContent><SelectItem value="all">Todos los departamentos</SelectItem>
                      {departments.map(d => (<SelectItem key={d} value={d}>{d}</SelectItem>))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2"><Label>Año</Label>
                  <Select value={String(newPeriodForm.year)} onValueChange={(v) => setNewPeriodForm({...newPeriodForm, year: parseInt(v)})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>{[2024, 2025, 2026, 2027].map(year => (<SelectItem key={year} value={String(year)}>{year}</SelectItem>))}</SelectContent>
                  </Select>
                </div>
                <div className="space-y-2"><Label>Mes</Label>
                  <Select value={String(newPeriodForm.month)} onValueChange={(v) => setNewPeriodForm({...newPeriodForm, month: parseInt(v)})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>{months.map(m => (<SelectItem key={m.value} value={String(m.value)}>{m.label}</SelectItem>))}</SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2"><Label>Fecha Inicio</Label><Input type="date" value={newPeriodForm.start_date} onChange={(e) => setNewPeriodForm({...newPeriodForm, start_date: e.target.value})} /></div>
                <div className="space-y-2"><Label>Fecha Fin</Label><Input type="date" value={newPeriodForm.end_date} onChange={(e) => setNewPeriodForm({...newPeriodForm, end_date: e.target.value})} /></div>
              </div>
              <div className="space-y-2"><Label>Descripción</Label><Input value={newPeriodForm.description} onChange={(e) => setNewPeriodForm({...newPeriodForm, description: e.target.value})} placeholder="Ej: Nómina Quincenal Enero 2026" /></div>
            </div>
            <DialogFooter><Button variant="outline" onClick={() => setShowNewPeriod(false)}>Cancelar</Button><Button onClick={handleCreatePeriod}>Crear Nómina</Button></DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Pay Dialog */}
        <Dialog open={showPayDialog} onOpenChange={setShowPayDialog}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Wallet className="w-5 h-5 text-emerald-600" />
                Pagar Nómina
              </DialogTitle>
              <DialogDescription>Configure el pago y archivo bancario</DialogDescription>
            </DialogHeader>
            {selectedPeriod && (
              <div className="space-y-4">
                <div className="p-4 bg-slate-50 rounded-lg">
                  <p className="font-semibold">{selectedPeriod.description}</p>
                  <p className="text-sm text-slate-500 mt-1">{selectedPeriod.employee_count} empleados</p>
                  <div className="mt-3 p-3 bg-emerald-100 rounded-lg">
                    <p className="text-sm text-emerald-700">Total a Pagar</p>
                    <p className="text-2xl font-bold text-emerald-800">{formatCurrency(selectedPeriod.total_net)}</p>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label>Cuenta Contable</Label>
                  <Select value={selectedBankAccount} onValueChange={setSelectedBankAccount}>
                    <SelectTrigger>
                      <SelectValue placeholder="Seleccione cuenta" />
                    </SelectTrigger>
                    <SelectContent>
                      {bankAccounts.map(acc => (
                        <SelectItem key={acc.code} value={acc.code}>{acc.code} - {acc.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="border-t pt-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <Label className="flex items-center gap-2">
                      <FileSpreadsheet className="w-4 h-4 text-blue-500" />
                      Generar archivo bancario
                    </Label>
                    <input 
                      type="checkbox" 
                      checked={generateBankFile} 
                      onChange={(e) => setGenerateBankFile(e.target.checked)}
                      className="w-4 h-4 rounded border-slate-300"
                    />
                  </div>
                  
                  {generateBankFile && (
                    <div className="space-y-2 pl-6">
                      <Label className="text-sm">Banco para archivo de pago</Label>
                      <Select value={selectedPaymentBank} onValueChange={setSelectedPaymentBank}>
                        <SelectTrigger>
                          <SelectValue placeholder="Seleccione banco" />
                        </SelectTrigger>
                        <SelectContent>
                          {paymentBanks.map(bank => (
                            <SelectItem key={bank.id} value={bank.id}>
                              {bank.name} ({bank.format})
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <p className="text-xs text-slate-500">
                        Se descargará automáticamente el archivo para carga en el banco
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowPayDialog(false)}>Cancelar</Button>
              <Button 
                className="bg-emerald-600 hover:bg-emerald-700" 
                onClick={handlePayPeriod} 
                disabled={!selectedBankAccount || (generateBankFile && !selectedPaymentBank)}
              >
                <CreditCard className="w-4 h-4 mr-2" />
                Confirmar Pago
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Novelty Dialog */}
        <Dialog open={showNoveltyDialog} onOpenChange={setShowNoveltyDialog}>
          <DialogContent>
            <DialogHeader><DialogTitle>Agregar Novedad</DialogTitle>
              <DialogDescription>Agregue un ingreso o deducción adicional a {selectedEntry?.employee_name}</DialogDescription></DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <Button variant={noveltyForm.novelty_type === 'income' ? 'default' : 'outline'} className="h-auto py-3 flex flex-col"
                  onClick={() => setNoveltyForm({...noveltyForm, novelty_type: 'income', code: '', name: ''})}>
                  <PlusCircle className="w-5 h-5 mb-1 text-emerald-500" /><span>Ingreso</span>
                </Button>
                <Button variant={noveltyForm.novelty_type === 'deduction' ? 'default' : 'outline'} className="h-auto py-3 flex flex-col"
                  onClick={() => setNoveltyForm({...noveltyForm, novelty_type: 'deduction', code: '', name: ''})}>
                  <MinusCircle className="w-5 h-5 mb-1 text-red-500" /><span>Deducción</span>
                </Button>
              </div>
              <div className="space-y-2"><Label>Tipo de {noveltyForm.novelty_type === 'income' ? 'Ingreso' : 'Deducción'}</Label>
                <Select value={noveltyForm.code} onValueChange={(v) => {
                  const types = noveltyForm.novelty_type === 'income' ? noveltyTypes.income : noveltyTypes.deduction;
                  const selected = types.find(t => t.code === v);
                  setNoveltyForm({...noveltyForm, code: v, name: selected?.name || '', description: selected?.description || ''});
                }}>
                  <SelectTrigger><SelectValue placeholder="Seleccione" /></SelectTrigger>
                  <SelectContent>
                    {(noveltyForm.novelty_type === 'income' ? noveltyTypes.income : noveltyTypes.deduction).map(t => (
                      <SelectItem key={t.code} value={t.code}>{t.code} - {t.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2"><Label>Monto (RD$)</Label>
                <Input type="number" step="0.01" value={noveltyForm.amount} onChange={(e) => setNoveltyForm({...noveltyForm, amount: e.target.value})} placeholder="0.00" />
              </div>
              <div className="space-y-2"><Label>Descripción (Opcional)</Label>
                <Input value={noveltyForm.description} onChange={(e) => setNoveltyForm({...noveltyForm, description: e.target.value})} placeholder="Ej: Comisión ventas enero" />
              </div>
            </div>
            <DialogFooter><Button variant="outline" onClick={() => setShowNoveltyDialog(false)}>Cancelar</Button>
              <Button onClick={handleAddNovelty}><Plus className="w-4 h-4 mr-2" />Agregar Novedad</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
