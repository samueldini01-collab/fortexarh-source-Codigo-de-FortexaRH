import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { toast } from "sonner";
import {
  Building2, Users, DollarSign, Shield, LogOut, Search,
  CheckCircle, XCircle, Activity, CreditCard, Banknote,
  Gift, ArrowUpDown, Eye, Power, PowerOff, Clock,
  TrendingUp, ChevronDown, RefreshCw, AlertTriangle,
  Mail, Phone, Settings2, Columns3, ChevronRight, Loader2, Receipt, Ticket, Share2, ShoppingCart, LogIn, FileWarning
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "../components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Toaster } from "../components/ui/sonner";
import { DropdownMenu, DropdownMenuContent, DropdownMenuCheckboxItem, DropdownMenuTrigger } from "../components/ui/dropdown-menu";
import { SupportContent } from "./SupportAdminPage";
import { BrochureBuilderPanel } from "./BrochureBuilderPage";
import AbandonedCartsTab from "../components/super-admin/AbandonedCartsTab";
import CollectionsDashboard from "../components/super-admin/CollectionsDashboard";
import RevenueTab from "../components/super-admin/RevenueTab";
import InvoicesPendingTab from "../components/super-admin/InvoicesPendingTab";

const API = process.env.REACT_APP_BACKEND_URL + "/api/super-admin";

function SuperAdminLogin({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await axios.post(`${API}/login`, { username, password });
      sessionStorage.setItem("sa_token", res.data.token);
      onLogin(res.data.token);
    } catch {
      toast.error("Credenciales invalidas");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <Card className="w-full max-w-sm border-slate-800 bg-slate-900 shadow-2xl">
        <CardHeader className="text-center pb-2">
          <div className="w-16 h-16 mx-auto mb-3 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <CardTitle className="text-xl text-white">FortexaRH</CardTitle>
          <CardDescription className="text-slate-400">Panel de Administracion</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <Label className="text-slate-300 text-sm">Usuario</Label>
              <Input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="bg-slate-800 border-slate-700 text-white"
                placeholder="Usuario"
                data-testid="sa-login-user"
                required
              />
            </div>
            <div>
              <Label className="text-slate-300 text-sm">Clave</Label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="bg-slate-800 border-slate-700 text-white"
                placeholder="Clave"
                data-testid="sa-login-pass"
                required
              />
            </div>
            <Button type="submit" disabled={loading} className="w-full bg-indigo-600 hover:bg-indigo-700" data-testid="sa-login-btn">
              {loading ? "Accediendo..." : "Acceder"}
            </Button>
          </form>
        </CardContent>
      </Card>
      <Toaster position="top-right" richColors />
    </div>
  );
}

const PAYMENT_METHODS = {
  tarjeta: { label: "Tarjeta", icon: CreditCard, color: "text-blue-500 bg-blue-50" },
  transferencia: { label: "Transferencia", icon: Banknote, color: "text-emerald-500 bg-emerald-50" },
  efectivo: { label: "Efectivo", icon: DollarSign, color: "text-amber-500 bg-amber-50" },
  regalia: { label: "Regalia (sin pago)", icon: Gift, color: "text-purple-500 bg-purple-50" },
  sin_definir: { label: "Sin definir", icon: AlertTriangle, color: "text-slate-400 bg-slate-50" },
};

const PLAN_BADGES = {
  basico:     { label: "Basico",     color: "bg-sky-500/20 text-sky-400" },
  pro:        { label: "Pro",        color: "bg-indigo-500/20 text-indigo-400" },
  enterprise: { label: "Enterprise", color: "bg-amber-500/20 text-amber-400" },
  partner_basico:    { label: "Partner Basico",    color: "bg-teal-500/20 text-teal-400" },
  partner_pro:       { label: "Partner Pro",       color: "bg-teal-500/20 text-teal-400" },
  partner_enterprise: { label: "Partner Enterprise", color: "bg-teal-500/20 text-teal-400" },
  partner:    { label: "Partner",    color: "bg-teal-500/20 text-teal-400" },
  trial:      { label: "Prueba",     color: "bg-orange-500/20 text-orange-400" },
  free:       { label: "Gratuito",   color: "bg-slate-500/20 text-slate-400" },
};

function getPaymentBadge(method) {
  const m = PAYMENT_METHODS[method] || PAYMENT_METHODS.sin_definir;
  const Icon = m.icon;
  return (
    <Badge variant="outline" className={`${m.color} border-0 gap-1`}>
      <Icon className="w-3 h-3" /> {m.label}
    </Badge>
  );
}

function getPlanBadge(plan, monthlyPrice) {
  const p = PLAN_BADGES[plan] || PLAN_BADGES.free;
  return (
    <div className="flex flex-col gap-0.5">
      <Badge className={`${p.color} border-0 text-xs`}>{p.label}</Badge>
      {monthlyPrice > 0 && <span className="text-[10px] text-slate-500">${monthlyPrice}/mes</span>}
    </div>
  );
}

const ALL_COLUMNS = [
  { key: "name", label: "Empresa", default: true, locked: true },
  { key: "status", label: "Estado", default: true },
  { key: "plan", label: "Plan", default: true },
  { key: "monthly_billing", label: "Facturación", default: true },
  { key: "active_employees", label: "Empl. Activos", default: true },
  { key: "users", label: "Usuarios", default: true },
  { key: "contact", label: "Contacto", default: true },
  { key: "payment_method", label: "Método Pago", default: true },
  { key: "activation_date", label: "F. Activación", default: false },
  { key: "next_payment", label: "Próx. Pago", default: false },
  { key: "activity", label: "Actividad", default: true },
  { key: "actions", label: "Acciones", default: true, locked: true },
];

function SuperAdminDashboard({ token, onLogout }) {
  const [companies, setCompanies] = useState([]);
  const [stats, setStats] = useState({});
  const [events, setEvents] = useState([]);
  const [revenue, setRevenue] = useState({});
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [activateDialog, setActivateDialog] = useState(null);
  const [activateForm, setActivateForm] = useState({ payment_method: "transferencia", notes: "", amount: 0 });
  const [deactivateDialog, setDeactivateDialog] = useState(null);
  const [planDialog, setPlanDialog] = useState(null);
  const [planForm, setPlanForm] = useState({ plan_id: "basico", custom_price: null });
  const [actionLoading, setActionLoading] = useState(false);
  const [syncLoading, setSyncLoading] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const [alertsLoading, setAlertsLoading] = useState(false);
  const [pendingInvoices, setPendingInvoices] = useState({ items: [], count: 0, total_amount: 0 });
  const [supportActions, setSupportActions] = useState([]);
  const [supportActionsLoading, setSupportActionsLoading] = useState(false);
  const [visibleCols, setVisibleCols] = useState(() => {
    const saved = localStorage.getItem("sa_columns");
    if (saved) try { return JSON.parse(saved); } catch {}
    return ALL_COLUMNS.filter(c => c.default).map(c => c.key);
  });
  const [drillCompany, setDrillCompany] = useState(null);
  const [drillData, setDrillData] = useState(null);
  const [drillLoading, setDrillLoading] = useState(false);

  const headers = { Authorization: `Bearer ${token}` };

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [compRes, statsRes, eventsRes, revRes, alertsRes, invoicesRes] = await Promise.all([
        axios.get(`${API}/companies`, { headers }),
        axios.get(`${API}/stats`, { headers }),
        axios.get(`${API}/events?limit=50`, { headers }),
        axios.get(`${API}/revenue`, { headers }),
        axios.get(`${API}/alerts`, { headers }).catch(() => ({ data: [] })),
        axios.get(`${API}/invoices/pending`, { headers }).catch(() => ({ data: { items: [], count: 0, total_amount: 0 } })),
      ]);
      setCompanies(compRes.data);
      setStats(statsRes.data);
      setEvents(eventsRes.data);
      setRevenue(revRes.data);
      setAlerts(alertsRes.data);
      setPendingInvoices(invoicesRes.data);
    } catch (err) {
      if (err.response?.status === 401) onLogout();
      else toast.error("Error cargando datos");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleActivate = async () => {
    if (!activateDialog) return;
    setActionLoading(true);
    try {
      await axios.post(`${API}/companies/${activateDialog.company_id}/activate`, activateForm, { headers });
      toast.success(`${activateDialog.name} activada`);
      setActivateDialog(null);
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Error");
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeactivate = async () => {
    if (!deactivateDialog) return;
    setActionLoading(true);
    try {
      await axios.post(`${API}/companies/${deactivateDialog.company_id}/deactivate`, {}, { headers });
      toast.success(`${deactivateDialog.name} desactivada`);
      setDeactivateDialog(null);
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Error");
    } finally {
      setActionLoading(false);
    }
  };

  const handlePlanChange = async () => {
    if (!planDialog) return;
    setActionLoading(true);
    try {
      await axios.post(`${API}/companies/${planDialog.company_id}/plan`, planForm, { headers });
      toast.success("Plan actualizado");
      setPlanDialog(null);
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Error");
    } finally {
      setActionLoading(false);
    }
  };

  const handleSyncStatuses = async () => {
    setSyncLoading(true);
    try {
      const res = await axios.post(`${API}/sync-statuses`, {}, { headers });
      toast.success(`Sincronizado: ${res.data.activated} activadas, ${res.data.deactivated} desactivadas`);
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Error sincronizando");
    } finally {
      setSyncLoading(false);
    }
  };

  const handleDrillDown = async (company) => {
    setDrillCompany(company);
    setDrillLoading(true);
    setDrillData(null);
    try {
      const res = await axios.get(`${API}/companies/${company.company_id}/detail`, { headers });
      setDrillData(res.data);
    } catch (err) {
      // Fallback to the legacy users endpoint
      try {
        const res = await axios.get(`${API}/companies/${company.company_id}/users`, { headers });
        setDrillData({ users: res.data.users, employees: res.data.employees });
      } catch {
        toast.error("Error cargando datos de la empresa");
      }
    } finally {
      setDrillLoading(false);
    }
  };

  const handleImpersonate = async (company) => {
    if (!window.confirm(`Iniciarás sesión como soporte en "${company.name}". ¿Continuar?`)) return;
    try {
      const res = await axios.post(
        `${API}/companies/${company.company_id}/impersonate`,
        {},
        { headers }
      );
      const { token: impToken, user } = res.data;
      // Save real-app credentials (Bearer + user) and the support flag
      localStorage.setItem("token", impToken);
      localStorage.setItem("user", JSON.stringify(user));
      localStorage.setItem("fortexa_support_session", "1");
      localStorage.setItem("fortexa_support_company", company.name || company.company_id);
      // Navigate to the real app dashboard in a new tab so the SA keeps their session
      window.open("/dashboard", "_blank");
      toast.success("Sesión de soporte iniciada (1h)");
    } catch (err) {
      toast.error(err.response?.data?.detail || "No se pudo iniciar sesión de soporte");
    }
  };

  const handleMarkInvoicePaid = async (companyId) => {
    if (!window.confirm("¿Marcar la factura actual como pagada (avanzar el período 30 días)?")) return;
    try {
      await axios.post(`${API}/companies/${companyId}/invoices/mark-paid`, { payment_method: "transferencia" }, { headers });
      toast.success("Factura marcada como pagada");
      fetchData();
      if (drillCompany?.company_id === companyId) handleDrillDown(drillCompany);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Error al marcar como pagada");
    }
  };

  const fetchSupportActions = useCallback(async () => {
    setSupportActionsLoading(true);
    try {
      const res = await axios.get(`${API}/support-actions?limit=100`, { headers });
      setSupportActions(res.data.items || []);
    } catch {
      toast.error("Error cargando acciones de soporte");
    } finally {
      setSupportActionsLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const toggleColumn = (key) => {
    const col = ALL_COLUMNS.find(c => c.key === key);
    if (col?.locked) return;
    setVisibleCols(prev => {
      const next = prev.includes(key) ? prev.filter(k => k !== key) : [...prev, key];
      localStorage.setItem("sa_columns", JSON.stringify(next));
      return next;
    });
  };

  const isColVisible = (key) => visibleCols.includes(key);

  const filtered = companies.filter(c => {
    const matchSearch = !search || (c.name || "").toLowerCase().includes(search.toLowerCase()) || (c.rnc || "").includes(search);
    const matchStatus = statusFilter === "all" || (statusFilter === "active" ? c.status === "active" : c.status !== "active");
    return matchSearch && matchStatus;
  });

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <Shield className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-lg">FortexaRH <span className="text-indigo-400 text-sm font-normal">Super Admin</span></span>
          </div>
          <div className="flex items-center gap-3">
            <Button size="sm" variant="ghost" onClick={handleSyncStatuses} disabled={syncLoading} className="text-slate-400 hover:text-indigo-400" data-testid="btn-sync-statuses" title="Sincronizar estados">
              {syncLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
              <span className="ml-1 hidden sm:inline">Sync</span>
            </Button>
            <Button size="sm" variant="ghost" onClick={fetchData} className="text-slate-400 hover:text-white">
              <RefreshCw className="w-4 h-4" />
            </Button>
            <Button size="sm" variant="ghost" onClick={onLogout} className="text-slate-400 hover:text-red-400" data-testid="sa-logout">
              <LogOut className="w-4 h-4 mr-1" /> Salir
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {/* KPIs */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card className="bg-slate-900 border-slate-800 cursor-pointer hover:border-slate-600 transition-all" onClick={() => setStatusFilter("all")} data-testid="kpi-total-companies">
            <CardContent className="p-4">
              <p className="text-xs text-slate-500 uppercase tracking-wider">Total Empresas</p>
              <p className="text-3xl font-bold mt-1">{stats.total_companies || 0}</p>
              <Building2 className="w-5 h-5 text-slate-600 mt-1" />
            </CardContent>
          </Card>
          <Card className={`bg-slate-900 border-slate-800 cursor-pointer hover:border-emerald-600 transition-all ${statusFilter === "active" ? "ring-2 ring-emerald-500" : ""}`} onClick={() => setStatusFilter(statusFilter === "active" ? "all" : "active")} data-testid="kpi-active">
            <CardContent className="p-4">
              <p className="text-xs text-emerald-400 uppercase tracking-wider">Activas</p>
              <p className="text-3xl font-bold text-emerald-400 mt-1">{stats.active_companies || 0}</p>
              <CheckCircle className="w-5 h-5 text-emerald-700 mt-1" />
            </CardContent>
          </Card>
          <Card className={`bg-slate-900 border-slate-800 cursor-pointer hover:border-red-600 transition-all ${statusFilter === "inactive" ? "ring-2 ring-red-500" : ""}`} onClick={() => setStatusFilter(statusFilter === "inactive" ? "all" : "inactive")} data-testid="kpi-inactive">
            <CardContent className="p-4">
              <p className="text-xs text-red-400 uppercase tracking-wider">Inactivas</p>
              <p className="text-3xl font-bold text-red-400 mt-1">{stats.inactive_companies || 0}</p>
              <XCircle className="w-5 h-5 text-red-700 mt-1" />
            </CardContent>
          </Card>
          <Card className="bg-slate-900 border-slate-800">
            <CardContent className="p-4">
              <p className="text-xs text-slate-500 uppercase tracking-wider">Empleados</p>
              <p className="text-3xl font-bold text-sky-400 mt-1">{stats.total_employees || 0}</p>
              <Users className="w-5 h-5 text-sky-700 mt-1" />
            </CardContent>
          </Card>
          <Card className="bg-slate-900 border-slate-800">
            <CardContent className="p-4">
              <p className="text-xs text-slate-500 uppercase tracking-wider">Usuarios</p>
              <p className="text-3xl font-bold text-amber-400 mt-1">{stats.total_users || 0}</p>
              <TrendingUp className="w-5 h-5 text-amber-700 mt-1" />
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="companies" className="space-y-4">
          <TabsList className="bg-slate-900 border border-slate-800">
            <TabsTrigger value="companies" className="data-[state=active]:bg-indigo-600" data-testid="tab-companies">
              <Building2 className="w-4 h-4 mr-1.5" /> Empresas
            </TabsTrigger>
            <TabsTrigger value="revenue" className="data-[state=active]:bg-indigo-600" data-testid="tab-revenue">
              <DollarSign className="w-4 h-4 mr-1.5" /> Revenue
            </TabsTrigger>
            <TabsTrigger value="events" className="data-[state=active]:bg-indigo-600" data-testid="tab-events">
              <Activity className="w-4 h-4 mr-1.5" /> Eventos
            </TabsTrigger>
            <TabsTrigger value="alerts" className="data-[state=active]:bg-amber-600" data-testid="tab-alerts">
              <AlertTriangle className="w-4 h-4 mr-1.5" /> Alertas {alerts.length > 0 && <Badge className="ml-1 bg-red-500/80 text-white text-[10px] px-1.5 py-0">{alerts.length}</Badge>}
            </TabsTrigger>
            <TabsTrigger value="invoices-pending" className="data-[state=active]:bg-red-600" data-testid="tab-invoices-pending">
              <FileWarning className="w-4 h-4 mr-1.5" /> Facturas pendientes {pendingInvoices.count > 0 && <Badge className="ml-1 bg-red-500/80 text-white text-[10px] px-1.5 py-0">{pendingInvoices.count}</Badge>}
            </TabsTrigger>
            <TabsTrigger value="collections" className="data-[state=active]:bg-emerald-600" data-testid="tab-collections">
              <DollarSign className="w-4 h-4 mr-1.5" /> Cobranza
            </TabsTrigger>
            <TabsTrigger value="support-actions" className="data-[state=active]:bg-orange-600" data-testid="tab-support-actions">
              <LogIn className="w-4 h-4 mr-1.5" /> Acciones de soporte
            </TabsTrigger>
            <TabsTrigger value="support" className="data-[state=active]:bg-emerald-600" data-testid="tab-support">
              <Ticket className="w-4 h-4 mr-1.5" /> Soporte
            </TabsTrigger>
            <TabsTrigger value="brochure-builder" className="data-[state=active]:bg-indigo-600" data-testid="tab-brochure-builder">
              <Share2 className="w-4 h-4 mr-1.5" /> Brochure Builder
            </TabsTrigger>
            <TabsTrigger value="abandoned-carts" className="data-[state=active]:bg-rose-600" data-testid="tab-abandoned-carts">
              <ShoppingCart className="w-4 h-4 mr-1.5" /> Carritos
            </TabsTrigger>
          </TabsList>

          {/* Companies Tab */}
          <TabsContent value="companies" className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <Input
                  placeholder="Buscar empresa o RNC..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-9 bg-slate-900 border-slate-700 text-white"
                  data-testid="sa-search"
                />
              </div>
              <Badge variant="outline" className="text-slate-400 border-slate-700">
                {filtered.length} de {companies.length}
              </Badge>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button size="sm" variant="ghost" className="text-slate-400 hover:text-white" data-testid="btn-column-config">
                    <Columns3 className="w-4 h-4 mr-1" /> Columnas
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="bg-slate-900 border-slate-700">
                  {ALL_COLUMNS.map(col => (
                    <DropdownMenuCheckboxItem
                      key={col.key}
                      checked={visibleCols.includes(col.key)}
                      disabled={col.locked}
                      onCheckedChange={() => toggleColumn(col.key)}
                      className="text-slate-300"
                    >
                      {col.label}
                    </DropdownMenuCheckboxItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>
            </div>

            <Card className="bg-slate-900 border-slate-800 overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-800 hover:bg-slate-800/50">
                    {isColVisible("name") && <TableHead className="text-slate-400">Empresa</TableHead>}
                    {isColVisible("status") && <TableHead className="text-slate-400">Estado</TableHead>}
                    {isColVisible("plan") && <TableHead className="text-slate-400">Plan</TableHead>}
                    {isColVisible("monthly_billing") && <TableHead className="text-slate-400 text-right">Facturación</TableHead>}
                    {isColVisible("active_employees") && <TableHead className="text-slate-400 text-center">Empl.</TableHead>}
                    {isColVisible("users") && <TableHead className="text-slate-400 text-center">Users</TableHead>}
                    {isColVisible("contact") && <TableHead className="text-slate-400">Contacto</TableHead>}
                    {isColVisible("payment_method") && <TableHead className="text-slate-400">Método Pago</TableHead>}
                    {isColVisible("activation_date") && <TableHead className="text-slate-400">F. Activación</TableHead>}
                    {isColVisible("next_payment") && <TableHead className="text-slate-400">Próx. Pago</TableHead>}
                    {isColVisible("activity") && <TableHead className="text-slate-400">Actividad</TableHead>}
                    {isColVisible("actions") && <TableHead className="text-slate-400 text-right">Acciones</TableHead>}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    Array.from({ length: 5 }).map((_, i) => (
                      <TableRow key={i} className="border-slate-800">
                        <TableCell colSpan={visibleCols.length}><div className="h-8 bg-slate-800 rounded animate-pulse" /></TableCell>
                      </TableRow>
                    ))
                  ) : filtered.length === 0 ? (
                    <TableRow className="border-slate-800">
                      <TableCell colSpan={visibleCols.length} className="text-center py-8 text-slate-500">No se encontraron empresas</TableCell>
                    </TableRow>
                  ) : filtered.map(c => (
                    <TableRow key={c.company_id} className="border-slate-800 hover:bg-slate-800/30 cursor-pointer" onClick={() => handleDrillDown(c)}>
                      {isColVisible("name") && (
                        <TableCell className="font-medium text-white max-w-[200px]">
                          <div className="flex items-center gap-1.5">
                            <span className="truncate">{c.name || c.company_id}</span>
                            <ChevronRight className="w-3.5 h-3.5 text-slate-600 flex-shrink-0" />
                          </div>
                          {c.rnc && <p className="text-[10px] text-slate-500 font-mono">{c.rnc}</p>}
                        </TableCell>
                      )}
                      {isColVisible("status") && (
                        <TableCell>
                          {c.status === "active" ? (
                            <Badge className="bg-emerald-500/20 text-emerald-400 border-0">Activa</Badge>
                          ) : (
                            <Badge className="bg-red-500/20 text-red-400 border-0">Inactiva</Badge>
                          )}
                        </TableCell>
                      )}
                      {isColVisible("plan") && <TableCell>{getPlanBadge(c.subscription_plan || "free", c.monthly_price || 0)}</TableCell>}
                      {isColVisible("monthly_billing") && (
                        <TableCell className="text-right">
                          <span className="text-emerald-400 font-bold">${(c.monthly_billing || 0).toFixed(2)}</span>
                          {c.monthly_billing > 0 && <p className="text-[10px] text-slate-500">/mes</p>}
                        </TableCell>
                      )}
                      {isColVisible("active_employees") && <TableCell className="text-center text-slate-300">{c.active_employee_count || 0}</TableCell>}
                      {isColVisible("users") && <TableCell className="text-center text-slate-300">{c.user_count}</TableCell>}
                      {isColVisible("contact") && (
                        <TableCell>
                          {c.contact_name || c.contact_email ? (
                            <div>
                              {c.contact_name && <p className="text-sm text-slate-300">{c.contact_name}</p>}
                              {c.contact_email && <p className="text-[10px] text-slate-500">{c.contact_email}</p>}
                            </div>
                          ) : <span className="text-slate-600">—</span>}
                        </TableCell>
                      )}
                      {isColVisible("payment_method") && <TableCell>{getPaymentBadge(c.payment_method || "sin_definir")}</TableCell>}
                      {isColVisible("activation_date") && (
                        <TableCell className="text-sm text-slate-400">{c.activation_date ? c.activation_date.split("T")[0] : "—"}</TableCell>
                      )}
                      {isColVisible("next_payment") && (
                        <TableCell className="text-sm text-slate-400">{c.next_payment_date ? c.next_payment_date.split("T")[0] : "—"}</TableCell>
                      )}
                      {isColVisible("activity") && (
                        <TableCell>
                          <div className="flex items-center gap-1.5">
                            <span className="text-slate-400 text-sm">{(c.last_activity || c.created_at || "").split("T")[0]}</span>
                            {c.days_inactive != null && c.days_inactive >= 30 && (
                              <Badge className={`text-[10px] px-1.5 py-0 border-0 ${c.days_inactive >= 60 ? 'bg-red-500/20 text-red-400' : 'bg-amber-500/20 text-amber-400'}`}>
                                {c.days_inactive}d
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                      )}
                      {isColVisible("actions") && (
                        <TableCell onClick={e => e.stopPropagation()}>
                          <div className="flex justify-end gap-1">
                            <Button size="sm" variant="ghost" className="text-indigo-400 hover:text-indigo-300 hover:bg-indigo-500/10" onClick={() => { setPlanDialog(c); setPlanForm({ plan_id: c.subscription_plan || "basico", custom_price: null }); }} data-testid={`btn-plan-${c.company_id}`}>
                              <ArrowUpDown className="w-4 h-4 mr-1" /> Plan
                            </Button>
                            {c.status === "active" ? (
                              <Button size="sm" variant="ghost" className="text-red-400 hover:text-red-300 hover:bg-red-500/10" onClick={() => setDeactivateDialog(c)} data-testid={`btn-deactivate-${c.company_id}`}>
                                <PowerOff className="w-4 h-4 mr-1" /> Inactivar
                              </Button>
                            ) : (
                              <Button size="sm" variant="ghost" className="text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10" onClick={() => setActivateDialog(c)} data-testid={`btn-activate-${c.company_id}`}>
                                <Power className="w-4 h-4 mr-1" /> Activar
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      )}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          </TabsContent>

          {/* Revenue Tab */}
          <TabsContent value="revenue" className="space-y-4" data-testid="revenue-tab">
            <RevenueTab revenue={revenue} getPaymentBadge={getPaymentBadge} />
          </TabsContent>

          {/* Events Tab */}
          <TabsContent value="events" className="space-y-4">
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader className="pb-3">
                <CardTitle className="text-base text-white flex items-center gap-2">
                  <Activity className="w-5 h-5 text-indigo-400" /> Eventos del Sistema
                </CardTitle>
                <CardDescription className="text-slate-500">Actividad reciente de todas las empresas</CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                {events.length === 0 ? (
                  <div className="text-center py-12 text-slate-500">
                    <Activity className="w-10 h-10 mx-auto mb-3 text-slate-700" />
                    <p>No hay eventos registrados</p>
                  </div>
                ) : (
                  <div className="divide-y divide-slate-800">
                    {events.map((evt, i) => (
                      <div key={evt.event_id || i} className="px-4 py-3 hover:bg-slate-800/30 transition-colors flex items-start gap-3">
                        <div className="w-8 h-8 rounded-full bg-indigo-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                          <Activity className="w-4 h-4 text-indigo-400" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-sm font-medium text-white">{evt.event_type || evt.action || "evento"}</span>
                            {evt.company_name && (
                              <Badge variant="outline" className="text-xs border-slate-700 text-slate-400">{evt.company_name}</Badge>
                            )}
                          </div>
                          <p className="text-xs text-slate-500 mt-0.5 truncate">{evt.description || evt.details || ""}</p>
                          <p className="text-[10px] text-slate-600 mt-1">
                            <Clock className="w-3 h-3 inline mr-1" />
                            {(evt.created_at || evt.timestamp || "").replace("T", " ").substring(0, 19)}
                            {evt.user_email && ` - ${evt.user_email}`}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Alerts Tab */}
          <TabsContent value="alerts" className="space-y-4">
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-amber-400" />
                  Empresas Inactivas (+30 días)
                </CardTitle>
                <CardDescription className="text-slate-400">
                  Empresas sin actividad reciente que podrían necesitar seguimiento comercial
                </CardDescription>
              </CardHeader>
              <CardContent>
                {alerts.length === 0 ? (
                  <div className="text-center py-12 text-slate-500">
                    <CheckCircle className="w-12 h-12 mx-auto mb-3 text-emerald-500/50" />
                    <p className="text-lg font-medium text-emerald-400">Sin alertas</p>
                    <p className="text-sm mt-1">Todas las empresas tienen actividad reciente</p>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow className="border-slate-800 hover:bg-transparent">
                        <TableHead className="text-slate-400">Empresa</TableHead>
                        <TableHead className="text-slate-400">Plan</TableHead>
                        <TableHead className="text-slate-400 text-center">Empleados</TableHead>
                        <TableHead className="text-slate-400 text-center">Usuarios</TableHead>
                        <TableHead className="text-slate-400">Días Inactivo</TableHead>
                        <TableHead className="text-slate-400">Riesgo</TableHead>
                        <TableHead className="text-slate-400">Última Actividad</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {alerts.map((a, idx) => (
                        <TableRow key={idx} className="border-slate-800" data-testid={`alert-row-${idx}`}>
                          <TableCell>
                            <div>
                              <p className="font-medium">{a.name}</p>
                              <p className="text-xs text-slate-500 font-mono">{a.company_id}</p>
                            </div>
                          </TableCell>
                          <TableCell>{getPlanBadge(a.subscription_plan || "free", 0)}</TableCell>
                          <TableCell className="text-center">{a.employee_count}</TableCell>
                          <TableCell className="text-center">{a.user_count}</TableCell>
                          <TableCell>
                            <span className={`text-lg font-bold ${a.days_inactive >= 60 ? 'text-red-400' : 'text-amber-400'}`}>
                              {a.days_inactive}d
                            </span>
                          </TableCell>
                          <TableCell>
                            {a.risk === "high" ? (
                              <Badge className="bg-red-500/20 text-red-400 border-0">Alto</Badge>
                            ) : (
                              <Badge className="bg-amber-500/20 text-amber-400 border-0">Medio</Badge>
                            )}
                          </TableCell>
                          <TableCell className="text-sm text-slate-400">
                            {a.last_activity ? new Date(a.last_activity).toLocaleDateString() : "—"}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Pending Invoices Tab */}
          <TabsContent value="invoices-pending" className="space-y-4" data-testid="invoices-pending-tab">
            <InvoicesPendingTab
              pendingInvoices={pendingInvoices}
              onMarkPaid={handleMarkInvoicePaid}
              onViewCompany={(companyId) => {
                const c = companies.find(c => c.company_id === companyId);
                if (c) handleDrillDown(c);
              }}
            />
          </TabsContent>

          {/* Support Actions Tab */}
          <TabsContent value="collections" className="space-y-4" data-testid="collections-tab">
            <CollectionsDashboard token={token} />
          </TabsContent>

          {/* Support Actions Tab */}
          <TabsContent value="support-actions" className="space-y-4" data-testid="support-actions-tab">
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <LogIn className="w-5 h-5 text-orange-400" />
                      Acciones de soporte
                    </CardTitle>
                    <CardDescription className="text-slate-400">
                      Auditoría de todas las mutaciones (POST/PUT/PATCH/DELETE) realizadas durante una sesión de soporte impersonada.
                    </CardDescription>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    className="bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700"
                    onClick={fetchSupportActions}
                    disabled={supportActionsLoading}
                    data-testid="support-actions-refresh-btn"
                  >
                    <Loader2 className={`w-4 h-4 mr-2 ${supportActionsLoading ? "animate-spin" : "hidden"}`} />
                    Cargar
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {supportActions.length === 0 ? (
                  <div className="text-center py-12 text-slate-500" data-testid="no-support-actions">
                    <CheckCircle className="w-12 h-12 mx-auto mb-3 text-emerald-500/50" />
                    <p className="text-lg font-medium text-emerald-400">Sin acciones registradas</p>
                    <p className="text-sm mt-1">Haz click en "Cargar" para consultar el log más reciente.</p>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow className="border-slate-800 hover:bg-transparent">
                        <TableHead className="text-slate-400">Fecha</TableHead>
                        <TableHead className="text-slate-400">Soporte como</TableHead>
                        <TableHead className="text-slate-400">Método</TableHead>
                        <TableHead className="text-slate-400">Endpoint</TableHead>
                        <TableHead className="text-slate-400 text-center">Estado</TableHead>
                        <TableHead className="text-slate-400">IP</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {supportActions.map((row) => (
                        <TableRow key={row.id} className="border-slate-800" data-testid={`support-action-${row.id}`}>
                          <TableCell className="text-slate-300 text-sm whitespace-nowrap">{new Date(row.created_at).toLocaleString()}</TableCell>
                          <TableCell className="text-indigo-400 text-sm">{row.email}</TableCell>
                          <TableCell>
                            <Badge
                              className={`border-0 text-[10px] ${
                                row.method === "DELETE"
                                  ? "bg-red-500/20 text-red-400"
                                  : row.method === "POST"
                                  ? "bg-emerald-500/20 text-emerald-400"
                                  : "bg-amber-500/20 text-amber-400"
                              }`}
                            >
                              {row.method}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-slate-300 font-mono text-xs">{row.path}{row.query ? `?${row.query}` : ""}</TableCell>
                          <TableCell className="text-center">
                            <Badge
                              className={`border-0 text-[10px] ${
                                row.status_code < 300
                                  ? "bg-emerald-500/20 text-emerald-400"
                                  : row.status_code < 400
                                  ? "bg-blue-500/20 text-blue-400"
                                  : "bg-red-500/20 text-red-400"
                              }`}
                            >
                              {row.status_code}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-slate-500 font-mono text-xs">{row.ip || "—"}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Support Tab */}
          <TabsContent value="support" className="space-y-4" data-testid="support-tab">
            <SupportContent />
          </TabsContent>

          {/* Brochure Builder Tab */}
          <TabsContent value="brochure-builder" className="space-y-4" data-testid="brochure-builder-tab">
            <BrochureBuilderPanel containerClassName="space-y-6" showCreatorFilter={true} />
          </TabsContent>
          <TabsContent value="abandoned-carts" className="space-y-4" data-testid="abandoned-carts-content">
            <AbandonedCartsTab saToken={token} />
          </TabsContent>
        </Tabs>
      </main>

      {/* Activate Dialog */}
      <Dialog open={!!activateDialog} onOpenChange={() => setActivateDialog(null)}>
        <DialogContent className="bg-slate-900 border-slate-700 text-white">
          <DialogHeader>
            <DialogTitle>Activar Empresa</DialogTitle>
            <DialogDescription className="text-slate-400">
              {activateDialog?.name}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label className="text-slate-300">Modalidad de Pago</Label>
              <Select value={activateForm.payment_method} onValueChange={(v) => setActivateForm(p => ({ ...p, payment_method: v }))}>
                <SelectTrigger className="bg-slate-800 border-slate-700 text-white" data-testid="activate-payment-method">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="tarjeta">Tarjeta</SelectItem>
                  <SelectItem value="transferencia">Transferencia</SelectItem>
                  <SelectItem value="efectivo">Efectivo</SelectItem>
                  <SelectItem value="regalia">Regalia (sin pago)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-slate-300">Monto (RD$)</Label>
              <Input
                type="number"
                value={activateForm.amount}
                onChange={(e) => setActivateForm(p => ({ ...p, amount: parseFloat(e.target.value) || 0 }))}
                className="bg-slate-800 border-slate-700 text-white"
                data-testid="activate-amount"
              />
            </div>
            <div>
              <Label className="text-slate-300">Notas</Label>
              <Textarea
                value={activateForm.notes}
                onChange={(e) => setActivateForm(p => ({ ...p, notes: e.target.value }))}
                className="bg-slate-800 border-slate-700 text-white"
                placeholder="Notas opcionales..."
                data-testid="activate-notes"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setActivateDialog(null)} className="text-slate-400">Cancelar</Button>
            <Button onClick={handleActivate} disabled={actionLoading} className="bg-emerald-600 hover:bg-emerald-700" data-testid="confirm-activate">
              {actionLoading ? "Activando..." : "Activar Empresa"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Deactivate Dialog */}
      <Dialog open={!!deactivateDialog} onOpenChange={() => setDeactivateDialog(null)}>
        <DialogContent className="bg-slate-900 border-slate-700 text-white">
          <DialogHeader>
            <DialogTitle className="text-red-400">Inactivar Empresa</DialogTitle>
            <DialogDescription className="text-slate-400">
              Esta accion desactivara el acceso de <strong className="text-white">{deactivateDialog?.name}</strong> al sistema.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setDeactivateDialog(null)} className="text-slate-400">Cancelar</Button>
            <Button onClick={handleDeactivate} disabled={actionLoading} className="bg-red-600 hover:bg-red-700" data-testid="confirm-deactivate">
              {actionLoading ? "Desactivando..." : "Confirmar Inactivacion"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Plan Change Dialog */}
      <Dialog open={!!planDialog} onOpenChange={() => setPlanDialog(null)}>
        <DialogContent className="bg-slate-900 border-slate-700 text-white">
          <DialogHeader>
            <DialogTitle>Cambiar Plan</DialogTitle>
            <DialogDescription className="text-slate-400">
              {planDialog?.name} - Plan actual: {planDialog?.subscription_plan || "Sin definir"}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label className="text-slate-300">Plan</Label>
              <Select value={planForm.plan_id} onValueChange={(v) => setPlanForm(p => ({ ...p, plan_id: v }))}>
                <SelectTrigger className="bg-slate-800 border-slate-700 text-white" data-testid="plan-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="basico">FortexaRH Basico (RD$2,500/mes)</SelectItem>
                  <SelectItem value="pro">FortexaRH Pro (RD$5,000/mes)</SelectItem>
                  <SelectItem value="enterprise">FortexaRH Enterprise (RD$12,000/mes)</SelectItem>
                  <SelectItem value="partner_basico">Partner Basico (RD$1,800/mes)</SelectItem>
                  <SelectItem value="partner_pro">Partner Pro (RD$3,500/mes)</SelectItem>
                  <SelectItem value="partner_enterprise">Partner Enterprise (RD$9,000/mes)</SelectItem>
                  <SelectItem value="trial">Prueba Gratuita</SelectItem>
                  <SelectItem value="free">Gratuito</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-slate-300">Precio personalizado (opcional, RD$/mes)</Label>
              <Input
                type="number"
                placeholder="Dejar vacio para usar precio del plan"
                value={planForm.custom_price ?? ""}
                onChange={(e) => setPlanForm(p => ({ ...p, custom_price: e.target.value ? parseFloat(e.target.value) : null }))}
                className="bg-slate-800 border-slate-700 text-white"
                data-testid="plan-custom-price"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setPlanDialog(null)} className="text-slate-400">Cancelar</Button>
            <Button onClick={handlePlanChange} disabled={actionLoading} className="bg-indigo-600 hover:bg-indigo-700" data-testid="confirm-plan-change">
              {actionLoading ? "Guardando..." : "Guardar Plan"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Toaster position="top-right" richColors />

      {/* Drill-down Dialog */}
      <Dialog open={!!drillCompany} onOpenChange={() => setDrillCompany(null)}>
        <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto bg-slate-950 border-slate-800 text-white">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Building2 className="w-5 h-5 text-indigo-400" />
              {drillCompany?.name || drillCompany?.company_id}
            </DialogTitle>
            <DialogDescription className="text-slate-400">
              {drillCompany?.rnc && <span className="font-mono">RNC: {drillCompany.rnc} | </span>}
              Plan: {drillCompany?.plan_name} | Facturación: ${(drillCompany?.monthly_billing || 0).toFixed(2)}/mes
            </DialogDescription>
          </DialogHeader>
          {drillLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin text-indigo-400" />
            </div>
          ) : drillData ? (
            <div className="space-y-4">
              {/* Quick actions */}
              <div className="flex flex-wrap gap-2 pb-3 border-b border-slate-800" data-testid="drill-quick-actions">
                <Button
                  size="sm"
                  className="bg-orange-600/20 hover:bg-orange-600/30 text-orange-300 border border-orange-700/50"
                  onClick={() => handleImpersonate(drillCompany)}
                  data-testid="drill-impersonate-btn"
                >
                  <LogIn className="w-4 h-4 mr-2" /> Iniciar sesión como soporte
                </Button>
                <Button
                  size="sm"
                  className="bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-700/50"
                  onClick={() => {
                    setPlanDialog(drillCompany);
                    setPlanForm({ plan_id: drillCompany.subscription_plan || "basico", custom_price: null });
                  }}
                  data-testid="drill-plan-btn"
                >
                  <ArrowUpDown className="w-4 h-4 mr-2" /> Suscripción
                </Button>
                {drillData.subscription?.status && drillData.subscription?.current_period_end && (() => {
                  let overdue = 0;
                  try {
                    overdue = Math.floor((Date.now() - new Date(drillData.subscription.current_period_end).getTime()) / 86400000);
                  } catch { overdue = 0; }
                  if (overdue > 0) {
                    return (
                      <Button
                        size="sm"
                        className="bg-red-600/20 hover:bg-red-600/30 text-red-300 border border-red-700/50"
                        onClick={() => handleMarkInvoicePaid(drillCompany.company_id)}
                        data-testid="drill-mark-paid-btn"
                      >
                        <CheckCircle className="w-4 h-4 mr-2" /> Marcar como pagada ({overdue}d vencida)
                      </Button>
                    );
                  }
                  return null;
                })()}
              </div>

              {/* Subscription summary */}
              {drillData.subscription && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm" data-testid="drill-subscription-summary">
                  <div className="bg-slate-900/50 rounded p-2 border border-slate-800">
                    <p className="text-[10px] uppercase text-slate-500">Plan</p>
                    <p className="text-slate-200 font-medium">{drillData.subscription.plan_name || "—"}</p>
                  </div>
                  <div className="bg-slate-900/50 rounded p-2 border border-slate-800">
                    <p className="text-[10px] uppercase text-slate-500">Facturación mes</p>
                    <p className="text-emerald-400 font-bold">${(drillData.subscription.monthly_billing || 0).toFixed(2)}</p>
                  </div>
                  <div className="bg-slate-900/50 rounded p-2 border border-slate-800">
                    <p className="text-[10px] uppercase text-slate-500">Próx. pago</p>
                    <p className="text-slate-200">{drillData.subscription.current_period_end ? new Date(drillData.subscription.current_period_end).toLocaleDateString() : "—"}</p>
                  </div>
                  <div className="bg-slate-900/50 rounded p-2 border border-slate-800">
                    <p className="text-[10px] uppercase text-slate-500">Estado sub.</p>
                    <p className="text-slate-200 capitalize">{drillData.subscription.status || "—"}</p>
                  </div>
                </div>
              )}

              <div>
                <h3 className="text-sm font-semibold text-slate-300 mb-2 flex items-center gap-1.5">
                  <Users className="w-4 h-4" /> Usuarios Registrados ({drillData.users?.length || 0})
                </h3>
                {drillData.users?.length > 0 ? (
                  <Table>
                    <TableHeader>
                      <TableRow className="border-slate-800 hover:bg-transparent">
                        <TableHead className="text-slate-500">Nombre</TableHead>
                        <TableHead className="text-slate-500">Email</TableHead>
                        <TableHead className="text-slate-500">Rol</TableHead>
                        <TableHead className="text-slate-500">Último Login</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {drillData.users.map((u, i) => (
                        <TableRow key={i} className="border-slate-800/50" data-testid={`drill-user-${i}`}>
                          <TableCell className="text-slate-300">{u.name || "—"}</TableCell>
                          <TableCell><span className="text-indigo-400 text-sm">{u.email}</span></TableCell>
                          <TableCell><Badge variant="outline" className="text-[10px] border-slate-700 text-slate-400">{u.role || "user"}</Badge></TableCell>
                          <TableCell className="text-slate-500 text-sm">{u.last_login ? new Date(u.last_login).toLocaleDateString() : "—"}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                ) : <p className="text-sm text-slate-500 py-2">Sin usuarios registrados</p>}
              </div>

              {drillData.transactions?.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-slate-300 mb-2 flex items-center gap-1.5">
                    <Receipt className="w-4 h-4" /> Últimas transacciones ({drillData.transactions.length})
                  </h3>
                  <Table>
                    <TableHeader>
                      <TableRow className="border-slate-800 hover:bg-transparent">
                        <TableHead className="text-slate-500">Fecha</TableHead>
                        <TableHead className="text-slate-500">Plan</TableHead>
                        <TableHead className="text-slate-500">Monto</TableHead>
                        <TableHead className="text-slate-500">Estado</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {drillData.transactions.slice(0, 6).map((tx, i) => (
                        <TableRow key={i} className="border-slate-800/50" data-testid={`drill-tx-${i}`}>
                          <TableCell className="text-slate-400 text-sm">{tx.created_at ? new Date(tx.created_at).toLocaleDateString() : "—"}</TableCell>
                          <TableCell className="text-slate-300 text-sm">{tx.plan_name || tx.plan_id || "—"}</TableCell>
                          <TableCell className="text-emerald-400 text-sm font-mono">${(tx.amount || 0).toFixed(2)} {tx.currency?.toUpperCase()}</TableCell>
                          <TableCell><Badge variant="outline" className={`text-[10px] ${tx.payment_status === "completed" ? "border-emerald-700 text-emerald-400" : "border-slate-700 text-slate-400"}`}>{tx.payment_status || "—"}</Badge></TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}

              {drillData.employees?.length > 0 && (
                <div>
                <h3 className="text-sm font-semibold text-slate-300 mb-2 flex items-center gap-1.5">
                  <Shield className="w-4 h-4" /> Empleados ({drillData.employees?.length || 0})
                </h3>
                  <Table>
                    <TableHeader>
                      <TableRow className="border-slate-800 hover:bg-transparent">
                        <TableHead className="text-slate-500">Nombre</TableHead>
                        <TableHead className="text-slate-500">Cédula</TableHead>
                        <TableHead className="text-slate-500">Posición</TableHead>
                        <TableHead className="text-slate-500">Dept.</TableHead>
                        <TableHead className="text-slate-500">Estado</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {drillData.employees.map((e, i) => (
                        <TableRow key={i} className="border-slate-800/50" data-testid={`drill-emp-${i}`}>
                          <TableCell className="text-slate-300">{e.first_name} {e.last_name}</TableCell>
                          <TableCell className="text-slate-400 font-mono text-sm">{e.cedula || "—"}</TableCell>
                          <TableCell className="text-slate-400 text-sm">{e.position || "—"}</TableCell>
                          <TableCell className="text-slate-400 text-sm">{e.department || "—"}</TableCell>
                          <TableCell>
                            {e.status === "active" ? (
                              <Badge className="bg-emerald-500/20 text-emerald-400 border-0 text-[10px]">Activo</Badge>
                            ) : (
                              <Badge className="bg-slate-500/20 text-slate-400 border-0 text-[10px]">{e.status || "—"}</Badge>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </div>
          ) : null}
        </DialogContent>
      </Dialog>

      <Toaster position="top-right" richColors />
    </div>
  );
}

export default function SuperAdminPage() {
  const [token, setToken] = useState(() => sessionStorage.getItem("sa_token"));

  const handleLogout = () => {
    sessionStorage.removeItem("sa_token");
    setToken(null);
  };

  if (!token) return <SuperAdminLogin onLogin={setToken} />;
  return <SuperAdminDashboard token={token} onLogout={handleLogout} />;
}
