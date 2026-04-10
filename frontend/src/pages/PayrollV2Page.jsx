import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
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
  Briefcase,
  Eye,
  Building2,
  Shield,
  List,
  Send
} from "lucide-react";
import { toast } from "sonner";
import { DrillDownModal } from "@/components/DrillDown";

// These will be populated inside the component with translations
const MONTH_KEYS = [
  { value: 1, key: "january" }, { value: 2, key: "february" }, { value: 3, key: "march" },
  { value: 4, key: "april" }, { value: 5, key: "may" }, { value: 6, key: "june" },
  { value: 7, key: "july" }, { value: 8, key: "august" }, { value: 9, key: "september" },
  { value: 10, key: "october" }, { value: 11, key: "november" }, { value: 12, key: "december" }
];

const PERIOD_TYPE_KEYS = [
  { value: "quincenal_1", key: "biweekly1" },
  { value: "quincenal_2", key: "biweekly2" },
  { value: "mensual", key: "monthly" }
];

const PAYROLL_TYPE_KEYS = [
  { value: "REG", key: "regular", icon: Calendar, color: "blue" },
  { value: "TEMP", key: "temporary", icon: Briefcase, color: "orange" },
  { value: "BONO", key: "bonus", icon: Gift, color: "purple" },
  { value: "REG13", key: "christmas", icon: Gift, color: "emerald" },
  { value: "VAC", key: "vacation", icon: Calendar, color: "cyan" },
  { value: "LIQ", key: "severance", icon: FileText, color: "red" },
  { value: "OBREROS_NG", key: "construction", icon: Briefcase, color: "amber" },
];

// Static department list (these come from user data, not translations)
const departments = ["Administración", "Ventas", "Marketing", "TI", "Recursos Humanos", "Finanzas", "Operaciones", "Legal", "Producción", "Logística"];

export default function PayrollPage() {
  const { t } = useTranslation();
  
  // Generate translated arrays
  const months = MONTH_KEYS.map(m => ({ value: m.value, label: t(`common.months.${m.key}`) }));
  const periodTypes = PERIOD_TYPE_KEYS.map(p => ({ value: p.value, label: t(`payrollV2.periodTypes.${p.key}`) }));
  const payrollTypes = PAYROLL_TYPE_KEYS.map(p => ({ 
    value: p.value, 
    label: t(`payrollV2.payrollTypes.${p.key}`), 
    icon: p.icon, 
    color: p.color 
  }));
  
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
  const [qbSyncing, setQbSyncing] = useState(false);
  
  // Quick filter states
  const [quickFilter, setQuickFilter] = useState(null);
  const [departmentFilter, setDepartmentFilter] = useState("all");
  
  // TSS Report states
  const [showTssPreview, setShowTssPreview] = useState(false);
  const [tssPreviewData, setTssPreviewData] = useState(null);
  const [tssLoading, setTssLoading] = useState(false);
  
  // Drill-down state for period details
  const [drillDown, setDrillDown] = useState({ open: false, title: "", data: [], columns: [] });
  const [drillDownLoading, setDrillDownLoading] = useState(false);
  
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

  // Fetch company settings
  const fetchCompanySettings = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/company/settings`, { headers: getAuthHeaders(), withCredentials: true });
      // Company settings returns { company: { name: "..." }, ... }
      if (response.data?.company?.name) {
        setCompanyName(response.data.company.name);
      }
    } catch (_error) {
      // If company settings endpoint fails, try from auth/me
      try {
        const meResponse = await axios.get(`${API}/auth/me`, { headers: getAuthHeaders(), withCredentials: true });
        if (meResponse.data?.company_name) {
          setCompanyName(meResponse.data.company_name);
        }
      } catch (meError) {
        // Company name fetch failed silently
      }
    }
  }, [getAuthHeaders]);

  const fetchPeriods = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/payroll/periods`, { headers: getAuthHeaders(), withCredentials: true });
      setPeriods(response.data);
    } catch (_error) {
      toast.error(t('payrollV2.messages.errorLoadingPeriods'));
    }
  }, [getAuthHeaders, t]);

  const fetchPeriodDetails = useCallback(async (periodId) => {
    try {
      const response = await axios.get(`${API}/payroll/periods/${periodId}`, { headers: getAuthHeaders(), withCredentials: true });
      setPeriodEntries(response.data.entries || []);
    } catch (_error) {
      console.error("Error fetching period details");
    }
  }, [getAuthHeaders]);

  const fetchBankAccounts = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/accounting/accounts`, { headers: getAuthHeaders(), withCredentials: true });
      const banks = response.data.filter(acc => acc.code.startsWith('1101') || (acc.account_type === 'asset' && acc.name.toLowerCase().includes('banco')));
      setBankAccounts(banks);
      if (banks.length > 0) setSelectedBankAccount(banks[0].code);
    } catch (_error) {
      console.error("Error fetching bank accounts");
    }
  }, [getAuthHeaders]);

  const fetchNoveltyTypes = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/payroll/novelty-types`, { headers: getAuthHeaders(), withCredentials: true });
      setNoveltyTypes(response.data);
    } catch (_error) {
      console.error("Error fetching novelty types");
    }
  }, [getAuthHeaders]);

  // TSS Report functions
  const openTssPreview = async (periodId) => {
    // Find and set the period for download button
    const period = periods.find(p => p.period_id === periodId);
    if (period) setSelectedPeriod(period);
    
    setTssLoading(true);
    setShowTssPreview(true);
    try {
      const response = await axios.get(
        `${API}/payroll/periods/${periodId}/tss-preview`,
        { headers: getAuthHeaders(), withCredentials: true }
      );
      setTssPreviewData(response.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || t('payrollV2.messages.errorLoadingTss'));
      setShowTssPreview(false);
    } finally {
      setTssLoading(false);
    }
  };

  const downloadTssReport = async (periodId) => {
    try {
      const response = await axios.get(
        `${API}/payroll/periods/${periodId}/tss-report`,
        { 
          headers: getAuthHeaders(), 
          withCredentials: true,
          responseType: 'blob'
        }
      );
      const blob = new Blob([response.data], { type: 'text/plain;charset=utf-8' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      const filename = tssPreviewData?.filename || `TSS_Report_${periodId}.txt`;
      link.download = filename;
      link.click();
      toast.success(t('payrollV2.messages.tssDownloaded'));
    } catch (error) {
      toast.error(error.response?.data?.detail || t('payrollV2.messages.errorDownloadingTss'));
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-DO', {
      style: 'currency',
      currency: 'DOP',
      minimumFractionDigits: 2
    }).format(amount || 0);
  };

  useEffect(() => {
    fetchPeriods();
    fetchBankAccounts();
    fetchNoveltyTypes();
    fetchCompanySettings();
    if (user?.company_name) setCompanyName(user.company_name);
  }, [fetchPeriods, fetchBankAccounts, fetchNoveltyTypes, fetchCompanySettings, user?.company_name]);

  useEffect(() => {
    if (selectedPeriod) fetchPeriodDetails(selectedPeriod.period_id);
  }, [selectedPeriod, fetchPeriodDetails]);

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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [newPeriodForm.period_type, newPeriodForm.year, newPeriodForm.month]);

  const handleCreatePeriod = async () => {
    try {
      const dataToSend = {
        ...newPeriodForm,
        department_filter: newPeriodForm.department_filter === "all" ? null : newPeriodForm.department_filter
      };
      await axios.post(`${API}/payroll/periods`, dataToSend, { headers: getAuthHeaders(), withCredentials: true });
      toast.success(t('payrollV2.messages.periodCreated'));
      setShowNewPeriod(false);
      fetchPeriods();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('payrollV2.messages.errorCreatingPeriod'));
    }
  };

  const handleAddEmployees = async (periodId) => {
    try {
      const response = await axios.post(`${API}/payroll/periods/${periodId}/add-employees`, {}, { headers: getAuthHeaders(), withCredentials: true });
      toast.success(response.data.message);
      fetchPeriodDetails(periodId);
      fetchPeriods();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    }
  };

  const handleCalculatePeriod = async (periodId) => {
    try {
      await axios.post(`${API}/payroll/periods/${periodId}/calculate`, {}, { headers: getAuthHeaders(), withCredentials: true });
      toast.success(t('payrollV2.messages.payrollsCalculated'));
      fetchPeriodDetails(periodId);
      fetchPeriods();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    }
  };

  const handleSubmitForApproval = async (periodId) => {
    try {
      await axios.post(`${API}/payroll/periods/${periodId}/submit-for-approval`, {}, { headers: getAuthHeaders(), withCredentials: true });
      toast.success(t('payrollV2.messages.sentForApproval'));
      fetchPeriods();
      if (selectedPeriod?.period_id === periodId) {
        const updated = await axios.get(`${API}/payroll/periods/${periodId}`, { headers: getAuthHeaders(), withCredentials: true });
        setSelectedPeriod(prev => ({ ...prev, status: 'pending_approval' }));
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || t('payrollV2.messages.errorSendingForApproval'));
    }
  };

  const handleApprovePeriod = async (periodId) => {
    try {
      await axios.post(`${API}/payroll/periods/${periodId}/approve`, {}, { headers: getAuthHeaders(), withCredentials: true });
      toast.success(t('payrollV2.messages.periodApproved'));
      fetchPeriods();
      if (selectedPeriod?.period_id === periodId) {
        setSelectedPeriod(prev => ({ ...prev, status: 'approved' }));
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || t('payrollV2.messages.errorApproving'));
    }
  };

  const handleRejectPeriod = async (periodId, reason) => {
    if (!reason) {
      toast.error(t('payrollV2.messages.rejectReasonRequired'));
      return;
    }
    try {
      await axios.post(`${API}/payroll/periods/${periodId}/reject`, { comments: reason }, { headers: getAuthHeaders(), withCredentials: true });
      toast.success(t('payrollV2.messages.periodRejected'));
      fetchPeriods();
      if (selectedPeriod?.period_id === periodId) {
        setSelectedPeriod(prev => ({ ...prev, status: 'draft' }));
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || t('payrollV2.messages.errorRejecting'));
    }
  };

  const openPayDialog = (period) => { setSelectedPeriod(period); setShowPayDialog(true); };

  const handlePayPeriod = async () => {
    if (!selectedPeriod) return;
    try {
      const response = await axios.post(`${API}/payroll/periods/${selectedPeriod.period_id}/pay`, 
        { bank_account_code: selectedBankAccount },
        { headers: getAuthHeaders(), withCredentials: true }
      );
      toast.success(t('payrollV2.messages.payrollPaid', { entryNumber: response.data.entry_number }));
      
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
          
          toast.success(t('payrollV2.messages.bankFileDownloaded', { bankName: bank?.name }));
        } catch (bankError) {
          toast.error(t('payrollV2.messages.errorGeneratingBankFile'));
        }
      }
      
      setShowPayDialog(false);
      setSelectedPaymentBank("");
      fetchPeriods();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error");
    }
  };

  const handleSyncToQuickBooks = async (periodId) => {
    if (!confirm("¿Enviar el asiento de diario de esta nómina a QuickBooks?")) return;
    setQbSyncing(true);
    try {
      const response = await axios.post(`${API}/quickbooks/sync/payroll`, 
        { sync_type: "payroll", period_id: periodId },
        { headers: getAuthHeaders(), withCredentials: true }
      );
      toast.success(response.data.message || "Asiento enviado a QuickBooks");
      fetchPeriodDetails(periodId);
      fetchPeriods();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al enviar a QuickBooks");
    } finally {
      setQbSyncing(false);
    }
  };

  const handleDeletePeriod = async (periodId) => {
    if (!confirm("¿Eliminar este período y su asiento asociado?")) return;
    try {
      await axios.delete(`${API}/payroll/periods/${periodId}`, { headers: getAuthHeaders(), withCredentials: true });
      toast.success(t('payrollV2.messages.periodDeleted'));
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

      // If editing ISR, send as isr_override so backend uses the manual value
      if (editingCell.field === 'isr') {
        updateData.isr_override = numValue;
      } else {
        updateData[editingCell.field] = numValue;
      }

      await axios.put(`${API}/payroll/entries/${entry.entry_id}`, updateData, { headers: getAuthHeaders(), withCredentials: true });
      toast.success(t('payrollV2.messages.updated'));
      fetchPeriodDetails(entry.period_id);
      fetchPeriods();
    } catch (error) {
      toast.error(t('common.error'));
    } finally {
      cancelEditing();
    }
  };

  const handleDeleteEntry = async (entryId, periodId) => {
    if (!confirm("¿Eliminar esta entrada?")) return;
    try {
      await axios.delete(`${API}/payroll/entries/${entryId}`, { headers: getAuthHeaders(), withCredentials: true });
      toast.success(t('payrollV2.messages.deleted'));
      fetchPeriodDetails(periodId);
      fetchPeriods();
    } catch (error) {
      toast.error(t('common.error'));
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
      toast.error(t('payrollV2.messages.completeRequiredFields'));
      return;
    }

    try {
      await axios.post(`${API}/payroll/entries/${selectedEntry.entry_id}/novelties`, {
        entry_id: selectedEntry.entry_id,
        ...noveltyForm,
        amount: parseFloat(noveltyForm.amount) || 0
      }, { headers: getAuthHeaders(), withCredentials: true });
      toast.success(t('payrollV2.messages.noveltyAdded'));
      setShowNoveltyDialog(false);
      fetchPeriodDetails(selectedEntry.period_id);
      fetchPeriods();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error");
    }
  };

  const handleDeleteNovelty = async (entryId, noveltyId, periodId) => {
    try {
      await axios.delete(`${API}/payroll/entries/${entryId}/novelties/${noveltyId}`, { headers: getAuthHeaders(), withCredentials: true });
      toast.success(t('payrollV2.messages.noveltyDeleted'));
      fetchPeriodDetails(periodId);
      fetchPeriods();
    } catch (error) {
      toast.error(t('common.error'));
    }
  };

  // Export handlers
  const handleExportExcel = async (periodId) => {
    try {
      const response = await axios.get(`${API}/payroll/periods/${periodId}/export/excel`, { headers: getAuthHeaders(), withCredentials: true });
      const data = response.data;
      
      // Use company name from response or state
      const exportCompanyName = data.company_name || companyName;
      
      // Create CSV content
      let csv = `${exportCompanyName}\n`;
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
      csv += `${data.totals.salario_base},${data.totals.comisiones},${data.totals.bonos},${data.totals.he_diurnas || 0},${data.totals.he_nocturnas || 0},${data.totals.he_finsemana || 0},${data.totals.he_feriados || 0},${data.totals.otros_ingresos || 0},`;
      csv += `${data.totals.total_ingresos},${data.totals.sfs},${data.totals.afp},${data.totals.isr},${data.totals.otros_descuentos || 0},`;
      csv += `${data.totals.total_descuentos},${data.totals.neto}\n`;

      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `nomina_${data.period.period_id}.csv`;
      link.click();
      toast.success(t('payrollV2.messages.excelExported'));
    } catch (error) {
      console.error("Export error:", error);
      toast.error(error.response?.data?.detail || t('payrollV2.messages.errorExporting'));
    }
  };

  // Download TSS Autodeterminación Excel file
  const handleDownloadTSSAutodeterminacion = async (periodId) => {
    try {
      const response = await axios.get(`${API}/payroll/periods/${periodId}/export/tss-autodeterminacion`, {
        headers: getAuthHeaders(),
        withCredentials: true,
        responseType: 'blob'
      });
      const blob = new Blob([response.data], { type: 'application/vnd.ms-excel' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `TSS_Autodeterminacion.xls`;
      link.click();
      toast.success(t('payrollV2.messages.tssAutodeterminacionDownloaded'));
    } catch (error) {
      toast.error(error.response?.data?.detail || t('payrollV2.messages.errorDownloadingTssAutodeterminacion'));
    }
  };

  // Download TSS Novedades Excel file
  const handleDownloadTSSNovedades = async (periodId) => {
    try {
      const response = await axios.get(`${API}/payroll/periods/${periodId}/export/tss-novedades`, {
        headers: getAuthHeaders(),
        withCredentials: true,
        responseType: 'blob'
      });
      const blob = new Blob([response.data], { type: 'application/vnd.ms-excel' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `TSS_Novedades.xls`;
      link.click();
      toast.success(t('payrollV2.messages.tssNovedadesDownloaded'));
    } catch (error) {
      toast.error(error.response?.data?.detail || t('payrollV2.messages.errorDownloadingTssNovedades'));
    }
  };

  // Download IR-3 Excel file
  const handleDownloadIR3 = async (periodId) => {
    try {
      const response = await axios.get(`${API}/payroll/periods/${periodId}/export/ir3`, {
        headers: getAuthHeaders(),
        withCredentials: true,
        responseType: 'blob'
      });
      const blob = new Blob([response.data], { type: 'application/vnd.ms-excel' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `IR3_Retenciones.xls`;
      link.click();
      toast.success(t('payrollV2.messages.ir3Downloaded'));
    } catch (error) {
      toast.error(error.response?.data?.detail || t('payrollV2.messages.errorDownloadingIr3'));
    }
  };

  // Download IR-17 Excel file
  const handleDownloadIR17 = async (periodId) => {
    try {
      const response = await axios.get(`${API}/payroll/periods/${periodId}/export/ir17`, {
        headers: getAuthHeaders(),
        withCredentials: true,
        responseType: 'blob'
      });
      const blob = new Blob([response.data], { type: 'application/vnd.ms-excel' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `IR17_Declaracion.xls`;
      link.click();
      toast.success(t('payrollV2.messages.ir17Downloaded'));
    } catch (error) {
      toast.error(error.response?.data?.detail || t('payrollV2.messages.errorDownloadingIr17'));
    }
  };

  // Legacy TSS export (JSON/CSV)
  const handleExportTSS = async (periodId) => {
    try {
      const response = await axios.get(`${API}/payroll/periods/${periodId}/export/tss`, { headers: getAuthHeaders(), withCredentials: true });
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
      toast.success(t('payrollV2.messages.tssExported'));
    } catch (error) {
      toast.error(t('payrollV2.messages.errorExportingTss'));
    }
  };

  const formatNumber = (value) => new Intl.NumberFormat('es-DO', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(value || 0);

  const getStatusBadge = (status) => {
    const badges = {
      'open': <Badge variant="outline" className="border-blue-500 text-blue-600 dark:text-blue-400">{t('payrollV2.statuses.open')}</Badge>,
      'draft': <Badge variant="outline" className="border-slate-500 text-slate-600 dark:text-slate-400">{t('payrollV2.statuses.draft')}</Badge>,
      'pending_approval': <Badge className="bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400">{t('payrollV2.statuses.pendingApproval')}</Badge>,
      'calculated': <Badge className="bg-amber-100 text-amber-700 dark:text-amber-400">{t('payrollV2.statuses.calculated')}</Badge>,
      'approved': <Badge className="bg-emerald-100 text-emerald-700 dark:text-emerald-400">{t('payrollV2.statuses.approved')}</Badge>,
      'paid': <Badge className="bg-purple-100 text-purple-700 dark:text-purple-400">{t('payrollV2.statuses.paid')}</Badge>,
    };
    return badges[status] || <Badge variant="secondary">{status}</Badge>;
  };

  const getPayrollTypeBadge = (type) => {
    const pt = payrollTypes.find(p => p.value === type);
    if (!pt) return null;
    return <Badge className={`bg-${pt.color}-100 text-${pt.color}-700`}>{pt.label}</Badge>;
  };

  // Drill-down for period details
  const handlePeriodDrillDown = async (period) => {
    setDrillDownLoading(true);
    setDrillDown({ open: true, title: "", data: [], columns: [] });
    
    try {
      // Use existing endpoint that returns period with entries
      const response = await axios.get(`${API}/payroll/periods/${period.period_id}`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      
      // Entries are included in the period response
      const entries = response.data?.entries || response.data?.employee_records || [];
      const columns = [
        { header: t('payrollV2.table.employee'), accessor: "employee_name" },
        { header: t('payrollV2.table.department'), accessor: "department" },
        { header: t('payrollV2.messages.baseSalary'), accessor: "base_salary", render: (val) => formatCurrency(val), className: "text-right", cellClassName: "text-right" },
        { header: t('payrollV2.table.gross'), accessor: "gross_salary", render: (val) => formatCurrency(val), className: "text-right", cellClassName: "text-right" },
        { header: t('payrollV2.table.deductions'), accessor: "total_deductions", render: (val) => formatCurrency(val), className: "text-right", cellClassName: "text-right text-red-600" },
        { header: t('payrollV2.table.net'), accessor: "net_salary", render: (val) => formatCurrency(val), className: "text-right", cellClassName: "text-right font-bold text-emerald-600" }
      ];
      
      setDrillDown({
        open: true,
        title: `${t('payrollV2.breakdown')}: ${period.description}`,
        data: entries,
        columns
      });
    } catch (error) {
      console.error("Error fetching period entries:", error);
      toast.error(t('payrollV2.messages.errorLoadingBreakdown'));
      setDrillDown({ open: false, title: "", data: [], columns: [] });
    } finally {
      setDrillDownLoading(false);
    }
  };

  const closeDrillDown = () => {
    setDrillDown({ open: false, title: "", data: [], columns: [] });
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
          <Button size="icon" variant="ghost" className="h-5 w-5" onClick={saveInlineEdit}><Check className="w-3 h-3 text-emerald-600 dark:text-emerald-400" /></Button>
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
    <DashboardLayout title={t('payroll.title')}>
      <div className="space-y-6" data-testid="payroll-page">
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">{t('payroll.pageTitle')}</h1>
            <p className="text-slate-500 dark:text-slate-400">{t('payroll.pageSubtitle')}</p>
          </div>
          <div className="flex gap-2">
            <Button onClick={fetchPeriods} variant="outline" size="sm"><RefreshCw className="w-4 h-4 mr-2" />{t('payroll.refresh')}</Button>
            <Button onClick={() => setShowNewPeriod(true)} size="sm"><Plus className="w-4 h-4 mr-2" />{t('payroll.newPayroll')}</Button>
          </div>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid grid-cols-5 w-full max-w-2xl">
            <TabsTrigger value="dashboard">{t('payroll.tabs.dashboard')}</TabsTrigger>
            <TabsTrigger value="periodos">{t('payroll.tabs.periods')} ({periods.length})</TabsTrigger>
            <TabsTrigger value="nomina">{t('payroll.tabs.payrollSheet')}</TabsTrigger>
            <TabsTrigger value="aprobacion">{t('payroll.tabs.approval')}</TabsTrigger>
            <TabsTrigger value="reportes">{t('payroll.tabs.reports')}</TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card 
                className={`border-l-4 border-l-blue-500 cursor-pointer transition-all hover:shadow-md ${quickFilter === 'open' ? 'ring-2 ring-blue-400' : ''}`}
                onClick={() => setQuickFilter(quickFilter === 'open' ? null : 'open')}
              >
                <CardContent className="p-4">
                  <p className="text-sm text-slate-500 dark:text-slate-400">{t('payroll.stats.openPeriods')}</p>
                  <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{stats.openPeriods}</p>
                </CardContent>
              </Card>
              <Card 
                className={`border-l-4 border-l-orange-500 cursor-pointer transition-all hover:shadow-md ${quickFilter === 'pending' ? 'ring-2 ring-orange-400' : ''}`}
                onClick={() => setQuickFilter(quickFilter === 'pending' ? null : 'pending')}
              >
                <CardContent className="p-4">
                  <p className="text-sm text-slate-500 dark:text-slate-400">{t('payroll.stats.pendingPayrolls')}</p>
                  <p className="text-2xl font-bold text-orange-600">{stats.pendingPayrolls}</p>
                </CardContent>
              </Card>
              <Card 
                className={`border-l-4 border-l-purple-500 cursor-pointer transition-all hover:shadow-md ${quickFilter === 'paid' ? 'ring-2 ring-purple-400' : ''}`}
                onClick={() => setQuickFilter(quickFilter === 'paid' ? null : 'paid')}
              >
                <CardContent className="p-4">
                  <p className="text-sm text-slate-500 dark:text-slate-400">{t('payroll.stats.totalPaid')}</p>
                  <p className="text-xl font-bold text-purple-600 dark:text-purple-400">{formatCurrency(stats.totalPaid)}</p>
                </CardContent>
              </Card>
              <Card className="border-l-4 border-l-emerald-500">
                <CardContent className="p-4">
                  <p className="text-sm text-slate-500 dark:text-slate-400">{t('payroll.stats.payrollTypes')}</p>
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
                  {t('common.filter')}: {quickFilter === 'open' ? t('payrollV2.filters.openPeriods') : quickFilter === 'pending' ? t('payrollV2.filters.pending') : t('payrollV2.filters.paid')}
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
                  <SelectItem value="all">{t('payrollV2.todosLosDepartamentos')}</SelectItem>
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
                <p className="text-slate-500 mb-4">{t('payrollV2.noHayPeriodosDe')}</p>
                <Button onClick={() => setShowNewPeriod(true)}>{t('payrollV2.crearPrimeraNomina')}</Button>
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
                            <Calendar className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <h4 className="font-semibold">{period.description}</h4>
                              {getPayrollTypeBadge(period.payroll_type)}
                            </div>
                            <p className="text-sm text-slate-500 dark:text-slate-400">{period.start_date} - {period.end_date} • {period.employee_count} empleados</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="text-right">
                            <p className="text-sm text-slate-500 dark:text-slate-400">{t('payrollV2.totalNeto')}</p>
                            <p className="font-mono font-semibold">{formatCurrency(period.total_net)}</p>
                          </div>
                          {getStatusBadge(period.status)}
                          <Button 
                            variant="ghost" 
                            size="sm"
                            onClick={(e) => { 
                              e.stopPropagation(); 
                              handlePeriodDrillDown(period); 
                            }}
                            title="Ver desglose rápido"
                          >
                            <List className="w-4 h-4" />
                          </Button>
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
                <p className="text-slate-500 dark:text-slate-400">{t('payrollV2.seleccioneUnPeriodo')}</p>
                <Button variant="link" onClick={() => setActiveTab('periodos')}>{t('payrollV2.verPeriodos')}</Button>
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
                          {/* Draft/Open: Add employees, Calculate, Submit for Approval */}
                          {['open', 'draft'].includes(selectedPeriod.status) && (
                            <>
                              <Button size="sm" variant="secondary" onClick={() => handleAddEmployees(selectedPeriod.period_id)}><Users className="w-4 h-4 mr-1" />{t('payrollV2.agregar')}</Button>
                              <Button size="sm" variant="secondary" onClick={() => handleCalculatePeriod(selectedPeriod.period_id)}><Calculator className="w-4 h-4 mr-1" />{t('payrollV2.calcular')}</Button>
                              {selectedPeriod.employee_count > 0 && (
                                <Button size="sm" className="bg-orange-500 hover:bg-orange-600" onClick={() => handleSubmitForApproval(selectedPeriod.period_id)}>
                                  <ChevronRight className="w-4 h-4 mr-1" />Enviar a Aprobación
                                </Button>
                              )}
                            </>
                          )}
                          {/* Pending Approval: Approve or Reject */}
                          {selectedPeriod.status === 'pending_approval' && (
                            <>
                              <Button size="sm" variant="secondary" onClick={() => {
                                const reason = prompt("Motivo del rechazo:");
                                if (reason) handleRejectPeriod(selectedPeriod.period_id, reason);
                              }}>
                                <X className="w-4 h-4 mr-1" />Rechazar
                              </Button>
                              <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700" onClick={() => handleApprovePeriod(selectedPeriod.period_id)}>
                                <Check className="w-4 h-4 mr-1" />Aprobar
                              </Button>
                            </>
                          )}
                          {/* Calculated (legacy support) */}
                          {selectedPeriod.status === 'calculated' && (
                            <Button size="sm" variant="secondary" onClick={() => handleApprovePeriod(selectedPeriod.period_id)}><Check className="w-4 h-4 mr-1" />{t('payrollV2.aprobar')}</Button>
                          )}
                          {/* Approved: Pay */}
                          {selectedPeriod.status === 'approved' && (
                            <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700" onClick={() => openPayDialog(selectedPeriod)}><CreditCard className="w-4 h-4 mr-1" />{t('payrollV2.pagar')}</Button>
                          )}
                          <Button size="sm" variant="secondary" onClick={() => handleExportExcel(selectedPeriod.period_id)}><Download className="w-4 h-4 mr-1" />{t('payrollV2.excel')}</Button>
                          {/* Send to QuickBooks - only for paid periods */}
                          {selectedPeriod.status === 'paid' && !selectedPeriod.qb_journal_entry_id && (
                            <Button 
                              size="sm" 
                              variant="outline"
                              className="border-emerald-300 text-emerald-700 hover:bg-emerald-50"
                              onClick={() => handleSyncToQuickBooks(selectedPeriod.period_id)}
                              disabled={qbSyncing}
                              data-testid="btn-sync-qbo"
                            >
                              {qbSyncing ? <RefreshCw className="w-4 h-4 mr-1 animate-spin" /> : <Send className="w-4 h-4 mr-1" />}
                              Enviar a QBO
                            </Button>
                          )}
                          {selectedPeriod.qb_journal_entry_id && (
                            <Badge className="bg-emerald-100 text-emerald-700 text-xs" data-testid="qb-synced-badge">
                              <Check className="w-3 h-3 mr-1" />QBO JE #{selectedPeriod.qb_journal_entry_id}
                            </Badge>
                          )}
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
                    <p className="text-slate-500 dark:text-slate-400">{t('payrollV2.noHayEmpleados')}</p>
                    <Button variant="link" onClick={() => handleAddEmployees(selectedPeriod.period_id)}>{t('payrollV2.agregarEmpleados')}</Button>
                  </CardContent></Card>
                ) : (
                  <Card>
                    <CardContent className="p-0 overflow-x-auto">
                      <Table className="text-[10px]">
                        <TableHeader>
                          <TableRow className="bg-slate-100 dark:bg-slate-800">
                            <TableHead className="font-bold text-center border-r w-8">{t('payrollV2.no')}</TableHead>
                            <TableHead className="font-bold border-r min-w-[150px]">{t('payrollV2.empleado')}</TableHead>
                            <TableHead className="font-bold text-center border-r w-24">{t('payrollV2.cedula')}</TableHead>
                            <TableHead className="font-bold text-right border-r bg-blue-50 w-24">{t('payrollV2.salario')}</TableHead>
                            <TableHead className="font-bold text-right border-r bg-emerald-50 w-20">{t('payrollV2.comis')}</TableHead>
                            <TableHead className="font-bold text-right border-r bg-emerald-50 w-20">{t('payrollV2.bonos')}</TableHead>
                            <TableHead className="font-bold text-right border-r bg-emerald-50 w-20">{t('payrollV2.hextras')}</TableHead>
                            <TableHead className="font-bold text-right border-r bg-amber-50 w-20">{t('payrollV2.novedades')}</TableHead>
                            <TableHead className="font-bold text-right border-r bg-slate-200 w-24">{t('payrollV2.bruto')}</TableHead>
                            <TableHead className="font-bold text-right border-r bg-red-50 w-20">{t('payrollV2.sfs')}</TableHead>
                            <TableHead className="font-bold text-right border-r bg-red-50 w-20">{t('payrollV2.afp')}</TableHead>
                            <TableHead className="font-bold text-right border-r bg-red-50 w-20">{t('payrollV2.isr')}</TableHead>
                            <TableHead className="font-bold text-right border-r bg-orange-50 w-20">{t('payrollV2.novedades1')}</TableHead>
                            <TableHead className="font-bold text-right border-r bg-red-100 w-24">{t('payrollV2.deducciones')}</TableHead>
                            <TableHead className="font-bold text-right bg-emerald-100 w-24">{t('payrollV2.neto')}</TableHead>
                            {selectedPeriod.status !== 'paid' && <TableHead className="w-16"></TableHead>}
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {periodEntries.map((entry, index) => {
                            const totalOvertime = (entry.overtime_day_amount || 0) + (entry.overtime_night_amount || 0) + 
                              (entry.overtime_weekend_amount || 0) + (entry.overtime_holiday_amount || 0);
                            const novelties = entry.novelties || [];
                            
                            return (
                              <TableRow key={entry.entry_id} className="hover:bg-slate-50 dark:bg-slate-800">
                                <TableCell className="text-center border-r font-medium">{index + 1}</TableCell>
                                <TableCell className="border-r">
                                  <div><p className="font-medium text-[11px]">{entry.employee_name}</p>
                                    <p className="text-slate-500 dark:text-slate-400">{entry.position}</p>
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
                                <TableCell className="text-right border-r bg-emerald-50/50 text-emerald-600 dark:text-emerald-400">{formatNumber(totalOvertime)}</TableCell>
                                <TableCell className="text-right border-r bg-amber-50/50 text-amber-600 dark:text-amber-400">{formatNumber(entry.total_income_novelties || 0)}</TableCell>
                                <TableCell className="text-right border-r bg-slate-100 font-bold">{formatNumber(entry.gross_salary)}</TableCell>
                                <TableCell className="text-right border-r bg-red-50/50 text-red-600 dark:text-red-400">{formatNumber(entry.sfs_employee)}</TableCell>
                                <TableCell className="text-right border-r bg-red-50/50 text-red-600 dark:text-red-400">{formatNumber(entry.afp_employee)}</TableCell>
                                <TableCell className="text-right border-r bg-red-50/50 text-red-600 dark:text-red-400">{renderEditableCell(entry, 'isr', entry.isr)}</TableCell>
                                <TableCell className="text-right border-r bg-orange-50/50 text-orange-600">{formatNumber(entry.total_deduction_novelties || 0)}</TableCell>
                                <TableCell className="text-right border-r bg-red-100/50 font-bold text-red-700 dark:text-red-400">{formatNumber(entry.total_deductions)}</TableCell>
                                <TableCell className="text-right bg-emerald-100/50 font-bold text-emerald-700 dark:text-emerald-400">{formatNumber(entry.net_salary)}</TableCell>
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
                            <TableCell colSpan={3} className="text-right border-r">{t('payrollV2.totales')}</TableCell>
                            <TableCell className="text-right border-r font-mono">{formatNumber(totals.baseSalary)}</TableCell>
                            <TableCell className="text-right border-r font-mono">{formatNumber(totals.commissions)}</TableCell>
                            <TableCell className="text-right border-r font-mono">{formatNumber(totals.bonuses)}</TableCell>
                            <TableCell className="text-right border-r font-mono">{formatNumber(totals.overtimeDay + totals.overtimeNight + totals.overtimeWeekend + totals.overtimeHoliday)}</TableCell>
                            <TableCell className="text-right border-r font-mono text-amber-600 dark:text-amber-400">{formatNumber(totals.incomeNovelties)}</TableCell>
                            <TableCell className="text-right border-r font-mono">{formatNumber(totals.grossSalary)}</TableCell>
                            <TableCell className="text-right border-r font-mono text-red-600 dark:text-red-400">{formatNumber(totals.sfsEmployee)}</TableCell>
                            <TableCell className="text-right border-r font-mono text-red-600 dark:text-red-400">{formatNumber(totals.afpEmployee)}</TableCell>
                            <TableCell className="text-right border-r font-mono text-red-600 dark:text-red-400">{formatNumber(totals.isr)}</TableCell>
                            <TableCell className="text-right border-r font-mono text-orange-600">{formatNumber(totals.deductionNovelties)}</TableCell>
                            <TableCell className="text-right border-r font-mono text-red-700 dark:text-red-400">{formatNumber(totals.totalDeductions)}</TableCell>
                            <TableCell className="text-right font-mono text-emerald-700 dark:text-emerald-400">{formatNumber(totals.netSalary)}</TableCell>
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
              <CardHeader><CardTitle>{t('payrollV2.nominasPendientesDeAprobacion')}</CardTitle></CardHeader>
              <CardContent>
                {periods.filter(p => p.status === 'calculated').length === 0 ? (
                  <div className="text-center py-8 text-slate-500 dark:text-slate-400"><Check className="w-12 h-12 mx-auto mb-4 text-slate-300" /><p>{t('payrollV2.noHayPendientes')}</p></div>
                ) : (
                  <div className="space-y-3">
                    {periods.filter(p => p.status === 'calculated').map(period => (
                      <div key={period.period_id} className="flex items-center justify-between p-4 border rounded-lg">
                        <div><h4 className="font-semibold">{period.description}</h4><p className="text-sm text-slate-500 dark:text-slate-400">{period.employee_count} empleados • {formatCurrency(period.total_net)}</p></div>
                        <div className="flex gap-2">
                          <Button variant="outline" onClick={() => { setSelectedPeriod(period); setActiveTab('nomina'); }}>{t('payrollV2.ver')}</Button>
                          <Button onClick={() => handleApprovePeriod(period.period_id)}><Check className="w-4 h-4 mr-2" />{t('payrollV2.aprobar')}</Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle className="text-emerald-700 dark:text-emerald-400">{t('payrollV2.listosParaPagar')}</CardTitle></CardHeader>
              <CardContent>
                {periods.filter(p => p.status === 'approved').length === 0 ? (
                  <div className="text-center py-8 text-slate-500 dark:text-slate-400"><CreditCard className="w-12 h-12 mx-auto mb-4 text-slate-300" /><p>{t('payrollV2.noHayAprobados')}</p></div>
                ) : (
                  <div className="space-y-3">
                    {periods.filter(p => p.status === 'approved').map(period => (
                      <div key={period.period_id} className="flex items-center justify-between p-4 border border-emerald-200 bg-emerald-50 rounded-lg">
                        <div><h4 className="font-semibold text-emerald-800">{period.description}</h4><p className="text-sm text-emerald-600 dark:text-emerald-400">{period.employee_count} empleados • {formatCurrency(period.total_net)}</p></div>
                        <Button className="bg-emerald-600 hover:bg-emerald-700" onClick={() => openPayDialog(period)}><CreditCard className="w-4 h-4 mr-2" />{t('payrollV2.pagar')}</Button>
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
                <CardHeader><CardTitle>{t('payrollV2.exportarNominas')}</CardTitle><CardDescription>{t('payrollV2.descargaEnFormatoExcel')}</CardDescription></CardHeader>
                <CardContent>
                  {periods.filter(p => ['calculated', 'approved', 'paid'].includes(p.status)).length === 0 ? (
                    <p className="text-slate-500 text-center py-4">{t('payrollV2.noHayNominasPara')}</p>
                  ) : (
                    <div className="space-y-2">
                      {periods.filter(p => ['calculated', 'approved', 'paid'].includes(p.status)).map(period => (
                        <div key={period.period_id} className="flex items-center justify-between p-3 border rounded-lg">
                          <div><p className="font-medium">{period.description}</p>{getStatusBadge(period.status)}</div>
                          <div className="flex gap-2">
                            <Button variant="outline" size="sm" onClick={() => handleExportExcel(period.period_id)}><FileSpreadsheet className="w-4 h-4 mr-1" />{t('payrollV2.csv')}</Button>
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
                    <Shield className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                    Archivos TSS
                  </CardTitle>
                  <CardDescription>{t('payrollV2.tesoreriaDeLaSeguridad')}</CardDescription>
                </CardHeader>
                <CardContent>
                  {periods.filter(p => p.status === 'paid').length === 0 ? (
                    <p className="text-slate-500 text-center py-4">{t('payrollV2.pagueUnaNominaPara')}</p>
                  ) : (
                    <div className="space-y-3">
                      {periods.filter(p => p.status === 'paid').map(period => (
                        <div key={period.period_id} className="p-3 border rounded-lg bg-slate-50 dark:bg-slate-800">
                          <div className="flex items-center justify-between mb-2">
                            <div>
                              <p className="font-medium">{period.description}</p>
                              <p className="text-xs text-slate-500 dark:text-slate-400">{period.month}/{period.year} • {period.employee_count} empleados</p>
                            </div>
                            {getPayrollTypeBadge(period.payroll_type)}
                          </div>
                          <div className="flex gap-2 flex-wrap">
                            {period.payroll_type !== "OBREROS_NG" ? (
                              <>
                                <Button variant="outline" size="sm" className="text-emerald-600 border-emerald-200 hover:bg-emerald-50 dark:bg-emerald-900/30" 
                                  onClick={() => openTssPreview(period.period_id)}>
                                  <Eye className="w-4 h-4 mr-1" />Vista Previa
                                </Button>
                                <Button variant="outline" size="sm" className="text-blue-600 border-blue-200 hover:bg-blue-50 dark:bg-blue-900/30" 
                                  onClick={() => handleDownloadTSSAutodeterminacion(period.period_id)}>
                                  <Download className="w-4 h-4 mr-1" />Autodeterminación
                                </Button>
                                <Button variant="outline" size="sm" className="text-purple-600 border-purple-200 hover:bg-purple-50 dark:bg-purple-900/30"
                                  onClick={() => handleDownloadTSSNovedades(period.period_id)}>
                                  <Download className="w-4 h-4 mr-1" />Novedades
                                </Button>
                              </>
                            ) : (
                              <div className="text-sm text-amber-600 dark:text-amber-400 flex items-center gap-2">
                                <AlertCircle className="w-4 h-4" />
                                <span>{t('payrollV2.obrerosNgNoRequiere')}</span>
                              </div>
                            )}
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
                  <FileText className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                  Reportes DGII-TSS
                </CardTitle>
                <CardDescription>{t('payrollV2.formulariosIr3EIr17')}</CardDescription>
              </CardHeader>
              <CardContent>
                {periods.filter(p => p.status === 'paid').length === 0 ? (
                  <p className="text-slate-500 text-center py-4">{t('payrollV2.pagueUnaNominaPara1')}</p>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {periods.filter(p => p.status === 'paid').map(period => (
                      <div key={period.period_id} className="p-4 border rounded-lg bg-gradient-to-br from-emerald-50 to-white">
                        <div className="mb-3">
                          <p className="font-semibold text-emerald-800">{period.description}</p>
                          <p className="text-xs text-emerald-600 dark:text-emerald-400">{formatCurrency(period.total_net)} pagado</p>
                        </div>
                        <div className="space-y-2">
                          <Button variant="outline" size="sm" className="w-full justify-start text-emerald-700 border-emerald-200 hover:bg-emerald-100 dark:bg-emerald-900/50"
                            onClick={() => handleDownloadIR3(period.period_id)}>
                            <Download className="w-4 h-4 mr-2" />
                            <span>{t('payrollV2.ir3')}</span>
                            <span className="ml-auto text-xs text-emerald-500">{t('payrollV2.retenciones')}</span>
                          </Button>
                          <Button variant="outline" size="sm" className="w-full justify-start text-emerald-700 border-emerald-200 hover:bg-emerald-100 dark:bg-emerald-900/50"
                            onClick={() => handleDownloadIR17(period.period_id)}>
                            <Download className="w-4 h-4 mr-2" />
                            <span>{t('payrollV2.ir17')}</span>
                            <span className="ml-auto text-xs text-emerald-500">{t('payrollV2.declaracion')}</span>
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
            <DialogHeader><DialogTitle>{t('payrollV2.crearNuevaNomina')}</DialogTitle><DialogDescription>{t('payrollV2.defineElTipoY')}</DialogDescription></DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>{t('payrollV2.tipoDeNomina')}</Label>
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
                <div className="space-y-2"><Label>{t('payrollV2.periodo')}</Label>
                  <Select value={newPeriodForm.period_type} onValueChange={(v) => setNewPeriodForm({...newPeriodForm, period_type: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>{periodTypes.map(type => (<SelectItem key={type.value} value={type.value}>{type.label}</SelectItem>))}</SelectContent>
                  </Select>
                </div>
                <div className="space-y-2"><Label>{t('payrollV2.departamentoOpcional')}</Label>
                  <Select value={newPeriodForm.department_filter} onValueChange={(v) => setNewPeriodForm({...newPeriodForm, department_filter: v})}>
                    <SelectTrigger><SelectValue placeholder="Todos" /></SelectTrigger>
                    <SelectContent><SelectItem value="all">{t('payrollV2.todosLosDepartamentos')}</SelectItem>
                      {departments.map(d => (<SelectItem key={d} value={d}>{d}</SelectItem>))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2"><Label>{t('payrollV2.ano')}</Label>
                  <Select value={String(newPeriodForm.year)} onValueChange={(v) => setNewPeriodForm({...newPeriodForm, year: parseInt(v)})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>{[2024, 2025, 2026, 2027].map(year => (<SelectItem key={year} value={String(year)}>{year}</SelectItem>))}</SelectContent>
                  </Select>
                </div>
                <div className="space-y-2"><Label>{t('payrollV2.mes')}</Label>
                  <Select value={String(newPeriodForm.month)} onValueChange={(v) => setNewPeriodForm({...newPeriodForm, month: parseInt(v)})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>{months.map(m => (<SelectItem key={m.value} value={String(m.value)}>{m.label}</SelectItem>))}</SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2"><Label>{t('payrollV2.fechaInicio')}</Label><Input type="date" value={newPeriodForm.start_date} onChange={(e) => setNewPeriodForm({...newPeriodForm, start_date: e.target.value})} /></div>
                <div className="space-y-2"><Label>{t('payrollV2.fechaFin')}</Label><Input type="date" value={newPeriodForm.end_date} onChange={(e) => setNewPeriodForm({...newPeriodForm, end_date: e.target.value})} /></div>
              </div>
              <div className="space-y-2"><Label>{t('payrollV2.descripcion')}</Label><Input value={newPeriodForm.description} onChange={(e) => setNewPeriodForm({...newPeriodForm, description: e.target.value})} placeholder="Ej: Nómina Quincenal Enero 2026" /></div>
            </div>
            <DialogFooter><Button variant="outline" onClick={() => setShowNewPeriod(false)}>{t('payrollV2.cancelar')}</Button><Button onClick={handleCreatePeriod}>{t('payrollV2.crearNomina')}</Button></DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Pay Dialog */}
        <Dialog open={showPayDialog} onOpenChange={setShowPayDialog}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Wallet className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                Pagar Nómina
              </DialogTitle>
              <DialogDescription>{t('payrollV2.configureElPagoY')}</DialogDescription>
            </DialogHeader>
            {selectedPeriod && (
              <div className="space-y-4">
                <div className="p-4 bg-slate-50 rounded-lg">
                  <p className="font-semibold">{selectedPeriod.description}</p>
                  <p className="text-sm text-slate-500 mt-1">{selectedPeriod.employee_count} empleados</p>
                  <div className="mt-3 p-3 bg-emerald-100 rounded-lg">
                    <p className="text-sm text-emerald-700 dark:text-emerald-400">{t('payrollV2.totalAPagar')}</p>
                    <p className="text-2xl font-bold text-emerald-800">{formatCurrency(selectedPeriod.total_net)}</p>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label>{t('payrollV2.cuentaContable')}</Label>
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
                      <Label className="text-sm">{t('payrollV2.bancoParaArchivoDe')}</Label>
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
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        Se descargará automáticamente el archivo para carga en el banco
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowPayDialog(false)}>{t('payrollV2.cancelar')}</Button>
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
            <DialogHeader><DialogTitle>{t('payrollV2.agregarNovedad')}</DialogTitle>
              <DialogDescription>{t('payrollV2.agregueUnIngresoODeduccion', {name: selectedEntry?.employee_name})}</DialogDescription></DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <Button variant={noveltyForm.novelty_type === 'income' ? 'default' : 'outline'} className="h-auto py-3 flex flex-col"
                  onClick={() => setNoveltyForm({...noveltyForm, novelty_type: 'income', code: '', name: ''})}>
                  <PlusCircle className="w-5 h-5 mb-1 text-emerald-500" /><span>{t('payrollV2.ingreso')}</span>
                </Button>
                <Button variant={noveltyForm.novelty_type === 'deduction' ? 'default' : 'outline'} className="h-auto py-3 flex flex-col"
                  onClick={() => setNoveltyForm({...noveltyForm, novelty_type: 'deduction', code: '', name: ''})}>
                  <MinusCircle className="w-5 h-5 mb-1 text-red-500" /><span>{t('payrollV2.deduccion')}</span>
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
              <div className="space-y-2"><Label>{t('payrollV2.montoRd')}</Label>
                <Input type="number" step="0.01" value={noveltyForm.amount} onChange={(e) => setNoveltyForm({...noveltyForm, amount: e.target.value})} placeholder="0.00" />
              </div>
              <div className="space-y-2"><Label>{t('payrollV2.descripcionOpcional')}</Label>
                <Input value={noveltyForm.description} onChange={(e) => setNoveltyForm({...noveltyForm, description: e.target.value})} placeholder="Ej: Comisión ventas enero" />
              </div>
            </div>
            <DialogFooter><Button variant="outline" onClick={() => setShowNoveltyDialog(false)}>{t('payrollV2.cancelar')}</Button>
              <Button onClick={handleAddNovelty}><Plus className="w-4 h-4 mr-2" />{t('payrollV2.agregarNovedad')}</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* TSS Preview Modal */}
        <Dialog open={showTssPreview} onOpenChange={setShowTssPreview}>
          <DialogContent className="max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5 text-blue-600" />
                Vista Previa - Reporte TSS
              </DialogTitle>
              <DialogDescription>
                Autodeterminación Mensual para SUIR+ (Tesorería de Seguridad Social)
              </DialogDescription>
            </DialogHeader>

            {tssLoading ? (
              <div className="flex items-center justify-center py-12">
                <RefreshCw className="w-8 h-8 animate-spin text-slate-400" />
              </div>
            ) : tssPreviewData?.error ? (
              <div className="text-center py-8">
                <AlertCircle className="w-12 h-12 mx-auto text-amber-500 mb-4" />
                <h3 className="font-semibold text-lg mb-2">{tssPreviewData.message}</h3>
                <p className="text-slate-500">{tssPreviewData.reason}</p>
              </div>
            ) : tssPreviewData ? (
              <div className="flex-1 overflow-auto min-h-0 space-y-4">
                {/* Company and Period Info */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                  <div>
                    <span className="text-xs text-slate-500">{t('payrollV2.empresa')}</span>
                    <p className="font-medium">{tssPreviewData.company?.name}</p>
                  </div>
                  <div>
                    <span className="text-xs text-slate-500">{t('payrollV2.rnc')}</span>
                    <p className="font-mono">{tssPreviewData.company?.rnc}</p>
                  </div>
                  <div>
                    <span className="text-xs text-slate-500">{t('payrollV2.periodo')}</span>
                    <p className="font-medium">{tssPreviewData.period?.month}/{tssPreviewData.period?.year}</p>
                  </div>
                  <div>
                    <span className="text-xs text-slate-500">{t('payrollV2.empleados')}</span>
                    <p className="font-medium">{tssPreviewData.employee_count}</p>
                  </div>
                </div>

                {/* Rates Info */}
                <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-sm">
                  <p className="font-medium text-blue-800 dark:text-blue-200 mb-2">{t('payrollV2.tasasAplicadas')}</p>
                  <div className="grid grid-cols-3 md:grid-cols-6 gap-2 text-blue-700 dark:text-blue-300">
                    <span>SFS Emp: {tssPreviewData.rates?.sfs_empleado}</span>
                    <span>AFP Emp: {tssPreviewData.rates?.afp_empleado}</span>
                    <span>SFS Pat: {tssPreviewData.rates?.sfs_patronal}</span>
                    <span>AFP Pat: {tssPreviewData.rates?.afp_patronal}</span>
                    <span>SRL: {tssPreviewData.rates?.srl}</span>
                    <span>INFOTEP: {tssPreviewData.rates?.infotep}</span>
                  </div>
                </div>

                {/* Employee Table */}
                <div className="border rounded-lg overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-slate-100 dark:bg-slate-800">
                        <TableHead>{t('payrollV2.cedula1')}</TableHead>
                        <TableHead>{t('payrollV2.nombre')}</TableHead>
                        <TableHead className="text-right">{t('payrollV2.salarioCot')}</TableHead>
                        <TableHead className="text-right">{t('payrollV2.sfsEmp')}</TableHead>
                        <TableHead className="text-right">{t('payrollV2.afpEmp')}</TableHead>
                        <TableHead className="text-right">{t('payrollV2.sfsPat')}</TableHead>
                        <TableHead className="text-right">{t('payrollV2.afpPat')}</TableHead>
                        <TableHead className="text-right">{t('payrollV2.srl')}</TableHead>
                        <TableHead className="text-right">{t('payrollV2.infotep')}</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {tssPreviewData.employees?.map((emp, idx) => (
                        <TableRow key={idx}>
                          <TableCell className="font-mono text-sm">{emp.cedula}</TableCell>
                          <TableCell>{emp.nombre}</TableCell>
                          <TableCell className="text-right font-mono">{formatCurrency(emp.salario_cotizable)}</TableCell>
                          <TableCell className="text-right font-mono text-blue-600">{formatCurrency(emp.sfs_empleado)}</TableCell>
                          <TableCell className="text-right font-mono text-blue-600">{formatCurrency(emp.afp_empleado)}</TableCell>
                          <TableCell className="text-right font-mono text-emerald-600">{formatCurrency(emp.sfs_patronal)}</TableCell>
                          <TableCell className="text-right font-mono text-emerald-600">{formatCurrency(emp.afp_patronal)}</TableCell>
                          <TableCell className="text-right font-mono text-emerald-600">{formatCurrency(emp.srl)}</TableCell>
                          <TableCell className="text-right font-mono text-emerald-600">{formatCurrency(emp.infotep)}</TableCell>
                        </TableRow>
                      ))}
                      {/* Totals Row */}
                      <TableRow className="bg-slate-100 dark:bg-slate-800 font-bold border-t-2">
                        <TableCell colSpan={2} className="text-right">{t('payrollV2.totales1')}</TableCell>
                        <TableCell className="text-right font-mono">{formatCurrency(tssPreviewData.totals?.salario_cotizable)}</TableCell>
                        <TableCell className="text-right font-mono text-blue-600">{formatCurrency(tssPreviewData.totals?.sfs_empleado)}</TableCell>
                        <TableCell className="text-right font-mono text-blue-600">{formatCurrency(tssPreviewData.totals?.afp_empleado)}</TableCell>
                        <TableCell className="text-right font-mono text-emerald-600">{formatCurrency(tssPreviewData.totals?.sfs_patronal)}</TableCell>
                        <TableCell className="text-right font-mono text-emerald-600">{formatCurrency(tssPreviewData.totals?.afp_patronal)}</TableCell>
                        <TableCell className="text-right font-mono text-emerald-600">{formatCurrency(tssPreviewData.totals?.srl)}</TableCell>
                        <TableCell className="text-right font-mono text-emerald-600">{formatCurrency(tssPreviewData.totals?.infotep)}</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </div>

                {/* Summary Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <Card className="border-l-4 border-l-blue-500">
                    <CardContent className="p-3">
                      <p className="text-xs text-slate-500">{t('payrollV2.totalAportesEmpleado')}</p>
                      <p className="text-lg font-bold text-blue-600">{formatCurrency(tssPreviewData.totals?.total_empleado)}</p>
                    </CardContent>
                  </Card>
                  <Card className="border-l-4 border-l-emerald-500">
                    <CardContent className="p-3">
                      <p className="text-xs text-slate-500">{t('payrollV2.totalAportesPatronal')}</p>
                      <p className="text-lg font-bold text-emerald-600">{formatCurrency(tssPreviewData.totals?.total_patronal)}</p>
                    </CardContent>
                  </Card>
                  <Card className="border-l-4 border-l-purple-500">
                    <CardContent className="p-3">
                      <p className="text-xs text-slate-500">{t('payrollV2.totalAPagarTss')}</p>
                      <p className="text-lg font-bold text-purple-600">{formatCurrency((tssPreviewData.totals?.total_empleado || 0) + (tssPreviewData.totals?.total_patronal || 0))}</p>
                    </CardContent>
                  </Card>
                  <Card className="border-l-4 border-l-slate-500">
                    <CardContent className="p-3">
                      <p className="text-xs text-slate-500">{t('payrollV2.archivo')}</p>
                      <p className="text-sm font-mono truncate">{tssPreviewData.filename}</p>
                    </CardContent>
                  </Card>
                </div>
              </div>
            ) : null}

            <DialogFooter className="border-t pt-4">
              <Button variant="outline" onClick={() => setShowTssPreview(false)}>
                Cerrar
              </Button>
              {tssPreviewData && !tssPreviewData.error && (
                <Button onClick={() => downloadTssReport(selectedPeriod?.period_id)}>
                  <Download className="w-4 h-4 mr-2" />
                  Descargar TXT (SUIR+)
                </Button>
              )}
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Drill-Down Modal */}
        <DrillDownModal
          open={drillDown.open}
          onClose={closeDrillDown}
          title={drillDown.title}
          data={drillDown.data}
          columns={drillDown.columns}
          loading={drillDownLoading}
        />
      </div>
    </DashboardLayout>
  );
}
