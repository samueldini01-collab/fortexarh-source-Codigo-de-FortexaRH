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
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import PayrollColumnsPicker from "@/components/payroll/PayrollColumnsPicker";
import { buildPayrollColumns } from "@/components/payroll/payrollColumns";
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
  FileDown,
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
  Send,
  BookOpen,
  GitBranch,
  Globe
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
  const [editingNoveltyId, setEditingNoveltyId] = useState(null);

  // ----- Payroll Sheet — customizable columns -------------------------------
  // We build the catalog inside render to capture latest t / countryRates /
  // renderEditableCell, but the column STATE (order + visibility) is stable.
  const COLUMNS_STORAGE_KEY = "payroll-sheet-cols-v1";

  const [columnsState, setColumnsState] = useState(() => {
    try {
      const raw = localStorage.getItem(COLUMNS_STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed && Array.isArray(parsed.order) && parsed.visible) return parsed;
      }
    } catch { /* ignore */ }
    return null; // sentinel — will hydrate from defaults on first render
  });

  const saveColumnsState = (state) => {
    setColumnsState(state);
    try { localStorage.setItem(COLUMNS_STORAGE_KEY, JSON.stringify(state)); } catch { /* ignore */ }
  };

  const resetColumns = () => {
    try { localStorage.removeItem(COLUMNS_STORAGE_KEY); } catch { /* ignore */ }
    setColumnsState(null);
  };
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

  // ACH Bank File states
  const [showAchDialog, setShowAchDialog] = useState(false);
  const [achBank, setAchBank] = useState("banreservas");
  const [achPreview, setAchPreview] = useState(null);
  const [achLoading, setAchLoading] = useState(false);

  // Workflow status for selected period
  const [workflowStatus, setWorkflowStatus] = useState(null);

  // Deductions Detail Dialog
  const [showDeductionsDialog, setShowDeductionsDialog] = useState(false);
  const [deductionsEntry, setDeductionsEntry] = useState(null);
  const [deductionsForm, setDeductionsForm] = useState({
    sfs_override: null,
    afp_override: null,
    isr_override: null,
    additional_deductions: []
  });
  const [newPayrollDeduction, setNewPayrollDeduction] = useState({ type: "Préstamo Empresa", description: "", amount: "", is_percentage: false });
  const [savingDeductions, setSavingDeductions] = useState(false);
  
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
      
      // Fetch workflow status for this period
      try {
        const wfRes = await axios.get(`${API}/payroll/periods/${periodId}/workflow-status`, { headers: getAuthHeaders(), withCredentials: true });
        setWorkflowStatus(wfRes.data);
      } catch (_) {
        setWorkflowStatus(null);
      }
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

  // Multi-country payroll rates (labels + codes + rates per company country)
  const [countryRates, setCountryRates] = useState(null);
  const fetchCountryRates = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/country-config/rates-flat`, { headers: getAuthHeaders(), withCredentials: true });
      setCountryRates(response.data);
    } catch (_error) {
      // Fallback: null → UI uses default DR i18n labels
    }
  }, [getAuthHeaders]);

  // Helper: get deduction label for a DB field, preferring country profile code when not DR
  const getDeductionLabel = useCallback((field, fallbackI18nKey) => {
    if (countryRates?.country_code && countryRates.country_code !== 'DO') {
      const code = countryRates?.codes?.[field];
      if (code) return code;
    }
    return t(fallbackI18nKey);
  }, [countryRates, t]);

  const getDeductionRatePct = useCallback((field) => {
    const rateMap = {
      sfs_employee: countryRates?.sfs_employee_rate,
      afp_employee: countryRates?.afp_employee_rate,
      sfs_employer: countryRates?.sfs_employer_rate,
      afp_employer: countryRates?.afp_employer_rate,
      srl_employer: countryRates?.srl_employer_rate,
      infotep_employer: countryRates?.infotep_employer_rate,
    };
    const r = rateMap[field];
    if (r === undefined || r === null) return '';
    return `${(r * 100).toFixed(2)}%`;
  }, [countryRates]);

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

  // Download universal fiscal summary (multi-country) - works for all 29 countries
  const downloadUniversalFiscalReport = async (period, format) => {
    try {
      const periodParam = period?.period_id || (period?.year && period?.month ? `${period.year}-${String(period.month).padStart(2, '0')}` : '');
      if (!periodParam) {
        toast.error('Período inválido');
        return;
      }
      const response = await axios.get(
        `${API}/multi-country-reports/fiscal-summary?period=${encodeURIComponent(periodParam)}&format=${format}`,
        { headers: getAuthHeaders(), withCredentials: true, responseType: 'blob' }
      );
      const mimeType = format === 'pdf' ? 'application/pdf' : 'text/csv';
      const blob = new Blob([response.data], { type: `${mimeType};charset=utf-8` });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      const countryCode = countryRates?.country_code || 'DO';
      link.download = `FiscalSummary_${countryCode}_${periodParam}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      toast.success(`Reporte fiscal (${format.toUpperCase()}) descargado`);
    } catch (error) {
      const msg = error.response?.status === 404 ? 'No hay datos de nómina para este período'
                : error.response?.data?.detail || 'Error al descargar reporte';
      toast.error(msg);
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
    fetchCountryRates();
    if (user?.company_name) setCompanyName(user.company_name);
  }, [fetchPeriods, fetchBankAccounts, fetchNoveltyTypes, fetchCompanySettings, fetchCountryRates, user?.company_name]);

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
    if (!confirm(t('payrollV2.recalcConfirm', { defaultValue: '¿Recalcular todas las entradas del período? Esto refrescará SFS, AFP, ISR y el neto en base a las novedades, salarios y configuración actuales.' }))) return;
    try {
      const res = await axios.post(`${API}/payroll/periods/${periodId}/calculate`, {}, { headers: getAuthHeaders(), withCredentials: true });
      const count = res?.data?.recalculated ?? '';
      toast.success(count
        ? t('payrollV2.messages.payrollsCalculatedCount', { count, defaultValue: `${count} entradas recalculadas` })
        : t('payrollV2.messages.payrollsCalculated'));
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

  const [bankCheckWarning, setBankCheckWarning] = useState(null);
  const [showBankWarningDialog, setShowBankWarningDialog] = useState(false);
  const [pendingApprovalPeriodId, setPendingApprovalPeriodId] = useState(null);

  const handleApprovePeriod = async (periodId) => {
    // First check bank info
    try {
      const checkRes = await axios.get(`${API}/payroll/periods/${periodId}/bank-check`, { headers: getAuthHeaders(), withCredentials: true });
      const data = checkRes.data;
      
      if (data.missing_count > 0) {
        setBankCheckWarning(data);
        setPendingApprovalPeriodId(periodId);
        setShowBankWarningDialog(true);
        return;
      }
    } catch (err) {
      // If check fails, proceed without warning
    }
    
    await executeApproval(periodId);
  };

  const executeApproval = async (periodId) => {
    try {
      const res = await axios.post(`${API}/payroll/periods/${periodId}/approve`, {}, { headers: getAuthHeaders(), withCredentials: true });
      
      if (res.data.status === "workflow_pending") {
        // Intermediate step approved, not final
        toast.success(res.data.message);
        fetchPeriods();
        if (selectedPeriod?.period_id === periodId) {
          setSelectedPeriod(prev => ({ ...prev, status: 'workflow_pending' }));
          fetchPeriodDetails(periodId);
        }
      } else {
        toast.success(t('payrollV2.messages.periodApproved'));
        if (res.data.bank_warning) {
          const w = res.data.bank_warning;
          toast.warning(`${w.missing_count} empleados sin datos bancarios`, { duration: 5000 });
        }
        fetchPeriods();
        if (selectedPeriod?.period_id === periodId) {
          setSelectedPeriod(prev => ({ ...prev, status: 'approved' }));
          fetchPeriodDetails(periodId);
        }
      }
      
      setShowBankWarningDialog(false);
      setBankCheckWarning(null);
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

  // ACH Bank File functions
  const openAchDialog = async (period) => {
    setSelectedPeriod(period);
    setShowAchDialog(true);
    setAchLoading(true);
    try {
      const response = await axios.get(
        `${API}/bank-files/preview/${period.period_id}/${achBank}`,
        { headers: getAuthHeaders(), withCredentials: true }
      );
      setAchPreview(response.data);
    } catch (error) {
      toast.error("Error al cargar vista previa ACH");
    } finally {
      setAchLoading(false);
    }
  };

  const handleAchBankChange = async (bankId) => {
    setAchBank(bankId);
    if (!selectedPeriod) return;
    setAchLoading(true);
    try {
      const response = await axios.get(
        `${API}/bank-files/preview/${selectedPeriod.period_id}/${bankId}`,
        { headers: getAuthHeaders(), withCredentials: true }
      );
      setAchPreview(response.data);
    } catch (error) {
      toast.error("Error al cargar vista previa");
    } finally {
      setAchLoading(false);
    }
  };

  const handleDownloadAch = async () => {
    if (!selectedPeriod) return;
    try {
      const response = await axios.get(
        `${API}/bank-files/generate/${selectedPeriod.period_id}/${achBank}`,
        { headers: getAuthHeaders(), withCredentials: true, responseType: 'blob' }
      );
      const ext = achBank === 'banreservas' ? 'csv' : 'txt';
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `ACH_${achBank}_${selectedPeriod.description || selectedPeriod.period_id}.${ext}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      toast.success(`Archivo ACH ${achBank} descargado`);
      setShowAchDialog(false);
    } catch (error) {
      const detail = error.response?.data;
      if (detail instanceof Blob) {
        const text = await detail.text();
        try { toast.error(JSON.parse(text).detail); } catch { toast.error("Error al generar archivo ACH"); }
      } else {
        toast.error(error.response?.data?.detail || "Error al generar archivo ACH");
      }
    }
  };

  const handleGenerateJE = async (periodId) => {
    try {
      const res = await axios.post(`${API}/payroll/periods/${periodId}/generate-je`, {}, { headers: getAuthHeaders(), withCredentials: true });
      toast.success(res.data.message || "Asiento generado");
      fetchPeriodDetails(periodId);

      fetchPeriods();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al generar asiento");
    }
  };

  const handleDeleteJE = async (periodId) => {
    if (!confirm("¿Eliminar el asiento de diario vinculado a este período?")) return;
    try {
      const res = await axios.delete(`${API}/payroll/periods/${periodId}/journal-entry`, { headers: getAuthHeaders(), withCredentials: true });
      toast.success(res.data.message || "Asiento eliminado");
      fetchPeriodDetails(periodId);
      fetchPeriods();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al eliminar asiento");
    }
  };

  const handleDeletePeriod = async (periodId) => {
    const period = periods.find(p => p.period_id === periodId) || selectedPeriod;
    const isPaid = period?.status === 'paid';
    const hasJE = !!period?.journal_entry_id;
    
    let msg = t('payrollV2.confirmDeletePeriod');
    if (isPaid && hasJE) {
      msg = t('payrollV2.confirmDeletePaidWithJE');
    } else if (isPaid) {
      msg = t('payrollV2.confirmDeletePaid');
    }
    
    if (!confirm(msg)) return;
    try {
      await axios.delete(`${API}/payroll/periods/${periodId}`, { headers: getAuthHeaders(), withCredentials: true });
      toast.success(isPaid && hasJE ? t('payrollV2.messages.periodAndJEDeleted') : t('payrollV2.messages.periodDeleted'));
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

      // Map field to override parameter for backend
      if (editingCell.field === 'isr') {
        updateData.isr_override = numValue;
      } else if (editingCell.field === 'sfs_employee') {
        updateData.sfs_override = numValue;
      } else if (editingCell.field === 'afp_employee') {
        updateData.afp_override = numValue;
      } else if (editingCell.field === 'overtime_total') {
        updateData.overtime_override = numValue;
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

  // Deductions Detail Dialog handlers
  const openDeductionsDialog = (entry) => {
    if (selectedPeriod?.status === 'paid') return;
    setDeductionsEntry(entry);
    setDeductionsForm({
      sfs_override: entry.sfs_employee || 0,
      afp_override: entry.afp_employee || 0,
      isr_override: entry.isr || 0,
      additional_deductions: (entry.additional_deductions || []).map(d => ({ ...d }))
    });
    setNewPayrollDeduction({ type: "Préstamo Empresa", description: "", amount: "", is_percentage: false });
    setShowDeductionsDialog(true);
  };

  const addPayrollDeduction = () => {
    if (!newPayrollDeduction.amount) return;
    setDeductionsForm(prev => ({
      ...prev,
      additional_deductions: [...prev.additional_deductions, { ...newPayrollDeduction, amount: parseFloat(newPayrollDeduction.amount) || 0 }]
    }));
    setNewPayrollDeduction({ type: "Préstamo Empresa", description: "", amount: "", is_percentage: false });
  };

  const removePayrollDeduction = (index) => {
    setDeductionsForm(prev => ({
      ...prev,
      additional_deductions: prev.additional_deductions.filter((_, i) => i !== index)
    }));
  };

  const saveDeductions = async () => {
    if (!deductionsEntry) return;
    setSavingDeductions(true);
    try {
      const updateData = {
        period_id: deductionsEntry.period_id,
        employee_id: deductionsEntry.employee_id,
        base_salary: deductionsEntry.base_salary,
        overtime_day_hours: deductionsEntry.overtime_day_hours || 0,
        overtime_night_hours: deductionsEntry.overtime_night_hours || 0,
        overtime_weekend_hours: deductionsEntry.overtime_weekend_hours || 0,
        overtime_holiday_hours: deductionsEntry.overtime_holiday_hours || 0,
        bonuses: deductionsEntry.bonuses || 0,
        commissions: deductionsEntry.commissions || 0,
        sfs_override: parseFloat(deductionsForm.sfs_override) || 0,
        afp_override: parseFloat(deductionsForm.afp_override) || 0,
        isr_override: parseFloat(deductionsForm.isr_override) || 0,
        additional_deductions: deductionsForm.additional_deductions
      };
      await axios.put(`${API}/payroll/entries/${deductionsEntry.entry_id}`, updateData, { headers: getAuthHeaders(), withCredentials: true });
      toast.success(t('payrollV2.messages.deductionsUpdated'));
      setShowDeductionsDialog(false);
      fetchPeriodDetails(deductionsEntry.period_id);
      fetchPeriods();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    } finally {
      setSavingDeductions(false);
    }
  };

  // Download individual payslip PDF
  const handleDownloadPayslip = async (entryId) => {
    try {
      const response = await axios.get(`${API}/payroll/payslip/${entryId}/pdf`, {
        headers: getAuthHeaders(),
        withCredentials: true,
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `recibo_nomina_${entryId}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      toast.success(t('payrollV2.messages.payslipDownloaded'));
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    }
  };

  // Novelty handlers
  const openNoveltyDialog = (entry) => {
    setSelectedEntry(entry);
    setEditingNoveltyId(null);
    setNoveltyForm({ novelty_type: "income", code: "", name: "", description: "", amount: "", is_percentage: false });
    setShowNoveltyDialog(true);
  };

  const openEditNoveltyDialog = (entry, novelty) => {
    if (!novelty) return;
    setSelectedEntry(entry);
    setEditingNoveltyId(novelty.novelty_id);
    setNoveltyForm({
      novelty_type: novelty.novelty_type || "income",
      code: novelty.code || "",
      name: novelty.name || "",
      description: novelty.description || "",
      amount: novelty.amount ?? "",
      is_percentage: !!novelty.is_percentage,
    });
    setShowNoveltyDialog(true);
  };

  const handleSaveNovelty = async () => {
    if (!selectedEntry || !noveltyForm.code || noveltyForm.amount === "" || noveltyForm.amount === null) {
      toast.error(t('payrollV2.messages.completeRequiredFields'));
      return;
    }
    const payload = {
      entry_id: selectedEntry.entry_id,
      ...noveltyForm,
      amount: parseFloat(noveltyForm.amount) || 0,
    };
    try {
      if (editingNoveltyId) {
        await axios.patch(
          `${API}/payroll/entries/${selectedEntry.entry_id}/novelties/${editingNoveltyId}`,
          payload,
          { headers: getAuthHeaders(), withCredentials: true },
        );
        toast.success(t('payrollV2.messages.noveltyUpdated', { defaultValue: 'Novedad actualizada' }));
      } else {
        await axios.post(
          `${API}/payroll/entries/${selectedEntry.entry_id}/novelties`,
          payload,
          { headers: getAuthHeaders(), withCredentials: true },
        );
        toast.success(t('payrollV2.messages.noveltyAdded'));
      }
      setShowNoveltyDialog(false);
      setEditingNoveltyId(null);
      fetchPeriodDetails(selectedEntry.period_id);
      fetchPeriods();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error");
    }
  };

  // Kept for backwards-compat with any external caller
  const handleAddNovelty = handleSaveNovelty;

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
      const response = await axios.get(
        `${API}/payroll/periods/${periodId}/export/excel`,
        { headers: getAuthHeaders(), withCredentials: true, responseType: 'blob' }
      );

      // Try to pull the filename from Content-Disposition; fall back to period id
      let filename = `nomina_${periodId}.xlsx`;
      const cd = response.headers?.['content-disposition'] || response.headers?.['Content-Disposition'];
      if (cd) {
        const m = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(cd);
        if (m && m[1]) filename = decodeURIComponent(m[1]);
      }

      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(link.href);
      toast.success(t('payrollV2.messages.excelExported'));
    } catch (error) {
      console.error("Export error:", error);
      const detail = error.response?.data instanceof Blob
        ? await error.response.data.text().catch(() => '')
        : error.response?.data?.detail;
      toast.error(detail || t('payrollV2.messages.errorExporting'));
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
      'workflow_pending': <Badge className="bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">Aprobación en Curso</Badge>,
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
        onClick={() => canEdit && startEditing(entry.entry_id, field, value)} title={canEdit ? "Clic para editar" : ""}
        data-testid={`editable-${field}-${entry.entry_id}`}>
        {isCurrency ? formatNumber(value) : value}
      </span>
    );
  };

  // Editable cell for novelty CODE columns (INC, HED, COOP, ANTIC, etc.).
  // Smart behavior:
  //   - 0 novelties for that code → POST a new novelty
  //   - 1 novelty (non-percentage) → PATCH it, or DELETE if value becomes 0
  //   - 2+ novelties → open the novelties dialog instead of inline editing
  const renderEditableCodeCell = (entry, code, noveltyType, codeName, sum) => {
    const fieldKey = `novelty:${noveltyType}:${code}`;
    const isEditing = editingCell?.entryId === entry.entry_id && editingCell?.field === fieldKey;
    const canEdit = selectedPeriod?.status !== 'paid';
    const matching = (entry.novelties || []).filter(n => n?.code === code && n?.novelty_type === noveltyType);
    const hasMultiple = matching.length > 1;
    const hasPercentage = matching.some(n => n.is_percentage);

    if (isEditing) {
      return (
        <div className="flex items-center gap-1">
          <Input type="number" step="0.01" className="w-20 h-6 text-right text-xs" value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') saveCodeNoveltyEdit(); if (e.key === 'Escape') cancelEditing(); }}
            autoFocus
          />
          <Button size="icon" variant="ghost" className="h-5 w-5" onClick={saveCodeNoveltyEdit} data-testid={`save-code-${code}-${entry.entry_id}`}><Check className="w-3 h-3 text-emerald-600 dark:text-emerald-400" /></Button>
          <Button size="icon" variant="ghost" className="h-5 w-5" onClick={cancelEditing}><X className="w-3 h-3 text-red-500" /></Button>
        </div>
      );
    }

    const onClick = () => {
      if (!canEdit) return;
      if (hasMultiple) {
        toast.info(`${matching.length} novedades ${code}. Edítalas individualmente desde el detalle.`);
        return;
      }
      if (hasPercentage) {
        toast.info(`Esta novedad ${code} está en %. Edítala desde el detalle.`);
        return;
      }
      const existing = matching[0];
      setEditingCell({
        entryId: entry.entry_id,
        field: fieldKey,
        code,
        noveltyType,
        codeName,
        existingNoveltyId: existing?.novelty_id || null,
      });
      setEditValue(String(sum || 0));
    };

    const tooltipText = !canEdit
      ? ''
      : hasMultiple
        ? `${matching.length} novedades — usa el detalle`
        : hasPercentage
          ? 'Novedad en % — usa el detalle'
          : matching[0]
            ? 'Clic para editar'
            : 'Clic para agregar';

    return (
      <span
        className={`font-mono text-[10px] ${canEdit ? 'cursor-pointer hover:bg-blue-50 px-1 rounded' : ''} ${hasMultiple ? 'underline decoration-dotted decoration-orange-400' : ''}`}
        onClick={onClick}
        title={tooltipText}
        data-testid={`code-cell-${code}-${entry.entry_id}`}
      >
        {formatNumber(sum)}
        {hasMultiple && <sup className="ml-0.5 text-[8px] text-orange-500">×{matching.length}</sup>}
      </span>
    );
  };

  const saveCodeNoveltyEdit = async () => {
    if (!editingCell || !editingCell.code) return;
    const entry = periodEntries.find(e => e.entry_id === editingCell.entryId);
    if (!entry) return;
    const numValue = parseFloat(editValue) || 0;
    const { code, noveltyType, codeName, existingNoveltyId } = editingCell;
    try {
      if (existingNoveltyId) {
        if (numValue === 0) {
          await axios.delete(
            `${API}/payroll/entries/${entry.entry_id}/novelties/${existingNoveltyId}`,
            { headers: getAuthHeaders(), withCredentials: true }
          );
        } else {
          await axios.patch(
            `${API}/payroll/entries/${entry.entry_id}/novelties/${existingNoveltyId}`,
            {
              entry_id: entry.entry_id,
              novelty_type: noveltyType,
              code,
              name: codeName || code,
              description: "",
              amount: numValue,
              is_percentage: false,
            },
            { headers: getAuthHeaders(), withCredentials: true }
          );
        }
      } else if (numValue > 0) {
        await axios.post(
          `${API}/payroll/entries/${entry.entry_id}/novelties`,
          {
            entry_id: entry.entry_id,
            novelty_type: noveltyType,
            code,
            name: codeName || code,
            description: "",
            amount: numValue,
            is_percentage: false,
          },
          { headers: getAuthHeaders(), withCredentials: true }
        );
      }
      toast.success(t('payrollV2.messages.updated'));
      fetchPeriodDetails(entry.period_id);
      fetchPeriods();
    } catch (error) {
      toast.error(error?.response?.data?.detail || t('common.error'));
    } finally {
      cancelEditing();
    }
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
                        {countryRates && (
                          <Badge
                            variant="outline"
                            className="mt-2 bg-slate-900/40 text-slate-100 border-slate-500"
                            data-testid="payroll-country-badge"
                            title={`Motor fiscal: ${countryRates.country_name} — moneda ${countryRates.currency}`}
                          >
                            <Globe className="w-3 h-3 mr-1" />
                            {t('payrollV2.fiscalEngine') || 'Motor fiscal'}: {countryRates.country_name} ({countryRates.currency})
                          </Badge>
                        )}
                      </div>
                      <div className="text-right">
                        {getStatusBadge(selectedPeriod.status)}
                        <div className="mt-3 flex gap-2 flex-wrap justify-end">
                          {/* Draft/Open: Add employees, Calculate, Submit for Approval */}
                          {['open', 'draft'].includes(selectedPeriod.status) && (
                            <>
                              <Button size="sm" variant="secondary" onClick={() => handleAddEmployees(selectedPeriod.period_id)}><Users className="w-4 h-4 mr-1" />{t('payrollV2.agregar')}</Button>
                              <Button size="sm" className="bg-blue-600 hover:bg-blue-700 text-white" onClick={() => handleCalculatePeriod(selectedPeriod.period_id)} data-testid="recalc-period-btn"><Calculator className="w-4 h-4 mr-1" />{t('payrollV2.calcular')}</Button>
                              {selectedPeriod.employee_count > 0 && (
                                <Button size="sm" className="bg-orange-500 hover:bg-orange-600" onClick={() => handleSubmitForApproval(selectedPeriod.period_id)}>
                                  <ChevronRight className="w-4 h-4 mr-1" />Enviar a Aprobación
                                </Button>
                              )}
                            </>
                          )}
                          {/* Pending Approval: Approve or Reject */}
                          {(selectedPeriod.status === 'pending_approval' || selectedPeriod.status === 'workflow_pending') && (
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
                          {/* Journal Entry actions */}
                          {(selectedPeriod.status === 'approved' || selectedPeriod.status === 'paid') && (
                            <>
                              {selectedPeriod.journal_entry_id ? (
                                <div className="flex items-center gap-1">
                                  <Badge className="bg-blue-100 text-blue-700 text-xs" data-testid="je-badge">
                                    <BookOpen className="w-3 h-3 mr-1" />JE: {selectedPeriod.journal_entry_id.slice(-8)}
                                  </Badge>
                                  <Button size="sm" variant="ghost" className="h-6 w-6 p-0 text-red-500 hover:text-red-700" onClick={() => handleDeleteJE(selectedPeriod.period_id)} data-testid="btn-delete-je" title="Eliminar asiento">
                                    <Trash2 className="w-3 h-3" />
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    className="h-6 px-2 text-xs border-violet-300 text-violet-700 hover:bg-violet-50"
                                    onClick={() => {
                                      const link = document.createElement("a");
                                      link.href = `${API}/payroll/periods/${selectedPeriod.period_id}/export/iif`;
                                      link.download = "";
                                      const token = localStorage.getItem("token") || sessionStorage.getItem("token");
                                      fetch(`${API}/payroll/periods/${selectedPeriod.period_id}/export/iif`, {
                                        headers: { Authorization: `Bearer ${token}` },
                                        credentials: "include"
                                      }).then(r => {
                                        if (!r.ok) throw new Error("Error");
                                        return r.blob();
                                      }).then(blob => {
                                        const url = URL.createObjectURL(blob);
                                        const a = document.createElement("a");
                                        a.href = url;
                                        a.download = `FortexaRH_JE_${selectedPeriod.period_id}.iif`;
                                        a.click();
                                        URL.revokeObjectURL(url);
                                        toast.success("Archivo IIF descargado para QuickBooks Desktop");
                                      }).catch(() => toast.error("Error al exportar IIF"));
                                    }}
                                    data-testid="btn-export-iif"
                                    title="Exportar IIF para QuickBooks Desktop"
                                  >
                                    IIF
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    className="h-6 px-2 text-xs border-emerald-300 text-emerald-700 hover:bg-emerald-50"
                                    onClick={() => openAchDialog(selectedPeriod)}
                                    data-testid="btn-generate-ach"
                                    title="Generar archivo ACH bancario"
                                  >
                                    <Download className="w-3 h-3 mr-1" />ACH
                                  </Button>
                                </div>
                              ) : (
                                <Button 
                                  size="sm" 
                                  variant="outline" 
                                  className="border-blue-300 text-blue-700 hover:bg-blue-50"
                                  onClick={() => handleGenerateJE(selectedPeriod.period_id)}
                                  data-testid="btn-generate-je"
                                >
                                  <BookOpen className="w-4 h-4 mr-1" />Generar Asiento
                                </Button>
                              )}
                            </>
                          )}
                          {selectedPeriod.status === 'paid' ? (
                            <Button size="sm" variant="destructive" className="bg-red-600 hover:bg-red-700" onClick={() => handleDeletePeriod(selectedPeriod.period_id)} data-testid="btn-delete-paid-period">
                              <Trash2 className="w-4 h-4 mr-1" />{t('payrollV2.deletePeriod')}
                            </Button>
                          ) : (
                            <Button size="sm" variant="destructive" onClick={() => handleDeletePeriod(selectedPeriod.period_id)} data-testid="btn-delete-period"><Trash2 className="w-4 h-4" /></Button>
                          )}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Workflow Progress Indicator */}
                {workflowStatus?.has_workflow && (selectedPeriod.status === 'pending_approval' || selectedPeriod.status === 'workflow_pending') && (
                  <Card className="border-blue-200 dark:border-blue-800 bg-blue-50/50 dark:bg-blue-900/10" data-testid="workflow-progress">
                    <CardContent className="py-3 px-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <GitBranch className="w-4 h-4 text-blue-600" />
                          <span className="text-xs font-semibold text-blue-800 dark:text-blue-300 uppercase tracking-wider">
                            {workflowStatus.workflow_name}
                          </span>
                        </div>
                        <Badge variant="outline" className="text-xs">
                          Paso {workflowStatus.current_step} de {workflowStatus.total_steps}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2">
                        {workflowStatus.all_steps?.map((step, idx) => {
                          const isCompleted = workflowStatus.approvals?.some(a => a.step_number === step.step_number);
                          const isCurrent = step.step_number === workflowStatus.current_step;
                          return (
                            <div key={idx} className="flex items-center gap-2">
                              <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                                isCompleted ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' :
                                isCurrent ? 'bg-blue-200 text-blue-800 dark:bg-blue-800 dark:text-blue-200 ring-2 ring-blue-400' :
                                'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400'
                              }`}>
                                {isCompleted ? <CheckCircle className="w-3.5 h-3.5" /> : 
                                 isCurrent ? <AlertCircle className="w-3.5 h-3.5" /> : 
                                 <span className="w-3.5 h-3.5 rounded-full border-2 border-current inline-block" />}
                                <span>{step.name}</span>
                                {isCompleted && (
                                  <span className="text-[10px] opacity-70">
                                    ({workflowStatus.approvals?.find(a => a.step_number === step.step_number)?.approved_by_name})
                                  </span>
                                )}
                              </div>
                              {idx < workflowStatus.all_steps.length - 1 && (
                                <ChevronRight className="w-4 h-4 text-slate-300 shrink-0" />
                              )}
                            </div>
                          );
                        })}
                      </div>
                      {workflowStatus.current_step_info && !workflowStatus.can_current_user_approve && (
                        <p className="text-xs text-amber-700 dark:text-amber-400 mt-2 flex items-center gap-1">
                          <AlertCircle className="w-3.5 h-3.5" />
                          Pendiente de aprobación por: <strong>{workflowStatus.current_step_info.approver_name}</strong>
                        </p>
                      )}
                      {workflowStatus.can_current_user_approve && (
                        <p className="text-xs text-emerald-700 dark:text-emerald-400 mt-2 flex items-center gap-1">
                          <CheckCircle className="w-3.5 h-3.5" />
                          Tu aprobación es requerida para este paso
                        </p>
                      )}
                    </CardContent>
                  </Card>
                )}

                {/* Payroll Sheet — fully customizable columns */}
                {periodEntries.length === 0 ? (
                  <Card className="py-12"><CardContent className="text-center">
                    <Users className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                    <p className="text-slate-500 dark:text-slate-400">{t('payrollV2.noHayEmpleados')}</p>
                    <Button variant="link" onClick={() => handleAddEmployees(selectedPeriod.period_id)}>{t('payrollV2.agregarEmpleados')}</Button>
                  </CardContent></Card>
                ) : (() => {
                  // Build column catalog
                  const allColumns = buildPayrollColumns({
                    formatNumber, t, countryRates, renderEditableCell, renderEditableCodeCell,
                    periodType: selectedPeriod?.period_type,
                    workingDaysMonth: countryRates?.working_days_month || 23.83,
                  });
                  const defaultOrder = allColumns.map(c => c.id);
                  const defaultVisible = Object.fromEntries(allColumns.map(c => [c.id, !!c.defaultVisible]));

                  // Hydrate from saved state, merging in any new columns added since last save
                  const order = columnsState
                    ? [...columnsState.order.filter(id => defaultOrder.includes(id)),
                       ...defaultOrder.filter(id => !columnsState.order.includes(id))]
                    : defaultOrder;
                  const visible = columnsState
                    ? { ...defaultVisible, ...columnsState.visible }
                    : defaultVisible;
                  const colMap = new Map(allColumns.map(c => [c.id, c]));
                  const visibleColumns = order.map(id => colMap.get(id)).filter(c => c && visible[c.id]);

                  // Custom cell builders passed to columns via ctx
                  const ctx = {
                    renderEmployeeCell: (entry) => {
                      const novelties = entry.novelties || [];
                      return (
                        <div><p className="font-medium text-[11px]">{entry.employee_name}</p>
                          <p className="text-slate-500 dark:text-slate-400">{entry.position}</p>
                          {novelties.length > 0 && (
                            <div className="flex gap-1 mt-1 flex-wrap">
                              {novelties.map(n => {
                                const canEdit = selectedPeriod.status !== 'paid';
                                const fmtDate = (iso) => {
                                  if (!iso) return null;
                                  try { return new Date(iso).toLocaleString(undefined, { year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit' }); }
                                  catch { return iso; }
                                };
                                const createdDate = fmtDate(n.created_at);
                                const updatedDate = fmtDate(n.updated_at);
                                return (
                                  <TooltipProvider key={n.novelty_id} delayDuration={200}>
                                    <Tooltip>
                                      <TooltipTrigger asChild>
                                        <Badge variant="outline"
                                          className={`text-[8px] ${n.novelty_type === 'income' ? 'border-emerald-300 text-emerald-600' : 'border-red-300 text-red-600'} ${canEdit ? 'cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-700' : ''}`}
                                          onClick={canEdit ? () => openEditNoveltyDialog(entry, n) : undefined}
                                          data-testid={`novelty-badge-${n.novelty_id}`}>
                                          {n.code}: {formatNumber(n.amount)}{n.is_percentage ? '%' : ''}
                                          {canEdit && (
                                            <X className="w-2 h-2 ml-1 cursor-pointer"
                                              onClick={(e) => { e.stopPropagation(); handleDeleteNovelty(entry.entry_id, n.novelty_id, selectedPeriod.period_id); }}
                                              data-testid={`novelty-delete-${n.novelty_id}`} />
                                          )}
                                        </Badge>
                                      </TooltipTrigger>
                                      <TooltipContent side="top" className="text-[11px] max-w-xs" data-testid={`novelty-tooltip-${n.novelty_id}`}>
                                        <div className="space-y-1">
                                          <div className="font-semibold">{n.name || n.code}</div>
                                          {n.description && <div className="text-slate-500">{n.description}</div>}
                                          {n.created_by && (
                                            <div>
                                              <span className="text-slate-400">{t('payrollV2.tooltip.createdBy', { defaultValue: 'Creado por' })}:</span>{' '}
                                              <span className="font-medium">{n.created_by}</span>
                                              {createdDate && <span className="text-slate-400"> · {createdDate}</span>}
                                            </div>
                                          )}
                                          {!n.created_by && createdDate && (
                                            <div>
                                              <span className="text-slate-400">{t('payrollV2.tooltip.createdAt', { defaultValue: 'Creado' })}:</span>{' '}
                                              <span>{createdDate}</span>
                                            </div>
                                          )}
                                          {n.updated_at && n.updated_at !== n.created_at && (
                                            <div>
                                              <span className="text-slate-400">{t('payrollV2.tooltip.editedBy', { defaultValue: 'Última edición por' })}:</span>{' '}
                                              <span className="font-medium">{n.updated_by || '—'}</span>
                                              {updatedDate && <span className="text-slate-400"> · {updatedDate}</span>}
                                            </div>
                                          )}
                                        </div>
                                      </TooltipContent>
                                    </Tooltip>
                                  </TooltipProvider>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      );
                    },
                    renderDeductionsButton: (entry) => (
                      <button type="button"
                        onClick={() => openDeductionsDialog(entry)}
                        className={`font-mono font-bold ${selectedPeriod?.status !== 'paid' ? 'cursor-pointer hover:underline hover:text-red-900' : ''}`}
                        disabled={selectedPeriod?.status === 'paid'}
                        data-testid={`deductions-cell-${entry.entry_id}`}>
                        {formatNumber(entry.total_deductions)}
                      </button>
                    ),
                  };

                  // Compute TOTALS row dynamically from visible columns
                  const totalsByCol = {};
                  visibleColumns.forEach(c => {
                    totalsByCol[c.id] = periodEntries.reduce((sum, e) => sum + (c.getValue ? c.getValue(e) : 0), 0);
                  });

                  return (
                    <Card>
                      <div className="flex items-center justify-between px-4 py-2 border-b bg-slate-50 dark:bg-slate-900">
                        <span className="text-xs text-slate-500 dark:text-slate-400">{periodEntries.length} empleados · {visibleColumns.length} columnas</span>
                        <PayrollColumnsPicker
                          columns={allColumns}
                          order={order}
                          visible={visible}
                          onChange={saveColumnsState}
                          onReset={resetColumns}
                        />
                      </div>
                      <CardContent className="p-0 overflow-x-auto">
                        <Table className="text-[10px]">
                          <TableHeader>
                            <TableRow>
                              {visibleColumns.map(col => (
                                <TableHead
                                  key={col.id}
                                  className={`font-bold border-r ${col.bgClass || ''} ${col.width || ''} ${col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : ''} align-bottom`}
                                  title={col.label}
                                  data-testid={`th-${col.id}`}
                                >
                                  {col.header || col.label}
                                </TableHead>
                              ))}
                              <TableHead className="w-20 text-center">{t('payrollV2.table.actions')}</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {periodEntries.map((entry, index) => (
                              <TableRow key={entry.entry_id} className="hover:bg-slate-50 dark:bg-slate-800">
                                {visibleColumns.map(col => (
                                  <TableCell
                                    key={col.id}
                                    className={`border-r ${col.bgClass || ''} ${col.textClass || ''} ${col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : ''}`}
                                    data-testid={`cell-${col.id}-${entry.entry_id}`}
                                  >
                                    {col.render ? col.render(entry, { ...ctx, index }) : formatNumber(col.getValue ? col.getValue(entry) : 0)}
                                  </TableCell>
                                ))}
                                <TableCell className="text-center">
                                  <div className="flex gap-1 justify-center">
                                    <Button size="icon" variant="ghost" className="h-6 w-6" onClick={() => handleDownloadPayslip(entry.entry_id)} title={t('payrollV2.downloadPayslip')}>
                                      <FileDown className="w-3.5 h-3.5 text-blue-600" />
                                    </Button>
                                    {selectedPeriod.status !== 'paid' && (
                                      <>
                                        <Button size="icon" variant="ghost" className="h-6 w-6" onClick={() => openNoveltyDialog(entry)} title="Agregar novedad">
                                          <PlusCircle className="w-3 h-3 text-blue-500" />
                                        </Button>
                                        <Button size="icon" variant="ghost" className="h-6 w-6 text-red-500" onClick={() => handleDeleteEntry(entry.entry_id, selectedPeriod.period_id)}>
                                          <Trash2 className="w-3 h-3" />
                                        </Button>
                                      </>
                                    )}
                                  </div>
                                </TableCell>
                              </TableRow>
                            ))}
                            {/* Totals row */}
                            <TableRow className="bg-slate-200 dark:bg-slate-700 font-bold text-[11px]" data-testid="payroll-totals-row">
                              {visibleColumns.map((col, idx) => {
                                if (idx === 0) {
                                  return (
                                    <TableCell key={col.id} className="text-right border-r" colSpan={1}>
                                      {t('payrollV2.totales', { defaultValue: 'TOTALES:' })}
                                    </TableCell>
                                  );
                                }
                                const isLabelCol = col.id === 'employee' || col.id === 'cedula';
                                return (
                                  <TableCell
                                    key={col.id}
                                    className={`border-r font-mono ${col.textClass || ''} ${col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : ''}`}
                                  >
                                    {isLabelCol ? '' : formatNumber(totalsByCol[col.id] || 0)}
                                  </TableCell>
                                );
                              })}
                              <TableCell></TableCell>
                            </TableRow>
                          </TableBody>
                        </Table>
                      </CardContent>
                    </Card>
                  );
                })()}
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

            {/* Universal Multi-Country Fiscal Report */}
            <Card data-testid="universal-fiscal-report-card" className="border-2 border-blue-200 dark:border-blue-800 bg-gradient-to-br from-blue-50/40 to-emerald-50/40 dark:from-blue-950/30 dark:to-emerald-950/30">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Globe className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                  Reporte Fiscal Universal
                  {countryRates && (
                    <Badge variant="outline" className="ml-2">
                      {countryRates.country_name} · {countryRates.currency}
                    </Badge>
                  )}
                </CardTitle>
                <CardDescription>
                  Resumen fiscal adaptado al motor del país activo. Funciona para los <b>29 países</b> soportados.
                  Incluye deducciones del empleado, contribuciones del empleador, ISR y totales con la agencia fiscal correspondiente.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {periods.filter(p => ['calculated', 'approved', 'paid'].includes(p.status)).length === 0 ? (
                  <p className="text-slate-500 text-center py-4">{t('payrollV2.pagueUnaNominaPara') || 'Calcule o apruebe una nómina para generar el reporte.'}</p>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {periods.filter(p => ['calculated', 'approved', 'paid'].includes(p.status)).map(period => (
                      <div key={period.period_id} className="p-4 border rounded-lg bg-white dark:bg-slate-900 shadow-sm"
                           data-testid={`universal-report-row-${period.period_id}`}>
                        <div className="mb-3">
                          <p className="font-semibold text-slate-800 dark:text-slate-100">{period.description}</p>
                          <p className="text-xs text-slate-500 dark:text-slate-400">
                            {period.month}/{period.year} • {period.employee_count || 0} empleados
                          </p>
                        </div>
                        <div className="flex gap-2 flex-wrap">
                          <Button
                            variant="outline"
                            size="sm"
                            className="text-blue-700 border-blue-300 hover:bg-blue-100 dark:hover:bg-blue-900/30"
                            onClick={() => downloadUniversalFiscalReport(period, 'csv')}
                            data-testid={`universal-csv-${period.period_id}`}
                          >
                            <FileSpreadsheet className="w-4 h-4 mr-1" />CSV
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            className="text-emerald-700 border-emerald-300 hover:bg-emerald-100 dark:hover:bg-emerald-900/30"
                            onClick={() => downloadUniversalFiscalReport(period, 'pdf')}
                            data-testid={`universal-pdf-${period.period_id}`}
                          >
                            <FileDown className="w-4 h-4 mr-1" />PDF
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

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
        <Dialog open={showNoveltyDialog} onOpenChange={(open) => { setShowNoveltyDialog(open); if (!open) setEditingNoveltyId(null); }}>
          <DialogContent>
            <DialogHeader><DialogTitle>{editingNoveltyId ? t('payrollV2.editarNovedad', { defaultValue: 'Editar Novedad' }) : t('payrollV2.agregarNovedad')}</DialogTitle>
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
            <DialogFooter><Button variant="outline" onClick={() => { setShowNoveltyDialog(false); setEditingNoveltyId(null); }}>{t('payrollV2.cancelar')}</Button>
              <Button onClick={handleSaveNovelty} data-testid="save-novelty-btn">
                <Plus className="w-4 h-4 mr-2" />
                {editingNoveltyId
                  ? t('payrollV2.actualizarNovedad', { defaultValue: 'Actualizar Novedad' })
                  : t('payrollV2.agregarNovedad')}
              </Button>
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

        {/* ACH Bank File Dialog */}
        <Dialog open={showAchDialog} onOpenChange={setShowAchDialog}>
          <DialogContent className="sm:max-w-lg">
            <DialogHeader>
              <DialogTitle>Generar Archivo ACH</DialogTitle>
              <DialogDescription>
                {selectedPeriod?.description || "Período seleccionado"} - Archivo de pago bancario
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>Banco</Label>
                <Select value={achBank} onValueChange={handleAchBankChange}>
                  <SelectTrigger data-testid="ach-bank-select"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="banreservas">Banreservas</SelectItem>
                    <SelectItem value="popular">Banco Popular Dominicano</SelectItem>
                    <SelectItem value="bhd">BHD León</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {achLoading ? (
                <div className="py-6 text-center text-sm text-slate-500">Cargando vista previa...</div>
              ) : achPreview ? (
                <div className="space-y-3">
                  <div className="grid grid-cols-3 gap-3">
                    <div className="bg-emerald-50 dark:bg-emerald-900/20 rounded-lg p-3 text-center">
                      <p className="text-xs text-slate-500">Listos</p>
                      <p className="text-lg font-bold text-emerald-700" data-testid="ach-ready-count">{achPreview.ready_count}</p>
                    </div>
                    <div className="bg-amber-50 dark:bg-amber-900/20 rounded-lg p-3 text-center">
                      <p className="text-xs text-slate-500">Sin banco</p>
                      <p className="text-lg font-bold text-amber-700" data-testid="ach-missing-count">{achPreview.missing_count}</p>
                    </div>
                    <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 text-center">
                      <p className="text-xs text-slate-500">Total</p>
                      <p className="text-sm font-bold text-blue-700" data-testid="ach-total-amount">
                        RD${achPreview.total_amount?.toLocaleString('es-DO', {minimumFractionDigits: 2})}
                      </p>
                    </div>
                  </div>

                  {achPreview.missing_count > 0 && (
                    <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                      <p className="text-xs font-medium text-amber-800 mb-1 flex items-center gap-1">
                        <AlertCircle className="w-3.5 h-3.5" /> Empleados sin datos bancarios:
                      </p>
                      <div className="space-y-0.5">
                        {achPreview.missing?.slice(0, 5).map((m, i) => (
                          <p key={i} className="text-xs text-amber-700">
                            {m.employee_name} - RD${m.amount?.toLocaleString('es-DO', {minimumFractionDigits: 2})}
                          </p>
                        ))}
                      </div>
                      <p className="text-[10px] text-amber-600 mt-1">
                        Configura los datos bancarios en el perfil de cada empleado
                      </p>
                    </div>
                  )}

                  {achPreview.ready_count > 0 && (
                    <div className="max-h-[150px] overflow-y-auto border rounded-lg">
                      <table className="w-full text-xs">
                        <thead className="bg-slate-50 sticky top-0">
                          <tr>
                            <th className="text-left px-2 py-1.5 font-medium text-slate-500">Empleado</th>
                            <th className="text-left px-2 py-1.5 font-medium text-slate-500">Cuenta</th>
                            <th className="text-right px-2 py-1.5 font-medium text-slate-500">Monto</th>
                          </tr>
                        </thead>
                        <tbody>
                          {achPreview.ready?.map((r, i) => (
                            <tr key={i} className="border-t">
                              <td className="px-2 py-1 text-slate-700">{r.employee_name}</td>
                              <td className="px-2 py-1 text-slate-500 font-mono text-[10px]">{r.account}</td>
                              <td className="px-2 py-1 text-right text-emerald-700 font-medium">
                                RD${r.amount?.toLocaleString('es-DO', {minimumFractionDigits: 2})}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {!achPreview.company_account && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                      <p className="text-xs text-red-700 flex items-center gap-1">
                        <AlertCircle className="w-3.5 h-3.5" />
                        No hay cuenta bancaria de empresa configurada para {achBank}. 
                        Ve a Configuración para agregarla.
                      </p>
                    </div>
                  )}
                </div>
              ) : null}
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowAchDialog(false)}>Cancelar</Button>
              <Button
                onClick={handleDownloadAch}
                disabled={!achPreview || achPreview.ready_count === 0}
                className="bg-emerald-600 hover:bg-emerald-700 text-white"
                data-testid="btn-download-ach"
              >
                <Download className="w-4 h-4 mr-2" />
                Descargar ACH ({achPreview?.ready_count || 0} registros)
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Bank Info Warning Dialog */}
        <Dialog open={showBankWarningDialog} onOpenChange={setShowBankWarningDialog}>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-amber-700">
                <AlertCircle className="w-5 h-5" /> Empleados sin Datos Bancarios
              </DialogTitle>
              <DialogDescription>
                {bankCheckWarning?.missing_count} de {bankCheckWarning?.total} empleados no tienen cuenta bancaria configurada. No se podrá generar archivo ACH para estos empleados.
              </DialogDescription>
            </DialogHeader>
            {bankCheckWarning?.missing?.length > 0 && (
              <div className="max-h-[200px] overflow-y-auto border rounded-lg">
                <table className="w-full text-xs">
                  <thead className="bg-amber-50 sticky top-0">
                    <tr>
                      <th className="text-left px-3 py-2 font-medium text-amber-800">Empleado</th>
                      <th className="text-right px-3 py-2 font-medium text-amber-800">Neto a Pagar</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bankCheckWarning.missing.map((emp, i) => (
                      <tr key={i} className="border-t border-amber-100">
                        <td className="px-3 py-1.5 text-slate-700">{emp.name}</td>
                        <td className="px-3 py-1.5 text-right font-medium text-slate-700">
                          RD${emp.amount?.toLocaleString('es-DO', {minimumFractionDigits: 2})}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <p className="text-xs text-slate-500">
              Puedes configurar los datos bancarios en el perfil de cada empleado (sección Datos Bancarios).
            </p>
            <DialogFooter className="gap-2">
              <Button variant="outline" onClick={() => setShowBankWarningDialog(false)}>Cancelar</Button>
              <Button
                onClick={() => executeApproval(pendingApprovalPeriodId)}
                className="bg-amber-600 hover:bg-amber-700 text-white"
                data-testid="btn-approve-with-warning"
              >
                <Check className="w-4 h-4 mr-1" /> Aprobar de todos modos
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Deductions Detail Dialog */}
      <Dialog open={showDeductionsDialog} onOpenChange={setShowDeductionsDialog}>
        <DialogContent className="max-w-lg max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Calculator className="w-5 h-5 text-red-600" />
              {t('payrollV2.deductionsDialog.title')}
            </DialogTitle>
            <DialogDescription>
              {deductionsEntry?.employee_name} &middot; {t('payrollV2.deductionsDialog.subtitle')}
            </DialogDescription>
          </DialogHeader>

          {deductionsEntry && (
            <div className="space-y-5">
              {/* Salary reference */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 flex justify-between items-center">
                <span className="text-sm font-medium text-blue-700">{t('payrollV2.deductionsDialog.grossSalary')}</span>
                <span className="font-mono font-bold text-blue-700">{formatNumber(deductionsEntry.gross_salary)}</span>
              </div>

              {/* Legal Deductions */}
              <div className="space-y-3">
                <h4 className="text-sm font-semibold text-slate-700">{t('payrollV2.deductionsDialog.legalDeductions')}</h4>
                
                <div className="space-y-2">
                  <div className="flex items-center justify-between gap-3">
                    <Label className="text-sm w-24" title={countryRates?.labels?.sfs_employee}>{getDeductionLabel('sfs_employee', 'payrollV2.sfs')} ({getDeductionRatePct('sfs_employee') || '3.04%'})</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={deductionsForm.sfs_override}
                      onChange={(e) => setDeductionsForm({ ...deductionsForm, sfs_override: e.target.value })}
                      className="w-40 text-right font-mono"
                      data-testid="deductions-sfs"
                    />
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <Label className="text-sm w-24">AFP (2.87%)</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={deductionsForm.afp_override}
                      onChange={(e) => setDeductionsForm({ ...deductionsForm, afp_override: e.target.value })}
                      className="w-40 text-right font-mono"
                      data-testid="deductions-afp"
                    />
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <Label className="text-sm w-24">ISR</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={deductionsForm.isr_override}
                      onChange={(e) => setDeductionsForm({ ...deductionsForm, isr_override: e.target.value })}
                      className="w-40 text-right font-mono"
                      data-testid="deductions-isr"
                    />
                  </div>
                </div>

                <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-2 flex justify-between items-center">
                  <span className="text-xs font-medium text-emerald-700">{t('payrollV2.deductionsDialog.subtotalLegal')}</span>
                  <span className="font-mono font-bold text-emerald-700 text-sm">
                    {formatNumber((parseFloat(deductionsForm.sfs_override) || 0) + (parseFloat(deductionsForm.afp_override) || 0) + (parseFloat(deductionsForm.isr_override) || 0))}
                  </span>
                </div>
              </div>

              {/* Additional Deductions */}
              <div className="space-y-3">
                <h4 className="text-sm font-semibold text-slate-700">{t('payrollV2.deductionsDialog.additionalDeductions')}</h4>
                
                {deductionsForm.additional_deductions.length === 0 ? (
                  <p className="text-sm text-slate-400 italic text-center py-2">{t('payrollV2.deductionsDialog.noAdditional')}</p>
                ) : (
                  <div className="space-y-2">
                    {deductionsForm.additional_deductions.map((ded, idx) => (
                      <div key={idx} className="flex items-center justify-between p-2 bg-slate-50 rounded-lg border gap-2">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium">{ded.type}</p>
                          {ded.description && <p className="text-xs text-slate-500">{ded.description}</p>}
                        </div>
                        <div className="flex items-center gap-1">
                          <Input
                            type="number"
                            step="0.01"
                            value={ded.amount}
                            onChange={(e) => {
                              const updated = [...deductionsForm.additional_deductions];
                              updated[idx] = { ...updated[idx], amount: parseFloat(e.target.value) || 0 };
                              setDeductionsForm({ ...deductionsForm, additional_deductions: updated });
                            }}
                            className="w-28 text-right font-mono text-sm h-8"
                            data-testid={`ded-amount-${idx}`}
                          />
                          <Button type="button" variant="ghost" size="icon" className="h-7 w-7 text-red-500 shrink-0" onClick={() => removePayrollDeduction(idx)}>
                            <X className="w-3.5 h-3.5" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {deductionsForm.additional_deductions.length > 0 && (
                  <div className="bg-orange-50 border border-orange-200 rounded-lg p-2 flex justify-between items-center">
                    <span className="text-xs font-medium text-orange-700">{t('payrollV2.deductionsDialog.subtotalAdditional')}</span>
                    <span className="font-mono font-bold text-orange-700 text-sm">
                      {formatNumber(deductionsForm.additional_deductions.reduce((s, d) => s + (d.is_percentage ? 0 : (parseFloat(d.amount) || 0)), 0))}
                    </span>
                  </div>
                )}

                {/* Add deduction form */}
                <div className="bg-blue-50 rounded-lg p-3 border border-blue-200 space-y-2">
                  <p className="text-xs font-semibold text-blue-700">+ {t('payrollV2.deductionsDialog.addDeduction')}</p>
                  <div className="grid grid-cols-3 gap-2">
                    <Select value={newPayrollDeduction.type} onValueChange={(v) => setNewPayrollDeduction({ ...newPayrollDeduction, type: v })}>
                      <SelectTrigger className="bg-white text-xs h-8">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Préstamo Empresa">Préstamo Empresa</SelectItem>
                        <SelectItem value="Pensión Alimenticia">Pensión Alimenticia</SelectItem>
                        <SelectItem value="Adelanto Salario">Adelanto Salario</SelectItem>
                        <SelectItem value="Seguro Complementario">Seguro Complementario</SelectItem>
                        <SelectItem value="Cooperativa">Cooperativa</SelectItem>
                        <SelectItem value="Otro">Otro</SelectItem>
                      </SelectContent>
                    </Select>
                    <Input
                      placeholder={t('payrollV2.deductionsDialog.descPlaceholder')}
                      value={newPayrollDeduction.description}
                      onChange={(e) => setNewPayrollDeduction({ ...newPayrollDeduction, description: e.target.value })}
                      className="bg-white text-xs h-8"
                    />
                    <div className="flex gap-1">
                      <Input
                        type="number"
                        step="0.01"
                        placeholder="0.00"
                        value={newPayrollDeduction.amount}
                        onChange={(e) => setNewPayrollDeduction({ ...newPayrollDeduction, amount: e.target.value })}
                        className="bg-white text-xs h-8"
                      />
                      <Button type="button" size="sm" className="h-8 px-2 bg-blue-600" onClick={addPayrollDeduction} disabled={!newPayrollDeduction.amount}>
                        <Plus className="w-3 h-3" />
                      </Button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Grand Total */}
              <div className="bg-red-50 border-2 border-red-200 rounded-lg p-3 flex justify-between items-center">
                <span className="font-semibold text-red-700">{t('payrollV2.deductionsDialog.totalDeductions')}</span>
                <span className="font-mono font-bold text-red-700 text-lg">
                  {formatNumber(
                    (parseFloat(deductionsForm.sfs_override) || 0) +
                    (parseFloat(deductionsForm.afp_override) || 0) +
                    (parseFloat(deductionsForm.isr_override) || 0) +
                    deductionsForm.additional_deductions.reduce((s, d) => s + (d.is_percentage ? 0 : (parseFloat(d.amount) || 0)), 0)
                  )}
                </span>
              </div>
            </div>
          )}

          <DialogFooter className="gap-2 mt-4">
            <Button variant="outline" onClick={() => setShowDeductionsDialog(false)}>{t('common.cancel')}</Button>
            <Button onClick={saveDeductions} disabled={savingDeductions} className="bg-emerald-600 hover:bg-emerald-700" data-testid="save-deductions-btn">
              {savingDeductions ? <RefreshCw className="w-4 h-4 mr-1 animate-spin" /> : <Save className="w-4 h-4 mr-1" />}
              {t('payrollV2.deductionsDialog.save')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </DashboardLayout>
  );
}
