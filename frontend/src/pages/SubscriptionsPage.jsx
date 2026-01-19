import { useState, useEffect } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
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
  Check, X, CreditCard, Users, Building2, Zap, Shield, Clock,
  AlertTriangle, RefreshCw, ArrowUpRight, Crown, Rocket, Globe, Loader2
} from "lucide-react";
import { toast } from "sonner";

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
  const { getAuthHeaders } = useAuth();
  const [loading, setLoading] = useState(true);
  const [processingPayment, setProcessingPayment] = useState(false);
  const [subscription, setSubscription] = useState(null);
  const [plans, setPlans] = useState([]);
  const [showChangePlan, setShowChangePlan] = useState(false);
  const [showAdjustEmployees, setShowAdjustEmployees] = useState(false);
  const [showAddUsers, setShowAddUsers] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [employeeCount, setEmployeeCount] = useState(5);
  const [additionalUsers, setAdditionalUsers] = useState(0);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
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
      toast.error("Error al cargar datos de suscripción");
    } finally {
      setLoading(false);
    }
  };

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
        toast.error("Error al procesar el pago");
      }
    } catch (error) {
      console.error("Checkout error:", error);
      toast.error(error.response?.data?.detail || "Error al procesar el pago");
    } finally {
      setProcessingPayment(false);
    }
  };

  const handleUpdateEmployees = async () => {
    try {
      await axios.put(`${API}/subscription`, {
        employee_count: employeeCount
      }, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Cantidad de empleados actualizada");
      setShowAdjustEmployees(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al actualizar");
    }
  };

  const handleUpdateUsers = async () => {
    try {
      await axios.put(`${API}/subscription`, {
        additional_users: additionalUsers
      }, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Usuarios adicionales actualizados");
      setShowAddUsers(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al actualizar");
    }
  };

  const handleCancelSubscription = async () => {
    if (!window.confirm("¿Está seguro de cancelar su suscripción? Perderá acceso al sistema al final del período actual.")) return;
    
    try {
      await axios.put(`${API}/subscription`, {
        action: "cancel"
      }, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Suscripción cancelada");
      fetchData();
    } catch (error) {
      toast.error("Error al cancelar");
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
      active: "bg-emerald-100 text-emerald-700",
      trial: "bg-blue-100 text-blue-700",
      cancelled: "bg-red-100 text-red-700",
      expired: "bg-red-100 text-red-700"
    };
    const labels = {
      active: "Activo",
      trial: "Prueba Gratuita",
      cancelled: "Cancelado",
      expired: "Vencido"
    };
    return <Badge className={styles[status] || "bg-slate-100 text-slate-700"}>{labels[status] || status}</Badge>;
  };

  const calculateTotal = (plan, empCount) => {
    if (!plan) return 0;
    const base = plan.base_price || 0;
    const perEmp = plan.price_per_employee || 0;
    return base + (empCount * perEmp);
  };

  if (loading) {
    return (
      <DashboardLayout title="Suscripción">
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
              <h3 className="font-semibold text-blue-800">Período de Prueba</h3>
              <p className="text-blue-600 text-sm">
                Te quedan {subscription?.trial_days_remaining || 0} días de prueba. 
                Actualiza a un plan pagado para desbloquear todas las funciones.
              </p>
            </div>
            <Button onClick={() => setShowChangePlan(true)} className="bg-blue-600 hover:bg-blue-700">
              <ArrowUpRight className="w-4 h-4 mr-2" />Ver Planes
            </Button>
          </div>
        )}

        {subscription?.status === 'expired' && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-4">
            <AlertTriangle className="w-8 h-8 text-red-500" />
            <div className="flex-1">
              <h3 className="font-semibold text-red-800">Suscripción Vencida</h3>
              <p className="text-red-600 text-sm">Tu período de prueba ha terminado. Selecciona un plan para continuar usando el sistema.</p>
            </div>
            <Button onClick={() => setShowChangePlan(true)} className="bg-red-600 hover:bg-red-700">
              <CreditCard className="w-4 h-4 mr-2" />Seleccionar Plan
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
                    Plan Actual
                  </CardTitle>
                  <CardDescription>Detalles de su suscripción</CardDescription>
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
                  <h2 className="text-2xl font-bold text-slate-800">
                    {subscription?.plan_name || "Prueba Gratuita"}
                  </h2>
                  <p className="text-slate-500">
                    {maxEmployees === -1 || maxEmployees === 9999 
                      ? 'Empleados ilimitados' 
                      : `Hasta ${maxEmployees} empleado${maxEmployees > 1 ? 's' : ''}`}
                  </p>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                    <div className="p-3 bg-slate-50 rounded-lg">
                      <p className="text-xs text-slate-500">Base mensual</p>
                      <p className="text-lg font-bold">{formatCurrency(currentPlan?.base_price)}</p>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-lg">
                      <p className="text-xs text-slate-500">Por empleado</p>
                      <p className="text-lg font-bold">{formatCurrency(currentPlan?.price_per_employee)}</p>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-lg">
                      <p className="text-xs text-slate-500">Empleados</p>
                      <p className="text-lg font-bold">{subscription?.current_employees || 0}</p>
                    </div>
                    <div className="p-3 bg-emerald-50 rounded-lg">
                      <p className="text-xs text-emerald-600">Total mensual</p>
                      <p className="text-lg font-bold text-emerald-700">{formatCurrency(subscription?.total_monthly)}</p>
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
                    <Users className="w-4 h-4 mr-2" />Ajustar Empleados
                  </Button>
                  <Button variant="outline" onClick={() => setShowAddUsers(true)}>
                    <Users className="w-4 h-4 mr-2" />Usuarios Adicionales
                  </Button>
                  {subscription?.status === 'active' && (
                    <Button variant="ghost" className="text-red-600 ml-auto" onClick={handleCancelSubscription}>
                      <X className="w-4 h-4 mr-2" />Cancelar
                    </Button>
                  )}
                </>
              )}
            </CardFooter>
          </Card>

          {/* Usage Summary */}
          <Card>
            <CardHeader>
              <CardTitle>Uso Actual</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-500">Empleados</span>
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
                  <span className="text-slate-500">Usuarios</span>
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
                <p className="text-sm text-slate-500">Período actual</p>
                <p className="font-medium">
                  {formatDate(subscription?.current_period_start)} - {formatDate(subscription?.current_period_end)}
                </p>
              </div>

              {subscription?.status === 'trial' && subscription?.trial_days_remaining !== undefined && (
                <div className="p-3 bg-blue-50 rounded-lg">
                  <p className="text-sm text-blue-700">
                    <Clock className="w-4 h-4 inline mr-1" />
                    {subscription.trial_days_remaining} días restantes de prueba
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Plan Comparison */}
        <Card>
          <CardHeader>
            <CardTitle>Comparación de Planes</CardTitle>
            <CardDescription>Encuentra el plan perfecto para tu empresa</CardDescription>
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
                      <Badge className="absolute -top-3 left-1/2 -translate-x-1/2 bg-emerald-500">Plan Actual</Badge>
                    )}
                    {plan.plan_id === 'pro' && !isCurrentPlan && (
                      <Badge className="absolute -top-3 left-1/2 -translate-x-1/2 bg-purple-500">Más Popular</Badge>
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
                        <span className="text-slate-500">/mes</span>
                      </div>
                      <p className="text-sm text-slate-500">+ {formatCurrency(plan.price_per_employee)}/empleado</p>
                    </div>

                    <div className="space-y-2 mb-6">
                      <p className="text-sm font-medium text-slate-700">
                        {plan.max_employees === -1 || plan.max_employees === 9999 
                          ? 'Empleados ilimitados' 
                          : `Hasta ${plan.max_employees} empleados`}
                      </p>
                      <p className="text-sm text-slate-500">{plan.included_users} usuarios incluidos</p>
                    </div>

                    <div className="space-y-2 mb-6 max-h-48 overflow-y-auto">
                      {(plan.features || []).slice(0, 8).map((feature, idx) => (
                        <div key={idx} className="flex items-start gap-2 text-sm">
                          <Check className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                          <span className="text-slate-600">{feature}</span>
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
                      {isCurrentPlan ? 'Plan Actual' : 'Seleccionar'}
                    </Button>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Change Plan Dialog - Shows all plans */}
        <Dialog open={showChangePlan} onOpenChange={setShowChangePlan}>
          <DialogContent className="max-w-3xl">
            <DialogHeader>
              <DialogTitle>Seleccionar Plan</DialogTitle>
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
                        <Badge className="absolute -top-2 right-2 bg-slate-500 text-xs">Actual</Badge>
                      )}
                      
                      <div className="text-center">
                        <Icon className={`w-8 h-8 mx-auto mb-2 ${
                          plan.plan_id === 'basic' ? 'text-blue-500' :
                          plan.plan_id === 'pro' ? 'text-purple-500' :
                          'text-amber-500'
                        }`} />
                        <h4 className="font-bold">{plan.name}</h4>
                        <p className="text-2xl font-bold mt-1">{formatCurrency(plan.base_price)}<span className="text-sm font-normal text-slate-500">/mes</span></p>
                        <p className="text-xs text-slate-500">+ {formatCurrency(plan.price_per_employee)}/empleado</p>
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
                  <h4 className="font-semibold mb-3">Resumen del cambio</h4>
                  
                  <div className="mb-4">
                    <Label>Cantidad de empleados</Label>
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
                      <span>Base del plan ({selectedPlan.name})</span>
                      <span>{formatCurrency(selectedPlan.base_price)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>{employeeCount} empleados × {formatCurrency(selectedPlan.price_per_employee)}</span>
                      <span>{formatCurrency(employeeCount * selectedPlan.price_per_employee)}</span>
                    </div>
                    <div className="flex justify-between font-bold text-lg border-t pt-2 mt-2">
                      <span>Total mensual</span>
                      <span className="text-emerald-600">{formatCurrency(calculateTotal(selectedPlan, employeeCount))}</span>
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
              <DialogTitle>Ajustar Cantidad de Empleados</DialogTitle>
              <DialogDescription>
                Modifique la cantidad de empleados incluidos en su plan
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4 py-4">
              <div>
                <Label>Cantidad de empleados: {employeeCount}</Label>
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
                  <span>Base del plan</span>
                  <span>{formatCurrency(currentPlan?.base_price)}</span>
                </div>
                <div className="flex justify-between">
                  <span>{employeeCount} empleados × {formatCurrency(currentPlan?.price_per_employee)}</span>
                  <span>{formatCurrency(employeeCount * (currentPlan?.price_per_employee || 0))}</span>
                </div>
                <div className="flex justify-between font-bold border-t mt-2 pt-2">
                  <span>Total mensual</span>
                  <span>{formatCurrency((currentPlan?.base_price || 0) + (employeeCount * (currentPlan?.price_per_employee || 0)))}</span>
                </div>
              </div>
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowAdjustEmployees(false)}>Cancelar</Button>
              <Button onClick={handleUpdateEmployees}>Confirmar Cambio</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Add Users Dialog */}
        <Dialog open={showAddUsers} onOpenChange={setShowAddUsers}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Usuarios Adicionales</DialogTitle>
              <DialogDescription>
                Agregue usuarios adicionales a su suscripción ($2.50/mes por usuario)
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4 py-4">
              <div>
                <Label>Usuarios adicionales: {additionalUsers}</Label>
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
                  <span>Usuarios incluidos</span>
                  <span>{includedUsers}</span>
                </div>
                <div className="flex justify-between">
                  <span>Usuarios adicionales</span>
                  <span>{additionalUsers} × $2.50 = {formatCurrency(additionalUsers * 2.50)}</span>
                </div>
                <div className="flex justify-between font-bold border-t mt-2 pt-2">
                  <span>Total usuarios</span>
                  <span>{includedUsers + additionalUsers}</span>
                </div>
              </div>
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowAddUsers(false)}>Cancelar</Button>
              <Button onClick={handleUpdateUsers}>Confirmar</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
