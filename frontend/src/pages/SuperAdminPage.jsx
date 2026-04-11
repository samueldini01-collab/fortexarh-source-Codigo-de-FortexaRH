import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { toast } from "sonner";
import {
  Building2, Users, DollarSign, Shield, LogOut, Search,
  CheckCircle, XCircle, Activity, CreditCard, Banknote,
  Gift, ArrowUpDown, Eye, Power, PowerOff, Clock,
  TrendingUp, ChevronDown, RefreshCw, AlertTriangle
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

function getPaymentBadge(method) {
  const m = PAYMENT_METHODS[method] || PAYMENT_METHODS.sin_definir;
  const Icon = m.icon;
  return (
    <Badge variant="outline" className={`${m.color} border-0 gap-1`}>
      <Icon className="w-3 h-3" /> {m.label}
    </Badge>
  );
}

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

  const headers = { Authorization: `Bearer ${token}` };

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [compRes, statsRes, eventsRes, revRes] = await Promise.all([
        axios.get(`${API}/companies`, { headers }),
        axios.get(`${API}/stats`, { headers }),
        axios.get(`${API}/events?limit=50`, { headers }),
        axios.get(`${API}/revenue`, { headers }),
      ]);
      setCompanies(compRes.data);
      setStats(statsRes.data);
      setEvents(eventsRes.data);
      setRevenue(revRes.data);
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
            </div>

            <Card className="bg-slate-900 border-slate-800 overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="border-slate-800 hover:bg-slate-800/50">
                    <TableHead className="text-slate-400">Empresa</TableHead>
                    <TableHead className="text-slate-400">RNC</TableHead>
                    <TableHead className="text-slate-400">Estado</TableHead>
                    <TableHead className="text-slate-400">Modalidad</TableHead>
                    <TableHead className="text-slate-400 text-center">Emp.</TableHead>
                    <TableHead className="text-slate-400 text-center">Users</TableHead>
                    <TableHead className="text-slate-400">Registro</TableHead>
                    <TableHead className="text-slate-400 text-right">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    Array.from({ length: 5 }).map((_, i) => (
                      <TableRow key={i} className="border-slate-800">
                        <TableCell colSpan={8}><div className="h-8 bg-slate-800 rounded animate-pulse" /></TableCell>
                      </TableRow>
                    ))
                  ) : filtered.length === 0 ? (
                    <TableRow className="border-slate-800">
                      <TableCell colSpan={8} className="text-center py-8 text-slate-500">No se encontraron empresas</TableCell>
                    </TableRow>
                  ) : filtered.map(c => (
                    <TableRow key={c.company_id} className="border-slate-800 hover:bg-slate-800/30">
                      <TableCell className="font-medium text-white max-w-[200px] truncate">{c.name || c.company_id}</TableCell>
                      <TableCell className="text-slate-400 font-mono text-sm">{c.rnc || "-"}</TableCell>
                      <TableCell>
                        {c.status === "active" ? (
                          <Badge className="bg-emerald-500/20 text-emerald-400 border-0">Activa</Badge>
                        ) : (
                          <Badge className="bg-red-500/20 text-red-400 border-0">Inactiva</Badge>
                        )}
                      </TableCell>
                      <TableCell>{getPaymentBadge(c.payment_method || "sin_definir")}</TableCell>
                      <TableCell className="text-center text-slate-300">{c.employee_count}</TableCell>
                      <TableCell className="text-center text-slate-300">{c.user_count}</TableCell>
                      <TableCell className="text-slate-400 text-sm">{(c.created_at || "").split("T")[0]}</TableCell>
                      <TableCell>
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
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          </TabsContent>

          {/* Revenue Tab */}
          <TabsContent value="revenue" className="space-y-4" data-testid="revenue-tab">
            {/* Revenue KPIs */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card className="bg-gradient-to-br from-emerald-900/40 to-slate-900 border-emerald-800">
                <CardContent className="p-4">
                  <p className="text-xs text-emerald-400 uppercase tracking-wider">MRR</p>
                  <p className="text-2xl font-bold text-emerald-300 mt-1">RD${(revenue.mrr || 0).toLocaleString()}</p>
                  <p className="text-[10px] text-slate-500 mt-1">Monthly Recurring Revenue</p>
                </CardContent>
              </Card>
              <Card className="bg-gradient-to-br from-sky-900/40 to-slate-900 border-sky-800">
                <CardContent className="p-4">
                  <p className="text-xs text-sky-400 uppercase tracking-wider">ARR</p>
                  <p className="text-2xl font-bold text-sky-300 mt-1">RD${(revenue.arr || 0).toLocaleString()}</p>
                  <p className="text-[10px] text-slate-500 mt-1">Annual Recurring Revenue</p>
                </CardContent>
              </Card>
              <Card className="bg-gradient-to-br from-purple-900/40 to-slate-900 border-purple-800">
                <CardContent className="p-4">
                  <p className="text-xs text-purple-400 uppercase tracking-wider">Partners</p>
                  <p className="text-2xl font-bold text-purple-300 mt-1">{revenue.partner_companies || 0}</p>
                  <p className="text-[10px] text-slate-500 mt-1">MRR: RD${(revenue.partner_mrr || 0).toLocaleString()}</p>
                </CardContent>
              </Card>
              <Card className={`bg-gradient-to-br ${(revenue.overdue_count || 0) > 0 ? 'from-red-900/40 border-red-800' : 'from-slate-800/40 border-slate-700'} to-slate-900`}>
                <CardContent className="p-4">
                  <p className={`text-xs uppercase tracking-wider ${(revenue.overdue_count || 0) > 0 ? 'text-red-400' : 'text-slate-400'}`}>Vencidos</p>
                  <p className={`text-2xl font-bold mt-1 ${(revenue.overdue_count || 0) > 0 ? 'text-red-300' : 'text-slate-300'}`}>{revenue.overdue_count || 0}</p>
                  <p className="text-[10px] text-slate-500 mt-1">Pagos pendientes</p>
                </CardContent>
              </Card>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Plan Distribution */}
              <Card className="bg-slate-900 border-slate-800">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base text-white">Distribucion por Plan</CardTitle>
                  <CardDescription className="text-slate-500">Empresas por tipo de plan</CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  {Object.entries(revenue.plan_distribution || {}).map(([key, val]) => (
                    <div key={key} className="flex items-center justify-between p-2 rounded-lg bg-slate-800/50">
                      <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${val.type === 'partner' ? 'bg-purple-400' : val.type === 'trial' || val.type === 'free' ? 'bg-slate-500' : 'bg-emerald-400'}`} />
                        <span className="text-sm text-white">{val.plan_name}</span>
                        {val.type === "partner" && <Badge className="bg-purple-500/20 text-purple-400 border-0 text-[10px]">Partner</Badge>}
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="text-sm text-slate-400">{val.count} empresas</span>
                        <span className="text-sm font-medium text-emerald-400 w-28 text-right">RD${val.mrr.toLocaleString()}/mes</span>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>

              {/* Overdue Alerts */}
              <Card className="bg-slate-900 border-slate-800">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base text-white flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-amber-400" /> Alertas de Pago
                  </CardTitle>
                  <CardDescription className="text-slate-500">Empresas con pago vencido</CardDescription>
                </CardHeader>
                <CardContent>
                  {(revenue.overdue_alerts || []).length === 0 ? (
                    <div className="text-center py-8 text-slate-500">
                      <CheckCircle className="w-8 h-8 mx-auto mb-2 text-emerald-600" />
                      <p className="text-sm">No hay pagos vencidos</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {revenue.overdue_alerts.map((alert, i) => (
                        <div key={i} className="p-3 rounded-lg bg-red-500/10 border border-red-800/50">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium text-white">{alert.company_name || alert.company_id}</span>
                            <Badge className="bg-red-500/20 text-red-400 border-0">{alert.days_overdue}d vencido</Badge>
                          </div>
                          <p className="text-xs text-slate-400 mt-1">{alert.plan} - RD${(alert.monthly || 0).toLocaleString()}/mes</p>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Payment History */}
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader className="pb-3">
                <CardTitle className="text-base text-white flex items-center gap-2">
                  <CreditCard className="w-5 h-5 text-indigo-400" /> Historial de Activaciones / Pagos
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                {(revenue.payment_history || []).length === 0 ? (
                  <div className="text-center py-8 text-slate-500">No hay registros de pago</div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow className="border-slate-800">
                        <TableHead className="text-slate-400">Fecha</TableHead>
                        <TableHead className="text-slate-400">Empresa</TableHead>
                        <TableHead className="text-slate-400">Modalidad</TableHead>
                        <TableHead className="text-slate-400 text-right">Monto</TableHead>
                        <TableHead className="text-slate-400">Notas</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(revenue.payment_history || []).map((p, i) => (
                        <TableRow key={p.activation_id || i} className="border-slate-800">
                          <TableCell className="text-slate-300 text-sm">{(p.created_at || "").split("T")[0]}</TableCell>
                          <TableCell className="text-white text-sm">{p.company_name || p.company_id}</TableCell>
                          <TableCell>{getPaymentBadge(p.payment_method || "sin_definir")}</TableCell>
                          <TableCell className="text-right text-emerald-400 font-mono">RD${(p.amount || 0).toLocaleString()}</TableCell>
                          <TableCell className="text-slate-500 text-sm max-w-[200px] truncate">{p.notes || "-"}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
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
