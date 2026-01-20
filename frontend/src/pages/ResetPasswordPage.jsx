import { useState, useEffect } from "react";
import { Link, useSearchParams, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Lock, ArrowLeft, CheckCircle, AlertCircle, Eye, EyeOff } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";
import { API } from "@/App";

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get("token");
  
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) {
      setError("Token no válido. Solicita un nuevo enlace de recuperación.");
    }
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    
    if (password.length < 6) {
      setError("La contraseña debe tener al menos 6 caracteres");
      return;
    }
    
    if (password !== confirmPassword) {
      setError("Las contraseñas no coinciden");
      return;
    }
    
    setLoading(true);

    try {
      await axios.post(`${API}/auth/reset-password`, {
        token,
        new_password: password
      });
      setSuccess(true);
      toast.success("Contraseña actualizada correctamente");
    } catch (err) {
      const message = err.response?.data?.detail || "Error al restablecer la contraseña";
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <Link to="/" className="inline-block mb-4">
              <img 
                src="/fortexarh-logo.png" 
                alt="FortexaRH" 
                className="h-16 w-auto mx-auto"
              />
            </Link>
          </div>

          <Card className="shadow-lg border-slate-200">
            <CardHeader className="text-center">
              <div className="mx-auto w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mb-4">
                <CheckCircle className="w-8 h-8 text-emerald-600" />
              </div>
              <CardTitle className="text-2xl heading">Contraseña Actualizada</CardTitle>
              <CardDescription>
                Tu contraseña ha sido actualizada correctamente
              </CardDescription>
            </CardHeader>
            <CardContent className="text-center">
              <Button 
                onClick={() => navigate("/login")}
                className="bg-emerald-600 hover:bg-emerald-700"
                data-testid="go-to-login-btn"
              >
                Iniciar Sesión
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link to="/" className="inline-block mb-4">
            <img 
              src="/fortexarh-logo.png" 
              alt="FortexaRH" 
              className="h-16 w-auto mx-auto"
            />
          </Link>
        </div>

        <Card className="shadow-lg border-slate-200">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl heading">Nueva Contraseña</CardTitle>
            <CardDescription>
              Ingresa tu nueva contraseña
            </CardDescription>
          </CardHeader>
          <CardContent>
            {error && !token && (
              <div className="flex items-center gap-2 p-3 bg-red-50 text-red-700 rounded-lg text-sm mb-4">
                <AlertCircle className="w-4 h-4" />
                {error}
              </div>
            )}
            
            {token && (
              <form onSubmit={handleSubmit} className="space-y-4">
                {error && (
                  <div className="flex items-center gap-2 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
                    <AlertCircle className="w-4 h-4" />
                    {error}
                  </div>
                )}
                
                <div className="space-y-2">
                  <Label htmlFor="password">Nueva Contraseña</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                    <Input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      placeholder="Mínimo 6 caracteres"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="pl-10 pr-10"
                      required
                      minLength={6}
                      data-testid="new-password-input"
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
                      type={showPassword ? "text" : "password"}
                      placeholder="Repite la contraseña"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="pl-10"
                      required
                      data-testid="confirm-password-input"
                    />
                  </div>
                </div>

                <Button 
                  type="submit" 
                  className="w-full bg-emerald-600 hover:bg-emerald-700" 
                  disabled={loading}
                  data-testid="reset-submit-btn"
                >
                  {loading ? "Actualizando..." : "Actualizar Contraseña"}
                </Button>
              </form>
            )}
          </CardContent>
          <CardFooter className="justify-center">
            <Link 
              to="/login" 
              className="flex items-center gap-2 text-sm text-slate-600 hover:text-slate-800"
            >
              <ArrowLeft className="w-4 h-4" />
              Volver al inicio de sesión
            </Link>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
}
