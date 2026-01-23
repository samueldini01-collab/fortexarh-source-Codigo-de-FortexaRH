import { useState, useEffect, useCallback } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
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
        toast.success("¡Pago verificado! Complete su registro para activar su cuenta.");
      } else {
        toast.error("El pago aún no ha sido confirmado. Intente nuevamente.");
      }
    } catch (err) {
      console.error("Error verifying payment:", err);
      toast.error(err.response?.data?.detail || "Error al verificar el pago");
    } finally {
      setVerifyingPayment(false);
    }
  }, [sessionId]);

  // Verify payment on mount if session_id is present
  useEffect(() => {
    if (sessionId && paymentStatus === "success") {
      verifyPayment();
    }
  }, [sessionId, paymentStatus, verifyPayment]);
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (formData.password !== formData.confirmPassword) {
      setError("Las contraseñas no coinciden");
      return;
    }

    if (formData.password.length < 6) {
      setError("La contraseña debe tener al menos 6 caracteres");
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
        toast.success("¡Cuenta creada y plan activado exitosamente!");
      } else {
        toast.success("¡Cuenta creada exitosamente!");
      }
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.detail || "Error al crear la cuenta");
      toast.error("Error al registrarse");
    } finally {
      setLoading(false);
    }
  };

  // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
  const handleGoogleSignup = () => {
    const redirectUrl = window.location.origin + "/dashboard";
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4 py-8">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link to="/" className="inline-block mb-4">
            <img 
              src="/favicon.png" 
              alt="FortexaRH" 
              className="h-16 w-auto mx-auto"
            />
          </Link>
        </div>

        {/* Payment Verification Loading */}
        {verifyingPayment && (
          <Card className="shadow-lg border-blue-200 bg-blue-50 mb-4">
            <CardContent className="py-6 text-center">
              <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-3" />
              <p className="text-blue-700 font-medium">Verificando su pago...</p>
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
                  <p className="font-semibold text-emerald-800">¡Pago Verificado!</p>
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
              {paymentVerified ? "Complete su Registro" : "Crear Cuenta"}
            </CardTitle>
            <CardDescription>
              {paymentVerified 
                ? "Ingrese sus datos para activar su cuenta" 
                : "Comienza tu prueba gratuita de 5 días"
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
                <Label htmlFor="name">Nombre Completo</Label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <Input
                    id="name"
                    name="name"
                    type="text"
                    placeholder="Juan Pérez"
                    value={formData.name}
                    onChange={handleChange}
                    className="pl-10"
                    required
                    data-testid="name-input"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">Correo Electrónico</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    placeholder="tu@email.com"
                    value={formData.email}
                    onChange={handleChange}
                    className="pl-10"
                    required
                    data-testid="email-input"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="company_name">Nombre de tu Empresa</Label>
                <div className="relative">
                  <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <Input
                    id="company_name"
                    name="company_name"
                    type="text"
                    placeholder="Mi Empresa S.A."
                    value={formData.company_name}
                    onChange={handleChange}
                    className="pl-10"
                    required
                    data-testid="company-input"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Contraseña</Label>
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
                <Label htmlFor="confirmPassword">Confirmar Contraseña</Label>
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
                {loading ? "Creando cuenta..." : "Crear Cuenta Gratis"}
              </Button>
            </form>

            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-200"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-slate-500">O continúa con</span>
              </div>
            </div>

            <Button 
              type="button" 
              variant="outline" 
              className="w-full" 
              onClick={handleGoogleSignup}
              data-testid="google-signup-btn"
            >
              <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              Registrarse con Google
            </Button>

            <div className="mt-6 space-y-2">
              <div className="flex items-center gap-2 text-sm text-slate-600">
                <Check className="w-4 h-4 text-emerald-500" />
                5 días de prueba gratuita
              </div>
              <div className="flex items-center gap-2 text-sm text-slate-600">
                <Check className="w-4 h-4 text-emerald-500" />
                Sin tarjeta de crédito
              </div>
              <div className="flex items-center gap-2 text-sm text-slate-600">
                <Check className="w-4 h-4 text-emerald-500" />
                Hasta 5 empleados gratis
              </div>
            </div>
          </CardContent>
          <CardFooter className="justify-center">
            <p className="text-sm text-slate-600">
              ¿Ya tienes cuenta?{" "}
              <Link to="/login" className="text-emerald-600 hover:text-emerald-700 font-medium">
                Inicia sesión
              </Link>
            </p>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
}
