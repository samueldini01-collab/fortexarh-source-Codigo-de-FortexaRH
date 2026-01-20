import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Mail, ArrowLeft, CheckCircle } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";
import { API } from "@/App";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await axios.post(`${API}/auth/forgot-password`, { email });
      setSent(true);
      toast.success("Revisa tu correo electrónico");
    } catch (err) {
      toast.error("Error al procesar la solicitud");
    } finally {
      setLoading(false);
    }
  };

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
          {!sent ? (
            <>
              <CardHeader className="text-center">
                <CardTitle className="text-2xl heading">Recuperar Contraseña</CardTitle>
                <CardDescription>
                  Ingresa tu correo electrónico y te enviaremos instrucciones para restablecer tu contraseña
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="email">Correo Electrónico</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                      <Input
                        id="email"
                        type="email"
                        placeholder="tu@email.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="pl-10"
                        required
                        data-testid="forgot-email-input"
                      />
                    </div>
                  </div>

                  <Button 
                    type="submit" 
                    className="w-full bg-emerald-600 hover:bg-emerald-700" 
                    disabled={loading}
                    data-testid="forgot-submit-btn"
                  >
                    {loading ? "Enviando..." : "Enviar Instrucciones"}
                  </Button>
                </form>
              </CardContent>
            </>
          ) : (
            <>
              <CardHeader className="text-center">
                <div className="mx-auto w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mb-4">
                  <CheckCircle className="w-8 h-8 text-emerald-600" />
                </div>
                <CardTitle className="text-2xl heading">Correo Enviado</CardTitle>
                <CardDescription>
                  Si el correo está registrado, recibirás un enlace para restablecer tu contraseña
                </CardDescription>
              </CardHeader>
              <CardContent className="text-center space-y-4">
                <p className="text-sm text-slate-600">
                  Revisa tu bandeja de entrada y sigue las instrucciones del correo.
                </p>
                <p className="text-sm text-slate-500">
                  ¿No recibiste el correo? Revisa tu carpeta de spam o{" "}
                  <button 
                    onClick={() => setSent(false)}
                    className="text-emerald-600 hover:text-emerald-700 font-medium"
                  >
                    intenta de nuevo
                  </button>
                </p>
              </CardContent>
            </>
          )}
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
