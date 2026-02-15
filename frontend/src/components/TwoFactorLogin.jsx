import { useState, useRef, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ShieldCheck, ArrowLeft } from "lucide-react";

export default function TwoFactorLogin({ userId, tempToken, onVerified, onBack }) {
  const { t } = useTranslation();
  const [code, setCode] = useState(["", "", "", "", "", ""]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const inputRefs = useRef([]);

  useEffect(() => {
    inputRefs.current[0]?.focus();
  }, []);

  const handleChange = (index, value) => {
    if (!/^\d*$/.test(value)) return;
    const newCode = [...code];
    newCode[index] = value.slice(-1);
    setCode(newCode);
    setError("");

    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }

    // Auto-submit when all 6 digits filled
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
      await onVerified(userId, tempToken, codeStr);
    } catch (err) {
      setError(err?.response?.data?.detail || t("auth.twoFactor.invalidCode"));
      setCode(["", "", "", "", "", ""]);
      inputRefs.current[0]?.focus();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-100 mb-4">
            <ShieldCheck className="w-8 h-8 text-emerald-600" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900">{t("auth.twoFactor.title")}</h1>
          <p className="text-slate-500 mt-1">{t("auth.twoFactor.subtitle")}</p>
        </div>

        <Card className="shadow-lg border-slate-200">
          <CardHeader className="text-center pb-2">
            <CardTitle className="text-lg">{t("auth.twoFactor.enterCodeTitle")}</CardTitle>
            <CardDescription>{t("auth.twoFactor.enterCodeDesc")}</CardDescription>
          </CardHeader>
          <CardContent>
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
                onClick={onBack}
                data-testid="2fa-back-btn"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                {t("auth.twoFactor.backToLogin")}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
