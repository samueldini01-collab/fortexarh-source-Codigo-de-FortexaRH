import { useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { API } from "@/App";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Mail, ArrowLeft, CheckCircle2, Loader2 } from "lucide-react";
import { toast } from "sonner";

export default function ForgotPasswordPage() {
  const { t } = useTranslation();
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await axios.post(`${API}/auth/forgot-password`, { email });
      setSent(true);
      toast.success(t("auth.forgotPassword.successToast"));
    } catch (err) {
      console.error("Error:", err);
      // Still show success to prevent email enumeration
      setSent(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
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

        <Card className="shadow-lg border-slate-200">
          {sent ? (
            <>
              <CardHeader className="text-center">
                <div className="w-16 h-16 rounded-full bg-emerald-100 mx-auto mb-4 flex items-center justify-center">
                  <CheckCircle2 className="w-8 h-8 text-emerald-600" />
                </div>
                <CardTitle className="text-2xl heading">{t("auth.forgotPassword.sentTitle")}</CardTitle>
                <CardDescription>
                  {t("auth.forgotPassword.sentMessage")}
                </CardDescription>
              </CardHeader>
              <CardContent className="text-center">
                <p className="text-sm text-slate-600 mb-6">
                  {t("auth.forgotPassword.checkInbox")}
                </p>
                <p className="text-sm text-slate-500">
                  {t("auth.forgotPassword.notReceived")}{" "}
                  <button 
                    onClick={() => setSent(false)}
                    className="text-emerald-600 hover:text-emerald-700 font-medium"
                  >
                    {t("auth.forgotPassword.tryAgain")}
                  </button>
                </p>
              </CardContent>
            </>
          ) : (
            <>
              <CardHeader className="text-center">
                <CardTitle className="text-2xl heading">{t("auth.forgotPassword.title")}</CardTitle>
                <CardDescription>
                  {t("auth.forgotPassword.subtitle")}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="email">{t("auth.forgotPassword.email")}</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                      <Input
                        id="email"
                        type="email"
                        placeholder={t("auth.forgotPassword.emailPlaceholder")}
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
                    className="w-full bg-slate-900 hover:bg-slate-800" 
                    disabled={loading}
                    data-testid="forgot-submit-btn"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        {t("auth.forgotPassword.sending")}
                      </>
                    ) : (
                      t("auth.forgotPassword.submit")
                    )}
                  </Button>
                </form>
              </CardContent>
            </>
          )}
          <CardFooter className="justify-center">
            <Link 
              to="/login" 
              className="inline-flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900"
            >
              <ArrowLeft className="w-4 h-4" />
              {t("auth.forgotPassword.backToLogin")}
            </Link>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
}
