import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Eye, EyeOff, Loader2, Lock } from "lucide-react";
import { toast } from "sonner";
import { useEmployeeAuth } from "./EmployeeAuthContext";
import LanguageSelector from "@/components/LanguageSelector";

const LOGO_URL = "https://customer-assets.emergentagent.com/job_hrpulse-26/artifacts/ohljcqui_FortexaRH%20Logo.png";

export function EmployeeLogin() {
  const { t } = useTranslation();
  const { login } = useEmployeeAuth();
  const [documentNumber, setDocumentNumber] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(documentNumber, password);
      toast.success(t('employeePortal.welcomeToPortal'));
    } catch (error) {
      toast.error(error.response?.data?.detail || t('employeePortal.login.errorLogin'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center p-4 relative">
      {/* Language Selector - top right */}
      <div className="absolute top-4 right-4 z-20" data-testid="portal-login-lang-switcher">
        <LanguageSelector variant="landing" />
      </div>

      <Card className="w-full max-w-md" data-testid="employee-login-card">
        <CardHeader className="text-center">
          <div className="flex flex-col items-center mb-4">
            <img src={LOGO_URL} alt="FortexaRH Logo" className="h-20 w-auto object-contain" />
            <p className="text-sm text-slate-500 mt-2">{t('employeePortal.hrSystem')}</p>
          </div>
          <CardTitle className="text-2xl">{t('employeePortal.login.title')}</CardTitle>
          <CardDescription>{t('employeePortal.login.subtitle')}</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-2">
              <Label>{t('employeePortal.login.documentNumber')}</Label>
              <Input
                value={documentNumber}
                onChange={(e) => setDocumentNumber(e.target.value)}
                placeholder={t('employeePortal.login.documentPlaceholder')}
                required
                data-testid="employee-login-document"
              />
            </div>
            <div className="space-y-2">
              <Label>{t('employeePortal.login.password')}</Label>
              <div className="relative">
                <Input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={t('employeePortal.login.passwordPlaceholder')}
                  className="pr-10"
                  required
                  data-testid="employee-login-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              <p className="text-xs text-slate-500">{t('employeePortal.login.firstTimeHint')}</p>
            </div>
            <Button type="submit" className="w-full" disabled={loading} data-testid="employee-login-submit">
              {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Lock className="w-4 h-4 mr-2" />}
              {t('employeePortal.login.loginButton')}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
