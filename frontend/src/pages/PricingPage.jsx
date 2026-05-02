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
import { languages } from "@/i18n";

export default function PricingPage() {
  const { t, i18n } = useTranslation();
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user, getAuthHeaders } = useAuth();
  const navigate = useNavigate();

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
    localStorage.setItem('fortexarh-language', lng);
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
      toast.error(error.response?.data?.detail || t('common.error'));
    }
  };

  // Feature translation mapping (Spanish source -> translation key)
  const featureKeyMap = {
    // Basic plan features
    "Hasta 50 empleados": "pricing.features.upTo50",
    "3 usuarios incluidos": "pricing.features.users3",
    "Gestión de empleados": "pricing.features.employeeManagement",
    "Nómina básica": "pricing.features.basicPayroll",
    "Asistencias y vacaciones": "pricing.features.attendanceVacations",
    "Calculadora de nómina": "pricing.features.payrollCalculator",
    "Módulo de préstamos": "pricing.features.loansModule",
    "Reportes básicos": "pricing.features.basicReports",
    "Exportación Excel/CSV": "pricing.features.excelExport",
    "Soporte por email": "pricing.features.emailSupport",
    "Integración FortexaERP": "pricing.features.erpIntegration",
    // Pro plan features
    "Hasta 200 empleados": "pricing.features.upTo200",
    "5 usuarios incluidos": "pricing.features.users5",
    "Todo lo del plan Básico": "pricing.features.allBasic",
    "Evaluaciones de desempeño": "pricing.features.evaluations",
    "Módulo de reclutamiento": "pricing.features.recruitment",
    "Portal autoservicio empleados": "pricing.features.employeePortal",
    "Organigrama intuitivo": "pricing.features.orgChart",
    "Reportes avanzados": "pricing.features.advancedReports",
    "Integración QuickBooks": "pricing.features.quickbooks",
    "QuickBooks Desktop (IIF)": "pricing.features.qbDesktop",
    "Pagos ACH bancarios": "pricing.features.achPayments",
    "Soporte prioritario": "pricing.features.prioritySupport",
    // Enterprise plan features
    "Empleados ilimitados": "pricing.features.unlimitedEmployees",
    "7 usuarios incluidos": "pricing.features.users7",
    "Todo lo del plan Pro": "pricing.features.allPro",
    "Roles personalizados": "pricing.features.customRoles",
    "Múltiples administradores": "pricing.features.multiAdmin",
    "Contratos laborales": "pricing.features.contracts",
    "Firma electrónica": "pricing.features.eSignature",
    "Workflows de aprobación": "pricing.features.approvalWorkflows",
    "API personalizada": "pricing.features.customAPI",
    "Flujos de trabajo avanzados": "pricing.features.advancedWorkflows",
    "Integración SAP/Oracle/Dynamics": "pricing.features.sapOracleIntegration",
    "Soporte 24/7": "pricing.features.support247",
    "Gerente de cuenta dedicado": "pricing.features.dedicatedManager"
  };

  // Translate feature from Spanish to current language
  const translateFeature = (feature) => {
    const key = featureKeyMap[feature];
    if (key) {
      return t(key, feature); // fallback to original if key not found
    }
    return feature;
  };

  // Build localized free plan
  const getFreePlan = () => ({
    plan_id: "free",
    name: t('landing.pricing.plans.free.name'),
    base_price: 0,
    price_per_employee: 0,
    max_employees: 5,
    features: [
      t('landing.pricing.plans.free.features.employees'),
      t('landing.pricing.plans.free.features.management'),
      t('landing.pricing.plans.free.features.attendance'),
      t('landing.pricing.plans.free.features.support')
    ]
  });

  // Translate plan name based on plan_id
  const getPlanName = (plan) => {
    const nameMap = {
      'basic': t('pricing.planNames.basic', 'FortexaRH Basic'),
      'pro': t('pricing.planNames.pro', 'FortexaRH Pro'),
      'enterprise': t('pricing.planNames.enterprise', 'FortexaRH Enterprise')
    };
    return nameMap[plan.plan_id] || plan.name;
  };

  const allPlans = [
    getFreePlan(),
    ...plans.map(plan => ({
      ...plan,
      name: getPlanName(plan),
      features: plan.features.map(f => translateFeature(f))
    }))
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
              {/* Language Selector */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="sm" className="gap-2" data-testid="pricing-language-selector">
                    <Globe className="w-4 h-4" />
                    <span className="hidden sm:inline">{languages.find(l => l.code === i18n.language)?.name || 'Español'}</span>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  {languages.map((lang) => (
                    <DropdownMenuItem
                      key={lang.code}
                      onClick={() => changeLanguage(lang.code)}
                      className={i18n.language === lang.code ? 'bg-slate-100' : ''}
                    >
                      <span className="mr-2">{lang.flag}</span>
                      {lang.name}
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>
              
              {user ? (
                <Link to="/dashboard">
                  <Button variant="outline" data-testid="go-dashboard-btn">
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    {t('landing.pricing.goToDashboard')}
                  </Button>
                </Link>
              ) : (
                <>
                  <Link to="/login">
                    <Button variant="ghost">{t('landing.nav.login')}</Button>
                  </Link>
                  <Link to="/register">
                    <Button className="bg-slate-900 hover:bg-slate-800">{t('landing.nav.getStarted')}</Button>
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
              {t('landing.pricing.badge')}
            </div>
            <h1 className="text-4xl sm:text-5xl font-bold text-slate-900 heading mb-4">
              {t('landing.pricing.title')}
            </h1>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              {t('landing.pricing.subtitle')}
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
                      {t('landing.pricing.mostPopular')}
                    </div>
                  )}
                  <CardHeader className="text-center pb-4">
                    <CardTitle className="text-xl heading">{plan.name}</CardTitle>
                    <div className="mt-4">
                      <span className="text-4xl font-bold text-slate-900">${plan.base_price}</span>
                      <span className="text-slate-500">/{t('landing.pricing.month')}</span>
                    </div>
                    {plan.price_per_employee > 0 && (
                      <p className="text-sm text-slate-500 mt-1">
                        + ${plan.price_per_employee} {t('landing.pricing.perEmployee')}
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
                      {isFree ? t('landing.pricing.startFree') : t('landing.pricing.selectPlan')}
                    </Button>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {/* FAQ Section */}
          <div className="mt-20 text-center">
            <h2 className="text-2xl font-bold text-slate-900 heading mb-8">
              {t('landing.pricing.faq.title')}
            </h2>
            <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto text-left">
              <div>
                <h3 className="font-semibold text-slate-900 mb-2">{t('landing.pricing.faq.changePlan.question')}</h3>
                <p className="text-slate-600 text-sm">
                  {t('landing.pricing.faq.changePlan.answer')}
                </p>
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 mb-2">{t('landing.pricing.faq.perEmployee.question')}</h3>
                <p className="text-slate-600 text-sm">
                  {t('landing.pricing.faq.perEmployee.answer')}
                </p>
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 mb-2">{t('landing.pricing.faq.trial.question')}</h3>
                <p className="text-slate-600 text-sm">
                  {t('landing.pricing.faq.trial.answer')}
                </p>
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 mb-2">{t('landing.pricing.faq.payment.question')}</h3>
                <p className="text-slate-600 text-sm">
                  {t('landing.pricing.faq.payment.answer')}
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-slate-900 text-white py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p className="text-slate-400">
            © {new Date().getFullYear()} FortexaRH. {t('landing.footer.rights')}
          </p>
        </div>
      </footer>
    </div>
  );
}
