import { useState, useEffect } from "react";
import { Link, useSearchParams, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  Check, ArrowLeft, CreditCard, Users, Zap, Shield, Crown, Rocket, Loader2, Building2, Mail
} from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

// Plan configuration (non-translatable data)
const PLANS_CONFIG = {
  basic: {
    id: "basic",
    basePrice: 5,
    pricePerEmployee: 1.5,
    maxEmployees: 50,
    icon: Rocket,
    color: "blue",
    featureKeys: ["employees", "users", "management", "payroll", "attendance", "calculator", "reports", "export", "support"]
  },
  pro: {
    id: "pro",
    basePrice: 10,
    pricePerEmployee: 1.5,
    maxEmployees: 200,
    icon: Zap,
    color: "purple",
    popular: true,
    featureKeys: ["employees", "users", "allBasic", "evaluations", "recruitment", "orgChart", "reports", "quickbooks", "support"]
  },
  enterprise: {
    id: "enterprise",
    basePrice: 20,
    pricePerEmployee: 1.5,
    maxEmployees: 9999,
    icon: Crown,
    color: "amber",
    featureKeys: ["employees", "users", "allPro", "customRoles", "multiAdmin", "api", "integrations", "support247", "manager"]
  }
};

export default function CheckoutPage() {
  const { t, i18n } = useTranslation();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const planId = searchParams.get("plan") || "basic";
  const cartIdFromUrl = searchParams.get("cart") || null;
  const planConfig = PLANS_CONFIG[planId] || PLANS_CONFIG.basic;
  const Icon = planConfig.icon;
  
  const [employeeCount, setEmployeeCount] = useState(5);
  const [email, setEmail] = useState("");
  const [emailError, setEmailError] = useState("");
  const [cartId, setCartId] = useState(cartIdFromUrl);
  const [loading, setLoading] = useState(false);

  const totalMonthly = planConfig.basePrice + (employeeCount * planConfig.pricePerEmployee);

  // Rehydrate cart from URL param (recovery email links back here)
  useEffect(() => {
    if (!cartIdFromUrl) return;
    axios
      .get(`${API}/public/abandoned-carts/${cartIdFromUrl}`)
      .then(({ data }) => {
        if (data?.email) setEmail(data.email);
        if (data?.employee_count) setEmployeeCount(data.employee_count);
      })
      .catch(() => { /* ignore — cart expired or not found */ });
  }, [cartIdFromUrl]);

  const isValidEmail = (v) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);

  // Best-effort cart capture — fires 1.2s after email becomes valid so we
  // don't spam the backend while the user types.
  useEffect(() => {
    if (!isValidEmail(email)) return;
    const timer = setTimeout(async () => {
      try {
        const { data } = await axios.post(`${API}/public/abandoned-carts`, {
          email,
          plan_id: planConfig.id,
          employee_count: employeeCount,
          origin_url: window.location.origin,
          country: (localStorage.getItem("fortexarh-landing-country") || "").toUpperCase() || null,
          language: i18n.language?.split("-")[0] || "es",
        });
        if (data?.cart_id) setCartId(data.cart_id);
      } catch {
        // silent — capture is best-effort
      }
    }, 1200);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [email, employeeCount, planConfig.id]);

  // Get translated plan name
  const planName = t(`checkout.plans.${planId}.name`);

  // Get translated features for the plan
  const getFeatures = () => {
    return planConfig.featureKeys.map(key => t(`checkout.plans.${planId}.features.${key}`));
  };

  const handleCheckout = async () => {
    if (!isValidEmail(email)) {
      setEmailError(t("checkout.errors.invalidEmail", "Ingresa un email válido"));
      return;
    }
    setEmailError("");
    setLoading(true);
    try {
      const response = await axios.post(`${API}/public/checkout`, {
        plan_id: planConfig.id,
        employee_count: employeeCount,
        origin_url: window.location.origin,
        email,
        country: (localStorage.getItem("fortexarh-landing-country") || "").toUpperCase() || null,
        language: i18n.language?.split("-")[0] || "es",
        cart_id: cartId,
      });

      if (response.data.checkout_url) {
        window.location.href = response.data.checkout_url;
      } else {
        toast.error(t("checkout.errors.paymentError"));
      }
    } catch (error) {
      console.error("Checkout error:", error);
      toast.error(error.response?.data?.detail || t("checkout.errors.processError"));
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
              {t("checkout.header.backToPlans")}
            </Button>
          </Link>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-12">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-slate-900 mb-2">{t("checkout.title")}</h1>
          <p className="text-slate-600">{t("checkout.subtitle")}</p>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Plan Summary */}
          <Card className="h-fit">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center bg-gradient-to-br ${
                  planConfig.color === 'blue' ? 'from-blue-500 to-blue-600' :
                  planConfig.color === 'purple' ? 'from-purple-500 to-purple-600' :
                  'from-amber-500 to-amber-600'
                } text-white`}>
                  <Icon className="w-6 h-6" />
                </div>
                <div>
                  <CardTitle>{planName}</CardTitle>
                  {planConfig.popular && <Badge className="bg-purple-500 mt-1">{t("checkout.mostPopular")}</Badge>}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 mb-6">
                {getFeatures().map((feature, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-sm">
                    <Check className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                    <span className="text-slate-600">{feature}</span>
                  </div>
                ))}
              </div>

              <div className="border-t pt-4">
                <div className="flex justify-between text-sm text-slate-500 mb-1">
                  <span>{t("checkout.pricing.baseMonthly")}</span>
                  <span>{formatCurrency(planConfig.basePrice)}</span>
                </div>
                <div className="flex justify-between text-sm text-slate-500">
                  <span>{t("checkout.pricing.perEmployee")}</span>
                  <span>{formatCurrency(planConfig.pricePerEmployee)}</span>
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
                  {t("checkout.employeeCount.title")}
                </CardTitle>
                <CardDescription>
                  {t("checkout.employeeCount.description")}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center gap-4">
                    <Input 
                      type="number" 
                      value={employeeCount}
                      onChange={(e) => setEmployeeCount(Math.max(1, Math.min(planConfig.maxEmployees === 9999 ? 1000 : planConfig.maxEmployees, parseInt(e.target.value) || 1)))}
                      min={1}
                      max={planConfig.maxEmployees === 9999 ? 1000 : planConfig.maxEmployees}
                      className="w-24 text-center text-lg font-bold"
                    />
                    <Slider
                      value={[employeeCount]}
                      onValueChange={(v) => setEmployeeCount(v[0])}
                      min={1}
                      max={planConfig.maxEmployees === 9999 ? 100 : planConfig.maxEmployees}
                      step={1}
                      className="flex-1"
                    />
                  </div>
                  <p className="text-sm text-slate-500">
                    {planConfig.maxEmployees === 9999 
                      ? t("checkout.employeeCount.noLimit")
                      : t("checkout.employeeCount.maxInPlan", { max: planConfig.maxEmployees })}
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gradient-to-br from-emerald-50 to-white border-emerald-200">
              <CardHeader>
                <CardTitle className="text-emerald-800">{t("checkout.paymentSummary.title")}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-slate-600">{t("checkout.paymentSummary.plan", { name: planName })}</span>
                    <span className="font-medium">{formatCurrency(planConfig.basePrice)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">{t("checkout.paymentSummary.employees", { count: employeeCount, price: formatCurrency(planConfig.pricePerEmployee) })}</span>
                    <span className="font-medium">{formatCurrency(employeeCount * planConfig.pricePerEmployee)}</span>
                  </div>
                  <div className="border-t border-emerald-200 pt-3 mt-3">
                    <div className="flex justify-between items-center">
                      <span className="text-lg font-semibold text-slate-800">{t("checkout.paymentSummary.totalMonthly")}</span>
                      <span className="text-2xl font-bold text-emerald-600">{formatCurrency(totalMonthly)}</span>
                    </div>
                  </div>
                </div>

                {/* Email capture — required before Stripe, also feeds abandoned-cart recovery */}
                <div className="mt-5 space-y-2">
                  <Label htmlFor="checkout-email" className="flex items-center gap-2 text-slate-700 font-semibold">
                    <Mail className="w-4 h-4" />
                    {t("checkout.email.label", "Tu email")}
                  </Label>
                  <Input
                    id="checkout-email"
                    type="email"
                    autoComplete="email"
                    required
                    placeholder={t("checkout.email.placeholder", "tu@empresa.com")}
                    value={email}
                    onChange={(e) => { setEmail(e.target.value); if (emailError) setEmailError(""); }}
                    className={emailError ? "border-rose-400" : ""}
                    data-testid="checkout-email-input"
                  />
                  {emailError ? (
                    <p className="text-xs text-rose-600" data-testid="checkout-email-error">{emailError}</p>
                  ) : (
                    <p className="text-xs text-slate-500">
                      {t("checkout.email.hint", "Lo usaremos para enviarte la factura y acceder a tu cuenta después del pago.")}
                    </p>
                  )}
                </div>

                <Button 
                  className="w-full mt-6 h-12 text-lg bg-emerald-600 hover:bg-emerald-700"
                  onClick={handleCheckout}
                  disabled={loading || !isValidEmail(email)}
                  data-testid="proceed-to-payment-btn"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                      {t("checkout.buttons.processing")}
                    </>
                  ) : (
                    <>
                      <CreditCard className="w-5 h-5 mr-2" />
                      {t("checkout.buttons.proceedToPayment")}
                    </>
                  )}
                </Button>

                <div className="mt-4 text-center">
                  <p className="text-xs text-slate-500">
                    {t("checkout.footer.securePayment")}
                  </p>
                </div>
              </CardContent>
            </Card>

            <div className="text-center">
              <p className="text-sm text-slate-500">
                {t("checkout.footer.tryFirst")}{" "}
                <Link to="/register" className="text-blue-600 hover:underline">
                  {t("checkout.footer.freeTrial")}
                </Link>
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
