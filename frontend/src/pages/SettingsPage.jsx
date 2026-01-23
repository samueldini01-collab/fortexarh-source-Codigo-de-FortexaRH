import { useState, useEffect, useCallback } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { Building2, CreditCard, User, Check, Crown, Lock, Eye, EyeOff, AlertCircle } from "lucide-react";
import { toast } from "sonner";

export default function SettingsPage() {
  const [company, setCompany] = useState(null);
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [companyForm, setCompanyForm] = useState({
    name: "",
    industry: "",
    address: "",
    phone: ""
  });
  
  // Password change state
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: ""
  });
  const [passwordError, setPasswordError] = useState("");
  const [showPasswords, setShowPasswords] = useState(false);
  const [savingPassword, setSavingPassword] = useState(false);
  
  const { getAuthHeaders, user } = useAuth();

  const fetchData = useCallback(async () => {
    try {
      const [companyRes, subRes] = await Promise.all([
        axios.get(`${API}/company`, { headers: getAuthHeaders(), withCredentials: true }),
        axios.get(`${API}/subscription`, { headers: getAuthHeaders(), withCredentials: true })
      ]);
      setCompany(companyRes.data);
      setSubscription(subRes.data);
      setCompanyForm({
        name: companyRes.data.name || "",
        industry: companyRes.data.industry || "",
        address: companyRes.data.address || "",
        phone: companyRes.data.phone || ""
      });
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSaveCompany = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await axios.put(`${API}/company`, companyForm, { headers: getAuthHeaders(), withCredentials: true });
      toast.success("Información actualizada");
      fetchData();
    } catch (error) {
      toast.error("Error al actualizar");
    } finally {
      setSaving(false);
    }
  };

  const handleUpgrade = async (planId) => {
    try {
      const response = await axios.post(`${API}/checkout`, {
        plan_id: planId,
        origin_url: window.location.origin
      }, { headers: getAuthHeaders(), withCredentials: true });
      
      window.location.href = response.data.url;
    } catch (error) {
      toast.error("Error al procesar el pago");
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setPasswordError("");
    
    // Validations
    if (passwordForm.newPassword.length < 6) {
      setPasswordError("La nueva contraseña debe tener al menos 6 caracteres");
      return;
    }
    
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      setPasswordError("Las contraseñas no coinciden");
      return;
    }
    
    setSavingPassword(true);
    try {
      await axios.post(`${API}/auth/change-password`, {
        current_password: passwordForm.currentPassword,
        new_password: passwordForm.newPassword
      }, { headers: getAuthHeaders(), withCredentials: true });
      
      toast.success("Contraseña actualizada correctamente");
      setPasswordForm({ currentPassword: "", newPassword: "", confirmPassword: "" });
    } catch (error) {
      const message = error.response?.data?.detail || "Error al cambiar contraseña";
      setPasswordError(message);
      toast.error(message);
    } finally {
      setSavingPassword(false);
    }
  };

  const plans = [
    {
      id: "basic",
      name: "FortexaRH Básico",
      price: "$10/mes + $1.5/empleado",
      features: ["Hasta 50 empleados", "Gestión de empleados", "Nómina básica", "Asistencias", "Vacaciones", "Soporte por email"]
    },
    {
      id: "pro",
      name: "FortexaRH Pro",
      price: "$20/mes + $1.5/empleado",
      popular: true,
      features: ["Hasta 200 empleados", "Todas las funciones básicas", "Evaluaciones de desempeño", "Reclutamiento", "Reportes avanzados", "Soporte prioritario"]
    },
    {
      id: "enterprise",
      name: "FortexaRH Enterprise",
      price: "$76/mes + $1.5/empleado",
      features: ["Empleados ilimitados", "Todas las funciones", "API personalizada", "Soporte 24/7", "Gerente de cuenta dedicado", "Capacitación incluida"]
    }
  ];

  return (
    <DashboardLayout title="Configuración">
      <div className="space-y-6" data-testid="settings-page">
        <Tabs defaultValue="company" className="space-y-6">
          <TabsList>
            <TabsTrigger value="company" data-testid="tab-company">
              <Building2 className="w-4 h-4 mr-2" />
              Empresa
            </TabsTrigger>
            <TabsTrigger value="subscription" data-testid="tab-subscription">
              <CreditCard className="w-4 h-4 mr-2" />
              Suscripción
            </TabsTrigger>
            <TabsTrigger value="account" data-testid="tab-account">
              <User className="w-4 h-4 mr-2" />
              Mi Cuenta
            </TabsTrigger>
          </TabsList>

          {/* Company Tab */}
          <TabsContent value="company">
            <Card className="border-slate-200 dark:border-slate-700">
              <CardHeader>
                <CardTitle>Información de la Empresa</CardTitle>
                <CardDescription>Actualiza los datos de tu empresa</CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="space-y-4">
                    {Array(4).fill(0).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}
                  </div>
                ) : (
                  <form onSubmit={handleSaveCompany} className="space-y-4 max-w-lg">
                    <div className="space-y-2">
                      <Label>Nombre de la Empresa</Label>
                      <Input
                        value={companyForm.name}
                        onChange={(e) => setCompanyForm({...companyForm, name: e.target.value})}
                        required
                        data-testid="company-name"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Industria</Label>
                      <Input
                        value={companyForm.industry}
                        onChange={(e) => setCompanyForm({...companyForm, industry: e.target.value})}
                        placeholder="Ej: Tecnología, Manufactura, Servicios..."
                        data-testid="company-industry"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Dirección</Label>
                      <Input
                        value={companyForm.address}
                        onChange={(e) => setCompanyForm({...companyForm, address: e.target.value})}
                        data-testid="company-address"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Teléfono</Label>
                      <Input
                        value={companyForm.phone}
                        onChange={(e) => setCompanyForm({...companyForm, phone: e.target.value})}
                        data-testid="company-phone"
                      />
                    </div>
                    <Button type="submit" className="bg-slate-900 hover:bg-slate-800" disabled={saving} data-testid="save-company-btn">
                      {saving ? "Guardando..." : "Guardar Cambios"}
                    </Button>
                  </form>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Subscription Tab */}
          <TabsContent value="subscription" className="space-y-6">
            {/* Current Plan */}
            <Card className="border-emerald-200 bg-emerald-50/30">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-emerald-600 font-medium">Plan Actual</p>
                    <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">{subscription?.current_plan?.name || "Cargando..."}</p>
                    <p className="text-sm text-slate-500 mt-1">
                      {subscription?.employee_count} empleados • ${subscription?.monthly_cost?.toFixed(2)}/mes
                    </p>
                  </div>
                  <div className="w-16 h-16 bg-emerald-100 rounded-xl flex items-center justify-center">
                    <Crown className="w-8 h-8 text-emerald-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Available Plans */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {plans.map((plan) => {
                const isCurrentPlan = subscription?.current_plan?.plan_id === plan.id;
                return (
                  <Card 
                    key={plan.id} 
                    className={`relative ${plan.popular ? "border-emerald-500 shadow-lg" : "border-slate-200 dark:border-slate-700"}`}
                    data-testid={`plan-card-${plan.id}`}
                  >
                    {plan.popular && (
                      <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-emerald-500 text-white text-xs font-medium rounded-full">
                        Más Popular
                      </div>
                    )}
                    <CardHeader className="text-center pb-2">
                      <CardTitle>{plan.name}</CardTitle>
                      <p className="text-2xl font-bold text-slate-900 mt-2">{plan.price}</p>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <ul className="space-y-2">
                        {plan.features.map((feature, index) => (
                          <li key={index} className="flex items-center gap-2 text-sm">
                            <Check className="w-4 h-4 text-emerald-500" />
                            {feature}
                          </li>
                        ))}
                      </ul>
                      <Button 
                        className={`w-full ${isCurrentPlan ? "bg-slate-200 text-slate-600 dark:text-slate-300" : plan.popular ? "bg-emerald-600 hover:bg-emerald-700" : "bg-slate-900 hover:bg-slate-800"}`}
                        disabled={isCurrentPlan}
                        onClick={() => handleUpgrade(plan.id)}
                        data-testid={`upgrade-${plan.id}`}
                      >
                        {isCurrentPlan ? "Plan Actual" : "Actualizar"}
                      </Button>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </TabsContent>

          {/* Account Tab */}
          <TabsContent value="account" className="space-y-6">
            <Card className="border-slate-200 dark:border-slate-700">
              <CardHeader>
                <CardTitle>Mi Cuenta</CardTitle>
                <CardDescription>Información de tu cuenta personal</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4 max-w-lg">
                  <div className="flex items-center gap-4">
                    <div className="w-16 h-16 bg-slate-200 rounded-full flex items-center justify-center text-xl font-bold text-slate-600 dark:text-slate-300">
                      {user?.name?.split(" ").map(n => n[0]).join("").toUpperCase() || "U"}
                    </div>
                    <div>
                      <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">{user?.name}</p>
                      <p className="text-slate-500 dark:text-slate-400">{user?.email}</p>
                    </div>
                  </div>
                  <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-slate-500 dark:text-slate-400">Rol</p>
                        <p className="font-medium capitalize">{user?.role || "Admin"}</p>
                      </div>
                      <div>
                        <p className="text-slate-500 dark:text-slate-400">ID de Usuario</p>
                        <p className="font-mono text-xs">{user?.user_id}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Change Password Section */}
            <Card className="border-slate-200 dark:border-slate-700">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Lock className="w-5 h-5" />
                  Cambiar Contraseña
                </CardTitle>
                <CardDescription>
                  Actualiza tu contraseña para mantener tu cuenta segura
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleChangePassword} className="space-y-4 max-w-lg">
                  {passwordError && (
                    <div className="flex items-center gap-2 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
                      <AlertCircle className="w-4 h-4 shrink-0" />
                      {passwordError}
                    </div>
                  )}
                  
                  <div className="space-y-2">
                    <Label htmlFor="currentPassword">Contraseña Actual</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <Input
                        id="currentPassword"
                        type={showPasswords ? "text" : "password"}
                        value={passwordForm.currentPassword}
                        onChange={(e) => setPasswordForm({...passwordForm, currentPassword: e.target.value})}
                        className="pl-9 pr-10"
                        placeholder="Tu contraseña actual"
                        required
                        data-testid="current-password-input"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPasswords(!showPasswords)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:text-slate-300"
                      >
                        {showPasswords ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="newPassword">Nueva Contraseña</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <Input
                        id="newPassword"
                        type={showPasswords ? "text" : "password"}
                        value={passwordForm.newPassword}
                        onChange={(e) => setPasswordForm({...passwordForm, newPassword: e.target.value})}
                        className="pl-9"
                        placeholder="Mínimo 6 caracteres"
                        required
                        minLength={6}
                        data-testid="new-password-input"
                      />
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="confirmPassword">Confirmar Nueva Contraseña</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <Input
                        id="confirmPassword"
                        type={showPasswords ? "text" : "password"}
                        value={passwordForm.confirmPassword}
                        onChange={(e) => setPasswordForm({...passwordForm, confirmPassword: e.target.value})}
                        className="pl-9"
                        placeholder="Repite la nueva contraseña"
                        required
                        data-testid="confirm-new-password-input"
                      />
                    </div>
                  </div>
                  
                  <Button 
                    type="submit" 
                    disabled={savingPassword}
                    className="bg-emerald-600 hover:bg-emerald-700"
                    data-testid="change-password-btn"
                  >
                    {savingPassword ? "Guardando..." : "Cambiar Contraseña"}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}
