import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Users, Check, ArrowLeft, Zap, Globe } from "lucide-react";
import { toast } from "sonner";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const languages = [
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' }
];

export default function PricingPage() {
  const { t, i18n } = useTranslation();
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user, getAuthHeaders } = useAuth();
  const navigate = useNavigate();

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
    localStorage.setItem('i18nextLng', lng);
  };

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const response = await axios.get(`${API}/plans`);
      setPlans(response.data.filter(p => p.plan_id !== "free"));
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPlan = async (planId) => {
    if (!user) {
      navigate("/register");
      return;
    }

    try {
      const response = await axios.post(`${API}/checkout`, {
        plan_id: planId,
        origin_url: window.location.origin
      }, { headers: getAuthHeaders(), withCredentials: true });
      
      window.location.href = response.data.url;
    } catch (error) {
      toast.error(error.response?.data?.detail || "Error al procesar");
    }
  };

  const allPlans = [
    {
      plan_id: "free",
      name: "Prueba Gratuita",
      base_price: 0,
      price_per_employee: 0,
      max_employees: 5,
      features: ["Hasta 5 empleados", "Gestión básica de empleados", "Control de asistencias", "Soporte por email"]
    },
    ...plans
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-slate-900 rounded-lg flex items-center justify-center">
                <Users className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-slate-900 heading">FortexaRH</span>
            </Link>
            <div className="flex items-center gap-3">
              {user ? (
                <Link to="/dashboard">
                  <Button variant="outline" data-testid="go-dashboard-btn">
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Ir al Dashboard
                  </Button>
                </Link>
              ) : (
                <>
                  <Link to="/login">
                    <Button variant="ghost">Iniciar Sesión</Button>
                  </Link>
                  <Link to="/register">
                    <Button className="bg-slate-900 hover:bg-slate-800">Comenzar Gratis</Button>
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 bg-emerald-50 text-emerald-700 px-4 py-2 rounded-full text-sm font-medium mb-6">
              <Zap className="w-4 h-4" />
              Planes flexibles para cada empresa
            </div>
            <h1 className="text-4xl sm:text-5xl font-bold text-slate-900 heading mb-4">
              Elige el plan perfecto para tu equipo
            </h1>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              Modelo híbrido: paga una tarifa base más un costo por empleado. 
              Escala según creces.
            </p>
          </div>

          {/* Plans Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6" data-testid="pricing-grid">
            {allPlans.map((plan, index) => {
              const isPopular = plan.plan_id === "pro";
              const isFree = plan.plan_id === "free";
              
              return (
                <Card 
                  key={plan.plan_id}
                  className={`relative ${isPopular ? "border-emerald-500 shadow-xl scale-105" : "border-slate-200"}`}
                  data-testid={`pricing-card-${plan.plan_id}`}
                >
                  {isPopular && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 bg-emerald-500 text-white text-xs font-semibold rounded-full">
                      Más Popular
                    </div>
                  )}
                  <CardHeader className="text-center pb-4">
                    <CardTitle className="text-xl heading">{plan.name}</CardTitle>
                    <div className="mt-4">
                      <span className="text-4xl font-bold text-slate-900">${plan.base_price}</span>
                      <span className="text-slate-500">/mes</span>
                    </div>
                    {plan.price_per_employee > 0 && (
                      <p className="text-sm text-slate-500 mt-1">
                        + ${plan.price_per_employee} por empleado
                      </p>
                    )}
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <ul className="space-y-3">
                      {plan.features.map((feature, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm">
                          <Check className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />
                          <span className="text-slate-600">{feature}</span>
                        </li>
                      ))}
                    </ul>
                    <Button 
                      className={`w-full ${
                        isFree 
                          ? "bg-slate-100 text-slate-900 hover:bg-slate-200" 
                          : isPopular 
                            ? "bg-emerald-600 hover:bg-emerald-700" 
                            : "bg-slate-900 hover:bg-slate-800"
                      }`}
                      onClick={() => isFree ? navigate("/register") : handleSelectPlan(plan.plan_id)}
                      data-testid={`select-plan-${plan.plan_id}`}
                    >
                      {isFree ? "Comenzar Gratis" : "Seleccionar Plan"}
                    </Button>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {/* FAQ Section */}
          <div className="mt-20 text-center">
            <h2 className="text-2xl font-bold text-slate-900 heading mb-8">
              Preguntas Frecuentes
            </h2>
            <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto text-left">
              <div>
                <h3 className="font-semibold text-slate-900 mb-2">¿Puedo cambiar de plan?</h3>
                <p className="text-slate-600 text-sm">
                  Sí, puedes actualizar o degradar tu plan en cualquier momento. 
                  Los cambios se aplican en tu próximo ciclo de facturación.
                </p>
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 mb-2">¿Cómo funciona el cobro por empleado?</h3>
                <p className="text-slate-600 text-sm">
                  Pagas la tarifa base del plan más una cantidad fija por cada empleado activo en tu sistema al momento de la facturación.
                </p>
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 mb-2">¿Hay periodo de prueba?</h3>
                <p className="text-slate-600 text-sm">
                  El plan gratuito te permite probar el sistema con hasta 5 empleados sin límite de tiempo.
                </p>
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 mb-2">¿Qué métodos de pago aceptan?</h3>
                <p className="text-slate-600 text-sm">
                  Aceptamos todas las tarjetas de crédito y débito principales a través de Stripe.
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="py-8 px-4 border-t border-slate-200 bg-white">
        <div className="max-w-7xl mx-auto text-center text-slate-500 text-sm">
          © {new Date().getFullYear()} FortexaRH. Todos los derechos reservados.
        </div>
      </footer>
    </div>
  );
}
