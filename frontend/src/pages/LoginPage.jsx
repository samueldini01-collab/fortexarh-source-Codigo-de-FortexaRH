import { useState, useEffect, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth, API } from "@/App";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Mail, Lock, AlertCircle, Eye, EyeOff, Briefcase } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";
import LanguageSelector from "@/components/LanguageSelector";
import TwoFactorLogin from "@/components/TwoFactorLogin";

export default function LoginPage() {
  const { t } = useTranslation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [partnerInfo, setPartnerInfo] = useState(null);
  const [twoFactorData, setTwoFactorData] = useState(null);
  const { login } = useAuth();
  const navigate = useNavigate();
  const debounceRef = useRef(null);

  // Debounced partner check when email changes
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);

    // Only check if email looks valid
    if (!email || !email.includes("@") || !email.includes(".")) {
      setPartnerInfo(null);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      try {
        const res = await axios.post(`${API}/auth/check-partner`, { email });
        if (res.data.is_partner) {
          setPartnerInfo({ firm_name: res.data.firm_name });
        } else {
          setPartnerInfo(null);
        }
      } catch {
        setPartnerInfo(null);
      }
    }, 600);

    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [email]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      
      // Check if 2FA is required
      if (response.data.requires_2fa) {
        setTwoFactorData({
          user_id: response.data.user_id,
          temp_token: response.data.temp_token
        });
        setLoading(false);
        return;
      }

      // Normal login (no 2FA)
      const { token, user: userData } = response.data;
      localStorage.setItem("token", token);
      localStorage.setItem("user", JSON.stringify(userData));
      window.location.href = userData?.is_partner ? "/partner-dashboard" : "/dashboard";
    } catch (err) {
      setError(err.response?.data?.detail || t('errors.generic'));
      toast.error(t('errors.generic'));
    } finally {
      setLoading(false);
    }
  };

  const handle2FAVerified = async (userId, tempToken, code) => {
    const response = await axios.post(`${API}/auth/2fa/verify-login`, {
      user_id: userId,
      temp_token: tempToken,
      code
    });
    const { token, user: userData } = response.data;
    localStorage.setItem("token", token);
    localStorage.setItem("user", JSON.stringify(userData));
    toast.success(t('common.welcome') + "!");
    window.location.href = userData?.is_partner ? "/partner-dashboard" : "/dashboard";
  };

  // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
  const handleGoogleLogin = () => {
    const redirectUrl = window.location.origin + "/dashboard";
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  // If 2FA is required, show the verification screen
  if (twoFactorData) {
    return (
      <TwoFactorLogin
        userId={twoFactorData.user_id}
        tempToken={twoFactorData.temp_token}
        onVerified={handle2FAVerified}
        onBack={() => setTwoFactorData(null)}
      />
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link to="/" className="inline-block mb-2">
            <img 
              src="https://customer-assets.emergentagent.com/job_hrpulse-26/artifacts/ohljcqui_FortexaRH%20Logo.png" 
              alt="FortexaRH" 
              className="h-32 w-auto mx-auto"
            />
          </Link>
          <p className="text-sm text-slate-500">{t('landing.footer.tagline')}</p>
        </div>

        {/* Partner welcome banner */}
        {partnerInfo && (
          <div
            className="mb-4 flex items-center gap-3 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 animate-in fade-in slide-in-from-top-2 duration-300"
            data-testid="partner-welcome-banner"
          >
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-emerald-100">
              <Briefcase className="h-5 w-5 text-emerald-600" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-emerald-800" data-testid="partner-banner-title">
                {t('auth.login.partnerPortal')}
              </p>
              {partnerInfo.firm_name && (
                <p className="text-xs text-emerald-600 truncate" data-testid="partner-banner-firm">
                  {partnerInfo.firm_name}
                </p>
              )}
            </div>
          </div>
        )}

        <Card className="shadow-lg border-slate-200">
          <CardHeader className="text-center">
            <div className="flex justify-end mb-2">
              <LanguageSelector variant="compact" />
            </div>
            <CardTitle className="text-2xl heading">{t('auth.login.title')}</CardTitle>
            <CardDescription>
              {partnerInfo ? t('auth.login.partnerSubtitle') : t('auth.login.subtitle')}
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
                <Label htmlFor="email">{t('auth.login.email')}</Label>
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
                    data-testid="email-input"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password">{t('auth.login.password')}</Label>
                  <Link 
                    to="/forgot-password" 
                    className="text-sm text-emerald-600 hover:text-emerald-700"
                    data-testid="forgot-password-link"
                  >
                    {t('auth.login.forgotPassword')}
                  </Link>
                </div>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="pl-10 pr-10"
                    required
                    data-testid="password-input"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                    data-testid="toggle-password-visibility"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              <Button 
                type="submit" 
                className={`w-full ${partnerInfo ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-slate-900 hover:bg-slate-800'}`}
                disabled={loading}
                data-testid="login-submit-btn"
              >
                {loading
                  ? t('common.loading')
                  : partnerInfo
                    ? t('auth.login.partnerSubmit')
                    : t('auth.login.submit')
                }
              </Button>
            </form>

            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-200"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-slate-500">{t('auth.login.orContinueWith')}</span>
              </div>
            </div>

            <Button 
              type="button" 
              variant="outline" 
              className="w-full" 
              onClick={handleGoogleLogin}
              data-testid="google-login-btn"
            >
              <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              {t('auth.login.googleLogin')}
            </Button>
          </CardContent>
          <CardFooter className="justify-center">
            <p className="text-sm text-slate-600">
              {t('auth.login.noAccount')}{" "}
              <Link to="/register" className="text-emerald-600 hover:text-emerald-700 font-medium">
                {t('auth.login.createAccount')}
              </Link>
            </p>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
}
