import { useState, useEffect } from "react";
import { Link, useSearchParams, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  Check, ArrowLeft, CreditCard, Users, Zap, Shield, Crown, Rocket, Loader2, Building2
} from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

const PLANS = {
  basic: {
    id: "basic",
    name: "FortexaRH Básico",
    basePrice: 5,
    pricePerEmployee: 1.5,
    maxEmployees: 50,
    icon: Rocket,
    color: "blue",
    features: [
      "Hasta 50 empleados",
      "3 usuarios incluidos",
      "Gestión de empleados",
      "Nómina básica",
      "Asistencias y vacaciones",
      "Calculadora de nómina",
      "Reportes básicos",
      "Exportación Excel/CSV",
      "Soporte por email"
    ]
  },
  pro: {
    id: "pro",
    name: "FortexaRH Pro",
    basePrice: 10,
    pricePerEmployee: 1.5,
    maxEmployees: 200,
    icon: Zap,
    color: "purple",
    popular: true,
    features: [
      "Hasta 200 empleados",
      "5 usuarios incluidos",
      "Todo lo del plan Básico",
      "Evaluaciones de desempeño",
      "Módulo de reclutamiento",
      "Organigrama intuitivo",
      "Reportes avanzados",
      "Integración QuickBooks",
      "Soporte prioritario"
    ]
  },
  enterprise: {
    id: "enterprise",
    name: "FortexaRH Enterprise",
    basePrice: 20,
    pricePerEmployee: 1.5,
    maxEmployees: 9999,
    icon: Crown,
    color: "amber",
    features: [
      "Empleados ilimitados",
      "7 usuarios incluidos",
      "Todo lo del plan Pro",
      "Roles personalizados",
      "Múltiples administradores",
      "API personalizada",
      "Integración SAP/Oracle",
      "Soporte 24/7",
      "Gerente de cuenta dedicado"
    ]
  }
};

export default function CheckoutPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const planId = searchParams.get("plan") || "basic";
  const plan = PLANS[planId] || PLANS.basic;
  const Icon = plan.icon;
  
  const [employeeCount, setEmployeeCount] = useState(5);
  const [loading, setLoading] = useState(false);

  const totalMonthly = plan.basePrice + (employeeCount * plan.pricePerEmployee);

  const handleCheckout = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/public/checkout`, {
        plan_id: plan.id,
        employee_count: employeeCount,
        origin_url: window.location.origin
      });

      if (response.data.checkout_url) {
        window.location.href = response.data.checkout_url;
      } else {
        toast.error("Error al iniciar el proceso de pago");
      }
    } catch (error) {
      console.error("Checkout error:", error);
      toast.error(error.response?.data?.detail || "Error al procesar el pago");
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <img src="/favicon.png" alt="FortexaRH" className="h-8 w-8" />
            <span className="font-bold text-slate-800">FortexaRH</span>
          </Link>
          <Link to="/#pricing">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Volver a planes
            </Button>
          </Link>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-12">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-slate-900 mb-2">Completa tu Compra</h1>
          <p className="text-slate-600">Configura tu plan y procede al pago seguro</p>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Plan Summary */}
          <Card className="h-fit">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center bg-gradient-to-br ${
                  plan.color === 'blue' ? 'from-blue-500 to-blue-600' :
                  plan.color === 'purple' ? 'from-purple-500 to-purple-600' :
                  'from-amber-500 to-amber-600'
                } text-white`}>
                  <Icon className="w-6 h-6" />
                </div>
                <div>
                  <CardTitle>{plan.name}</CardTitle>
                  {plan.popular && <Badge className="bg-purple-500 mt-1">Más Popular</Badge>}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 mb-6">
                {plan.features.map((feature, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-sm">
                    <Check className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                    <span className="text-slate-600">{feature}</span>
                  </div>
                ))}
              </div>

              <div className="border-t pt-4">
                <div className="flex justify-between text-sm text-slate-500 mb-1">
                  <span>Base mensual</span>
                  <span>{formatCurrency(plan.basePrice)}</span>
                </div>
                <div className="flex justify-between text-sm text-slate-500">
                  <span>Por empleado</span>
                  <span>{formatCurrency(plan.pricePerEmployee)}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Configuration & Payment */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="w-5 h-5" />
                  Cantidad de Empleados
                </CardTitle>
                <CardDescription>
                  ¿Cuántos empleados tendrá en su empresa?
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center gap-4">
                    <Input 
                      type="number" 
                      value={employeeCount}
                      onChange={(e) => setEmployeeCount(Math.max(1, Math.min(plan.maxEmployees === 9999 ? 1000 : plan.maxEmployees, parseInt(e.target.value) || 1)))}
                      min={1}
                      max={plan.maxEmployees === 9999 ? 1000 : plan.maxEmployees}
                      className="w-24 text-center text-lg font-bold"
                    />
                    <Slider
                      value={[employeeCount]}
                      onValueChange={(v) => setEmployeeCount(v[0])}
                      min={1}
                      max={plan.maxEmployees === 9999 ? 100 : plan.maxEmployees}
                      step={1}
                      className="flex-1"
                    />
                  </div>
                  <p className="text-sm text-slate-500">
                    {plan.maxEmployees === 9999 ? 'Sin límite de empleados' : `Máximo ${plan.maxEmployees} empleados en este plan`}
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-emerald-50 to-white border-emerald-200">
              <CardHeader>
                <CardTitle className="text-emerald-800">Resumen del Pago</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-slate-600">Plan {plan.name}</span>
                    <span className="font-medium">{formatCurrency(plan.basePrice)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">{employeeCount} empleados × {formatCurrency(plan.pricePerEmployee)}</span>
                    <span className="font-medium">{formatCurrency(employeeCount * plan.pricePerEmployee)}</span>
                  </div>
                  <div className="border-t border-emerald-200 pt-3 mt-3">
                    <div className="flex justify-between items-center">
                      <span className="text-lg font-semibold text-slate-800">Total mensual</span>
                      <span className="text-2xl font-bold text-emerald-600">{formatCurrency(totalMonthly)}</span>
                    </div>
                  </div>
                </div>

                <Button 
                  className="w-full mt-6 h-12 text-lg bg-emerald-600 hover:bg-emerald-700"
                  onClick={handleCheckout}
                  disabled={loading}
                  data-testid="proceed-to-payment-btn"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                      Procesando...
                    </>
                  ) : (
                    <>
                      <CreditCard className="w-5 h-5 mr-2" />
                      Proceder al Pago
                    </>
                  )}
                </Button>

                <div className="mt-4 text-center">
                  <p className="text-xs text-slate-500">
                    Pago seguro procesado por Stripe. Después del pago podrás crear tu cuenta.
                  </p>
                </div>
              </CardContent>
            </Card>

            <div className="text-center">
              <p className="text-sm text-slate-500">
                ¿Prefieres probar primero?{" "}
                <Link to="/register" className="text-blue-600 hover:underline">
                  Prueba gratis por 5 días
                </Link>
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
