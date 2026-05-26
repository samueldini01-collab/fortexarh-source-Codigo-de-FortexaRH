import { useState, useEffect, useCallback } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Users, Mail, Lock, User, Building2, AlertCircle, Check, CheckCircle2, Loader2, CreditCard, Eye, EyeOff } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";

export default function RegisterPage() {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get("session_id");
  const paymentStatus = searchParams.get("payment");
  const planFromUrl = searchParams.get("plan");
  const _employeesFromUrl = searchParams.get("employees");
  
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
    company_name: ""
  });
  const [loading, setLoading] = useState(false);
  const [verifyingPayment, setVerifyingPayment] = useState(false);
  const [paymentVerified, setPaymentVerified] = useState(false);
  const [paymentInfo, setPaymentInfo] = useState(null);
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const verifyPayment = useCallback(async () => {
    setVerifyingPayment(true);
    try {
      const response = await axios.get(`${API}/public/checkout/verify/${sessionId}`);
      if (response.data.valid && response.data.payment_status === "paid") {
        setPaymentVerified(true);
        setPaymentInfo(response.data);
        toast.success(t("auth.register.paymentVerifiedMsg"));
      } else {
        toast.error(t("auth.register.paymentNotConfirmed"));
      }
    } catch (err) {
      console.error("Error verifying payment:", err);
      toast.error(err.response?.data?.detail || t("auth.register.errorVerifyingPayment"));
    } finally {
      setVerifyingPayment(false);
    }
  }, [sessionId, t]);

  // Verify payment on mount if session_id is present
  useEffect(() => {
    if (sessionId && paymentStatus === "success") {
      verifyPayment();
    }
  }, [sessionId, paymentStatus, verifyPayment]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (formData.password !== formData.confirmPassword) {
      setError(t("auth.register.passwordsNotMatch"));
      return;
    }

    if (formData.password.length < 6) {
      setError(t("auth.register.passwordTooShort"));
      return;
    }

    setLoading(true);

    try {
      // Include payment_session_id if this is a paid registration
      const registrationData = {
        email: formData.email,
        password: formData.password,
        name: formData.name,
        company_name: formData.company_name
      };
      
      if (paymentVerified && sessionId) {
        registrationData.payment_session_id = sessionId;
      }
      
      await register(
        registrationData.email, 
        registrationData.password, 
        registrationData.name, 
        registrationData.company_name,
        registrationData.payment_session_id
      );
      
      if (paymentVerified) {
        toast.success(t("auth.register.accountCreatedPaid"));
      } else {
        toast.success(t("auth.register.accountCreated"));
      }
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.detail || t("auth.register.errorCreating"));
      toast.error(t("auth.register.errorCreating"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4 py-8">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link to="/" className="inline-block mb-2">
            <img 
              src="https://customer-assets.emergentagent.com/job_hrpulse-26/artifacts/ohljcqui_FortexaRH%20Logo.png" 
              alt="FortexaRH" 
              className="h-24 w-auto mx-auto"
            />
          </Link>
          <p className="text-sm text-slate-500">Sistema de RRHH y Nómina</p>
        </div>

        {/* Payment Verification Loading */}
        {verifyingPayment && (
          <Card className="shadow-lg border-blue-200 bg-blue-50 mb-4">
            <CardContent className="py-6 text-center">
              <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-3" />
              <p className="text-blue-700 font-medium">{t("auth.register.paymentVerifying")}</p>
            </CardContent>
          </Card>
        )}

        {/* Payment Verified Badge */}
        {paymentVerified && paymentInfo && (
          <Card className="shadow-lg border-emerald-200 bg-emerald-50 mb-4">
            <CardContent className="py-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center">
                  <CheckCircle2 className="w-6 h-6 text-emerald-600" />
                </div>
                <div className="flex-1">
                  <p className="font-semibold text-emerald-800">{t("auth.register.paymentVerified")}</p>
                  <p className="text-sm text-emerald-600">
                    Plan: {paymentInfo.plan_name} • {paymentInfo.employee_count} empleados • ${paymentInfo.amount}/mes
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        <Card className="shadow-lg border-slate-200">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl heading">
              {paymentVerified ? t("auth.register.completeTitle") : t("auth.register.title")}
            </CardTitle>
            <CardDescription>
              {paymentVerified 
                ? t("auth.register.subtitlePaid") 
                : t("auth.register.subtitle")
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="flex items-center gap-2 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
                  <AlertCircle className="w-4 h-4" />
                  {error}
                </div>
              )}
              
              <div className="space-y-2">
                <Label htmlFor="name">{t("auth.register.fullName")}</Label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <Input
                    id="name"
                    name="name"
                    type="text"
                    placeholder={t("auth.register.fullNamePlaceholder")}
                    value={formData.name}
                    onChange={handleChange}
                    className="pl-10"
                    required
                    data-testid="name-input"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">{t("auth.register.email")}</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    placeholder={t("auth.register.emailPlaceholder")}
                    value={formData.email}
                    onChange={handleChange}
                    className="pl-10"
                    required
                    data-testid="email-input"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="company_name">{t("auth.register.companyName")}</Label>
                <div className="relative">
                  <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <Input
                    id="company_name"
                    name="company_name"
                    type="text"
                    placeholder={t("auth.register.companyPlaceholder")}
                    value={formData.company_name}
                    onChange={handleChange}
                    className="pl-10"
                    required
                    data-testid="company-input"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">{t("auth.register.password")}</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <Input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    value={formData.password}
                    onChange={handleChange}
                    className="pl-10 pr-10"
                    required
                    data-testid="password-input"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirmPassword">{t("auth.register.confirmPassword")}</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <Input
                    id="confirmPassword"
                    name="confirmPassword"
                    type={showConfirmPassword ? "text" : "password"}
                    placeholder="••••••••"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    className="pl-10 pr-10"
                    required
                    data-testid="confirm-password-input"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  >
                    {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              <Button 
                type="submit" 
                className="w-full bg-slate-900 hover:bg-slate-800" 
                disabled={loading}
                data-testid="register-submit-btn"
              >
                {loading ? t("auth.register.creating") : t("auth.register.submit")}
              </Button>
            </form>

            <div className="mt-6 space-y-2">
              <div className="flex items-center gap-2 text-sm text-slate-600">
                <Check className="w-4 h-4 text-emerald-500" />
                {t("auth.register.benefits.freeTrial")}
              </div>
              <div className="flex items-center gap-2 text-sm text-slate-600">
                <Check className="w-4 h-4 text-emerald-500" />
                {t("auth.register.benefits.noCard")}
              </div>
              <div className="flex items-center gap-2 text-sm text-slate-600">
                <Check className="w-4 h-4 text-emerald-500" />
                {t("auth.register.benefits.freeEmployees")}
              </div>
            </div>
          </CardContent>
          <CardFooter className="justify-center">
            <p className="text-sm text-slate-600">
              {t("auth.register.hasAccount")}{" "}
              <Link to="/login" className="text-emerald-600 hover:text-emerald-700 font-medium">
                {t("auth.register.login")}
              </Link>
            </p>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
}
