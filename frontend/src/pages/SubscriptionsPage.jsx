import { useState, useEffect, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useSearchParams } from "react-router-dom";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, useSubscription, API } from "@/App";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { 
  Check, X, CreditCard, Users, Building2, Zap, Shield, Clock,
  AlertTriangle, RefreshCw, ArrowUpRight, Crown, Rocket, Globe, Loader2, CheckCircle2,
  FileText, Download, Receipt, Gift, Heart, MessageSquare, XCircle, RotateCcw, History
} from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { toast } from "sonner";
import PaymentMethodDialog from "@/components/PaymentMethodForm";

const PLAN_ICONS = {
  trial: Shield,
  basic: Rocket,
  pro: Zap,
  enterprise: Crown
};

const PLAN_COLORS = {
  trial: "slate",
  basic: "blue",
  pro: "purple",
  enterprise: "amber"
};

export default function SubscriptionsPage() {
  const { t } = useTranslation();
  const { getAuthHeaders } = useAuth();
  const { refreshSubscription } = useSubscription();
  const [searchParams, setSearchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [processingPayment, setProcessingPayment] = useState(false);
  const [checkingPayment, setCheckingPayment] = useState(false);
  const [subscription, setSubscription] = useState(null);
  const [plans, setPlans] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [showChangePlan, setShowChangePlan] = useState(false);
  const [showAdjustEmployees, setShowAdjustEmployees] = useState(false);
  const [showAddUsers, setShowAddUsers] = useState(false);
  const [showPaymentSuccess, setShowPaymentSuccess] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [employeeCount, setEmployeeCount] = useState(5);
  const [additionalUsers, setAdditionalUsers] = useState(0);
  
  // Payment method state
  const [paymentMethod, setPaymentMethod] = useState(null);
  const [loadingPaymentMethod, setLoadingPaymentMethod] = useState(false);
  const [showPaymentMethodDialog, setShowPaymentMethodDialog] = useState(false);
  const [pmHistory, setPmHistory] = useState([]);
  
  // Cancellation flow states
  const [showCancelFlow, setShowCancelFlow] = useState(false);
  const [cancelStep, setCancelStep] = useState(1); // 1: retention offer, 2: survey, 3: confirm
  const [cancellationInfo, setCancellationInfo] = useState(null);
  const [cancelReason, setCancelReason] = useState("");
  const [cancelFeedback, setCancelFeedback] = useState("");
  const [cancelWouldReturn, setCancelWouldReturn] = useState(null);
  const [processingCancel, setProcessingCancel] = useState(false);

  // Fetch payment method
  const fetchPaymentMethod = useCallback(async () => {
    setLoadingPaymentMethod(true);
    try {
      const response = await axios.get(`${API}/payment-method`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setPaymentMethod(response.data);
    } catch (error) {
      console.error("Error fetching payment method:", error);
      setPaymentMethod({ has_payment_method: false, payment_method: null });
    } finally {
      setLoadingPaymentMethod(false);
    }
  }, [getAuthHeaders]);

  // Handle payment method updated from inline form
  const handlePaymentMethodUpdated = (newPm) => {
    setPaymentMethod({ has_payment_method: true, payment_method: newPm });
    fetchPmHistory();
  };

  const fetchPmHistory = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/payment-method/history`, {
        headers: getAuthHeaders(),
        withCredentials: true,
      });
      setPmHistory(res.data || []);
    } catch {
      setPmHistory([]);
    }
  }, [getAuthHeaders]);

  const fetchInvoices = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/invoices`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setInvoices(response.data || []);
    } catch (error) {
      console.error("Error fetching invoices:", error);
    }
  }, [getAuthHeaders]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [subRes, plansRes] = await Promise.all([
        axios.get(`${API}/subscription`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/plans`, { headers: getAuthHeaders(), withCredentials: true })
      ]);
      setSubscription(subRes.data);
      setPlans(plansRes.data);
      setEmployeeCount(subRes.data.employee_count || 1);
      setAdditionalUsers(subRes.data.additional_users || 0);
    } catch (error) {
      console.error("Error fetching subscription:", error);
      toast.error(t('subscriptions.errorLoadingData'));
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  // Poll payment status after returning from Stripe
  const pollPaymentStatus = useCallback(async (sessionId, attempts = 0) => {
    const maxAttempts = 10;
    const pollInterval = 2000;

    if (attempts >= maxAttempts) {
      toast.error(t('subscriptions.paymentVerificationError'));
      setCheckingPayment(false);
      setSearchParams({});
      return;
    }

    setCheckingPayment(true);

    try {
      const response = await axios.get(`${API}/checkout/status/${sessionId}`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });

      if (response.data.payment_status === 'paid') {
        setCheckingPayment(false);
        setShowPaymentSuccess(true);
        toast.success(t('subscriptions.paymentSuccess'));
        // Clear URL params
        setSearchParams({});
        // Refresh subscription data in both local state and global context
        fetchData();
        if (refreshSubscription) {
          refreshSubscription();
        }
        return;
      } else if (response.data.status === 'expired') {
        setCheckingPayment(false);
        toast.error(t('subscriptions.paymentExpired'));
        setSearchParams({});
        return;
      }

      // Continue polling
      setTimeout(() => pollPaymentStatus(sessionId, attempts + 1), pollInterval);
    } catch (error) {
      console.error("Error checking payment status:", error);
      setTimeout(() => pollPaymentStatus(sessionId, attempts + 1), pollInterval);
    }
  }, [getAuthHeaders, fetchData, refreshSubscription, setSearchParams]);

  // Check for payment return from Stripe
  useEffect(() => {
    const sessionId = searchParams.get('session_id');
    const status = searchParams.get('status');
    
    if (sessionId && status === 'success') {
      pollPaymentStatus(sessionId);
    } else if (status === 'cancelled') {
      toast.info(t('subscriptions.paymentCancelled'));
      // Clear URL params
      setSearchParams({});
    }
  }, [searchParams, pollPaymentStatus, setSearchParams]);

  useEffect(() => {
    fetchData();
    fetchInvoices();
    fetchPaymentMethod();
    fetchPmHistory();
  }, [fetchData, fetchInvoices, fetchPaymentMethod, fetchPmHistory]);

  // Handle payment method update callback (legacy redirect flow)
  useEffect(() => {
    if (searchParams.get("payment_method_updated") === "true") {
      toast.success(t('subscriptions.paymentMethodUpdated'));
      fetchPaymentMethod();
      setSearchParams({});
    } else if (searchParams.get("payment_method_cancelled") === "true") {
      setSearchParams({});
    }
  }, [searchParams, setSearchParams, fetchPaymentMethod, t]);

  const handleSelectPlan = async (plan) => {
    if (!plan) return;
    
    setProcessingPayment(true);
    try {
      // Create Stripe checkout session
      const response = await axios.post(`${API}/checkout`, {
        plan_id: plan.plan_id,
        employee_count: employeeCount,
        origin_url: window.location.origin
      }, { headers: getAuthHeaders(), withCredentials: true });
      
      // Redirect to Stripe checkout
      if (response.data.checkout_url) {
        window.location.href = response.data.checkout_url;
      } else {
        toast.error(t('subscriptions.errorProcessingPayment'));
      }
    } catch (error) {
      console.error("Checkout error:", error);
      toast.error(error.response?.data?.detail || t('subscriptions.errorProcessingPayment'));
    } finally {
      setProcessingPayment(false);
    }
  };

  const handleUpdateEmployees = async () => {
    try {
      await axios.put(`${API}/subscription`, {
        employee_count: employeeCount
      }, { headers: getAuthHeaders(), withCredentials: true });
      toast.success(t('subscriptions.employeeCountUpdated'));
      setShowAdjustEmployees(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('subscriptions.errorUpdating'));
    }
  };

  const handleUpdateUsers = async () => {
    try {
      await axios.put(`${API}/subscription`, {
        additional_users: additionalUsers
      }, { headers: getAuthHeaders(), withCredentials: true });
      toast.success(t('subscriptions.additionalUsersUpdated'));
      setShowAddUsers(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('subscriptions.errorUpdating'));
    }
  };

  const handleCancelSubscription = async () => {
    // Open cancellation flow instead of direct cancel
    try {
      const response = await axios.get(`${API}/subscription/cancellation-info`, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      setCancellationInfo(response.data);
      setCancelStep(1);
      setShowCancelFlow(true);
    } catch (error) {
      toast.error(t('subscriptions.errorLoadingCancellationInfo'));
    }
  };

  const handleAcceptRetentionOffer = async () => {
    setProcessingCancel(true);
    try {
      const response = await axios.post(`${API}/subscription/accept-retention-offer`, {}, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success(t('subscriptions.discountApplied', { savings: formatCurrency(response.data.savings_3_months) }));
      setShowCancelFlow(false);
      fetchData();
    } catch (error) {
      toast.error(t('subscriptions.errorApplyingDiscount'));
    } finally {
      setProcessingCancel(false);
    }
  };

  const handleConfirmCancellation = async () => {
    if (!cancelReason) {
      toast.error(t('subscriptions.pleaseSelectReason'));
      return;
    }
    
    setProcessingCancel(true);
    try {
      await axios.post(`${API}/subscription/cancel`, {
        reason: cancelReason,
        feedback: cancelFeedback,
        would_return: cancelWouldReturn
      }, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success(t('subscriptions.subscriptionCancelled'));
      setShowCancelFlow(false);
      setCancelStep(1);
      setCancelReason("");
      setCancelFeedback("");
      fetchData();
    } catch (error) {
      toast.error(t('subscriptions.errorCancellingSubscription'));
    } finally {
      setProcessingCancel(false);
    }
  };

  const handleReactivateSubscription = async () => {
    try {
      await axios.post(`${API}/subscription/reactivate`, {}, {
        headers: getAuthHeaders(),
        withCredentials: true
      });
      toast.success(t('subscriptions.subscriptionReactivated'));
      fetchData();
    } catch (error) {
      toast.error(t('subscriptions.errorReactivatingSubscription'));
    }
  };

  const handleDownloadInvoice = async (invoiceId, invoiceNumber) => {
    try {
      const response = await axios.get(`${API}/invoices/${invoiceId}/pdf`, {
        headers: getAuthHeaders(),
        withCredentials: true,
        responseType: 'blob'
      });
      
      // Create blob and download
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `Factura_${invoiceNumber || invoiceId}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.success(t('subscriptions.invoiceDownloaded'));
    } catch (error) {
      console.error("Error downloading invoice:", error);
      toast.error(t('subscriptions.errorDownloadingInvoice'));
    }
  };

  const formatCurrency = (value) => {
    if (value === null || value === undefined || isNaN(value)) return "$0.00";
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "N/A";
    try {
      const date = new Date(dateStr);
      if (isNaN(date.getTime())) return "N/A";
      return date.toLocaleDateString('es-DO', { day: '2-digit', month: 'short', year: 'numeric' });
    } catch {
      return "N/A";
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      active: "bg-emerald-100 text-emerald-700 dark:text-emerald-400",
      trial: "bg-blue-100 text-blue-700 dark:text-blue-400",
      cancelled: "bg-red-100 text-red-700",
      expired: "bg-red-100 text-red-700"
    };
    const labels = {
      active: "Activo",
      trial: "Prueba Gratuita",
      cancelled: "Cancelado",
      expired: "Vencido"
    };
    return <Badge className={styles[status] || "bg-slate-100 text-slate-700 dark:text-slate-200"}>{labels[status] || status}</Badge>;
  };

  const calculateTotal = (plan, empCount) => {
    if (!plan) return 0;
    const base = plan.base_price || 0;
    const perEmp = plan.price_per_employee || 0;
    return base + (empCount * perEmp);
  };

  if (loading) {
    return (
      <DashboardLayout title={t('subscriptions.title')}>
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      </DashboardLayout>
    );
  }

  const currentPlanId = subscription?.plan_id || "trial";
  const currentPlan = subscription?.plan_details || {};
  const maxEmployees = currentPlan?.max_employees || 1;
  const includedUsers = currentPlan?.included_users || 1;

  return (
    <DashboardLayout title="Suscripción">
      <div className="space-y-6" data-testid="subscriptions-page">
        {/* Alert for trial/expired */}
        {subscription?.status === 'trial' && (
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-center gap-4">
            <Clock className="w-8 h-8 text-blue-500" />
            <div className="flex-1">
              <h3 className="font-semibold text-blue-800">{t('subscriptions.periodoDePrueba')}</h3>
              <p className="text-blue-600 text-sm">
                Te quedan {subscription?.trial_days_remaining || 0} días de prueba. 
                Actualiza a un plan pagado para desbloquear todas las funciones.
              </p>
            </div>
            <Button onClick={() => setShowChangePlan(true)} className="bg-blue-600 hover:bg-blue-700">
              <ArrowUpRight className="w-4 h-4 mr-2" />{t('subscriptions.viewPlans')}
            </Button>
          </div>
        )}

        {subscription?.status === 'expired' && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-4">
            <AlertTriangle className="w-8 h-8 text-red-500" />
            <div className="flex-1">
              <h3 className="font-semibold text-red-800">{t('subscriptions.suscripcionVencida')}</h3>
              <p className="text-red-600 text-sm">{t('subscriptions.tuPeriodoDePrueba')}</p>
            </div>
            <Button onClick={() => setShowChangePlan(true)} className="bg-red-600 hover:bg-red-700">
              <CreditCard className="w-4 h-4 mr-2" />{t('subscriptions.selectPlan')}
            </Button>
          </div>
        )}

        {/* Current Plan Overview */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="lg:col-span-2">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <CreditCard className="w-5 h-5" />
                    {t('subscriptions.currentPlan')}
                  </CardTitle>
                  <CardDescription>{t('subscriptions.detallesDeSuSuscripcion')}</CardDescription>
                </div>
                {getStatusBadge(subscription?.status)}
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex items-start gap-6">
                <div className={`w-16 h-16 rounded-2xl flex items-center justify-center bg-gradient-to-br ${
                  currentPlanId === 'trial' ? 'from-slate-500 to-slate-600' :
                  currentPlanId === 'basic' ? 'from-blue-500 to-blue-600' :
                  currentPlanId === 'pro' ? 'from-purple-500 to-purple-600' :
                  'from-amber-500 to-amber-600'
                }`}>
                  {(() => { 
                    const Icon = PLAN_ICONS[currentPlanId] || Shield; 
                    return <Icon className="w-8 h-8 text-white" />; 
                  })()}
                </div>
                <div className="flex-1">
                  <h2 className="text-2xl font-bold text-slate-800 dark:text-slate-100">
                    {subscription?.plan_name || "Prueba Gratuita"}
                  </h2>
                  <p className="text-slate-500 dark:text-slate-400">
                    {maxEmployees === -1 || maxEmployees === 9999 
                      ? 'Empleados ilimitados' 
                      : `Hasta ${maxEmployees} empleado${maxEmployees > 1 ? 's' : ''}`}
                  </p>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                    <div className="p-3 bg-slate-50 rounded-lg">
                      <p className="text-xs text-slate-500 dark:text-slate-400">{t('subscriptions.baseMensual')}</p>
                      <p className="text-lg font-bold">{formatCurrency(currentPlan?.base_price)}</p>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-lg">
                      <p className="text-xs text-slate-500 dark:text-slate-400">{t('subscriptions.porEmpleado')}</p>
                      <p className="text-lg font-bold">{formatCurrency(currentPlan?.price_per_employee)}</p>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-lg">
                      <p className="text-xs text-slate-500 dark:text-slate-400">{t('subscriptions.empleados')}</p>
                      <p className="text-lg font-bold">{subscription?.current_employees || 0}</p>
                    </div>
                    <div className="p-3 bg-emerald-50 rounded-lg">
                      <p className="text-xs text-emerald-600 dark:text-emerald-400">{t('subscriptions.totalMensual')}</p>
                      <p className="text-lg font-bold text-emerald-700 dark:text-emerald-400">{formatCurrency(subscription?.total_monthly)}</p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex flex-wrap gap-2 border-t pt-4">
              <Button variant="outline" onClick={() => setShowChangePlan(true)}>
                <ArrowUpRight className="w-4 h-4 mr-2" />
                {currentPlanId === 'trial' ? 'Actualizar Plan' : 'Cambiar Plan'}
              </Button>
              {currentPlanId !== 'trial' && (
                <>
                  <Button variant="outline" onClick={() => setShowAdjustEmployees(true)}>
                    <Users className="w-4 h-4 mr-2" />{t('subscriptions.adjustEmployees')}
                  </Button>
                  <Button variant="outline" onClick={() => setShowAddUsers(true)}>
                    <Users className="w-4 h-4 mr-2" />{t('subscriptions.additionalUsers')}
                  </Button>
                  {(subscription?.status === 'active') && (
                    <Button variant="ghost" className="text-red-600 ml-auto" onClick={handleCancelSubscription}>
                      <XCircle className="w-4 h-4 mr-2" />{t('subscriptions.cancelSubscription')}
                    </Button>
                  )}
                  {(subscription?.status === 'canceling' || subscription?.status === 'cancelled') && (
                    <Button variant="outline" className="text-emerald-600 border-emerald-300 ml-auto" onClick={handleReactivateSubscription}>
                      <RotateCcw className="w-4 h-4 mr-2" />{t('subscriptions.reactivateSubscription')}
                    </Button>
                  )}
                </>
              )}
            </CardFooter>
          </Card>

          {/* Usage Summary */}
          <Card>
            <CardHeader>
              <CardTitle>{t('subscriptions.usoActual')}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-500 dark:text-slate-400">{t('subscriptions.empleados')}</span>
                  <span className="font-medium">
                    {subscription?.current_employees || 0} / {maxEmployees === -1 || maxEmployees === 9999 ? '∞' : maxEmployees}
                  </span>
                </div>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-blue-500 rounded-full"
                    style={{ 
                      width: `${maxEmployees === -1 || maxEmployees === 9999 
                        ? 30 
                        : Math.min(100, ((subscription?.current_employees || 0) / maxEmployees) * 100)}%` 
                    }}
                  />
                </div>
              </div>
              
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-500 dark:text-slate-400">{t('subscriptions.usuarios')}</span>
                  <span className="font-medium">
                    {subscription?.current_users || 0} / {includedUsers + (subscription?.additional_users || 0)}
                  </span>
                </div>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-purple-500 rounded-full"
                    style={{ 
                      width: `${Math.min(100, ((subscription?.current_users || 0) / (includedUsers + (subscription?.additional_users || 0))) * 100)}%` 
                    }}
                  />
                </div>
              </div>

              <div className="pt-4 border-t">
                <p className="text-sm text-slate-500 dark:text-slate-400">{t('subscriptions.periodoActual')}</p>
                <p className="font-medium">
                  {formatDate(subscription?.current_period_start)} - {formatDate(subscription?.current_period_end)}
                </p>
              </div>

              {subscription?.status === 'trial' && subscription?.trial_days_remaining !== undefined && (
                <div className="p-3 bg-blue-50 rounded-lg">
                  <p className="text-sm text-blue-700 dark:text-blue-400">
                    <Clock className="w-4 h-4 inline mr-1" />
                    {subscription.trial_days_remaining} días restantes de prueba
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Payment Method Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CreditCard className="w-5 h-5" />
                {t('subscriptions.paymentMethod.title')}
              </CardTitle>
              <CardDescription>{t('subscriptions.paymentMethod.description')}</CardDescription>
            </CardHeader>
            <CardContent>
              {loadingPaymentMethod ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
                </div>
              ) : paymentMethod?.has_payment_method && paymentMethod.payment_method ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-8 bg-gradient-to-br from-slate-700 to-slate-900 rounded flex items-center justify-center text-white text-xs font-bold">
                        {paymentMethod.payment_method.brand}
                      </div>
                      <div>
                        <p className="font-medium">
                          •••• •••• •••• {paymentMethod.payment_method.last4}
                        </p>
                        <p className="text-sm text-slate-500 dark:text-slate-400">
                          {t('subscriptions.paymentMethod.expires')}: {paymentMethod.payment_method.exp_month.toString().padStart(2, '0')}/{paymentMethod.payment_method.exp_year}
                        </p>
                      </div>
                    </div>
                    <Badge className="bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">
                      {t('subscriptions.paymentMethod.active')}
                    </Badge>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                      {t('subscriptions.paymentMethod.autoRenewal')}
                    </p>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowPaymentMethodDialog(true)}
                      data-testid="update-payment-method-btn"
                    >
                      <RefreshCw className="w-4 h-4 mr-2" />
                      {t('subscriptions.paymentMethod.update')}
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="text-center py-6">
                  <CreditCard className="w-12 h-12 mx-auto text-slate-300 mb-3" />
                  <p className="text-slate-500 dark:text-slate-400 mb-4">
                    {t('subscriptions.paymentMethod.noMethod')}
                  </p>
                  <Button
                    onClick={() => setShowPaymentMethodDialog(true)}
                    data-testid="add-payment-method-btn"
                  >
                    <CreditCard className="w-4 h-4 mr-2" />
                    {t('subscriptions.paymentMethod.add')}
                  </Button>
                </div>
              )}
              
              {/* Card expiration warning */}
              {paymentMethod?.has_payment_method && paymentMethod.payment_method && (() => {
                const currentDate = new Date();
                const expMonth = paymentMethod.payment_method.exp_month;
                const expYear = paymentMethod.payment_method.exp_year;
                const isExpiringSoon = (expYear === currentDate.getFullYear() && expMonth <= currentDate.getMonth() + 2) ||
                                       (expYear === currentDate.getFullYear() && expMonth === currentDate.getMonth() + 1);
                const isExpired = (expYear < currentDate.getFullYear()) || 
                                  (expYear === currentDate.getFullYear() && expMonth < currentDate.getMonth() + 1);
                
                if (isExpired) {
                  return (
                    <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                      <div className="flex items-center gap-2 text-red-700 dark:text-red-400">
                        <AlertTriangle className="w-4 h-4" />
                        <span className="text-sm font-medium">{t('subscriptions.paymentMethod.expired')}</span>
                      </div>
                      <p className="text-sm text-red-600 dark:text-red-400 mt-1">
                        {t('subscriptions.paymentMethod.expiredMessage')}
                      </p>
                    </div>
                  );
                } else if (isExpiringSoon) {
                  return (
                    <div className="mt-4 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
                      <div className="flex items-center gap-2 text-amber-700 dark:text-amber-400">
                        <AlertTriangle className="w-4 h-4" />
                        <span className="text-sm font-medium">{t('subscriptions.paymentMethod.expiringSoon')}</span>
                      </div>
                      <p className="text-sm text-amber-600 dark:text-amber-400 mt-1">
                        {t('subscriptions.paymentMethod.expiringSoonMessage')}
                      </p>
                    </div>
                  );
                }
                return null;
              })()}

              {/* Card Change History */}
              {pmHistory.length > 0 && (
                <div className="mt-5 border-t pt-4" data-testid="pm-history-section">
                  <h4 className="text-sm font-semibold flex items-center gap-1.5 mb-3 text-slate-700 dark:text-slate-200">
                    <History className="w-4 h-4" />
                    {t('subscriptions.paymentMethod.history.title')}
                  </h4>
                  <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                    {pmHistory.map((entry, idx) => (
                      <div
                        key={idx}
                        className="flex items-center gap-3 text-xs p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800"
                        data-testid={`pm-history-entry-${idx}`}
                      >
                        <div className="flex-shrink-0 w-2 h-2 rounded-full bg-blue-500" />
                        <div className="flex-1 min-w-0">
                          {entry.change_type === 'added' ? (
                            <span className="text-slate-600 dark:text-slate-300">
                              {t('subscriptions.paymentMethod.history.added', {
                                brand: entry.new_card?.brand,
                                last4: entry.new_card?.last4,
                              })}
                            </span>
                          ) : (
                            <span className="text-slate-600 dark:text-slate-300">
                              <span className="text-slate-400 line-through">
                                {entry.previous_card?.brand} ••{entry.previous_card?.last4}
                              </span>
                              {' → '}
                              <span className="font-medium text-slate-700 dark:text-slate-200">
                                {entry.new_card?.brand} ••{entry.new_card?.last4}
                              </span>
                            </span>
                          )}
                        </div>
                        <span className="flex-shrink-0 text-slate-400">
                          {formatDate(entry.changed_at)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Plan Comparison */}
        <Card>
          <CardHeader>
            <CardTitle>{t('subscriptions.planComparison')}</CardTitle>
            <CardDescription>{t('subscriptions.findPerfectPlan')}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {plans.map(plan => {
                const Icon = PLAN_ICONS[plan.plan_id] || Rocket;
                const isCurrentPlan = currentPlanId === plan.plan_id;
                const colorClass = PLAN_COLORS[plan.plan_id] || 'blue';
                
                return (
                  <div 
                    key={plan.plan_id}
                    className={`relative rounded-xl border-2 p-6 transition-all ${
                      isCurrentPlan ? 'border-emerald-500 bg-emerald-50' : 'border-slate-200 hover:border-slate-300 hover:shadow-md'
                    }`}
                  >
                    {isCurrentPlan && (
                      <Badge className="absolute -top-3 left-1/2 -translate-x-1/2 bg-emerald-500">{t('subscriptions.currentPlan')}</Badge>
                    )}
                    {plan.plan_id === 'pro' && !isCurrentPlan && (
                      <Badge className="absolute -top-3 left-1/2 -translate-x-1/2 bg-purple-500">{t('subscriptions.mostPopular')}</Badge>
                    )}
                    
                    <div className="text-center mb-4">
                      <div className={`w-14 h-14 mx-auto rounded-xl flex items-center justify-center bg-gradient-to-br ${
                        colorClass === 'blue' ? 'from-blue-500 to-blue-600' :
                        colorClass === 'purple' ? 'from-purple-500 to-purple-600' :
                        'from-amber-500 to-amber-600'
                      } text-white mb-3`}>
                        <Icon className="w-7 h-7" />
                      </div>
                      <h3 className="text-xl font-bold">{plan.name}</h3>
                      <div className="mt-2">
                        <span className="text-3xl font-bold">{formatCurrency(plan.base_price)}</span>
                        <span className="text-slate-500 dark:text-slate-400">/mes</span>
                      </div>
                      <p className="text-sm text-slate-500 dark:text-slate-400">+ {formatCurrency(plan.price_per_employee)}/{t('common.employee')}</p>
                    </div>

                    <div className="space-y-2 mb-6">
                      <p className="text-sm font-medium text-slate-700 dark:text-slate-200">
                        {plan.max_employees === -1 || plan.max_employees === 9999 
                          ? 'Empleados ilimitados' 
                          : `Hasta ${plan.max_employees} empleados`}
                      </p>
                      <p className="text-sm text-slate-500 dark:text-slate-400">{plan.included_users} usuarios incluidos</p>
                    </div>

                    <div className="space-y-2 mb-6 max-h-48 overflow-y-auto">
                      {(plan.features || []).slice(0, 8).map((feature, idx) => (
                        <div key={idx} className="flex items-start gap-2 text-sm">
                          <Check className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                          <span className="text-slate-600 dark:text-slate-300">{feature}</span>
                        </div>
                      ))}
                      {(plan.features || []).length > 8 && (
                        <p className="text-xs text-slate-400">+ {plan.features.length - 8} más...</p>
                      )}
                    </div>

                    <Button 
                      className={`w-full ${isCurrentPlan ? 'bg-slate-400 cursor-not-allowed' : ''}`}
                      disabled={isCurrentPlan || processingPayment}
                      onClick={() => {
                        setSelectedPlan(plan);
                        setShowChangePlan(true);
                      }}
                    >
                      {isCurrentPlan ? t('subscriptions.currentPlan') : t('subscriptions.select')}
                    </Button>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Invoice History */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Receipt className="w-5 h-5" />
                  {t('subscriptions.invoiceHistory.title')}
                </CardTitle>
                <CardDescription>{t('subscriptions.invoiceHistory.description')}</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {invoices.length === 0 ? (
              <div className="text-center py-8 text-slate-500 dark:text-slate-400">
                <FileText className="w-12 h-12 mx-auto text-slate-300 mb-3" />
                <p>{t('subscriptions.invoiceHistory.noInvoices')}</p>
                <p className="text-sm">{t('subscriptions.invoiceHistory.invoicesWillAppear')}</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{t('subscriptions.invoiceHistory.invoice')}</TableHead>
                    <TableHead>{t('subscriptions.invoiceHistory.date')}</TableHead>
                    <TableHead>{t('subscriptions.invoiceHistory.plan')}</TableHead>
                    <TableHead>{t('subscriptions.invoiceHistory.employees')}</TableHead>
                    <TableHead className="text-right">{t('subscriptions.invoiceHistory.total')}</TableHead>
                    <TableHead>{t('subscriptions.invoiceHistory.status')}</TableHead>
                    <TableHead className="text-center">{t('subscriptions.invoiceHistory.actions')}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {invoices.map((invoice) => (
                    <TableRow key={invoice.invoice_id}>
                      <TableCell className="font-medium">{invoice.invoice_number}</TableCell>
                      <TableCell>{invoice.paid_at || formatDate(invoice.created_at)}</TableCell>
                      <TableCell>{invoice.plan_name}</TableCell>
                      <TableCell>{invoice.employee_count}</TableCell>
                      <TableCell className="text-right font-semibold text-emerald-600 dark:text-emerald-400">
                        {formatCurrency(invoice.total)}
                      </TableCell>
                      <TableCell>
                        <Badge className={invoice.status === 'paid' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}>
                          {invoice.status === 'paid' ? t('subscriptions.paid') : t('subscriptions.pending')}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-center">
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => handleDownloadInvoice(invoice.invoice_id, invoice.invoice_number)}
                          data-testid={`download-invoice-${invoice.invoice_id}`}
                        >
                          <Download className="w-4 h-4 mr-1" />
                          PDF
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* Change Plan Dialog - Shows all plans */}
        <Dialog open={showChangePlan} onOpenChange={setShowChangePlan}>
          <DialogContent className="max-w-3xl">
            <DialogHeader>
              <DialogTitle>{t('subscriptions.seleccionarPlan')}</DialogTitle>
              <DialogDescription>
                Elige el plan que mejor se adapte a tu empresa
              </DialogDescription>
            </DialogHeader>
            
            <div className="py-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {plans.map(plan => {
                  const isSelected = selectedPlan?.plan_id === plan.plan_id;
                  const isCurrentPlan = currentPlanId === plan.plan_id;
                  const Icon = PLAN_ICONS[plan.plan_id] || Rocket;
                  
                  return (
                    <div 
                      key={plan.plan_id}
                      onClick={() => !isCurrentPlan && setSelectedPlan(plan)}
                      className={`relative p-4 rounded-xl border-2 cursor-pointer transition-all ${
                        isSelected ? 'border-blue-500 bg-blue-50' : 
                        isCurrentPlan ? 'border-slate-300 bg-slate-100 cursor-not-allowed opacity-60' :
                        'border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      {isCurrentPlan && (
                        <Badge className="absolute -top-2 right-2 bg-slate-500 text-xs">{t('subscriptions.actual')}</Badge>
                      )}
                      
                      <div className="text-center">
                        <Icon className={`w-8 h-8 mx-auto mb-2 ${
                          plan.plan_id === 'basic' ? 'text-blue-500' :
                          plan.plan_id === 'pro' ? 'text-purple-500' :
                          'text-amber-500'
                        }`} />
                        <h4 className="font-bold">{plan.name}</h4>
                        <p className="text-2xl font-bold mt-1">{formatCurrency(plan.base_price)}<span className="text-sm font-normal text-slate-500 dark:text-slate-400">/mes</span></p>
                        <p className="text-xs text-slate-500 dark:text-slate-400">+ {formatCurrency(plan.price_per_employee)}/empleado</p>
                        <p className="text-xs text-slate-400 mt-2">
                          {plan.max_employees === 9999 ? 'Ilimitados' : `Hasta ${plan.max_employees}`} empleados
                        </p>
                      </div>
                      
                      {isSelected && (
                        <div className="absolute top-2 right-2">
                          <Check className="w-5 h-5 text-blue-500" />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
              
              {selectedPlan && (
                <div className="mt-6 p-4 bg-slate-50 rounded-xl">
                  <h4 className="font-semibold mb-3">{t('subscriptions.resumenDelCambio')}</h4>
                  
                  <div className="mb-4">
                    <Label>{t('subscriptions.cantidadDeEmpleados')}</Label>
                    <div className="flex items-center gap-4 mt-2">
                      <Input 
                        type="number" 
                        value={employeeCount}
                        onChange={(e) => setEmployeeCount(Math.max(1, parseInt(e.target.value) || 1))}
                        min={1}
                        max={selectedPlan.max_employees === 9999 ? 1000 : selectedPlan.max_employees}
                        className="w-24"
                      />
                      <Slider
                        value={[employeeCount]}
                        onValueChange={(v) => setEmployeeCount(v[0])}
                        min={1}
                        max={selectedPlan.max_employees === 9999 ? 100 : selectedPlan.max_employees}
                        step={1}
                        className="flex-1"
                      />
                    </div>
                  </div>
                  
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>{t('subscriptions.planBase', {name: selectedPlan.name})}</span>
                      <span>{formatCurrency(selectedPlan.base_price)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>{employeeCount} {t('subscriptions.employeesX')} {formatCurrency(selectedPlan.price_per_employee)}</span>
                      <span>{formatCurrency(employeeCount * selectedPlan.price_per_employee)}</span>
                    </div>
                    <div className="flex justify-between font-bold text-lg border-t pt-2 mt-2">
                      <span>{t('subscriptions.totalMensual')}</span>
                      <span className="text-emerald-600 dark:text-emerald-400">{formatCurrency(calculateTotal(selectedPlan, employeeCount))}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => {
                setShowChangePlan(false);
                setSelectedPlan(null);
              }}>
                Cancelar
              </Button>
              <Button 
                onClick={() => handleSelectPlan(selectedPlan)} 
                disabled={!selectedPlan || processingPayment}
                className="bg-emerald-600 hover:bg-emerald-700"
              >
                {processingPayment ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Procesando...
                  </>
                ) : (
                  <>
                    <CreditCard className="w-4 h-4 mr-2" />
                    Pagar {selectedPlan ? formatCurrency(calculateTotal(selectedPlan, employeeCount)) : ''}
                  </>
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Adjust Employees Dialog */}
        <Dialog open={showAdjustEmployees} onOpenChange={setShowAdjustEmployees}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{t('subscriptions.ajustarCantidadDeEmpleados')}</DialogTitle>
              <DialogDescription>
                Modifique la cantidad de empleados incluidos en su plan
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4 py-4">
              <div>
                <Label>{t('subscriptions.employeeCount', {count: employeeCount})}</Label>
                <Slider
                  value={[employeeCount]}
                  onValueChange={(v) => setEmployeeCount(v[0])}
                  min={1}
                  max={maxEmployees === -1 || maxEmployees === 9999 ? 500 : maxEmployees}
                  step={1}
                  className="mt-2"
                />
              </div>
              
              <div className="p-4 bg-slate-50 rounded-lg">
                <div className="flex justify-between">
                  <span>{t('subscriptions.baseDelPlan')}</span>
                  <span>{formatCurrency(currentPlan?.base_price)}</span>
                </div>
                <div className="flex justify-between">
                  <span>{employeeCount} {t('subscriptions.employeesX')} {formatCurrency(currentPlan?.price_per_employee)}</span>
                  <span>{formatCurrency(employeeCount * (currentPlan?.price_per_employee || 0))}</span>
                </div>
                <div className="flex justify-between font-bold border-t mt-2 pt-2">
                  <span>{t('subscriptions.totalMensual')}</span>
                  <span>{formatCurrency((currentPlan?.base_price || 0) + (employeeCount * (currentPlan?.price_per_employee || 0)))}</span>
                </div>
              </div>
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowAdjustEmployees(false)}>{t('subscriptions.cancelar')}</Button>
              <Button onClick={handleUpdateEmployees}>{t('subscriptions.confirmarCambio')}</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Add Users Dialog */}
        <Dialog open={showAddUsers} onOpenChange={setShowAddUsers}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{t('subscriptions.usuariosAdicionales')}</DialogTitle>
              <DialogDescription>
                Agregue usuarios adicionales a su suscripción ($2.50/{t('subscriptions.perMonth')})
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4 py-4">
              <div>
                <Label>{t('subscriptions.additionalUsersCount', {count: additionalUsers})}</Label>
                <Slider
                  value={[additionalUsers]}
                  onValueChange={(v) => setAdditionalUsers(v[0])}
                  min={0}
                  max={20}
                  step={1}
                  className="mt-2"
                />
              </div>
              
              <div className="p-4 bg-slate-50 rounded-lg">
                <div className="flex justify-between">
                  <span>{t('subscriptions.usuariosIncluidos')}</span>
                  <span>{includedUsers}</span>
                </div>
                <div className="flex justify-between">
                  <span>{t('subscriptions.usuariosAdicionales1')}</span>
                  <span>{additionalUsers} × $2.50 = {formatCurrency(additionalUsers * 2.50)}</span>
                </div>
                <div className="flex justify-between font-bold border-t mt-2 pt-2">
                  <span>{t('subscriptions.totalUsuarios')}</span>
                  <span>{includedUsers + additionalUsers}</span>
                </div>
              </div>
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowAddUsers(false)}>{t('subscriptions.cancelar')}</Button>
              <Button onClick={handleUpdateUsers}>{t('subscriptions.confirmar')}</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Payment Success Dialog */}
        <Dialog open={showPaymentSuccess} onOpenChange={setShowPaymentSuccess}>
          <DialogContent className="sm:max-w-md">
            <div className="text-center py-6">
              <div className="w-16 h-16 mx-auto rounded-full bg-emerald-100 flex items-center justify-center mb-4">
                <CheckCircle2 className="w-10 h-10 text-emerald-600 dark:text-emerald-400" />
              </div>
              <h2 className="text-2xl font-bold text-slate-900 mb-2">{t('subscriptions.pagoExitoso')}</h2>
              <p className="text-slate-600 mb-6">
                Su suscripción ha sido activada correctamente. Ahora tiene acceso a todas las funciones de su plan.
              </p>
              <Button 
                className="w-full bg-emerald-600 hover:bg-emerald-700"
                onClick={() => setShowPaymentSuccess(false)}
              >
                Continuar
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* Checking Payment Modal */}
        <Dialog open={checkingPayment} onOpenChange={() => {}}>
          <DialogContent className="sm:max-w-md">
            <div className="text-center py-6">
              <Loader2 className="w-12 h-12 mx-auto text-blue-500 animate-spin mb-4" />
              <h2 className="text-xl font-bold text-slate-900 mb-2">{t('subscriptions.verificandoPago')}</h2>
              <p className="text-slate-600 dark:text-slate-300">
                Por favor espere mientras confirmamos su pago...
              </p>
            </div>
          </DialogContent>
        </Dialog>

        {/* Cancellation Flow Dialog */}
        <Dialog open={showCancelFlow} onOpenChange={(open) => {
          if (!open) {
            setShowCancelFlow(false);
            setCancelStep(1);
            setCancelReason("");
            setCancelFeedback("");
          }
        }}>
          <DialogContent className="max-w-lg">
            {/* Step 1: Retention Offer */}
            {cancelStep === 1 && cancellationInfo && (
              <>
                <DialogHeader>
                  <DialogTitle className="flex items-center gap-2">
                    <Heart className="w-5 h-5 text-red-500" />
                    ¡Espera! Tenemos una oferta para ti
                  </DialogTitle>
                </DialogHeader>
                
                <div className="py-4 space-y-4">
                  <div className="bg-gradient-to-br from-emerald-50 to-blue-50 rounded-xl p-6 border border-emerald-200">
                    <div className="text-center">
                      <Gift className="w-12 h-12 mx-auto text-emerald-500 mb-3" />
                      <h3 className="text-xl font-bold text-emerald-800">
                        {cancellationInfo.retention_offer?.discount_percent}% de Descuento
                      </h3>
                      <p className="text-emerald-600 dark:text-emerald-400">por {cancellationInfo.retention_offer?.duration_months} meses</p>
                    </div>
                    
                    <div className="mt-4 space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-600 dark:text-slate-300">{t('subscriptions.precioActual')}</span>
                        <span className="line-through text-slate-400">{formatCurrency(cancellationInfo.current_plan?.monthly_cost)}/mes</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600 dark:text-slate-300">{t('subscriptions.nuevoPrecio')}</span>
                        <span className="font-bold text-emerald-600 dark:text-emerald-400">{formatCurrency(cancellationInfo.retention_offer?.discounted_monthly)}/mes</span>
                      </div>
                      <div className="flex justify-between pt-2 border-t">
                        <span className="font-medium">{t('subscriptions.ahorrasEn3Meses')}</span>
                        <span className="font-bold text-emerald-600 dark:text-emerald-400">{formatCurrency(cancellationInfo.retention_offer?.savings_total)}</span>
                      </div>
                    </div>
                  </div>
                  
                  <p className="text-sm text-slate-500 text-center">
                    Quédate con nosotros y aprovecha este descuento exclusivo
                  </p>
                </div>
                
                <DialogFooter className="flex-col gap-2 sm:flex-col">
                  <Button 
                    className="w-full bg-emerald-600 hover:bg-emerald-700" 
                    onClick={handleAcceptRetentionOffer}
                    disabled={processingCancel}
                  >
                    {processingCancel ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Gift className="w-4 h-4 mr-2" />}
                    Aceptar Descuento
                  </Button>
                  <Button 
                    variant="ghost" 
                    className="w-full text-slate-500 dark:text-slate-400"
                    onClick={() => setCancelStep(2)}
                  >
                    No gracias, continuar con la cancelación
                  </Button>
                </DialogFooter>
              </>
            )}

            {/* Step 2: Survey */}
            {cancelStep === 2 && cancellationInfo && (
              <>
                <DialogHeader>
                  <DialogTitle className="flex items-center gap-2">
                    <MessageSquare className="w-5 h-5 text-blue-500" />
                    ¿Por qué te vas?
                  </DialogTitle>
                  <DialogDescription>
                    Tu opinión nos ayuda a mejorar
                  </DialogDescription>
                </DialogHeader>
                
                <div className="py-4 space-y-4">
                  <div>
                    <Label className="text-sm font-medium">{t('subscriptions.motivoDeCancelacion')}</Label>
                    <RadioGroup value={cancelReason} onValueChange={setCancelReason} className="mt-2 space-y-2">
                      {(cancellationInfo.cancellation_reasons || []).map(reason => (
                        <div key={reason.id} className="flex items-center space-x-2">
                          <RadioGroupItem value={reason.id} id={reason.id} />
                          <Label htmlFor={reason.id} className="cursor-pointer">{reason.label}</Label>
                        </div>
                      ))}
                    </RadioGroup>
                  </div>
                  
                  <div>
                    <Label className="text-sm font-medium">{t('subscriptions.comentariosAdicionalesOpcional')}</Label>
                    <Textarea 
                      placeholder="Cuéntanos más sobre tu experiencia..."
                      value={cancelFeedback}
                      onChange={(e) => setCancelFeedback(e.target.value)}
                      className="mt-2"
                      rows={3}
                    />
                  </div>
                  
                  <div>
                    <Label className="text-sm font-medium">{t('subscriptions.considerariasVolverEnEl')}</Label>
                    <div className="flex gap-4 mt-2">
                      <Button 
                        type="button"
                        variant={cancelWouldReturn === true ? "default" : "outline"}
                        size="sm"
                        onClick={() => setCancelWouldReturn(true)}
                      >
                        Sí, posiblemente
                      </Button>
                      <Button 
                        type="button"
                        variant={cancelWouldReturn === false ? "default" : "outline"}
                        size="sm"
                        onClick={() => setCancelWouldReturn(false)}
                      >
                        No lo creo
                      </Button>
                    </div>
                  </div>
                </div>
                
                <DialogFooter>
                  <Button variant="outline" onClick={() => setCancelStep(1)}>
                    Volver
                  </Button>
                  <Button 
                    variant="destructive"
                    onClick={() => setCancelStep(3)}
                    disabled={!cancelReason}
                  >
                    Continuar
                  </Button>
                </DialogFooter>
              </>
            )}

            {/* Step 3: Confirm */}
            {cancelStep === 3 && (
              <>
                <DialogHeader>
                  <DialogTitle className="flex items-center gap-2 text-red-600 dark:text-red-400">
                    <AlertTriangle className="w-5 h-5" />
                    Confirmar Cancelación
                  </DialogTitle>
                </DialogHeader>
                
                <div className="py-4 space-y-4">
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <h4 className="font-medium text-red-800 mb-2">{t('subscriptions.alCancelarPerderasAcceso')}</h4>
                    <ul className="text-sm text-red-700 space-y-1">
                      <li>• Procesamiento de nóminas</li>
                      <li>• Gestión de empleados</li>
                      <li>• Reportes DGII-TSS</li>
                      <li>• Todas las funciones del sistema</li>
                    </ul>
                  </div>
                  
                  <div className="bg-slate-50 rounded-lg p-4">
                    <p className="text-sm text-slate-600 dark:text-slate-300">
                      <strong>{t('subscriptions.nota')}</strong> Tendrás acceso hasta el final de tu período de facturación actual. 
                      Tus datos se mantendrán guardados por 30 días por si decides volver.
                    </p>
                  </div>
                </div>
                
                <DialogFooter>
                  <Button variant="outline" onClick={() => setCancelStep(2)}>
                    Volver
                  </Button>
                  <Button 
                    variant="destructive"
                    onClick={handleConfirmCancellation}
                    disabled={processingCancel}
                  >
                    {processingCancel ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <XCircle className="w-4 h-4 mr-2" />}
                    Confirmar Cancelación
                  </Button>
                </DialogFooter>
              </>
            )}
          </DialogContent>
        </Dialog>

        {/* Payment Method Dialog (Stripe Elements) */}
        <PaymentMethodDialog
          open={showPaymentMethodDialog}
          onOpenChange={setShowPaymentMethodDialog}
          onSuccess={handlePaymentMethodUpdated}
        />
      </div>
    </DashboardLayout>
  );
}
