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
  Check,
  Banknote,
  ArrowUpRight,
  ShieldCheck,
  AlertTriangle,
  X,
  Info,
  Share2
} from "lucide-react";
import { KPIDrillDownDialog } from "@/components/partner/KPIDrillDownDialog";
import { AddClientDialog } from "@/components/partner/AddClientDialog";
import { PayoutRequestDialog } from "@/components/partner/PayoutRequestDialog";
import NotificationBell from "@/components/NotificationBell";
import { BrochureBuilderPanel } from "./BrochureBuilderPage";

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

// KPI Card component - clickable for drill-down
const KPICard = ({ title, value, subtitle, icon: Icon, trend, trendValue, color = "emerald", onClick }) => (
  <Card
    className={`bg-slate-800/50 border-slate-700 transition-all ${onClick ? "cursor-pointer hover:border-slate-500 hover:bg-slate-800/70 hover:scale-[1.02]" : ""}`}
    onClick={onClick}
    data-testid={`kpi-card-${title.toLowerCase().replace(/\s+/g, "-")}`}
  >
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
        <div className="flex flex-col items-end gap-2">
          <div className={`w-12 h-12 bg-${color}-500/20 rounded-lg flex items-center justify-center`}>
            <Icon className={`w-6 h-6 text-${color}-400`} />
          </div>
          {onClick && <ChevronRight className="w-4 h-4 text-slate-500" />}
        </div>
      </div>
    </CardContent>
  </Card>
);

export default function PartnerDashboardPage() {
  const { t } = useTranslation();
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

  // Plans and activation state
  const [plans, setPlans] = useState([]);
  const [showActivateClient, setShowActivateClient] = useState(false);
  const [showEditSubscription, setShowEditSubscription] = useState(false);
  const [selectedClient, setSelectedClient] = useState(null);
  const [activationData, setActivationData] = useState({ plan_id: "basic", employee_count: 1 });
  const [activating, setActivating] = useState(false);

  // Fetch plans
  const fetchPlans = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/partners/plans`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPlans(response.data.plans || []);
    } catch (error) {
      console.error("Error fetching plans:", error);
    }
  }, [token]);

  // Payouts state
  const [payoutBalance, setPayoutBalance] = useState(null);
  const [payoutHistory, setPayoutHistory] = useState([]);
  const [stripeConnectStatus, setStripeConnectStatus] = useState(null);
  const [requestingPayout, setRequestingPayout] = useState(false);
  const [connectingStripe, setConnectingStripe] = useState(false);
  const [showPayoutModal, setShowPayoutModal] = useState(false);
  const [payoutAmount, setPayoutAmount] = useState("");

  // Drill-down states
  const [drillDown, setDrillDown] = useState(null); // "clients" | "pending" | "earned" | "pricing"

  // PayPal state
  const [paypalEmail, setPaypalEmail] = useState("");
  const [savingPaypal, setSavingPaypal] = useState(false);
  const [payoutMethod, setPayoutMethod] = useState("stripe");

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
        toast.error(t('common.accessDenied'));
        navigate("/dashboard");
      }
    }
  }, [token, navigate, t]);

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
        fetchPayoutData(),
        fetchPlans()
      ]);
      setLoading(false);
    };
    
    if (token) {
      loadData();
    }
  }, [token, fetchDashboard, fetchClients, fetchCommissions, fetchPayoutData, fetchPlans]);

  // Add new client
  const handleAddClient = async (e) => {
    e.preventDefault();
    
    if (!newClient.company_name || !newClient.contact_name || !newClient.email) {
      toast.error(t('partner.dashboard.completeRequiredFields'));
      return;
    }
    
    setAddingClient(true);
    try {
      const response = await axios.post(`${API}/partners/clients`, newClient, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success(t('partner.dashboard.clientAdded'));
      
      // Show email sent status
      if (response.data.email_sent) {
        toast.success(t('partner.dashboard.invitationSent', { email: response.data.email_sent_to }));
      }
      
      // Copy invitation link
      if (response.data.invitation_link) {
        navigator.clipboard.writeText(response.data.invitation_link);
        toast.info(t('partner.dashboard.invitationLinkCopied'));
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
      toast.error(error.response?.data?.detail || t('partner.dashboard.errorAddingClient'));
    } finally {
      setAddingClient(false);
    }
  };

  // Copy referral link
  const copyReferralLink = () => {
    if (dashboardData?.firm?.referral_link) {
      navigator.clipboard.writeText(dashboardData.firm.referral_link);
      toast.success(t('partner.dashboard.referralLinkCopied'));
    }
  };

  // Resend invitation email
  const resendInvitation = async (clientId, clientEmail) => {
    try {
      await axios.post(`${API}/partners/clients/${clientId}/resend-invitation`, null, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(t('partner.dashboard.invitationResent', { email: clientEmail }));
      fetchClients();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('partner.dashboard.errorResendingInvitation'));
    }
  };

  // Change client billing type
  const updateClientBilling = async (clientId, billingType) => {
    try {
      await axios.patch(`${API}/partners/clients/${clientId}/billing`, null, {
        params: { billing_type: billingType },
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(t('partner.dashboard.billingTypeUpdated'));
      fetchClients();
    } catch (error) {
      toast.error(t('partner.dashboard.errorUpdatingBilling'));
    }
  };

  // Calculate monthly value for plan + employees
  const calculateMonthly = (planId, empCount) => {
    const plan = plans.find(p => p.plan_id === planId);
    if (!plan) return 0;
    return plan.base_price + (empCount * plan.price_per_employee);
  };

  // Activate client with plan
  const handleActivateClient = async () => {
    if (!selectedClient) return;
    setActivating(true);
    try {
      await axios.patch(`${API}/partners/clients/${selectedClient.client_id}/activate`, activationData, {
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }
      });
      toast.success(`Cliente ${selectedClient.company_name} activado exitosamente`);
      setShowActivateClient(false);
      setSelectedClient(null);
      setActivationData({ plan_id: "basic", employee_count: 1 });
      fetchClients();
      fetchDashboard();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al activar cliente");
    } finally {
      setActivating(false);
    }
  };

  // Update client subscription
  const handleUpdateSubscription = async () => {
    if (!selectedClient) return;
    setActivating(true);
    try {
      await axios.patch(`${API}/partners/clients/${selectedClient.client_id}/subscription`, activationData, {
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }
      });
      toast.success("Suscripción actualizada exitosamente");
      setShowEditSubscription(false);
      setSelectedClient(null);
      fetchClients();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al actualizar suscripción");
    } finally {
      setActivating(false);
    }
  };

  // Deactivate client
  const handleDeactivateClient = async (clientId, companyName) => {
    if (!window.confirm(`¿Estás seguro de desactivar a ${companyName}?`)) return;
    try {
      await axios.patch(`${API}/partners/clients/${clientId}/deactivate`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Cliente desactivado");
      fetchClients();
      fetchDashboard();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al desactivar cliente");
    }
  };

  // Clipboard fallback
  const safeCopy = (text) => {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => {
        toast.success(t('partner.dashboard.invitationLinkCopied'));
      }).catch(() => {
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        toast.success(t('partner.dashboard.invitationLinkCopied'));
      });
    } else {
      toast.info("Link: " + text);
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
      toast.error(error.response?.data?.detail || t('partner.dashboard.errorConnectingStripe'));
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
      toast.error(t('partner.dashboard.errorOpeningStripeDashboard'));
    }
  };

  // Request payout
  const handleRequestPayout = async () => {
    const amount = payoutAmount ? parseFloat(payoutAmount) : null;
    
    if (amount && amount < 50) {
      toast.error(t('partner.dashboard.minWithdrawalAmount'));
      return;
    }
    
    if (amount && amount > (payoutBalance?.available_balance || 0)) {
      toast.error(t('partner.dashboard.amountExceedsBalance'));
      return;
    }
    
    setRequestingPayout(true);
    try {
      const response = await axios.post(`${API}/partners/payouts/request`, {
        amount: amount,
        method: payoutMethod
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success(response.data.message);
      setShowPayoutModal(false);
      setPayoutAmount("");
      fetchPayoutData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('partner.dashboard.errorProcessingWithdrawal'));
    } finally {
      setRequestingPayout(false);
    }
  };

  // Configure PayPal
  const handleSavePaypal = async () => {
    if (!paypalEmail || !paypalEmail.includes("@")) {
      toast.error("Ingresa un email de PayPal válido");
      return;
    }
    setSavingPaypal(true);
    try {
      await axios.post(`${API}/partners/paypal/configure`, {
        paypal_email: paypalEmail
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Email de PayPal configurado correctamente");
      fetchPayoutData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al configurar PayPal");
    } finally {
      setSavingPaypal(false);
    }
  };

  // Remove PayPal
  const handleRemovePaypal = async () => {
    try {
      await axios.delete(`${API}/partners/paypal/configure`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Configuración de PayPal eliminada");
      setPaypalEmail("");
      fetchPayoutData();
    } catch (error) {
      toast.error("Error al eliminar PayPal");
    }
  };

  // Check for Stripe return
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const stripeParam = urlParams.get("stripe");
    
    if (stripeParam === "success") {
      toast.success(t('partner.dashboard.stripeConnected'));
      fetchPayoutData();
      // Clean URL
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (stripeParam === "refresh") {
      toast.info(t('partner.dashboard.completeStripeSetup'));
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, [fetchPayoutData]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-900 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 text-emerald-400 animate-spin mx-auto mb-4" />
          <p className="text-slate-400">{t('partnerDashboard.cargandoDashboard')}</p>
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
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-900" data-testid="partner-dashboard-page">
      {/* Header */}
      <header className="bg-slate-900/80 backdrop-blur-md border-b border-slate-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <img src="/fortexarh-logo.png" alt="FortexaRH" className="h-8 w-auto" />
              <div>
                <h1 className="font-bold text-white">{firm.name || "Mi Firma"}</h1>
                <p className="text-emerald-400 text-xs">{t('partnerDashboard.portalDePartner')}</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <NotificationBell />
              <Link to="/dashboard">
                <Button variant="ghost" className="text-slate-300 hover:text-white hover:bg-slate-700">
                  <Building2 className="w-4 h-4 mr-2" />
                  {t('partner.dashboard.myCompany')}
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
                    {t('partner.dashboard.settings')}
                  </DropdownMenuItem>
                  <DropdownMenuItem 
                    className="text-red-400 hover:text-red-300 hover:bg-slate-700"
                    onClick={logout}
                    data-testid="partner-logout-btn"
                  >
                    <LogOut className="w-4 h-4 mr-2" />
                    {t('partner.dashboard.logout')}
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
            {t('partner.dashboard.hello', { name: user?.name || firm.name })}
          </h2>
          <p className="text-slate-400">
            {t('partner.dashboard.manageClients')}
          </p>
        </div>

        {/* Referral Link Banner */}
        <Card className="bg-gradient-to-r from-emerald-600/20 to-teal-600/20 border-emerald-500/30 mb-8">
          <CardContent className="p-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h3 className="font-semibold text-white flex items-center gap-2">
                  <Award className="w-5 h-5 text-emerald-400" />
                  {t('partner.dashboard.yourReferralLink')}
                </h3>
                <p className="text-slate-300 text-sm mt-1">
                  {t('partner.dashboard.shareForCommission')}
                </p>
                <code className="text-emerald-400 text-sm mt-2 block">
                  {firm.referral_link || "Cargando..."}
                </code>
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={copyReferralLink}
                  className="bg-emerald-500 hover:bg-emerald-600"
                  data-testid="copy-referral-link-btn"
                >
                  <Copy className="w-4 h-4 mr-2" />
                  {t('partner.dashboard.copyLink')}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <KPICard
            title={t('partner.dashboard.activeClients')}
            value={stats.active_clients || 0}
            subtitle={`${stats.trial_clients || 0} ${t('partner.dashboard.onTrial')}`}
            icon={Users}
            color="emerald"
            onClick={() => setDrillDown("clients")}
          />
          <KPICard
            title={t('partner.dashboard.pendingCommissions')}
            value={`$${(commissionsData.pending || 0).toFixed(2)}`}
            subtitle={t('partner.dashboard.toPay')}
            icon={Wallet}
            color="amber"
            onClick={() => setDrillDown("pending")}
          />
          <KPICard
            title={t('partner.dashboard.totalEarned')}
            value={`$${(commissionsData.total_earned || 0).toFixed(2)}`}
            subtitle={commissionsData.commission_rate}
            icon={TrendingUp}
            color="blue"
            onClick={() => setDrillDown("earned")}
          />
          <KPICard
            title={t('partner.dashboard.yourMonthlyPrice')}
            value={`$${typeof pricing.current_price === "number" ? pricing.current_price : 10}`}
            subtitle={benefits.has_benefits ? t('partner.dashboard.partnerPlan') : t('partner.dashboard.standardPlan')}
            icon={CreditCard}
            color={benefits.has_benefits ? "emerald" : "slate"}
            onClick={() => setDrillDown("pricing")}
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
                    {t('partner.dashboard.benefitsInactive')}
                  </p>
                  <p className="text-slate-400 text-sm mt-1">
                    {t('partner.dashboard.benefitsRequirement')}
                    {benefits.grace_days_remaining > 0 && (
                      <span className="text-amber-400">
                        {" "}{t('partner.dashboard.graceDaysRemaining', { days: benefits.grace_days_remaining })}
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
            <TabsTrigger value="overview" className="data-[state=active]:bg-emerald-600" data-testid="tab-overview">
              <BarChart3 className="w-4 h-4 mr-2" />
              {t('partner.dashboard.overview')}
            </TabsTrigger>
            <TabsTrigger value="clients" className="data-[state=active]:bg-emerald-600" data-testid="tab-clients">
              <Users className="w-4 h-4 mr-2" />
              {t('partner.dashboard.clients')} ({stats.total_clients || 0})
            </TabsTrigger>
            <TabsTrigger value="commissions" className="data-[state=active]:bg-emerald-600" data-testid="tab-commissions">
              <DollarSign className="w-4 h-4 mr-2" />
              {t('partner.dashboard.commissions')}
            </TabsTrigger>
            <TabsTrigger value="payouts" className="data-[state=active]:bg-emerald-600" data-testid="tab-payouts">
              <Banknote className="w-4 h-4 mr-2" />
              {t('partner.dashboard.withdrawals')}
            </TabsTrigger>
            <TabsTrigger value="brochure-builder" className="data-[state=active]:bg-indigo-600" data-testid="tab-brochure-builder">
              <Share2 className="w-4 h-4 mr-2" />
              Brochure Builder
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid lg:grid-cols-2 gap-6">
              {/* Recent Clients */}
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="text-white">{t('partnerDashboard.clientesRecientes')}</CardTitle>
                    <CardDescription className="text-slate-400">
                      {t('partner.dashboard.lastAdded')}
                    </CardDescription>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowAddClient(true)}
                    className="border-emerald-500 text-emerald-400 hover:bg-emerald-500 hover:text-white"
                  >
                    <Plus className="w-4 h-4 mr-1" />
                    {t('partner.dashboard.add')}
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
                      <p className="text-slate-400">{t('partnerDashboard.noTienesClientesAun')}</p>
                      <Button
                        variant="link"
                        onClick={() => setShowAddClient(true)}
                        className="text-emerald-400 mt-2"
                      >
                        {t('partner.dashboard.addFirstClient')}
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Commission Summary */}
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white">{t('partnerDashboard.resumenDeComisiones')}</CardTitle>
                  <CardDescription className="text-slate-400">
                    {t('partner.dashboard.last12Months')}
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
                      <p className="text-slate-400">{t('partner.dashboard.noCommissions')}</p>
                      <p className="text-slate-500 text-sm mt-1">
                        {t('partner.dashboard.commissionsWillAppear')}
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
                    <p className="text-slate-400 text-sm mb-1">{t('partnerDashboard.tuSuscripcion')}</p>
                    <p className="text-2xl font-bold text-white">
                      ${pricing.current_price || 10}/mes
                    </p>
                    <p className="text-emerald-400 text-sm mt-1">
                      {benefits.has_benefits ? t('partner.dashboard.unlimitedEmployees') : t('partner.dashboard.pricePerEmployee')}
                    </p>
                  </div>
                  <div className="p-4 bg-slate-700/50 rounded-lg">
                    <p className="text-slate-400 text-sm mb-1">{t('partnerDashboard.comisionPorCliente')}</p>
                    <p className="text-2xl font-bold text-emerald-400">30%</p>
                    <p className="text-slate-400 text-sm mt-1">{t('partnerDashboard.recurrenteDePorVida')}</p>
                  </div>
                  <div className="p-4 bg-slate-700/50 rounded-lg">
                    <p className="text-slate-400 text-sm mb-1">{t('partnerDashboard.requisitoParaBeneficios')}</p>
                    <p className="text-2xl font-bold text-white">1+</p>
                    <p className="text-slate-400 text-sm mt-1">{t('partnerDashboard.clienteActivoPagando')}</p>
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
                  <CardTitle className="text-white">{t('partnerDashboard.misClientes')}</CardTitle>
                  <CardDescription className="text-slate-400">
                    {t('partner.dashboard.manageReferredClients')}
                  </CardDescription>
                </div>
                <Button
                  onClick={() => setShowAddClient(true)}
                  className="bg-emerald-500 hover:bg-emerald-600"
                  data-testid="add-client-btn"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  {t('partner.dashboard.addClient')}
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
                          <TableHead className="text-slate-400">Plan</TableHead>
                          <TableHead className="text-slate-400">Empleados</TableHead>
                          <TableHead className="text-slate-400">Valor Mensual</TableHead>
                          <TableHead className="text-slate-400">Comisión (30%)</TableHead>
                          <TableHead className="text-slate-400">Acciones</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {clients.map((client) => {
                          const isActive = client.status === "active";
                          const planName = plans.find(p => p.plan_id === client.subscription_plan)?.name || "-";
                          return (
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
                                  {client.phone && <p className="text-slate-500 text-sm">{client.phone}</p>}
                                </div>
                              </TableCell>
                              <TableCell>
                                <StatusBadge status={client.subscription_status || client.status} />
                              </TableCell>
                              <TableCell>
                                {client.subscription_plan ? (
                                  <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30">
                                    {planName}
                                  </Badge>
                                ) : (
                                  <span className="text-slate-500">-</span>
                                )}
                              </TableCell>
                              <TableCell>
                                {client.employee_count ? (
                                  <span className="text-slate-300 font-medium">{client.employee_count}</span>
                                ) : (
                                  <span className="text-slate-500">-</span>
                                )}
                              </TableCell>
                              <TableCell>
                                {client.monthly_value ? (
                                  <span className="text-white font-medium">${client.monthly_value.toFixed(2)}</span>
                                ) : (
                                  <span className="text-slate-500">-</span>
                                )}
                              </TableCell>
                              <TableCell>
                                {client.monthly_value ? (
                                  <span className="text-emerald-400 font-semibold">
                                    ${(client.monthly_value * 0.3).toFixed(2)}
                                  </span>
                                ) : (
                                  <span className="text-slate-500">-</span>
                                )}
                              </TableCell>
                              <TableCell>
                                <div className="flex items-center gap-1">
                                  {!isActive ? (
                                    <Button
                                      size="sm"
                                      className="bg-emerald-500 hover:bg-emerald-600 text-xs"
                                      data-testid={`activate-client-${client.client_id}`}
                                      onClick={() => {
                                        setSelectedClient(client);
                                        setActivationData({ plan_id: "basic", employee_count: 1 });
                                        setShowActivateClient(true);
                                      }}
                                    >
                                      Activar
                                    </Button>
                                  ) : (
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      className="border-slate-600 text-slate-300 text-xs"
                                      data-testid={`edit-sub-${client.client_id}`}
                                      onClick={() => {
                                        setSelectedClient(client);
                                        setActivationData({
                                          plan_id: client.subscription_plan || "basic",
                                          employee_count: client.employee_count || 1
                                        });
                                        setShowEditSubscription(true);
                                      }}
                                    >
                                      <Edit2 className="w-3 h-3 mr-1" />
                                      Editar
                                    </Button>
                                  )}
                                  <DropdownMenu>
                                    <DropdownMenuTrigger asChild>
                                      <Button variant="ghost" size="sm" className="text-slate-400">
                                        <MoreHorizontal className="w-4 h-4" />
                                      </Button>
                                    </DropdownMenuTrigger>
                                    <DropdownMenuContent align="end" className="bg-slate-800 border-slate-700">
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
                                        onClick={() => safeCopy(client.invitation_link)}
                                      >
                                        <Copy className="w-4 h-4 mr-2" />
                                        Copiar Link
                                      </DropdownMenuItem>
                                      {isActive && (
                                        <DropdownMenuItem
                                          className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                                          onClick={() => handleDeactivateClient(client.client_id, client.company_name)}
                                        >
                                          <XCircle className="w-4 h-4 mr-2" />
                                          Desactivar
                                        </DropdownMenuItem>
                                      )}
                                    </DropdownMenuContent>
                                  </DropdownMenu>
                                </div>
                              </TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Users className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-white mb-2">No tienes clientes aún</h3>
                    <p className="text-slate-400 mb-4">
                      Comienza agregando tu primer cliente o comparte tu link de referido
                    </p>
                    <div className="flex gap-3 justify-center">
                      <Button onClick={() => setShowAddClient(true)} className="bg-emerald-500 hover:bg-emerald-600">
                        <Plus className="w-4 h-4 mr-2" />
                        Agregar Cliente
                      </Button>
                      <Button variant="outline" onClick={() => safeCopy(dashboardData.referral_link)} className="border-slate-600 text-slate-300">
                        <Copy className="w-4 h-4 mr-2" />
                        Copiar Link
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Plans Summary */}
            {plans.length > 0 && (
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white text-lg">Planes Disponibles</CardTitle>
                  <CardDescription className="text-slate-400">Planes que puedes asignar a tus clientes</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid md:grid-cols-3 gap-4">
                    {plans.map((plan) => (
                      <div key={plan.plan_id} className="bg-slate-700/50 border border-slate-600 rounded-lg p-4">
                        <h4 className="text-white font-semibold mb-1">{plan.name}</h4>
                        <p className="text-emerald-400 text-2xl font-bold">${plan.base_price}<span className="text-sm text-slate-400">/mes</span></p>
                        <p className="text-slate-400 text-sm mt-1">+ ${plan.price_per_employee}/empleado</p>
                        <p className="text-slate-500 text-xs mt-2">Máx. {plan.max_employees >= 9999 ? "ilimitados" : plan.max_employees} empleados</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Commissions Tab */}
          <TabsContent value="commissions" className="space-y-6">
            <div className="grid md:grid-cols-3 gap-4 mb-6">
              <Card className="bg-slate-800/50 border-slate-700">
                <CardContent className="p-6">
                  <p className="text-slate-400 text-sm mb-1">{t('partnerDashboard.totalGanado')}</p>
                  <p className="text-3xl font-bold text-white">
                    ${(commissionsData.total_earned || 0).toFixed(2)}
                  </p>
                </CardContent>
              </Card>
              <Card className="bg-slate-800/50 border-slate-700">
                <CardContent className="p-6">
                  <p className="text-slate-400 text-sm mb-1">{t('partnerDashboard.pagado')}</p>
                  <p className="text-3xl font-bold text-emerald-400">
                    ${(commissionsData.total_paid || 0).toFixed(2)}
                  </p>
                </CardContent>
              </Card>
              <Card className="bg-slate-800/50 border-slate-700">
                <CardContent className="p-6">
                  <p className="text-slate-400 text-sm mb-1">{t('partnerDashboard.pendiente')}</p>
                  <p className="text-3xl font-bold text-amber-400">
                    ${(commissionsData.pending || 0).toFixed(2)}
                  </p>
                </CardContent>
              </Card>
            </div>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">{t('partnerDashboard.historialDeComisiones')}</CardTitle>
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
                          <TableHead className="text-slate-400">{t('partnerDashboard.fecha')}</TableHead>
                          <TableHead className="text-slate-400">{t('partnerDashboard.cliente')}</TableHead>
                          <TableHead className="text-slate-400">{t('partnerDashboard.monto')}</TableHead>
                          <TableHead className="text-slate-400">{t('partnerDashboard.estado')}</TableHead>
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
            {/* Payment Methods */}
            <div className="grid md:grid-cols-2 gap-4">
              {/* Stripe Connect Card */}
              <Card className={`border ${stripeConnectStatus?.connected && stripeConnectStatus?.status === "active" ? "bg-emerald-500/10 border-emerald-500/30" : "bg-slate-800/50 border-slate-700"}`}>
                <CardContent className="p-6">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 bg-purple-500/20 rounded-xl flex items-center justify-center shrink-0">
                      <CreditCard className="w-6 h-6 text-purple-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-white">Stripe Connect</h3>
                      {stripeConnectStatus?.connected && stripeConnectStatus?.status === "active" ? (
                        <>
                          <p className="text-emerald-400 text-sm flex items-center gap-1 mt-1">
                            <ShieldCheck className="w-4 h-4" /> Conectado
                          </p>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={openStripeDashboard}
                            className="mt-3 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20"
                            data-testid="stripe-dashboard-btn"
                          >
                            <ExternalLink className="w-3 h-3 mr-1" /> Ver Dashboard
                          </Button>
                        </>
                      ) : (
                        <>
                          <p className="text-slate-400 text-sm mt-1">
                            Recibe pagos directos a tu cuenta bancaria
                          </p>
                          <Button
                            size="sm"
                            onClick={connectStripeAccount}
                            disabled={connectingStripe}
                            className="mt-3 bg-purple-500 hover:bg-purple-600"
                            data-testid="connect-stripe-btn"
                          >
                            {connectingStripe ? (
                              <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                            ) : (
                              <CreditCard className="w-3 h-3 mr-1" />
                            )}
                            {stripeConnectStatus?.status === "pending" ? "Completar" : "Conectar"}
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* PayPal Card */}
              <Card className={`border ${payoutBalance?.paypal_connected ? "bg-blue-500/10 border-blue-500/30" : "bg-slate-800/50 border-slate-700"}`}>
                <CardContent className="p-6">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 bg-blue-500/20 rounded-xl flex items-center justify-center shrink-0">
                      <Wallet className="w-6 h-6 text-blue-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-white">PayPal</h3>
                      {payoutBalance?.paypal_connected ? (
                        <>
                          <p className="text-blue-400 text-sm flex items-center gap-1 mt-1">
                            <ShieldCheck className="w-4 h-4" /> {payoutBalance.paypal_email}
                          </p>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={handleRemovePaypal}
                            className="mt-3 border-red-500/30 text-red-400 hover:bg-red-500/20"
                            data-testid="remove-paypal-btn"
                          >
                            <X className="w-3 h-3 mr-1" /> Desconectar
                          </Button>
                        </>
                      ) : (
                        <>
                          <p className="text-slate-400 text-sm mt-1">
                            Recibe pagos a tu cuenta de PayPal
                          </p>
                          <div className="flex gap-2 mt-3">
                            <Input
                              type="email"
                              value={paypalEmail}
                              onChange={(e) => setPaypalEmail(e.target.value)}
                              placeholder="tu@paypal.com"
                              className="bg-slate-700 border-slate-600 text-white text-sm h-9"
                              data-testid="paypal-email-input"
                            />
                            <Button
                              size="sm"
                              onClick={handleSavePaypal}
                              disabled={savingPaypal || !paypalEmail}
                              className="bg-blue-500 hover:bg-blue-600 shrink-0"
                              data-testid="save-paypal-btn"
                            >
                              {savingPaypal ? <Loader2 className="w-3 h-3 animate-spin" /> : "Guardar"}
                            </Button>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Balance Cards */}
            <div className="grid md:grid-cols-4 gap-4">
              <Card className="bg-slate-800/50 border-slate-700">
                <CardContent className="p-6">
                  <p className="text-slate-400 text-sm mb-1">{t('partnerDashboard.balanceDisponible')}</p>
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
                  <p className="text-slate-400 text-sm mb-1">{t('partnerDashboard.totalGanado')}</p>
                  <p className="text-3xl font-bold text-white">
                    ${payoutBalance?.total_earned?.toFixed(2) || "0.00"}
                  </p>
                </CardContent>
              </Card>
              <Card className="bg-slate-800/50 border-slate-700">
                <CardContent className="p-6">
                  <p className="text-slate-400 text-sm mb-1">{t('partnerDashboard.totalPagado')}</p>
                  <p className="text-3xl font-bold text-blue-400">
                    ${payoutBalance?.total_paid?.toFixed(2) || "0.00"}
                  </p>
                </CardContent>
              </Card>
              <Card className="bg-slate-800/50 border-slate-700">
                <CardContent className="p-6">
                  <p className="text-slate-400 text-sm mb-1">{t('partnerDashboard.enProceso')}</p>
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
                    <h3 className="text-white font-semibold">{t('partnerDashboard.solicitarRetiro')}</h3>
                    <p className="text-slate-400 text-sm">
                      Retira vía {payoutBalance?.stripe_connected && payoutBalance?.paypal_connected ? "Stripe o PayPal" : payoutBalance?.paypal_connected ? "PayPal" : "Stripe"}. Los pagos se procesan en 2-5 días hábiles.
                    </p>
                  </div>
                  <Button
                    onClick={() => {
                      setPayoutMethod(payoutBalance?.stripe_connected ? "stripe" : "paypal");
                      setShowPayoutModal(true);
                    }}
                    disabled={!payoutBalance?.can_withdraw}
                    className="bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50"
                    data-testid="request-payout-btn"
                  >
                    <Banknote className="w-4 h-4 mr-2" />
                    {payoutBalance?.can_withdraw 
                      ? "Retirar Fondos" 
                      : (payoutBalance?.stripe_connected || payoutBalance?.paypal_connected)
                        ? `Mínimo $${payoutBalance?.minimum_payout || 50}` 
                        : "Configura un método de pago"}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Payout History */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">{t('partnerDashboard.historialDeRetiros')}</CardTitle>
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
                          <TableHead className="text-slate-400">{t('partnerDashboard.fecha')}</TableHead>
                          <TableHead className="text-slate-400">ID</TableHead>
                          <TableHead className="text-slate-400">Método</TableHead>
                          <TableHead className="text-slate-400">{t('partnerDashboard.monto')}</TableHead>
                          <TableHead className="text-slate-400">{t('partnerDashboard.estado')}</TableHead>
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
                            <TableCell>
                              <Badge variant="outline" className={payout.method === "paypal" ? "text-blue-400 border-blue-500/30" : "text-purple-400 border-purple-500/30"}>
                                {payout.method === "paypal" ? "PayPal" : "Stripe"}
                              </Badge>
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

          {/* Brochure Builder Tab */}
          <TabsContent value="brochure-builder" className="space-y-6" data-testid="brochure-builder-tab">
            <BrochureBuilderPanel containerClassName="space-y-6" />
          </TabsContent>
        </Tabs>
      </main>

      {/* Add Client Modal */}
      <AddClientDialog
        open={showAddClient}
        onOpenChange={setShowAddClient}
        newClient={newClient}
        setNewClient={setNewClient}
        addingClient={addingClient}
        onSubmit={handleAddClient}
      />

      {/* Activate Client Dialog */}
      <Dialog open={showActivateClient} onOpenChange={setShowActivateClient}>
        <DialogContent className="bg-slate-800 border-slate-700 max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-white">Activar Cliente</DialogTitle>
            <DialogDescription className="text-slate-400">
              Selecciona un plan y la cantidad de empleados para <span className="text-emerald-400 font-medium">{selectedClient?.company_name}</span>
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6 py-4">
            {/* Plan Selection */}
            <div className="space-y-3">
              <Label className="text-slate-300 font-medium">Plan de Suscripción</Label>
              <div className="grid gap-3">
                {plans.map((plan) => (
                  <div
                    key={plan.plan_id}
                    onClick={() => setActivationData(prev => ({ ...prev, plan_id: plan.plan_id }))}
                    className={`cursor-pointer rounded-lg border p-4 transition-all ${
                      activationData.plan_id === plan.plan_id
                        ? "border-emerald-500 bg-emerald-500/10"
                        : "border-slate-600 bg-slate-700/30 hover:border-slate-500"
                    }`}
                    data-testid={`plan-option-${plan.plan_id}`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="text-white font-semibold">{plan.name}</h4>
                        <p className="text-slate-400 text-sm">${plan.base_price}/mes base + ${plan.price_per_employee}/empleado</p>
                      </div>
                      <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                        activationData.plan_id === plan.plan_id
                          ? "border-emerald-500 bg-emerald-500"
                          : "border-slate-500"
                      }`}>
                        {activationData.plan_id === plan.plan_id && (
                          <Check className="w-3 h-3 text-white" />
                        )}
                      </div>
                    </div>
                    <p className="text-slate-500 text-xs mt-1">
                      Máx. {plan.max_employees >= 9999 ? "ilimitados" : plan.max_employees} empleados
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Employee Count */}
            <div className="space-y-2">
              <Label className="text-slate-300 font-medium">Cantidad de Empleados</Label>
              <Input
                type="number"
                min="1"
                max={plans.find(p => p.plan_id === activationData.plan_id)?.max_employees || 999}
                value={activationData.employee_count}
                onChange={(e) => setActivationData(prev => ({ ...prev, employee_count: Math.max(1, parseInt(e.target.value) || 1) }))}
                className="bg-slate-700 border-slate-600 text-white"
                data-testid="employee-count-input"
              />
            </div>

            {/* Price Preview */}
            <div className="bg-slate-700/50 rounded-lg p-4 space-y-2">
              <div className="flex justify-between text-slate-400 text-sm">
                <span>Base del plan</span>
                <span>${plans.find(p => p.plan_id === activationData.plan_id)?.base_price || 0}</span>
              </div>
              <div className="flex justify-between text-slate-400 text-sm">
                <span>{activationData.employee_count} empleados x ${plans.find(p => p.plan_id === activationData.plan_id)?.price_per_employee || 0}</span>
                <span>${(activationData.employee_count * (plans.find(p => p.plan_id === activationData.plan_id)?.price_per_employee || 0)).toFixed(2)}</span>
              </div>
              <div className="border-t border-slate-600 pt-2 flex justify-between">
                <span className="text-white font-semibold">Total Mensual</span>
                <span className="text-white font-bold text-lg">${calculateMonthly(activationData.plan_id, activationData.employee_count).toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-emerald-400 text-sm font-medium">
                <span>Tu comisión (30%)</span>
                <span>${(calculateMonthly(activationData.plan_id, activationData.employee_count) * 0.3).toFixed(2)}/mes</span>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowActivateClient(false)} className="border-slate-600 text-slate-300">
              Cancelar
            </Button>
            <Button
              onClick={handleActivateClient}
              className="bg-emerald-500 hover:bg-emerald-600"
              disabled={activating}
              data-testid="confirm-activate-btn"
            >
              {activating ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Check className="w-4 h-4 mr-2" />}
              {activating ? "Activando..." : "Activar Cliente"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Subscription Dialog */}
      <Dialog open={showEditSubscription} onOpenChange={setShowEditSubscription}>
        <DialogContent className="bg-slate-800 border-slate-700 max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-white">Editar Suscripción</DialogTitle>
            <DialogDescription className="text-slate-400">
              Modifica el plan o la cantidad de empleados de <span className="text-emerald-400 font-medium">{selectedClient?.company_name}</span>
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6 py-4">
            {/* Plan Selection */}
            <div className="space-y-3">
              <Label className="text-slate-300 font-medium">Plan de Suscripción</Label>
              <div className="grid gap-3">
                {plans.map((plan) => (
                  <div
                    key={plan.plan_id}
                    onClick={() => setActivationData(prev => ({ ...prev, plan_id: plan.plan_id }))}
                    className={`cursor-pointer rounded-lg border p-4 transition-all ${
                      activationData.plan_id === plan.plan_id
                        ? "border-emerald-500 bg-emerald-500/10"
                        : "border-slate-600 bg-slate-700/30 hover:border-slate-500"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="text-white font-semibold">{plan.name}</h4>
                        <p className="text-slate-400 text-sm">${plan.base_price}/mes base + ${plan.price_per_employee}/empleado</p>
                      </div>
                      <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                        activationData.plan_id === plan.plan_id
                          ? "border-emerald-500 bg-emerald-500"
                          : "border-slate-500"
                      }`}>
                        {activationData.plan_id === plan.plan_id && (
                          <Check className="w-3 h-3 text-white" />
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Employee Count */}
            <div className="space-y-2">
              <Label className="text-slate-300 font-medium">Cantidad de Empleados</Label>
              <Input
                type="number"
                min="1"
                max={plans.find(p => p.plan_id === activationData.plan_id)?.max_employees || 999}
                value={activationData.employee_count}
                onChange={(e) => setActivationData(prev => ({ ...prev, employee_count: Math.max(1, parseInt(e.target.value) || 1) }))}
                className="bg-slate-700 border-slate-600 text-white"
                data-testid="edit-employee-count"
              />
            </div>

            {/* Price Preview */}
            <div className="bg-slate-700/50 rounded-lg p-4 space-y-2">
              <div className="flex justify-between">
                <span className="text-white font-semibold">Nuevo Total Mensual</span>
                <span className="text-white font-bold text-lg">${calculateMonthly(activationData.plan_id, activationData.employee_count).toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-emerald-400 text-sm font-medium">
                <span>Tu comisión (30%)</span>
                <span>${(calculateMonthly(activationData.plan_id, activationData.employee_count) * 0.3).toFixed(2)}/mes</span>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditSubscription(false)} className="border-slate-600 text-slate-300">
              Cancelar
            </Button>
            <Button
              onClick={handleUpdateSubscription}
              className="bg-emerald-500 hover:bg-emerald-600"
              disabled={activating}
              data-testid="confirm-edit-sub-btn"
            >
              {activating ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Check className="w-4 h-4 mr-2" />}
              {activating ? "Guardando..." : "Guardar Cambios"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* KPI Drill-Down Dialog */}
      <KPIDrillDownDialog
        drillDown={drillDown}
        setDrillDown={setDrillDown}
        stats={stats}
        clients={clients}
        commissions={commissions}
        commissionsData={commissionsData}
        commissionSummary={commissionSummary}
        pricing={pricing}
        benefits={benefits}
        setActiveTab={setActiveTab}
      />


      {/* Payout Request Modal */}
      <PayoutRequestDialog
        open={showPayoutModal}
        onOpenChange={setShowPayoutModal}
        payoutBalance={payoutBalance}
        payoutMethod={payoutMethod}
        setPayoutMethod={setPayoutMethod}
        payoutAmount={payoutAmount}
        setPayoutAmount={setPayoutAmount}
        requestingPayout={requestingPayout}
        onSubmit={handleRequestPayout}
      />
    </div>
  );
}
