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
import { Textarea } from "@/components/ui/textarea";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";
import { 
  BookOpen, 
  Plus, 
  Edit, 
  Trash2, 
  FileText, 
  DollarSign,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw,
  Search,
  Download,
  Settings,
  Link2,
  AlertTriangle,
  CheckCircle,
  X,
  FileSpreadsheet,
  List,
  Eye
} from "lucide-react";
import { toast } from "sonner";

export default function AccountingPage() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState("asientos");
  const [entries, setEntries] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showNewEntry, setShowNewEntry] = useState(false);
  const [showEditEntry, setShowEditEntry] = useState(false);
  const [showEditAccount, setShowEditAccount] = useState(false);
  const [showNewAccount, setShowNewAccount] = useState(false);
  const [showCatalogSelector, setShowCatalogSelector] = useState(false);
  const [catalogTemplates, setCatalogTemplates] = useState([]);
  const [selectedEntry, setSelectedEntry] = useState(null);
  const [selectedAccount, setSelectedAccount] = useState(null);
  
  // CSV Preview states
  const [showPreview, setShowPreview] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  const [previewFormat, setPreviewFormat] = useState("summary");
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewEntry, setPreviewEntry] = useState(null);
  
  // Filters
  const [searchNumber, setSearchNumber] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  
  // Entry form
  const [entryForm, setEntryForm] = useState({
    entry_date: new Date().toISOString().split('T')[0],
    reference: "",
    description: "",
    period: new Date().toISOString().slice(0, 7),
    entry_type: "manual",
    notes: "",
    lines: [
      { account_code: "", account_name: "", description: "", debit: 0, credit: 0 }
    ]
  });
  
  // Account form
  const [accountForm, setAccountForm] = useState({
    code: "",
    name: "",
    account_type: "expense",
    parent_code: "",
    description: ""
  });

  const { getAuthHeaders } = useAuth();

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [entriesRes, accountsRes] = await Promise.all([
        axios.get(`${API}/accounting/journal-entries`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/accounting/accounts`, { headers: getAuthHeaders(), withCredentials: true })
      ]);
      setEntries(entriesRes.data);
      setAccounts(accountsRes.data);
    } catch (error) {
      console.error("Error fetching data:", error);
      toast.error(t('accounting.messages.errorLoading'));
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders, t]);

  const fetchCatalogTemplates = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/accounting/catalog-templates`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setCatalogTemplates(response.data);
    } catch (error) {
      console.error("Error fetching catalog templates:", error);
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    fetchData();
    fetchCatalogTemplates();
  }, [fetchData, fetchCatalogTemplates]);

  const loadCatalogTemplate = async (catalogId) => {
    if (!window.confirm(t('accounting.messages.confirmLoadCatalog'))) {
      return;
    }
    
    try {
      const response = await axios.post(`${API}/accounting/accounts/load-catalog/${catalogId}`, {}, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success(response.data.message);
      setShowCatalogSelector(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('accounting.messages.errorLoadCatalog'));
    }
  };

  const handleSearch = async () => {
    try {
      const params = new URLSearchParams();
      if (searchNumber) params.append("entry_number", searchNumber);
      if (startDate) params.append("start_date", startDate);
      if (endDate) params.append("end_date", endDate);
      
      const response = await axios.get(`${API}/accounting/journal-entries/search?${params.toString()}`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setEntries(response.data);
    } catch (error) {
      toast.error(t('accounting.messages.errorSearch'));
    }
  };

  const clearSearch = () => {
    setSearchNumber("");
    setStartDate("");
    setEndDate("");
    fetchData();
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-DO', {
      style: 'currency',
      currency: 'DOP',
      minimumFractionDigits: 2
    }).format(value || 0);
  };

  // Entry line management
  const addLine = () => {
    setEntryForm({
      ...entryForm,
      lines: [...entryForm.lines, { account_code: "", account_name: "", description: "", debit: 0, credit: 0 }]
    });
  };

  const removeLine = (index) => {
    const lines = entryForm.lines.filter((_, i) => i !== index);
    setEntryForm({ ...entryForm, lines });
  };

  const updateLine = (index, field, value) => {
    const lines = [...entryForm.lines];
    lines[index] = { ...lines[index], [field]: field === 'debit' || field === 'credit' ? parseFloat(value) || 0 : value };
    
    if (field === 'account_code') {
      const account = accounts.find(a => a.code === value);
      if (account) {
        lines[index].account_name = account.name;
      }
    }
    
    setEntryForm({ ...entryForm, lines });
  };

  const getTotalDebits = () => entryForm.lines.reduce((sum, line) => sum + (parseFloat(line.debit) || 0), 0);
  const getTotalCredits = () => entryForm.lines.reduce((sum, line) => sum + (parseFloat(line.credit) || 0), 0);
  const isBalanced = () => Math.abs(getTotalDebits() - getTotalCredits()) < 0.01;

  // Entry CRUD
  const handleCreateEntry = async () => {
    if (!isBalanced()) {
      toast.error(t('accounting.messages.notBalanced'));
      return;
    }
    
    try {
      await axios.post(`${API}/accounting/journal-entries`, entryForm, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success(t('accounting.messages.entryCreated'));
      setShowNewEntry(false);
      resetEntryForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('accounting.messages.errorCreatingEntry'));
    }
  };

  const handleUpdateEntry = async () => {
    if (!selectedEntry || !isBalanced()) {
      toast.error(t('accounting.messages.notBalanced'));
      return;
    }
    
    try {
      await axios.put(`${API}/accounting/journal-entries/${selectedEntry.entry_id}`, entryForm, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success(t('accounting.messages.entryUpdated'));
      setShowEditEntry(false);
      setSelectedEntry(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('accounting.messages.errorUpdatingEntry'));
    }
  };

  const handleDeleteEntry = async (entry) => {
    const hasPayroll = entry.payroll_period_id;
    const message = hasPayroll 
      ? t('accounting.messages.confirmDeleteWithPayroll')
      : t('accounting.messages.confirmDeleteEntry');
    
    if (!confirm(message)) return;
    
    try {
      const endpoint = hasPayroll 
        ? `/accounting/journal-entries/${entry.entry_id}/with-payroll`
        : `/accounting/journal-entries/${entry.entry_id}`;
      
      await axios.delete(`${API}${endpoint}`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success(t('accounting.messages.entryDeleted'));
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('accounting.messages.errorDeletingEntry'));
    }
  };

  const openEditEntry = (entry) => {
    setSelectedEntry(entry);
    setEntryForm({
      entry_date: entry.entry_date,
      reference: entry.reference || "",
      description: entry.description || "",
      period: entry.period || "",
      entry_type: entry.entry_type || "manual",
      notes: entry.notes || "",
      lines: entry.lines || []
    });
    setShowEditEntry(true);
  };

  const resetEntryForm = () => {
    setEntryForm({
      entry_date: new Date().toISOString().split('T')[0],
      reference: "",
      description: "",
      period: new Date().toISOString().slice(0, 7),
      entry_type: "manual",
      notes: "",
      lines: [{ account_code: "", account_name: "", description: "", debit: 0, credit: 0 }]
    });
  };

  // Account CRUD
  const handleCreateAccount = async () => {
    try {
      await axios.post(`${API}/accounting/accounts`, accountForm, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success(t('accounting.messages.accountCreated'));
      setShowNewAccount(false);
      resetAccountForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('accounting.messages.errorCreatingAccount'));
    }
  };

  const handleUpdateAccount = async () => {
    if (!selectedAccount) return;
    
    try {
      await axios.put(`${API}/accounting/accounts/${selectedAccount.account_id}`, accountForm, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success(t('accounting.messages.accountUpdated'));
      setShowEditAccount(false);
      setSelectedAccount(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('accounting.messages.errorUpdatingAccount'));
    }
  };

  const handleDeleteAccount = async (accountId) => {
    if (!confirm(t('accounting.messages.confirmDeleteAccount'))) return;
    
    try {
      await axios.delete(`${API}/accounting/accounts/${accountId}`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success(t('accounting.messages.accountDeleted'));
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('accounting.messages.errorDeletingAccount'));
    }
  };

  const handleResetAccounts = async () => {
    if (!confirm(t('accounting.messages.confirmResetAccounts'))) return;
    
    try {
      await axios.post(`${API}/accounting/accounts/reset-defaults`, {}, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success(t('accounting.messages.accountsReset'));
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('accounting.messages.errorResetAccounts'));
    }
  };

  const openEditAccount = (account) => {
    setSelectedAccount(account);
    setAccountForm({
      code: account.code,
      name: account.name,
      account_type: account.account_type,
      parent_code: account.parent_code || "",
      description: account.description || ""
    });
    setShowEditAccount(true);
  };

  const resetAccountForm = () => {
    setAccountForm({
      code: "",
      name: "",
      account_type: "expense",
      parent_code: "",
      description: ""
    });
  };

  // Preview functions
  const openPreview = async (entry, format = "summary") => {
    setPreviewEntry(entry);
    setPreviewFormat(format);
    setPreviewLoading(true);
    setShowPreview(true);
    
    try {
      const response = await axios.get(
        `${API}/accounting/journal-entries/${entry.entry_id}/preview?format=${format}`,
        { headers: getAuthHeaders(), withCredentials: true }
      );
      setPreviewData(response.data);
    } catch (error) {
      toast.error(t('accounting.messages.errorPreview'));
      setShowPreview(false);
    } finally {
      setPreviewLoading(false);
    }
  };

  const changePreviewFormat = async (newFormat) => {
    if (!previewEntry || newFormat === previewFormat) return;
    setPreviewFormat(newFormat);
    setPreviewLoading(true);
    
    try {
      const response = await axios.get(
        `${API}/accounting/journal-entries/${previewEntry.entry_id}/preview?format=${newFormat}`,
        { headers: getAuthHeaders(), withCredentials: true }
      );
      setPreviewData(response.data);
    } catch (error) {
      toast.error(t('accounting.messages.errorChangeFormat'));
    } finally {
      setPreviewLoading(false);
    }
  };

  const downloadFromPreview = () => {
    if (previewEntry) {
      exportToCSV(previewEntry, previewFormat);
    }
  };

  // Export functions
  const exportToCSV = async (entry, format = "summary") => {
    try {
      const response = await axios.get(
        `${API}/accounting/journal-entries/${entry.entry_id}/export?format=${format}`,
        { 
          headers: getAuthHeaders(), 
          withCredentials: true,
          responseType: 'blob'
        }
      );
      
      const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      const formatSuffix = format === "summary" ? t('accounting.preview.summary').toLowerCase() : t('accounting.preview.detailed').toLowerCase();
      link.download = `asiento_${entry.entry_number || entry.entry_id}_${formatSuffix}.csv`;
      link.click();
      toast.success(`CSV ${format === "summary" ? t('accounting.preview.summary').toLowerCase() : t('accounting.preview.detailed').toLowerCase()} ${t('common.downloaded')}`);
    } catch (error) {
      toast.error(t('accounting.messages.errorExport'));
    }
  };

  const exportToExcel = async (entry, format = "summary") => {
    await exportToCSV(entry, format);
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'draft':
        return <Badge variant="outline" className="border-slate-400">{t('accounting.filters.draft')}</Badge>;
      case 'posted':
        return <Badge className="bg-emerald-100 text-emerald-700 dark:text-emerald-400">{t('accounting.filters.posted')}</Badge>;
      case 'voided':
        return <Badge className="bg-red-100 text-red-700">{t('accounting.filters.voided')}</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  const getAccountTypeBadge = (type) => {
    switch (type) {
      case 'expense':
        return <Badge className="bg-red-100 text-red-700">{t('accounting.account.expense')}</Badge>;
      case 'asset':
        return <Badge className="bg-blue-100 text-blue-700 dark:text-blue-400">{t('accounting.account.asset')}</Badge>;
      case 'liability':
        return <Badge className="bg-amber-100 text-amber-700 dark:text-amber-400">{t('accounting.account.liability')}</Badge>;
      case 'income':
        return <Badge className="bg-emerald-100 text-emerald-700 dark:text-emerald-400">{t('accounting.account.income')}</Badge>;
      case 'equity':
        return <Badge className="bg-purple-100 text-purple-700">{t('accounting.account.equity')}</Badge>;
      default:
        return <Badge variant="secondary">{type}</Badge>;
    }
  };

  // Stats
  const stats = {
    totalEntries: entries.length,
    totalDebits: entries.reduce((sum, e) => sum + (e.total_debits || 0), 0),
    totalCredits: entries.reduce((sum, e) => sum + (e.total_credits || 0), 0),
    payrollEntries: entries.filter(e => e.payroll_period_id).length
  };

  return (
    <DashboardLayout title="Contabilidad">
      <div className="space-y-6" data-testid="accounting-page">
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">Módulo Contable</h1>
            <p className="text-slate-500 dark:text-slate-400">Asientos de diario y plan de cuentas</p>
          </div>
          <Button onClick={fetchData} variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Actualizar
          </Button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="border-l-4 border-l-blue-500">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500 dark:text-slate-400">Total Asientos</p>
                  <p className="text-2xl font-bold">{stats.totalEntries}</p>
                </div>
                <FileText className="w-8 h-8 text-blue-300" />
              </div>
            </CardContent>
          </Card>
          <Card className="border-l-4 border-l-emerald-500">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500 dark:text-slate-400">Total Débitos</p>
                  <p className="text-xl font-bold text-emerald-600 dark:text-emerald-400">{formatCurrency(stats.totalDebits)}</p>
                </div>
                <ArrowUpRight className="w-8 h-8 text-emerald-300" />
              </div>
            </CardContent>
          </Card>
          <Card className="border-l-4 border-l-red-500">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500 dark:text-slate-400">Total Créditos</p>
                  <p className="text-xl font-bold text-red-600 dark:text-red-400">{formatCurrency(stats.totalCredits)}</p>
                </div>
                <ArrowDownRight className="w-8 h-8 text-red-300" />
              </div>
            </CardContent>
          </Card>
          <Card className="border-l-4 border-l-purple-500">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500 dark:text-slate-400">De Nómina</p>
                  <p className="text-2xl font-bold text-purple-600">{stats.payrollEntries}</p>
                </div>
                <Link2 className="w-8 h-8 text-purple-300" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid grid-cols-2 w-full max-w-md">
            <TabsTrigger value="asientos">Asientos de Diario</TabsTrigger>
            <TabsTrigger value="cuentas">Catálogo de Cuentas</TabsTrigger>
          </TabsList>

          {/* Asientos Tab */}
          <TabsContent value="asientos" className="space-y-4">
            {/* Search and Filters */}
            <Card>
              <CardContent className="p-4">
                <div className="flex flex-wrap gap-4 items-end">
                  <div className="space-y-1">
                    <Label className="text-xs text-slate-500 dark:text-slate-400">Buscar por Número</Label>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <Input 
                        className="pl-9 w-40" 
                        placeholder="000001"
                        value={searchNumber}
                        onChange={(e) => setSearchNumber(e.target.value)}
                      />
                    </div>
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs text-slate-500 dark:text-slate-400">Fecha Inicio</Label>
                    <Input 
                      type="date" 
                      className="w-40"
                      value={startDate}
                      onChange={(e) => setStartDate(e.target.value)}
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs text-slate-500 dark:text-slate-400">Fecha Fin</Label>
                    <Input 
                      type="date" 
                      className="w-40"
                      value={endDate}
                      onChange={(e) => setEndDate(e.target.value)}
                    />
                  </div>
                  <Button onClick={handleSearch}>
                    <Search className="w-4 h-4 mr-2" />
                    Buscar
                  </Button>
                  <Button variant="outline" onClick={clearSearch}>
                    Limpiar
                  </Button>
                  <div className="flex-1" />
                  <Button onClick={() => { resetEntryForm(); setShowNewEntry(true); }}>
                    <Plus className="w-4 h-4 mr-2" />
                    Nuevo Asiento
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Entries Table */}
            <Card>
              <CardContent className="p-0">
                {loading ? (
                  <div className="p-8 space-y-4">
                    {[1, 2, 3].map(i => (
                      <div key={i} className="h-16 bg-slate-100 rounded animate-pulse" />
                    ))}
                  </div>
                ) : entries.length === 0 ? (
                  <div className="text-center py-12">
                    <BookOpen className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                    <p className="text-slate-500 dark:text-slate-400">No hay asientos de diario</p>
                    <Button variant="link" onClick={() => { resetEntryForm(); setShowNewEntry(true); }}>
                      Crear primer asiento
                    </Button>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-24">Número</TableHead>
                        <TableHead>Fecha</TableHead>
                        <TableHead>Referencia</TableHead>
                        <TableHead>Descripción</TableHead>
                        <TableHead className="text-right">Débito</TableHead>
                        <TableHead className="text-right">Crédito</TableHead>
                        <TableHead>Estado</TableHead>
                        <TableHead className="text-right">Acciones</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {entries.map(entry => (
                        <TableRow key={entry.entry_id}>
                          <TableCell>
                            <span className="font-mono font-bold text-blue-600 dark:text-blue-400">
                              #{entry.entry_number || '-'}
                            </span>
                          </TableCell>
                          <TableCell>{entry.entry_date}</TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              {entry.reference}
                              {entry.payroll_period_id && (
                                <Badge variant="outline" className="text-xs border-purple-300 text-purple-600">
                                  <Link2 className="w-3 h-3 mr-1" />
                                  Nómina
                                </Badge>
                              )}
                            </div>
                          </TableCell>
                          <TableCell className="max-w-xs truncate">{entry.description}</TableCell>
                          <TableCell className="text-right font-mono">{formatCurrency(entry.total_debits)}</TableCell>
                          <TableCell className="text-right font-mono">{formatCurrency(entry.total_credits)}</TableCell>
                          <TableCell>{getStatusBadge(entry.status)}</TableCell>
                          <TableCell>
                            <div className="flex justify-end gap-1">
                              <Button size="icon" variant="ghost" onClick={() => openPreview(entry, "summary")} title="Vista Previa">
                                <Eye className="w-4 h-4" />
                              </Button>
                              <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                  <Button size="icon" variant="ghost" title="Exportar">
                                    <Download className="w-4 h-4" />
                                  </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end">
                                  <DropdownMenuLabel>Exportar como</DropdownMenuLabel>
                                  <DropdownMenuSeparator />
                                  <DropdownMenuItem onClick={() => exportToCSV(entry, "summary")}>
                                    <FileSpreadsheet className="w-4 h-4 mr-2" />
                                    Resumido (por cuenta)
                                  </DropdownMenuItem>
                                  <DropdownMenuItem onClick={() => exportToCSV(entry, "detailed")}>
                                    <List className="w-4 h-4 mr-2" />
                                    Detallado (por empleado)
                                  </DropdownMenuItem>
                                </DropdownMenuContent>
                              </DropdownMenu>
                              <Button size="icon" variant="ghost" onClick={() => openEditEntry(entry)} title="Editar">
                                <Edit className="w-4 h-4" />
                              </Button>
                              <Button size="icon" variant="ghost" className="text-red-500" onClick={() => handleDeleteEntry(entry)} title="Eliminar">
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Cuentas Tab */}
          <TabsContent value="cuentas" className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold">Catálogo de Cuentas</h3>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setShowCatalogSelector(true)}>
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Cargar Catálogo
                </Button>
                <Button onClick={() => { resetAccountForm(); setShowNewAccount(true); }}>
                  <Plus className="w-4 h-4 mr-2" />
                  Nueva Cuenta
                </Button>
              </div>
            </div>

            <Card>
              <CardContent className="p-0">
                {accounts.length === 0 ? (
                  <div className="text-center py-12">
                    <Settings className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                    <p className="text-slate-500 mb-4">No hay cuentas configuradas</p>
                    <Button onClick={() => setShowCatalogSelector(true)}>
                      Seleccionar Catálogo de Cuentas
                    </Button>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Código</TableHead>
                        <TableHead>Nombre</TableHead>
                        <TableHead>Tipo</TableHead>
                        <TableHead>Descripción</TableHead>
                        <TableHead className="text-right">Acciones</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {accounts.map(account => (
                        <TableRow key={account.account_id}>
                          <TableCell className="font-mono font-bold">{account.code}</TableCell>
                          <TableCell>{account.name}</TableCell>
                          <TableCell>{getAccountTypeBadge(account.account_type)}</TableCell>
                          <TableCell className="text-slate-500 max-w-xs truncate">
                            {account.description || "-"}
                          </TableCell>
                          <TableCell>
                            <div className="flex justify-end gap-1">
                              <Button size="icon" variant="ghost" onClick={() => openEditAccount(account)}>
                                <Edit className="w-4 h-4" />
                              </Button>
                              <Button size="icon" variant="ghost" className="text-red-500" onClick={() => handleDeleteAccount(account.account_id)}>
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* New/Edit Entry Dialog */}
        <Dialog open={showNewEntry || showEditEntry} onOpenChange={(open) => { if (!open) { setShowNewEntry(false); setShowEditEntry(false); setSelectedEntry(null); } }}>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{showEditEntry ? "Editar Asiento" : "Nuevo Asiento de Diario"}</DialogTitle>
              <DialogDescription>
                {showEditEntry ? "Modifique los datos del asiento contable" : "Complete los datos para crear un nuevo asiento"}
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="space-y-2">
                  <Label>Fecha</Label>
                  <Input 
                    type="date" 
                    value={entryForm.entry_date}
                    onChange={(e) => setEntryForm({...entryForm, entry_date: e.target.value})}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Referencia</Label>
                  <Input 
                    value={entryForm.reference}
                    onChange={(e) => setEntryForm({...entryForm, reference: e.target.value})}
                    placeholder="Ej: FAC-001"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Período</Label>
                  <Input 
                    type="month" 
                    value={entryForm.period}
                    onChange={(e) => setEntryForm({...entryForm, period: e.target.value})}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Tipo</Label>
                  <Select value={entryForm.entry_type} onValueChange={(v) => setEntryForm({...entryForm, entry_type: v})}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="manual">Manual</SelectItem>
                      <SelectItem value="payroll">Nómina</SelectItem>
                      <SelectItem value="adjustment">Ajuste</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Descripción</Label>
                <Input 
                  value={entryForm.description}
                  onChange={(e) => setEntryForm({...entryForm, description: e.target.value})}
                  placeholder="Descripción del asiento"
                />
              </div>

              {/* Lines */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Líneas del Asiento</Label>
                  <Button type="button" variant="outline" size="sm" onClick={addLine}>
                    <Plus className="w-4 h-4 mr-1" />
                    Agregar Línea
                  </Button>
                </div>

                <div className="border rounded-lg overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-slate-50 dark:bg-slate-800">
                        <TableHead className="w-40">Cuenta</TableHead>
                        <TableHead>Descripción</TableHead>
                        <TableHead className="w-32 text-right">Débito</TableHead>
                        <TableHead className="w-32 text-right">Crédito</TableHead>
                        <TableHead className="w-12"></TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {entryForm.lines.map((line, index) => (
                        <TableRow key={index}>
                          <TableCell>
                            <Select 
                              value={line.account_code} 
                              onValueChange={(v) => updateLine(index, 'account_code', v)}
                            >
                              <SelectTrigger>
                                <SelectValue placeholder="Cuenta" />
                              </SelectTrigger>
                              <SelectContent>
                                {accounts.map(acc => (
                                  <SelectItem key={acc.code} value={acc.code}>
                                    {acc.code} - {acc.name}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </TableCell>
                          <TableCell>
                            <Input 
                              value={line.description}
                              onChange={(e) => updateLine(index, 'description', e.target.value)}
                              placeholder="Detalle"
                            />
                          </TableCell>
                          <TableCell>
                            <Input 
                              type="number"
                              step="0.01"
                              className="text-right"
                              value={line.debit || ""}
                              onChange={(e) => updateLine(index, 'debit', e.target.value)}
                            />
                          </TableCell>
                          <TableCell>
                            <Input 
                              type="number"
                              step="0.01"
                              className="text-right"
                              value={line.credit || ""}
                              onChange={(e) => updateLine(index, 'credit', e.target.value)}
                            />
                          </TableCell>
                          <TableCell>
                            {entryForm.lines.length > 1 && (
                              <Button type="button" variant="ghost" size="icon" onClick={() => removeLine(index)}>
                                <X className="w-4 h-4 text-red-500" />
                              </Button>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                      {/* Totals Row */}
                      <TableRow className="bg-slate-50 font-bold">
                        <TableCell colSpan={2} className="text-right">TOTALES:</TableCell>
                        <TableCell className="text-right font-mono">{formatCurrency(getTotalDebits())}</TableCell>
                        <TableCell className="text-right font-mono">{formatCurrency(getTotalCredits())}</TableCell>
                        <TableCell></TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </div>

                {/* Balance indicator */}
                <div className={`flex items-center gap-2 p-3 rounded-lg ${isBalanced() ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'}`}>
                  {isBalanced() ? (
                    <>
                      <CheckCircle className="w-5 h-5" />
                      <span>Asiento balanceado</span>
                    </>
                  ) : (
                    <>
                      <AlertTriangle className="w-5 h-5" />
                      <span>Diferencia: {formatCurrency(Math.abs(getTotalDebits() - getTotalCredits()))}</span>
                    </>
                  )}
                </div>
              </div>

              <div className="space-y-2">
                <Label>Notas (Opcional)</Label>
                <Textarea 
                  value={entryForm.notes}
                  onChange={(e) => setEntryForm({...entryForm, notes: e.target.value})}
                  placeholder="Notas adicionales..."
                  rows={2}
                />
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => { setShowNewEntry(false); setShowEditEntry(false); }}>
                Cancelar
              </Button>
              <Button 
                onClick={showEditEntry ? handleUpdateEntry : handleCreateEntry}
                disabled={!isBalanced()}
              >
                {showEditEntry ? "Guardar Cambios" : "Crear Asiento"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* New/Edit Account Dialog */}
        <Dialog open={showNewAccount || showEditAccount} onOpenChange={(open) => { if (!open) { setShowNewAccount(false); setShowEditAccount(false); setSelectedAccount(null); } }}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{showEditAccount ? "Editar Cuenta" : "Nueva Cuenta Contable"}</DialogTitle>
              <DialogDescription>
                {showEditAccount ? "Modifique los datos de la cuenta" : "Complete los datos para crear una nueva cuenta"}
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Código</Label>
                  <Input 
                    value={accountForm.code}
                    onChange={(e) => setAccountForm({...accountForm, code: e.target.value})}
                    placeholder="Ej: 5101"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Tipo de Cuenta</Label>
                  <Select value={accountForm.account_type} onValueChange={(v) => setAccountForm({...accountForm, account_type: v})}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="asset">Activo</SelectItem>
                      <SelectItem value="liability">Pasivo</SelectItem>
                      <SelectItem value="equity">Capital</SelectItem>
                      <SelectItem value="income">Ingreso</SelectItem>
                      <SelectItem value="expense">Gasto</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Nombre de la Cuenta</Label>
                <Input 
                  value={accountForm.name}
                  onChange={(e) => setAccountForm({...accountForm, name: e.target.value})}
                  placeholder="Ej: Gastos de Sueldos y Salarios"
                />
              </div>

              <div className="space-y-2">
                <Label>Código Padre (Opcional)</Label>
                <Input 
                  value={accountForm.parent_code}
                  onChange={(e) => setAccountForm({...accountForm, parent_code: e.target.value})}
                  placeholder="Ej: 51"
                />
              </div>

              <div className="space-y-2">
                <Label>Descripción (Opcional)</Label>
                <Textarea 
                  value={accountForm.description}
                  onChange={(e) => setAccountForm({...accountForm, description: e.target.value})}
                  placeholder="Descripción de la cuenta..."
                  rows={2}
                />
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => { setShowNewAccount(false); setShowEditAccount(false); }}>
                Cancelar
              </Button>
              <Button onClick={showEditAccount ? handleUpdateAccount : handleCreateAccount}>
                {showEditAccount ? "Guardar Cambios" : "Crear Cuenta"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Catalog Selector Dialog */}
        <Dialog open={showCatalogSelector} onOpenChange={setShowCatalogSelector}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Seleccionar Catálogo de Cuentas</DialogTitle>
              <DialogDescription>
                Elija una plantilla de catálogo de cuentas. Esto reemplazará todas las cuentas existentes.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              {catalogTemplates.map((template) => (
                <div 
                  key={template.catalog_id}
                  className="border rounded-lg p-4 hover:border-emerald-500 hover:bg-emerald-50 cursor-pointer transition-colors"
                  onClick={() => loadCatalogTemplate(template.catalog_id)}
                  data-testid={`catalog-${template.catalog_id}`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-semibold text-slate-800 dark:text-slate-100">{template.name}</h4>
                      <p className="text-sm text-slate-500 mt-1">{template.description}</p>
                    </div>
                    <Badge variant="secondary" className="ml-4">
                      {template.account_count} cuentas
                    </Badge>
                  </div>
                </div>
              ))}
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setShowCatalogSelector(false)}>
                Cancelar
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* CSV Preview Dialog */}
        <Dialog open={showPreview} onOpenChange={setShowPreview}>
          <DialogContent className="max-w-4xl max-h-[85vh] overflow-hidden flex flex-col">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Eye className="w-5 h-5" />
                Vista Previa - {previewFormat === "summary" ? "Resumido" : "Detallado"}
              </DialogTitle>
              <DialogDescription>
                {previewData?.description || "Asiento contable"}
              </DialogDescription>
            </DialogHeader>

            {/* Format Toggle */}
            <div className="flex items-center gap-2 py-2 border-b">
              <span className="text-sm text-slate-500">Formato:</span>
              <Button
                size="sm"
                variant={previewFormat === "summary" ? "default" : "outline"}
                onClick={() => changePreviewFormat("summary")}
                disabled={previewLoading}
              >
                <FileSpreadsheet className="w-4 h-4 mr-1" />
                Resumido
              </Button>
              <Button
                size="sm"
                variant={previewFormat === "detailed" ? "default" : "outline"}
                onClick={() => changePreviewFormat("detailed")}
                disabled={previewLoading}
              >
                <List className="w-4 h-4 mr-1" />
                Detallado
              </Button>
            </div>

            {/* Preview Content */}
            <div className="flex-1 overflow-auto min-h-0">
              {previewLoading ? (
                <div className="flex items-center justify-center py-12">
                  <RefreshCw className="w-8 h-8 animate-spin text-slate-400" />
                </div>
              ) : previewData ? (
                <div className="space-y-4">
                  {/* Header Info */}
                  <div className="grid grid-cols-3 gap-4 p-3 bg-slate-50 dark:bg-slate-800 rounded-lg text-sm">
                    <div>
                      <span className="text-slate-500">Fecha:</span>
                      <span className="ml-2 font-medium">{previewData.entry_date}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Referencia:</span>
                      <span className="ml-2 font-medium">{previewData.reference || "-"}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">ID:</span>
                      <span className="ml-2 font-mono text-xs">{previewData.entry_id}</span>
                    </div>
                  </div>

                  {/* Data Table */}
                  <div className="border rounded-lg overflow-hidden">
                    <Table>
                      <TableHeader>
                        <TableRow className="bg-slate-100 dark:bg-slate-800">
                          <TableHead className="font-semibold">Código</TableHead>
                          <TableHead className="font-semibold">Nombre de Cuenta</TableHead>
                          {previewData.has_cost_center && (
                            <TableHead className="font-semibold">Centro de Costos</TableHead>
                          )}
                          {previewFormat === "detailed" && (
                            <TableHead className="font-semibold">Empleado</TableHead>
                          )}
                          <TableHead className="text-right font-semibold">Débito</TableHead>
                          <TableHead className="text-right font-semibold">Crédito</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {previewData.rows?.map((row, idx) => (
                          <TableRow key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800">
                            <TableCell className="font-mono text-sm">{row.account_code}</TableCell>
                            <TableCell>{row.account_name}</TableCell>
                            {previewData.has_cost_center && (
                              <TableCell>{row.cost_center || "-"}</TableCell>
                            )}
                            {previewFormat === "detailed" && (
                              <TableCell className="text-slate-600">{row.employee_name || "-"}</TableCell>
                            )}
                            <TableCell className="text-right font-mono">
                              {row.debit > 0 ? formatCurrency(row.debit) : "-"}
                            </TableCell>
                            <TableCell className="text-right font-mono">
                              {row.credit > 0 ? formatCurrency(row.credit) : "-"}
                            </TableCell>
                          </TableRow>
                        ))}
                        {/* Totals Row */}
                        <TableRow className="bg-slate-100 dark:bg-slate-800 font-bold border-t-2">
                          <TableCell colSpan={previewData.has_cost_center ? (previewFormat === "detailed" ? 4 : 3) : (previewFormat === "detailed" ? 3 : 2)} className="text-right">
                            TOTALES
                          </TableCell>
                          <TableCell className="text-right font-mono text-emerald-600 dark:text-emerald-400">
                            {formatCurrency(previewData.totals?.debits || 0)}
                          </TableCell>
                          <TableCell className="text-right font-mono text-red-600 dark:text-red-400">
                            {formatCurrency(previewData.totals?.credits || 0)}
                          </TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </div>

                  {/* Row Count */}
                  <div className="text-sm text-slate-500 text-right">
                    {previewData.rows?.length || 0} líneas
                  </div>
                </div>
              ) : (
                <div className="text-center py-12 text-slate-500">
                  No hay datos para mostrar
                </div>
              )}
            </div>

            <DialogFooter className="border-t pt-4">
              <Button variant="outline" onClick={() => setShowPreview(false)}>
                Cerrar
              </Button>
              <Button onClick={downloadFromPreview} disabled={!previewData}>
                <Download className="w-4 h-4 mr-2" />
                Descargar CSV
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
