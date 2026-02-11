import { useState, useEffect, useCallback } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Receipt,
  Plus,
  Search,
  MoreHorizontal,
  Eye,
  CheckCircle,
  XCircle,
  Clock,
  DollarSign,
  Calendar,
  MapPin,
  FileText,
  Upload,
  Plane,
  Car,
  Hotel,
  UtensilsCrossed,
  Package,
  GraduationCap,
  Shirt,
  FileCheck,
  AlertCircle,
  ChevronRight,
  Send,
  History,
  Filter,
  RefreshCw,
  Banknote,
  ArrowRight,
  User,
  Building2
} from "lucide-react";
import axios from "axios";
import { useTranslation } from "react-i18next";
import { API, useAuth } from "@/App";
import { toast } from "sonner";
import { Switch } from "@/components/ui/switch";

// Category icons mapping
const categoryIcons = {
  transporte: Car,
  alojamiento: Hotel,
  alimentacion: UtensilsCrossed,
  materiales: Package,
  viajes: Plane,
  administrativos: FileText,
  educacion: GraduationCap,
  uniformes: Shirt,
  otros: Receipt
};

// Status badge styles - now uses translation keys
const getStatusConfig = (t) => ({
  pending: { label: t("expenses.status.pending"), color: "bg-amber-100 text-amber-700 dark:text-amber-400", icon: Clock },
  approved_manager: { label: t("expenses.status.approved_manager"), color: "bg-blue-100 text-blue-700 dark:text-blue-400", icon: CheckCircle },
  approved_admin: { label: t("expenses.status.approved_admin"), color: "bg-emerald-100 text-emerald-700 dark:text-emerald-400", icon: CheckCircle },
  rejected: { label: t("expenses.status.rejected"), color: "bg-red-100 text-red-700", icon: XCircle },
  in_progress: { label: t("expenses.status.in_progress"), color: "bg-purple-100 text-purple-700", icon: RefreshCw },
  pending_verification: { label: t("expenses.status.pending_verification"), color: "bg-orange-100 text-orange-700", icon: FileCheck },
  completed: { label: t("expenses.status.completed"), color: "bg-green-100 text-green-700", icon: CheckCircle },
  cancelled: { label: t("expenses.status.cancelled"), color: "bg-slate-100 text-slate-500 dark:text-slate-400", icon: XCircle }
});

// Expense type labels - now uses translation keys
const getExpenseTypeLabels = (t) => ({
  travel: t("expenses.types.travel"),
  administrative: t("expenses.types.administrative"),
  accommodation: t("expenses.types.accommodation"),
  meals: t("expenses.types.meals"),
  transportation: t("expenses.types.transportation"),
  other: t("expenses.types.other")
});

export default function ExpensesPage() {
  const { t } = useTranslation();
  const { getAuthHeaders, user } = useAuth();
  
  // Initialize status styles and labels with translations
  const statusStyles = getStatusConfig(t);
  const expenseTypeLabels = getExpenseTypeLabels(t);
  
  const [activeTab, setActiveTab] = useState("my-requests");
  const [loading, setLoading] = useState(true);
  const [requests, setRequests] = useState([]);
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [categories, setCategories] = useState([]);
  const [summary, setSummary] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  
  // Modal states
  const [showNewRequest, setShowNewRequest] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [showApproval, setShowApproval] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [requestDetails, setRequestDetails] = useState(null);
  
  // Form state
  const [formData, setFormData] = useState({
    title: "",
    expense_type: "travel",
    description: "",
    destination: "",
    start_date: "",
    end_date: "",
    estimated_budget: "",
    requires_advance: false,
    advance_amount: "",
    advance_date: "",
    notes: "",
    budget_breakdown: []
  });
  
  const [approvalData, setApprovalData] = useState({
    action: "",
    comments: ""
  });

  const isManager = user?.role === "manager" || user?.role === "admin" || user?.role === "hr_manager";

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [requestsRes, categoriesRes] = await Promise.all([
        axios.get(`${API}/expenses/requests`, {
          headers: getAuthHeaders(),
          withCredentials: true
        }),
        axios.get(`${API}/expenses/categories`, {
          headers: getAuthHeaders(),
          withCredentials: true
        })
      ]);
      
      setRequests(requestsRes.data);
      setCategories(categoriesRes.data);
      
      // Fetch pending approvals if user is manager/admin
      if (isManager) {
        const approvalsRes = await axios.get(`${API}/expenses/requests/pending-approval`, {
          headers: getAuthHeaders(),
          withCredentials: true
        });
        setPendingApprovals(approvalsRes.data);
        
        // Fetch summary
        const summaryRes = await axios.get(`${API}/expenses/reports/summary`, {
          headers: getAuthHeaders(),
          withCredentials: true
        });
        setSummary(summaryRes.data);
      }
    } catch (error) {
      console.error("Error fetching data:", error);
      toast.error(t("expenses.messages.errorLoad"));
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders, isManager]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleCreateRequest = async () => {
    if (!formData.title || !formData.description || !formData.start_date || !formData.end_date || !formData.estimated_budget) {
      toast.error(t("expenses.messages.fillRequired"));
      return;
    }
    
    try {
      const payload = {
        ...formData,
        estimated_budget: parseFloat(formData.estimated_budget),
        advance_amount: formData.requires_advance ? parseFloat(formData.advance_amount) : null
      };
      
      await axios.post(`${API}/expenses/requests`, payload, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      
      toast.success(t("expenses.messages.created"));
      setShowNewRequest(false);
      resetForm();
      fetchData();
    } catch (error) {
      console.error("Error creating request:", error);
      toast.error(error.response?.data?.detail || t("expenses.messages.errorCreate"));
    }
  };

  const handleViewDetails = async (request) => {
    try {
      const response = await axios.get(`${API}/expenses/requests/${request.request_id}`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setRequestDetails(response.data);
      setSelectedRequest(request);
      setShowDetails(true);
    } catch (error) {
      console.error("Error fetching details:", error);
      toast.error(t("expenses.messages.errorLoad"));
    }
  };

  const handleApprovalAction = async () => {
    if (!approvalData.action) {
      toast.error(t("expenses.messages.selectAction"));
      return;
    }
    
    try {
      await axios.post(
        `${API}/expenses/requests/${selectedRequest.request_id}/approve`,
        approvalData,
        {
          headers: getAuthHeaders(),
          withCredentials: true
        }
      );
      
      toast.success(approvalData.action === "approve" ? t("expenses.messages.approved") : t("expenses.messages.rejected"));
      setShowApproval(false);
      setApprovalData({ action: "", comments: "" });
      fetchData();
    } catch (error) {
      console.error("Error processing approval:", error);
      toast.error(error.response?.data?.detail || t("expenses.messages.errorApprove"));
    }
  };

  const handleCancelRequest = async (requestId) => {
    try {
      await axios.delete(`${API}/expenses/requests/${requestId}`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success("Solicitud cancelada");
      fetchData();
    } catch (error) {
      console.error("Error cancelling request:", error);
      toast.error(error.response?.data?.detail || "Error al cancelar la solicitud");
    }
  };

  const resetForm = () => {
    setFormData({
      title: "",
      expense_type: "travel",
      description: "",
      destination: "",
      start_date: "",
      end_date: "",
      estimated_budget: "",
      requires_advance: false,
      advance_amount: "",
      advance_date: "",
      notes: "",
      budget_breakdown: []
    });
  };

  const addBudgetItem = () => {
    setFormData(prev => ({
      ...prev,
      budget_breakdown: [
        ...prev.budget_breakdown,
        { category: "transporte", amount: "", description: "" }
      ]
    }));
  };

  const updateBudgetItem = (index, field, value) => {
    setFormData(prev => ({
      ...prev,
      budget_breakdown: prev.budget_breakdown.map((item, i) =>
        i === index ? { ...item, [field]: value } : item
      )
    }));
  };

  const removeBudgetItem = (index) => {
    setFormData(prev => ({
      ...prev,
      budget_breakdown: prev.budget_breakdown.filter((_, i) => i !== index)
    }));
  };

  // Filter requests
  const filteredRequests = requests.filter(req => {
    const matchesSearch = searchQuery === "" ||
      req.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      req.employee_name?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || req.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-DO', {
      style: 'currency',
      currency: 'DOP'
    }).format(amount || 0);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleDateString('es-DO', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    });
  };

  return (
    <DashboardLayout title="Gastos y Viáticos">
      <div className="space-y-6">
        {/* Header Stats */}
        {isManager && summary && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="border-0 shadow-sm bg-gradient-to-br from-blue-50 to-white">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Total Solicitudes</p>
                    <p className="text-2xl font-bold text-slate-800 dark:text-slate-100">{summary.total_requests}</p>
                  </div>
                  <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center">
                    <Receipt className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card className="border-0 shadow-sm bg-gradient-to-br from-amber-50 to-white">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Anticipos Pendientes</p>
                    <p className="text-2xl font-bold text-slate-800 dark:text-slate-100">{summary.pending_advances?.count || 0}</p>
                  </div>
                  <div className="w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center">
                    <Banknote className="w-5 h-5 text-amber-600 dark:text-amber-400" />
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card className="border-0 shadow-sm bg-gradient-to-br from-emerald-50 to-white">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Total Estimado</p>
                    <p className="text-2xl font-bold text-slate-800 dark:text-slate-100">{formatCurrency(summary.total_estimated)}</p>
                  </div>
                  <div className="w-10 h-10 rounded-xl bg-emerald-100 flex items-center justify-center">
                    <DollarSign className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card className="border-0 shadow-sm bg-gradient-to-br from-purple-50 to-white">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Ahorro</p>
                    <p className="text-2xl font-bold text-slate-800 dark:text-slate-100">{formatCurrency(summary.savings)}</p>
                  </div>
                  <div className="w-10 h-10 rounded-xl bg-purple-100 flex items-center justify-center">
                    <ArrowRight className="w-5 h-5 text-purple-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Main Content */}
        <Card className="border-0 shadow-sm">
          <CardHeader className="border-b bg-slate-50/50">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Receipt className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                  Solicitudes de Gastos y Viáticos
                </CardTitle>
                <CardDescription>Gestiona solicitudes de gastos, anticipos y reembolsos</CardDescription>
              </div>
              <Button onClick={() => setShowNewRequest(true)} className="bg-emerald-600 hover:bg-emerald-700" data-testid="new-expense-btn">
                <Plus className="w-4 h-4 mr-2" />
                Nueva Solicitud
              </Button>
            </div>
          </CardHeader>
          
          <CardContent className="p-0">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <div className="border-b px-4">
                <TabsList className="h-12 bg-transparent p-0 gap-4">
                  <TabsTrigger 
                    value="my-requests" 
                    className="data-[state=active]:border-b-2 data-[state=active]:border-emerald-600 data-[state=active]:text-emerald-600 rounded-none bg-transparent px-1 pb-3"
                  >
                    Mis Solicitudes
                  </TabsTrigger>
                  {isManager && (
                    <TabsTrigger 
                      value="approvals" 
                      className="data-[state=active]:border-b-2 data-[state=active]:border-emerald-600 data-[state=active]:text-emerald-600 rounded-none bg-transparent px-1 pb-3"
                    >
                      Por Aprobar
                      {pendingApprovals.length > 0 && (
                        <Badge className="ml-2 bg-amber-100 text-amber-700 hover:bg-amber-100 dark:bg-amber-900/50">
                          {pendingApprovals.length}
                        </Badge>
                      )}
                    </TabsTrigger>
                  )}
                  {isManager && (
                    <TabsTrigger 
                      value="all" 
                      className="data-[state=active]:border-b-2 data-[state=active]:border-emerald-600 data-[state=active]:text-emerald-600 rounded-none bg-transparent px-1 pb-3"
                    >
                      Todas
                    </TabsTrigger>
                  )}
                </TabsList>
              </div>

              {/* Filters */}
              <div className="p-4 border-b flex flex-col md:flex-row gap-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input
                    placeholder="Buscar por título o empleado..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                    data-testid="expense-search"
                  />
                </div>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-full md:w-48" data-testid="status-filter">
                    <Filter className="w-4 h-4 mr-2" />
                    <SelectValue placeholder="Estado" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todos los estados</SelectItem>
                    <SelectItem value="pending">Pendiente</SelectItem>
                    <SelectItem value="approved_manager">Aprobado (Gerente)</SelectItem>
                    <SelectItem value="approved_admin">Aprobado</SelectItem>
                    <SelectItem value="in_progress">En Progreso</SelectItem>
                    <SelectItem value="completed">Completado</SelectItem>
                    <SelectItem value="rejected">Rechazado</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <TabsContent value="my-requests" className="m-0">
                <RequestsTable 
                  requests={filteredRequests}
                  loading={loading}
                  onView={handleViewDetails}
                  onCancel={handleCancelRequest}
                  formatCurrency={formatCurrency}
                  formatDate={formatDate}
                />
              </TabsContent>

              <TabsContent value="approvals" className="m-0">
                <RequestsTable 
                  requests={pendingApprovals}
                  loading={loading}
                  onView={handleViewDetails}
                  onApprove={(req) => {
                    setSelectedRequest(req);
                    setShowApproval(true);
                  }}
                  isApprovalView
                  formatCurrency={formatCurrency}
                  formatDate={formatDate}
                />
              </TabsContent>

              <TabsContent value="all" className="m-0">
                <RequestsTable 
                  requests={filteredRequests}
                  loading={loading}
                  onView={handleViewDetails}
                  onApprove={(req) => {
                    setSelectedRequest(req);
                    setShowApproval(true);
                  }}
                  isApprovalView
                  formatCurrency={formatCurrency}
                  formatDate={formatDate}
                />
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {/* New Request Dialog */}
        <Dialog open={showNewRequest} onOpenChange={setShowNewRequest}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Receipt className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                Nueva Solicitud de Gastos
              </DialogTitle>
              <DialogDescription>
                Complete el formulario para crear una nueva solicitud de gastos o viáticos
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-6 py-4">
              {/* Basic Info */}
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="md:col-span-2">
                    <Label>Título de la Solicitud *</Label>
                    <Input
                      placeholder="Ej: Viaje de negocios a Santiago"
                      value={formData.title}
                      onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                      data-testid="expense-title"
                    />
                  </div>
                  
                  <div>
                    <Label>Tipo de Gasto *</Label>
                    <Select 
                      value={formData.expense_type} 
                      onValueChange={(v) => setFormData(prev => ({ ...prev, expense_type: v }))}
                    >
                      <SelectTrigger data-testid="expense-type">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="travel">Viaje de Negocios</SelectItem>
                        <SelectItem value="administrative">Gastos Administrativos</SelectItem>
                        <SelectItem value="accommodation">Alojamiento</SelectItem>
                        <SelectItem value="meals">Alimentación</SelectItem>
                        <SelectItem value="transportation">Transporte</SelectItem>
                        <SelectItem value="other">Otros</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <Label>Destino</Label>
                    <Input
                      placeholder="Ciudad o lugar"
                      value={formData.destination}
                      onChange={(e) => setFormData(prev => ({ ...prev, destination: e.target.value }))}
                      data-testid="expense-destination"
                    />
                  </div>
                </div>
                
                <div>
                  <Label>Descripción / Justificación *</Label>
                  <Textarea
                    placeholder="Describa el propósito y justificación del gasto..."
                    value={formData.description}
                    onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                    rows={3}
                    data-testid="expense-description"
                  />
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <Label>Fecha Inicio *</Label>
                    <Input
                      type="date"
                      value={formData.start_date}
                      onChange={(e) => setFormData(prev => ({ ...prev, start_date: e.target.value }))}
                      data-testid="expense-start-date"
                    />
                  </div>
                  
                  <div>
                    <Label>Fecha Fin *</Label>
                    <Input
                      type="date"
                      value={formData.end_date}
                      onChange={(e) => setFormData(prev => ({ ...prev, end_date: e.target.value }))}
                      data-testid="expense-end-date"
                    />
                  </div>
                  
                  <div>
                    <Label>Presupuesto Estimado (RD$) *</Label>
                    <Input
                      type="number"
                      placeholder="0.00"
                      value={formData.estimated_budget}
                      onChange={(e) => setFormData(prev => ({ ...prev, estimated_budget: e.target.value }))}
                      data-testid="expense-budget"
                    />
                  </div>
                </div>
              </div>

              {/* Budget Breakdown */}
              <div className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <Label className="text-base font-medium">Desglose del Presupuesto</Label>
                  <Button variant="outline" size="sm" onClick={addBudgetItem} data-testid="add-budget-item">
                    <Plus className="w-4 h-4 mr-1" /> Agregar
                  </Button>
                </div>
                
                {formData.budget_breakdown.length === 0 ? (
                  <p className="text-sm text-slate-500 text-center py-4">
                    No hay items en el desglose. Haga clic en "Agregar" para incluir categorías.
                  </p>
                ) : (
                  <div className="space-y-3">
                    {formData.budget_breakdown.map((item, index) => (
                      <div key={index} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                        <Select 
                          value={item.category}
                          onValueChange={(v) => updateBudgetItem(index, 'category', v)}
                        >
                          <SelectTrigger className="w-40">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {categories.map(cat => (
                              <SelectItem key={cat.id} value={cat.id}>{cat.name}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <Input
                          placeholder="Monto"
                          type="number"
                          value={item.amount}
                          onChange={(e) => updateBudgetItem(index, 'amount', e.target.value)}
                          className="w-32"
                        />
                        <Input
                          placeholder="Descripción"
                          value={item.description}
                          onChange={(e) => updateBudgetItem(index, 'description', e.target.value)}
                          className="flex-1"
                        />
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          onClick={() => removeBudgetItem(index)}
                          className="text-red-500 hover:text-red-700"
                        >
                          <XCircle className="w-4 h-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Advance Request */}
              <div className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <Label className="text-base font-medium">Solicitar Anticipo</Label>
                    <p className="text-sm text-slate-500 dark:text-slate-400">¿Necesita un anticipo antes del viaje/gasto?</p>
                  </div>
                  <Switch
                    checked={formData.requires_advance}
                    onCheckedChange={(v) => setFormData(prev => ({ ...prev, requires_advance: v }))}
                    data-testid="expense-requires-advance"
                  />
                </div>
                
                {formData.requires_advance && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 pt-4 border-t">
                    <div>
                      <Label>Monto del Anticipo (RD$)</Label>
                      <Input
                        type="number"
                        placeholder="0.00"
                        value={formData.advance_amount}
                        onChange={(e) => setFormData(prev => ({ ...prev, advance_amount: e.target.value }))}
                        data-testid="expense-advance-amount"
                      />
                    </div>
                    <div>
                      <Label>Fecha Necesaria</Label>
                      <Input
                        type="date"
                        value={formData.advance_date}
                        onChange={(e) => setFormData(prev => ({ ...prev, advance_date: e.target.value }))}
                        data-testid="expense-advance-date"
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Notes */}
              <div>
                <Label>Notas Adicionales</Label>
                <Textarea
                  placeholder="Información adicional relevante..."
                  value={formData.notes}
                  onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                  rows={2}
                  data-testid="expense-notes"
                />
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setShowNewRequest(false)}>
                Cancelar
              </Button>
              <Button onClick={handleCreateRequest} className="bg-emerald-600 hover:bg-emerald-700" data-testid="submit-expense">
                <Send className="w-4 h-4 mr-2" />
                Enviar Solicitud
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Request Details Dialog */}
        <Dialog open={showDetails} onOpenChange={setShowDetails}>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Eye className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                Detalles de la Solicitud
              </DialogTitle>
            </DialogHeader>

            {requestDetails && (
              <div className="space-y-6 py-4">
                {/* Status Banner */}
                <div className={`p-4 rounded-lg ${
                  requestDetails.request.status === 'approved_admin' ? 'bg-emerald-50 border border-emerald-200' :
                  requestDetails.request.status === 'rejected' ? 'bg-red-50 border border-red-200' :
                  requestDetails.request.status === 'pending' ? 'bg-amber-50 border border-amber-200' :
                  'bg-blue-50 border border-blue-200'
                }`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {statusStyles[requestDetails.request.status]?.icon && (() => {
                        const StatusIcon = statusStyles[requestDetails.request.status].icon;
                        return (
                          <StatusIcon className={`w-5 h-5 ${
                            requestDetails.request.status === 'approved_admin' ? 'text-emerald-600' :
                            requestDetails.request.status === 'rejected' ? 'text-red-600' :
                            requestDetails.request.status === 'pending' ? 'text-amber-600' :
                            'text-blue-600'
                          }`} />
                        );
                      })()}
                      <div>
                        <p className="font-medium">{statusStyles[requestDetails.request.status]?.label || requestDetails.request.status}</p>
                        <p className="text-sm text-slate-500 dark:text-slate-400">
                          Creado: {formatDate(requestDetails.request.created_at)}
                        </p>
                      </div>
                    </div>
                    <Badge className={statusStyles[requestDetails.request.status]?.color}>
                      {requestDetails.request.request_id}
                    </Badge>
                  </div>
                </div>

                {/* Request Info */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div>
                      <Label className="text-slate-500 dark:text-slate-400">Título</Label>
                      <p className="font-medium">{requestDetails.request.title}</p>
                    </div>
                    <div>
                      <Label className="text-slate-500 dark:text-slate-400">Tipo de Gasto</Label>
                      <p>{expenseTypeLabels[requestDetails.request.expense_type] || requestDetails.request.expense_type}</p>
                    </div>
                    <div>
                      <Label className="text-slate-500 dark:text-slate-400">Solicitante</Label>
                      <p className="flex items-center gap-2">
                        <User className="w-4 h-4 text-slate-400" />
                        {requestDetails.request.employee_name}
                      </p>
                    </div>
                    {requestDetails.request.department && (
                      <div>
                        <Label className="text-slate-500 dark:text-slate-400">Departamento</Label>
                        <p className="flex items-center gap-2">
                          <Building2 className="w-4 h-4 text-slate-400" />
                          {requestDetails.request.department}
                        </p>
                      </div>
                    )}
                  </div>
                  
                  <div className="space-y-4">
                    <div>
                      <Label className="text-slate-500 dark:text-slate-400">Período</Label>
                      <p className="flex items-center gap-2">
                        <Calendar className="w-4 h-4 text-slate-400" />
                        {formatDate(requestDetails.request.start_date)} - {formatDate(requestDetails.request.end_date)}
                      </p>
                    </div>
                    {requestDetails.request.destination && (
                      <div>
                        <Label className="text-slate-500 dark:text-slate-400">Destino</Label>
                        <p className="flex items-center gap-2">
                          <MapPin className="w-4 h-4 text-slate-400" />
                          {requestDetails.request.destination}
                        </p>
                      </div>
                    )}
                    <div>
                      <Label className="text-slate-500 dark:text-slate-400">Presupuesto Estimado</Label>
                      <p className="text-lg font-semibold text-emerald-600 dark:text-emerald-400">
                        {formatCurrency(requestDetails.request.estimated_budget)}
                      </p>
                    </div>
                    {requestDetails.request.actual_spent > 0 && (
                      <div>
                        <Label className="text-slate-500 dark:text-slate-400">Gasto Real</Label>
                        <p className="text-lg font-semibold">
                          {formatCurrency(requestDetails.request.actual_spent)}
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Description */}
                <div>
                  <Label className="text-slate-500 dark:text-slate-400">Descripción / Justificación</Label>
                  <p className="mt-1 p-3 bg-slate-50 rounded-lg">{requestDetails.request.description}</p>
                </div>

                {/* Budget Breakdown */}
                {requestDetails.request.budget_breakdown?.length > 0 && (
                  <div>
                    <Label className="text-slate-500 mb-2 block">Desglose del Presupuesto</Label>
                    <div className="border rounded-lg overflow-hidden">
                      <Table>
                        <TableHeader>
                          <TableRow className="bg-slate-50 dark:bg-slate-800">
                            <TableHead>Categoría</TableHead>
                            <TableHead>Descripción</TableHead>
                            <TableHead className="text-right">Monto</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {requestDetails.request.budget_breakdown.map((item, i) => {
                            const CategoryIcon = categoryIcons[item.category] || Receipt;
                            return (
                              <TableRow key={i}>
                                <TableCell className="flex items-center gap-2">
                                  <CategoryIcon className="w-4 h-4 text-slate-400" />
                                  {categories.find(c => c.id === item.category)?.name || item.category}
                                </TableCell>
                                <TableCell>{item.description || "-"}</TableCell>
                                <TableCell className="text-right font-medium">
                                  {formatCurrency(item.amount)}
                                </TableCell>
                              </TableRow>
                            );
                          })}
                        </TableBody>
                      </Table>
                    </div>
                  </div>
                )}

                {/* Advances */}
                {requestDetails.advances?.length > 0 && (
                  <div>
                    <Label className="text-slate-500 mb-2 block">Anticipos</Label>
                    <div className="space-y-2">
                      {requestDetails.advances.map((adv, i) => (
                        <div key={i} className="flex items-center justify-between p-3 bg-amber-50 border border-amber-100 rounded-lg">
                          <div className="flex items-center gap-3">
                            <Banknote className="w-5 h-5 text-amber-600 dark:text-amber-400" />
                            <div>
                              <p className="font-medium">{formatCurrency(adv.amount)}</p>
                              <p className="text-sm text-slate-500 dark:text-slate-400">
                                Estado: {adv.status === 'disbursed' ? 'Desembolsado' : 
                                        adv.status === 'approved' ? 'Aprobado' : 
                                        adv.status === 'pending' ? 'Pendiente' : adv.status}
                              </p>
                            </div>
                          </div>
                          {adv.disbursed_amount > 0 && (
                            <Badge variant="outline" className="bg-emerald-50 text-emerald-700 dark:text-emerald-400">
                              Desembolsado: {formatCurrency(adv.disbursed_amount)}
                            </Badge>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Approval History */}
                {requestDetails.approval_history?.length > 0 && (
                  <div>
                    <Label className="text-slate-500 mb-2 block">Historial de Aprobaciones</Label>
                    <div className="space-y-2">
                      {requestDetails.approval_history.map((approval, i) => (
                        <div key={i} className="flex items-start gap-3 p-3 border rounded-lg">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                            approval.action === 'approve' ? 'bg-emerald-100' :
                            approval.action === 'reject' ? 'bg-red-100' :
                            'bg-blue-100'
                          }`}>
                            {approval.action === 'approve' ? (
                              <CheckCircle className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                            ) : approval.action === 'reject' ? (
                              <XCircle className="w-4 h-4 text-red-600 dark:text-red-400" />
                            ) : (
                              <History className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                            )}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center justify-between">
                              <p className="font-medium text-sm">{approval.performed_by_name || "Sistema"}</p>
                              <span className="text-xs text-slate-400">{formatDate(approval.created_at)}</span>
                            </div>
                            <p className="text-sm text-slate-600 dark:text-slate-300">
                              {approval.action === 'approve' ? 'Aprobó la solicitud' :
                               approval.action === 'reject' ? 'Rechazó la solicitud' :
                               approval.action === 'created' ? 'Creó la solicitud' :
                               approval.action}
                              {approval.role && <span className="text-slate-400"> ({approval.role})</span>}
                            </p>
                            {approval.comments && (
                              <p className="text-sm text-slate-500 mt-1 italic">"{approval.comments}"</p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            <DialogFooter>
              <Button variant="outline" onClick={() => setShowDetails(false)}>
                Cerrar
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Approval Dialog */}
        <Dialog open={showApproval} onOpenChange={setShowApproval}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <FileCheck className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                Aprobar / Rechazar Solicitud
              </DialogTitle>
              <DialogDescription>
                {selectedRequest?.title}
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              {selectedRequest && (
                <div className="p-4 bg-slate-50 rounded-lg space-y-2">
                  <p><strong>Solicitante:</strong> {selectedRequest.employee_name}</p>
                  <p><strong>Monto:</strong> {formatCurrency(selectedRequest.estimated_budget)}</p>
                  <p><strong>Tipo:</strong> {expenseTypeLabels[selectedRequest.expense_type] || selectedRequest.expense_type}</p>
                </div>
              )}
              
              <div className="grid grid-cols-2 gap-3">
                <Button
                  variant={approvalData.action === 'approve' ? 'default' : 'outline'}
                  className={approvalData.action === 'approve' ? 'bg-emerald-600 hover:bg-emerald-700' : ''}
                  onClick={() => setApprovalData(prev => ({ ...prev, action: 'approve' }))}
                  data-testid="approve-btn"
                >
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Aprobar
                </Button>
                <Button
                  variant={approvalData.action === 'reject' ? 'destructive' : 'outline'}
                  onClick={() => setApprovalData(prev => ({ ...prev, action: 'reject' }))}
                  data-testid="reject-btn"
                >
                  <XCircle className="w-4 h-4 mr-2" />
                  Rechazar
                </Button>
              </div>
              
              <div>
                <Label>Comentarios</Label>
                <Textarea
                  placeholder="Agregue un comentario (opcional)..."
                  value={approvalData.comments}
                  onChange={(e) => setApprovalData(prev => ({ ...prev, comments: e.target.value }))}
                  rows={3}
                  data-testid="approval-comments"
                />
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setShowApproval(false)}>
                Cancelar
              </Button>
              <Button 
                onClick={handleApprovalAction}
                disabled={!approvalData.action}
                className={approvalData.action === 'approve' ? 'bg-emerald-600 hover:bg-emerald-700' : 
                          approvalData.action === 'reject' ? 'bg-red-600 hover:bg-red-700' : ''}
                data-testid="confirm-approval"
              >
                Confirmar
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}

// Requests Table Component
function RequestsTable({ 
  requests, 
  loading, 
  onView, 
  onCancel, 
  onApprove, 
  isApprovalView = false,
  formatCurrency,
  formatDate 
}) {
  if (loading) {
    return (
      <div className="p-8 text-center">
        <div className="w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-slate-500 dark:text-slate-400">Cargando solicitudes...</p>
      </div>
    );
  }

  if (requests.length === 0) {
    return (
      <div className="p-12 text-center">
        <Receipt className="w-12 h-12 mx-auto text-slate-300 mb-4" />
        <h3 className="text-lg font-medium text-slate-700 mb-2">No hay solicitudes</h3>
        <p className="text-slate-500 dark:text-slate-400">
          {isApprovalView 
            ? "No hay solicitudes pendientes de aprobación" 
            : "Cree una nueva solicitud para comenzar"
          }
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow className="bg-slate-50 dark:bg-slate-800">
            <TableHead>Solicitud</TableHead>
            <TableHead>Solicitante</TableHead>
            <TableHead>Tipo</TableHead>
            <TableHead>Período</TableHead>
            <TableHead className="text-right">Monto</TableHead>
            <TableHead>Estado</TableHead>
            <TableHead className="w-12"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {requests.map((request) => {
            const StatusIcon = statusStyles[request.status]?.icon || Clock;
            return (
              <TableRow key={request.request_id} className="hover:bg-slate-50 dark:bg-slate-800" data-testid={`expense-row-${request.request_id}`}>
                <TableCell>
                  <div>
                    <p className="font-medium text-slate-800 dark:text-slate-100">{request.title}</p>
                    <p className="text-xs text-slate-400">{request.request_id}</p>
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center">
                      <User className="w-4 h-4 text-slate-500 dark:text-slate-400" />
                    </div>
                    <div>
                      <p className="text-sm">{request.employee_name}</p>
                      <p className="text-xs text-slate-400">{request.department || '-'}</p>
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className="capitalize">
                    {expenseTypeLabels[request.expense_type] || request.expense_type}
                  </Badge>
                </TableCell>
                <TableCell>
                  <p className="text-sm">
                    {formatDate(request.start_date)}
                  </p>
                  <p className="text-xs text-slate-400">
                    a {formatDate(request.end_date)}
                  </p>
                </TableCell>
                <TableCell className="text-right">
                  <p className="font-medium">{formatCurrency(request.estimated_budget)}</p>
                  {request.requires_advance && (
                    <p className="text-xs text-amber-600 dark:text-amber-400">
                      Anticipo: {formatCurrency(request.advance_amount)}
                    </p>
                  )}
                </TableCell>
                <TableCell>
                  <Badge className={statusStyles[request.status]?.color || 'bg-slate-100 text-slate-600'}>
                    <StatusIcon className="w-3 h-3 mr-1" />
                    {statusStyles[request.status]?.label || request.status}
                  </Badge>
                </TableCell>
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm" data-testid={`expense-actions-${request.request_id}`}>
                        <MoreHorizontal className="w-4 h-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => onView(request)}>
                        <Eye className="w-4 h-4 mr-2" /> Ver Detalles
                      </DropdownMenuItem>
                      {isApprovalView && onApprove && ['pending', 'approved_manager'].includes(request.status) && (
                        <DropdownMenuItem onClick={() => onApprove(request)}>
                          <FileCheck className="w-4 h-4 mr-2" /> Aprobar/Rechazar
                        </DropdownMenuItem>
                      )}
                      {onCancel && ['pending', 'draft'].includes(request.status) && (
                        <DropdownMenuItem 
                          onClick={() => onCancel(request.request_id)}
                          className="text-red-600 dark:text-red-400"
                        >
                          <XCircle className="w-4 h-4 mr-2" /> Cancelar
                        </DropdownMenuItem>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
