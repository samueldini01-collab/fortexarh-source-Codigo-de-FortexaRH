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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { 
  Check, X, CreditCard, Users, Building2, Zap, Shield, Clock,
  AlertTriangle, RefreshCw, ArrowUpRight, Crown, Rocket, Globe
} from "lucide-react";
import { toast } from "sonner";

const PLAN_ICONS = {
  basic: Rocket,
  pro: Zap,
  enterprise: Crown
};

const PLAN_COLORS = {
  basic: "blue",
  pro: "purple",
  enterprise: "amber"
};

export default function SubscriptionsPage() {
  const { getAuthHeaders } = useAuth();
  const [loading, setLoading] = useState(true);
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
      setEmployeeCount(subRes.data.employee_count || 5);
      setAdditionalUsers(subRes.data.additional_users || 0);
    } catch (error) {
      console.error("Error fetching subscription:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleChangePlan = async (planId) => {
    try {
      await axios.put(`${API}/subscription`, {
        plan_id: planId
      }, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Plan actualizado correctamente");
      setShowChangePlan(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al cambiar plan");
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

  const handleRenewSubscription = async () => {
    try {
      await axios.put(`${API}/subscription`, {
        action: "renew"
      }, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Suscripción renovada correctamente");
      fetchData();
    } catch (error) {
      toast.error("Error al renovar");
    }
  };

  const formatCurrency = (value) => 
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value || 0);

  const getStatusBadge = (status) => {
    const styles = {
      active: "bg-emerald-100 text-emerald-700",
      trial: "bg-blue-100 text-blue-700",
      cancelled: "bg-red-100 text-red-700",
      expired: "bg-slate-100 text-slate-700"
    };
    const labels = {
      active: "Activo",
      trial: "Prueba",
      cancelled: "Cancelado",
      expired: "Vencido"
    };
    return <Badge className={styles[status]}>{labels[status] || status}</Badge>;
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

  const currentPlan = subscription?.plan_details || plans.find(p => p.id === subscription?.plan_id);

  return (
    <DashboardLayout title="Suscripción">
      <div className="space-y-6" data-testid="subscriptions-page">
        {/* Alert for cancelled/expired */}
        {(subscription?.status === 'cancelled' || subscription?.status === 'expired') && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-4">
            <AlertTriangle className="w-8 h-8 text-red-500" />
            <div className="flex-1">
              <h3 className="font-semibold text-red-800">Suscripción {subscription.status === 'cancelled' ? 'Cancelada' : 'Vencida'}</h3>
              <p className="text-red-600 text-sm">Renueve su suscripción para continuar usando el sistema.</p>
            </div>
            <Button onClick={handleRenewSubscription} className="bg-red-600 hover:bg-red-700">
              <RefreshCw className="w-4 h-4 mr-2" />Renovar Ahora
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
                <div className={`w-16 h-16 rounded-2xl flex items-center justify-center bg-gradient-to-br from-${PLAN_COLORS[subscription?.plan_id] || 'blue'}-500 to-${PLAN_COLORS[subscription?.plan_id] || 'blue'}-600`}>
                  {PLAN_ICONS[subscription?.plan_id] && (
                    <div className="text-white">
                      {(() => { const Icon = PLAN_ICONS[subscription?.plan_id]; return <Icon className="w-8 h-8" />; })()}
                    </div>
                  )}
                </div>
                <div className="flex-1">
                  <h2 className="text-2xl font-bold text-slate-800">{subscription?.plan_name}</h2>
                  <p className="text-slate-500">{currentPlan?.max_employees === -1 ? 'Empleados ilimitados' : `Hasta ${currentPlan?.max_employees} empleados`}</p>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                    <div className="p-3 bg-slate-50 rounded-lg">
                      <p className="text-xs text-slate-500">Base mensual</p>
                      <p className="text-lg font-bold">{formatCurrency(subscription?.base_price)}</p>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-lg">
                      <p className="text-xs text-slate-500">Por empleado</p>
                      <p className="text-lg font-bold">{formatCurrency(subscription?.employee_price)}</p>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-lg">
                      <p className="text-xs text-slate-500">Empleados</p>
                      <p className="text-lg font-bold">{subscription?.employee_count}</p>
                    </div>
                    <div className="p-3 bg-emerald-50 rounded-lg">
                      <p className="text-xs text-emerald-600">Total mensual</p>
                      <p className="text-lg font-bold text-emerald-700">{formatCurrency(subscription?.total_monthly)}</p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex gap-2 border-t pt-4">
              <Button variant="outline" onClick={() => setShowChangePlan(true)}>
                <ArrowUpRight className="w-4 h-4 mr-2" />Cambiar Plan
              </Button>
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
                  <span className="font-medium">{subscription?.current_employees} / {subscription?.max_employees === -1 ? '∞' : subscription?.max_employees}</span>
                </div>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-blue-500 rounded-full"
                    style={{ width: `${subscription?.max_employees === -1 ? 30 : (subscription?.current_employees / subscription?.max_employees) * 100}%` }}
                  />
                </div>
              </div>
              
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-500">Usuarios</span>
                  <span className="font-medium">{subscription?.current_users} / {subscription?.included_users + (subscription?.additional_users || 0)}</span>
                </div>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-purple-500 rounded-full"
                    style={{ width: `${(subscription?.current_users / (subscription?.included_users + (subscription?.additional_users || 0))) * 100}%` }}
                  />
                </div>
              </div>

              <div className="pt-4 border-t">
                <p className="text-sm text-slate-500">Período actual</p>
                <p className="font-medium">
                  {new Date(subscription?.current_period_start).toLocaleDateString()} - {new Date(subscription?.current_period_end).toLocaleDateString()}
                </p>
              </div>

              {subscription?.status === 'trial' && (
                <div className="p-3 bg-blue-50 rounded-lg">
                  <p className="text-sm text-blue-700">
                    <Clock className="w-4 h-4 inline mr-1" />
                    Prueba termina: {new Date(subscription?.trial_ends_at).toLocaleDateString()}
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
                const Icon = PLAN_ICONS[plan.id] || Rocket;
                const isCurrentPlan = subscription?.plan_id === plan.id;
                
                return (
                  <div 
                    key={plan.id}
                    className={`relative rounded-xl border-2 p-6 transition-all ${
                      isCurrentPlan ? 'border-blue-500 bg-blue-50' : 'border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    {isCurrentPlan && (
                      <Badge className="absolute -top-3 left-1/2 -translate-x-1/2 bg-blue-500">Plan Actual</Badge>
                    )}
                    
                    <div className="text-center mb-4">
                      <div className={`w-14 h-14 mx-auto rounded-xl flex items-center justify-center bg-gradient-to-br from-${PLAN_COLORS[plan.id]}-500 to-${PLAN_COLORS[plan.id]}-600 text-white mb-3`}>
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
                        {plan.max_employees === -1 ? 'Empleados ilimitados' : `Hasta ${plan.max_employees} empleados`}
                      </p>
                      <p className="text-sm text-slate-500">{plan.included_users} usuarios incluidos</p>
                    </div>

                    <div className="space-y-2 mb-6 max-h-48 overflow-y-auto">
                      {plan.features.slice(0, 8).map((feature, idx) => (
                        <div key={idx} className="flex items-start gap-2 text-sm">
                          <Check className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                          <span className="text-slate-600">{feature}</span>
                        </div>
                      ))}
                      {plan.features.length > 8 && (
                        <p className="text-xs text-slate-400">+ {plan.features.length - 8} más...</p>
                      )}
                    </div>

                    <Button 
                      className={`w-full ${isCurrentPlan ? 'bg-slate-400' : ''}`}
                      disabled={isCurrentPlan}
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

        {/* Change Plan Dialog */}
        <Dialog open={showChangePlan} onOpenChange={setShowChangePlan}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Cambiar Plan</DialogTitle>
              <DialogDescription>
                {selectedPlan ? `¿Desea cambiar a ${selectedPlan.name}?` : 'Seleccione un nuevo plan'}
              </DialogDescription>
            </DialogHeader>
            
            {selectedPlan && (
              <div className="space-y-4">
                <div className="p-4 bg-slate-50 rounded-lg">
                  <h4 className="font-semibold">{selectedPlan.name}</h4>
                  <p className="text-2xl font-bold mt-1">{formatCurrency(selectedPlan.base_price)}<span className="text-sm font-normal">/mes</span></p>
                  <p className="text-sm text-slate-500">+ {formatCurrency(selectedPlan.price_per_employee)} por empleado</p>
                </div>
                
                <div className="text-sm text-slate-600">
                  <p>El cambio se aplicará inmediatamente. Se ajustará el monto prorrateado en su próxima factura.</p>
                </div>
              </div>
            )}
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowChangePlan(false)}>Cancelar</Button>
              <Button onClick={() => handleChangePlan(selectedPlan?.id)} disabled={!selectedPlan}>
                Confirmar Cambio
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
                  max={currentPlan?.max_employees === -1 ? 500 : currentPlan?.max_employees}
                  step={1}
                  className="mt-2"
                />
              </div>
              
              <div className="p-4 bg-slate-50 rounded-lg">
                <div className="flex justify-between">
                  <span>Base del plan</span>
                  <span>{formatCurrency(subscription?.base_price)}</span>
                </div>
                <div className="flex justify-between">
                  <span>{employeeCount} empleados × {formatCurrency(subscription?.employee_price)}</span>
                  <span>{formatCurrency(employeeCount * subscription?.employee_price)}</span>
                </div>
                <div className="flex justify-between font-bold border-t mt-2 pt-2">
                  <span>Total mensual</span>
                  <span>{formatCurrency(subscription?.base_price + (employeeCount * subscription?.employee_price))}</span>
                </div>
              </div>
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowAdjustEmployees(false)}>Cancelar</Button>
              <Button onClick={handleUpdateEmployees}>Guardar Cambios</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Additional Users Dialog */}
        <Dialog open={showAddUsers} onOpenChange={setShowAddUsers}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Usuarios Adicionales</DialogTitle>
              <DialogDescription>
                Compre usuarios adicionales a $2.50/mes cada uno
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4 py-4">
              <div>
                <Label>Usuarios adicionales: {additionalUsers}</Label>
                <div className="flex items-center gap-4 mt-2">
                  <Button variant="outline" size="icon" onClick={() => setAdditionalUsers(Math.max(0, additionalUsers - 1))}>-</Button>
                  <span className="text-2xl font-bold w-12 text-center">{additionalUsers}</span>
                  <Button variant="outline" size="icon" onClick={() => setAdditionalUsers(additionalUsers + 1)}>+</Button>
                </div>
              </div>
              
              <div className="p-4 bg-slate-50 rounded-lg">
                <p className="text-sm text-slate-600">
                  Usuarios incluidos en su plan: <strong>{subscription?.included_users}</strong>
                </p>
                <p className="text-sm text-slate-600">
                  Usuarios adicionales: <strong>{additionalUsers}</strong> × $2.50 = <strong>{formatCurrency(additionalUsers * 2.5)}</strong>/mes
                </p>
                <p className="text-sm font-semibold mt-2">
                  Total usuarios disponibles: <strong>{subscription?.included_users + additionalUsers}</strong>
                </p>
              </div>
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowAddUsers(false)}>Cancelar</Button>
              <Button onClick={handleUpdateUsers}>Guardar Cambios</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
