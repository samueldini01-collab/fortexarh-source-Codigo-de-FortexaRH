import { useState, useRef, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { ShieldCheck, ArrowLeft, KeyRound } from "lucide-react";
import axios from "axios";
import { API } from "@/App";

export default function TwoFactorLogin({ userId, tempToken, onVerified, onBack }) {
  const { t } = useTranslation();
  const [code, setCode] = useState(["", "", "", "", "", ""]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [useRecovery, setUseRecovery] = useState(false);
  const [recoveryCode, setRecoveryCode] = useState("");
  const [rememberDevice, setRememberDevice] = useState(false);
  const inputRefs = useRef([]);

  useEffect(() => {
    if (!useRecovery) inputRefs.current[0]?.focus();
  }, [useRecovery]);

  const handleChange = (index, value) => {
    if (!/^\d*$/.test(value)) return;
    const newCode = [...code];
    newCode[index] = value.slice(-1);
    setCode(newCode);
    setError("");

    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }

    if (value && index === 5) {
      const fullCode = [...newCode.slice(0, 5), value.slice(-1)].join("");
      if (fullCode.length === 6) handleSubmit(fullCode);
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === "Backspace" && !code[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
    const newCode = [...code];
    for (let i = 0; i < pasted.length; i++) {
      newCode[i] = pasted[i];
    }
    setCode(newCode);
    if (pasted.length === 6) {
      handleSubmit(pasted);
    } else {
      inputRefs.current[Math.min(pasted.length, 5)]?.focus();
    }
  };

  const handleSubmit = async (fullCode) => {
    const codeStr = fullCode || code.join("");
    if (codeStr.length !== 6) {
      setError(t("auth.twoFactor.enterCode"));
      return;
    }
    setLoading(true);
    setError("");
    try {
      await onVerified(userId, tempToken, codeStr, rememberDevice);
    } catch (err) {
      setError(err?.response?.data?.detail || t("auth.twoFactor.invalidCode"));
      setCode(["", "", "", "", "", ""]);
      inputRefs.current[0]?.focus();
    } finally {
      setLoading(false);
    }
  };

  const handleRecoverySubmit = async (e) => {
    e.preventDefault();
    const trimmed = recoveryCode.trim().toUpperCase();
    if (!trimmed || trimmed.length < 4) {
      setError(t("auth.twoFactor.recovery.enterCode"));
      return;
    }
    setLoading(true);
    setError("");
    try {
      const response = await axios.post(`${API}/auth/2fa/verify-recovery`, {
        user_id: userId,
        temp_token: tempToken,
        recovery_code: trimmed,
        remember_device: rememberDevice,
      });
      const { token, user: userData, trusted_device: trusted } = response.data;
      localStorage.setItem("token", token);
      localStorage.setItem("user", JSON.stringify(userData));
      if (trusted?.device_token) {
        localStorage.setItem("fortexa_device_token", trusted.device_token);
      }
      window.location.href = userData?.is_partner ? "/partner-dashboard" : "/dashboard";
    } catch (err) {
      setError(err?.response?.data?.detail || t("auth.twoFactor.recovery.invalidCode"));
      setRecoveryCode("");
    } finally {
      setLoading(false);
    }
  };

  const switchToRecovery = () => {
    setUseRecovery(true);
    setError("");
    setRecoveryCode("");
  };

  const switchToTotp = () => {
    setUseRecovery(false);
    setError("");
    setCode(["", "", "", "", "", ""]);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-100 dark:bg-emerald-900/40 mb-4">
            {useRecovery
              ? <KeyRound className="w-8 h-8 text-emerald-600 dark:text-emerald-400" />
              : <ShieldCheck className="w-8 h-8 text-emerald-600 dark:text-emerald-400" />
            }
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            {useRecovery ? t("auth.twoFactor.recovery.title") : t("auth.twoFactor.title")}
          </h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            {useRecovery ? t("auth.twoFactor.recovery.subtitle") : t("auth.twoFactor.subtitle")}
          </p>
        </div>

        <Card className="shadow-lg border-slate-200 dark:border-slate-700">
          <CardHeader className="text-center pb-2">
            <CardTitle className="text-lg">
              {useRecovery ? t("auth.twoFactor.recovery.enterCodeTitle") : t("auth.twoFactor.enterCodeTitle")}
            </CardTitle>
            <CardDescription>
              {useRecovery ? t("auth.twoFactor.recovery.enterCodeDesc") : t("auth.twoFactor.enterCodeDesc")}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {useRecovery ? (
              <form onSubmit={handleRecoverySubmit} className="space-y-6">
                <Input
                  type="text"
                  value={recoveryCode}
                  onChange={(e) => { setRecoveryCode(e.target.value.toUpperCase()); setError(""); }}
                  placeholder="XXXXXXXX"
                  className="font-mono text-center text-lg tracking-widest uppercase"
                  maxLength={8}
                  autoFocus
                  data-testid="recovery-code-input"
                />

                {error && (
                  <p className="text-sm text-red-600 text-center" data-testid="2fa-error">{error}</p>
                )}

                <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300 cursor-pointer select-none">
                  <Checkbox
                    checked={rememberDevice}
                    onCheckedChange={(v) => setRememberDevice(!!v)}
                    data-testid="remember-device-recovery"
                  />
                  {t("auth.twoFactor.rememberDevice")}
                </label>

                <Button
                  type="submit"
                  className="w-full bg-emerald-600 hover:bg-emerald-700"
                  disabled={loading || recoveryCode.trim().length < 4}
                  data-testid="recovery-verify-btn"
                >
                  {loading ? t("common.loading") : t("auth.twoFactor.verify")}
                </Button>

                <Button
                  type="button"
                  variant="ghost"
                  className="w-full text-slate-500"
                  onClick={switchToTotp}
                  data-testid="switch-to-totp-btn"
                >
                  <ShieldCheck className="w-4 h-4 mr-2" />
                  {t("auth.twoFactor.recovery.useAuthApp")}
                </Button>

                <Button
                  type="button"
                  variant="ghost"
                  className="w-full text-slate-500"
                  onClick={onBack}
                  data-testid="2fa-back-btn"
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  {t("auth.twoFactor.backToLogin")}
                </Button>
              </form>
            ) : (
              <form onSubmit={(e) => { e.preventDefault(); handleSubmit(); }} className="space-y-6">
                <div className="flex justify-center gap-2" data-testid="2fa-code-inputs">
                  {code.map((digit, i) => (
                    <Input
                      key={i}
                      ref={(el) => (inputRefs.current[i] = el)}
                      type="text"
                      inputMode="numeric"
                      maxLength={1}
                      value={digit}
                      onChange={(e) => handleChange(i, e.target.value)}
                      onKeyDown={(e) => handleKeyDown(i, e)}
                      onPaste={i === 0 ? handlePaste : undefined}
                      className="w-12 h-14 text-center text-xl font-mono font-bold border-2 focus:border-emerald-500 focus:ring-emerald-500"
                      data-testid={`2fa-digit-${i}`}
                    />
                  ))}
                </div>

                {error && (
                  <p className="text-sm text-red-600 text-center" data-testid="2fa-error">{error}</p>
                )}

                <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300 cursor-pointer select-none">
                  <Checkbox
                    checked={rememberDevice}
                    onCheckedChange={(v) => setRememberDevice(!!v)}
                    data-testid="remember-device-totp"
                  />
                  {t("auth.twoFactor.rememberDevice")}
                </label>

                <Button
                  type="submit"
                  className="w-full bg-emerald-600 hover:bg-emerald-700"
                  disabled={loading || code.join("").length !== 6}
                  data-testid="2fa-verify-btn"
                >
                  {loading ? t("common.loading") : t("auth.twoFactor.verify")}
                </Button>

                <Button
                  type="button"
                  variant="ghost"
                  className="w-full text-slate-500"
                  onClick={switchToRecovery}
                  data-testid="switch-to-recovery-btn"
                >
                  <KeyRound className="w-4 h-4 mr-2" />
                  {t("auth.twoFactor.recovery.useRecoveryCode")}
                </Button>

                <Button
                  type="button"
                  variant="ghost"
                  className="w-full text-slate-500"
                  onClick={onBack}
                  data-testid="2fa-back-btn"
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  {t("auth.twoFactor.backToLogin")}
                </Button>
              </form>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
