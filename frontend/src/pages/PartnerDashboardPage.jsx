import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { useAuth } from "@/App";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
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
  Users,
  DollarSign,
  TrendingUp,
  Building2,
  Copy,
  ExternalLink,
  Plus,
  MoreHorizontal,
  Mail,
  Phone,
  Calendar,
  CheckCircle,
  Clock,
  XCircle,
  AlertCircle,
  RefreshCw,
  Loader2,
  Briefcase,
  Wallet,
  BarChart3,
  Settings,
  LogOut,
  ChevronRight,
  Award,
  Percent,
  CreditCard,
  Receipt,
  FileText,
  Eye,
  Edit2,
  Banknote,
  ArrowUpRight,
  ShieldCheck,
  AlertTriangle
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Status badge component
const StatusBadge = ({ status }) => {
  const statusConfig = {
    active: { label: "Activo", color: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" },
    trial: { label: "Prueba", color: "bg-blue-500/20 text-blue-400 border-blue-500/30" },
    invited: { label: "Invitado", color: "bg-amber-500/20 text-amber-400 border-amber-500/30" },
    pending: { label: "Pendiente", color: "bg-slate-500/20 text-slate-400 border-slate-500/30" },
    inactive: { label: "Inactivo", color: "bg-red-500/20 text-red-400 border-red-500/30" },
    paid: { label: "Pagado", color: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" },
    cancelled: { label: "Cancelado", color: "bg-red-500/20 text-red-400 border-red-500/30" }
  };
  
  const config = statusConfig[status] || statusConfig.pending;
  
  return (
    <Badge variant="outline" className={config.color}>
      {config.label}
    </Badge>
  );
};

// KPI Card component
const KPICard = ({ title, value, subtitle, icon: Icon, trend, trendValue, color = "emerald" }) => (
  <Card className="bg-slate-800/50 border-slate-700">
    <CardContent className="p-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-slate-400 text-sm mb-1">{title}</p>
          <p className="text-3xl font-bold text-white">{value}</p>
          {subtitle && <p className="text-slate-500 text-sm mt-1">{subtitle}</p>}
          {trend && (
            <div className={`flex items-center gap-1 mt-2 text-sm ${trend === 'up' ? 'text-emerald-400' : 'text-red-400'}`}>
              <TrendingUp className={`w-4 h-4 ${trend === 'down' ? 'rotate-180' : ''}`} />
              {trendValue}
            </div>
          )}
        </div>
        <div className={`w-12 h-12 bg-${color}-500/20 rounded-lg flex items-center justify-center`}>
          <Icon className={`w-6 h-6 text-${color}-400`} />
        </div>
      </div>
    </CardContent>
  </Card>
);

export default function PartnerDashboardPage() {
  const navigate = useNavigate();
  const { user, token, logout } = useAuth();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");
  
  // Dashboard data
  const [dashboardData, setDashboardData] = useState(null);
  const [clients, setClients] = useState([]);
  const [commissions, setCommissions] = useState([]);
  const [commissionSummary, setCommissionSummary] = useState(null);
  
  // Modal states
  const [showAddClient, setShowAddClient] = useState(false);
  const [addingClient, setAddingClient] = useState(false);
  const [newClient, setNewClient] = useState({
    company_name: "",
    contact_name: "",
    email: "",
    phone: "",
    billing_type: "direct"
  });

  // Payouts state
  const [payoutBalance, setPayoutBalance] = useState(null);
  const [payoutHistory, setPayoutHistory] = useState([]);
  const [stripeConnectStatus, setStripeConnectStatus] = useState(null);
  const [requestingPayout, setRequestingPayout] = useState(false);
  const [connectingStripe, setConnectingStripe] = useState(false);
  const [showPayoutModal, setShowPayoutModal] = useState(false);
  const [payoutAmount, setPayoutAmount] = useState("");

  // Fetch dashboard data
  const fetchDashboard = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/partners/dashboard`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDashboardData(response.data);
    } catch (error) {
      console.error("Error fetching dashboard:", error);
      if (error.response?.status === 403) {
        toast.error("No tienes acceso al portal de partners");
        navigate("/dashboard");
      }
    }
  }, [token, navigate]);

  // Fetch clients
  const fetchClients = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/partners/clients`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setClients(response.data.clients || []);
    } catch (error) {
      console.error("Error fetching clients:", error);
    }
  }, [token]);

  // Fetch commissions
  const fetchCommissions = useCallback(async () => {
    try {
      const [commissionsRes, summaryRes] = await Promise.all([
        axios.get(`${API}/partners/commissions`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/partners/commissions/summary`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      setCommissions(commissionsRes.data.commissions || []);
      setCommissionSummary(summaryRes.data);
    } catch (error) {
      console.error("Error fetching commissions:", error);
    }
  }, [token]);

  // Fetch payout data
  const fetchPayoutData = useCallback(async () => {
    try {
      const [balanceRes, historyRes, connectRes] = await Promise.all([
        axios.get(`${API}/partners/payouts/balance`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/partners/payouts/history`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/partners/connect/status`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      setPayoutBalance(balanceRes.data);
      setPayoutHistory(historyRes.data.payouts || []);
      setStripeConnectStatus(connectRes.data);
    } catch (error) {
      console.error("Error fetching payout data:", error);
    }
  }, [token]);

  // Load all data
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([
        fetchDashboard(),
        fetchClients(),
        fetchCommissions(),
        fetchPayoutData()
      ]);
      setLoading(false);
    };
    
    if (token) {
      loadData();
    }
  }, [token, fetchDashboard, fetchClients, fetchCommissions, fetchPayoutData]);

  // Add new client
  const handleAddClient = async (e) => {
    e.preventDefault();
    
    if (!newClient.company_name || !newClient.contact_name || !newClient.email) {
      toast.error("Por favor completa los campos requeridos");
      return;
    }
    
    setAddingClient(true);
    try {
      const response = await axios.post(`${API}/partners/clients`, newClient, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success("Cliente agregado exitosamente");
      
      // Show email sent status
      if (response.data.email_sent) {
        toast.success(`Invitación enviada a ${response.data.email_sent_to}`);
      }
      
      // Copy invitation link
      if (response.data.invitation_link) {
        navigator.clipboard.writeText(response.data.invitation_link);
        toast.info("Link de invitación copiado al portapapeles");
      }
      
      // Reset form and close modal
      setNewClient({
        company_name: "",
        contact_name: "",
        email: "",
        phone: "",
        billing_type: "direct"
      });
      setShowAddClient(false);
      
      // Refresh data
      fetchClients();
      fetchDashboard();
      
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al agregar cliente");
    } finally {
      setAddingClient(false);
    }
  };

  // Copy referral link
  const copyReferralLink = () => {
    if (dashboardData?.firm?.referral_link) {
      navigator.clipboard.writeText(dashboardData.firm.referral_link);
      toast.success("Link de referido copiado al portapapeles");
    }
  };

  // Resend invitation email
  const resendInvitation = async (clientId, clientEmail) => {
    try {
      await axios.post(`${API}/partners/clients/${clientId}/resend-invitation`, null, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(`Invitación reenviada a ${clientEmail}`);
      fetchClients();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al reenviar invitación");
    }
  };

  // Change client billing type
  const updateClientBilling = async (clientId, billingType) => {
    try {
      await axios.patch(`${API}/partners/clients/${clientId}/billing`, null, {
        params: { billing_type: billingType },
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Tipo de facturación actualizado");
      fetchClients();
    } catch (error) {
      toast.error("Error al actualizar facturación");
    }
  };

  // Connect Stripe account
  const connectStripeAccount = async () => {
    setConnectingStripe(true);
    try {
      const response = await axios.post(`${API}/partners/connect/onboard`, {
        return_url: `${window.location.origin}/partner-dashboard?stripe=success`,
        refresh_url: `${window.location.origin}/partner-dashboard?stripe=refresh`
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Redirect to Stripe onboarding
      window.location.href = response.data.url;
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al conectar con Stripe");
      setConnectingStripe(false);
    }
  };

  // Open Stripe dashboard
  const openStripeDashboard = async () => {
    try {
      const response = await axios.get(`${API}/partners/connect/dashboard`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      window.open(response.data.url, "_blank");
    } catch (error) {
      toast.error("Error al abrir el dashboard de Stripe");
    }
  };

  // Request payout
  const handleRequestPayout = async () => {
    const amount = payoutAmount ? parseFloat(payoutAmount) : null;
    
    if (amount && amount < 50) {
      toast.error("El monto mínimo para retiro es $50.00");
      return;
    }
    
    if (amount && amount > (payoutBalance?.available_balance || 0)) {
      toast.error("Monto superior al balance disponible");
      return;
    }
    
    setRequestingPayout(true);
    try {
      const response = await axios.post(`${API}/partners/payouts/request`, {
        amount: amount
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success(response.data.message);
      setShowPayoutModal(false);
      setPayoutAmount("");
      fetchPayoutData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al procesar el retiro");
    } finally {
      setRequestingPayout(false);
    }
  };

  // Check for Stripe return
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const stripeParam = urlParams.get("stripe");
    
    if (stripeParam === "success") {
      toast.success("¡Cuenta de Stripe conectada exitosamente!");
      fetchPayoutData();
      // Clean URL
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (stripeParam === "refresh") {
      toast.info("Por favor completa la configuración de tu cuenta de Stripe");
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, [fetchPayoutData]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-900 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 text-emerald-400 animate-spin mx-auto mb-4" />
          <p className="text-slate-400">Cargando dashboard...</p>
        </div>
      </div>
    );
  }

  const firm = dashboardData?.firm || {};
  const stats = dashboardData?.statistics || {};
  const commissionsData = dashboardData?.commissions || {};
  const benefits = dashboardData?.benefits || {};
  const pricing = dashboardData?.pricing || {};

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-900">
      {/* Header */}
      <header className="bg-slate-900/80 backdrop-blur-md border-b border-slate-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <img src="/fortexarh-logo.png" alt="FortexaRH" className="h-8 w-auto" />
              <div>
                <h1 className="font-bold text-white">{firm.name || "Mi Firma"}</h1>
                <p className="text-emerald-400 text-xs">Portal de Partner</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <Link to="/dashboard">
                <Button variant="ghost" className="text-slate-300 hover:text-white hover:bg-slate-700">
                  <Building2 className="w-4 h-4 mr-2" />
                  Mi Empresa
                </Button>
              </Link>
              
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="text-slate-300 hover:text-white hover:bg-slate-700">
                    <Settings className="w-4 h-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="bg-slate-800 border-slate-700">
                  <DropdownMenuItem className="text-slate-300 hover:text-white hover:bg-slate-700">
                    <Settings className="w-4 h-4 mr-2" />
                    Configuración
                  </DropdownMenuItem>
                  <DropdownMenuItem 
                    className="text-red-400 hover:text-red-300 hover:bg-slate-700"
                    onClick={logout}
                  >
                    <LogOut className="w-4 h-4 mr-2" />
                    Cerrar Sesión
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-white mb-2">
            ¡Hola, {user?.name || firm.name}!
          </h2>
          <p className="text-slate-400">
            Gestiona tus clientes y comisiones desde tu portal de partner.
          </p>
        </div>

        {/* Referral Link Banner */}
        <Card className="bg-gradient-to-r from-emerald-600/20 to-teal-600/20 border-emerald-500/30 mb-8">
          <CardContent className="p-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h3 className="font-semibold text-white flex items-center gap-2">
                  <Award className="w-5 h-5 text-emerald-400" />
                  Tu Link de Referido
                </h3>
                <p className="text-slate-300 text-sm mt-1">
                  Comparte este link para ganar 30% de comisión por cada cliente
                </p>
                <code className="text-emerald-400 text-sm mt-2 block">
                  {firm.referral_link || "Cargando..."}
                </code>
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={copyReferralLink}
                  className="bg-emerald-500 hover:bg-emerald-600"
                >
                  <Copy className="w-4 h-4 mr-2" />
                  Copiar Link
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <KPICard
            title="Clientes Activos"
            value={stats.active_clients || 0}
            subtitle={`${stats.trial_clients || 0} en prueba`}
            icon={Users}
            color="emerald"
          />
          <KPICard
            title="Comisiones Pendientes"
            value={`$${(commissionsData.pending || 0).toFixed(2)}`}
            subtitle="Por pagar"
            icon={Wallet}
            color="amber"
          />
          <KPICard
            title="Total Ganado"
            value={`$${(commissionsData.total_earned || 0).toFixed(2)}`}
            subtitle={commissionsData.commission_rate}
            icon={TrendingUp}
            color="blue"
          />
          <KPICard
            title="Tu Precio Mensual"
            value={`$${pricing.current_price || 10}`}
            subtitle={benefits.has_benefits ? "Plan Partner" : "Plan Estándar"}
            icon={CreditCard}
            color={benefits.has_benefits ? "emerald" : "slate"}
          />
        </div>

        {/* Benefits Status */}
        {!benefits.has_benefits && (
          <Card className="bg-amber-500/10 border-amber-500/30 mb-8">
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-amber-400 font-medium">
                    Beneficios de Partner Inactivos
                  </p>
                  <p className="text-slate-400 text-sm mt-1">
                    Necesitas al menos 1 cliente activo con suscripción pagada para mantener el precio de $10/mes.
                    {benefits.grace_days_remaining > 0 && (
                      <span className="text-amber-400">
                        {" "}Te quedan {benefits.grace_days_remaining} días de gracia.
                      </span>
                    )}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="bg-slate-800 border border-slate-700">
            <TabsTrigger value="overview" className="data-[state=active]:bg-emerald-600">
              <BarChart3 className="w-4 h-4 mr-2" />
              Resumen
            </TabsTrigger>
            <TabsTrigger value="clients" className="data-[state=active]:bg-emerald-600">
              <Users className="w-4 h-4 mr-2" />
              Clientes ({stats.total_clients || 0})
            </TabsTrigger>
            <TabsTrigger value="commissions" className="data-[state=active]:bg-emerald-600">
              <DollarSign className="w-4 h-4 mr-2" />
              Comisiones
            </TabsTrigger>
            <TabsTrigger value="payouts" className="data-[state=active]:bg-emerald-600">
              <Banknote className="w-4 h-4 mr-2" />
              Retiros
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid lg:grid-cols-2 gap-6">
              {/* Recent Clients */}
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="text-white">Clientes Recientes</CardTitle>
                    <CardDescription className="text-slate-400">
                      Últimos clientes agregados
                    </CardDescription>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowAddClient(true)}
                    className="border-emerald-500 text-emerald-400 hover:bg-emerald-500 hover:text-white"
                  >
                    <Plus className="w-4 h-4 mr-1" />
                    Agregar
                  </Button>
                </CardHeader>
                <CardContent>
                  {dashboardData?.recent_clients?.length > 0 ? (
                    <div className="space-y-3">
                      {dashboardData.recent_clients.map((client, index) => (
                        <div
                          key={client.client_id || index}
                          className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg"
                        >
                          <div>
                            <p className="text-white font-medium">{client.company_name}</p>
                            <p className="text-slate-400 text-sm">{client.contact_name}</p>
                          </div>
                          <StatusBadge status={client.status} />
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <Users className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                      <p className="text-slate-400">No tienes clientes aún</p>
                      <Button
                        variant="link"
                        onClick={() => setShowAddClient(true)}
                        className="text-emerald-400 mt-2"
                      >
                        Agregar primer cliente
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Commission Summary */}
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white">Resumen de Comisiones</CardTitle>
                  <CardDescription className="text-slate-400">
                    Últimos 12 meses
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {commissionSummary?.monthly_breakdown?.length > 0 ? (
                    <div className="space-y-3">
                      {commissionSummary.monthly_breakdown.slice(0, 6).map((month, index) => (
                        <div
                          key={month.month || index}
                          className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg"
                        >
                          <div>
                            <p className="text-white font-medium">{month.month}</p>
                            <p className="text-slate-400 text-sm">
                              {month.transactions} transacciones
                            </p>
                          </div>
                          <p className="text-emerald-400 font-semibold">
                            ${month.total?.toFixed(2) || "0.00"}
                          </p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <DollarSign className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                      <p className="text-slate-400">Sin comisiones aún</p>
                      <p className="text-slate-500 text-sm mt-1">
                        Las comisiones aparecerán cuando tus clientes paguen
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Pricing Info */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Percent className="w-5 h-5 text-emerald-400" />
                  Tu Modelo de Precios
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-3 gap-6">
                  <div className="p-4 bg-slate-700/50 rounded-lg">
                    <p className="text-slate-400 text-sm mb-1">Tu Suscripción</p>
                    <p className="text-2xl font-bold text-white">
                      ${pricing.current_price || 10}/mes
                    </p>
                    <p className="text-emerald-400 text-sm mt-1">
                      {benefits.has_benefits ? "Empleados ilimitados" : "Precio por empleado activo"}
                    </p>
                  </div>
                  <div className="p-4 bg-slate-700/50 rounded-lg">
                    <p className="text-slate-400 text-sm mb-1">Comisión por Cliente</p>
                    <p className="text-2xl font-bold text-emerald-400">30%</p>
                    <p className="text-slate-400 text-sm mt-1">Recurrente de por vida</p>
                  </div>
                  <div className="p-4 bg-slate-700/50 rounded-lg">
                    <p className="text-slate-400 text-sm mb-1">Requisito para Beneficios</p>
                    <p className="text-2xl font-bold text-white">1+</p>
                    <p className="text-slate-400 text-sm mt-1">Cliente activo pagando</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Clients Tab */}
          <TabsContent value="clients" className="space-y-6">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-white">Mis Clientes</CardTitle>
                  <CardDescription className="text-slate-400">
                    Gestiona tus clientes referidos
                  </CardDescription>
                </div>
                <Button
                  onClick={() => setShowAddClient(true)}
                  className="bg-emerald-500 hover:bg-emerald-600"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Agregar Cliente
                </Button>
              </CardHeader>
              <CardContent>
                {clients.length > 0 ? (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow className="border-slate-700">
                          <TableHead className="text-slate-400">Empresa</TableHead>
                          <TableHead className="text-slate-400">Contacto</TableHead>
                          <TableHead className="text-slate-400">Estado</TableHead>
                          <TableHead className="text-slate-400">Invitación</TableHead>
                          <TableHead className="text-slate-400">Facturación</TableHead>
                          <TableHead className="text-slate-400">Comisión</TableHead>
                          <TableHead className="text-slate-400">Acciones</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {clients.map((client) => (
                          <TableRow key={client.client_id} className="border-slate-700">
                            <TableCell>
                              <div>
                                <p className="text-white font-medium">{client.company_name}</p>
                                <p className="text-slate-500 text-sm">{client.email}</p>
                              </div>
                            </TableCell>
                            <TableCell>
                              <div className="text-slate-300">
                                <p>{client.contact_name}</p>
                                {client.phone && (
                                  <p className="text-slate-500 text-sm">{client.phone}</p>
                                )}
                              </div>
                            </TableCell>
                            <TableCell>
                              <StatusBadge status={client.subscription_status || client.status} />
                            </TableCell>
                            <TableCell>
                              {client.invitation_sent ? (
                                <Badge variant="outline" className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
                                  <Mail className="w-3 h-3 mr-1" />
                                  Enviada
                                </Badge>
                              ) : (
                                <Badge variant="outline" className="bg-amber-500/20 text-amber-400 border-amber-500/30">
                                  <Clock className="w-3 h-3 mr-1" />
                                  Pendiente
                                </Badge>
                              )}
                            </TableCell>
                            <TableCell>
                              <Select
                                value={client.billing_type}
                                onValueChange={(value) => updateClientBilling(client.client_id, value)}
                              >
                                <SelectTrigger className="w-32 bg-slate-700 border-slate-600 text-slate-300">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent className="bg-slate-800 border-slate-700">
                                  <SelectItem value="direct">Directo</SelectItem>
                                  <SelectItem value="firm">Firma paga</SelectItem>
                                </SelectContent>
                              </Select>
                            </TableCell>
                            <TableCell>
                              <p className="text-emerald-400 font-medium">
                                ${(client.commission_earned || 0).toFixed(2)}
                              </p>
                            </TableCell>
                            <TableCell>
                              <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                  <Button variant="ghost" size="sm" className="text-slate-400">
                                    <MoreHorizontal className="w-4 h-4" />
                                  </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end" className="bg-slate-800 border-slate-700">
                                  <DropdownMenuItem className="text-slate-300 hover:text-white hover:bg-slate-700">
                                    <Eye className="w-4 h-4 mr-2" />
                                    Ver Detalles
                                  </DropdownMenuItem>
                                  {(client.status === "invited" || client.subscription_status === "pending") && (
                                    <DropdownMenuItem 
                                      className="text-slate-300 hover:text-white hover:bg-slate-700"
                                      onClick={() => resendInvitation(client.client_id, client.email)}
                                    >
                                      <Mail className="w-4 h-4 mr-2" />
                                      Reenviar Invitación
                                    </DropdownMenuItem>
                                  )}
                                  <DropdownMenuItem 
                                    className="text-slate-300 hover:text-white hover:bg-slate-700"
                                    onClick={() => {
                                      navigator.clipboard.writeText(client.invitation_link);
                                      toast.success("Link de invitación copiado");
                                    }}
                                  >
                                    <Copy className="w-4 h-4 mr-2" />
                                    Copiar Link
                                  </DropdownMenuItem>
                                </DropdownMenuContent>
                              </DropdownMenu>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Users className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-white mb-2">
                      No tienes clientes aún
                    </h3>
                    <p className="text-slate-400 mb-4">
                      Comienza agregando tu primer cliente o comparte tu link de referido
                    </p>
                    <div className="flex gap-3 justify-center">
                      <Button
                        onClick={() => setShowAddClient(true)}
                        className="bg-emerald-500 hover:bg-emerald-600"
                      >
                        <Plus className="w-4 h-4 mr-2" />
                        Agregar Cliente
                      </Button>
                      <Button
                        variant="outline"
                        onClick={copyReferralLink}
                        className="border-slate-600 text-slate-300"
                      >
                        <Copy className="w-4 h-4 mr-2" />
                        Copiar Link
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Commissions Tab */}
          <TabsContent value="commissions" className="space-y-6">
            <div className="grid md:grid-cols-3 gap-4 mb-6">
              <Card className="bg-slate-800/50 border-slate-700">
                <CardContent className="p-6">
                  <p className="text-slate-400 text-sm mb-1">Total Ganado</p>
                  <p className="text-3xl font-bold text-white">
                    ${(commissionsData.total_earned || 0).toFixed(2)}
                  </p>
                </CardContent>
              </Card>
              <Card className="bg-slate-800/50 border-slate-700">
                <CardContent className="p-6">
                  <p className="text-slate-400 text-sm mb-1">Pagado</p>
                  <p className="text-3xl font-bold text-emerald-400">
                    ${(commissionsData.total_paid || 0).toFixed(2)}
                  </p>
                </CardContent>
              </Card>
              <Card className="bg-slate-800/50 border-slate-700">
                <CardContent className="p-6">
                  <p className="text-slate-400 text-sm mb-1">Pendiente</p>
                  <p className="text-3xl font-bold text-amber-400">
                    ${(commissionsData.pending || 0).toFixed(2)}
                  </p>
                </CardContent>
              </Card>
            </div>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Historial de Comisiones</CardTitle>
                <CardDescription className="text-slate-400">
                  Todas las comisiones generadas por tus clientes
                </CardDescription>
              </CardHeader>
              <CardContent>
                {commissions.length > 0 ? (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow className="border-slate-700">
                          <TableHead className="text-slate-400">Fecha</TableHead>
                          <TableHead className="text-slate-400">Cliente</TableHead>
                          <TableHead className="text-slate-400">Monto</TableHead>
                          <TableHead className="text-slate-400">Estado</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {commissions.map((commission, index) => (
                          <TableRow key={commission.commission_id || index} className="border-slate-700">
                            <TableCell className="text-slate-300">
                              {new Date(commission.created_at).toLocaleDateString()}
                            </TableCell>
                            <TableCell className="text-white">
                              {commission.client_name || commission.client_id}
                            </TableCell>
                            <TableCell className="text-emerald-400 font-medium">
                              ${commission.amount?.toFixed(2) || "0.00"}
                            </TableCell>
                            <TableCell>
                              <StatusBadge status={commission.status} />
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <DollarSign className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-white mb-2">
                      Sin comisiones aún
                    </h3>
                    <p className="text-slate-400">
                      Las comisiones se generarán cuando tus clientes realicen pagos
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Payouts Tab */}
          <TabsContent value="payouts" className="space-y-6">
            {/* Stripe Connect Status */}
            {!stripeConnectStatus?.connected || stripeConnectStatus?.status !== "active" ? (
              <Card className="bg-gradient-to-r from-purple-600/20 to-indigo-600/20 border-purple-500/30">
                <CardContent className="p-6">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="flex items-start gap-4">
                      <div className="w-12 h-12 bg-purple-500/20 rounded-xl flex items-center justify-center">
                        <CreditCard className="w-6 h-6 text-purple-400" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-white flex items-center gap-2">
                          Conecta tu Cuenta Bancaria
                        </h3>
                        <p className="text-slate-300 text-sm mt-1 max-w-md">
                          Para recibir tus comisiones, necesitas conectar tu cuenta bancaria a través de Stripe.
                          Es seguro, rápido y solo toma unos minutos.
                        </p>
                        {stripeConnectStatus?.status === "pending" && (
                          <p className="text-amber-400 text-sm mt-2 flex items-center gap-1">
                            <AlertTriangle className="w-4 h-4" />
                            Verificación pendiente - completa tu configuración
                          </p>
                        )}
                      </div>
                    </div>
                    <Button
                      onClick={connectStripeAccount}
                      disabled={connectingStripe}
                      className="bg-purple-500 hover:bg-purple-600"
                    >
                      {connectingStripe ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Conectando...
                        </>
                      ) : stripeConnectStatus?.status === "pending" ? (
                        <>
                          <ArrowUpRight className="w-4 h-4 mr-2" />
                          Completar Configuración
                        </>
                      ) : (
                        <>
                          <CreditCard className="w-4 h-4 mr-2" />
                          Conectar con Stripe
                        </>
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card className="bg-emerald-500/10 border-emerald-500/30">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <ShieldCheck className="w-6 h-6 text-emerald-400" />
                      <div>
                        <p className="text-emerald-400 font-medium">Cuenta de Stripe Conectada</p>
                        <p className="text-slate-400 text-sm">Lista para recibir pagos</p>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={openStripeDashboard}
                      className="border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20"
                    >
                      <ExternalLink className="w-4 h-4 mr-2" />
                      Ver Dashboard
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Balance Cards */}
            <div className="grid md:grid-cols-4 gap-4">
              <Card className="bg-slate-800/50 border-slate-700">
                <CardContent className="p-6">
                  <p className="text-slate-400 text-sm mb-1">Balance Disponible</p>
                  <p className="text-3xl font-bold text-emerald-400">
                    ${payoutBalance?.available_balance?.toFixed(2) || "0.00"}
                  </p>
                  <p className="text-slate-500 text-xs mt-1">
                    Mínimo para retiro: ${payoutBalance?.minimum_payout || 50}
                  </p>
                </CardContent>
              </Card>
              <Card className="bg-slate-800/50 border-slate-700">
                <CardContent className="p-6">
                  <p className="text-slate-400 text-sm mb-1">Total Ganado</p>
                  <p className="text-3xl font-bold text-white">
                    ${payoutBalance?.total_earned?.toFixed(2) || "0.00"}
                  </p>
                </CardContent>
              </Card>
              <Card className="bg-slate-800/50 border-slate-700">
                <CardContent className="p-6">
                  <p className="text-slate-400 text-sm mb-1">Total Pagado</p>
                  <p className="text-3xl font-bold text-blue-400">
                    ${payoutBalance?.total_paid?.toFixed(2) || "0.00"}
                  </p>
                </CardContent>
              </Card>
              <Card className="bg-slate-800/50 border-slate-700">
                <CardContent className="p-6">
                  <p className="text-slate-400 text-sm mb-1">En Proceso</p>
                  <p className="text-3xl font-bold text-amber-400">
                    ${payoutBalance?.pending_payouts?.toFixed(2) || "0.00"}
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Withdraw Button */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                  <div>
                    <h3 className="text-white font-semibold">Solicitar Retiro</h3>
                    <p className="text-slate-400 text-sm">
                      Los pagos se procesan mensualmente. El dinero llega en 2-3 días hábiles.
                    </p>
                  </div>
                  <Button
                    onClick={() => setShowPayoutModal(true)}
                    disabled={!payoutBalance?.can_withdraw}
                    className="bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50"
                    data-testid="request-payout-btn"
                  >
                    <Banknote className="w-4 h-4 mr-2" />
                    {payoutBalance?.can_withdraw 
                      ? "Retirar Fondos" 
                      : payoutBalance?.stripe_connected 
                        ? `Mínimo $${payoutBalance?.minimum_payout || 50}` 
                        : "Conecta Stripe primero"}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Payout History */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Historial de Retiros</CardTitle>
                <CardDescription className="text-slate-400">
                  Todos los retiros procesados y pendientes
                </CardDescription>
              </CardHeader>
              <CardContent>
                {payoutHistory.length > 0 ? (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow className="border-slate-700">
                          <TableHead className="text-slate-400">Fecha</TableHead>
                          <TableHead className="text-slate-400">ID</TableHead>
                          <TableHead className="text-slate-400">Monto</TableHead>
                          <TableHead className="text-slate-400">Estado</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {payoutHistory.map((payout, index) => (
                          <TableRow key={payout.payout_id || index} className="border-slate-700">
                            <TableCell className="text-slate-300">
                              {new Date(payout.requested_at).toLocaleDateString()}
                            </TableCell>
                            <TableCell className="text-slate-400 font-mono text-xs">
                              {payout.payout_id}
                            </TableCell>
                            <TableCell className="text-emerald-400 font-medium">
                              ${payout.amount?.toFixed(2) || "0.00"}
                            </TableCell>
                            <TableCell>
                              <StatusBadge status={payout.status} />
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Banknote className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-white mb-2">
                      Sin retiros aún
                    </h3>
                    <p className="text-slate-400">
                      Cuando solicites un retiro, aparecerá aquí
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>

      {/* Add Client Modal */}
      <Dialog open={showAddClient} onOpenChange={setShowAddClient}>
        <DialogContent className="bg-slate-800 border-slate-700 max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white">Agregar Nuevo Cliente</DialogTitle>
            <DialogDescription className="text-slate-400">
              Ingresa los datos del cliente para enviarle una invitación
            </DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleAddClient} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="company_name" className="text-slate-300">
                Nombre de la Empresa *
              </Label>
              <Input
                id="company_name"
                value={newClient.company_name}
                onChange={(e) => setNewClient(prev => ({ ...prev, company_name: e.target.value }))}
                placeholder="Empresa Cliente SRL"
                className="bg-slate-700 border-slate-600 text-white"
                data-testid="add-client-company"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="contact_name" className="text-slate-300">
                Nombre del Contacto *
              </Label>
              <Input
                id="contact_name"
                value={newClient.contact_name}
                onChange={(e) => setNewClient(prev => ({ ...prev, contact_name: e.target.value }))}
                placeholder="Juan Pérez"
                className="bg-slate-700 border-slate-600 text-white"
                data-testid="add-client-contact"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="client_email" className="text-slate-300">
                Correo Electrónico *
              </Label>
              <Input
                id="client_email"
                type="email"
                value={newClient.email}
                onChange={(e) => setNewClient(prev => ({ ...prev, email: e.target.value }))}
                placeholder="contacto@empresa.com"
                className="bg-slate-700 border-slate-600 text-white"
                data-testid="add-client-email"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="client_phone" className="text-slate-300">
                Teléfono
              </Label>
              <Input
                id="client_phone"
                value={newClient.phone}
                onChange={(e) => setNewClient(prev => ({ ...prev, phone: e.target.value }))}
                placeholder="809-000-0000"
                className="bg-slate-700 border-slate-600 text-white"
              />
            </div>
            
            <div className="space-y-2">
              <Label className="text-slate-300">Tipo de Facturación</Label>
              <Select
                value={newClient.billing_type}
                onValueChange={(value) => setNewClient(prev => ({ ...prev, billing_type: value }))}
              >
                <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-700">
                  <SelectItem value="direct">
                    Directo al cliente (cliente paga su suscripción)
                  </SelectItem>
                  <SelectItem value="firm">
                    Firma paga (tú pagas con descuento)
                  </SelectItem>
                </SelectContent>
              </Select>
              <p className="text-slate-500 text-xs">
                {newClient.billing_type === "direct" 
                  ? "El cliente pagará directamente y recibirás 30% de comisión"
                  : "Tú pagas la suscripción del cliente con 30% de descuento"
                }
              </p>
            </div>
            
            <DialogFooter className="pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowAddClient(false)}
                className="border-slate-600 text-slate-300"
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                className="bg-emerald-500 hover:bg-emerald-600"
                disabled={addingClient}
              >
                {addingClient ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Agregando...
                  </>
                ) : (
                  <>
                    <Plus className="w-4 h-4 mr-2" />
                    Agregar Cliente
                  </>
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Payout Request Modal */}
      <Dialog open={showPayoutModal} onOpenChange={setShowPayoutModal}>
        <DialogContent className="bg-slate-800 border-slate-700 max-w-md">
          <DialogHeader>
            <DialogTitle className="text-white">Solicitar Retiro</DialogTitle>
            <DialogDescription className="text-slate-400">
              Retira tus comisiones a tu cuenta bancaria
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="bg-slate-700/50 rounded-lg p-4">
              <p className="text-slate-400 text-sm">Balance Disponible</p>
              <p className="text-2xl font-bold text-emerald-400">
                ${payoutBalance?.available_balance?.toFixed(2) || "0.00"}
              </p>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="payout_amount" className="text-slate-300">
                Monto a Retirar (USD)
              </Label>
              <Input
                id="payout_amount"
                type="number"
                min="50"
                max={payoutBalance?.available_balance || 0}
                step="0.01"
                value={payoutAmount}
                onChange={(e) => setPayoutAmount(e.target.value)}
                placeholder={`Mínimo $50 - Máximo $${payoutBalance?.available_balance?.toFixed(2) || "0.00"}`}
                className="bg-slate-700 border-slate-600 text-white"
                data-testid="payout-amount-input"
              />
              <p className="text-slate-500 text-xs">
                Deja en blanco para retirar todo el balance disponible
              </p>
            </div>
            
            <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3">
              <p className="text-blue-400 text-sm flex items-center gap-2">
                <Clock className="w-4 h-4" />
                El dinero llegará a tu cuenta en 2-3 días hábiles
              </p>
            </div>
          </div>
          
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowPayoutModal(false)}
              className="border-slate-600 text-slate-300"
            >
              Cancelar
            </Button>
            <Button
              onClick={handleRequestPayout}
              className="bg-emerald-500 hover:bg-emerald-600"
              disabled={requestingPayout}
              data-testid="confirm-payout-btn"
            >
              {requestingPayout ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Procesando...
                </>
              ) : (
                <>
                  <Banknote className="w-4 h-4 mr-2" />
                  Confirmar Retiro
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
